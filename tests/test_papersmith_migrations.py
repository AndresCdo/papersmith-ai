"""Artifact-migration core: selection, idempotence, and refusing to guess.

`upgrade` synchronizes framework FILES. These tests cover the mechanism that
carries a workspace's own artifacts to the installed release, and in particular
the two ways it must decline to act: when nothing orders the workspace against
a migration's gate, and when the record of what already ran is unreadable.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from papersmith.core import migrations as migrations_module
from papersmith.core.migrations import Migration
from papersmith.errors import SourceError, UserError


class _Recorder(Migration):
    """A migration whose plan and outcome the test dictates."""

    def __init__(self, identifier: str, *, applies_from: str | None = None,
                 actions: list[str] | None = None, failures: list[str] | None = None) -> None:
        self.id = identifier
        self.applies_from = applies_from
        self.summary = f"recorder {identifier}"
        self._actions = actions if actions is not None else ["did a thing"]
        self._failures = failures or []
        self.applied_times = 0
        self.planned_times = 0

    def plan(self, workspace: Path) -> list[str]:
        self.planned_times += 1
        return list(self._actions)

    def apply(self, workspace: Path) -> tuple[list[str], list[str]]:
        self.applied_times += 1
        return list(self._actions), list(self._failures)


class MigrationTests(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / ".papersmith").mkdir(parents=True)
        return root

    def run_registry(self, workspace: Path, registry, *, recorded: str, kit: str):
        return migrations_module.run(workspace, recorded=recorded, kit_version=kit,
                                     registry=registry)

    # --- convergence migrations -------------------------------------------

    def test_a_convergence_migration_runs_without_any_version_to_compare(self) -> None:
        """A convergence migration asks the filesystem, not the version. It is
        the only kind that can act on a workspace whose recorded version is
        missing, which is exactly the damaged workspace `upgrade` repairs."""
        workspace = self.new_workspace()
        migration = _Recorder("converge", actions=["created sota-pool/"])
        report = self.run_registry(workspace, [migration], recorded="", kit="0.11.0")

        assert migration.applied_times == 1
        assert [outcome.migration_id for outcome in report.applied] == ["converge"]
        assert report.ok

    def test_a_satisfied_convergence_migration_applies_nothing(self) -> None:
        """An empty plan is the probe reporting there is nothing to do. Calling
        `apply` anyway would make every upgrade rewrite artifacts it had no
        reason to touch."""
        workspace = self.new_workspace()
        migration = _Recorder("converge", actions=[])
        report = self.run_registry(workspace, [migration], recorded="0.10.0", kit="0.11.0")

        assert migration.planned_times == 1
        assert migration.applied_times == 0
        assert report.satisfied == ["converge"]
        assert report.applied == []

    def test_a_convergence_migration_is_never_recorded_as_finished(self) -> None:
        """It is never done: the next release can change what the workspace
        must converge to. Recording it would retire it silently."""
        workspace = self.new_workspace()
        migration = _Recorder("converge")
        self.run_registry(workspace, [migration], recorded="0.10.0", kit="0.11.0")
        self.run_registry(workspace, [migration], recorded="0.11.0", kit="0.11.0")

        assert migration.applied_times == 2

    # --- version-gated migrations -----------------------------------------

    def test_a_version_gate_selects_only_the_releases_it_spans(self) -> None:
        workspace = self.new_workspace()
        spanned = _Recorder("spanned", applies_from="0.11.0")
        self.run_registry(workspace, [spanned], recorded="0.10.0", kit="0.11.0")
        assert spanned.applied_times == 1

    def test_a_gate_above_the_installed_kit_has_not_shipped_yet(self) -> None:
        """A migration keyed at a version the installed kit predates belongs to
        a release this workspace has not received. Running it would migrate
        artifacts to a shape the synchronized files cannot read."""
        workspace = self.new_workspace()
        future = _Recorder("future", applies_from="0.12.0")
        report = self.run_registry(workspace, [future], recorded="0.10.0", kit="0.11.0")

        assert future.applied_times == 0
        assert future.planned_times == 0
        assert report.applied == []

    def test_a_gate_the_workspace_already_passed_is_not_reapplied(self) -> None:
        workspace = self.new_workspace()
        passed = _Recorder("passed", applies_from="0.11.0")
        report = self.run_registry(workspace, [passed], recorded="0.11.0", kit="0.12.0")

        assert passed.applied_times == 0
        assert report.applied == []

    def test_a_recorded_gate_is_not_applied_twice(self) -> None:
        """The ledger, not the version marker, is what makes this idempotent: a
        second run at the same recorded version must not repeat the work."""
        workspace = self.new_workspace()
        migration = _Recorder("once", applies_from="0.11.0")
        self.run_registry(workspace, [migration], recorded="0.10.0", kit="0.11.0")
        self.run_registry(workspace, [migration], recorded="0.10.0", kit="0.11.0")

        assert migration.applied_times == 1
        applied = migrations_module.read_applied(workspace)
        assert [entry["id"] for entry in applied] == ["once"]
        assert applied[0]["version"] == "0.11.0"

    def test_a_failed_gate_is_not_recorded_so_a_later_run_retries_it(self) -> None:
        """Recording a failure as applied would strand the workspace: the
        migration would never be offered again, and the artifacts would stay in
        the old shape under the new version."""
        workspace = self.new_workspace()
        failing = _Recorder("failing", applies_from="0.11.0", failures=["renderer missing"])
        report = self.run_registry(workspace, [failing], recorded="0.10.0", kit="0.11.0")

        assert not report.ok
        assert report.failures == ["failing: renderer missing"]
        assert migrations_module.read_applied(workspace) == []

    # --- refusing to guess -------------------------------------------------

    def test_an_unorderable_recorded_version_leaves_a_gate_undetermined(self) -> None:
        """The gate's whole claim is that one version precedes another. With a
        recorded version that carries no number that claim cannot be made, and
        migrating artifacts under a relationship nobody established is the
        silence `_refuse_a_downgrade` already removes on the file side."""
        workspace = self.new_workspace()
        gated = _Recorder("gated", applies_from="0.11.0")
        report = self.run_registry(workspace, [gated], recorded="nightly", kit="0.11.0")

        assert gated.applied_times == 0
        assert report.undetermined == ["gated"]
        assert report.ok

    def test_a_missing_recorded_version_leaves_a_gate_undetermined(self) -> None:
        """There is nothing to migrate FROM. A convergence migration still
        runs; a gated one cannot be placed and says so."""
        workspace = self.new_workspace()
        gated = _Recorder("gated", applies_from="0.11.0")
        report = self.run_registry(workspace, [gated], recorded="", kit="0.11.0")

        assert gated.applied_times == 0
        assert report.undetermined == ["gated"]

    def test_a_damaged_ledger_refuses_before_applying_anything(self) -> None:
        """Reading it as empty would re-apply every recorded migration, which
        is the one failure mode a ledger exists to prevent."""
        workspace = self.new_workspace()
        (workspace / ".papersmith/migrations.json").write_text("not json", encoding="utf-8")
        migration = _Recorder("converge")

        with self.assertRaisesRegex(UserError, "corrupted migrations ledger"):
            self.run_registry(workspace, [migration], recorded="0.10.0", kit="0.11.0")
        assert migration.applied_times == 0

    def test_a_ledger_from_an_unknown_schema_refuses_too(self) -> None:
        workspace = self.new_workspace()
        (workspace / ".papersmith/migrations.json").write_text(
            json.dumps({"schema": 99, "kind": "migrations", "applied": []}), encoding="utf-8")

        with self.assertRaisesRegex(UserError, "corrupted migrations ledger"):
            self.run_registry(workspace, [_Recorder("converge")], recorded="0.10.0", kit="0.11.0")

    def test_a_gate_that_cannot_be_ordered_is_a_packaging_defect(self) -> None:
        """Not a user error: a registry entry nobody can place is a bug in the
        shipped framework, so it carries SOURCE_ERROR rather than blaming the
        operator's workspace."""
        workspace = self.new_workspace()
        broken = _Recorder("broken", applies_from="whenever")

        with self.assertRaisesRegex(SourceError, "broken"):
            self.run_registry(workspace, [broken], recorded="0.10.0", kit="0.11.0")

    # --- planning writes nothing ------------------------------------------

    def test_planning_reports_the_pending_set_and_writes_nothing(self) -> None:
        workspace = self.new_workspace()
        converge = _Recorder("converge", actions=["would create sota-pool/"])
        gated = _Recorder("gated", applies_from="0.11.0", actions=["would rewrite atlas"])
        satisfied = _Recorder("satisfied", actions=[])

        report = migrations_module.plan(workspace, recorded="0.10.0", kit_version="0.11.0",
                                       registry=[converge, gated, satisfied])

        assert converge.applied_times == 0
        assert gated.applied_times == 0
        assert [entry.migration_id for entry in report.pending] == ["converge", "gated"]
        assert report.pending[0].actions == ("would create sota-pool/",)
        assert report.satisfied == ["satisfied"]
        assert not (workspace / ".papersmith/migrations.json").exists()

    def test_the_shipped_registry_declares_no_gate_at_or_below_this_release(self) -> None:
        """A migration keyed at a version already released would never be
        selected for any workspace that is already on it, and would fire for
        every older one without the release that introduced it ever existing.
        """
        from papersmith import __version__

        current = migrations_module.version_order(__version__)
        for migration in migrations_module.REGISTRY:
            if migration.applies_from is None:
                continue
            gate = migrations_module.version_order(migration.applies_from)
            assert gate is not None, migration.id
            assert gate > current, f"{migration.id} is keyed at a released version"


if __name__ == "__main__":
    unittest.main()

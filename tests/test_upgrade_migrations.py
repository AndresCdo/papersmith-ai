"""`upgrade` runs artifact migrations, and the version marker obeys them.

The invariant every test here circles: `.papersmith/version` is a claim about
this workspace's ARTIFACTS, so it advances only when the migrations for that
release are known to be done. The manifest is a claim about FILES and advances
with them, which is what keeps a half-finished upgrade reporting honestly
instead of reporting every synchronized file as drift.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from papersmith.cli import main
from papersmith.core import init as init_module, manifest, migrations as migrations_module
from papersmith.core import upgrade as upgrade_module
from papersmith.core.migrations import Migration
from papersmith.errors import UserError


class _Probe(Migration):
    """A migration whose plan and outcome the test dictates."""

    def __init__(self, identifier: str = "probe", *, applies_from: str | None = None,
                 actions: list[str] | None = None, failures: list[str] | None = None) -> None:
        self.id = identifier
        self.applies_from = applies_from
        self.summary = f"probe {identifier}"
        self._actions = actions if actions is not None else ["touched an artifact"]
        self._failures = failures or []
        self.applied_times = 0
        self.seen_paths: list[Path] = []

    def plan(self, workspace: Path) -> list[str]:
        return list(self._actions)

    def apply(self, workspace: Path) -> tuple[list[str], list[str]]:
        self.applied_times += 1
        self.seen_paths.append(workspace)
        return list(self._actions), list(self._failures)


class UpgradeMigrationTests(unittest.TestCase):
    def new_tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def set_env(self, name: str, value: str) -> None:
        patcher = mock.patch.dict(os.environ, {name: value})
        patcher.start()
        self.addCleanup(patcher.stop)

    def workspace(self, tmp_path: Path) -> Path:
        root = tmp_path / "paper"
        init_module.initialize(root, run_npm=False, run_env=False)
        return root

    def use_registry(self, *entries: Migration) -> None:
        patcher = mock.patch.object(migrations_module, "REGISTRY", tuple(entries))
        patcher.start()
        self.addCleanup(patcher.stop)

    def newer_kit(self, tmp_path: Path) -> str:
        """Install a minimal kit one minor above the version a fresh workspace
        records, so the version marker has somewhere to move."""
        live = manifest.kit_version(upgrade_module.resolve_and_validate())
        major, minor, _ = (int(part) for part in live.split(".")[:3])
        version = f"{major}.{minor + 1}.0"
        kit = tmp_path / f"kit-{version}"
        for relpath, content in {
            "skills/paper-ingestion/SKILL.md": "# skill\n",
            "scripts/setup_env.py": "# env\n",
            ".claude/agents/paper-ingestion.md":
                "---\nname: paper-ingestion\ndescription: d\n---\n",
            "package.json": '{"version": "%s"}\n' % version,
            "requirements.txt": "kagglesdk==0.1.37\n",
            "CLAUDE.md": "# kit marker\n",
        }.items():
            path = kit / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.set_env("PAPERSMITH_KIT_ROOT", str(kit))
        return version

    def recorded_version(self, workspace: Path) -> str:
        return (workspace / ".papersmith/version").read_text(encoding="utf-8").strip()

    # --- the happy path ----------------------------------------------------

    def test_upgrade_runs_a_migration_and_reports_it(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        probe = _Probe(actions=["rebuilt the atlas"])
        self.use_registry(probe)

        result = upgrade_module.upgrade(workspace)

        assert probe.applied_times == 1
        assert probe.seen_paths == [workspace]
        assert result["migrations"]["applied"] == [
            {"id": "probe", "actions": ["rebuilt the atlas"], "failures": []}]
        assert result["migrations"]["ran"] is True

    def test_a_migration_sees_the_synchronized_kit_not_the_old_one(self) -> None:
        """A migration may need the new release's own scripts and assets — the
        atlas renderer is a kit file. Running before the copy would hand it the
        previous release's renderer."""
        seen: list[str] = []

        class _ReadsAKitFile(_Probe):
            def apply(self, workspace: Path) -> tuple[list[str], list[str]]:
                seen.append((workspace / "skills/paper-ingestion/SKILL.md")
                            .read_text(encoding="utf-8"))
                return ["read it"], []

        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        (workspace / "skills/paper-ingestion/SKILL.md").write_text("# stale\n", encoding="utf-8")
        self.use_registry(_ReadsAKitFile())
        self.newer_kit(tmp_path)

        upgrade_module.upgrade(workspace)

        assert seen == ["# skill\n"]

    def test_the_version_marker_advances_when_migrations_succeed(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        self.use_registry(_Probe())
        version = self.newer_kit(tmp_path)

        result = upgrade_module.upgrade(workspace)

        assert self.recorded_version(workspace) == version
        assert result["version"] == version

    # --- the invariant -----------------------------------------------------

    def test_a_failed_migration_keeps_the_version_marker_where_it_was(self) -> None:
        """This is the whole feature. Advancing the marker over artifacts that
        did not move makes the workspace report a shape it does not have, and
        nothing downstream can ever notice."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        before = self.recorded_version(workspace)
        self.use_registry(_Probe(failures=["renderer missing"]))
        version = self.newer_kit(tmp_path)

        result = upgrade_module.upgrade(workspace)

        assert self.recorded_version(workspace) == before
        assert result["migrations"]["failures"] == ["probe: renderer missing"]
        assert ".papersmith/version" not in result["changed_files"]

    def test_a_failed_migration_still_records_the_files_it_did_synchronize(self) -> None:
        """The manifest is a claim about files, and the files DID move. Holding
        it back would make `status` report every synchronized file as drift and
        bury the one fact that matters."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        self.use_registry(_Probe(failures=["renderer missing"]))
        version = self.newer_kit(tmp_path)

        upgrade_module.upgrade(workspace)

        stored = json.loads((workspace / ".papersmith/manifest.json").read_text(encoding="utf-8"))
        assert stored["version"] == version
        assert (workspace / "skills/paper-ingestion/SKILL.md").read_text() == "# skill\n"

    def test_a_failed_migration_is_retried_by_the_next_run(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        probe = _Probe(failures=["renderer missing"])
        self.use_registry(probe)
        self.newer_kit(tmp_path)

        upgrade_module.upgrade(workspace)
        upgrade_module.upgrade(workspace)

        assert probe.applied_times == 2
        assert migrations_module.read_applied(workspace) == []

    def test_skipping_migrations_also_holds_the_version_marker_back(self) -> None:
        """`--no-migrate` means "synchronize the files, leave my artifacts".
        Advancing the marker anyway would turn the flag into a way to record a
        release the artifacts never reached — the one lie this feature removes.
        One rule, no exception: the marker moves when the migrations are done.
        """
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        before = self.recorded_version(workspace)
        probe = _Probe()
        self.use_registry(probe)
        self.newer_kit(tmp_path)

        result = upgrade_module.upgrade(workspace, migrate=False)

        assert probe.applied_times == 0
        assert self.recorded_version(workspace) == before
        assert result["migrations"]["ran"] is False
        assert result["migrations"]["pending"] == [
            {"id": "probe", "summary": "probe probe",
             "actions": ["touched an artifact"]}]

    def test_skipping_migrations_advances_the_marker_when_none_are_pending(self) -> None:
        """Nothing was withheld, so nothing is owed."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        self.use_registry(_Probe(actions=[]))
        version = self.newer_kit(tmp_path)

        upgrade_module.upgrade(workspace, migrate=False)

        assert self.recorded_version(workspace) == version

    def test_an_undetermined_migration_does_not_block_the_marker(self) -> None:
        """Undetermined is not failure: nothing was attempted, so nothing is
        half-done. It is reported and the file-side upgrade completes."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        (workspace / ".papersmith/version").write_text("nightly\n", encoding="utf-8")
        self.use_registry(_Probe(applies_from="99.0.0"))
        version = self.newer_kit(tmp_path)

        result = upgrade_module.upgrade(workspace, allow_downgrade=True)

        assert result["migrations"]["undetermined"] == ["probe"]
        assert self.recorded_version(workspace) == version

    def test_a_damaged_ledger_refuses_before_a_single_file_is_synchronized(self) -> None:
        """Same placement as the downgrade guard, for the same reason: a damaged
        ledger cannot be told from an empty one, and discovering that after the
        files are copied leaves a half-moved workspace and no record of why."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        stale = workspace / "skills/paper-ingestion/SKILL.md"
        stale.write_text("# stale\n", encoding="utf-8")
        (workspace / ".papersmith/migrations.json").write_text("not json", encoding="utf-8")
        self.use_registry(_Probe())
        self.newer_kit(tmp_path)

        with self.assertRaisesRegex(UserError, "corrupted migrations ledger"):
            upgrade_module.upgrade(workspace)
        assert stale.read_text(encoding="utf-8") == "# stale\n"

    # --- planning ----------------------------------------------------------

    def test_planning_writes_nothing_at_all(self) -> None:
        """Not even the kit copy. A preview that synchronized files on the way
        would be a preview of something that already happened."""
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        before = self.recorded_version(workspace)
        (workspace / "skills/paper-ingestion/SKILL.md").write_text("# stale\n", encoding="utf-8")
        probe = _Probe(actions=["would rebuild the atlas"])
        self.use_registry(probe)
        self.newer_kit(tmp_path)

        result = upgrade_module.upgrade(workspace, plan_migrations=True)

        assert probe.applied_times == 0
        assert self.recorded_version(workspace) == before
        assert (workspace / "skills/paper-ingestion/SKILL.md").read_text() == "# stale\n"
        assert not (workspace / ".papersmith/migrations.json").exists()
        assert result["migrations"]["pending"] == [
            {"id": "probe", "summary": "probe probe", "actions": ["would rebuild the atlas"]}]
        assert result["planned"] is True

    # --- the CLI contract --------------------------------------------------

    def test_cli_reports_a_failed_migration_as_a_non_zero_exit(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        before = self.recorded_version(workspace)
        self.use_registry(_Probe(failures=["renderer missing"]))
        self.newer_kit(tmp_path)

        buffer, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
            code = main(["upgrade", str(workspace)])

        assert code != 0
        assert "renderer missing" in buffer.getvalue() + errors.getvalue()
        assert self.recorded_version(workspace) == before

    def test_cli_plan_migrations_prints_the_pending_set_and_exits_zero(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        self.use_registry(_Probe(actions=["would rebuild the atlas"]))
        self.newer_kit(tmp_path)

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert main(["upgrade", str(workspace), "--plan-migrations"]) == 0
        printed = buffer.getvalue()

        assert "would rebuild the atlas" in printed
        assert "probe" in printed

    def test_cli_no_migrate_says_what_it_held_back(self) -> None:
        tmp_path = self.new_tmp()
        workspace = self.workspace(tmp_path)
        self.use_registry(_Probe())
        self.newer_kit(tmp_path)

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert main(["upgrade", str(workspace), "--no-migrate"]) == 0

        assert "probe" in buffer.getvalue()


if __name__ == "__main__":
    unittest.main()

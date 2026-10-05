"""The graph pool: scaffolded at init, converged on upgrade, never overwritten.

`sota-pool/` holds the plausibility flow's graph state — `candidates.json` from
`sota-scout`, `atlas.json` from `sota-grapher`, and the `atlas.html` rendered
from it. Until this feature the CLI did not know the directory existed:
`grep -rn sota-pool src/papersmith` returned nothing, `_create_topology` never
created it, and the workspace `.gitignore` template omitted it while claiming
to mirror this framework's own root ignore file entry for entry.
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from papersmith.cli import main
from papersmith.core import init as init_module, upgrade as upgrade_module


class GraphPoolTopologyTests(unittest.TestCase):
    def new_tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def workspace(self, tmp_path: Path) -> Path:
        root = tmp_path / "paper"
        init_module.initialize(root, run_npm=False, run_env=False)
        return root

    def predates_the_scaffolding(self, tmp_path: Path) -> Path:
        """A workspace in the shape an older release left behind."""
        root = self.workspace(tmp_path)
        keep = root / "sota-pool" / ".gitkeep"
        if keep.exists():
            keep.unlink()
            keep.parent.rmdir()
        return root

    # --- init scaffolds it -------------------------------------------------

    def test_a_fresh_workspace_scaffolds_the_graph_pool(self) -> None:
        """Every other drop-zone travels through git as an empty folder. The
        graph pool did not, so a collaborator cloning a workspace received no
        place for the atlas to land."""
        workspace = self.workspace(self.new_tmp())
        assert (workspace / "sota-pool" / ".gitkeep").is_file()

    def test_the_workspace_ignore_file_keeps_the_graph_pool_local(self) -> None:
        """The template's own comment says every entry mirrors this framework's
        root `.gitignore` so "nobody's papers, proposals, or run products leave
        their machine by accident". The graph pool IS run product, and it was
        the one entry missing — `atlas.html` inlines a whole viewer bundle."""
        workspace = self.workspace(self.new_tmp())
        ignored = (workspace / ".gitignore").read_text(encoding="utf-8")
        assert "sota-pool/*" in ignored
        assert "!sota-pool/.gitkeep" in ignored

    # --- upgrade converges an existing workspace ---------------------------

    def test_upgrade_scaffolds_the_graph_pool_in_an_older_workspace(self) -> None:
        """`upgrade` synchronizes files and renders projections; it had no way
        to create a directory an existing workspace was missing. This is what
        the convergence migration is for."""
        workspace = self.predates_the_scaffolding(self.new_tmp())
        result = upgrade_module.upgrade(workspace)

        assert (workspace / "sota-pool" / ".gitkeep").is_file()
        assert "sota-pool-scaffold" in [
            entry["id"] for entry in result["migrations"]["applied"]]

    def test_converging_never_touches_the_graph_artifacts_themselves(self) -> None:
        """The pool is research state. The migration scaffolds the folder and
        stops; rewriting an atlas would destroy the work the folder exists for.
        """
        workspace = self.predates_the_scaffolding(self.new_tmp())
        atlas = workspace / "sota-pool" / "atlas.json"
        atlas.parent.mkdir(parents=True, exist_ok=True)
        atlas.write_text('{"systems": ["mine"]}\n', encoding="utf-8")
        candidates = workspace / "sota-pool" / "candidates.json"
        candidates.write_text('{"candidates": ["mine"]}\n', encoding="utf-8")

        upgrade_module.upgrade(workspace)

        assert atlas.read_text(encoding="utf-8") == '{"systems": ["mine"]}\n'
        assert candidates.read_text(encoding="utf-8") == '{"candidates": ["mine"]}\n'

    def test_a_scaffolded_workspace_reports_the_migration_as_satisfied(self) -> None:
        """A convergence migration is evaluated on every upgrade, so an
        already-converged workspace must do nothing rather than rewrite."""
        workspace = self.workspace(self.new_tmp())
        result = upgrade_module.upgrade(workspace)

        assert "sota-pool-scaffold" in result["migrations"]["satisfied"]
        assert result["migrations"]["applied"] == []

    def test_a_blocked_graph_pool_is_reported_not_raised(self) -> None:
        """A migration that raises aborts a run which has already synchronized
        files, leaving the operator no report of what did happen. A path
        occupied by a regular file is reported as a failure instead."""
        workspace = self.predates_the_scaffolding(self.new_tmp())
        (workspace / "sota-pool").write_text("not a directory\n", encoding="utf-8")

        result = upgrade_module.upgrade(workspace)

        assert result["migrations"]["failures"], result["migrations"]
        assert "sota-pool" in result["migrations"]["failures"][0]

    def test_the_cli_reports_a_blocked_graph_pool_as_a_non_zero_exit(self) -> None:
        workspace = self.predates_the_scaffolding(self.new_tmp())
        (workspace / "sota-pool").write_text("not a directory\n", encoding="utf-8")

        buffer, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
            code = main(["upgrade", str(workspace)])

        assert code != 0
        assert "sota-pool" in buffer.getvalue() + errors.getvalue()


if __name__ == "__main__":
    unittest.main()

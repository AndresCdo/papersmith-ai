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
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from papersmith.cli import main
from papersmith.core import init as init_module, upgrade as upgrade_module

#: The smallest atlas the renderer accepts. `_readable_shape` admits a system
#: without an `id`, which `_scene` then requires — a pre-existing gap in
#: `render_atlas.py` that is not this feature's to close, so the fixture names
#: the field the renderer actually reads.
VALID_ATLAS = '{"systems":[{"id":"s1","label":"S","family":"F","planets":[]}],"links":[]}\n'


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
        atlas.write_text(VALID_ATLAS, encoding="utf-8")
        candidates = workspace / "sota-pool" / "candidates.json"
        candidates.write_text('{"candidates": ["mine"]}\n', encoding="utf-8")

        upgrade_module.upgrade(workspace)

        assert atlas.read_text(encoding="utf-8") == VALID_ATLAS
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


class RenderedAtlasTests(unittest.TestCase):
    """`atlas.html` is DERIVED: the renderer and the viewer bundle it inlines
    are both kit files, so a release that ships either leaves the rendered
    graph stale with nothing that notices. This is the artifact adjustment the
    whole migration mechanism was built for.
    """

    def new_tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def workspace(self, tmp_path: Path) -> Path:
        root = tmp_path / "paper"
        init_module.initialize(root, run_npm=False, run_env=False)
        return root

    def with_atlas(self, tmp_path: Path, content: str = VALID_ATLAS) -> Path:
        root = self.workspace(tmp_path)
        atlas = root / "sota-pool" / "atlas.json"
        atlas.parent.mkdir(parents=True, exist_ok=True)
        atlas.write_text(content, encoding="utf-8")
        return root

    def test_a_workspace_with_no_atlas_has_nothing_to_render(self) -> None:
        """The pool is empty until the grapher fills it. Rendering a page from
        an atlas that does not exist would invent a graph."""
        workspace = self.workspace(self.new_tmp())
        result = upgrade_module.upgrade(workspace)

        assert "atlas-render-refresh" in result["migrations"]["satisfied"]
        assert not (workspace / "sota-pool" / "atlas.html").exists()

    def test_an_unrendered_atlas_is_rendered(self) -> None:
        workspace = self.with_atlas(self.new_tmp())
        result = upgrade_module.upgrade(workspace)

        page = workspace / "sota-pool" / "atlas.html"
        assert page.is_file()
        assert "<!DOCTYPE html>" in page.read_text(encoding="utf-8")
        assert "atlas-render-refresh" in [
            entry["id"] for entry in result["migrations"]["applied"]]
        assert result["migrations"]["failures"] == []

    def test_a_current_page_is_left_alone(self) -> None:
        """Re-rendering on every upgrade would rewrite a 580 KB artifact for no
        reason and make the migration's report meaningless."""
        workspace = self.with_atlas(self.new_tmp())
        upgrade_module.upgrade(workspace)
        page = workspace / "sota-pool" / "atlas.html"
        rendered = page.read_bytes()

        result = upgrade_module.upgrade(workspace)

        assert page.read_bytes() == rendered
        assert "atlas-render-refresh" in result["migrations"]["satisfied"]

    def test_a_release_that_changed_the_viewer_makes_the_page_stale(self) -> None:
        """The staleness signal is a hash of the renderer and the viewer bundle,
        not a timestamp: a copy's mtime says when the file was written, and two
        builds a user cannot tell apart are two pages nobody can order either.
        """
        workspace = self.with_atlas(self.new_tmp())
        upgrade_module.upgrade(workspace)
        stamp = workspace / "sota-pool" / ".atlas-render.json"
        recorded = json.loads(stamp.read_text(encoding="utf-8"))
        recorded["viewer"] = "0" * 64  # as if rendered under a previous bundle
        stamp.write_text(json.dumps(recorded), encoding="utf-8")

        result = upgrade_module.upgrade(workspace)

        assert "atlas-render-refresh" in [
            entry["id"] for entry in result["migrations"]["applied"]]
        assert json.loads(stamp.read_text(encoding="utf-8"))["viewer"] != "0" * 64

    def test_an_edited_atlas_makes_the_page_stale_too(self) -> None:
        workspace = self.with_atlas(self.new_tmp())
        upgrade_module.upgrade(workspace)
        (workspace / "sota-pool" / "atlas.json").write_text(
            '{"systems":[{"id":"s2","label":"T","family":"G","planets":[]}],"links":[]}\n',
            encoding="utf-8")

        result = upgrade_module.upgrade(workspace)

        assert "atlas-render-refresh" in [
            entry["id"] for entry in result["migrations"]["applied"]]

    def test_an_unrenderable_atlas_is_reported_and_holds_the_version_back(self) -> None:
        """The renderer's own typed refusal must reach the operator. Swallowing
        it would leave a stale page under a version claiming otherwise, and
        raising would abort a run that already synchronized files."""
        tmp_path = self.new_tmp()
        workspace = self.with_atlas(tmp_path, '{"systems": "not a list"}\n')
        before = (workspace / ".papersmith/version").read_text(encoding="utf-8")

        result = upgrade_module.upgrade(workspace)

        assert result["migrations"]["failures"], result["migrations"]
        failure = result["migrations"]["failures"][0]
        assert "atlas-render-refresh" in failure
        assert "SYSTEMS_NOT_A_NONEMPTY_LIST" in failure
        assert (workspace / ".papersmith/version").read_text(encoding="utf-8") == before

    def test_a_deleted_renderer_is_restored_before_the_migration_runs(self) -> None:
        """The ordering, proved from the outside: migrations run after the kit
        is synchronized, so a migration always sees the installed release's own
        renderer. Running before the copy would hand it the previous one — or,
        here, nothing at all."""
        workspace = self.with_atlas(self.new_tmp())
        (workspace / "skills/plausibility/scripts/render_atlas.py").unlink()

        result = upgrade_module.upgrade(workspace)

        assert result["migrations"]["failures"] == []
        assert (workspace / "sota-pool" / "atlas.html").is_file()


if __name__ == "__main__":
    unittest.main()

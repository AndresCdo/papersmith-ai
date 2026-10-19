"""Regenerating the SOTA atlas: the dashboard button, its route and the CLI.

The rebuild runs the WORKSPACE's own plausibility scripts (checker, then
renderer), so fixture workspaces copy the real scripts and viewer bundle from
this repository.
"""

from __future__ import annotations

import asyncio
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from papersmith.cli import build_parser
from skills._core.command_center import atlas_build, server

REPO = Path(__file__).resolve().parent.parent
PLAUSIBILITY = REPO / "skills" / "plausibility"
COMMAND_CENTER = REPO / "skills" / "_core" / "command_center"

from tests.test_command_center_atlas import valid_atlas  # noqa: E402


class _Request:
    """The one thing the route reads from a request: nothing."""


def _routes(app) -> dict:
    return {(r.path, tuple(sorted(getattr(r, "methods", None) or ()))): r.endpoint
            for r in app.routes if hasattr(r, "path") and hasattr(r, "endpoint")}


def _route(app, path: str, method: str):
    for (route_path, methods), endpoint in _routes(app).items():
        if route_path == path and method in methods:
            return endpoint
    raise AssertionError(f"no {method} {path} route")


class _Workspace(unittest.TestCase):
    def new_workspace(self, *, scripts: bool = True) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sota-pool").mkdir()
        if scripts:
            target = root / "skills" / "plausibility"
            (target / "scripts").mkdir(parents=True)
            (target / "assets").mkdir()
            for name in ("check_atlas.py", "render_atlas.py"):
                shutil.copy(PLAUSIBILITY / "scripts" / name, target / "scripts" / name)
            shutil.copy(PLAUSIBILITY / "assets" / "atlas3d.bundle.js",
                        target / "assets" / "atlas3d.bundle.js")
            center = root / "skills" / "_core" / "command_center"
            center.mkdir(parents=True)
            for name in ("__init__.py", "atlas_build.py"):
                shutil.copy(COMMAND_CENTER / name, center / name)
        return root

    def write_atlas(self, root: Path, data: dict) -> None:
        (root / "sota-pool" / "atlas.json").write_text(json.dumps(data), encoding="utf-8")


class BuildTests(_Workspace):
    def test_a_valid_atlas_is_rendered_and_counted(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        result = atlas_build.build(root)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["stage"], "rendered")
        self.assertEqual((result["systems"], result["planets"], result["links"]), (3, 27, 3))
        page = (root / "sota-pool" / "atlas.html").read_text(encoding="utf-8")
        self.assertIn('id="atlas-data"', page)

    def test_a_failing_checker_leaves_the_old_page_untouched(self) -> None:
        root = self.new_workspace()
        broken = valid_atlas()
        broken["systems"][0]["planets"] = broken["systems"][0]["planets"][:2]
        self.write_atlas(root, broken)
        old = root / "sota-pool" / "atlas.html"
        old.write_text("<html>previous</html>", encoding="utf-8")
        result = atlas_build.build(root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "check")
        self.assertTrue(result["violations"])
        self.assertEqual(old.read_text(encoding="utf-8"), "<html>previous</html>")

    def test_the_pool_is_enforced_when_candidates_exist(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        (root / "sota-pool" / "candidates.json").write_text("[]", encoding="utf-8")
        result = atlas_build.build(root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "check")

    def test_a_missing_atlas_json_is_reported(self) -> None:
        root = self.new_workspace()
        result = atlas_build.build(root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "absent")
        self.assertFalse((root / "sota-pool" / "atlas.html").exists())

    def test_missing_scripts_are_reported(self) -> None:
        root = self.new_workspace(scripts=False)
        self.write_atlas(root, valid_atlas())
        result = atlas_build.build(root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "scripts")


class RouteTests(_Workspace):
    def call(self, root: Path):
        app = server.create_app(root, history_store=None)
        endpoint = _route(app, "/api/atlas/build", "POST")
        response = endpoint()
        if asyncio.iscoroutine(response):
            response = asyncio.run(response)
        return response.status_code, json.loads(bytes(response.body).decode("utf-8"))

    def test_the_route_rebuilds_the_page(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        status, body = self.call(root)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["systems"], 3)
        self.assertTrue((root / "sota-pool" / "atlas.html").is_file())

    def test_the_route_reports_a_failure_without_writing(self) -> None:
        root = self.new_workspace()
        status, body = self.call(root)
        self.assertEqual(status, 404)
        self.assertFalse(body["ok"])
        self.assertEqual(body["stage"], "absent")

    def test_the_route_refuses_a_failing_atlas(self) -> None:
        root = self.new_workspace()
        broken = valid_atlas()
        broken["links"] = "nope"
        self.write_atlas(root, broken)
        status, body = self.call(root)
        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])

    def test_the_view_route_still_serves_the_page(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        self.call(root)
        app = server.create_app(root, history_store=None)
        response = _route(app, "/api/atlas/view", "GET")()
        self.assertEqual(response.status_code, 200)


class CliTests(_Workspace):
    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        parser = build_parser("smith")
        args = parser.parse_args(list(argv))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = args.handler(args)
        return code, out.getvalue(), err.getvalue()

    def test_smith_atlas_build_renders(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        code, out, _err = self.run_cli("atlas", "build", str(root))
        self.assertEqual(code, 0)
        self.assertIn("3 systems", out)
        self.assertTrue((root / "sota-pool" / "atlas.html").is_file())

    def test_smith_atlas_build_fails_closed(self) -> None:
        root = self.new_workspace()
        code, _out, err = self.run_cli("atlas", "build", str(root))
        self.assertEqual(code, 1)
        self.assertIn("atlas.json", err)

    def test_smith_atlas_build_json(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, valid_atlas())
        code, out, _err = self.run_cli("atlas", "build", "--json", str(root))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["ok"])

    def test_the_ui_command_is_still_registered(self) -> None:
        args = build_parser("smith").parse_args(["ui", "--no-browser", "."])
        self.assertTrue(args.no_browser)


if __name__ == "__main__":
    unittest.main()

"""A workspace records which framework build it came from, and a dirty one refuses.

`init` and `upgrade` copy whatever kit the installed CLI resolves. From an
editable install that is the live checkout, uncommitted edits included, and
nothing recorded which commit a workspace was built from. These tests pin the
two halves of the fix:

- every `init` and every `upgrade` writes `.papersmith/kit-source.json`
  (version, commit, dirty, source) and `status` reports it;
- a kit source tree with uncommitted changes under its shipped paths, or one
  whose git state cannot be read at all, refuses before a byte is written
  unless `--allow-dirty-kit` (or `PAPERSMITH_ALLOW_DIRTY_KIT=1`) is given.

The suite itself runs from a checkout that is usually dirty, so
`tests/conftest.py` sets `PAPERSMITH_ALLOW_DIRTY_KIT=1`; every test here
removes it first, so the refusal is exercised for real.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from papersmith import kit as kit_module
from papersmith.cli import main
from papersmith.core import init as init_module
from papersmith.core import provenance
from papersmith.core import status as status_module
from papersmith.core import upgrade as upgrade_module
from papersmith.errors import UserError
from papersmith.mcp import registry

ROOT = Path(__file__).resolve().parent.parent
HAS_GIT = shutil.which("git") is not None

KIT_FILES = {
    "skills/paper-ingestion/SKILL.md": "# skill\n",
    "scripts/setup_env.py": "# env\n",
    ".claude/agents/paper-ingestion.md": "---\nname: paper-ingestion\ndescription: d\n---\n",
    "requirements.txt": "kagglesdk==0.1.37\n",
    "CLAUDE.md": "# kit marker\n",
}


def _git(root: Path, *args: str) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


class _KitSourceCase(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(provenance.ALLOW_DIRTY_ENV, None)

    def new_tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def make_kit(self, tmp: Path, *, version: str, git: bool) -> Path:
        kit = tmp / f"kit-{version}"
        for relpath, content in {**KIT_FILES,
                                 "package.json": '{"version": "%s"}\n' % version}.items():
            path = kit / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        if git:
            _git(kit, "init", "-q")
            _git(kit, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
            _git(kit, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
                 "commit", "-q", "-m", "kit")
        os.environ["PAPERSMITH_KIT_ROOT"] = str(kit)
        return kit

    def init(self, destination: Path, **kwargs) -> dict:
        return init_module.initialize(destination, run_npm=False, run_env=False, **kwargs)

    def record(self, workspace: Path) -> dict:
        return json.loads((workspace / provenance.KIT_SOURCE_RECORD).read_text(encoding="utf-8"))


@unittest.skipUnless(HAS_GIT, "git is required to build a kit source tree")
class InitRecordsAndRefusesTests(_KitSourceCase):
    def test_a_clean_git_kit_initializes_and_records_its_commit(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        workspace = tmp / "ws"
        self.init(workspace)
        record = self.record(workspace)
        self.assertEqual(record["version"], "9.1.0")
        self.assertEqual(record["commit"], _git(kit, "rev-parse", "HEAD"))
        self.assertIs(record["dirty"], False)
        self.assertEqual(record["source"], "override")
        self.assertNotIn("allowedDirty", record)
        self.assertIn("recordedAt", record)

    def test_a_modified_shipped_file_refuses_before_anything_is_written(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        workspace = tmp / "ws"
        with self.assertRaises(UserError) as caught:
            self.init(workspace)
        message = str(caught.exception)
        self.assertIn("--allow-dirty-kit", message)
        self.assertIn("skills/paper-ingestion/SKILL.md", message)
        self.assertFalse(workspace.exists(), "the refusal must precede every write")

    def test_an_untracked_shipped_file_also_counts_as_dirty(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "skills/new-skill").mkdir()
        (kit / "skills/new-skill/SKILL.md").write_text("# new\n", encoding="utf-8")
        with self.assertRaises(UserError):
            self.init(tmp / "ws")

    def test_an_edit_outside_the_shipped_paths_does_not_refuse(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "notes.txt").write_text("scratch\n", encoding="utf-8")
        self.init(tmp / "ws")
        self.assertIs(self.record(tmp / "ws")["dirty"], False)

    def test_the_flag_overrides_and_the_record_says_so(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        self.init(tmp / "ws", allow_dirty_kit=True)
        record = self.record(tmp / "ws")
        self.assertIs(record["dirty"], True)
        self.assertIs(record["allowedDirty"], True)
        self.assertEqual(record["commit"], _git(kit, "rev-parse", "HEAD"))

    def test_the_environment_variable_is_the_same_override(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        os.environ[provenance.ALLOW_DIRTY_ENV] = "1"
        self.init(tmp / "ws")
        self.assertIs(self.record(tmp / "ws")["allowedDirty"], True)

    def test_the_cli_flag_reaches_init(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        base = ["init", str(tmp / "ws"), "--no-npm", "--no-env", "--no-progress"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(base), 1)
            self.assertFalse((tmp / "ws").exists())
            self.assertEqual(main([*base, "--allow-dirty-kit"]), 0)
        self.assertIs(self.record(tmp / "ws")["dirty"], True)


class UnknownGitStateTests(_KitSourceCase):
    def test_a_source_tree_outside_git_refuses_as_unknown(self) -> None:
        tmp = self.new_tmp()
        self.make_kit(tmp, version="9.1.0", git=False)
        with self.assertRaises(UserError) as caught:
            self.init(tmp / "ws")
        message = str(caught.exception)
        self.assertIn("cannot determine", message)
        self.assertIn("--allow-dirty-kit", message)
        self.assertFalse((tmp / "ws").exists())

    def test_the_flag_admits_it_with_an_unknown_commit(self) -> None:
        tmp = self.new_tmp()
        self.make_kit(tmp, version="9.1.0", git=False)
        self.init(tmp / "ws", allow_dirty_kit=True)
        record = self.record(tmp / "ws")
        self.assertIsNone(record["commit"])
        self.assertIsNone(record["dirty"])
        self.assertIs(record["allowedDirty"], True)
        self.assertTrue(record["reason"])

    def test_a_missing_git_binary_is_unknown_not_clean(self) -> None:
        tmp = self.new_tmp()
        kit = self.make_kit(tmp, version="9.1.0", git=False)
        with mock.patch.object(provenance.subprocess, "run", side_effect=FileNotFoundError("git")):
            state = provenance.describe(kit, "override")
        self.assertIsNone(state.commit)
        self.assertIsNone(state.dirty)
        with self.assertRaises(UserError):
            provenance.require_admissible(state, verb="init", allow_dirty=False)


class BuiltKitTests(_KitSourceCase):
    def built_kit(self, tmp: Path, **build: object) -> Path:
        kit = self.make_kit(tmp, version="9.2.0", git=False)
        payload = {"schema": 1, "kind": "kit", "version": "9.2.0",
                   "files": {rel: "0" * 64 for rel in KIT_FILES}, **build}
        (kit / "kit-manifest.json").write_text(json.dumps(payload), encoding="utf-8")
        return kit

    def test_a_built_kit_reports_the_commit_captured_at_build_time(self) -> None:
        kit = self.built_kit(self.new_tmp(), commit="a" * 40, dirty=False)
        state = provenance.describe(kit, "bundled")
        self.assertEqual((state.version, state.commit, state.dirty, state.source),
                         ("9.2.0", "a" * 40, False, "bundled"))
        provenance.require_admissible(state, verb="init", allow_dirty=False)

    def test_a_kit_built_from_a_dirty_tree_refuses(self) -> None:
        kit = self.built_kit(self.new_tmp(), commit="a" * 40, dirty=True)
        state = provenance.describe(kit, "bundled")
        with self.assertRaises(UserError) as caught:
            provenance.require_admissible(state, verb="upgrade", allow_dirty=False)
        self.assertIn("--allow-dirty-kit", str(caught.exception))

    def test_a_built_kit_without_build_provenance_is_frozen_not_refused(self) -> None:
        # A kit built before 0.14.0, or from a tree with no git: its bytes are a
        # frozen snapshot named by the manifest, so the commit is unknown but the
        # bytes are not live edits.
        kit = self.built_kit(self.new_tmp())
        state = provenance.describe(kit, "bundled")
        self.assertIsNone(state.commit)
        self.assertIsNone(state.dirty)
        provenance.require_admissible(state, verb="init", allow_dirty=False)

    def test_resolution_names_the_bundled_source(self) -> None:
        tmp = self.new_tmp()
        site = tmp / "site" / "papersmith"
        site.mkdir(parents=True)
        (site / "kit.py").write_text("", encoding="utf-8")
        os.environ.pop("PAPERSMITH_KIT_ROOT", None)
        root, source = kit_module.resolve_kit_origin(site / "kit.py")
        self.assertEqual((root, source), (site / "_kit", "bundled"))

    def test_resolution_names_the_override_source(self) -> None:
        tmp = self.new_tmp()
        os.environ["PAPERSMITH_KIT_ROOT"] = str(tmp)
        self.assertEqual(kit_module.resolve_kit_origin(tmp / "x.py"), (tmp, "override"))


@unittest.skipUnless(HAS_GIT and (ROOT / ".git").exists(), "needs this repository's git tree")
class BuildKitEmbedsProvenanceTests(_KitSourceCase):
    def test_build_kit_writes_the_commit_and_dirty_flag(self) -> None:
        spec = importlib.util.spec_from_file_location("build_kit", ROOT / "scripts" / "build-kit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        target = self.new_tmp() / "_kit"
        module.KIT = target
        module.assemble(quiet=True)
        data = json.loads((target / "kit-manifest.json").read_text(encoding="utf-8"))
        expected = provenance.git_state(ROOT)
        self.assertEqual(data["commit"], _git(ROOT, "rev-parse", "HEAD"))
        self.assertEqual(data["dirty"], expected.dirty)
        self.assertIsInstance(data["dirty"], bool)


@unittest.skipUnless(HAS_GIT, "git is required to build a kit source tree")
class UpgradeRecordsAndRefusesTests(_KitSourceCase):
    def workspace(self, tmp: Path) -> Path:
        self.make_kit(tmp, version="9.1.0", git=True)
        workspace = tmp / "ws"
        self.init(workspace)
        return workspace

    def test_upgrade_refuses_a_dirty_kit_before_writing(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        kit = self.make_kit(tmp / "next", version="9.2.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        before = (workspace / ".papersmith/manifest.json").read_bytes()
        record_before = self.record(workspace)
        with self.assertRaises(UserError) as caught:
            upgrade_module.upgrade(workspace)
        self.assertIn("--allow-dirty-kit", str(caught.exception))
        self.assertEqual((workspace / ".papersmith/manifest.json").read_bytes(), before)
        self.assertEqual(self.record(workspace), record_before)
        self.assertEqual((workspace / ".papersmith/version").read_text().strip(), "9.1.0")

    def test_upgrade_with_the_flag_records_the_new_source(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        kit = self.make_kit(tmp / "next", version="9.2.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        upgrade_module.upgrade(workspace, allow_dirty_kit=True)
        record = self.record(workspace)
        self.assertEqual(record["version"], "9.2.0")
        self.assertIs(record["dirty"], True)

    def test_plan_migrations_writes_nothing_so_it_does_not_refuse(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        kit = self.make_kit(tmp / "next", version="9.2.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        result = upgrade_module.upgrade(workspace, plan_migrations=True)
        self.assertTrue(result["planned"])

    def test_a_workspace_recorded_before_0_14_0_gains_the_record_on_upgrade(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        (workspace / provenance.KIT_SOURCE_RECORD).unlink()
        snapshot = status_module.status(workspace)
        self.assertEqual(snapshot["framework"]["kit_source"],
                         {"recorded": False, "detail": "unknown (recorded before 0.14.0)"})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status_module.print_human(snapshot)
        self.assertIn("Kit source: unknown (recorded before 0.14.0)", out.getvalue())
        upgrade_module.upgrade(workspace)
        self.assertEqual(self.record(workspace)["version"], "9.1.0")

    def test_status_reports_the_recorded_source(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        commit = self.record(workspace)["commit"]
        snapshot = status_module.status(workspace)
        source = snapshot["framework"]["kit_source"]
        self.assertTrue(source["recorded"])
        self.assertEqual(source["commit"], commit)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status_module.print_human(snapshot)
        self.assertIn(f"Kit source: 9.1.0 at {commit[:12]} (override, clean)", out.getvalue())

    def test_the_record_is_not_drift_for_audit(self) -> None:
        # The real kit, because `audit` runs the kit's own structural probe; the
        # checkout this suite runs from may be dirty, hence the flag.
        os.environ.pop("PAPERSMITH_KIT_ROOT", None)
        workspace = self.new_tmp() / "ws"
        self.init(workspace, allow_dirty_kit=True)
        self.assertTrue((workspace / provenance.KIT_SOURCE_RECORD).is_file())
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(["audit", str(workspace), "--check-drift"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertEqual(status_module.status(workspace)["framework"]["drifted_files"], [])

    def test_the_cli_flag_reaches_upgrade(self) -> None:
        tmp = self.new_tmp()
        workspace = self.workspace(tmp)
        kit = self.make_kit(tmp / "next", version="9.2.0", git=True)
        (kit / "skills/paper-ingestion/SKILL.md").write_text("# edited\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["upgrade", str(workspace)]), 1)
            self.assertEqual(main(["upgrade", str(workspace), "--allow-dirty-kit"]), 0)


class McpForwardsTheFlagTests(unittest.TestCase):
    def test_init_and_upgrade_tools_expose_and_forward_the_flag(self) -> None:
        workspace = Path(tempfile.gettempdir()).resolve()
        for name in ("papersmith.workspace_init", "papersmith.workspace_upgrade"):
            spec = registry.TOOLS_BY_NAME[name]
            self.assertIn("allow_dirty_kit", spec.input_schema["properties"])
            arguments = {"name": "paper"} if name.endswith("init") else {}
            self.assertNotIn("--allow-dirty-kit", spec.build(arguments, workspace).tokens)
            plan = spec.build({**arguments, "allow_dirty_kit": True}, workspace)
            self.assertIn("--allow-dirty-kit", plan.tokens)


if __name__ == "__main__":
    unittest.main()

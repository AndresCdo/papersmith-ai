"""Tests for scripts/fast_tests.py, the fast iteration tier.

The selection functions are pure, so most of this needs no git at all. One test
runs `--list` against a tiny throwaway repository it initialises itself.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile

FORGE = Path(__file__).resolve().parent.parent
SCRIPT = FORGE / "scripts" / "fast_tests.py"


def _load():
    spec = importlib.util.spec_from_file_location("papersmith_fast_tests", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fast = _load()


class TokenTests(unittest.TestCase):
    def test_src_file_yields_path_filename_and_dotted_module(self):
        tokens = fast.path_tokens("src/papersmith/core/init.py", {"init.py": 1})
        self.assertIn("src/papersmith/core/init.py", tokens)
        self.assertIn("init.py", tokens)
        self.assertIn("papersmith.core.init", tokens)

    def test_filename_token_only_when_basename_is_unique(self):
        path = "src/papersmith/core/init.py"
        self.assertNotIn("init.py", fast.path_tokens(path, {"init.py": 2}))
        self.assertNotIn("init.py", fast.path_tokens(path, {}))
        self.assertNotIn("init.py", fast.path_tokens(path))
        self.assertIn(path, fast.path_tokens(path, {"init.py": 2}))

    def test_generic_filenames_do_not_select(self):
        counts = {"README.md": 9, "SKILL.md": 30}
        picked = fast.select_tests(
            ["docs/README.md"], {"tests/test_r.py": "see README.md here"},
            basename_counts=counts, guards=())
        self.assertEqual(picked, {})

    def test_no_bare_short_stems(self):
        tokens = fast.path_tokens("src/papersmith/core/init.py")
        for stem in ("init", "core", "papersmith"):
            self.assertNotIn(stem, tokens)

    def test_skill_file_adds_skill_token(self):
        tokens = fast.path_tokens("skills/sota-graph/check.py")
        self.assertIn("skills/sota-graph", tokens)
        self.assertIn("skills/sota-graph/check.py", tokens)

    def test_core_skill_gets_dotted_form(self):
        tokens = fast.path_tokens("skills/_core/lib/util.py")
        self.assertIn("skills._core.lib.util", tokens)

    def test_package_init_maps_to_package(self):
        tokens = fast.path_tokens("src/papersmith/core/__init__.py")
        self.assertIn("papersmith.core", tokens)

    def test_top_level_package_init_is_not_a_bare_stem_token(self):
        tokens = fast.path_tokens("src/papersmith/__init__.py")
        self.assertNotIn("papersmith", tokens)

    def test_non_python_code_file_has_no_dotted_form(self):
        tokens = fast.path_tokens("scripts/run.sh", {"run.sh": 1})
        self.assertEqual(sorted(tokens), ["run.sh", "scripts/run.sh"])


class SelectionTests(unittest.TestCase):
    TEXTS = {
        "tests/test_a.py": "uses papersmith.core.init heavily",
        "tests/test_b.py": "mentions skills/sota-graph in a path",
        "tests/test_c.py": "nothing relevant, only the word init",
    }

    def select(self, changed, texts=None, guards=(), guards_only=False):
        return fast.select_tests(
            changed, self.TEXTS if texts is None else texts,
            guards=guards, guards_only=guards_only)

    def test_changed_test_is_taken_as_is(self):
        picked = self.select(["tests/test_c.py"])
        self.assertEqual(picked, {"tests/test_c.py": "changed test"})

    def test_non_test_under_tests_is_not_a_test(self):
        self.assertEqual(self.select(["tests/helpers.py"]), {})

    def test_dotted_module_token_selects_mentioning_test(self):
        picked = self.select(["src/papersmith/core/init.py"])
        self.assertEqual(list(picked), ["tests/test_a.py"])
        self.assertIn("papersmith.core.init", picked["tests/test_a.py"])

    def test_bare_stem_does_not_overselect(self):
        picked = self.select(["src/papersmith/core/init.py"])
        self.assertNotIn("tests/test_c.py", picked)

    def test_skill_token_selects(self):
        picked = self.select(["skills/sota-graph/check.py"])
        self.assertEqual(picked["tests/test_b.py"], "mentions skills/sota-graph")

    def test_guards_always_added_and_ordered_last(self):
        picked = self.select(["tests/test_c.py"], guards=("tests/test_a.py",))
        self.assertEqual(list(picked), ["tests/test_c.py", "tests/test_a.py"])
        self.assertEqual(picked["tests/test_a.py"], "guard")

    def test_guard_does_not_override_better_reason(self):
        picked = self.select(["tests/test_a.py"], guards=("tests/test_a.py",))
        self.assertEqual(picked["tests/test_a.py"], "changed test")

    def test_guards_only_ignores_changes(self):
        picked = self.select(["tests/test_c.py"], guards=("tests/test_a.py",),
                             guards_only=True)
        self.assertEqual(picked, {"tests/test_a.py": "guard"})

    def test_guard_node_id_is_kept_verbatim(self):
        guard = "tests/test_a.py::SomeClass"
        picked = self.select([], guards=(guard,))
        self.assertEqual(picked, {guard: "guard"})

    def test_deleted_changed_test_is_not_selected_when_absent(self):
        # a changed test that no longer exists is simply not in the texts map
        picked = fast.select_tests(["tests/test_gone.py"], {}, guards=())
        self.assertEqual(picked, {})


class NonCodeTests(unittest.TestCase):
    def test_non_code_paths_have_no_tokens(self):
        for path in ("README.md", "package.json", "CHANGELOG.md", "a/b.txt",
                     "pyproject.toml", "x/ci.yml", "x/ci.yaml", "dir/.gitkeep",
                     "odd/tasks/f.py", "docs/x.py", "openspec/specs/y.py"):
            self.assertEqual(fast.path_tokens(path, {}), [], path)

    def test_non_code_change_selects_nothing_but_guards(self):
        texts = {"tests/test_r.py": "README.md package.json docs/guide.md"}
        picked = fast.select_tests(
            ["README.md", "package.json", "docs/guide.md"], texts,
            basename_counts={}, guards=("tests/test_g.py",))
        self.assertEqual(picked, {"tests/test_g.py": "guard"})

    def test_changed_test_under_docs_like_name_is_still_selected(self):
        picked = fast.select_tests(
            ["tests/test_r.py"], {"tests/test_r.py": ""}, guards=())
        self.assertEqual(picked, {"tests/test_r.py": "changed test"})

    def test_python_files_still_tokenise(self):
        self.assertTrue(fast.path_tokens("scripts/tool.py", {}))


class RedundantGuardTests(unittest.TestCase):
    def test_class_guard_dropped_when_whole_file_selected(self):
        guard = "tests/test_a.py::Cls"
        picked = fast.select_tests(
            ["tests/test_a.py"], {"tests/test_a.py": ""}, guards=(guard,))
        self.assertEqual(list(picked), ["tests/test_a.py"])

    def test_class_guard_kept_when_file_not_selected(self):
        guard = "tests/test_a.py::Cls"
        picked = fast.select_tests([], {"tests/test_a.py": ""}, guards=(guard,))
        self.assertEqual(list(picked), [guard])


class SlowTests(unittest.TestCase):
    def test_slow_tests_declared_with_seconds(self):
        ids = dict(fast.SLOW_TESTS)
        self.assertEqual(ids[
            "tests/test_proposal_implementation.py::StepCommandTests::"
            "test_a_step_killed_mid_run_leaves_a_started_line_with_no_partner"], 120)
        self.assertEqual(len(ids), 3)

    def test_deselect_only_slow_tests_whose_file_is_selected(self):
        slow = (("tests/test_a.py::T::t1", 5), ("tests/test_b.py::T::t2", 9))
        picked = {"tests/test_a.py": "x", "tests/test_c.py::K": "guard"}
        got = fast.slow_to_deselect(picked, with_slow=False, slow=slow)
        self.assertEqual(got, [("tests/test_a.py::T::t1", 5)])

    def test_class_guard_does_not_pull_in_other_classes_slow_tests(self):
        slow = (("tests/test_a.py::Other::t1", 5), ("tests/test_a.py::Cls::t2", 7))
        got = fast.slow_to_deselect({"tests/test_a.py::Cls": "guard"},
                                    with_slow=False, slow=slow)
        self.assertEqual(got, [("tests/test_a.py::Cls::t2", 7)])

    def test_with_slow_deselects_nothing(self):
        slow = (("tests/test_a.py::T::t1", 5),)
        self.assertEqual(
            fast.slow_to_deselect({"tests/test_a.py": "x"}, with_slow=True, slow=slow), [])

    def test_command_carries_deselect_flags(self):
        cmd = fast.pytest_command("/p", ["tests/test_a.py"], ["tests/test_a.py::T::t1"])
        self.assertEqual(cmd[-3:], ["tests/test_a.py", "--deselect", "tests/test_a.py::T::t1"])


class WarningTests(unittest.TestCase):
    def test_warns_above_twelve_files(self):
        many = {f"tests/test_{i}.py": "x" for i in range(13)}
        self.assertIn("--guards-only", fast.size_warning(many))

    def test_no_warning_at_twelve(self):
        many = {f"tests/test_{i}.py": "x" for i in range(12)}
        self.assertEqual(fast.size_warning(many), "")


class GuardSetTests(unittest.TestCase):
    def test_declared_guards_exist_in_the_repo(self):
        for guard in fast.GUARDS:
            self.assertTrue((FORGE / guard.split("::")[0]).exists(), guard)

    def test_guard_set_is_the_agreed_one(self):
        self.assertIn("tests/test_forge_gate.py", fast.GUARDS)
        self.assertIn(
            "tests/test_proposal_implementation.py::ReportFirstSectionProseTests",
            fast.GUARDS)


class CommandTests(unittest.TestCase):
    def test_pytest_command_shape(self):
        cmd = fast.pytest_command("/x/python", ["tests/test_a.py"])
        self.assertEqual(
            cmd, ["/x/python", "-m", "pytest", "-q", "--no-header",
                  "-p", "no:cacheprovider", "tests/test_a.py"])

    def test_interpreter_falls_back_to_sys_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            py, label = fast.resolve_interpreter(Path(tmp))
        self.assertEqual(py, sys.executable)
        self.assertIn("sys.executable", label)

    def test_interpreter_prefers_gate_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "setup_env.py").write_text(
                'from pathlib import Path\n'
                'PROJECT_ROOT = Path(__file__).resolve().parent.parent\n'
                'MAMBA_ROOT = PROJECT_ROOT / ".micromamba"\n'
                'ENV_NAME = "papersmith"\n')
            gate = root / ".micromamba" / "envs" / "papersmith" / "bin"
            gate.mkdir(parents=True)
            (gate / "python").write_text("")
            py, label = fast.resolve_interpreter(root)
        self.assertTrue(py.endswith("envs/papersmith/bin/python"))
        self.assertIn("gate", label)

    def test_reminder_is_not_a_green_claim(self):
        self.assertEqual(
            fast.REMINDER,
            "fast tier only - run `npm run test:all` (or let CI run) before merging")


def _git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd, check=True, capture_output=True)


class ListEndToEndTests(unittest.TestCase):
    def make_repo(self, root):
        _git(root, "init", "-q")
        (root / "tests").mkdir()
        (root / "src" / "papersmith" / "core").mkdir(parents=True)
        (root / "src" / "papersmith" / "core" / "init.py").write_text("x = 1\n")
        (root / "tests" / "test_old.py").write_text(
            "# exercises papersmith.core.init\n")
        (root / "tests" / "test_other.py").write_text("# unrelated\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "base")
        (root / "src" / "papersmith" / "core" / "init.py").write_text("x = 2\n")
        (root / "tests" / "test_new.py").write_text("# brand new, untracked\n")
        # a committed change that only --since can see
        (root / "tests" / "test_other.py").write_text("# unrelated, edited\n")
        _git(root, "add", "tests/test_other.py")
        _git(root, "commit", "-q", "-m", "second")
        (root / "src" / "papersmith" / "core" / "init.py").write_text("x = 3\n")

    def run_list(self, root, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--list", "--root", str(root), *extra],
            capture_output=True, text=True)

    def test_default_is_uncommitted_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            proc = self.run_list(root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn("tests/test_new.py  <- changed test", out)
        self.assertIn("tests/test_old.py  <- mentions papersmith.core.init", out)
        self.assertNotIn("test_other.py", out)  # committed, not uncommitted
        self.assertIn("base: uncommitted work (HEAD)", out)
        self.assertIn(fast.REMINDER, out)

    def test_list_states_deselection_policy_in_real_repo_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            (root / "tests" / "test_skill_audit.py").write_text("# x\n")
            proc = self.run_list(root)
            slow = self.run_list(root, "--with-slow")
        self.assertIn("deselected", proc.stdout)
        self.assertIn("full gate still runs them", proc.stdout)
        self.assertNotIn("deselected", slow.stdout)

    def test_since_adds_committed_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            proc = self.run_list(root, "--since", "HEAD~1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("tests/test_other.py  <- changed test", proc.stdout)
        self.assertIn("base: uncommitted work + HEAD~1...HEAD", proc.stdout)


if __name__ == "__main__":
    unittest.main()

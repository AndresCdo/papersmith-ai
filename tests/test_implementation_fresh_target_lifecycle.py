"""B5: a freshly initialised target walks env -> plan -> apply -> materialize.

Three things stood in the way on a `git init` target:

- `env` built `.venv/` before anything ignored it, so the very next `plan`
  refused `DIRTY_WORKTREE` on the skill's own virtualenv;
- the `pip install -e` that `env` prints writes `src/<dist>.egg-info/`, which
  nothing ignored either, so the next clean-requiring command refused again;
- the plan approved before `apply` is `PLAN_STALE` for `materialize`, because
  `apply` carried out its `createDirs`. That one is the gate working (the plan
  described a tree that no longer exists); the refusal now says so.

The guards themselves are unchanged: anything the skill did not produce still
dirties the tree, and a stale plan still refuses.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
NAME = "Fresh-Method"


def run_cli(*args: str) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")}
    proc = subprocess.run([sys.executable, str(CLI), *args], capture_output=True,
                          text=True, env=env, cwd=FORGE)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"no JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from error


def porcelain(target: Path) -> str:
    return subprocess.run(["git", "-C", str(target), "status", "--porcelain"],
                          capture_output=True, text=True, check=True).stdout


def fresh_target(case: unittest.TestCase, suffix: str) -> Path:
    target = FORGE / "implementations" / f"_fresh_lifecycle_{suffix}_{os.getpid()}"
    shutil.rmtree(target, ignore_errors=True)
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    for key, value in (("user.email", "test@example.invalid"), ("user.name", "test")):
        subprocess.run(["git", "-C", str(target), "config", key, value], check=True)
    case.addCleanup(shutil.rmtree, target, ignore_errors=True)
    return target


class EnvLeavesAFreshTargetCleanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        holder = unittest.TestCase()
        cls._cleanups_holder = holder
        cls.target = fresh_target(holder, "env")
        cls.env_result = run_cli("env", "--target", str(cls.target), "--python", sys.executable)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cleanups_holder.doCleanups()

    def test_env_succeeds(self) -> None:
        self.assertEqual(self.env_result.get("status"), "created", self.env_result)

    def test_the_virtualenv_does_not_dirty_the_tree(self) -> None:
        self.assertTrue((self.target / ".venv" / "pyvenv.cfg").exists())
        self.assertEqual(porcelain(self.target), "")

    def test_plan_runs_right_after_env(self) -> None:
        result = run_cli("plan", "--target", str(self.target), "--name", NAME)
        self.assertNotEqual(result.get("code"), "DIRTY_WORKTREE", result)
        self.assertIn("createDirs", result)

    def test_the_editable_install_metadata_does_not_dirty_the_tree(self) -> None:
        metadata = self.target / "src" / "fresh_method.egg-info"
        metadata.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.target / "src", ignore_errors=True)
        (metadata / "PKG-INFO").write_text("Name: fresh-method\n", encoding="utf-8")
        self.assertEqual(porcelain(self.target), "")

    def test_env_writes_no_tracked_file_and_is_idempotent(self) -> None:
        self.assertFalse((self.target / ".gitignore").exists(),
                         "env must not leave an untracked file of its own")
        exclude = self.target / ".git" / "info" / "exclude"
        before = exclude.read_text(encoding="utf-8")
        again = run_cli("env", "--target", str(self.target), "--python", sys.executable)
        self.assertEqual(again.get("status"), "present", again)
        self.assertEqual(exclude.read_text(encoding="utf-8"), before)
        for entry in (".venv/", "*.egg-info/"):
            self.assertEqual(before.splitlines().count(entry), 1, before)

    def test_somebody_elses_untracked_file_still_dirties_the_tree(self) -> None:
        stray = self.target / "notes.txt"
        stray.write_text("x\n", encoding="utf-8")
        self.addCleanup(stray.unlink)
        result = run_cli("plan", "--target", str(self.target), "--name", NAME)
        self.assertEqual(result.get("code"), "DIRTY_WORKTREE", result)


class PlanApplyMaterializeLifecycleTests(unittest.TestCase):
    def test_materialize_needs_the_plan_taken_after_apply(self) -> None:
        target = fresh_target(self, "walk")
        scratch = target / ".git" / "plans"
        scratch.mkdir()
        first = scratch / "before-apply.json"
        first.write_text(json.dumps(run_cli("plan", "--target", str(target), "--name", NAME)),
                         encoding="utf-8")
        applied = run_cli("apply", "--target", str(target), "--name", NAME, "--plan", str(first))
        self.assertEqual(applied.get("status"), "applied", applied)

        stale = run_cli("materialize", "--target", str(target), "--name", NAME,
                        "--stage", "scaffold", "--plan", str(first), "--seed", "0")
        self.assertEqual(stale.get("code"), "PLAN_STALE", stale)
        self.assertIn("once `apply` has run", stale["detail"])

        second = scratch / "after-apply.json"
        second.write_text(json.dumps(run_cli("plan", "--target", str(target), "--name", NAME)),
                          encoding="utf-8")
        done = run_cli("materialize", "--target", str(target), "--name", NAME,
                       "--stage", "scaffold", "--plan", str(second), "--seed", "0")
        self.assertEqual(done.get("status"), "materialized", done)

    def test_the_ignore_file_a_target_carries_covers_editable_metadata(self) -> None:
        target = fresh_target(self, "ignore")
        plan = target / ".git" / "plan.json"
        plan.write_text(json.dumps(run_cli("plan", "--target", str(target), "--name", NAME)),
                        encoding="utf-8")
        applied = run_cli("apply", "--target", str(target), "--name", NAME, "--plan", str(plan))
        self.assertEqual(applied.get("status"), "applied", applied)
        lines = (target / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("*.egg-info/", lines)
        self.assertIn(".venv/", lines)


if __name__ == "__main__":
    unittest.main()

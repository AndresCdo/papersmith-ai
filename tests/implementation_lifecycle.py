"""A fresh implementation target walked through plan, apply, the scaffold stage
and the step-8 declaration, through the real CLI -- shared by the object-stage
and kit-token tests. Not a test module itself (no `test_` prefix).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
NAME = "Fresh-Method"
PACKAGE = "Fresh_Method"
REVISION = "draft-1.md"
REVISION_TEXT = "## 3\n\n$$\na = b \\tag{3.1}\n$$\n"


class Target:
    """One target under `implementations/`, removed by the owning test case."""

    def __init__(self, case: unittest.TestCase, suffix: str) -> None:
        self.proposals = Path(tempfile.mkdtemp())
        case.addCleanup(shutil.rmtree, self.proposals, ignore_errors=True)
        (self.proposals / REVISION).write_text(REVISION_TEXT, encoding="utf-8")
        self.root = FORGE / "implementations" / f"_lifecycle_{suffix}_{os.getpid()}_{id(case)}"
        shutil.rmtree(self.root, ignore_errors=True)
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for key, value in (("user.email", "test@example.invalid"), ("user.name", "test")):
            subprocess.run(["git", "-C", str(self.root), "config", key, value], check=True)
        self.plans = self.root / ".git" / "plans"
        self.plans.mkdir()
        self._count = 0

    def cli(self, *args: str) -> dict:
        env = {k: v for k, v in os.environ.items()
               if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")}
        env["IMPLEMENTATION_PROPOSALS"] = str(self.proposals)
        proc = subprocess.run([sys.executable, str(CLI), *args], capture_output=True,
                              text=True, env=env, cwd=FORGE)
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"no JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from error

    def plan(self, *extra: str) -> str:
        self._count += 1
        path = self.plans / f"plan-{self._count}.json"
        path.write_text(json.dumps(self.cli("plan", "--target", str(self.root),
                                            "--name", NAME, *extra)), encoding="utf-8")
        return str(path)

    def commit(self, message: str = "step") -> None:
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-q", "--allow-empty",
                        "-m", message], check=True)

    def materialize(self, *args: str) -> dict:
        return self.cli("materialize", "--target", str(self.root), "--name", NAME, *args)

    def scaffold(self, *plan_extra: str) -> dict:
        applied = self.cli("apply", "--target", str(self.root), "--name", NAME,
                           "--plan", self.plan(*plan_extra))
        assert applied.get("status") == "applied", applied
        done = self.materialize("--stage", "scaffold", "--plan", self.plan(*plan_extra),
                                "--seed", "7")
        assert done.get("status") == "materialized", done
        self.commit("scaffold")
        return done

    def declare(self) -> None:
        init = self.root / "src" / PACKAGE / "__init__.py"
        text = init.read_text(encoding="utf-8")
        text = re.sub(r'^    "revision": "",$', f'    "revision": "{REVISION}",', text,
                      count=1, flags=re.M)
        text = re.sub(r'^    "premises": \{\},$', '    "premises": {"metric": "m"},', text,
                      count=1, flags=re.M)
        init.write_text(text, encoding="utf-8")
        sealed = self.materialize("--authored", f"src/{PACKAGE}/__init__.py")
        assert sealed.get("status") == "authored", sealed
        self.commit("declare")

    def objects(self, *extra: str) -> dict:
        return self.materialize("--stage", "objects", "--plan", self.plan(), "--seed", "7",
                                *extra)

    def verify(self) -> dict:
        return self.cli("verify", "--target", str(self.root), "--name", NAME,
                        "--revision", REVISION)

    def receipt(self) -> dict:
        path = self.root / ".implementation" / "materialization.json"
        return {e["path"]: e for e in json.loads(path.read_text(encoding="utf-8"))["entries"]}

"""`adopt`'s survey resolves its target against the canonical workspace.

Regression for issue #52: `_adopt_workspace_target` named `WORKSPACE`
without importing it, so every survey crashed with `NameError` before the
containment check could refuse or admit the target. Both outcomes of that
check are pinned: a target outside the workspace is refused, and a valid
one is surveyed into a committed copy plus its adoption plan.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

#: The survey commits its copy; pin who commits so the test never depends on
#: the machine's git identity (the seal harness pins it the same way).
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Adopt Test", "GIT_AUTHOR_EMAIL": "adopt@test.invalid",
    "GIT_COMMITTER_NAME": "Adopt Test", "GIT_COMMITTER_EMAIL": "adopt@test.invalid",
}

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"


class AdoptWorkspaceTargetTest(unittest.TestCase):
    def _run_cli(self, *args):
        proc = subprocess.run(
            [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=FORGE,
            env={**os.environ, **GIT_IDENTITY},
        )
        payload = json.loads(proc.stdout or "{}")
        return payload, proc.returncode, proc

    def test_a_target_outside_the_workspace_is_refused_not_a_name_error(self):
        source = Path(tempfile.mkdtemp())
        outside = Path(tempfile.mkdtemp()) / "Demo"
        self.addCleanup(shutil.rmtree, source, ignore_errors=True)
        self.addCleanup(shutil.rmtree, outside.parent, ignore_errors=True)
        (source / "main.py").write_text("print('hi')\n", encoding="utf-8")

        payload, code, proc = self._run_cli(
            "adopt", "--target", str(outside), "--name", "Demo", "--source", str(source)
        )

        self.assertNotIn("NameError", proc.stderr)
        self.assertEqual(code, 2, proc.stdout + proc.stderr)
        self.assertEqual(payload.get("code"), "OUTSIDE_WORKSPACE", proc.stdout)
        self.assertFalse(outside.exists())
        self.assertEqual(sorted(p.name for p in source.iterdir()), ["main.py"])


    def test_adopt_valid_source_reaches_workspace_target(self):
        source = Path(tempfile.mkdtemp(prefix="adopt-source-"))
        self.addCleanup(shutil.rmtree, source, ignore_errors=True)
        (source / "main.py").write_text("print('hi')\n", encoding="utf-8")
        target = FORGE / "implementations" / f"_adopt_survey_{os.getpid()}_{uuid.uuid4().hex[:8]}"
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)

        payload, code, proc = self._run_cli(
            "adopt", "--target", str(target), "--name", "Demo", "--source", str(source)
        )

        self.assertNotIn("NameError", proc.stderr)
        self.assertEqual(code, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["status"], "surveyed", proc.stdout)
        self.assertEqual(Path(payload["target"]), target.resolve())
        plan_path = target / "adoption-plan.json"
        self.assertEqual(Path(payload["plan"]), plan_path.resolve())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual((plan["command"], plan["mode"]), ("adopt", "survey"))
        self.assertEqual(plan["name"], payload["name"])
        self.assertEqual(plan["sourceTreeHash"], payload["sourceTreeHash"])
        self.assertEqual((target / "main.py").read_bytes(), b"print('hi')\n")
        head = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(payload["commit"], head)
        self.assertEqual(sorted(p.name for p in source.iterdir()), ["main.py"])


if __name__ == "__main__":
    unittest.main()

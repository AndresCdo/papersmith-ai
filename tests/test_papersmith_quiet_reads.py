"""`status` and `audit` stay quiet about projection notes unless asked.

An intentionally malformed workspace skill provides a real generator note.
The Pi web tools now map to pi-web-access, so their old missing-tool note no
longer exists. Read-only commands still collect other projection notes:

- `status --json` carries them under `framework.generator_notes`;
- `status --verbose` and `audit --check-drift --verbose` print them to stderr;
- by default neither prints them.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

from papersmith.core import init as init_module
from papersmith.core import status as status_module

NOTE = "skipping skill 'quiet-read-probe': malformed front matter"
SRC = Path(__file__).resolve().parents[1] / "src"


def _cli(*argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC), env.get("PYTHONPATH")]))
    return subprocess.run([sys.executable, "-W", "default", "-m", "papersmith.cli", *argv],
                          capture_output=True, text=True, env=env)


class QuietReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._holder = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls._holder.name).resolve() / "quiet-paper"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            init_module.initialize(cls.workspace, run_npm=False, run_env=False)
        cls.init_warnings = [str(w.message) for w in caught]
        invalid = cls.workspace / "skills" / "quiet-read-probe"
        invalid.mkdir()
        (invalid / "SKILL.md").write_text("no front matter\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._holder.cleanup()

    def test_the_fixture_actually_has_a_note_to_hide(self) -> None:
        self.assertFalse(any("has no Pi tool" in message for message in self.init_warnings))
        notes = status_module.status(self.workspace)["framework"]["generator_notes"]
        self.assertIn(NOTE, notes)

    def test_status_warns_nothing_and_keeps_the_notes(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            snapshot = status_module.status(self.workspace)
        self.assertEqual([str(w.message) for w in caught if NOTE in str(w.message)], [])
        notes = snapshot["framework"]["generator_notes"]
        self.assertTrue(any(NOTE in note for note in notes), notes)

    def test_status_prints_nothing_to_stderr_by_default(self) -> None:
        ran = _cli("status", str(self.workspace))
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertNotIn(NOTE, ran.stderr + ran.stdout)

    def test_status_verbose_prints_the_notes(self) -> None:
        ran = _cli("status", str(self.workspace), "--verbose")
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertIn(NOTE, ran.stderr)

    def test_audit_prints_nothing_by_default(self) -> None:
        ran = _cli("audit", str(self.workspace), "--check-drift")
        self.assertNotIn(NOTE, ran.stderr + ran.stdout)
        self.assertIn("drift: clean", ran.stdout, ran.stderr)

    def test_audit_verbose_prints_the_notes(self) -> None:
        ran = _cli("audit", str(self.workspace), "--check-drift", "--verbose")
        self.assertIn(NOTE, ran.stderr)
        self.assertIn("drift: clean", ran.stdout, ran.stderr)


if __name__ == "__main__":
    unittest.main()

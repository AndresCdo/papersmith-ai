"""E5: `status` and `audit` stay quiet about projection notes unless asked.

Projecting the Claude agents into Pi drops tools Pi has no counterpart for
(`tool 'WebSearch' has no Pi tool; not granted`). That note belongs to the
moment the projection is written -- `init` and `upgrade` -- but `status` and
`audit --check-drift` re-render the projections to compare them, and printed
the same multi-line `UserWarning` on every call, where it reads like a fault
in a read-only command.

Now the read-only commands collect those notes instead of warning:

- `status --json` carries them under `framework.generator_notes`;
- `status --verbose` and `audit --check-drift --verbose` print them to stderr;
- by default neither prints them;
- `init` and `upgrade`, which write the projections, still emit them.
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

NOTE = "has no Pi tool"
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

    @classmethod
    def tearDownClass(cls) -> None:
        cls._holder.cleanup()

    def test_the_fixture_actually_has_a_note_to_hide(self) -> None:
        """Without a dropped tool there is nothing to be quiet about, and every
        test below would pass for nothing."""
        self.assertTrue(any(NOTE in message for message in self.init_warnings),
                        "init no longer emits the projection note it writes")

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

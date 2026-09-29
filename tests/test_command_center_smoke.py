"""The command-center smoke script actually runs in CI, not just exists.

`cli-paper-wiring-smoke.sh` is only existence-checked today; this wrapper
subprocess-runs the end-to-end command-center smoke so a broken dashboard
server, SSE channel, or wiring endpoint fails the suite instead of shipping.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "command-center-smoke.sh"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


@unittest.skipUnless(
    VENV_PYTHON.is_file() and os.access(VENV_PYTHON, os.X_OK),
    "the smoke runs the workspace's .venv/bin/python, the documented runner",
)
class CommandCenterSmokeTests(unittest.TestCase):
    def test_smoke_script_passes_end_to_end(self) -> None:
        self.assertTrue(SCRIPT.is_file(), f"missing {SCRIPT}")
        self.assertTrue(os.access(SCRIPT, os.X_OK), f"{SCRIPT} is not executable")

        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("command-center smoke: ok", output)
        self.assertIn("payload contract: ok", output)
        self.assertIn("wiring smoke runner: ok", output)

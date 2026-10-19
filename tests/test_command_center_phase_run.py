"""`/api/phase/run`'s compile branch reaches its compiler.

Regression: the branch called `os.environ.copy()` while `server.py` never
imported `os`, so every compile request answered 500 with
`name 'os' is not defined` before any compiler was invoked.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from skills._core.command_center import server


class _JsonRequest:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.headers: dict = {}

    async def json(self) -> dict:
        return self._payload


class PhaseRunCompileTests(unittest.TestCase):
    def test_compile_phase_invokes_the_compiler_with_an_inherited_env(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        app = server.create_app(root)
        endpoint = next(
            r.endpoint for r in app.routes if getattr(r, "path", None) == "/api/phase/run"
        )

        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(stdout="", returncode=0)

        with mock.patch.object(server.subprocess, "run", side_effect=fake_run):
            response = asyncio.run(endpoint(_JsonRequest({"phase_id": "9"})))

        body = json.loads(bytes(response.body).decode("utf-8"))
        self.assertTrue(body.get("ok"), body)
        self.assertTrue(calls, "the compiler was never invoked")
        self.assertEqual(calls[0][0][0], "pdflatex")
        self.assertIn("PATH", calls[0][1]["env"])


if __name__ == "__main__":
    unittest.main()

"""Scripts the CLI launches write no bytecode into the workspace.

A workspace's `skills/` is a kit copy that `upgrade` synchronizes and
`status`/`audit` hash. A bridged skill script that imports a sibling module
used to leave `skills/<skill>/scripts/__pycache__/` behind, because the
child inherited the parent environment unchanged. Every Python child the CLI
spawns for a workspace now carries `PYTHONDONTWRITEBYTECODE=1`, the rule the
MCP bridge and the dashboard child already followed.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from papersmith.bridges import python as python_bridge
from papersmith.core import executor


class _Case(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("PYTHONDONTWRITEBYTECODE", None)

    def new_tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()


class RunScriptTests(_Case):
    def test_a_bridged_script_leaves_no_pycache_under_skills(self) -> None:
        workspace = self.new_tmp()
        scripts = workspace / "skills" / "demo" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "helper.py").write_text("VALUE = 7\n", encoding="utf-8")
        (scripts / "entry.py").write_text(
            "import os, sys\nimport helper\n"
            "print(helper.VALUE, os.environ.get('PYTHONDONTWRITEBYTECODE'), "
            "sys.dont_write_bytecode)\n",
            encoding="utf-8")
        result = python_bridge.run_script(workspace, "skills/demo/scripts/entry.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["7", "1", "True"])
        self.assertEqual(list(workspace.rglob("__pycache__")), [])

    def test_an_explicit_caller_environment_still_wins(self) -> None:
        captured: dict = {}

        def fake_run(command, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(command, 0, "", "")

        workspace = self.new_tmp()
        (workspace / "s.py").write_text("", encoding="utf-8")
        with mock.patch.object(python_bridge.subprocess, "run", fake_run):
            python_bridge.run_script(workspace, "s.py", env={"PAPER": "1"})
        self.assertEqual(captured["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(captured["env"]["PAPER"], "1")


class ExecutorTests(_Case):
    def capture(self) -> list[dict]:
        seen: list[dict] = []

        def fake_run(command, **kwargs):
            seen.append(kwargs)
            return subprocess.CompletedProcess(command, 0)

        patcher = mock.patch.object(executor.subprocess, "run", fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)
        return seen

    def test_a_local_job_carries_the_flag(self) -> None:
        seen = self.capture()
        job = {"command": [sys.executable, "-c", "pass"], "env": {"X": "1"}, "shard_value": None}
        executor._local_job(self.new_tmp(), "smoke", "job-1", job, {})
        self.assertEqual(seen[0]["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(seen[0]["env"]["X"], "1")

    def test_a_kaggle_submission_child_carries_the_flag(self) -> None:
        seen = self.capture()
        workspace = self.new_tmp()
        yaml = {
            "execution_profiles": {"train": {"entrypoint": f"{shlex.quote(sys.executable)} run.py"}},
            "compute_targets": {"default": "pool",
                                "targets": {"pool": {"provider": "kaggle"}}},
        }
        jobs = [{"command": [], "command_text": "", "entrypoint": "python run.py", "env": {},
                 "shard_value": None, "target": "pool"}]
        with mock.patch.object(executor.config, "load_papersmith_yaml", return_value=yaml), \
                mock.patch.object(executor, "_profile_jobs", return_value=jobs), \
                mock.patch.object(executor.ledger, "append"):
            executor.run_profile(workspace, "train", consent="yes")
        self.assertEqual(seen[0]["env"]["PYTHONDONTWRITEBYTECODE"], "1")


if __name__ == "__main__":
    unittest.main()

"""A repository URL from run-config.json cannot steer git (issue #56).

`repo_url` and `repo_ref` are read from a file a cloned repository controls
and reach `git ls-remote` / `git fetch`. Neither may be read as an option,
select a transport helper (`ext::`), or reach a transport outside https,
ssh and local paths. Every check here is inert: the only "helper" ever
handed to git would touch a marker file inside a temporary directory, and
the test proves it never runs.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "skills/remote-execution/scripts/jobfolder.py"
NAME = "remote_execution_jobfolder"


def _load():
    existing = sys.modules.get(NAME)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(NAME, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = module
    spec.loader.exec_module(module)
    return module


JOBFOLDER = _load()
HOSTILE = (
    "--upload-pack=touch PWNED",
    "-oProxyCommand=touch PWNED",
    "ext::sh -c touch% PWNED",
    "fd::17",
    "https://example.invalid/repo.git\n--upload-pack=x",
    "",
)
ADMISSIBLE = (
    "https://github.com/owner/repo.git",
    "ssh://git@github.com/owner/repo.git",
    "git@github.com:owner/repo.git",
    "/srv/git/origin.git",
)


class RemoteArgumentGrammarTest(unittest.TestCase):
    def test_hostile_values_are_inadmissible(self):
        for value in HOSTILE:
            self.assertIsNotNone(JOBFOLDER._inadmissible_remote_argument(value), repr(value))

    def test_ordinary_remotes_are_admissible(self):
        for value in ADMISSIBLE:
            self.assertIsNone(JOBFOLDER._inadmissible_remote_argument(value), value)


class NetworkCallSitesTest(unittest.TestCase):
    def test_reachability_probe_refuses_before_any_git_call(self):
        for value in HOSTILE:
            with unittest.mock.patch.object(JOBFOLDER, "_run_git") as run_git:
                with self.assertRaises(JOBFOLDER.JobFolderError):
                    JOBFOLDER._verify_commit_reachable("c" * 40, value, "main")
                run_git.assert_not_called()

    def test_reachability_probe_refuses_an_option_like_commit(self):
        with unittest.mock.patch.object(JOBFOLDER, "_run_git") as run_git:
            with self.assertRaises(JOBFOLDER.JobFolderError):
                JOBFOLDER._verify_commit_reachable(
                    "--upload-pack=x", "https://example.invalid/r.git", "main"
                )
            run_git.assert_not_called()

    def test_published_equivalent_never_lists_a_hostile_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in HOSTILE:
                with unittest.mock.patch.object(JOBFOLDER, "_run_git") as run_git:
                    self.assertIsNone(
                        JOBFOLDER._published_equivalent(Path(tmp), "a" * 40, value, "main", ["src"])
                    )
                    run_git.assert_not_called()
            with unittest.mock.patch.object(JOBFOLDER, "_run_git") as run_git:
                JOBFOLDER._published_equivalent(
                    Path(tmp), "a" * 40, "https://example.invalid/r.git", "--all", ["src"]
                )
                run_git.assert_not_called()

    def test_option_terminator_precedes_the_remote(self):
        calls = []

        def fake_run_git(args, *, cwd, timeout=None, extra_env=None):
            calls.append(list(args))
            return unittest.mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.object(JOBFOLDER, "_run_git", side_effect=fake_run_git):
                JOBFOLDER._published_equivalent(
                    Path(tmp), "a" * 40, "https://example.invalid/r.git", "main", ["src"]
                )
        self.assertEqual(calls[0], ["ls-remote", "--", "https://example.invalid/r.git", "main"])


class TransportAllowlistTest(unittest.TestCase):
    def test_every_git_call_carries_the_protocol_allowlist(self):
        with unittest.mock.patch.object(JOBFOLDER.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")
            JOBFOLDER._run_git(["rev-parse", "HEAD"], cwd=".")
        self.assertEqual(run.call_args.kwargs["env"]["GIT_ALLOW_PROTOCOL"], "https:ssh:file")

    def test_a_remote_helper_is_never_executed_by_real_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "PWNED"
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            with self.assertRaises(JOBFOLDER.JobFolderError):
                JOBFOLDER._run_git(
                    ["ls-remote", "--", f"ext::sh -c touch% {marker}"], cwd=tmp, timeout=20
                )
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()

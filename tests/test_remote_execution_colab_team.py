"""The Colab adapter under the TEAM model: one worker per team owner.

`<workspace>/.papersmith/team.json` declares, per owner, a Colab tier and a
per-owner state directory (`configDir`). The adapter reads only `owner`,
`accounts.colab.tier` and `accounts.colab.configDir` from it, exposes one
worker `colab:<owner>` per declared account, and runs every CLI child for
that worker with `HOME=<configDir>` plus the CLI's own global
`--config <configDir>/.config/colab-cli/sessions.json`. Measured against the
CLI source (0.6.0 and 0.7.5 alike): the OAuth token path is
`os.path.expanduser("~/.config/colab-cli/token.json")`, fixed at import from
HOME, and `--config` names the session state FILE only -- so the child's HOME
is what isolates one owner's credential from another's.

No test here reaches the network: every child is a fake `colab` executable
placed first on PATH, which logs its argv and the HOME it was given.

Run with: python3 -m unittest tests.test_remote_execution_colab_team
"""
from __future__ import annotations

import builtins
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "skills/remote-execution/scripts"


def _load_or_reuse(module_name: str, script: Path):
    """Reuse an already-loaded copy under the same name (the seam's own
    `sys.modules` discipline), so `isinstance` checks agree across suites."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


LEDGER = _load_or_reuse("remote_execution_ledger", SCRIPTS / "ledger.py")
ADAPTER = _load_or_reuse("remote_execution_adapter", SCRIPTS / "adapter.py")
PACKER = _load_or_reuse("remote_execution_packer", SCRIPTS / "packer.py")
COLAB = _load_or_reuse(
    "remote_execution_colab_adapter", SCRIPTS / "adapters" / "colab.py"
)

# The fake CLI. It strips the global `--config <file>` pair (recording it),
# answers each subcommand with the shape the adapter parses, and appends one
# JSON line per call to the log named by its own constant -- never by an
# environment variable, because the adapter forwards none but PATH and HOME.
_FAKE_COLAB = r'''#!/usr/bin/env python3
import json, os, sys
LOG = {log!r}
SESSIONS = {sessions!r}
args = sys.argv[1:]
config = None
if args[:1] == ["--config"]:
    config = args[1]
    rest = args[2:]
else:
    rest = args
with open(LOG, "a") as handle:
    handle.write(json.dumps({{"argv": args, "home": os.environ.get("HOME"),
                              "config": config}}) + "\n")
command = rest[0] if rest else ""
def option(flag):
    return rest[rest.index(flag) + 1] if flag in rest else None
if command == "sessions":
    sys.stdout.write(SESSIONS)
elif command == "new":
    sys.stdout.write("[colab] Creating session... \n[colab] Session READY.\n")
elif command == "status":
    name = option("-s")
    sys.stdout.write(
        "[%s] m-endpoint | Hardware: GPU | Shape: STANDARD | Variant: A100 "
        "| Status: IDLE\n" % name)
elif command == "exec":
    helper = os.path.basename(option("-f") or "")
    if helper == "remote-mkdir.py":
        sys.stdout.write(json.dumps({{"created": "x", "exists": True}}) + "\n")
    elif helper == "dependency-probe.py":
        sys.stdout.write(json.dumps({{"nbclient": "1", "nbformat": "1",
                                      "jupyter_client": "1"}}) + "\n")
    elif helper == "launch.py":
        sys.stdout.write(json.dumps({{"launched_pid": 4242}}) + "\n")
    else:
        sys.stdout.write(json.dumps({{"status": None, "launch": None}}) + "\n")
raise SystemExit(0)
'''


def _sessions_file(config_dir: Path) -> str:
    return str(config_dir / ".config" / "colab-cli" / "sessions.json")


class ColabTeamTestCase(unittest.TestCase):
    """A temp workspace with a team registry, per-owner 0700 state
    directories, a job folder, and the fake CLI first on PATH."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self.home = self.root / "home"
        self.home.mkdir()
        self.state = self.root / "state"
        self.dirs = {}
        for owner in ("ana", "ben", "cai"):
            directory = self.state / owner
            directory.mkdir(parents=True)
            directory.chmod(0o700)
            self.dirs[owner] = directory
        self.registry = self.root / "workspace" / ".papersmith" / "team.json"
        self.registry.parent.mkdir(parents=True)
        self.write_registry(
            [
                self.member("ana", "pro"),
                self.member("ben", "payg"),
                self.member("cai", "free"),
            ]
        )
        self.write_fake()
        env = {"PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}",
               "HOME": str(self.home)}
        patcher = unittest.mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.job_dir = self.root / "jobs" / "pilot-job"
        self.job_dir.mkdir(parents=True)
        (self.job_dir / "runner.ipynb").write_text("{}", encoding="utf-8")
        (self.job_dir / "run-config.json").write_text(
            json.dumps({"commit": "0123abcd"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- fixtures ----------------------------------------------------------

    def member(self, owner: str, tier: str, config_dir: str | None = None) -> dict:
        return {
            "owner": owner,
            "displayName": owner.title(),
            "attestedAt": "2026-10-25",
            "attestation": "owns and operates exactly one account per service listed here",
            "accounts": {
                "colab": {
                    "tier": tier,
                    "configDir": config_dir if config_dir is not None else str(self.dirs[owner]),
                }
            },
        }

    def write_registry(self, members: list[dict]) -> None:
        self.registry.write_text(
            json.dumps({"schema": 1, "members": members}), encoding="utf-8"
        )

    def write_fake(self, sessions: str = "") -> None:
        script = self.bin / "colab"
        script.write_text(
            _FAKE_COLAB.format(log=str(self.log), sessions=sessions), encoding="utf-8"
        )
        script.chmod(0o755)

    def adapter(self, registry: Path | None = None):
        return COLAB.ColabAdapter(team_registry=registry or self.registry)

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines() if line]

    def job(self, worker: str, units: list[str] | None = None):
        run_config = {"units": units} if units is not None else {}
        return ADAPTER.Job(
            entrypoint=self.job_dir / "runner.ipynb", run_config=run_config, worker=worker
        )


class OneWorkerPerOwnerTests(ColabTeamTestCase):
    def test_one_worker_per_owner_free_tier_listed_first(self) -> None:
        workers = self.adapter().workers()
        self.assertEqual(
            [worker.id for worker in workers], ["colab:cai", "colab:ana", "colab:ben"]
        )
        self.assertEqual({worker.capacity for worker in workers}, {1})

    def test_every_child_runs_with_its_owner_home_and_config(self) -> None:
        adapter = self.adapter()
        submission = adapter.submit(self.job("colab:ana"))
        self.assertTrue(submission.id.startswith("colab:ana/psmith-pilot-job-"))
        self.assertEqual(submission.worker, "colab:ana")
        adapter.list_active("colab:ben")
        calls = self.calls()
        self.assertGreater(len(calls), 5)
        ana_calls = [call for call in calls if call["home"] == str(self.dirs["ana"])]
        ben_calls = [call for call in calls if call["home"] == str(self.dirs["ben"])]
        self.assertEqual(len(ana_calls) + len(ben_calls), len(calls))
        for call in ana_calls:
            self.assertEqual(call["argv"][:2], ["--config", _sessions_file(self.dirs["ana"])])
        self.assertEqual(len(ben_calls), 1)
        self.assertEqual(
            ben_calls[0]["argv"], ["--config", _sessions_file(self.dirs["ben"]), "sessions"]
        )

    def test_child_environment_is_only_path_and_home(self) -> None:
        seen: list[dict] = []
        real_run, real_popen = subprocess.run, subprocess.Popen

        def spy_run(*args, **kwargs):
            seen.append(dict(kwargs["env"]))
            return real_run(*args, **kwargs)

        def spy_popen(*args, **kwargs):
            seen.append(dict(kwargs["env"]))
            return real_popen(*args, **kwargs)

        with unittest.mock.patch.object(COLAB.subprocess, "run", spy_run), \
                unittest.mock.patch.object(COLAB.subprocess, "Popen", spy_popen):
            self.adapter().submit(self.job("colab:ben"))
        self.assertTrue(seen)
        for env in seen:
            self.assertEqual(set(env), {"PATH", "HOME"})
            self.assertEqual(env["HOME"], str(self.dirs["ben"]))

    def test_no_file_inside_any_config_dir_is_opened(self) -> None:
        opened: list[str] = []
        real_open, real_io_open, real_os_open = builtins.open, io.open, os.open

        def record(path) -> None:
            if isinstance(path, (str, os.PathLike)):
                opened.append(os.path.realpath(os.fspath(path)))

        def spy_open(file, *args, **kwargs):
            record(file)
            return real_open(file, *args, **kwargs)

        def spy_io_open(file, *args, **kwargs):
            record(file)
            return real_io_open(file, *args, **kwargs)

        def spy_os_open(path, *args, **kwargs):
            record(path)
            return real_os_open(path, *args, **kwargs)

        with unittest.mock.patch.object(builtins, "open", spy_open), \
                unittest.mock.patch.object(io, "open", spy_io_open), \
                unittest.mock.patch.object(os, "open", spy_os_open):
            adapter = self.adapter()
            adapter.workers()
            submission = adapter.submit(self.job("colab:ana"))
            adapter.poll(submission.id)
            adapter.list_active("colab:cai")
            adapter.cancel(submission.id)
        self.assertTrue(opened, "the spy must have seen the registry read at least")
        roots = [os.path.realpath(str(directory)) for directory in self.dirs.values()]
        inside = [path for path in opened
                  if any(path == root or path.startswith(root + os.sep) for root in roots)]
        self.assertEqual(inside, [])

    def test_submission_ids_route_back_to_their_owner(self) -> None:
        adapter = self.adapter()
        submission = adapter.submit(self.job("colab:cai"))
        before = len(self.calls())
        status = adapter.poll(submission.id)
        self.assertEqual(status.state, "queued")
        later = self.calls()[before:]
        self.assertTrue(later)
        self.assertEqual({call["home"] for call in later}, {str(self.dirs["cai"])})


class TierPolicyTests(ColabTeamTestCase):
    def test_free_tier_refuses_a_campaign_unit_by_name_before_any_child(self) -> None:
        adapter = self.adapter()
        with self.assertRaises(COLAB.ColabAdapterError) as caught:
            adapter.submit(self.job("colab:cai", units=["fold-1"]))
        message = str(caught.exception)
        self.assertIn("cai", message)
        self.assertIn("free", message)
        self.assertIn("running distributed computing workers", message)
        self.assertIn("https://research.google.com/colaboratory/faq.html", message)
        self.assertEqual(self.calls(), [])

    def test_campaign_refusal_names_free_workers_only(self) -> None:
        adapter = self.adapter()
        self.assertIn("free", adapter.campaign_refusal("colab:cai"))
        self.assertIsNone(adapter.campaign_refusal("colab:ana"))
        self.assertIsNone(adapter.campaign_refusal("colab:ben"))

    def test_free_tier_single_send_is_allowed(self) -> None:
        submission = self.adapter().submit(self.job("colab:cai"))
        self.assertTrue(submission.id.startswith("colab:cai/"))
        self.assertTrue(self.calls())

    def test_paid_tier_campaign_unit_is_allowed(self) -> None:
        submission = self.adapter().submit(self.job("colab:ana", units=["fold-1", "fold-2"]))
        self.assertTrue(submission.id.startswith("colab:ana/"))

    def test_a_split_campaign_skips_the_free_owner_and_uses_the_paid_ones(self) -> None:
        """`packer.distribute()` asks the adapter's `campaign_refusal` hook
        before probing a worker: the free owner is skipped by name, before
        any live probe of it, and the units land on the paid owners, so an
        idle free member never blocks the team's campaign."""
        adapter = self.adapter()
        distribution = PACKER.distribute(
            adapter=adapter, units=["u1", "u2"], ledger_lines=[], live_digest="d"
        )
        placed = {row.plan.worker for row in distribution.assignments if row.units}
        self.assertEqual(placed, {"colab:ana", "colab:ben"})
        skipped = {skip.worker: skip.reason for skip in distribution.skipped}
        self.assertIn("colab:cai", skipped)
        self.assertIn("running distributed computing workers", skipped["colab:cai"])
        ids = [adapter.submit(self.job(row.plan.worker, units=list(row.units))).id
               for row in distribution.assignments if row.units]
        self.assertEqual(sorted(i.split("/")[0] for i in ids), ["colab:ana", "colab:ben"])

    def test_a_paid_only_team_campaign_spreads_across_owners(self) -> None:
        self.write_registry([self.member("ana", "pro"), self.member("ben", "enterprise")])
        adapter = self.adapter()
        distribution = PACKER.distribute(
            adapter=adapter, units=["u1", "u2"], ledger_lines=[], live_digest="d"
        )
        ids = [adapter.submit(self.job(row.plan.worker, units=list(row.units))).id
               for row in distribution.assignments if row.units]
        self.assertEqual([i.split("/")[0] for i in ids], ["colab:ana", "colab:ben"])


class RegistryRefusalTests(ColabTeamTestCase):
    def test_duplicate_config_dir_across_owners_refuses(self) -> None:
        shared = str(self.dirs["ana"])
        self.write_registry(
            [self.member("ana", "pro"), self.member("ben", "pro", config_dir=shared + "/")]
        )
        with self.assertRaises(COLAB.ColabAdapterError) as caught:
            self.adapter().workers()
        message = str(caught.exception)
        self.assertIn("ana", message)
        self.assertIn("ben", message)
        self.assertIn("configDir", message)

    def test_duplicate_owner_refuses(self) -> None:
        self.write_registry([self.member("ana", "pro"), self.member("ana", "payg")])
        with self.assertRaises(COLAB.ColabAdapterError):
            self.adapter().workers()

    def test_unknown_tier_refuses(self) -> None:
        self.write_registry([self.member("ana", "premium")])
        with self.assertRaises(COLAB.ColabAdapterError):
            self.adapter().workers()

    def test_relative_config_dir_refuses(self) -> None:
        self.write_registry([self.member("ana", "pro", config_dir="state/ana")])
        with self.assertRaises(COLAB.ColabAdapterError):
            self.adapter().workers()

    def test_config_dir_open_to_others_refuses_before_any_child(self) -> None:
        self.dirs["ana"].chmod(0o755)
        with self.assertRaises(COLAB.ColabAdapterError) as caught:
            self.adapter().submit(self.job("colab:ana"))
        self.assertIn("0700", str(caught.exception))
        self.assertEqual(self.calls(), [])

    def test_missing_config_dir_refuses_naming_the_login(self) -> None:
        self.dirs["ben"].rmdir()
        with self.assertRaises(COLAB.ColabAdapterError) as caught:
            self.adapter().list_active("colab:ben")
        self.assertIn("HOME=", str(caught.exception))
        self.assertEqual(self.calls(), [])

    def test_unknown_or_legacy_worker_cannot_submit_in_team_mode(self) -> None:
        adapter = self.adapter()
        for worker in ("colab", "colab:zed"):
            with self.subTest(worker=worker):
                with self.assertRaises(COLAB.ColabAdapterError):
                    adapter.submit(self.job(worker))
        self.assertEqual(self.calls(), [])

    def test_members_without_a_colab_account_are_not_workers(self) -> None:
        kaggle_only = {"owner": "dee", "displayName": "Dee", "attestedAt": "2026-10-25",
                       "attestation": "x", "accounts": {"other": {"username": "dee"}}}
        self.write_registry([self.member("ana", "pro"), kaggle_only])
        self.assertEqual([w.id for w in self.adapter().workers()], ["colab:ana"])


class BackwardCompatibilityTests(ColabTeamTestCase):
    def test_no_registry_keeps_the_single_static_worker(self) -> None:
        missing = self.root / "nowhere" / ".papersmith" / "team.json"
        adapter = self.adapter(registry=missing)
        self.assertEqual(adapter.workers(), [ADAPTER.Worker(id="colab", capacity=1)])
        self.assertEqual(adapter._env_for(), {"PATH": os.environ["PATH"],
                                              "HOME": str(self.home)})
        submission = adapter.submit(self.job("colab"))
        self.assertTrue(submission.id.startswith("colab/psmith-pilot-job-"))
        calls = self.calls()
        self.assertTrue(calls)
        for call in calls:
            self.assertNotIn("--config", call["argv"])
            self.assertEqual(call["home"], str(self.home))

    def test_declared_capacity_counts_paid_owners_or_stays_static(self) -> None:
        reporter = ADAPTER.resolve_declared_capacity("colab")
        with unittest.mock.patch.object(COLAB, "DEFAULT_TEAM_REGISTRY", self.registry), \
                unittest.mock.patch.object(
                    COLAB.subprocess, "run", side_effect=AssertionError("no subprocess")):
            self.assertEqual(reporter(), (2, 1))
            self.write_registry([self.member("cai", "free")])
            self.assertEqual(reporter(), (1, 1))
            self.registry.unlink()
            self.assertEqual(reporter(), (1, 1))
            self.registry.write_text("{not json", encoding="utf-8")
            self.assertIsNone(reporter())


if __name__ == "__main__":
    unittest.main()

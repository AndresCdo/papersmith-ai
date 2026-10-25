"""The Kaggle adapter under the TEAM model: only owner-mapped accounts work.

`<workspace>/.papersmith/team.json` maps, per owner, at most one Kaggle
username (`accounts.kaggle.username`). When it maps at least one, the
adapter's `workers()` returns ONLY the stored accounts whose username an
owner maps -- one per owner. A stored account no owner maps stays stored but
is excluded with a stated reason (Kaggle staff: "the one account per person
applies to all Kaggle site use"); an owner mapping a username the store does
not hold is reported as not validated and yields no worker. With no registry,
or one mapping no Kaggle account, the worker list is exactly what it was.

No test here reaches the network: the account store is a fake
`accounts_cli.py` stand-in that prints usernames and nothing else.

Run with: python3 -m unittest tests.test_remote_execution_kaggle_team
"""
from __future__ import annotations

import importlib.util
import json
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


ADAPTER = _load_or_reuse("remote_execution_adapter", SCRIPTS / "adapter.py")
KAGGLE = _load_or_reuse(
    "remote_execution_kaggle_adapter", SCRIPTS / "adapters" / "kaggle.py"
)

STORE = ("acct-a", "acct-b", "acct-c")


class KaggleTeamWorkersTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.accounts_cli = self.tmp / "fake_accounts_cli.py"
        self._write_store(STORE)
        self.registry = self.tmp / ".papersmith" / "team.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_store(self, names) -> None:
        payload = {"accounts": [{"username": name} for name in names]}
        self.accounts_cli.write_text(
            f"import json\nprint(json.dumps({payload!r}))\n", encoding="utf-8"
        )

    def _write_registry(self, members) -> None:
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_text(
            json.dumps({"schema": 1, "members": members}), encoding="utf-8"
        )

    def _adapter(self, **extra):
        return KAGGLE.KaggleAdapter(
            accounts_cli=self.accounts_cli, team_registry=self.registry, **extra
        )

    @staticmethod
    def _member(owner: str, username: str | None = None, **more) -> dict:
        member = {"owner": owner, "displayName": owner.title(), **more}
        if username is not None:
            member["accounts"] = {"kaggle": {"username": username}}
        return member

    # -- mapped-only ----------------------------------------------------

    def test_workers_are_only_the_owner_mapped_accounts(self) -> None:
        self._write_registry([self._member("ana", "acct-c"), self._member("luis", "acct-a")])
        workers = self._adapter().workers()
        self.assertEqual([w.id for w in workers], ["acct-a", "acct-c"])
        for worker in workers:
            self.assertEqual(worker.capacity, KAGGLE.KAGGLE_WORKER_CAPACITY)

    def test_unmapped_stored_account_is_excluded_with_its_reason(self) -> None:
        self._write_registry([self._member("ana", "acct-a")])
        report = self._adapter().team_report()
        self.assertEqual(report.workers, ("acct-a",))
        excluded = dict(report.excluded)
        self.assertEqual(sorted(excluded), ["acct-b", "acct-c"])
        reason = excluded["acct-b"]
        self.assertIn("not mapped to a team owner: one account per person", reason)
        self.assertIn(
            "the one account per person applies to all Kaggle site use", reason
        )
        self.assertIn("https://www.kaggle.com/discussions/general/192527", reason)

    def test_mapped_username_absent_from_the_store_is_not_validated(self) -> None:
        self._write_registry([self._member("ana", "acct-a"), self._member("eva", "acct-z")])
        adapter = self._adapter()
        self.assertEqual([w.id for w in adapter.workers()], ["acct-a"])
        report = adapter.team_report()
        self.assertEqual([(o, u) for o, u, _ in report.not_validated], [("eva", "acct-z")])
        self.assertIn("not validated", report.not_validated[0][2])

    # -- backward compatibility -------------------------------------------

    def test_no_registry_leaves_the_worker_list_unchanged(self) -> None:
        adapter = self._adapter()
        self.assertFalse(self.registry.exists())
        self.assertEqual([w.id for w in adapter.workers()], list(STORE))
        self.assertIsNone(adapter.team_report())

    def test_registry_mapping_no_kaggle_account_leaves_list_unchanged(self) -> None:
        self._write_registry([
            self._member("ana", accounts={"colab": {"tier": "pro", "configDir": "/x"}}),
            self._member("luis"),
        ])
        adapter = self._adapter()
        self.assertEqual([w.id for w in adapter.workers()], list(STORE))
        self.assertIsNone(adapter.team_report())

    # -- one account per owner -------------------------------------------

    def test_same_username_under_two_owners_refuses(self) -> None:
        self._write_registry([self._member("ana", "acct-a"), self._member("luis", "acct-a")])
        with self.assertRaises(KAGGLE.KaggleAdapterError) as caught:
            self._adapter().workers()
        self.assertIn("acct-a", str(caught.exception))

    def test_owner_listed_twice_refuses(self) -> None:
        self._write_registry([self._member("ana", "acct-a"), self._member("ana", "acct-b")])
        with self.assertRaises(KAGGLE.KaggleAdapterError):
            self._adapter().workers()

    def test_duplicate_store_entries_yield_one_worker_per_owner(self) -> None:
        self._write_store(("acct-a", "acct-a", "acct-b"))
        self._write_registry([self._member("ana", "acct-a")])
        workers = self._adapter().workers()
        self.assertEqual([w.id for w in workers], ["acct-a"])

    def test_malformed_registry_refuses(self) -> None:
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_text("{not json", encoding="utf-8")
        with self.assertRaises(KAGGLE.KaggleAdapterError):
            self._adapter().workers()

    def test_registry_reads_only_owner_and_kaggle_username(self) -> None:
        # Unrelated fields (display name, attestation, other services) never
        # change the answer, and a Kaggle entry carrying extra keys is still
        # read for its username alone.
        self._write_registry([
            self._member("ana", "acct-b", attestation={"signed": "x"}),
        ])
        members = json.loads(self.registry.read_text(encoding="utf-8"))
        members["members"][0]["accounts"]["kaggle"]["tokenPath"] = "/nowhere/token"
        self.registry.write_text(json.dumps(members), encoding="utf-8")
        self.assertEqual([w.id for w in self._adapter().workers()], ["acct-b"])

    # -- the submission path ---------------------------------------------

    def test_submit_to_an_unmapped_account_refuses_before_any_credential(self) -> None:
        self._write_registry([self._member("ana", "acct-a")])
        job_dir = self.tmp / "job"
        job_dir.mkdir()
        entrypoint = job_dir / "runner.ipynb"
        entrypoint.write_text("{}", encoding="utf-8")
        provider = unittest.mock.Mock(side_effect=AssertionError("credential asked"))
        adapter = self._adapter(credentials=provider)
        job = ADAPTER.Job(entrypoint=entrypoint, run_config={}, worker="acct-b")
        with self.assertRaises(KAGGLE.KaggleAdapterError) as caught:
            adapter.submit(job)
        self.assertIn("not mapped to a team owner", str(caught.exception))
        provider.assert_not_called()

    def test_declared_capacity_counts_only_mapped_accounts(self) -> None:
        self._write_registry([self._member("ana", "acct-a"), self._member("eva", "acct-z")])
        with unittest.mock.patch.object(KAGGLE, "DEFAULT_ACCOUNTS_CLI", self.accounts_cli), \
                unittest.mock.patch.object(KAGGLE, "DEFAULT_TEAM_REGISTRY", self.registry):
            self.assertEqual(
                KAGGLE._declared_capacity(), (1, KAGGLE.KAGGLE_WORKER_CAPACITY)
            )

    def test_declared_capacity_without_registry_is_unchanged(self) -> None:
        with unittest.mock.patch.object(KAGGLE, "DEFAULT_ACCOUNTS_CLI", self.accounts_cli), \
                unittest.mock.patch.object(KAGGLE, "DEFAULT_TEAM_REGISTRY", self.registry):
            self.assertEqual(
                KAGGLE._declared_capacity(), (len(STORE), KAGGLE.KAGGLE_WORKER_CAPACITY)
            )


if __name__ == "__main__":
    unittest.main()

"""A populated 0.13.0 workspace upgrades to this release and keeps everything.

The workspace under test is `tests/fixtures/workspace_v0_13_0/workspace.tar.gz`,
produced by `scripts/build-v0_13_0-fixture.py` driving the 0.13.0 tree's own
CLI and engines (see `tests/fixtures/README.md`). It holds what a paper in
progress accumulates: two managed proposal revisions and one experiments
revision with their receipts, state and locks, and an implementation target
carrying the scaffold receipt, the kit's seal file, both implementation
skills' declared holders with settled items, and their position ledger.

One upgrade with today's CLI must leave every one of those bytes alone, apply
or find satisfied every registered migration, leave `audit --check-drift`
clean, and leave the engines able to read what they wrote.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from papersmith import __version__
from papersmith.cli import main
from papersmith.core import migrations, upgrade as upgrade_module

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "workspace_v0_13_0"
TARGET = "implementations/Smoother"
PACKAGE = "Smoother"

#: Every fixture file the upgrade is meant to rewrite, and why. Anything else
#: the fixture holds must come out byte-identical.
INTENDED_CHANGES = {
    ".papersmith/config.json": "upgrade rewrites `updated_at` on every run",
    ".papersmith/manifest.json": "the baseline now records this release's files",
    ".papersmith/version": "the marker moves to this release once migrations finish",
}

#: The deliberation engines and the profile each reads.
DELIBERATION_SKILLS = ("proposal-deliberation", "experimental-deliberation")
IMPLEMENTATION_HOLDERS = {
    "proposal-implementation": f"{PACKAGE}/AGREED.md",
    "experimental-implementation": f"{PACKAGE}/Experimental_AGREED.md",
}


def _listing() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in (FIXTURE / "contents.sha256").read_text(encoding="utf-8").splitlines():
        digest, relpath = line.split("  ", 1)
        entries[relpath] = digest
    return entries


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_fixture(destination: Path) -> Path:
    """The 0.13.0 workspace, extracted into ``destination/workspace``."""
    workspace = destination / "workspace"
    workspace.mkdir(parents=True)
    with tarfile.open(FIXTURE / "workspace.tar.gz") as tar:
        tar.extractall(workspace, filter="data")
    return workspace


def run_upgrade(workspace: Path) -> dict:
    """Today's upgrade, the dirty-kit override passed explicitly: the
    checkout this suite runs from may carry uncommitted edits."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return upgrade_module.upgrade(workspace, allow_dirty_kit=True)


class UpgradeOfAPopulatedV0130WorkspaceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._holder = tempfile.TemporaryDirectory()
        cls.workspace = extract_fixture(Path(cls._holder.name).resolve())
        cls.before = {relpath: _sha256(cls.workspace / relpath) for relpath in _listing()}
        cls.recorded_before = (cls.workspace / ".papersmith" / "version").read_text(
            encoding="utf-8").strip()
        cls.report = run_upgrade(cls.workspace)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._holder.cleanup()

    def test_the_fixture_is_what_its_listing_says(self) -> None:
        """The archive and the reviewable listing agree, and the workspace
        really was recorded at 0.13.0."""
        self.assertEqual(self.before, _listing())
        self.assertEqual(self.recorded_before, "0.13.0")

    def test_the_fixture_holds_every_kind_of_artifact_it_is_meant_to_test(self) -> None:
        listed = set(_listing())
        expected_prefixes = (
            ".proposal-deliberation/receipts/", ".proposal-deliberation/state/",
            ".proposal-deliberation/locks/", ".experimental-deliberation/receipts/",
            ".experimental-deliberation/state/", ".experimental-deliberation/locks/",
            "proposals/research-concept-", "experiments/experiments-",
            f"{TARGET}/.implementation/materialization.json",
            f"{TARGET}/src/{PACKAGE}/report_digest.py",
            f"{TARGET}/{PACKAGE}/.implementation/position.jsonl",
            *(f"{TARGET}/{holder}" for holder in IMPLEMENTATION_HOLDERS.values()),
        )
        for prefix in expected_prefixes:
            with self.subTest(prefix=prefix):
                self.assertTrue(any(path.startswith(prefix) for path in listed), prefix)
        revisions = [path for path in listed if path.startswith("proposals/research-concept-")]
        self.assertGreaterEqual(len(revisions), 2, "a v1 and one successor")

    def test_nothing_the_workspace_made_changes_except_what_is_listed_as_intended(self) -> None:
        changed = {relpath for relpath, digest in self.before.items()
                   if _sha256(self.workspace / relpath) != digest}
        self.assertEqual(changed, set(INTENDED_CHANGES))

    def test_the_marker_reaches_this_release(self) -> None:
        self.assertEqual(self.report["recorded_version"], __version__)

    def test_every_registered_migration_applies_or_is_already_satisfied(self) -> None:
        outcome = self.report["migrations"]
        self.assertEqual(outcome["failures"], [])
        self.assertEqual(outcome["undetermined"], [])
        reached = {entry["id"] for entry in outcome["applied"]} | set(outcome["satisfied"])
        self.assertEqual(reached, {migration.id for migration in migrations.REGISTRY})
        for entry in outcome["applied"]:
            self.assertEqual(entry["failures"], [], entry["id"])

    def test_audit_reports_no_drift_after_one_upgrade(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(["audit", str(self.workspace), "--check-drift"])
        self.assertEqual(code, 0, out.getvalue()[-2000:])
        self.assertIn("drift: clean", out.getvalue())

    def test_each_implementation_skill_still_reads_its_own_holder(self) -> None:
        for skill, holder in IMPLEMENTATION_HOLDERS.items():
            with self.subTest(skill=skill):
                completed = subprocess.run(
                    [sys.executable, f"skills/{skill}/scripts/implementation_cli.py", "verify",
                     "--target", TARGET, "--name", PACKAGE],
                    cwd=self.workspace, capture_output=True, text=True, check=False,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                self.assertEqual(completed.returncode, 0, completed.stdout[-2000:])
                payload = json.loads(completed.stdout)
                self.assertNotEqual(payload.get("status"), "refused", payload.get("detail"))
                self.assertEqual(payload["agreements"]["holders"], [holder])
                self.assertEqual(len(payload["agreements"]["open"]), 1)
                self.assertIn(f"({skill})", payload["agreements"]["open"][0])
                self.assertEqual(payload["position"]["holder"], holder)
                self.assertEqual(payload["fidelity"]["missingProvenance"], [],
                                 "the kit's seal file still owes no provenance")

    def test_each_deliberation_engine_audits_its_own_tree_clean(self) -> None:
        node = shutil.which("node")
        modules = REPO_ROOT / "node_modules"
        if node is None or not modules.is_dir():
            self.skipTest("node and the repository's node_modules are required for this leg")
        link = self.workspace / "node_modules"
        link.symlink_to(modules, target_is_directory=True)
        self.addCleanup(link.unlink)
        script = (
            "import {createJiti} from 'jiti';"
            "const root=process.cwd();"
            "const jiti=createJiti(root+'/');"
            "const audit=await jiti.import(root+'/skills/_core/deliberation/engine/consistency-audit.ts');"
            "const result=await audit.runConsistencyAudit({projectRoot:root});"
            "process.stdout.write(JSON.stringify({status:result.status,failures:result.failures}));"
        )
        for skill in DELIBERATION_SKILLS:
            with self.subTest(skill=skill):
                env = {key: value for key, value in os.environ.items()
                       if not key.startswith(("DELIBERATION_", "PROPOSAL_DELIBERATION_"))}
                env["DELIBERATION_DOMAIN_PROFILE"] = str(
                    self.workspace / "skills" / skill / "profile.ts")
                completed = subprocess.run([node, "--input-type=module", "-e", script],
                                           cwd=self.workspace, env=env, capture_output=True,
                                           text=True, check=False, timeout=180)
                self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
                result = json.loads(completed.stdout)
                self.assertEqual(result, {"status": "PASS", "failures": []})


if __name__ == "__main__":
    unittest.main()

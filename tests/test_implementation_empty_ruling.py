"""C9: an audit that found nothing can be ruled on, explicitly.

`admit` refused `NO_FINDINGS` whenever `tests/findings.py` declared an empty
list, so a target whose audit genuinely found no defect could never record
that fact and `verify` stayed at `audit: none` forever -- the same answer a
target that was never audited gets.

The fix keeps the refusal as the default: an empty ruling is recorded only by
`admit --no-findings`, an explicit act, and it is bound to the revision's
bytes exactly like any other ruling. Declared findings with the flag refuse,
so the flag can never stand in for ruling on a finding.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
NAME = "Method"
REVISION = "draft-1.md"
REVISION_TEXT = (
    "## 3\n\n$$\na = b \\tag{3.1}\n$$\n\nThroughout, the estimator is written E[x].\n"
)
ONE_FINDING = (
    "FINDINGS = [\n"
    "    {'id': 'loose', 'equations': ['3.1'], 'remedy_equations': ['3.1'],\n"
    "     'uses': ['E[x]'], 'introduces': [],\n"
    "     'adoption': {'absent': 'a = b', 'expect': ['a = c']}},\n"
    "]\n"
)


class EmptyRulingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposals = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.proposals, ignore_errors=True)
        (self.proposals / REVISION).write_text(REVISION_TEXT, encoding="utf-8")
        self.box = FORGE / "implementations" / f"_empty_ruling_{os.getpid()}_{id(self)}"
        shutil.rmtree(self.box, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        (self.box / "src" / NAME).mkdir(parents=True)
        (self.box / "tests").mkdir()
        subprocess.run(["git", "init", "-q", str(self.box)], check=True)
        (self.box / "src" / NAME / "__init__.py").write_text(
            f"__implementation__ = {{'revision': '{REVISION}', 'premises': {{}}}}\n",
            encoding="utf-8")
        self.findings("FINDINGS = []\n")

    def findings(self, text: str) -> None:
        (self.box / "tests" / "findings.py").write_text(text, encoding="utf-8")

    def run_cli(self, *args: str) -> dict:
        env = {k: v for k, v in os.environ.items()
               if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")}
        env["IMPLEMENTATION_PROPOSALS"] = str(self.proposals)
        proc = subprocess.run([sys.executable, str(CLI), *args], capture_output=True,
                              text=True, env=env, cwd=FORGE)
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"no JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from error

    def admit(self, *extra: str) -> dict:
        return self.run_cli("admit", "--target", str(self.box), "--name", NAME,
                            "--revision", REVISION, *extra)

    def audit(self) -> dict:
        return self.run_cli("verify", "--target", str(self.box), "--name", NAME,
                            "--revision", REVISION)["audit"]

    @property
    def ruling_path(self) -> Path:
        return self.box / "tests" / "admissibility.json"

    def test_an_empty_audit_still_refuses_without_the_explicit_flag(self) -> None:
        result = self.admit()
        self.assertEqual(result.get("code"), "NO_FINDINGS", result)
        self.assertIn("--no-findings", result.get("detail", ""))
        self.assertFalse(self.ruling_path.exists())
        self.assertEqual(self.audit()["status"], "none")

    def test_the_explicit_flag_records_an_empty_ruling_bound_to_the_revision(self) -> None:
        result = self.admit("--no-findings")
        self.assertEqual(result.get("status"), "no-findings", result)
        record = json.loads(self.ruling_path.read_text(encoding="utf-8"))
        self.assertEqual(record["findings"], {})
        self.assertIs(record["noFindings"], True)
        self.assertEqual(record["revision"], REVISION)
        self.assertIn("revisionSha256", record)

    def test_verify_reads_the_recorded_empty_ruling_as_an_audit_that_found_nothing(self) -> None:
        self.admit("--no-findings")
        audit = self.audit()
        self.assertEqual(audit["status"], "ok", audit)
        self.assertIs(audit.get("noFindings"), True, audit)
        self.assertEqual(audit["admissibility"]["status"], "present")

    def test_an_empty_ruling_goes_stale_with_the_revision_bytes(self) -> None:
        self.admit("--no-findings")
        (self.proposals / REVISION).write_text(REVISION_TEXT + "\nAppended.\n",
                                               encoding="utf-8")
        audit = self.audit()
        self.assertEqual(audit["status"], "incomplete", audit)
        self.assertEqual(audit["admissibility"]["status"], "stale")

    def test_the_flag_cannot_stand_in_for_ruling_on_declared_findings(self) -> None:
        self.findings(ONE_FINDING)
        result = self.admit("--no-findings")
        self.assertEqual(result.get("code"), "FINDINGS_DECLARED", result)
        self.assertFalse(self.ruling_path.exists())

    def test_an_empty_ruling_does_not_survive_a_finding_declared_afterwards(self) -> None:
        self.admit("--no-findings")
        self.findings(ONE_FINDING)
        audit = self.audit()
        self.assertNotEqual(audit["status"], "ok", audit)
        self.assertNotIn("noFindings", audit)


if __name__ == "__main__":
    unittest.main()

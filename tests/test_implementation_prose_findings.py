"""C8: a defect that lives in prose can be declared as a finding.

A finding's remedy was only ever expressible as one numbered locus rewritten
in place: the kit's `test_audit.py` demanded a non-empty remedy locus list,
`compose` substitutes at the locus's own tag, and `verify` kept asking for a
`remedy_block` for every local finding without one -- a block nobody can write
for a sentence that carries no tag. So a defect in the prose (an overstated
sentence, an undefined term in running text) could not be a finding at all.

A finding now says so explicitly with `"remedy_in_prose": True` and an empty
remedy locus list. It is admitted on the same notation and adoption checks as
any other, never asked for a `remedy_block`, and `handoff` defers it to a
deliberation session of its own (`prose-remedy`), the only place a prose
rewrite can be decided. Declaring it while also naming remedy loci is a
contradiction and is ruled inadmissible. A finding that leaves its locus list
empty WITHOUT the flag reads exactly as before.
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
KIT_AUDIT = FORGE / "skills/proposal-implementation/assets/kit/tests/test_audit.py"
NAME = "Method"
REVISION = "draft-1.md"
REVISION_TEXT = (
    "## 3\n\n$$\na = b \\tag{3.1}\n$$\n\n"
    "The estimator E[x] is always unbiased for every sample size.\n"
)


def finding(fid: str, **extra) -> dict:
    base = {
        "id": fid, "kind": "overstated-claim", "equations": [],
        "remedy_equations": [], "uses": ["E[x]"], "introduces": [],
        "adoption": {"absent": "always unbiased",
                     "expect": ["unbiased in expectation"]},
        "becomes_invariant": f"{fid}_holds", "status": "theorem",
        "statement": "The sentence claims more than the construction gives.",
        "remedy": "Restrict the claim to what the construction supports.",
    }
    base.update(extra)
    return base


def findings_source(*entries: dict) -> str:
    return f"FINDINGS = {json.dumps(list(entries), indent=4).replace('true', 'True')}\n"


class ProseFindingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposals = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.proposals, ignore_errors=True)
        (self.proposals / REVISION).write_text(REVISION_TEXT, encoding="utf-8")
        self.box = FORGE / "implementations" / f"_prose_findings_{os.getpid()}_{id(self)}"
        shutil.rmtree(self.box, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        (self.box / "src" / NAME).mkdir(parents=True)
        (self.box / "tests").mkdir()
        subprocess.run(["git", "init", "-q", str(self.box)], check=True)
        (self.box / "src" / NAME / "__init__.py").write_text(
            f"__implementation__ = {{'revision': '{REVISION}', 'premises': {{}}}}\n",
            encoding="utf-8")

    def declare(self, *entries: dict) -> None:
        (self.box / "tests" / "findings.py").write_text(findings_source(*entries),
                                                       encoding="utf-8")

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

    def command(self, verb: str) -> dict:
        return self.run_cli(verb, "--target", str(self.box), "--name", NAME,
                            "--revision", REVISION)

    def deferred(self) -> dict:
        return {item["id"]: item for item in self.command("handoff")["deferToOwnSession"]}

    def test_handoff_defers_a_prose_finding_to_a_session_of_its_own(self) -> None:
        self.declare(finding("wording", remedy_in_prose=True))
        item = self.deferred()["wording"]
        self.assertEqual(item["deferredBecause"], "prose-remedy", item)
        self.assertNotIn("blankKey", item)

    def test_verify_never_asks_a_prose_finding_for_a_remedy_block(self) -> None:
        self.declare(finding("wording", remedy_in_prose=True))
        result = self.command("verify")
        self.assertNotIn("wording", result["audit"]["localRemediesNotWritten"])
        self.assertFalse(any("wording" in json.dumps(entry)
                             for entry in result.get("toDiscuss", [])), result.get("toDiscuss"))

    def test_a_prose_finding_is_admitted_on_the_ordinary_checks(self) -> None:
        self.declare(finding("wording", remedy_in_prose=True))
        result = self.command("admit")
        self.assertEqual(result.get("admitted"), ["wording"], result)

    def test_a_prose_finding_still_owes_the_notation_check(self) -> None:
        self.declare(finding("wording", remedy_in_prose=True, uses=[r"\undefined"]))
        result = self.command("admit")
        self.assertIn("wording", result.get("inadmissible", {}), result)

    def test_prose_reach_with_remedy_loci_is_a_contradiction(self) -> None:
        self.declare(finding("wording", remedy_in_prose=True, remedy_equations=["3.1"]))
        result = self.command("admit")
        reasons = result.get("inadmissible", {}).get("wording", [])
        self.assertTrue(any("remedy_in_prose" in reason for reason in reasons), result)

    def test_a_flag_that_is_not_true_declares_nothing(self) -> None:
        self.declare(finding("wording", remedy_in_prose="yes"))
        result = self.command("admit")
        reasons = result.get("inadmissible", {}).get("wording", [])
        self.assertTrue(any("remedy_in_prose" in reason for reason in reasons), result)

    def test_an_empty_locus_list_without_the_flag_reads_as_before(self) -> None:
        self.declare(finding("blank"))
        item = self.deferred()["blank"]
        self.assertEqual(item["deferredBecause"], "remedy-locus-missing", item)
        result = self.command("verify")
        self.assertIn("blank", result["audit"]["localRemediesNotWritten"])


class KitAuditAcceptsProseFindingsTests(unittest.TestCase):
    """The kit's own level-4 check, run as a target would run it."""

    def run_audit(self, *entries: dict) -> subprocess.CompletedProcess:
        box = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, box, ignore_errors=True)
        shutil.copy(KIT_AUDIT, box / "test_audit.py")
        (box / "findings.py").write_text(findings_source(*entries), encoding="utf-8")
        (box / "sweep.py").write_text("SWEEP_SIZE = 1\n\ndef sweep():\n    return []\n",
                                      encoding="utf-8")
        return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                               "test_audit.py"], cwd=box, capture_output=True, text=True)

    def test_a_prose_finding_passes_the_kit_audit(self) -> None:
        proc = self.run_audit(finding("wording", remedy_in_prose=True))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_an_empty_locus_list_without_the_flag_still_fails_the_kit_audit(self) -> None:
        proc = self.run_audit(finding("blank"))
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("does not say what it changes", proc.stdout)

    def test_a_prose_finding_naming_remedy_loci_fails_the_kit_audit(self) -> None:
        proc = self.run_audit(finding("wording", remedy_in_prose=True,
                                      remedy_equations=["3.1"]))
        self.assertNotEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()

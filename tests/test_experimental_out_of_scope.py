"""C14: an experiments document can declare a proposal claim out of scope.

`agree` reports every claim the proposal declares that no experiment cites
(`untested:<id>`), and the only way to clear one was `--acknowledge
untested:<id>`, request-scoped by design, so it had to be retyped on every
call and nothing in either document recorded the decision.

The experiments document may now say so itself, with the shared convention's
`[out-of-scope:<id>]` marker (`skills/_core/conventions/experiments.json`,
key `outOfScope`). A declared claim the document marks that way is subtracted
from `untested` and echoed back under `outOfScope`. The marker never clears
anything else: a citation to a claim the proposal does not declare stays
`absent`, a marker naming an undeclared claim clears nothing, and a cited
claim is crossed whatever the marker says. A document with no marker reads
exactly as before.
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
CLI = FORGE / "skills/experimental-implementation/scripts/implementation_cli.py"
CONVENTION = FORGE / "skills/_core/conventions/experiments.json"
NAME = "Trial"
REVISION = "trial-1.md"
PROPOSAL = "## 1\n\n$$\na = b \\tag{9}\n$$\n\n$$\nc = d \\tag{10}\n$$\n"


class OutOfScopeDeclarationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiments = Path(tempfile.mkdtemp())
        self.proposals = Path(tempfile.mkdtemp())
        for root in (self.experiments, self.proposals):
            self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (self.proposals / "plan-v01.md").write_text(PROPOSAL, encoding="utf-8")
        self.box = FORGE / "implementations" / f"_out_of_scope_{os.getpid()}_{id(self)}"
        shutil.rmtree(self.box, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        self.box.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.box)], check=True)

    def agree(self, body: str, *extra: str) -> dict:
        (self.experiments / REVISION).write_text(
            "## Experiment [exp:E1] — a run\n\n" + body + "\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items()
               if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")}
        env["IMPLEMENTATION_PROPOSALS"] = str(self.experiments)
        env["IMPLEMENTATION_PROPOSALS_1"] = str(self.proposals)
        proc = subprocess.run([sys.executable, str(CLI), "agree", "--target", str(self.box),
                               "--name", NAME, "--revision", REVISION, *extra],
                              capture_output=True, text=True, env=env, cwd=FORGE)
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"no JSON: {proc.stdout!r} {proc.stderr!r}") from error

    def test_the_marker_is_registered_in_the_shared_convention(self) -> None:
        convention = json.loads(CONVENTION.read_text(encoding="utf-8"))
        self.assertEqual(convention.get("outOfScope"), "out-of-scope")

    def test_without_a_marker_an_uncited_claim_still_refuses(self) -> None:
        result = self.agree("Measures [claims:9].")
        self.assertEqual(result.get("code"), "AGREEMENT_DOCUMENTS_DISAGREE", result)
        self.assertIn("untested:10", result["detail"])
        self.assertNotIn("outOfScope", result)

    def test_a_claim_marked_out_of_scope_is_no_longer_untested(self) -> None:
        result = self.agree("Measures [claims:9].\n\nNot tested here: [out-of-scope:10].")
        self.assertEqual(result.get("status"), "agreed", result)
        self.assertEqual(result["outOfScope"], ["10"])
        self.assertEqual(result["crossed"], ["9"])

    def test_a_marker_naming_an_undeclared_claim_clears_nothing(self) -> None:
        result = self.agree("Measures [claims:9].\n\n[out-of-scope:11]")
        self.assertEqual(result.get("code"), "AGREEMENT_DOCUMENTS_DISAGREE", result)
        self.assertIn("untested:10", result["detail"])

    def test_only_declared_claims_are_echoed_as_out_of_scope(self) -> None:
        result = self.agree("Measures [claims:9].\n\n[out-of-scope:10] [out-of-scope:11]")
        self.assertEqual(result.get("status"), "agreed", result)
        self.assertEqual(result["outOfScope"], ["10"])

    def test_a_marker_never_clears_a_citation_to_an_undeclared_claim(self) -> None:
        result = self.agree("Measures [claims:9] and [claims:5].\n\n"
                            "[out-of-scope:10] [out-of-scope:5]")
        self.assertEqual(result.get("code"), "AGREEMENT_DOCUMENTS_DISAGREE", result)
        self.assertIn("absent:5", result["detail"])
        self.assertNotIn("untested:10", result["detail"].split("Unacknowledged:")[1])

    def test_a_cited_claim_is_crossed_whatever_the_marker_says(self) -> None:
        result = self.agree("Measures [claims:9] and [claims:10].\n\n[out-of-scope:10]")
        self.assertEqual(result.get("status"), "agreed", result)
        self.assertEqual(result["crossed"], ["10", "9"])
        self.assertNotIn("outOfScope", result)

    def test_acknowledging_still_works_beside_the_marker(self) -> None:
        result = self.agree("Measures [claims:9].", "--acknowledge", "untested:10")
        self.assertEqual(result.get("status"), "agreed", result)


if __name__ == "__main__":
    unittest.main()


class OutOfScopePatternValidationTests(unittest.TestCase):
    """The profile leaf is optional, and held to the crossing pattern's own
    one-group rule when declared."""

    def resolve(self, out_of_scope) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import test_experimental_implementation as helpers
        profile = helpers._real_profile()
        documents = [dict(entry) for entry in profile["documents"]]
        crossing = dict(documents[0]["cross_citation"])
        if out_of_scope is None:
            crossing.pop("out_of_scope", None)
        else:
            crossing["out_of_scope"] = out_of_scope
        documents[0]["cross_citation"] = crossing
        changed = dict(profile, documents=documents)
        box = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, box, ignore_errors=True)
        (box / "impl_profile.py").write_text(
            f"from pathlib import Path\nPROFILE = {helpers._to_source(changed)}\n",
            encoding="utf-8")
        helpers._resolve_with(box / "impl_profile.py")

    def test_the_leaf_is_optional(self) -> None:
        self.resolve(None)

    def test_a_pattern_without_exactly_one_group_refuses(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self.resolve(r"\[out-of-scope:[0-9]+\]")
        self.assertIn("INVALID_CROSS_CITATION_PATTERN", str(ctx.exception))

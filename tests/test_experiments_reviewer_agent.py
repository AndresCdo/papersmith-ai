"""The experiments reviewer agent and the significance-test guidance it checks.

Two halves of one change (odd/tasks/experiments-panel.md, T1, S3-S4):

* `experimental-deliberation` must tell the tutor WHICH significance test an
  experiment type calls for, including the arithmetic floor that makes a
  paired Wilcoxon over five folds unable to reach p < 0.05 at all.
* `experiments-reviewer` must exist, be delegated to by
  `experimental-implementation`, and review the four dimensions it was
  written for: code quality, optimisation, remote GPU use and statistical
  tests.

Stdlib only, like `test_agents.py`, which holds the generic agent rules.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / ".claude" / "agents" / "experiments-reviewer.md"
DELIBERATION = ROOT / "skills" / "experimental-deliberation" / "SKILL.md"
IMPLEMENTATION = ROOT / "skills" / "experimental-implementation" / "SKILL.md"


def flat(text: str) -> str:
    return " ".join(text.split())


class ExperimentsReviewerAgentTests(unittest.TestCase):

    def test_the_agent_file_exists(self) -> None:
        self.assertTrue(AGENT.is_file(), f"{AGENT} does not exist")

    def test_the_agent_names_its_four_review_dimensions(self) -> None:
        body = flat(AGENT.read_text(encoding="utf-8")).lower()
        for dimension in ("code quality", "optimisation", "gpu",
                          "statistical tests"):
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, body)

    def test_the_agent_is_read_only(self) -> None:
        header = AGENT.read_text(encoding="utf-8").split("---\n", 2)[1]
        tools = re.search(r"^tools:\s*(.+)$", header, re.MULTILINE)
        self.assertIsNotNone(tools)
        declared = {tool.strip() for tool in tools.group(1).split(",")}
        self.assertNotIn("Write", declared)
        self.assertNotIn("Edit", declared)

    def test_the_implementation_skill_delegates_the_review(self) -> None:
        doc = IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertIn("delegates to the `experiments-reviewer` agent", doc)
        self.assertIn("`.claude/agents/experiments-reviewer.md`", doc)

    def test_the_implementation_skill_documents_the_results_layout(self) -> None:
        doc = flat(IMPLEMENTATION.read_text(encoding="utf-8"))
        for fragment in ("Results/history", "Results/figures/",
                         "Results/tables/", "Results/summary.json",
                         "Results/significance", "p_adjusted",
                         "Experimental_AGREED.md", "AGREED.md"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, doc)


class SignificanceGuidanceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.doc = flat(DELIBERATION.read_text(encoding="utf-8"))

    def test_the_guidance_section_exists(self) -> None:
        self.assertIn("Choosing the significance test by experiment type",
                      self.doc)

    def test_the_guidance_names_the_tests_per_experiment_type(self) -> None:
        for name in ("Nadeau", "5x2cv", "Wilcoxon", "Friedman", "Nemenyi",
                     "McNemar", "DeLong", "bootstrap", "Page", "Jonckheere",
                     "Holm", "Benjamini", "Cliff", "ROPE"):
            with self.subTest(name=name):
                self.assertIn(name, self.doc)

    def test_the_wilcoxon_floor_at_five_folds_is_stated(self) -> None:
        self.assertIn("0.0625", self.doc)
        self.assertRegex(self.doc, r"n\s*=\s*5")

    def test_each_experiment_must_declare_its_test(self) -> None:
        for fragment in ("correction", "effect size", "confidence interval",
                         "significance table", "convergence"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.doc)


if __name__ == "__main__":
    unittest.main()

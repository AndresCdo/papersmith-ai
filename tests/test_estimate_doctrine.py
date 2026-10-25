"""Both implementation skills, and the four agents that build and walk their
flows, estimate the processing time before the pilot and before the full run.

The estimate itself is `remote-parallelism`'s `estimate` verb over the timing
probe's `Results/timing.json`; these checks hold the doctrine and the agents to
pointing at it, so a pilot or a launch is never asked for without a
measurement-derived range in front of the operator.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / ".claude" / "agents"

HEADING = "## Estimating the processing time before the pilot and before the full run"

#: Each agent's binding -- its FIRST skills/<x>/SKILL.md reference.
AGENT_BINDINGS = {
    "implementation-walk": "proposal-implementation",
    "experiments-walk": "experimental-implementation",
    "experiments-build": "experimental-implementation",
    "implementation-build": "proposal-implementation",
}


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class ImplementationDoctrineTests(unittest.TestCase):
    def test_both_skills_carry_the_estimate_section(self) -> None:
        for skill in ("proposal-implementation", "experimental-implementation"):
            with self.subTest(skill=skill):
                doc = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(HEADING, doc)
                section = doc.split(HEADING, 1)[1].split("\n## ", 1)[0]
                text = " ".join(section.split())
                for fragment in ("skills/remote-parallelism/SKILL.md", "`estimate`",
                                 "Results/timing.json", "`produces`", "before asking for a pilot",
                                 "a launch", "never a promise", "operator"):
                    self.assertIn(fragment, text, fragment)

    def test_the_sections_name_no_service(self) -> None:
        for skill in ("proposal-implementation", "experimental-implementation"):
            doc = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            section = doc.split(HEADING, 1)[1].split("\n## ", 1)[0].lower()
            for word in ("kaggle", "colab"):
                self.assertNotIn(word, section, f"{skill}: {word}")


class AgentEstimateTests(unittest.TestCase):
    def test_each_agent_runs_the_estimate_and_never_reads_it_as_authorization(self) -> None:
        for agent, binding in AGENT_BINDINGS.items():
            with self.subTest(agent=agent):
                path = AGENTS / f"{agent}.md"
                body = path.read_text(encoding="utf-8")
                named = re.findall(r"skills/([\w-]+)/SKILL\.md", body)
                self.assertEqual(named[0], binding)
                text = flat(path)
                for fragment in ("Results/timing.json", "`estimate`", "remote-parallelism",
                                 "timing probe", "never authorization"):
                    self.assertIn(fragment, text, fragment)

    def test_walk_agents_estimate_before_the_pilot(self) -> None:
        for agent in ("implementation-walk", "experiments-walk"):
            with self.subTest(agent=agent):
                self.assertIn("before the pilot", flat(AGENTS / f"{agent}.md"))


if __name__ == "__main__":
    unittest.main()

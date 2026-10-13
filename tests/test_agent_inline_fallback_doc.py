"""Every skill a generated agent is bound to says what to do when that agent
cannot be spawned: perform the stretch inline by following the agent's own
definition file.

The binding is derived from each `.claude/agents/<name>.md`'s own `Skill:`
line, never listed here, so a new agent fails this test until its skill
names it in the fallback section.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".claude" / "agents"
HEADING = "## When a delegated agent cannot be spawned"
BINDING = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")


def _bindings() -> dict[str, list[str]]:
    bound: dict[str, list[str]] = {}
    for agent in sorted(AGENTS.glob("*.md")):
        match = BINDING.search(agent.read_text(encoding="utf-8"))
        if match:
            bound.setdefault(match.group(1), []).append(agent.stem)
    return bound


def _section(text: str) -> str | None:
    if HEADING not in text:
        return None
    start = text.index(HEADING) + len(HEADING)
    end = text.find("\n## ", start)
    return text[start:] if end == -1 else text[start:end]


class AgentInlineFallbackDocTests(unittest.TestCase):
    def test_agents_are_bound(self) -> None:
        self.assertTrue(_bindings())

    def test_each_bound_skill_names_its_agents_in_the_fallback(self) -> None:
        for skill, agents in sorted(_bindings().items()):
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            section = _section(text)
            with self.subTest(skill=skill):
                self.assertIsNotNone(section, f"{skill}/SKILL.md lacks {HEADING!r}")
                for agent in agents:
                    self.assertIn(f"`.claude/agents/{agent}.md`", section)


if __name__ == "__main__":
    unittest.main()

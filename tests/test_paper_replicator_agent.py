"""The paper replicator agent (odd/tasks/replication-and-datasets.md, T1, S1).

`paper-replicator` reimplements the method of a referenced paper that ships no
public code, from its ingested Markdown, inside the target repository's layout.
It must run as a subagent of the active harness session on that session's own
model -- no pinned `model:`, no API key, no external LLM service -- name its
plan/analyze/code pipeline, keep a provenance table in `REPLICATION.md`, smoke
the code on the toy set before any GPU run, and be delegated to by
`proposal-implementation`.

Stdlib only, like `test_agents.py`, which holds the generic agent rules.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / ".claude" / "agents" / "paper-replicator.md"
IMPLEMENTATION = ROOT / "skills" / "proposal-implementation" / "SKILL.md"


def flat(text: str) -> str:
    return " ".join(text.split())


def header(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split("---\n", 2)[1] if text.startswith("---\n") else ""


class PaperReplicatorAgentTests(unittest.TestCase):

    def body(self) -> str:
        return flat(AGENT.read_text(encoding="utf-8"))

    def test_the_agent_file_exists(self) -> None:
        self.assertTrue(AGENT.is_file(), f"{AGENT} does not exist")

    def test_the_agent_pins_no_model(self) -> None:
        self.assertIsNone(
            re.search(r"^model:", header(AGENT), re.MULTILINE),
            "a `model:` key would pin a provider instead of inheriting the "
            "active session's model")

    def test_the_agent_declares_its_tools(self) -> None:
        tools = re.search(r"^tools:\s*(.+)$", header(AGENT), re.MULTILINE)
        self.assertIsNotNone(tools)
        declared = {tool.strip() for tool in tools.group(1).split(",")}
        self.assertEqual(declared,
                         {"Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebSearch", "WebFetch"})

    def test_published_code_is_searched_adopted_and_audited_before_any_reimplementation(self) -> None:
        body = self.body()
        self.assertIn("Act zero: look for published code first", body)
        self.assertLess(body.index("Act zero"), body.index("**Plan.**"))
        for rule in ("exact commit", "license", "`match`", "`deviation`", "`unspecified`",
                     "repository's own tests", "never a silent fix"):
            with self.subTest(rule=rule):
                self.assertIn(rule, body)

    def test_the_agent_names_its_pipeline_stages(self) -> None:
        body = self.body()
        for stage in ("**Plan.**", "**Analyze.**", "**Code.**", "**Verify.**"):
            with self.subTest(stage=stage):
                self.assertIn(stage, body)
        self.assertIn("lineage", body)
        self.assertIn("guidance/", body)

    def test_the_agent_keeps_a_provenance_table(self) -> None:
        body = self.body()
        self.assertIn("REPLICATION.md", body)
        self.assertIn("`unspecified`", body)
        self.assertIn("cites the paper's section or equation", body)

    def test_the_agent_smokes_on_the_toy_set_before_any_gpu_run(self) -> None:
        body = self.body()
        self.assertIn("toy set", body)
        self.assertIn("before any GPU run", body)
        for invariant in ("shapes", "gradients", "known cases"):
            with self.subTest(invariant=invariant):
                self.assertIn(invariant, body)

    def test_the_agent_uses_only_the_active_session_model(self) -> None:
        body = self.body()
        for fragment in ("Claude Code, OpenCode or Pi",
                         "no API key", "no external LLM service",
                         "no network LLM call"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, body)

    def test_the_agent_never_invents_results_or_launches(self) -> None:
        body = self.body()
        self.assertIn("Never invent a result", body)
        self.assertIn("never claim fidelity you did not test", body)
        self.assertIn("never launches a remote run", body)

    def test_the_implementation_skill_delegates_the_replication(self) -> None:
        doc = flat(IMPLEMENTATION.read_text(encoding="utf-8"))
        self.assertIn("delegates to the `paper-replicator` agent", doc)
        self.assertIn("`.claude/agents/paper-replicator.md`", doc)
        self.assertIn("Bringing in a comparison method: published code first, replication second", doc)


if __name__ == "__main__":
    unittest.main()

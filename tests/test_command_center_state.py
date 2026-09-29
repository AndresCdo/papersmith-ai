"""The command center's state extractor is read-only and honest.

Every fixture here is a hand-built workspace holding exactly the bytes the
assertion is about, so a failure names the input rather than a fixture
generator.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import state_extractor


def _contract(section: str, position: int, blocks: list[dict]) -> str:
    meta = {"section": section, "position": position, "mode": {"value": "argument"}, "blocks": blocks}
    return "---\n" + json.dumps(meta, indent=2) + "\n---\n\n# " + section + "\n\n**Extent** 100–250 words · one subsection\n"


class StateExtractorTests(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sections").mkdir(parents=True)
        (root / "paper").mkdir()
        return root

    def test_payload_always_carries_the_contract_keys(self) -> None:
        root = self.new_workspace()
        state = state_extractor.get_workspace_state(root)

        assert set(state) == {
            "generated_at", "workspace", "paper_metadata", "sections",
            "gates", "pipeline_stages", "experiments", "figures", "inbox", "totals",
        }
        assert [gate["id"] for gate in state["gates"]] == [
            "writing-readiness", "coupling-verification",
            "grounding-style-leak", "diagram-raster",
        ]
        assert [stage["id"] for stage in state["pipeline_stages"]] == [
            "ingestion", "deliberation", "experiments", "drafting", "auditing", "publishing",
        ]

    def test_a_missing_workspace_is_empty_not_an_error(self) -> None:
        root = self.new_workspace() / "does-not-exist"
        state = state_extractor.get_workspace_state(root)

        assert state["workspace"]["root"] == str(root)
        # The ten section slots are always present so the matrix renders; none
        # of them has a contract yet.
        assert len(state["sections"]) == 10
        assert all(section["status"] == "SCAFFOLDED" for section in state["sections"])
        assert state["totals"]["sections"] == 10
        assert state["totals"]["blocks_total"] == 0
        assert state["gates"][0]["state"] == "BLOCKED"

    def test_contract_without_a_draft_is_contracted(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-preamble", "requires_facts": [], "requires_declarations": [], "citations": "none"},
                {"id": "mm-proposal", "requires_facts": [{"value": "formulation"}],
                 "requires_declarations": [], "produces_facts": [{"value": "contributions"}]},
            ]),
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        section = state["sections"][0]
        assert section["status"] == "CONTRACTED"
        assert section["blocks_total"] == 2
        assert section["blocks_written"] == 0
        assert section["extent"] == {"min_words": 100, "max_words": 250}
        assert section["facts"]["demands"] == ["formulation"]
        assert section["facts"]["produces"] == ["contributions"]

    def test_word_count_and_drafting_come_from_block_markers(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-preamble", "requires_facts": [], "requires_declarations": [], "citations": "none"},
                {"id": "mm-proposal", "requires_facts": [], "requires_declarations": [], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        (root / "paper" / "main.tex").write_text(
            "\\documentclass{article}\n"
            "%% paper-writing block materials-and-methods.mm-preamble begin sha256=" + "a" * 64 + "\n"
            "one two three four five\n"
            "%% paper-writing block materials-and-methods.mm-preamble end\n"
            "%% paper-writing block materials-and-methods.mm-proposal begin sha256=" + "b" * 64 + "\n"
            "%% paper-writing block materials-and-methods.mm-proposal end\n",
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        section = state["sections"][0]
        assert section["blocks_written"] == 1
        assert section["word_count"] == 5
        assert section["status"] == "DRAFTING"

    def test_unresolved_citation_placeholder_blocks_the_grounding_gate(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-proposal", "requires_facts": [], "requires_declarations": [], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        (root / "paper" / "main.tex").write_text(
            "%% paper-writing block materials-and-methods.mm-proposal begin sha256=" + "a" * 64 + "\n"
            "We build on \\cite{unknown-key}.\n"
            "%% paper-writing block materials-and-methods.mm-proposal end\n",
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        gate = next(g for g in state["gates"] if g["id"] == "grounding-style-leak")
        assert gate["state"] == "BLOCKED"
        assert gate["parts"]["placeholder_citations"] == 1
        assert state["sections"][0]["status"] == "DRAFTING"

    def test_a_sealed_paper_reports_sealed(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-proposal", "requires_facts": [], "requires_declarations": [], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        (root / "paper" / "main.tex").write_text(
            "%% paper-writing block materials-and-methods.mm-proposal begin sha256=" + "a" * 64 + "\n"
            "A fully written paragraph.\n"
            "%% paper-writing block materials-and-methods.mm-proposal end\n",
            encoding="utf-8",
        )
        (root / "paper" / "verdict.json").write_text("{}", encoding="utf-8")
        state = state_extractor.get_workspace_state(root)

        assert state["sections"][0]["status"] == "SEALED"

    def test_coupling_gate_blocks_a_demand_without_a_producer(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-proposal", "requires_facts": [{"value": "formulation"}],
                 "requires_declarations": [], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        gate = next(g for g in state["gates"] if g["id"] == "coupling-verification")
        assert gate["state"] == "BLOCKED"
        assert gate["parts"]["unmatched"] == ["formulation"]

    def test_a_produced_fact_clears_the_coupling_gate(self) -> None:
        root = self.new_workspace()
        (root / "sections" / "01-materials-and-methods.md").write_text(
            _contract("materials-and-methods", 5, [
                {"id": "mm-a", "requires_facts": [], "requires_declarations": [],
                 "produces_facts": [{"value": "formulation"}], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        (root / "sections" / "02-experimental-setup.md").write_text(
            _contract("experimental-setup", 6, [
                {"id": "es-a", "requires_facts": [{"value": "formulation"}],
                 "requires_declarations": [], "citations": "none"},
            ]),
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        gate = next(g for g in state["gates"] if g["id"] == "coupling-verification")
        assert gate["state"] == "PASSED"

    def test_paper_metadata_prefers_the_workspace_yaml(self) -> None:
        root = self.new_workspace()
        (root / "papersmith.yaml").write_text(
            'version: "1"\nname: "my-paper"\ntitle: "A Real Title"\n'
            'topic: "graphs"\nvenue_target: "NeurIPS"\nauthors:\n  - "A. Author"\n',
            encoding="utf-8",
        )
        (root / ".papersmith").mkdir()
        (root / ".papersmith" / "config.json").write_text(
            json.dumps({"project_name": "fallback", "active_tools": ["claude"],
                        "execution_engine": {"active_compute_target": "local-workstation"}}),
            encoding="utf-8",
        )
        state = state_extractor.get_workspace_state(root)

        metadata = state["paper_metadata"]
        assert metadata["name"] == "my-paper"
        assert metadata["title"] == "A Real Title"
        assert metadata["topic"] == "graphs"
        assert metadata["authors"] == ["A. Author"]
        assert metadata["tools"] == ["claude"]
        assert metadata["compute_target"] == "local-workstation"

    def test_the_repository_contracts_parse(self) -> None:
        """The ten real contracts in this repository must all parse."""
        repository = Path(__file__).resolve().parent.parent
        state = state_extractor.get_workspace_state(repository)

        assert len(state["sections"]) == 10
        assert all(section["has_contract"] for section in state["sections"])
        assert all(section["blocks_total"] > 0 for section in state["sections"])
        assert state["totals"]["blocks_total"] > 0

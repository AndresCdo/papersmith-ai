"""The wiring inspector reports what it can measure, and never guesses healthy."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import health_inspector


def _skill(root: Path, name: str) -> None:
    directory = root / "skills" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")


def _agent(root: Path, name: str, *, skill: str, tools: str = "Read, Glob") -> None:
    directory = root / ".claude" / "agents"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"tools: {tools}\n"
        "stretch: write\n"
        "---\n\n"
        f"Skill: `.claude/skills/{skill}/SKILL.md`. Load it and follow it.\n",
        encoding="utf-8",
    )


class WiringInspectorTests(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        return root

    def test_skill_manifests_report_missing_manifests(self) -> None:
        root = self.new_workspace()
        _skill(root, "paper-writing")
        _skill(root, "figure-review")
        # kaggle-accounts is a core skill but has no SKILL.md here.
        rows = health_inspector.skill_manifests(root)

        by_name = {row["name"]: row for row in rows}
        assert by_name["paper-writing"]["state"] == "WIRED"
        assert by_name["figure-review"]["state"] == "WIRED"
        assert by_name["kaggle-accounts"]["state"] == "MISSING"
        assert by_name["kaggle-accounts"]["core"] is True

    def test_agent_integrity_flags_an_unbound_tool(self) -> None:
        root = self.new_workspace()
        _skill(root, "paper-writing")
        _agent(root, "redactor", skill="paper-writing")
        _agent(root, "diagram-author", skill="paper-writing", tools="Read, Telepathy")

        rows = {row["name"]: row for row in health_inspector.agent_integrity(root)}

        assert rows["redactor"]["state"] == "WIRED"
        assert rows["diagram-author"]["state"] == "TOOL_UNBOUND"
        assert rows["diagram-author"]["unbound_tools"] == ["Telepathy"]

    def test_a_missing_required_agent_is_reported(self) -> None:
        root = self.new_workspace()
        _skill(root, "paper-writing")
        rows = {row["name"]: row for row in health_inspector.agent_integrity(root)}

        for required in health_inspector.REQUIRED_AGENTS:
            assert rows[Path(required).stem]["state"] == "MISSING"

    def test_agent_referencing_an_absent_skill_is_not_wired(self) -> None:
        root = self.new_workspace()
        _agent(root, "redactor", skill="paper-writing")

        rows = {row["name"]: row for row in health_inspector.agent_integrity(root)}

        assert rows["redactor"]["state"] == "MISSING"

    def test_structural_drift_detects_a_missing_harness(self) -> None:
        root = self.new_workspace()
        state, detail = health_inspector._structural_drift(root, "claude")

        assert state == "UNKNOWN"
        assert ".claude/" in detail

    def test_structural_drift_detects_command_parity_break(self) -> None:
        root = self.new_workspace()
        _skill(root, "paper-writing")
        claude = root / ".claude"
        (claude / "commands").mkdir(parents=True)
        (claude / "skills").mkdir()
        # skills/ has paper-writing but .claude/commands/ lists nothing.
        state, detail = health_inspector._structural_drift(root, "claude")

        assert state == "DRIFT_DETECTED"
        assert "paper-writing" in detail

    def test_structural_drift_accepts_a_consistent_projection(self) -> None:
        root = self.new_workspace()
        _skill(root, "paper-writing")
        for tool in ("claude", "opencode"):
            prefix = root / f".{tool}"
            (prefix / "commands").mkdir(parents=True)
            (prefix / "skills").mkdir()
            (prefix / "commands" / "paper-writing.md").write_text("x", encoding="utf-8")
        state, detail = health_inspector._structural_drift(root, "claude")

        assert state == "IN_SYNC", detail

    def _stub_cli(self, root: Path, skill: str, relative: str) -> None:
        script = root / "skills" / skill / relative
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("import sys\nprint('usage')\nsys.exit(0)\n", encoding="utf-8")

    def test_full_payload_shape_on_a_fully_wired_workspace(self) -> None:
        root = self.new_workspace()
        core = [name for name, _ in health_inspector.CORE_SKILLS]
        for name in core:
            _skill(root, name)
        for name, relative in health_inspector.CORE_SKILLS:
            self._stub_cli(root, name, relative)
        for required in health_inspector.REQUIRED_AGENTS:
            _agent(root, Path(required).stem, skill="paper-writing")
        for tool in ("claude", "opencode", "pi", "antigravity"):
            prefix = root / f".{tool}"
            (prefix / "commands").mkdir(parents=True)
            for name in core:
                (prefix / "commands" / f"{name}.md").write_text("x", encoding="utf-8")
            os.symlink(os.path.relpath(root / "skills", prefix), prefix / "skills")

        health = health_inspector.get_wiring_health(root)

        assert set(health) == {
            "generated_at", "summary", "harness_sync", "skills",
            "cli_entrypoints", "agents", "environment", "matrix",
        }
        assert health["summary"]["components_total"] == health["summary"]["components_healthy"], (
            health["summary"], health["harness_sync"], health["cli_entrypoints"]
        )
        assert health["summary"]["state"] == "HEALTHY"
        assert all(row["state"] == "WIRED" for row in health["cli_entrypoints"])
        assert all(row["state"] == "WIRED" for row in health["agents"])
        assert all(row["state"] == "IN_SYNC" for row in health["harness_sync"]["harnesses"])
        assert health["matrix"]

    def test_environment_reports_missing_packages_as_tool_missing(self) -> None:
        root = self.new_workspace()
        environment = health_inspector.environment_health(root)

        names = {row["name"] for row in environment["packages"]}
        assert names == set(health_inspector.REQUIRED_PACKAGES)
        assert all(row["state"] in ("WIRED", "TOOL_MISSING") for row in environment["packages"])
        assert environment["python"]["state"] == "WIRED"

    def test_the_repository_itself_reports_every_skill_wired(self) -> None:
        repository = Path(__file__).resolve().parent.parent
        rows = health_inspector.skill_manifests(repository)

        core = {row["name"]: row["state"] for row in rows if row["core"]}
        assert core, "the repository must expose its core skills"
        assert all(state == "WIRED" for state in core.values())

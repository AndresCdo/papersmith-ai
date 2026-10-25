"""Success criterion #6: the MCP server never generates, reads, or overwrites `.mcp.json`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_series import (
    REPO_ROOT,
    build_workspace,
    call_many,
    request,
    run_cli,
    tool_call,
)


@pytest.fixture(scope="module")
def workspace(tmp_path_factory) -> Path:
    return build_workspace(tmp_path_factory.mktemp("mcp-json"))


def test_the_repo_discovery_scaffold_is_never_rewritten(workspace: Path) -> None:
    scaffold = REPO_ROOT / ".mcp.json"
    before = scaffold.read_bytes()
    call_many(workspace, [request("tools/list"), tool_call("papersmith.workspace_status")])
    run_cli("mcp", "inspect", cwd=workspace)
    assert scaffold.read_bytes() == before


def test_the_mcp_server_never_rewrites_the_workspace_mcp_json(workspace: Path) -> None:
    # `init` registers the lab's banco-lia server there; the papersmith MCP
    # server itself never writes it.
    config = workspace / ".mcp.json"
    before = config.read_bytes()
    call_many(workspace, [tool_call("papersmith.workspace_status")])
    assert config.read_bytes() == before
    assert "papersmith" not in json.loads(before)["mcpServers"]


def test_print_config_prints_a_snippet_and_writes_nothing(workspace: Path) -> None:
    before = sorted(path.name for path in workspace.iterdir())
    completed = run_cli("mcp", "print-config", "--workspace", str(workspace), cwd=workspace)
    assert completed.returncode == 0
    snippet = json.loads(completed.stdout)
    server = snippet["mcpServers"]["papersmith"]
    assert server["command"] == "smith"
    assert server["args"][:3] == ["mcp", "serve", "--workspace"]
    assert sorted(path.name for path in workspace.iterdir()) == before

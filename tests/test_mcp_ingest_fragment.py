"""`papersmith.ingest_fragment` end to end: through the MCP server, against a
paper ingested into a real workspace, one fragment comes back and the rest of
the document does not."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

import pytest

from mcp_series import build_workspace, call_many, tool_call

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "paper-ingestion" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import extract_pdf  # noqa: E402
from test_pdf_pipeline import MATH_PAGE, TEXT_PAGE, _StubHeavy, make_pdf  # noqa: E402


@pytest.fixture(scope="module")
def workspace(tmp_path_factory) -> Path:
    root = build_workspace(tmp_path_factory.mktemp("mcp-fragment"))
    paper = root / "guidance" / "topic" / "paper"
    paper.mkdir(parents=True)
    pdf = make_pdf(paper / "paper.pdf", [TEXT_PAGE, MATH_PAGE])
    engine = extract_pdf.RoutedEngine("auto", "fast", False, None)
    engine.heavy = _StubHeavy()
    with redirect_stderr(io.StringIO()):
        extract_pdf.render_paper(engine, pdf, True, paper)
    return root


def _result(response: dict) -> dict:
    return response["result"]


def test_one_page_comes_back_as_structured_json(workspace: Path) -> None:
    [response] = call_many(workspace, [tool_call(
        "papersmith.ingest_fragment", {"paper": "guidance/topic/paper", "page": 2})])
    result = _result(response)
    assert result["isError"] is False, result
    assert result["structuredContent"]["kind"] == "page"
    assert result["structuredContent"]["text"] == "$$\\alpha_2$$"
    assert "A Study of Routing" not in result["content"][0]["text"]


def test_a_heading_section_and_the_cap(workspace: Path) -> None:
    [response] = call_many(workspace, [tool_call(
        "papersmith.ingest_fragment", {"paper": "guidance/topic/paper/paper.json",
                                       "heading": "introduction", "max_chars": 40})])
    structured = _result(response)["structuredContent"]
    assert structured["heading"] == "1 Introduction"
    assert len(structured["text"]) == 40
    assert structured["truncated"]["shown"] == 40


def test_nothing_matched_is_an_error_result(workspace: Path) -> None:
    [response] = call_many(workspace, [tool_call(
        "papersmith.ingest_fragment", {"paper": "guidance/topic/paper", "page": 9})])
    result = _result(response)
    assert result["isError"] is True
    assert result["structuredContent"]["code"] == "USER_ERROR"
    assert "no page 9" in result["structuredContent"]["detail"]


def test_a_paper_outside_the_workspace_is_refused(workspace: Path) -> None:
    [response] = call_many(workspace, [tool_call(
        "papersmith.ingest_fragment", {"paper": "/etc", "outline": True})])
    assert _result(response)["structuredContent"]["code"] == "WORKSPACE_ESCAPE"

"""Figure-id option injection at the real render-to-subprocess boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

FORGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = FORGE_ROOT / "skills" / "paper-writing" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
import paper_figure  # noqa: E402
import paper_latex  # noqa: E402
from impl_refusals import Refused  # noqa: E402

SOURCE = b"% node: encoder\n"
MANIFEST = json.dumps({"components": ["encoder"]}).encode("utf-8")
PDF = b"%PDF-1.4 synthetic figure-id test\n"


def _write_figure(paper_dir: Path, figure_id: str) -> tuple[Path, Path]:
    """Create inputs directly so invalid-id setup never uses the validator."""
    figures = paper_dir / "Figures"
    figures.mkdir(parents=True)
    source = figures / f"{figure_id}.tex"
    manifest = figures / f"{figure_id}.diagram.json"
    source.write_bytes(SOURCE)
    manifest.write_bytes(MANIFEST)
    return source, manifest


@pytest.mark.parametrize("figure_id", ["-x", "--help", "-e=I81_SENTINEL"])
def test_render_refuses_option_like_id_before_subprocess(tmp_path: Path, figure_id: str) -> None:
    # Given: existing inputs, with discovery and process execution made inert.
    paper_dir = tmp_path / "paper"
    source, manifest = _write_figure(paper_dir, figure_id)
    with (
        patch.object(paper_latex, "discover_latexmk", return_value="/inert/latexmk") as discover,
        patch.object(
            paper_latex.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)
        ) as run,
    ):
        # When: the actual render pipeline receives an option-like id.
        with pytest.raises(Refused) as refusal:
            paper_figure.render(paper_dir, figure_id)

        # Then: no compiler argument can escape the identifier boundary.
        assert run.call_count == 0, f"unsafe compiler argv: {run.call_args.args[0]!r}"
        discover.assert_not_called()
    assert refusal.value.code == "DIAGRAM_SOURCE_ABSENT"
    assert source.read_bytes() == SOURCE
    assert manifest.read_bytes() == MANIFEST
    assert not (paper_dir / ".paper-writing").exists()
    assert not (paper_dir / "Figures" / f"{figure_id}.pdf").exists()


def test_render_publishes_contained_pdf_when_id_has_internal_hyphen(tmp_path: Path) -> None:
    # Given: a valid id and a subprocess double producing synthetic output.
    paper_dir = tmp_path / "paper"
    figure_id = "diag-1"
    source, manifest = _write_figure(paper_dir, figure_id)

    def compile_output(
        argv: list[str],
        **_kwargs: str | dict[str, str] | bool | float,
    ) -> subprocess.CompletedProcess[str]:
        scratch = Path(
            next(arg.removeprefix("-outdir=") for arg in argv if arg.startswith("-outdir="))
        )
        assert scratch.resolve().is_relative_to(paper_dir.resolve())
        (scratch / f"{figure_id}.log").write_text("", encoding="utf-8")
        (scratch / f"{figure_id}.pdf").write_bytes(PDF)
        return subprocess.CompletedProcess(argv, 0, "", "")

    with (
        patch.object(paper_latex, "discover_latexmk", return_value="/inert/latexmk"),
        patch.object(paper_latex.subprocess, "run", side_effect=compile_output) as run,
    ):
        # When: render compiles through paper_latex and publishes its result.
        result = paper_figure.render(paper_dir, figure_id)

        # Then: the named artifact is contained, correct, and inputs are preserved.
        assert run.call_count == 1
        assert run.call_args.args[0][-1] == "diag-1.tex"
        assert run.call_args.kwargs["cwd"] == str(paper_dir / "Figures")
    assert result["verdict"] == "success"
    published = Path(result["pdf"])
    assert published == paper_dir / "Figures" / "diag-1.pdf"
    assert published.resolve().is_relative_to((paper_dir / "Figures").resolve())
    assert published.read_bytes() == PDF
    assert source.read_bytes() == SOURCE
    assert manifest.read_bytes() == MANIFEST

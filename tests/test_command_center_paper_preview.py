"""The read-only paper preview: bounded block reader and whitelisted files.

Route functions are called directly with fakes (like ``test_command_center_server``);
the Host allow-list is exercised through the raw-ASGI harness used by
``test_command_center_server_history``.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import paper_preview

DIGEST = "a" * 64


def _block(block_id: str, body: str) -> str:
    return (f"%% paper-writing block {block_id} begin sha256={DIGEST}\n"
            f"{body}\n%% paper-writing block {block_id} end\n")


def _contract(name: str, position: int, ids: list[str], title: str | None = None) -> str:
    meta = {"section": name, "position": position, "blocks": [{"id": i} for i in ids]}
    if title:
        meta["title"] = title
    return "---\n" + json.dumps(meta) + "\n---\nBody prose.\n"


class _Workspace(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sections").mkdir()
        (root / "paper" / "Figures").mkdir(parents=True)
        return root

    def write(self, root: Path, rel: str, data: str | bytes) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_bytes(data)
        return path

    def preview(self, root: Path) -> dict:
        return paper_preview.build_preview(root)

    @staticmethod
    def snapshot(root: Path) -> dict:
        out = {}
        for path in sorted(root.rglob("*")):
            st = path.lstat()
            out[str(path.relative_to(root))] = (st.st_size, st.st_mtime_ns)
        return out


class BlockParsingTests(_Workspace):
    def setUp(self) -> None:
        self.root = self.new_workspace()
        self.write(self.root, "sections/06-introduction.md",
                   _contract("introduction", 6, ["introduction.hook", "introduction.gap"], "Intro"))

    def blocks(self) -> dict:
        data = self.preview(self.root)
        section = next(s for s in data["sections"] if s["id"] == "06-introduction")
        return {b["id"]: b for b in section["blocks"]}

    def test_written_and_unwritten_blocks(self) -> None:
        self.write(self.root, "paper/main.tex", _block("introduction.hook", "Hello world."))
        blocks = self.blocks()

        assert blocks["introduction.hook"]["written"] is True
        assert blocks["introduction.hook"]["text"] == "Hello world."
        assert blocks["introduction.hook"]["words"] == 2
        assert blocks["introduction.gap"] == {
            "id": "introduction.gap", "written": False, "text": None, "words": 0,
            "citations": [], "truncated": False, "duplicate": False}

    def test_cite_keys_are_extracted_and_text_is_unchanged(self) -> None:
        body = r"See \cite{a, b} and \citep{c}; again \cite{a}."
        self.write(self.root, "paper/main.tex", _block("introduction.hook", body))
        block = self.blocks()["introduction.hook"]

        assert block["citations"] == ["a", "b", "c"]
        assert block["text"] == body

    def test_text_is_plain_not_html(self) -> None:
        body = "<script>alert(1)</script> & x"
        self.write(self.root, "paper/main.tex", _block("introduction.hook", body))

        assert self.blocks()["introduction.hook"]["text"] == body

    def test_unterminated_block_is_dropped(self) -> None:
        text = (f"%% paper-writing block introduction.hook begin sha256={DIGEST}\n"
                "never closed\n")
        self.write(self.root, "paper/main.tex", text)

        assert self.blocks()["introduction.hook"]["written"] is False

    def test_duplicate_ids_first_wins_and_is_flagged(self) -> None:
        text = _block("introduction.hook", "first") + _block("introduction.hook", "second")
        self.write(self.root, "paper/main.tex", text)
        block = self.blocks()["introduction.hook"]

        assert block["text"] == "first"
        assert block["duplicate"] is True

    def test_declarations_and_provenance_regions_are_ignored(self) -> None:
        fake = f"%% paper-writing block introduction.hook begin sha256={DIGEST}"
        text = (
            f"%% paper-writing declarations begin sha256={DIGEST}\n"
            f"{fake}\n%% injected\n%% paper-writing block introduction.hook end\n"
            "%% paper-writing declarations end\n"
            f"%% paper-writing provenance begin sha256={DIGEST}\n"
            f"{fake}\n%% paper-writing block introduction.hook end\n"
            "%% paper-writing provenance end\n"
            + _block("introduction.hook", "real")
        )
        self.write(self.root, "paper/main.tex", text)

        assert self.blocks()["introduction.hook"]["text"] == "real"

    def test_blank_body_is_not_written(self) -> None:
        self.write(self.root, "paper/main.tex", _block("introduction.hook", "   "))

        assert self.blocks()["introduction.hook"]["written"] is False

    def test_missing_main_tex_leaves_every_block_unwritten(self) -> None:
        data = self.preview(self.root)

        assert data["main_tex"]["status"] == "absent"
        assert all(not b["written"] for s in data["sections"] for b in s["blocks"])


class SectionOrderTests(_Workspace):
    def test_canonical_order_then_extras_with_ids_and_titles(self) -> None:
        root = self.new_workspace()
        self.write(root, "sections/08-abstract.md", _contract("abstract", 8, ["abstract.body"]))
        self.write(root, "sections/01-materials-and-methods.md",
                   _contract("materials-and-methods", 1, [], "Methods"))
        self.write(root, "sections/99-extra.md", _contract("extra", 99, []))
        data = self.preview(root)
        ids = [s["id"] for s in data["sections"]]

        assert ids[0] == "01-materials-and-methods"
        assert ids.index("08-abstract") < ids.index("99-extra")
        assert ids[-1] == "99-extra"
        assert data["sections"][0]["title"] == "Methods"
        assert data["sections"][0]["position"] == 1
        assert data["sections"][0]["status"] == "CONTRACTED" or data["sections"][0]["status"] == "SCAFFOLDED"

    def test_status_reflects_written_blocks(self) -> None:
        root = self.new_workspace()
        self.write(root, "sections/08-abstract.md",
                   _contract("abstract", 8, ["abstract.a", "abstract.b"]))
        self.write(root, "paper/main.tex", _block("abstract.a", "text"))
        section = next(s for s in self.preview(root)["sections"] if s["id"] == "08-abstract")

        assert section["status"] == "DRAFTING"


class CapTests(_Workspace):
    def test_per_block_truncation_flag(self) -> None:
        root = self.new_workspace()
        self.write(root, "sections/06-introduction.md", _contract("introduction", 6, ["introduction.hook"]))
        big = "word " * 20000  # ~100 KB
        self.write(root, "paper/main.tex", _block("introduction.hook", big))
        data = self.preview(root)
        block = next(s for s in data["sections"] if s["id"] == "06-introduction")["blocks"][0]

        assert block["truncated"] is True
        assert len(block["text"].encode()) <= data["caps"]["block_text_bytes"]
        assert block["words"] == 20000
        assert data["truncated"] is True

    def test_total_cap_withholds_later_blocks(self) -> None:
        root = self.new_workspace()
        ids = [f"introduction.b{i}" for i in range(12)]
        self.write(root, "sections/06-introduction.md", _contract("introduction", 6, ids))
        text = "".join(_block(i, "x" * 30000) for i in ids)
        self.write(root, "paper/main.tex", text)
        data = self.preview(root)
        blocks = next(s for s in data["sections"] if s["id"] == "06-introduction")["blocks"]
        total = sum(len(b["text"].encode()) for b in blocks if b["text"])

        assert total <= data["caps"]["total_text_bytes"]
        assert data["truncated"] is True
        assert blocks[-1]["written"] is True and blocks[-1]["text"] is None
        assert blocks[-1]["truncated"] is True

    def test_main_tex_over_the_size_cap_is_too_large_with_no_content(self) -> None:
        root = self.new_workspace()
        self.write(root, "sections/06-introduction.md", _contract("introduction", 6, ["introduction.hook"]))
        path = root / "paper" / "main.tex"
        with open(path, "wb") as handle:
            handle.truncate(paper_preview.MAIN_TEX_MAX_BYTES + 1)  # sparse "huge" file
        data = self.preview(root)
        block = next(s for s in data["sections"] if s["id"] == "06-introduction")["blocks"][0]

        assert data["main_tex"]["status"] == "too_large"
        assert block["written"] is False and block["text"] is None

    def test_oversized_section_file_is_not_read(self) -> None:
        root = self.new_workspace()
        path = root / "sections" / "06-introduction.md"
        with open(path, "wb") as handle:
            handle.truncate(paper_preview.SECTION_MAX_BYTES + 1)
        section = next(s for s in self.preview(root)["sections"] if s["id"] == "06-introduction")

        assert section["blocks"] == []

    def test_reads_never_use_the_unbounded_extractor_reader(self) -> None:
        from unittest import mock
        root = self.new_workspace()
        self.write(root, "sections/06-introduction.md", _contract("introduction", 6, ["introduction.hook"]))
        self.write(root, "paper/main.tex", _block("introduction.hook", "x"))
        with mock.patch("skills._core.command_center.state_extractor._read_text",
                        side_effect=AssertionError("unbounded read")):
            self.preview(root)


class ContainmentTests(_Workspace):
    def test_symlinked_main_tex_escaping_the_workspace_is_refused(self) -> None:
        root = self.new_workspace()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        (outside / "secret.tex").write_text(_block("introduction.hook", "SECRET"))
        os.symlink(outside / "secret.tex", root / "paper" / "main.tex")
        self.write(root, "sections/06-introduction.md", _contract("introduction", 6, ["introduction.hook"]))
        data = self.preview(root)

        assert data["main_tex"]["status"] == "unsafe"
        assert "SECRET" not in json.dumps(data)

    def test_symlinked_section_file_escaping_is_not_read(self) -> None:
        root = self.new_workspace()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        (outside / "s.md").write_text(_contract("introduction", 6, ["introduction.leak"]))
        os.symlink(outside / "s.md", root / "sections" / "06-introduction.md")
        section = next(s for s in self.preview(root)["sections"] if s["id"] == "06-introduction")

        assert section["blocks"] == []

    def test_directory_named_main_tex_is_not_regular(self) -> None:
        root = self.new_workspace()
        (root / "paper" / "main.tex").mkdir()

        assert self.preview(root)["main_tex"]["status"] == "unreadable"

    def test_in_workspace_symlink_is_followed(self) -> None:
        root = self.new_workspace()
        real = self.write(root, "paper/real.tex", _block("introduction.hook", "ok"))
        os.symlink(real, root / "paper" / "main.tex")

        assert self.preview(root)["main_tex"]["status"] == "ok"


class PdfInfoTests(_Workspace):
    def test_pdf_absent_is_normal(self) -> None:
        pdf = self.preview(self.new_workspace())["pdf"]

        assert pdf == {"main": None, "figures": []}

    def test_staleness_follows_mtime(self) -> None:
        root = self.new_workspace()
        tex = self.write(root, "paper/main.tex", "x")
        pdf = self.write(root, "paper/main.pdf", b"%PDF-1.4")
        os.utime(tex, (2000, 2000))
        os.utime(pdf, (1000, 1000))
        assert self.preview(root)["pdf"]["main"] == {"present": True, "size": 8, "stale": True}
        os.utime(pdf, (3000, 3000))
        assert self.preview(root)["pdf"]["main"]["stale"] is False

    def test_figures_listed_by_id_and_kind_only_valid_regular_files(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/Figures/arch.pdf", b"%PDF")
        self.write(root, "paper/Figures/plot.png", b"\x89PNG")
        self.write(root, "paper/Figures/.hidden.pdf", b"%PDF")
        self.write(root, "paper/Figures/notes.txt", b"x")
        (root / "paper" / "Figures" / "dir.pdf").mkdir()
        figures = self.preview(root)["pdf"]["figures"]

        assert figures == [{"id": "arch", "kind": "pdf", "size": 4},
                           {"id": "plot", "kind": "png", "size": 4}]


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Return one piece of an ingested paper, never the whole document.

An ingested paper is a folder ``<stem>/`` holding ``<stem>.md`` and the
``<stem>.json`` map that ``extract_pdf.py`` writes beside it. This reads the map
and answers with exactly one of:

    --page N        the Markdown of page N
    --heading TEXT  the section under the first heading containing TEXT, up to
                    the next heading of the same or a higher level
    --equation K    display equation K (0-based) as LaTeX, with its page
    --search TEXT   the paragraphs containing TEXT, each with its page
    --outline       the headings, pages, equation and reference counts only

``--max-chars`` caps the answer (default 6000) and says when it cut. Stdlib
only and read-only: no model, no network, no write.

Usage:
    python pdf_fragment.py <paper-folder | stem.json | stem.md> --page 3
    python pdf_fragment.py guidance/topic/paper --heading "Variational bound" --json

Exit codes: 0 found, 1 nothing matched, 2 usage error or unreadable paper.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_MAX_CHARS = 6000
_PAGE_MARKER = re.compile(r"^<!-- page (\d+) -->$", re.MULTILINE)


class FragmentError(Exception):
    """The paper cannot be read, or the request names nothing in it."""


def load(target: str) -> tuple[dict, str]:
    """The sidecar map and the Markdown of an ingested paper."""
    path = Path(target).expanduser()
    if path.is_dir():
        maps = sorted(path.glob("*.json"))
        named = path / f"{path.name}.json"
        path = named if named.is_file() or len(maps) != 1 else maps[0]
    elif path.suffix == ".md":
        path = path.with_suffix(".json")
    if not path.is_file():
        raise FragmentError(f"{path} not found: ingest the paper first (extract_pdf.py writes it)")
    try:
        sidecar = json.loads(path.read_text(encoding="utf-8"))
        markdown = (path.parent / sidecar["markdown"]["file"]).read_text(encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FragmentError(f"{path} is not a readable ingestion map ({exc})") from None
    if sidecar.get("schema") != "papersmith.ingestion/v1":
        raise FragmentError(f"{path} has schema {sidecar.get('schema')!r}, expected papersmith.ingestion/v1")
    return sidecar, markdown


def _page_of(markdown: str, offset: int) -> int | None:
    pages = [int(m.group(1)) for m in _PAGE_MARKER.finditer(markdown, 0, offset + 1)]
    return pages[-1] if pages else None


def _clean(text: str) -> str:
    return _PAGE_MARKER.sub("", text).strip()


def page(sidecar: dict, markdown: str, number: int) -> dict:
    for row in sidecar.get("pages", []):
        if row.get("page") == number and "md_start" in row:
            return {"kind": "page", "page": number, "route": row.get("route"), "engine": row.get("engine"),
                    "text": markdown[row["md_start"]:row["md_end"]].strip()}
    total = sidecar.get("source", {}).get("pages")
    raise FragmentError(f"no page {number}" + (f" (the paper has {total})" if total else
                                               " (this paper was ingested without page markers)"))


def heading(sidecar: dict, markdown: str, query: str) -> dict:
    headings = sidecar.get("headings", [])
    wanted = query.casefold()
    for index, entry in enumerate(headings):
        if wanted in entry["text"].casefold():
            end = len(markdown)
            for later in headings[index + 1:]:
                if later["level"] <= entry["level"]:
                    end = later["md_offset"]
                    break
            return {"kind": "heading", "heading": entry["text"], "page": entry.get("page"),
                    "text": _clean(markdown[entry["md_offset"]:end])}
    raise FragmentError(f"no heading contains {query!r}")


def equation(sidecar: dict, number: int) -> dict:
    equations = sidecar.get("equations", [])
    if not 0 <= number < len(equations):
        raise FragmentError(f"no equation {number} (the paper has {len(equations)}, numbered from 0)")
    entry = equations[number]
    return {"kind": "equation", "index": number, "page": entry.get("page"), "text": entry["latex"]}


def search(markdown: str, query: str, limit: int = 5) -> dict:
    wanted = query.casefold()
    hits = []
    offset = 0
    for block in markdown.split("\n\n"):
        if wanted in block.casefold() and not _PAGE_MARKER.fullmatch(block.strip()):
            hits.append({"page": _page_of(markdown, offset), "text": block.strip()})
            if len(hits) >= limit:
                break
        offset += len(block) + 2
    if not hits:
        raise FragmentError(f"nothing contains {query!r}")
    return {"kind": "search", "query": query, "hits": hits,
            "text": "\n\n".join(f"[page {h['page']}] {h['text']}" for h in hits)}


def outline(sidecar: dict) -> dict:
    lines = [f"{'  ' * (h['level'] - 1)}{h['text']}  (page {h.get('page')})" for h in sidecar.get("headings", [])]
    return {"kind": "outline", "source": sidecar.get("source"), "engine": sidecar.get("engine"),
            "equations": len(sidecar.get("equations", [])), "references": len(sidecar.get("references", [])),
            "figures": len(sidecar.get("figures", [])), "text": "\n".join(lines)}


def cap(answer: dict, max_chars: int) -> dict:
    text = answer.get("text", "")
    if len(text) > max_chars:
        answer["text"] = text[:max_chars]
        answer["truncated"] = {"shown": max_chars, "total": len(text)}
    return answer


def main(argv: list[str] | None = None) -> int:
    # One usage row: the skill-audit probe reads the flag roster from it.
    os.environ.setdefault("COLUMNS", "240")
    parser = argparse.ArgumentParser(description="Return one fragment of an ingested paper.")
    parser.add_argument("paper", help="the paper folder, or its .json / .md")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--page", type=int, help="page number, from 1")
    which.add_argument("--heading", help="text contained in a heading")
    which.add_argument("--equation", type=int, help="display equation index, from 0")
    which.add_argument("--search", help="text to find in the paragraphs")
    which.add_argument("--outline", action="store_true", help="headings and counts only")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="cap on the returned text")
    parser.add_argument("--json", action="store_true", help="answer as JSON")
    args = parser.parse_args(argv)
    if args.max_chars < 1:
        print("Usage error: --max-chars must be positive.", file=sys.stderr)
        return 2
    try:
        sidecar, markdown = load(args.paper)
    except FragmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    try:
        if args.page is not None:
            answer = page(sidecar, markdown, args.page)
        elif args.heading is not None:
            answer = heading(sidecar, markdown, args.heading)
        elif args.equation is not None:
            answer = equation(sidecar, args.equation)
        elif args.search is not None:
            answer = search(markdown, args.search)
        else:
            answer = outline(sidecar)
    except FragmentError as exc:
        print(f"Not found: {exc}", file=sys.stderr)
        return 1
    answer = cap(answer, args.max_chars)
    if args.json:
        print(json.dumps(answer, ensure_ascii=False, indent=1))
    else:
        print(answer["text"])
        if "truncated" in answer:
            print(f"\n[truncated: {answer['truncated']['shown']} of {answer['truncated']['total']} characters]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The math panel's data: the paper's own LaTeX, condensed into cards.

Read-only. Sources, first match wins:

1. the latest proposal revision, ``proposals/research-concept-<slug>-rNN.md``:
   every display block (``$$`` alone on its line, the proposal's canonical
   form) with its ``\\tag{N}``, the heading it sits under and the first sentence
   of the paragraph after it as its "connection"; the matching
   ``proposals/research-concept-<slug>-rNN.sky.json`` overlay fills the novelty
   card (``sun``, ``novelty``, ``problem``, ``contribution`` planets);
2. ``.papersmith/model_spec.json`` (and the built-in MONEEG specification the
   model module already serves), normalised from its ``core_equations`` /
   ``optimization_problems`` / ``equations``;
3. nothing: an empty panel that says so, named after ``papersmith.yaml``.

The panel never invents mathematics: an empty source yields no equation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import model_spec

MAX_BYTES = 2 * 1024 * 1024
MAX_EQUATIONS = 40
TEXT_MAX = 600

_REVISION = re.compile(r"^research-concept-.+-r(\d+)\.md$")
_TAG = re.compile(r"\\tag\{([^{}]*)\}")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_SENTENCE = re.compile(r"^(.+?[.!?])(?:\s|$)", re.S)


def _first_sentence(text: str) -> str:
    text = " ".join(str(text or "").split())
    match = _SENTENCE.match(text)
    return (match.group(1) if match else text)[:TEXT_MAX]


def _read(path: Path) -> str | None:
    try:
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _yaml_field(root: Path, key: str) -> str:
    text = _read(root / "papersmith.yaml") or ""
    match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return match.group(1).strip().strip("'\"") if match else ""


# --------------------------------------------------------------------------
# proposals
# --------------------------------------------------------------------------
def _latest_proposal(root: Path) -> Path | None:
    folder = root / "proposals"
    if not folder.is_dir():
        return None
    ranked = []
    for path in folder.iterdir():
        match = _REVISION.match(path.name)
        if match and path.is_file():
            ranked.append((int(match.group(1)), path.name, path))
    return max(ranked)[2] if ranked else None


def _paragraph_after(lines: list[str], start: int) -> str:
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1
    paragraph = []
    while index < len(lines):
        line = lines[index].strip()
        if not line or line == "$$" or _HEADING.match(line):
            break
        paragraph.append(line)
        index += 1
    return " ".join(paragraph)


def equations_from_markdown(text: str) -> list[dict[str, Any]]:
    """Every closed ``$$`` display block, in order, with its context."""
    lines = text.splitlines()
    heading = ""
    found: list[dict[str, Any]] = []
    index = 0
    while index < len(lines) and len(found) < MAX_EQUATIONS:
        line = lines[index].strip()
        heading_match = _HEADING.match(line)
        if heading_match:
            heading = heading_match.group(2)
        if line != "$$":
            index += 1
            continue
        end = next((j for j in range(index + 1, len(lines)) if lines[j].strip() == "$$"), None)
        if end is None:
            break
        body = "\n".join(lines[index + 1:end]).strip()
        tag_match = _TAG.search(body)
        latex = _TAG.sub("", body).strip()
        if latex:
            found.append({
                "id": f"eq-{len(found) + 1}",
                "tag": tag_match.group(1).strip() if tag_match else str(len(found) + 1),
                "heading": heading,
                "latex": latex,
                "connection": _first_sentence(_paragraph_after(lines, end + 1)),
                "variables": [],
            })
        index = end + 1
    return found


def _novelty_from_sky(sky: Any, fallback_title: str) -> dict[str, Any]:
    planets = ((sky or {}).get("system") or {}).get("planets") if isinstance(sky, dict) else None
    planets = [p for p in planets or [] if isinstance(p, dict)]

    def first(slot: str, field: str = "label") -> str:
        for planet in planets:
            if planet.get("slot") == slot and isinstance(planet.get(field), str):
                return planet[field][:TEXT_MAX]
        return ""

    title = ((sky or {}).get("system") or {}).get("title") if isinstance(sky, dict) else ""
    return {
        "central_idea": first("sun") or (title if isinstance(title, str) else "") or fallback_title,
        "novelty": first("novelty"),
        "novelty_detail": first("novelty", "detail"),
        "problem": first("problem"),
        "problem_detail": first("problem", "detail"),
        "contributions": [p["label"][:TEXT_MAX] for p in planets
                          if p.get("slot") == "contribution" and isinstance(p.get("label"), str)],
    }


# --------------------------------------------------------------------------
# model specifications
# --------------------------------------------------------------------------
def _variables(raw: Any) -> list[dict[str, str]]:
    out = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            out.append({"symbol": str(item.get("sym") or item.get("symbol") or "")[:120],
                        "meaning": str(item.get("desc") or item.get("meaning") or "")[:TEXT_MAX]})
    return out


def equations_from_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    model = spec.get("mathematical_model") if isinstance(spec.get("mathematical_model"), dict) else {}
    raw = []
    for key in ("core_equations", "equations", "optimization_problems"):
        value = model.get(key)
        raw.extend(item for item in (value if isinstance(value, list) else []) if isinstance(item, dict))
    found = []
    for item in raw[:MAX_EQUATIONS]:
        latex = item.get("latex")
        if not isinstance(latex, str) or not latex.strip():
            continue
        number = str(item.get("number") or "").strip("() ")
        found.append({
            "id": str(item.get("id") or f"eq-{len(found) + 1}"),
            "tag": number or str(len(found) + 1),
            "heading": str(item.get("name") or "")[:TEXT_MAX],
            "latex": latex.strip(),
            "connection": _first_sentence(item.get("description") or ""),
            "variables": _variables(item.get("variables")),
        })
    return found


def _novelty_from_spec(spec: dict[str, Any], fallback_title: str) -> dict[str, Any]:
    novelty = spec.get("novelty") if isinstance(spec.get("novelty"), dict) else {}
    pillars = [p for p in novelty.get("pillars") or [] if isinstance(p, dict)]
    return {
        "central_idea": str(spec.get("title") or fallback_title)[:TEXT_MAX],
        "novelty": str(pillars[0].get("name") or "")[:TEXT_MAX] if pillars else "",
        "novelty_detail": str(pillars[0].get("summary") or "")[:TEXT_MAX] if pillars else "",
        "problem": _first_sentence(novelty.get("problem_statement") or ""),
        "problem_detail": "",
        "contributions": [str(p.get("name") or "")[:TEXT_MAX] for p in pillars[1:] if p.get("name")],
    }


# --------------------------------------------------------------------------
# the view
# --------------------------------------------------------------------------
def build(root: Path | str) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    title = _yaml_field(root, "title") or root.name
    topic = _yaml_field(root, "topic")

    proposal = _latest_proposal(root)
    if proposal is not None:
        text = _read(proposal) or ""
        sky_path = proposal.with_suffix(".sky.json")
        try:
            sky = json.loads(_read(sky_path) or "null")
        except ValueError:
            sky = None
        equations = equations_from_markdown(text)
        novelty = _novelty_from_sky(sky, title)
        source = f"proposal:{proposal.relative_to(root).as_posix()}"
        lema = novelty["novelty_detail"] or novelty["novelty"] or topic
    else:
        spec_file = root / ".papersmith" / "model_spec.json"
        spec = model_spec.get_model_specification(root)
        spec = spec if isinstance(spec, dict) else {}
        equations = equations_from_spec(spec)
        novelty = _novelty_from_spec(spec, title)
        if spec_file.is_file():
            source = "model_spec:.papersmith/model_spec.json"
        elif equations:
            source = "builtin:moneeg"
        else:
            source = "none"
            novelty = {"central_idea": title, "novelty": "", "novelty_detail": "", "problem": "",
                       "problem_detail": "", "contributions": []}
        lema = _first_sentence(spec.get("executive_summary") or "") if source != "none" else topic

    if not equations and source.startswith("proposal:"):
        lema = lema or topic
    novelty["key_equation"] = equations[0] if equations else None
    return {
        "title": title,
        "topic": topic,
        "source": source,
        "lema": lema or topic or title,
        "novelty": novelty,
        "equations": equations,
    }


__all__ = ["build", "equations_from_markdown", "equations_from_spec"]

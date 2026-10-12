#!/usr/bin/env python3
"""The manual's mechanical rules, as a check instead of a reading.

**Why this exists.** The manual was translated section by section, and every
section was verified by the same reading: does anything Spanish remain, did a
relative link survive, does a question still close. That reading costs minutes
per unit and depends on the reader's attention at hour three. The rules a
machine can decide are decided here instead; the one it cannot — the neutral
register — stays with the reader, deliberately, and this script never pretends
to judge it.

**How it knows what is untranslated.** Not from a word list, which is how a
check starts missing. From identity against the pinned Spanish original: a
heading or a prose line the manual still shares byte for byte with the text it
came from has not been translated. Measured on 2026-10-12, that rule finds the
21 headings of the untranslated sections and nothing in the 3,117 lines that are
already English, which is what makes it safe to fail a build on.

**What it cannot see, on purpose.**
- A heading of pure cognates that a translator left in place but reworded
  elsewhere is not identity, so it is not reported. Reworded is not untranslated.
- A Spanish question quoted *as an example* inside English prose is reported.
  The manual quotes Spanish invocations on purpose, and a human decides those.
- Markdown links: a line carrying `](` is exempt from the identity check, because
  a link line changes only when the prose around it does.

Exit code is 1 when any error was found, 0 otherwise. The script only reads; it
never writes to the manual.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FORGE = Path(__file__).resolve().parent.parent

#: The commit holdng the manual as it was before the translation began. The
#: record in `odd/tasks/readme-english.md` measures every unit against it.
PINNED_ORIGIN = "0d128f9"

#: The Spanish placeholders the brief sends to English. A real path, directory
#: or file name is never one of these, so a match is always residue.
PLACEHOLDERS = ("nombre", "puerto", "destino", "trabajo", "servicio", "carpeta")

#: How far a question may wrap before its `?` is considered missing.
QUESTION_WINDOW = 3

#: A line shorter than this, or carrying a URL or a link, survives translation
#: byte for byte often enough that identity proves nothing.
PROSE_MINIMUM = 40

ERROR = "error"
WARNING = "warning"

_PLACEHOLDER = re.compile(r"<(" + "|".join(PLACEHOLDERS) + r")>")
_HEADING = re.compile(r"^#{1,6}\s")
#: A heading the brief does translate. The document's one `#` line is the
#: project's own name, and the brief lists project names among the things that
#: never translate, so identity on it is the one heading match that proves
#: nothing.
_SECTION = re.compile(r"^#{2,6}\s")
_FENCE = re.compile(r"^\s*```")
_WORD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")
_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
_ABSOLUTE = ("http://", "https://", "mailto:", "#")


@dataclass(frozen=True)
class Finding:
    """One thing the manual does that its own rules forbid or doubt."""

    line: int
    severity: str
    code: str
    detail: str


def _numbered(text: str):
    """(number, line, inside_a_fence) for every line, numbers starting at 1."""
    inside = False
    for number, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            inside = not inside
            continue
        yield number, line, inside


def _in_scope(number: int, scope: tuple[int, int] | None) -> bool:
    return scope is None or scope[0] <= number <= scope[1]


_INLINE_CODE = re.compile(r"`[^`]*`")


def _is_translatable_prose(line: str) -> bool:
    """A line a translator has to rewrite, and whose identity therefore means it
    was not rewritten. Judged on the line with its inline code removed: a list of
    command names separated by commas is not prose, and it survives translation
    byte for byte, so its identity proves nothing."""
    stripped = _INLINE_CODE.sub(" ", line).strip()
    if len(stripped) < PROSE_MINIMUM:
        return False
    if stripped.startswith(("|", "<", "!", ">", "-", "*")):
        return False
    if "://" in stripped or "](" in stripped:
        return False
    return len(_WORD.findall(stripped)) >= 3


def _headings(text: str) -> dict[str, int]:
    return {line.strip(): number for number, line, inside in _numbered(text)
            if not inside and _SECTION.match(line)}


def _prose(text: str) -> set[str]:
    return {line.strip() for _, line, inside in _numbered(text)
            if not inside and _is_translatable_prose(line)}


def residue(text: str, original: str | None = None,
            scope: tuple[int, int] | None = None) -> list[Finding]:
    """Spanish left in the manual: punctuation, placeholders, and — when the
    pinned original is at hand — headings and prose lines that are still its own
    bytes."""
    original_headings = _headings(original) if original is not None else {}
    original_prose = _prose(original) if original is not None else set()
    lines = list(_numbered(text))
    found: list[Finding] = []
    for number, line, inside in lines:
        if not _in_scope(number, scope):
            continue
        stripped = line.strip()
        if "¿" in line or "¡" in line:
            found.append(Finding(number, ERROR, "inverted-punctuation", stripped))
            if not _closes_within(lines, number):
                found.append(Finding(number, ERROR, "unclosed-question", stripped))
        placeholder = _PLACEHOLDER.search(line)
        if placeholder:
            found.append(Finding(number, ERROR, "spanish-placeholder",
                                 f"<{placeholder.group(1)}> in {stripped}"))
        if inside:
            continue
        if original is not None and _SECTION.match(line) and stripped in original_headings:
            found.append(Finding(number, ERROR, "untranslated-heading", stripped))
        elif (original is not None and not _HEADING.match(line)
                and stripped in original_prose):
            found.append(Finding(number, WARNING, "untranslated-line", stripped))
    return found


def _closes_within(lines, start: int) -> bool:
    """Does a `?` appear on the question's line or the next few, allowing the
    question to wrap?"""
    for number, line, _ in lines:
        if number < start:
            continue
        if number > start + QUESTION_WINDOW:
            return False
        if "?" in line:
            return True
    return False


def _targets(text: str) -> list[tuple[int, str]]:
    """(line, target) for every relative markdown link or image, in order."""
    out: list[tuple[int, str]] = []
    for number, line, _ in _numbered(text):
        for target in _MARKDOWN_LINK.findall(line):
            if target.startswith(_ABSOLUTE):
                continue
            out.append((number, target))
    return out


def anchor_parity(original: str, current: str) -> list[Finding]:
    """Every relative target the original pointed at, still pointed at. The brief
    keeps them byte-identical, so a target that vanished is an error at the line
    where the original carried it."""
    here = {target for _, target in _targets(current)}
    seen: set[str] = set()
    found: list[Finding] = []
    for number, target in _targets(original):
        if target in here or target in seen:
            continue
        seen.add(target)
        found.append(Finding(number, ERROR, "anchor-missing",
                             f"{target} is in the original and not in the manual"))
    return found


def report(current: str, original: str | None = None,
           scope: tuple[int, int] | None = None) -> list[Finding]:
    """Every rule, in one list: residue first, then the anchors."""
    found = residue(current, original=original, scope=scope)
    if original is not None:
        found += anchor_parity(original, current)
    return found


def read_origin(origin: str) -> str | None:
    """The pinned manual, or None when this clone cannot resolve it."""
    proc = subprocess.run(["git", "show", f"{origin}:README.md"],
                          capture_output=True, text=True, cwd=FORGE)
    return proc.stdout if proc.returncode == 0 else None


def _scope(spec: str | None) -> tuple[int, int] | None:
    if not spec:
        return None
    first, _, last = spec.partition("-")
    return (int(first), int(last or first))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readme", default=str(FORGE / "README.md"))
    parser.add_argument("--origin", default=PINNED_ORIGIN,
                        help="the revision holding the untranslated manual")
    parser.add_argument("--no-origin", action="store_true",
                        help="skip identity and anchor checks; punctuation only")
    parser.add_argument("--lines", default=None, metavar="A-B",
                        help="restrict the check to a line range")
    parser.add_argument("--limit", type=int, default=0,
                        help="print at most N findings (0 prints all)")
    args = parser.parse_args(argv)

    path = Path(args.readme)
    current = path.read_text(encoding="utf-8")
    original = None if args.no_origin else read_origin(args.origin)
    if original is None and not args.no_origin:
        print(f"warning  the original at {args.origin} is not in this clone; "
              f"identity and anchor checks are off", file=sys.stderr)

    found = report(current, original=original, scope=_scope(args.lines))
    errors = [f for f in found if f.severity == ERROR]
    warnings = [f for f in found if f.severity == WARNING]

    print(f"manual: {path}")
    for index, finding in enumerate(found):
        if args.limit and index >= args.limit:
            print(f"... {len(found) - args.limit} more findings")
            break
        print(f"  {finding.severity:<7} line {finding.line:<5} "
              f"{finding.code:<22} {finding.detail[:100]}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

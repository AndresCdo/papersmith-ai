"""The section drawer shows each contract in Spanish without changing it.

The contracts under ``sections/`` stay in English: the paper-writing engine
checks every ``quote`` in their frontmatter against their own text. The
dashboard ships a Spanish copy of each, and serves it only while the
workspace's contract is the one it was translated from.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import server

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "sections"
COPIES = REPO / "skills" / "_core" / "command_center" / "static" / "i18n" / "es" / "sections"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def split(text: str) -> tuple[object, str]:
    match = FRONTMATTER.match(text)
    assert match, "a section contract opens with a JSON frontmatter block"
    return json.loads(match.group(1)), match.group(2)


def masked(node: object) -> object:
    """The frontmatter with every quote blanked: what a translation keeps."""
    if isinstance(node, dict):
        return {key: "" if key == "quote" else masked(value) for key, value in node.items()}
    if isinstance(node, list):
        return [masked(item) for item in node]
    return node


def quotes(node: object) -> list[tuple[str, str]]:
    """Every ``(file, quote)`` source the frontmatter cites."""
    if isinstance(node, dict):
        found = ([(node.get("file", ""), node["quote"])]
                 if isinstance(node.get("quote"), str) else [])
        return found + [q for key, value in node.items() if key != "quote" for q in quotes(value)]
    if isinstance(node, list):
        return [q for item in node for q in quotes(item)]
    return []


def flat(text: str) -> str:
    return " ".join(text.replace("*", "").replace("`", "").split())


class SpanishCopiesTests(unittest.TestCase):
    def test_every_contract_has_a_current_spanish_copy(self) -> None:
        recorded = json.loads((COPIES / "SOURCES.json").read_text(encoding="utf-8"))
        contracts = sorted(path.name for path in SOURCES.glob("*.md"))
        self.assertEqual(sorted(recorded), contracts)
        for name in contracts:
            with self.subTest(contract=name):
                self.assertTrue((COPIES / name).is_file())
                self.assertEqual(
                    recorded[name], hashlib.sha256((SOURCES / name).read_bytes()).hexdigest(),
                    f"sections/{name} changed: retranslate it and record its new sha256")

    def test_a_copy_keeps_the_contract_and_translates_only_its_quotes(self) -> None:
        for source in sorted(SOURCES.glob("*.md")):
            with self.subTest(contract=source.name):
                original, _ = split(source.read_text(encoding="utf-8"))
                copy, _ = split((COPIES / source.name).read_text(encoding="utf-8"))
                self.assertEqual(masked(copy), masked(original))
                # The engine matches a quote with emphasis stripped and
                # whitespace collapsed, against the file the source names.
                for cited, quote in quotes(copy):
                    _, body = split((COPIES / Path(cited).name).read_text(encoding="utf-8"))
                    self.assertTrue(flat(quote) in flat(body),
                                    f"{quote!r} is not a sentence of the Spanish {cited}")


class SectionTranslationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="section-es-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "sections").mkdir()
        self.name = "07-conclusions.md"
        shutil.copyfile(SOURCES / self.name, self.root / "sections" / self.name)
        app = server.create_app(self.root, history_store=None)
        self.route = next(r.endpoint for r in app.routes
                          if getattr(r, "path", None) == "/api/section-translation")

    def test_an_unchanged_contract_is_served_in_spanish(self) -> None:
        response = self.route(file=self.name, lang="es")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(bytes(response.body), (COPIES / self.name).read_bytes())

    def test_an_edited_contract_has_no_translation(self) -> None:
        contract = self.root / "sections" / self.name
        contract.write_text(contract.read_text(encoding="utf-8") + "\nOwn rule.\n",
                            encoding="utf-8")
        self.assertEqual(self.route(file=self.name, lang="es").status_code, 404)

    def test_a_missing_contract_has_no_translation(self) -> None:
        self.assertEqual(self.route(file="06-introduction.md", lang="es").status_code, 404)

    def test_only_a_plain_section_name_and_a_shipped_language_are_accepted(self) -> None:
        for file, lang in (("../papersmith.yaml", "es"), ("sub/07-conclusions.md", "es"),
                           ("07-conclusions.txt", "es"), (self.name, "fr"), ("", "es")):
            with self.subTest(file=file, lang=lang):
                self.assertEqual(self.route(file=file, lang=lang).status_code, 400)


if __name__ == "__main__":
    unittest.main()

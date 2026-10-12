"""Tests for scripts/check_manual.py, the manual's mechanical rules.

The rules are pure functions of two texts — the pinned Spanish original and the
manual as it stands — so most of this is strings, not the live README. Two tests
do read the live manual, and they assert only what already holds while the
translation is still in flight: every anchor is in place, and nothing above the
first untranslated heading carries inverted punctuation. The Spanish that is
still there is *measured*, never asserted away; a test demanding a fully English
manual would be red until the last unit lands, which is the opposite of a guard.

Why a script instead of a reading: every unit of this translation was verified by
hand, and the same four rules were re-checked from scratch each time. A rule a
machine can apply belongs in a machine, and the one a machine cannot apply — the
neutral register — stays with the reader.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parent.parent
SCRIPT = FORGE / "scripts" / "check_manual.py"


def _load():
    spec = importlib.util.spec_from_file_location("papersmith_check_manual", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


manual = _load()


def codes(findings):
    return [finding.code for finding in findings]


class ResidueTests(unittest.TestCase):
    def test_inverted_punctuation_is_an_error(self):
        found = manual.residue("Una frase normal.\n¿Qué es esto?\n")
        self.assertEqual(codes(found), ["inverted-punctuation"])
        self.assertEqual(found[0].line, 2)
        self.assertEqual(found[0].severity, "error")

    def test_a_spanish_placeholder_is_an_error(self):
        found = manual.residue("Run `papersmith init <nombre>` first.\n")
        self.assertEqual(codes(found), ["spanish-placeholder"])
        self.assertIn("<nombre>", found[0].detail)

    def test_an_english_placeholder_is_not_a_finding(self):
        self.assertEqual(manual.residue("Run `papersmith init <name>` first.\n"), [])

    def test_a_question_that_closes_across_a_line_break_is_not_unclosed(self):
        findings = manual.residue("¿Cómo funciona\neste comando?\n")
        self.assertNotIn("unclosed-question", codes(findings))

    def test_a_question_with_no_closing_mark_is_reported(self):
        findings = manual.residue("¿Cómo funciona esto.\n\nOtra frase aparte.\n")
        self.assertIn("unclosed-question", codes(findings))
        self.assertEqual([f.line for f in findings if f.code == "unclosed-question"], [1])

    def test_a_heading_identical_to_the_original_is_an_error(self):
        findings = manual.residue("## Arquitectura\n", original="## Arquitectura\n")
        self.assertEqual(codes(findings), ["untranslated-heading"])
        self.assertEqual(findings[0].line, 1)

    def test_a_translated_heading_is_not_a_finding(self):
        findings = manual.residue("## Architecture\n", original="## Arquitectura\n")
        self.assertEqual(findings, [])

    def test_a_heading_that_is_only_a_command_name_is_not_reported(self):
        # The brief never translates a command name, so a heading made of one is
        # not prose a translator was meant to rewrite.
        text = "### `papersmith init <dir>`\n"
        self.assertEqual(manual.residue(text, original=text), [])

    def test_a_heading_with_prose_in_it_is_still_reported(self):
        text = "### `papersmith init <dir>` and the files it writes\n"
        self.assertEqual(codes(manual.residue(text, original=text)),
                         ["untranslated-heading"])

    def test_the_level_one_title_is_the_project_name_and_is_never_reported(self):
        # The brief never translates the project's own name, so identity on the
        # document title is the one heading match that proves nothing.
        self.assertEqual(manual.residue("# papersmith-ai\n",
                                       original="# papersmith-ai\n"), [])

    def test_a_prose_line_identical_to_the_original_is_a_warning(self):
        line = "El motor no escribe nada hasta que el operador lo acepta.\n"
        findings = manual.residue(line, original=line)
        self.assertEqual(codes(findings), ["untranslated-line"])
        self.assertEqual(findings[0].severity, "warning")

    def test_a_short_or_url_carrying_identical_line_is_not_reported(self):
        # A command, a link and a badge survive translation byte for byte.
        for text in ("Ver `papersmith status`.\n",
                     "Ver [the manual](docs/README.md) para el resto del detalle.\n",
                     "  [![CI](https://example.test/badge.svg)](https://example.test)\n"):
            with self.subTest(text=text):
                self.assertEqual(manual.residue(text, original=text), [])

    def test_a_line_that_is_inline_code_and_commas_is_not_prose(self):
        # A list of command names survives translation byte for byte; it is not
        # a line a translator rewrites, so its identity proves nothing.
        text = "`/paper-ingestion`, `/proposal-deliberation`, `/experimental-deliberation`,\n"
        self.assertEqual(manual.residue(text, original=text), [])

    def test_a_prose_line_carrying_inline_code_is_still_prose(self):
        text = ("The engine writes nothing until the operator accepts it; "
                "`papersmith status` reports where that stands.\n")
        findings = manual.residue(text, original=text)
        self.assertEqual(codes(findings), ["untranslated-line"])

    def test_the_scope_limits_what_is_reported(self):
        text = "¿Uno?\n\n¿Dos?\n\n¿Tres?\n"
        found = manual.residue(text, scope=(3, 3))
        self.assertEqual([f.line for f in found], [3])

    def test_the_level_one_title_does_not_bound_a_scope(self):
        # The title is never a residue finding, so it cannot be what tells a
        # caller where the translated part ends.
        heads = [f.line for f in manual.residue("# papersmith-ai\n\n## Arquitectura\n",
                                                original="# papersmith-ai\n\n## Arquitectura\n")
                 if f.code == "untranslated-heading"]
        self.assertEqual(heads, [3])


class AnchorTests(unittest.TestCase):
    def test_a_relative_anchor_lost_in_translation_is_an_error(self):
        findings = manual.anchor_parity("[x](docs/a.md)\n", "[y](docs/b.md)\n")
        self.assertEqual(codes(findings), ["anchor-missing"])
        self.assertIn("docs/a.md", findings[0].detail)

    def test_a_relative_anchor_kept_byte_for_byte_is_a_match(self):
        text = "See [`docs/a.md`](docs/a.md).\n"
        self.assertEqual(manual.anchor_parity(text, text), [])

    def test_absolute_urls_and_fragments_are_not_compared(self):
        original = "[a](https://example.test/x) [b](#section)\n"
        current = "[a](https://example.test/y) [b](#other)\n"
        self.assertEqual(manual.anchor_parity(original, current), [])

    def test_a_fragment_that_matches_a_heading_resolves(self):
        text = "## The CLI commands\n\nSee [cli](#the-cli-commands).\n"
        self.assertEqual(manual.fragment_anchors(text), [])

    def test_a_fragment_with_no_heading_behind_it_is_an_error(self):
        text = "## The CLI commands\n\nSee [cli](#los-comandos-del-cli).\n"
        findings = manual.fragment_anchors(text)
        self.assertEqual(codes(findings), ["unresolved-anchor"])
        self.assertEqual(findings[0].line, 3)
        self.assertIn("los-comandos-del-cli", findings[0].detail)

    def test_an_em_dash_heading_slugifies_the_way_github_does_it(self):
        # The em dash leaves two spaces behind, so the slug carries two hyphens.
        self.assertEqual(manual.slug("Use flow — the short path"),
                         "use-flow--the-short-path")
        self.assertEqual(manual.slug("Cómputo remoto, con cuidado"),
                         "cómputo-remoto-con-cuidado")

    def test_a_heading_carrying_inline_code_slugifies_without_the_backticks(self):
        self.assertEqual(manual.slug("### `papersmith target {list,set,check}`"),
                         "papersmith-target-listsetcheck")

    def test_every_fragment_anchor_in_the_live_manual_resolves(self):
        current = (FORGE / "README.md").read_text(encoding="utf-8")
        findings = manual.fragment_anchors(current)
        self.assertEqual(findings, [], [f.detail for f in findings])


class ReportTests(unittest.TestCase):
    def test_the_report_collects_every_rule_in_one_list(self):
        findings = manual.report("¿Esto?\n[x](docs/b.md)\n",
                                 original="[a](docs/a.md)\n")
        self.assertEqual(codes(findings), ["inverted-punctuation", "anchor-missing"])

    def test_the_live_manual_keeps_every_anchor_of_its_pinned_original(self):
        original = _pinned_original(self)
        current = (FORGE / "README.md").read_text(encoding="utf-8")
        findings = manual.anchor_parity(original, current)
        self.assertEqual(findings, [], [f.detail for f in findings])

    def test_the_live_manual_has_no_errors_left(self):
        """The gate the record calls T9, arriving as soon as it can hold. While the
        translation was in flight this test bounded its own scope by the first
        untranslated heading, so it skipped once there were none; the manual being
        English end to end is now the invariant, and it is asserted directly."""
        current = (FORGE / "README.md").read_text(encoding="utf-8")
        errors = [f for f in manual.report(current, original=_pinned_original(self))
                  if f.severity == "error"]
        self.assertEqual(errors, [],
                         [f"line {f.line}: {f.code} {f.detail}" for f in errors])


class CommandLineTests(unittest.TestCase):
    def run_script(self, *argv, cwd=None):
        return subprocess.run([sys.executable, str(SCRIPT), *argv],
                              capture_output=True, text=True, cwd=cwd)

    def test_a_readme_with_residue_exits_nonzero_and_names_the_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            before = "## Architecture\n\nWrapped, and it still closes:\n¿what is this?\n"
            readme.write_text(before, encoding="utf-8")
            proc = self.run_script("--readme", str(readme), "--no-origin")
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertIn("inverted-punctuation", proc.stdout)
            self.assertIn("¿what is this?", proc.stdout)
            self.assertIn("1 errors", proc.stdout)
            self.assertEqual(readme.read_text(encoding="utf-8"), before)

    def test_an_english_readme_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("## Architecture\n\nNothing to close.\n", encoding="utf-8")
            proc = self.run_script("--readme", str(readme), "--no-origin")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("0 errors", proc.stdout)

    def test_a_range_restricts_the_check_to_its_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("## Architecture\n\n¿Uno?\n\nClean line.\n",
                              encoding="utf-8")
            proc = self.run_script("--readme", str(readme), "--no-origin",
                                   "--lines", "5-5")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("0 errors", proc.stdout)

    def test_the_origin_may_not_be_resolved_when_it_is_switched_off(self):
        # `--no-origin` must work from a directory that is not a repository at all.
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("## Architecture\n", encoding="utf-8")
            proc = self.run_script("--readme", str(readme), "--no-origin", cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


def _pinned_original(case):
    """The manual as it was before the translation, read from the pinned commit."""
    proc = subprocess.run(["git", "show", f"{manual.PINNED_ORIGIN}:README.md"],
                          capture_output=True, text=True, cwd=FORGE)
    if proc.returncode != 0:
        case.skipTest(f"{manual.PINNED_ORIGIN} is not in this clone")
    return proc.stdout


if __name__ == "__main__":
    unittest.main()

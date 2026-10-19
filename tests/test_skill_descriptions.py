"""Every skill description fits the ceiling the runtime that reads it enforces.

Pi validates a skill's `description` against the Agent Skills spec and caps it
at `MAX_DESCRIPTION_LENGTH = 1024` (`dist/core/skills.js:11`). Past the cap Pi
warns and loads the skill anyway, so nothing fails and the excess simply lives
on -- which is how two descriptions came to sit at 1680 and 1814 units while
every suite stayed green.

The unit is the one JS `length` counts: UTF-16 code units. Measuring in Python
characters would call a description legal that the runtime measures as over,
which is the whole difference the guard exists to catch.

OpenCode reads the same front matter through `.opencode/skills`, which a
workspace links to this tree. It holds `description` to the same 1024 ceiling,
and `name` to rules of its own (https://opencode.ai/docs/skills/): 1-64
lowercase alphanumerics in hyphen-joined runs, and the name of the directory
that holds the `SKILL.md` (#14).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest import mock

import yaml

from papersmith.generators import derive_command_description

FORGE_ROOT = Path(__file__).resolve().parents[1]
SKILLS = FORGE_ROOT / "skills"

#: Pi's ceiling, mirroring `MAX_DESCRIPTION_LENGTH` in `dist/core/skills.js`.
PI_DESCRIPTION_LIMIT = 1024

#: Skill front matter carries a long `Trigger: ...` paragraph on one line.
#: Single-line is the shape every harness's parser reads, so it is asserted
#: rather than assumed.
DESCRIPTION_RE = re.compile(r'^description:[ \t]*"(?P<value>.*)"[ \t]*$', re.MULTILINE)

#: The front matter block, which must open the file. YAML reads `name` inside
#: it, as a harness's loader does: quotes, comments and nesting are YAML's to
#: settle, and a `name:` in the body is not the skill's.
FRONT_MATTER_RE = re.compile(r"\A---\r?\n(?P<block>.*?)\r?\n---\r?\n", re.DOTALL)

#: OpenCode's rule for `name`, from the "Validate names" list of its skills
#: page: at most 64 characters, lowercase alphanumerics, single hyphens between.
OPENCODE_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
OPENCODE_NAME_LIMIT = 64


def _utf16_length(text: str) -> int:
    """The length JS `length` sees -- the unit the ceiling is written in."""
    return len(text.encode("utf-16-le")) // 2


def _skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


def _description(path: Path) -> str:
    matched = DESCRIPTION_RE.search(path.read_text(encoding="utf-8"))
    if matched is None:
        raise AssertionError(
            f"{path.relative_to(FORGE_ROOT)} has no single-line double-quoted "
            "`description:` in its front matter")
    return matched.group("value")


def _front_matter_name(text: str) -> str | None:
    """The string `name` the front matter of `text` declares, or None."""
    front = FRONT_MATTER_RE.match(text)
    data = yaml.safe_load(front.group("block")) if front else None
    name = data.get("name") if isinstance(data, dict) else None
    return name if isinstance(name, str) else None


def _name(path: Path) -> str:
    name = _front_matter_name(path.read_text(encoding="utf-8"))
    if name is None:
        raise AssertionError(
            f"{path.relative_to(FORGE_ROOT)} has no string `name:` in its front matter")
    return name


def _named() -> list[tuple[Path, str]]:
    return [(path, _name(path)) for path in _skill_files()]


def _measured() -> list[tuple[Path, str, int]]:
    return [(path, text, _utf16_length(text))
            for path, text in ((p, _description(p)) for p in _skill_files())]


class SkillDescriptionTests(unittest.TestCase):
    def test_there_is_a_description_to_measure_at_all(self) -> None:
        """A guard that measures nothing passes vacuously."""
        self.assertGreaterEqual(len(_skill_files()), 11)

    def test_every_skill_description_fits_the_pi_limit(self) -> None:
        over = [(path.relative_to(FORGE_ROOT).as_posix(), length)
                for path, _, length in _measured()
                if length > PI_DESCRIPTION_LIMIT]
        self.assertEqual(
            over, [],
            f"a skill description exceeds Pi's {PI_DESCRIPTION_LIMIT}-unit "
            f"ceiling (measured in UTF-16 code units, the unit JS `length` "
            f"counts): {over}")

    def test_every_skill_description_starts_with_the_trigger_convention(self) -> None:
        offenders = [path.relative_to(FORGE_ROOT).as_posix()
                     for path, text, _ in _measured()
                     if not text.startswith("Trigger:")]
        self.assertEqual(
            offenders, [],
            "a skill description does not open with the `Trigger:` convention "
            f"every harness routes on: {offenders}")

    def test_every_derived_command_description_is_non_empty(self) -> None:
        """`derive_command_description` keeps the first sentence, so a
        description with no sentence boundary still has to yield something."""
        empties = [path.relative_to(FORGE_ROOT).as_posix()
                   for path, text, _ in _measured()
                   if not derive_command_description(text).strip()]
        self.assertEqual(
            empties, [],
            f"a skill description derives an empty command description: {empties}")


class SkillNameTests(unittest.TestCase):
    """`SkillDescriptionTests.test_there_is_a_description_to_measure_at_all`
    keeps these from passing on an empty tree; a skill with no `name:` fails
    them outright."""

    def test_every_skill_name_is_its_directory(self) -> None:
        mismatched = [(path.relative_to(FORGE_ROOT).as_posix(), name)
                      for path, name in _named() if name != path.parent.name]
        self.assertEqual(
            mismatched, [],
            "a skill's front-matter `name` is not the directory that holds "
            f"its SKILL.md, which OpenCode requires: {mismatched}")

    def test_every_skill_name_follows_the_opencode_name_rule(self) -> None:
        invalid = [(path.relative_to(FORGE_ROOT).as_posix(), name)
                   for path, name in _named()
                   if len(name) > OPENCODE_NAME_LIMIT or not OPENCODE_NAME_RE.fullmatch(name)]
        self.assertEqual(
            invalid, [],
            f"a skill name breaks OpenCode's rule (at most {OPENCODE_NAME_LIMIT} "
            f"lowercase alphanumerics, single hyphens between): {invalid}")


class FrontMatterNameTests(unittest.TestCase):
    """The reader `SkillNameTests` stands on, on texts no shipped skill holds."""

    def test_a_name_reads_as_yaml_reads_it(self) -> None:
        for line in ("name: plausibility", 'name: "plausibility"',
                     "name: 'plausibility'", "name: plausibility  # the folder"):
            with self.subTest(line=line):
                text = f"---\n{line}\ndescription: x\n---\nbody\n"
                self.assertEqual(_front_matter_name(text), "plausibility")
        self.assertEqual(
            _front_matter_name("---\r\nname: plausibility\r\n---\r\n"), "plausibility")

    def test_a_text_that_declares_no_string_name_reads_as_none(self) -> None:
        for case, text in (
                ("no front matter", "name: plausibility\n"),
                ("front matter not first", "\n---\nname: plausibility\n---\n"),
                ("only the body names it", "---\ndescription: x\n---\nname: plausibility\n"),
                ("a nested key", "---\nmetadata:\n  name: plausibility\n---\n"),
                ("not a mapping", "---\n- plausibility\n---\n"),
                ("not a string", "---\nname: 42\n---\n"),
                ("empty", "---\nname:\n---\n")):
            with self.subTest(case=case):
                self.assertIsNone(_front_matter_name(text))

    def test_a_skill_that_declares_none_fails_loudly(self) -> None:
        skill = SKILLS / "plausibility" / "SKILL.md"
        with mock.patch.object(Path, "read_text", return_value="no front matter\n"):
            with self.assertRaisesRegex(
                    AssertionError, "skills/plausibility/SKILL.md has no string `name:`"):
                _name(skill)


if __name__ == "__main__":
    unittest.main()

"""Every checklist-holder filename a skill's docs spell is one some
implementation profile actually declares.

The holder name is a profile leaf (`PROFILE["holder"]["filename"]`), and
`settle`/`verify` read and write only that file. A doc that names any other
`*AGREE*.md` sends a reader to a file the engine never opens. The roster is
derived from the profiles, never listed here.
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
HOLDER_SPELLING = re.compile(r"[A-Za-z_]*AGREE[A-Za-z_]*\.md")


def _declared_holders() -> set[str]:
    holders = set()
    for profile in sorted(SKILLS.glob("*/impl_profile.py")):
        spec = importlib.util.spec_from_file_location(
            f"_holder_probe_{profile.parent.name.replace('-', '_')}", profile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        holders.add(module.PROFILE["holder"]["filename"])
    return holders


class HolderNameDocDriftTests(unittest.TestCase):
    def test_profiles_declare_holders(self) -> None:
        self.assertGreaterEqual(len(_declared_holders()), 1)

    def test_every_documented_holder_name_is_a_declared_one(self) -> None:
        declared = _declared_holders()
        docs = [*SKILLS.glob("*/SKILL.md"), *SKILLS.glob("*/references/*.md")]
        for doc in sorted(docs):
            text = doc.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                for spelled in HOLDER_SPELLING.findall(line):
                    with self.subTest(doc=str(doc.relative_to(ROOT)), line=lineno):
                        self.assertIn(spelled, declared,
                                      f"{doc.relative_to(ROOT)}:{lineno} names "
                                      f"{spelled}, which no profile declares")


if __name__ == "__main__":
    unittest.main()

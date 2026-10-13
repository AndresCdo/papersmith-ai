"""`declared_holder_filenames` -- the holder names every profile sharing one
engine declares, derived from the profiles themselves (never a hand-kept list).

`holder_resolution` excludes these names from its by-shape candidates, so a
sibling skill's own declared holder is never mistaken for an undeclared
checklist this skill should rename or adopt. The derivation must fail closed:
a sibling profile that cannot be read, or declares a malformed holder,
contributes nothing, so its file stays a candidate and still refuses.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
SKILLS = FORGE / "skills"
CORE = SKILLS / "_core" / "implementation"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_profile import seeded_profile  # noqa: E402  (path set above)


def _load_profile_resolver():
    """A fresh load of `impl_domain_profile` under a real shipped profile,
    never the cached module another test file may have resolved."""
    spec = importlib.util.spec_from_file_location(
        "impl_domain_profile_under_test", CORE / "impl_domain_profile.py")
    module = importlib.util.module_from_spec(spec)
    with seeded_profile(SKILLS / "proposal-implementation" / "impl_profile.py"):
        spec.loader.exec_module(module)
    return module


def _declared_by(path: Path) -> str:
    spec = importlib.util.spec_from_file_location("profile_reader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PROFILE["holder"]["filename"]


class DeclaredHolderFilenamesTests(unittest.TestCase):

    def setUp(self) -> None:
        self.resolver = _load_profile_resolver()

    def test_the_shipped_profiles_contribute_exactly_their_own_declared_names(self):
        """Derived on both sides: whatever each shipped `impl_profile.py`
        declares is what the engine excludes -- adding a third sibling skill
        needs no edit here or in the engine."""
        expected = {_declared_by(path) for path in SKILLS.glob("*/impl_profile.py")}
        self.assertTrue(expected, "no shipped profile found to derive from")
        self.assertEqual(self.resolver.declared_holder_filenames(SKILLS),
                         frozenset(expected))

    def test_an_unreadable_or_malformed_sibling_contributes_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)

            def profile(skill: str, body: str) -> None:
                (root / skill).mkdir()
                (root / skill / "impl_profile.py").write_text(
                    textwrap.dedent(body), encoding="utf-8")

            profile("good", 'PROFILE = {"holder": {"filename": "Good_AGREED.md"}}\n')
            profile("raises", 'raise RuntimeError("broken sibling")\n')
            profile("no-profile", "VALUE = 1\n")
            profile("not-a-mapping", "PROFILE = []\n")
            profile("no-holder", "PROFILE = {}\n")
            profile("path", 'PROFILE = {"holder": {"filename": "sub/X.md"}}\n')
            profile("suffix", 'PROFILE = {"holder": {"filename": "X.txt"}}\n')
            profile("not-str", 'PROFILE = {"holder": {"filename": 3}}\n')
            profile("syntax", "PROFILE = {\n")
            # A directory without a profile is not a sibling at all.
            (root / "_core").mkdir()

            self.assertEqual(self.resolver.declared_holder_filenames(root),
                             frozenset({"Good_AGREED.md"}))

    def test_a_missing_root_contributes_nothing(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(
                self.resolver.declared_holder_filenames(Path(raw) / "absent"),
                frozenset())


if __name__ == "__main__":
    unittest.main()

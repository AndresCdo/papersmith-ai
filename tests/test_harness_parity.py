"""Every harness the setup script serves must be visible in a fresh clone.

`scripts/setup-harnesses.sh` projects the canonical `skills/` tree into one
directory per harness. Those links are generated, so they are ignored -- but
ignoring the whole harness directory instead of just the link makes that
harness invisible to anyone who clones the repository. A collaborator then
sees three harness directories, concludes the fourth is unsupported, and is
reasonably right to: nothing in the tree says otherwise.

That is what happened to Pi. `.gitignore` carried `.pi/` where its siblings
carried `.claude/skills`, so no file under `.pi/` could ever be committed and
the directory did not exist until somebody ran the setup script.

The roster below is derived from the shell script's own `HARNESSES` array
rather than restated here, because a fifth harness added to that array and not
to this file is exactly the drift these assertions exist to catch.
"""

import re
import subprocess
import unittest
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parent.parent
SETUP = FORGE_ROOT / "scripts" / "setup-harnesses.sh"
GITIGNORE = FORGE_ROOT / ".gitignore"

#: `  ".pi/skills:Pi"` -> ("\.pi/skills", "Pi"). Matched against the array the
#: script actually iterates, so the test cannot pass over a roster nobody uses.
ENTRY = re.compile(r'^\s*"([^":]+):([^"]+)"\s*$', re.MULTILINE)


def declared_harnesses() -> list[tuple[str, str]]:
    """Every `<relative skills dir>, <label>` pair the setup script serves."""
    source = SETUP.read_text(encoding="utf-8")
    block = re.search(r"HARNESSES=\((.*?)\n\)", source, re.DOTALL)
    if not block:
        raise AssertionError(
            f"no HARNESSES=( ... ) array found in {SETUP}; this test derives "
            "its roster from that array and has nothing to assert without it")
    return ENTRY.findall(block.group(1))


class HarnessParityTests(unittest.TestCase):
    def test_the_roster_is_derived_and_not_empty(self) -> None:
        """Non-vacuity. A regex that stopped matching would make every
        assertion below pass over an empty list, and a roster that found no
        harnesses reads exactly like a repository with no drift."""
        found = declared_harnesses()
        self.assertGreaterEqual(
            len(found), 4,
            f"derived only {found} from {SETUP.name}; the assertions below "
            "would be checking nothing")
        self.assertIn("Pi", [label for _, label in found])

    def test_each_harness_ignores_its_generated_link_and_nothing_more(self) -> None:
        """The link is generated, so it is ignored. The directory holding it
        is not generated, and ignoring it hides the harness from the tree."""
        ignored = {line.strip() for line in GITIGNORE.read_text(encoding="utf-8").split("\n")}
        for rel, label in declared_harnesses():
            with self.subTest(harness=label):
                self.assertIn(
                    rel, ignored,
                    f"{label}'s generated link `{rel}` is not ignored; a "
                    "rebuilt symlink would show up as a repository change")
                parent = rel.split("/")[0]
                for shape in (parent, f"{parent}/"):
                    self.assertNotIn(
                        shape, ignored,
                        f"`{shape}` ignores {label}'s whole directory, not "
                        f"just its generated link. Nothing under it can be "
                        f"committed, so the directory does not exist in a "
                        f"fresh clone and {label} reads as unsupported")

    def test_each_harness_directory_travels_with_the_repository(self) -> None:
        """Ignoring only the link is permission, not presence. A directory
        with nothing committed in it still arrives absent."""
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=FORGE_ROOT,
            capture_output=True, text=True, check=True).stdout.split("\n")
        for rel, label in declared_harnesses():
            parent = rel.split("/")[0]
            with self.subTest(harness=label):
                carried = [p for p in tracked if p.startswith(f"{parent}/")]
                self.assertTrue(
                    carried,
                    f"{parent}/ holds no committed file, so it is absent from "
                    f"a fresh clone and a collaborator has no sign {label} is "
                    "a supported harness. One tracked file is enough, and it "
                    "should say why the directory looks empty")


if __name__ == "__main__":
    unittest.main()

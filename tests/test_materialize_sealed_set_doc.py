"""The sealed set `materialize --authored`/`--adopt` accept is stated in the
docs exactly as the engine computes it, and the refusal names it.

`NOT_A_KIT_DESTINATION` is what a reader meets when they name any other
path. Both halves are derived: the code half from `all_kit_destinations`
itself (in a subprocess, so the profile variable never leaks into this
process), the documented half from the list under the usage guide's own
heading.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "proposal-implementation"
USAGE = SKILL / "references" / "usage.md"
HEADING = "#### The sealed set"
NAME = "Example-Method"

PROBE = r"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import implementation_engine as impl
name = sys.argv[2]
out = {"package": impl.package_name(name),
       "destinations": impl.all_kit_destinations(name)}
with tempfile.TemporaryDirectory() as box:
    for mode in ("authored", "adopt"):
        fn = getattr(impl, "_materialize_" + mode)
        try:
            fn(Path(box), name, "README.md")
        except impl.Refused as refused:
            out[mode] = [refused.code, str(refused)]
print(json.dumps(out))
"""


def _engine_facts() -> dict:
    env = {k: v for k, v in os.environ.items()
           if k != "IMPLEMENTATION_DOMAIN_PROFILE"}
    env["IMPLEMENTATION_DOMAIN_PROFILE"] = str(SKILL / "impl_profile.py")
    ran = subprocess.run(
        [sys.executable, "-c", PROBE,
         str(ROOT / "skills/_core/implementation/engine"), NAME],
        capture_output=True, text=True, env=env, check=True)
    return json.loads(ran.stdout)


def _documented() -> list[str]:
    lines = USAGE.read_text(encoding="utf-8").splitlines()
    start = lines.index(HEADING)
    listed, seen_item = [], False
    for line in lines[start + 1:]:
        match = re.fullmatch(r"- `([^`]+)`(?: .*)?", line)
        if match:
            listed.append(match.group(1))
            seen_item = True
        elif line.startswith("#"):
            break
        elif seen_item and line.strip() and not line.startswith("  "):
            break
    return listed


class SealedSetDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = _engine_facts()

    def _code_list(self) -> list[str]:
        package = self.facts["package"]
        return [d.replace(f"src/{package}", "src/<Package>")
                 .replace(f"{NAME}/", "<Name>/")
                for d in self.facts["destinations"]]

    def test_usage_lists_exactly_the_engine_destinations(self) -> None:
        self.assertEqual(_documented(), self._code_list())

    def test_the_refusal_names_every_accepted_path(self) -> None:
        for mode in ("authored", "adopt"):
            with self.subTest(mode=mode):
                code, detail = self.facts[mode]
                self.assertEqual(code, "NOT_A_KIT_DESTINATION")
                for destination in self.facts["destinations"]:
                    self.assertIn(destination, detail)


if __name__ == "__main__":
    unittest.main()

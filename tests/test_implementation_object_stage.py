"""C11: the objects stage follows the package the approved map produced.

`materialize --stage objects` always wrote the literal `src/<Package>/module.py`,
and `verify`'s `structure.objectGaps` reported that path missing on any target
without it -- even one whose approved object map had already been written as
modules of their own names (`kernel.py`, `estimator.py`), so the structure
never read `ok` without a file nobody asked for.

Now the module destination is owed only while the package holds no module of
its own (the kit's own seal and `__init__.py` do not count), and `--module
<name>` names the module the stage writes. A target that already carries
`module.py` keeps verifying exactly as before.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from implementation_lifecycle import PACKAGE, Target  # noqa: E402

PROVENANCE_MODULE = (
    '"""A module of the approved map."""\n\n'
    '__provenance__ = {"revision": "draft-1.md", "sections": ["3"],\n'
    '                  "equations": ["3.1"], "invariants": []}\n\n\n'
    'def kernel(x):\n    return x\n'
)
MODULE = f"src/{PACKAGE}/module.py"


class ObjectStageFollowsTheMapTests(unittest.TestCase):
    def declared(self, suffix: str) -> Target:
        target = Target(self, suffix)
        target.scaffold()
        target.declare()
        return target

    def test_a_fresh_package_still_owes_the_default_module(self) -> None:
        target = self.declared("default")
        self.assertIn(MODULE, target.verify()["structure"]["objectGaps"])
        done = target.objects()
        self.assertEqual(done.get("status"), "materialized", done)
        self.assertIn(MODULE, done["written"])

    def test_a_package_with_its_own_module_owes_no_module_py(self) -> None:
        target = self.declared("own")
        (target.root / "src" / PACKAGE / "kernel.py").write_text(PROVENANCE_MODULE,
                                                                encoding="utf-8")
        target.commit("map")
        self.assertNotIn(MODULE, target.verify()["structure"]["objectGaps"])
        done = target.objects()
        self.assertEqual(done.get("status"), "materialized", done)
        self.assertNotIn(MODULE, done["written"])
        self.assertFalse((target.root / MODULE).exists())
        self.assertEqual(target.verify()["structure"]["objectGaps"], [])

    def test_the_module_flag_names_the_module_the_stage_writes(self) -> None:
        target = self.declared("named")
        done = target.objects("--module", "estimator")
        self.assertEqual(done.get("status"), "materialized", done)
        named = f"src/{PACKAGE}/estimator.py"
        self.assertIn(named, done["written"])
        self.assertFalse((target.root / MODULE).exists())
        self.assertEqual(target.receipt()[named]["stage"], "objects")
        self.assertEqual(target.verify()["structure"]["objectGaps"], [])

    def test_a_named_module_is_sealed_like_the_default_one(self) -> None:
        target = self.declared("sealed")
        target.objects("--module", "estimator")
        target.commit("objects")
        named = f"src/{PACKAGE}/estimator.py"
        (target.root / named).write_text(PROVENANCE_MODULE, encoding="utf-8")
        self.assertIn(named, target.verify()["structure"]["objectDrift"])
        authored = target.materialize("--authored", named)
        self.assertEqual(authored.get("status"), "authored", authored)
        self.assertNotIn(named, target.verify()["structure"]["objectDrift"])

    def test_a_module_name_that_is_not_an_identifier_or_is_the_kits_own_refuses(self) -> None:
        target = self.declared("invalid")
        for bad in ("1kernel", "kernel-map", "__init__", "report_digest", "class"):
            with self.subTest(module=bad):
                result = target.objects("--module", bad)
                self.assertEqual(result.get("code"), "MODULE_NAME_INVALID", result)
        self.assertFalse((target.root / MODULE).exists())

    def test_the_module_flag_belongs_to_the_objects_stage(self) -> None:
        target = Target(self, "stage")
        result = target.materialize("--stage", "harness", "--plan", target.plan(),
                                    "--module", "estimator")
        self.assertEqual(result.get("code"), "MODULE_STAGE_MISMATCH", result)

    def test_a_target_that_already_has_module_py_keeps_verifying(self) -> None:
        target = self.declared("legacy")
        target.objects()
        target.commit("objects")
        structure = target.verify()["structure"]
        self.assertEqual(structure["objectGaps"], [])
        self.assertEqual(structure["objectDrift"], [])
        self.assertEqual(structure["unrecordedObjects"], [])


if __name__ == "__main__":
    unittest.main()

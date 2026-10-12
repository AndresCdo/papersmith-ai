"""C10: a remedy test's control is recognized however it reaches the package.

`remediesWithoutControl` accepted a `test_remedy_<id>` only when it called a
name imported with `from <package>... import <name>` directly by that bare
name. Calling the declared implementation through a module (`mod.fn(...)`,
`import <package>.x as m; m.fn(...)`) or through a helper defined in the same
file read as "never exercises the implementation", so a correct control was
reported missing and the audit stayed `incomplete`.

The detection now follows the three spellings without loosening what it
demands: the test (or a same-file helper it calls, transitively) must CALL
something bound to the target's own package. Importing the package and never
calling into it, calling a helper that never reaches it, or calling a method
of an unrelated module still reads as no control.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
NAME = "Method"
PACKAGE = "Method"
REVISION = "draft-1.md"

REMEDIES = '''
import math
import Method
import Method.kernel as kernel_module
from Method import kernel
from Method.kernel import declared_form


def _helper_reaching():
    return kernel.declared_form(1.0)


def _helper_through_helper():
    return _helper_reaching()


def _helper_not_reaching():
    return math.sqrt(4.0)


def test_remedy_bare_name():
    assert declared_form(1.0) != 2.0


def test_remedy_module_attribute():
    assert kernel.declared_form(1.0) != 2.0


def test_remedy_aliased_module():
    assert kernel_module.declared_form(1.0) != 2.0


def test_remedy_package_attribute_chain():
    assert Method.kernel.declared_form(1.0) != 2.0


def test_remedy_helper():
    assert _helper_reaching() != 2.0


def test_remedy_helper_of_a_helper():
    assert _helper_through_helper() != 2.0


def test_remedy_imports_but_never_calls():
    assert kernel is not None


def test_remedy_unrelated_module_call():
    assert math.sqrt(4.0) == 2.0


def test_remedy_helper_that_never_reaches():
    assert _helper_not_reaching() == 2.0


def test_remedy_references_without_calling():
    reference = declared_form
    assert reference is not None
'''

REACHING = {"test_remedy_bare_name", "test_remedy_module_attribute",
            "test_remedy_aliased_module", "test_remedy_package_attribute_chain",
            "test_remedy_helper", "test_remedy_helper_of_a_helper"}
NOT_REACHING = {"test_remedy_imports_but_never_calls", "test_remedy_unrelated_module_call",
                "test_remedy_helper_that_never_reaches",
                "test_remedy_references_without_calling"}


class RemedyControlDetectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        proposals = Path(tempfile.mkdtemp())
        box = FORGE / "implementations" / f"_remedy_control_{os.getpid()}"
        try:
            (proposals / REVISION).write_text("## 3\n\n$$\na = b \\tag{3.1}\n$$\n",
                                              encoding="utf-8")
            shutil.rmtree(box, ignore_errors=True)
            (box / "src" / PACKAGE).mkdir(parents=True)
            (box / "tests").mkdir()
            subprocess.run(["git", "init", "-q", str(box)], check=True)
            (box / "src" / PACKAGE / "__init__.py").write_text(
                f"__implementation__ = {{'revision': '{REVISION}', 'premises': {{}}}}\n",
                encoding="utf-8")
            (box / "tests" / "test_remedies.py").write_text(REMEDIES, encoding="utf-8")
            env = {k: v for k, v in os.environ.items()
                   if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")}
            env["IMPLEMENTATION_PROPOSALS"] = str(proposals)
            proc = subprocess.run([sys.executable, str(CLI), "verify", "--target", str(box),
                                   "--name", NAME, "--revision", REVISION],
                                  capture_output=True, text=True, env=env, cwd=FORGE)
            cls.uncontrolled = set(json.loads(proc.stdout)["audit"]["remediesWithoutControl"])
        finally:
            shutil.rmtree(box, ignore_errors=True)
            shutil.rmtree(proposals, ignore_errors=True)

    def test_every_spelling_that_calls_into_the_package_is_a_control(self) -> None:
        self.assertEqual(sorted(self.uncontrolled & REACHING), [])

    def test_nothing_that_never_calls_into_the_package_is_a_control(self) -> None:
        self.assertEqual(sorted(NOT_REACHING - self.uncontrolled), [])


if __name__ == "__main__":
    unittest.main()

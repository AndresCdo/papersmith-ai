"""C12: kit placeholders are filled when their value is known, and say so when not.

`materialize` substituted only `{{PKG}}` and `{{SEED}}`. Everything else was
left for an agent to fill by hand, including values the engine already held:
the product name, the bound revision (in `tests/test_smoke.py`,
`tests/admissibility.py`, the verification notebook) and, once step 9 names
it, the module. A suite run before anybody filled them failed in ways that
named nothing useful -- `'r01.md' != '{{REVISION}}'`, a remedy refused against
"revision '{{REVISION}}'", and a `SyntaxError` at collection for `def
{{FUNCTION_NAME}}`.

Now:

- the scaffold stage answers `{{NAME}}`, and `{{REVISION}}` when it is known
  (the target already declares one, or the approved plan was bound to one);
- the objects stage, which runs only once step 8 declared the revision,
  answers `{{REVISION}}`, `{{NAME}}` and `{{MODULE}}` in what it writes, and
  fills the same tokens into every scaffold file still byte-identical to its
  receipt, re-sealing each one -- a file somebody edited is never touched;
- what is still unanswered fails with a message naming the token's step
  rather than a bare mismatch or a collection `SyntaxError`.

Targets materialized before this change keep their files and receipts: none
of this rewrites a file whose bytes moved from what its receipt sealed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from implementation_lifecycle import NAME, PACKAGE, REVISION, Target  # noqa: E402

SMOKE = "tests/test_smoke.py"
ADMISSIBILITY = "tests/admissibility.py"
NOTEBOOK = f"{NAME}/Notebooks/verification.ipynb"


def read(target: Target, rel: str) -> str:
    return (target.root / rel).read_text(encoding="utf-8")


def pytest_in(target: Target, *args: str) -> str:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           *args], cwd=str(target.root), capture_output=True, text=True)
    return proc.stdout + proc.stderr


class ScaffoldStageAnswersWhatItKnowsTests(unittest.TestCase):
    def test_the_product_name_is_always_answered(self) -> None:
        target = Target(self, "name")
        target.scaffold()
        self.assertNotIn("{{NAME}}", read(target, NOTEBOOK))
        self.assertIn(f"{NAME}/Notebooks/verification.ipynb", read(target, NOTEBOOK))

    def test_a_revision_the_plan_is_bound_to_is_answered_at_scaffold_time(self) -> None:
        target = Target(self, "bound")
        target.scaffold("--revision", REVISION)
        for rel in (SMOKE, ADMISSIBILITY, NOTEBOOK):
            with self.subTest(rel=rel):
                self.assertNotIn("{{REVISION}}", read(target, rel))
                self.assertIn(REVISION, read(target, rel))
        entry = target.receipt()[ADMISSIBILITY]
        self.assertEqual(entry["substitutions"].get("REVISION"), REVISION)

    def test_an_unknown_revision_is_left_standing_and_fails_clearly(self) -> None:
        target = Target(self, "unknown")
        target.scaffold()
        self.assertIn("{{REVISION}}", read(target, ADMISSIBILITY))
        probe = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, 'tests'); import admissibility, json, pathlib;"
             "pathlib.Path('tests/admissibility.json').write_text(json.dumps("
             "{'revision': 'x.md', 'findings': {'f': {'admissible': True}}}));"
             "admissibility.require_admissible('f')"],
            cwd=str(target.root), capture_output=True, text=True)
        self.assertNotEqual(probe.returncode, 0)
        self.assertIn("--stage objects", probe.stderr)
        self.assertNotIn("re-run `implementation_cli.py admit --revision {{REVISION}}`",
                         probe.stderr)

    def test_the_smoke_suite_says_which_answer_it_is_still_missing(self) -> None:
        target = Target(self, "smoke")
        target.scaffold()
        output = pytest_in(target, SMOKE)
        self.assertIn("does not know the bound revision", output)
        self.assertIn("step 9 has not named the module", output)
        self.assertIn(f"No module named '{PACKAGE}.", output)

    def test_the_scaffold_receipt_still_verifies(self) -> None:
        target = Target(self, "verifies")
        target.scaffold("--revision", REVISION)
        structure = target.verify()["structure"]
        self.assertEqual(structure["scaffoldDrift"], [])
        self.assertEqual(structure["unrecordedScaffold"], [])


class ObjectStageAnswersAndRefillsTests(unittest.TestCase):
    def declared(self, suffix: str) -> Target:
        target = Target(self, suffix)
        target.scaffold()
        target.declare()
        return target

    def test_the_objects_it_writes_carry_the_revision_name_and_module(self) -> None:
        target = self.declared("objects")
        done = target.objects("--module", "estimator")
        self.assertEqual(done.get("status"), "materialized", done)
        module = read(target, f"src/{PACKAGE}/estimator.py")
        self.assertIn(f'"revision": "{REVISION}"', module)
        self.assertIn(f"from {PACKAGE}.estimator import", read(target, "tests/test_invariants.py"))
        # Step 9's own answers stay standing: nothing here can know them.
        self.assertIn("{{FUNCTION_NAME}}", module)

    def test_untouched_scaffold_files_are_filled_and_resealed(self) -> None:
        target = self.declared("refill")
        done = target.objects("--module", "estimator")
        self.assertIn(SMOKE, done.get("filled", []), done)
        smoke = read(target, SMOKE)
        self.assertIn(f'"{PACKAGE}.estimator"', smoke)
        self.assertIn(f'"{REVISION}"', smoke)
        self.assertNotIn("{{REVISION}}", read(target, ADMISSIBILITY))
        self.assertNotIn("{{REVISION}}", read(target, NOTEBOOK))
        target.commit("objects")
        structure = target.verify()["structure"]
        self.assertEqual(structure["scaffoldDrift"], [])
        self.assertEqual(target.receipt()[SMOKE]["kind"], "materialized")

    def test_a_scaffold_file_somebody_edited_is_never_touched(self) -> None:
        target = self.declared("edited")
        path = target.root / ADMISSIBILITY
        edited = path.read_text(encoding="utf-8") + "\n# edited by hand\n"
        path.write_text(edited, encoding="utf-8")
        target.commit("edit")
        done = target.objects("--module", "estimator")
        self.assertNotIn(ADMISSIBILITY, done.get("filled", []), done)
        self.assertEqual(path.read_text(encoding="utf-8"), edited)

    def test_a_test_file_step_nine_has_not_authored_fails_naming_its_tokens(self) -> None:
        target = self.declared("collect")
        target.objects("--module", "estimator")
        output = pytest_in(target, "tests/test_invariants.py")
        self.assertIn("{{FUNCTION_NAME}}", output)
        self.assertIn("step 9", output)
        self.assertNotIn("SyntaxError", output)
        self.assertIn("1 failed", output)


if __name__ == "__main__":
    unittest.main()

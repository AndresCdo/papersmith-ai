"""E4: the message `walk` commits each step's product under is configurable.

`walk` commits what every local step left in the tree, because `step` refuses
on a dirty tree. The subject line was fixed at `walk: <step>`, so a target
that enforces Conventional Commits (a commit-msg hook, a CI lint) refused
every walked commit or carried history its own policy rejects.

`walk --commit-template` now takes the subject as a template with one
placeholder, `{step}`. The default stays `walk: {step}`, byte-identical to the
old subject. A template that names no `{step}`, carries any other brace, spans
more than one line, or is blank is refused before anything runs -- a commit
nobody can trace back to its step is worse than the mechanical default.

No receipt or ledger records the message (the walk's own output never did),
so nothing already on disk changes.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
ENGINE = FORGE / "skills/_core/implementation/engine/implementation_engine.py"
sys.path.insert(0, str(ENGINE.parent))
from domain_profile import seeded_profile  # noqa: E402  (path set above)
with seeded_profile(FORGE / "skills/proposal-implementation/impl_profile.py"):
    import implementation_engine as impl  # noqa: E402  (path set above)
from impl_refusals import Refused  # noqa: E402  (path set above)


def _git(repo: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *argv], check=True,
                          capture_output=True, text=True).stdout.strip()


class CommitSubjectTests(unittest.TestCase):
    def test_the_default_is_the_old_subject(self) -> None:
        self.assertEqual(impl.WALK_COMMIT_TEMPLATE, "walk: {step}")
        self.assertEqual(impl.walk_commit_subject(impl.WALK_COMMIT_TEMPLATE, "alpha"),
                         "walk: alpha")

    def test_a_conventional_commit_template_is_filled(self) -> None:
        self.assertEqual(impl.walk_commit_subject("chore(walk): {step}", "alpha"),
                         "chore(walk): alpha")

    def test_the_placeholder_may_repeat(self) -> None:
        self.assertEqual(impl.walk_commit_subject("feat({step}): run {step}", "b"),
                         "feat(b): run b")

    def test_a_malformed_template_is_refused(self) -> None:
        for template in ("chore: walked", "feat: {name}", "feat: {step} {",
                         "feat: {step}\n\nbody", "   ", ""):
            with self.subTest(template=template):
                with self.assertRaises(Refused) as caught:
                    impl.walk_commit_subject(template, "alpha")
                self.assertEqual(caught.exception.code, "WALK_COMMIT_TEMPLATE_MALFORMED")


class WalkedCommitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "walker@example.invalid")
        _git(self.repo, "config", "user.name", "Walker")
        (self.repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "seed")

    def _dirty(self) -> None:
        (self.repo / "product.txt").write_text("product\n", encoding="utf-8")

    def test_the_default_subject_is_unchanged(self) -> None:
        self._dirty()
        impl._commit_walked_step(self.repo, "alpha")
        self.assertEqual(_git(self.repo, "log", "-1", "--format=%s"), "walk: alpha")

    def test_the_template_shapes_the_subject(self) -> None:
        self._dirty()
        impl._commit_walked_step(self.repo, "alpha", "chore(walk): {step}")
        self.assertEqual(_git(self.repo, "log", "-1", "--format=%s"), "chore(walk): alpha")


class WalkFlagTests(unittest.TestCase):
    def test_a_malformed_template_refuses_before_anything_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ran = subprocess.run(
                [sys.executable, str(CLI), "walk", "--target", str(Path(tmp) / "absent"),
                 "--name", "Method", "--session", "s1", "--commit-template", "chore: walked"],
                capture_output=True, text=True,
                env={k: v for k, v in os.environ.items()
                     if k != "IMPLEMENTATION_DOMAIN_PROFILE"})
        self.assertNotEqual(ran.returncode, 0)
        self.assertIn("WALK_COMMIT_TEMPLATE_MALFORMED", ran.stdout + ran.stderr)


if __name__ == "__main__":
    unittest.main()

"""An unreadable `--plan` is a refusal, never a forge defect (#67).

`apply` and `materialize --stage` read the approved plan with a bare
`json.loads(Path(...).read_text())`. A missing, malformed or non-object plan
raised out of the command, `main()`'s catch-all recorded it as a forge-side
defect, and the open defect then refused `FORGE_DEFECT_OPEN` on every gating
command -- one mistyped path poisoned the target's lifecycle. `adopt --apply`
already refused `PLAN_STALE` for the same input; these now do too.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
ENGINE = FORGE / "skills/_core/implementation/engine/implementation_engine.py"
sys.path.insert(0, str(ENGINE.parent))
from domain_profile import seeded_profile  # noqa: E402

with seeded_profile(FORGE / "skills/proposal-implementation/impl_profile.py"):
    import implementation_engine as impl  # noqa: E402

NAME = "Plan-Input-Target"


class PlanInputRefusalTests(unittest.TestCase):
    def _git(self, cwd, *args):
        env = dict(os.environ)
        env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "plan-input-tests"
        env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "plan-input@example.invalid"
        subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)

    def _compliant_repo(self):
        box = FORGE / "implementations" / f"_plan_input_{os.getpid()}_{id(self)}"
        self.addCleanup(shutil.rmtree, box, ignore_errors=True)
        box.mkdir(parents=True)
        self._git(box, "init", "-q")
        for rel in impl.expected_dirs(NAME, with_data=False):
            (box / rel).mkdir(parents=True, exist_ok=True)
            (box / rel / ".gitkeep").touch()
        self._git(box, "add", "-A")
        self._git(box, "commit", "-q", "-m", "initial")
        return box

    def _run(self, *args):
        proc = subprocess.run(
            [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=FORGE
        )
        return proc, json.loads(proc.stdout or "{}")

    def _bad_plans(self, box):
        scratch = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        (scratch / "malformed.json").write_text("{not json", encoding="utf-8")
        (scratch / "array.json").write_text("[]", encoding="utf-8")
        (scratch / "binary.json").write_bytes(b"\xff\xfe\x00")
        # The plan that would apply, made unreadable: the permission is the
        # only thing wrong with it, so only the read failure can refuse it.
        (scratch / "denied.json").write_text(
            json.dumps(impl.build_plan(box, NAME)), encoding="utf-8"
        )
        (scratch / "denied.json").chmod(0)
        return {
            "missing": str(scratch / "absent.json"),
            "permission-denied": str(scratch / "denied.json"),
            "malformed": str(scratch / "malformed.json"),
            "array": str(scratch / "array.json"),
            "undecodable": str(scratch / "binary.json"),
            "directory": str(scratch),
        }

    def _assert_no_defect(self, box):
        ledger = box / NAME / ".implementation" / "position.jsonl"
        events = impl.impl_position.read_events(ledger) if ledger.exists() else []
        self.assertEqual(impl.impl_position.open_defects(events, impl.FORGE_ROOT), [])

    def _approved_plan(self, box):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.addCleanup(os.remove, handle.name)
        json.dump(impl.build_plan(box, NAME), handle)
        handle.close()
        return handle.name

    def _stageable(self, label, plan):
        """Root reads a mode-0 file, so there the permission case cannot be
        staged: skip it visibly instead of passing on another failure."""
        if label == "permission-denied" and os.access(plan, os.R_OK):
            self.skipTest("this process reads a mode-0 file (root)")

    def test_apply_refuses_an_unreadable_plan_and_stays_usable(self):
        box = self._compliant_repo()
        for label, plan in self._bad_plans(box).items():
            with self.subTest(plan=label):
                self._stageable(label, plan)
                proc, payload = self._run(
                    "apply", "--target", str(box), "--name", NAME, "--plan", plan
                )
                self.assertNotIn("Traceback", proc.stderr)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(payload.get("code"), "PLAN_STALE")
                self._assert_no_defect(box)
        proc, payload = self._run(
            "apply", "--target", str(box), "--name", NAME, "--plan", self._approved_plan(box)
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_materialize_refuses_an_unreadable_plan_and_stays_usable(self):
        box = self._compliant_repo()
        for label, plan in self._bad_plans(box).items():
            with self.subTest(plan=label):
                self._stageable(label, plan)
                proc, payload = self._run(
                    "materialize",
                    "--target",
                    str(box),
                    "--name",
                    NAME,
                    "--stage",
                    "scaffold",
                    "--plan",
                    plan,
                    "--seed",
                    "7",
                )
                self.assertNotIn("Traceback", proc.stderr)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(payload.get("code"), "PLAN_STALE")
                self._assert_no_defect(box)


class SessionIdentityTests(unittest.TestCase):
    """`--session` is persisted into the position header -- one `<!-- ... -->`
    comment -- and read back as `session=\\S+` over ASCII; a value the header
    cannot carry is refused by argparse before any command runs, so no
    unreadable header is written."""

    #: HTML comment delimiters: inside the header they open a second block or
    #: end its comment early.
    DELIMITERS = ("<!--", "-->", "--!>")
    REJECTED = (
        "two words",
        "tab\there",
        "line\nbreak",
        "sesión",
        "",
        "<!--position",
        "x<!--y",
        "a-->",
        "-->",
        "a--!>b",
    )
    #: Near misses that stay admitted: printable ASCII, no delimiter.
    ADMITTED = ("s1", "claude-session_2026.10.18", "a:b/c@d", "a--b", "<!-x", "->", "<--", "--!")

    @staticmethod
    def _header(session):
        return {
            "revision": "r01",
            "revisionSha256": "0" * 64,
            "derivedAt": "2026-10-18T00:00:00Z",
            "session": session,
            "target": "implement",
        }

    def test_unpersistable_sessions_are_rejected(self):
        for value in self.REJECTED:
            with self.subTest(session=value):
                with self.assertRaises(SystemExit) as caught, unittest.mock.patch("sys.stderr"):
                    impl.main(
                        [
                            "position",
                            "--target",
                            "implementations/_absent",
                            "--name",
                            NAME,
                            # `=` form: a value starting with `-` reaches the
                            # validator instead of reading as an option.
                            f"--session={value}",
                            "--revision",
                            "r01",
                        ]
                    )
                self.assertEqual(caught.exception.code, 2)

    @classmethod
    def _carried(cls, value):
        """Written into a header, `value` reads back unchanged and the header
        line stays one comment: opened by its first `<!--`, closed only by
        its final `-->`."""
        rendered = impl.impl_position.render(cls._header(value), [])
        try:
            block = impl.impl_position.locate_block(rendered.encode("utf-8"))
        except (impl.Refused, UnicodeDecodeError):
            return False
        line = rendered.split("\n", 1)[0]
        inner = line.removeprefix("<!--").removesuffix("-->")
        return block["session"] == value and not any(d in inner for d in cls.DELIMITERS)

    def test_header_round_trips_every_admitted_session(self):
        for value in self.ADMITTED:
            with self.subTest(session=value):
                self.assertEqual(impl._session_identity(value), value)
                self.assertTrue(self._carried(value))

    def test_every_rejected_session_is_one_the_header_cannot_carry(self):
        """Why the refusal exists: written, each of these leaves a header no
        later call reads back -- a malformed block, a second opener, a
        different session, (non-ASCII) a decode error that crashes the
        reader -- or one whose comment ends inside the session."""
        for value in self.REJECTED:
            with self.subTest(session=value):
                self.assertFalse(self._carried(value))


class SessionHeaderEndToEndTests(unittest.TestCase):
    """The tracker's refinement of #67, through the real CLI: an invalid
    `--session` leaves no header, no ledger and no defect behind, and the
    next valid call still writes."""

    REVISION = "session-r01.md"

    def setUp(self):
        self.proposals = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.proposals, ignore_errors=True)
        (self.proposals / self.REVISION).write_text("## 1\ntexto.\n", encoding="utf-8")
        self.box = FORGE / "implementations" / f"_session_header_{os.getpid()}_{id(self)}"
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        (self.box / NAME).mkdir(parents=True)
        (self.box / NAME / "AGREED.md").write_text(
            "# Agreed\n\n## Ladder\n\n- [ ] First measurable claim.\n", encoding="utf-8"
        )
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "initial")

    def _git(self, *args):
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "session-tests",
            "GIT_COMMITTER_NAME": "session-tests",
            "GIT_AUTHOR_EMAIL": "session@example.invalid",
            "GIT_COMMITTER_EMAIL": "session@example.invalid",
        }
        return subprocess.run(
            ["git", *args], cwd=self.box, env=env, check=True, capture_output=True, text=True
        ).stdout

    def _position(self, session):
        sequence = json.dumps([{"text": "First step.", "witness": {"kind": "record"}}])
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "position",
                "--target",
                str(self.box),
                "--name",
                NAME,
                "--revision",
                self.REVISION,
                "--session",
                session,
                "--sequence",
                sequence,
                "--target-level",
                "final",
            ],
            capture_output=True,
            text=True,
            cwd=FORGE,
            env={**os.environ, "IMPLEMENTATION_PROPOSALS": str(self.proposals)},
        )

    def test_an_invalid_session_leaves_the_target_usable(self):
        for session in ("sesión", "a-->"):
            with self.subTest(session=session):
                refused = self._position(session)
                self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
                self.assertEqual(self._git("status", "--porcelain", "--ignored"), "")
        written = self._position("s1")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        self.assertEqual(json.loads(written.stdout)["status"], "written")


if __name__ == "__main__":
    unittest.main()

"""#84: a revision's identity is its bytes.

`revisionSha256` -- in the position header, in `tests/admissibility.json`, in
the ledger's gate, offer and close events -- says which revision a record was
bound to. The skill's own words always said bytes ("bound to a revision whose
bytes no longer match", SKILL.md; "`revisionSha256` says which bytes",
usage.md), but every binding hashed the text `revision_source` decoded: UTF-8
with `errors="replace"` and universal newlines. Two files that decode to the
same text -- CRLF against LF against lone CR, or two different undecodable
bytes -- shared one identity, so a record bound to one read as current against
the other.

These tests hold the identity to the bytes at the real boundary -- the CLI's
own `position`, `admit`, `verify` and `probe`, against revision files written
byte for byte -- under both hosts the engine serves, and at both of the
experimental host's document positions. The text the parsers read is a
separate thing and stays exactly what it was (`RevisionTextTests`).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

FORGE = Path(__file__).resolve().parents[1]
ENGINE = FORGE / "skills/_core/implementation/engine/implementation_engine.py"
CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"
EXPERIMENTAL_CLI = FORGE / "skills/experimental-implementation/scripts/implementation_cli.py"
sys.path.insert(0, str(ENGINE.parent))
from domain_profile import seeded_profile  # noqa: E402  (path set above)

with seeded_profile(FORGE / "skills/proposal-implementation/impl_profile.py"):
    import implementation_engine as impl  # noqa: E402  (path set above)
import impl_position  # noqa: E402  (the engine put its own directory on the path)

NAME = "Method"
REVISION = "r1.md"

#: What a published revision starts with (`MANAGED_ARTIFACT_MARKER`, the
#: engine's own constant): the deliberation skill writes it, LF-terminated.
MARKER = b"<!-- proposal-workspace:artifact:v1 -->\n"
#: Carries an equation tag and a use, so the finding below can be ruled on.
TEXT = "## 3\n\n$$\na = b \\tag{3.1}\n$$\n\nThroughout, the estimator is written E[x].\n"
ONE_FINDING = (
    "FINDINGS = [\n"
    "    {'id': 'loose', 'equations': ['3.1'], 'remedy_equations': ['3.1'],\n"
    "     'uses': ['E[x]'], 'introduces': [],\n"
    "     'adoption': {'absent': 'a = b', 'expect': ['a = c']}},\n"
    "]\n"
)
NO_FINDINGS = "FINDINGS = []\n"
#: One refreshable item, so `position` re-binds the header and nothing else.
BLOCK_BODY = "- [ ] 1. Step. `@rehearsal job1`\n"

#: Byte forms that `read_text(encoding="utf-8", errors="replace")` folds into
#: one text, in two families. Every one is a file the engine accepts today.
LINE_ENDINGS = {
    "LF": TEXT.encode("utf-8"),
    "CRLF": TEXT.replace("\n", "\r\n").encode("utf-8"),
    "CR": TEXT.replace("\n", "\r").encode("utf-8"),
}
UNDECODABLE = {
    "0xff": TEXT.encode("utf-8").replace(b"estimator", b"estimator \xff"),
    "0xfe": TEXT.encode("utf-8").replace(b"estimator", b"estimator \xfe"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decoded(data: bytes) -> str:
    """What the engine has always read a revision as."""
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "revision.md"
        path.write_bytes(data)
        return path.read_text(encoding="utf-8", errors="replace")


def crlf(text: str) -> bytes:
    return text.replace("\n", "\r\n").encode("utf-8")


def cli_env(**proposals: Path) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("IMPLEMENTATION_DOMAIN_PROFILE", "VIRTUAL_ENV")
    }
    env.update({key: str(path) for key, path in proposals.items()})
    return env


class RevisionIdentityTests(unittest.TestCase):
    """The proposal host, one document, through its own CLI."""

    def setUp(self) -> None:
        self.proposals = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.proposals, ignore_errors=True)
        self.box = FORGE / "implementations" / f"_revision_identity_{os.getpid()}_{id(self)}"
        shutil.rmtree(self.box, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        (self.box / "src" / NAME).mkdir(parents=True)
        (self.box / "src" / f"{NAME}_Benchmark").mkdir(parents=True)
        (self.box / "tests").mkdir()
        (self.box / NAME).mkdir()
        subprocess.run(["git", "init", "-q", str(self.box)], check=True)
        (self.box / "src" / NAME / "__init__.py").write_text(
            f"__implementation__ = {{'revision': '{REVISION}', 'premises': {{}}}}\n",
            encoding="utf-8",
        )
        (self.box / "src" / f"{NAME}_Benchmark" / "__init__.py").write_text("", encoding="utf-8")
        self.write_header("a" * 64)

    # --- the boundary ------------------------------------------------------

    @property
    def revision(self) -> Path:
        return self.proposals / REVISION

    @property
    def ruling(self) -> Path:
        return self.box / "tests" / "admissibility.json"

    def run_cli(self, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(CLI), *args],
            capture_output=True,
            text=True,
            env=cli_env(IMPLEMENTATION_PROPOSALS=self.proposals),
            cwd=FORGE,
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise AssertionError(f"no JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from error

    def write_header(self, digest: str) -> None:
        """The position section as a binding to `digest` left it."""
        (self.box / NAME / "AGREED.md").write_text(
            f"<!-- position revision={REVISION} sha256={digest} "
            "derivedAt=2026-08-27T00:00:00Z session=s0 target=final -->\n"
            f"{BLOCK_BODY}<!-- /position -->\n",
            encoding="utf-8",
        )

    def bind_position(self) -> str:
        """`position` (a refresh) and the identity its header now carries."""
        result = self.run_cli(
            "position",
            "--target",
            str(self.box),
            "--name",
            NAME,
            "--revision",
            REVISION,
            "--session",
            "s1",
        )
        self.assertNotIn("code", result, result)
        block = impl_position.locate_block((self.box / NAME / "AGREED.md").read_bytes())
        return block["revisionSha256"]

    def bind_ruling(self, *, findings: str) -> str:
        """`admit` (with `--no-findings` when nothing is declared) and the
        identity `tests/admissibility.json` now carries."""
        (self.box / "tests" / "findings.py").write_text(findings, encoding="utf-8")
        extra = ("--no-findings",) if findings == NO_FINDINGS else ()
        result = self.run_cli(
            "admit", "--target", str(self.box), "--name", NAME, "--revision", REVISION, *extra
        )
        self.assertNotIn("code", result, result)
        return json.loads(self.ruling.read_text(encoding="utf-8"))["revisionSha256"]

    def verify(self) -> tuple[dict, dict]:
        report = self.run_cli(
            "verify", "--target", str(self.box), "--name", NAME, "--revision", REVISION
        )
        return report["position"], report["audit"]["admissibility"]

    # --- the acceptance tests the issue names --------------------------------

    def test_revision_identity_distinguishes_distinct_raw_document_bytes(self) -> None:
        for family, forms in (("line endings", LINE_ENDINGS), ("undecodable bytes", UNDECODABLE)):
            with self.subTest(family=family):
                # The collision is real for the reader the bindings used:
                # every form in a family decodes to one and the same text.
                self.assertEqual(len({decoded(data) for data in forms.values()}), 1)
                bound = {}
                for label, data in forms.items():
                    self.revision.write_bytes(data)
                    bound[label] = {
                        "position": self.bind_position(),
                        "admit": self.bind_ruling(findings=ONE_FINDING),
                        "admit --no-findings": self.bind_ruling(findings=NO_FINDINGS),
                    }
                for label, data in forms.items():
                    for boundary, identity in bound[label].items():
                        self.assertEqual(identity, sha256(data), f"{boundary} on {label}")
                for boundary in ("position", "admit", "admit --no-findings"):
                    identities = {bound[label][boundary] for label in forms}
                    self.assertEqual(len(identities), len(forms), boundary)

    def test_revision_identity_matches_hash_of_persisted_bytes(self) -> None:
        # A published artifact as a CRLF checkout or editor leaves it: the
        # publisher's LF marker, then a body whose lines end in CRLF.
        published = MARKER + LINE_ENDINGS["CRLF"]
        self.revision.write_bytes(published)
        header = self.bind_position()
        ruling = self.bind_ruling(findings=NO_FINDINGS)
        persisted = sha256(self.revision.read_bytes())
        self.assertEqual(header, persisted)
        self.assertEqual(ruling, persisted)
        # Read back: both bindings hold against the bytes they named...
        position, admissibility = self.verify()
        self.assertEqual(position["status"], "open", position)
        self.assertEqual(position["boundTo"], "current", position)
        self.assertEqual(admissibility["status"], "present", admissibility)
        # ...and stop holding the moment those bytes move, even when the
        # text the parsers read does not.
        self.revision.write_bytes(MARKER + LINE_ENDINGS["LF"])
        self.assertEqual(decoded(self.revision.read_bytes()), decoded(published))
        position, admissibility = self.verify()
        self.assertEqual(position["status"], "stale", position)
        self.assertEqual(admissibility["status"], "stale", admissibility)

    def test_revision_identity_compatibility_preserves_existing_records(self) -> None:
        """Every binding taken before #84 stored the digest of the decoded
        text. For a revision of LF lines in valid UTF-8 that IS the digest of
        its bytes, so such a record holds exactly as it did and nothing about
        it moves. For CRLF lines, the stored digest names a text those bytes
        fold into, never the bytes: refused (`stale`, since no digest is ever
        taken for bytes it does not name), but never silently -- the refusal
        says why, and the commands that bind the bytes are the migration."""
        for label, data in (
            ("LF", MARKER + LINE_ENDINGS["LF"]),
            ("CRLF", MARKER + LINE_ENDINGS["CRLF"]),
        ):
            with self.subTest(revision=label):
                self.revision.write_bytes(data)
                legacy = sha256(decoded(data).encode("utf-8"))
                self.write_header(legacy)
                self.bind_ruling(findings=NO_FINDINGS)
                record = json.loads(self.ruling.read_text(encoding="utf-8"))
                record["revisionSha256"] = legacy
                self.ruling.write_text(
                    json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                position, admissibility = self.verify()
                if label == "LF":
                    self.assertEqual(legacy, sha256(data))
                    self.assertEqual(position["boundTo"], "current", position)
                    self.assertNotIn("textOnlyMatch", position)
                    self.assertEqual(admissibility["status"], "present", admissibility)
                    continue
                self.assertEqual(position["status"], "stale", position)
                self.assertEqual(position["boundTo"], "stale", position)
                self.assertEqual(position["textOnlyMatch"], ["proposal"], position)
                self.assertEqual(admissibility["status"], "stale", admissibility)
                self.assertIn("decoded text, not its bytes", admissibility["detail"])
                self.assertIn("run `admit` again", admissibility["detail"])
                # The migration: binding the bytes, once.
                self.bind_position()
                self.bind_ruling(findings=NO_FINDINGS)
                position, admissibility = self.verify()
                self.assertEqual(position["boundTo"], "current", position)
                self.assertNotIn("textOnlyMatch", position)
                self.assertEqual(admissibility["status"], "present", admissibility)

    def test_a_revision_of_zero_bytes_has_an_identity(self) -> None:
        self.revision.write_bytes(MARKER + LINE_ENDINGS["LF"])
        self.bind_position()
        # Truncated to nothing, the header names bytes the file no longer has.
        self.revision.write_bytes(b"")
        position, _ = self.verify()
        self.assertEqual(position["status"], "stale", position)
        # And a binding to zero bytes is a binding like any other.
        self.assertEqual(self.bind_position(), sha256(b""))
        position, _ = self.verify()
        self.assertEqual(position["boundTo"], "current", position)


class RevisionTextTests(unittest.TestCase):
    """The reader's two halves, in-process: the text every parser reads is
    exactly what `read_text(encoding="utf-8", errors="replace")` always
    gave, and the identity beside it is the SHA-256 of the bytes."""

    #: Inputs where decoding, newline folding or the decoder's 8192-byte
    #: chunking could tell the two readings apart.
    CASES = {
        "LF": TEXT.encode("utf-8"),
        "CRLF": crlf(TEXT),
        "lone CR": b"one\rtwo\r",
        "CR then CRLF": b"a\r\r\nb",
        "trailing CR": b"end\r",
        "BOM": b"\xef\xbb\xbf## 1\r\ntext\r\n",
        "undecodable": b"a\xff\xfeb\x80\n",
        "zero bytes": b"",
        "CRLF across a chunk boundary": b"a" * 8191 + b"\r\nb\r\n",
        "CR at a chunk boundary": b"a" * 8191 + b"\r" + b"b" * 10,
        "multibyte across a chunk boundary": b"a" * 8190 + "é😀".encode("utf-8") + b"\r\n",
        "truncated multibyte at the end": b"a" * 8191 + "é".encode("utf-8")[:1],
        "long, mixed endings": b"x\r\ny\nz\r" * 5000,
    }

    def setUp(self) -> None:
        raw = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, raw, ignore_errors=True)
        self.root = Path(raw)
        patcher = mock.patch.dict(os.environ, {"IMPLEMENTATION_PROPOSALS": raw})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_text_is_what_read_text_gave_and_the_identity_is_the_bytes(self) -> None:
        for label, data in self.CASES.items():
            with self.subTest(case=label):
                path = self.root / "r.md"
                path.write_bytes(data)
                source = impl.revision_source("r.md")
                self.assertIsInstance(source, impl.RevisionText)
                self.assertEqual(str(source), path.read_text(encoding="utf-8", errors="replace"))
                self.assertEqual(impl.revision_identity(source), sha256(data))

    def test_a_text_only_match_is_the_old_digest_of_bytes_it_does_not_name(self) -> None:
        path = self.root / "r.md"
        path.write_bytes(crlf(TEXT))
        source = impl.revision_source("r.md")
        text_digest = sha256(TEXT.encode("utf-8"))
        self.assertTrue(impl.matches_text_only(text_digest, source))
        self.assertFalse(impl.matches_text_only(sha256(crlf(TEXT)), source))
        self.assertFalse(impl.matches_text_only("a" * 64, source))
        self.assertFalse(impl.matches_text_only(None, source))
        self.assertFalse(impl.matches_text_only(text_digest, None))
        # LF bytes ARE their text's encoding: there is nothing to tell apart.
        path.write_bytes(TEXT.encode("utf-8"))
        self.assertFalse(impl.matches_text_only(text_digest, impl.revision_source("r.md")))
        # A byte digest reads the same way once the bytes change in a way
        # decoding folds: a literal U+FFFD, valid UTF-8, turned into a byte
        # that does not decode. Same text, same line endings, other bytes.
        replacement = "\N{REPLACEMENT CHARACTER}".encode("utf-8")
        literal = b"estimator " + replacement + b"\n"
        path.write_bytes(literal)
        bound = impl.revision_identity(impl.revision_source("r.md"))
        self.assertEqual(bound, sha256(literal))
        path.write_bytes(literal.replace(replacement, b"\xff"))
        self.assertTrue(impl.matches_text_only(bound, impl.revision_source("r.md")))

    def test_a_plain_str_is_identified_by_its_utf8_encoding(self) -> None:
        """No file behind it, so no other byte form to name -- the
        convention `position_state`'s direct callers rely on."""
        self.assertEqual(impl.revision_identity("some content"), sha256(b"some content"))
        self.assertFalse(impl.matches_text_only(sha256(b"some content"), "some content"))


class ExperimentalHostIdentityTests(unittest.TestCase):
    """The experimental host declares two documents -- `experiments` at
    index 0, `proposal` at index 1 -- and each binds its own bytes, through
    the host's own CLI, at both positions."""

    PACKAGE = "ByteIdentity"
    TEXT_0 = "## E1\n\nThe first experiment.\n"
    TEXT_1 = "The proposal declares $$a = b \\tag{1}$$ only.\n"

    def setUp(self) -> None:
        self.doc0 = Path(tempfile.mkdtemp(prefix="identity-doc0-"))
        self.addCleanup(shutil.rmtree, self.doc0, ignore_errors=True)
        self.doc1 = Path(tempfile.mkdtemp(prefix="identity-doc1-"))
        self.addCleanup(shutil.rmtree, self.doc1, ignore_errors=True)
        self.box = FORGE / "implementations" / f"_revision_identity_exp_{os.getpid()}_{id(self)}"
        shutil.rmtree(self.box, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.box, ignore_errors=True)
        (self.box / self.PACKAGE).mkdir(parents=True)
        (self.box / self.PACKAGE / "Experimental_AGREED.md").write_text(
            "# Agreed\n\n## Ladder\n\n- [ ] First measurable claim.\n", encoding="utf-8"
        )
        env = dict(os.environ)
        env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "revision-identity"
        env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "revision-identity@example.invalid"
        subprocess.run(["git", "init", "-q", str(self.box)], check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=self.box, env=env, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "initial"],
            cwd=self.box,
            env=env,
            check=True,
            capture_output=True,
        )

    def write(self, data_0: bytes, data_1: bytes) -> None:
        (self.doc0 / "e1.md").write_bytes(data_0)
        (self.doc1 / "p1.md").write_bytes(data_1)

    def run_cli(self, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(EXPERIMENTAL_CLI), *args],
            capture_output=True,
            text=True,
            cwd=FORGE,
            env=cli_env(IMPLEMENTATION_PROPOSALS=self.doc0, IMPLEMENTATION_PROPOSALS_1=self.doc1),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(proc.stdout)

    def position(self, *extra: str) -> None:
        self.run_cli(
            "position",
            "--target",
            str(self.box),
            "--name",
            self.PACKAGE,
            "--revision",
            "e1.md",
            "--session",
            "s1",
            *extra,
        )

    def probe(self) -> dict:
        return self.run_cli(
            "probe", "--target", str(self.box), "--name", self.PACKAGE, "--revision", "e1.md"
        )["position"]

    def test_each_document_binds_its_own_bytes(self) -> None:
        both = {"experiments", "proposal"}
        self.write(crlf(self.TEXT_0), crlf(self.TEXT_1))
        self.position(
            "--sequence",
            json.dumps([{"text": "First step.", "witness": {"kind": "record"}}]),
            "--target-level",
            "final",
        )
        holder = self.box / self.PACKAGE / "Experimental_AGREED.md"
        block = impl_position.locate_block(holder.read_bytes())
        self.assertEqual(block["revisionSha256"], sha256(crlf(self.TEXT_0)))
        self.assertEqual(
            {entry["label"]: entry["revisionSha256"] for entry in block["documents"]},
            {"proposal": sha256(crlf(self.TEXT_1))},
        )
        self.assertEqual(self.probe()["boundTo"], dict.fromkeys(both, "current"))

        # The same two texts in LF are two other files: both bindings go
        # stale, and neither stored digest names the text the LF bytes are.
        self.write(self.TEXT_0.encode("utf-8"), self.TEXT_1.encode("utf-8"))
        position = self.probe()
        self.assertEqual(position["boundTo"], dict.fromkeys(both, "stale"))
        self.assertNotIn("textOnlyMatch", position)

        # Bound to LF, then turned CRLF: each stored digest is now the digest
        # of the text the CRLF bytes decode to, and probe names both.
        self.position()
        self.assertEqual(self.probe()["boundTo"], dict.fromkeys(both, "current"))
        self.write(crlf(self.TEXT_0), crlf(self.TEXT_1))
        position = self.probe()
        self.assertEqual(position["boundTo"], dict.fromkeys(both, "stale"))
        self.assertEqual(position["textOnlyMatch"], ["experiments", "proposal"])


if __name__ == "__main__":
    unittest.main()

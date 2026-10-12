#!/usr/bin/env python3
"""Rebuild ``tests/fixtures/workspace_v0_13_0/``: a populated 0.13.0 workspace.

The upgrade path has to be proven against a workspace that a real 0.13.0
release produced, not one hand-assembled to look like it. So nothing here
writes an artifact itself: it extracts the 0.13.0 tree (``git archive
55dcb4e``, the merge commit that carries ``__version__ = "0.13.0"``; that
release has no tag) into a scratch directory and drives THAT tree's own CLI
and engines:

* ``papersmith init --no-env --no-npm``;
* proposal-deliberation: ``CREATE_INITIAL_REVISION`` and one successor
  (resolve, preview, accept on one ``--serve`` process);
* experimental-deliberation: ``CREATE_INITIAL_REVISION``;
* one implementation target under ``implementations/``: ``plan``, then
  ``materialize --stage scaffold`` (its receipt and the kit's seal file), and
  for EACH implementation skill a ``position --sequence`` install (which
  creates that skill's declared holder), a ``discuss`` question and answer,
  and a ``settle`` (ledger events in ``position.jsonl``).

The deliberation engines need ``node_modules``; the repository's own is
linked in for the run and removed before the snapshot.

What is stored is the workspace minus the framework files ``init`` copied or
rendered and nobody touched since: every path the workspace's own
``.papersmith/manifest.json`` records whose bytes still hash to the recorded
value. Those are the release's files, not the workspace's state, and they are
megabytes (the skill tree alone is ~8 MB). ``upgrade`` writes every one of
them again from the installed kit whether the old bytes are present or not,
and its orphan sweep treats an absent baselined file as already removed, so
leaving them out does not change what an upgrade produces. Everything the
workspace itself made -- revisions, receipts, state, locks, holders, ledgers,
the scaffold receipt and seal, the manifest, the version marker -- is kept
byte for byte.

The snapshot is stored as one deterministic ``workspace.tar.gz`` (sorted
entries, zeroed owners and mtimes) because a workspace carries its own
``.gitignore``, which would hide most of its content from this repository's
git if the tree were committed as loose files. ``contents.sha256`` lists every
member, so a review can read what changed.

Rebuilding produces different bytes: the engines stamp wall-clock times into
receipts, state and ledger events, and those are hashed into other records, so
they are never rewritten here. A rebuild is a new snapshot, not a repair.

    python scripts/build-v0_13_0-fixture.py [--out tests/fixtures/workspace_v0_13_0]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
#: The 0.13.0 release commit. There is no tag; ``src/papersmith/__init__.py``
#: at this commit reads ``__version__ = "0.13.0"``.
BASE_COMMIT = "55dcb4e"
DEFAULT_OUT = ROOT / "tests" / "fixtures" / "workspace_v0_13_0"
TARGET = "implementations/Smoother"
PACKAGE = "Smoother"
SESSION = "fixture"
IMPLEMENTATION_SKILLS = ("proposal-implementation", "experimental-implementation")
#: Baselined files kept even when untouched: the version marker is the claim
#: an upgrade reads, and ``.gitignore`` is the one rendered file a user is
#: expected to edit, so its 0.13.0 bytes are part of what is tested.
ALWAYS_KEPT = frozenset({".papersmith/version", ".gitignore"})


def _run(argv: list[str], *, cwd: Path, env: dict[str, str], stdin: str | None = None) -> str:
    completed = subprocess.run(argv, cwd=cwd, env=env, input=stdin, text=True,
                               capture_output=True, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{' '.join(argv)} exited {completed.returncode}:\n"
                         f"{completed.stdout}\n{completed.stderr}")
    return completed.stdout


def _json(argv: list[str], *, cwd: Path, env: dict[str, str], stdin: str | None = None,
          expect: tuple[str, ...]) -> dict:
    payload = json.loads(_run(argv, cwd=cwd, env=env, stdin=stdin))
    if payload.get("status") not in expect:
        raise SystemExit(f"{' '.join(argv[:4])}: expected status in {expect}, got "
                         f"{json.dumps(payload)[:1500]}")
    return payload


def _extract_release(kit: Path) -> None:
    archive = subprocess.run(["git", "archive", BASE_COMMIT], cwd=ROOT, capture_output=True,
                             check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(kit, filter="data")


def _deliberate(ws: Path, env: dict[str, str]) -> None:
    proposal_cli = "skills/proposal-deliberation/cli.mjs"
    created = _json(["node", proposal_cli, json.dumps({
        "operation": "CREATE_INITIAL_REVISION",
        "instruction": "Smoothing estimator for noisy sequences. "
                       "We study a moving average estimator and bound its error.",
    })], cwd=ws, env=env, expect=("created",))
    source = created["targetFilename"]

    serve = subprocess.Popen(["node", proposal_cli, "--serve"], cwd=ws, env=env,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    def call(request: dict) -> dict:
        assert serve.stdin and serve.stdout
        serve.stdin.write(json.dumps(request) + "\n")
        serve.stdin.flush()
        return json.loads(serve.stdout.readline())

    try:
        query = "moving average estimator"
        resolved = call({"operation": "RESOLVE_TARGET", "sourceFilename": source, "query": query})
        if resolved.get("blocked") or not resolved.get("entryId"):
            raise SystemExit(f"RESOLVE_TARGET: {resolved}")
        request = {
            "operation": "CREATE_SUCCESSOR", "sourceFilename": source,
            "instruction": "Replace the body of the estimator section.",
            "selectedEntryId": query,
            "resolvedDecisions": [{
                "kind": "replace", "targetEntryId": resolved["entryId"],
                "replacementText": "## We study a moving average estimator and bound its error.\n\n"
                                   "The estimator averages a fixed window of past observations.\n",
            }],
        }
        preview = call(request)
        if preview.get("status") != "awaiting_acceptance":
            raise SystemExit(f"CREATE_SUCCESSOR preview: {preview}")
        published = call({**request, "acceptSuccessor": True,
                          "successorAcceptanceToken": preview["acceptanceToken"]})
        if published.get("status") != "published":
            raise SystemExit(f"CREATE_SUCCESSOR accept: {published}")
    finally:
        if serve.stdin:
            serve.stdin.close()
        serve.wait(timeout=120)

    # experimental-deliberation needs a data-paper source and a proposal on disk.
    data = ws / "guidance" / "data-paper" / "sample-data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "sample-data.md").write_text(
        "# Sample data\n\nA generic synthetic sequence dataset with a fixed train and test split.\n",
        encoding="utf-8")
    _json(["node", "skills/experimental-deliberation/cli.mjs", json.dumps({
        "operation": "CREATE_INITIAL_REVISION",
        "instruction": "Smoothing window sweep. Testing whether the window length changes the "
                       "estimator error. Claim C1: the error decreases with the window.\n\n"
                       "**Dataset:** sample-data (fixed train/test split).\n\n"
                       "**Validation scheme:** paired comparison, 3 seeds, 2 repetitions per seed.",
    })], cwd=ws, env=env, expect=("created",))
    published_successor = published["targetFilename"]
    (ws / ".fixture-revisions.json").write_text(json.dumps({
        "proposal": published_successor,
        "experiments": sorted(p.name for p in (ws / "experiments").glob("*.md"))[-1],
    }), encoding="utf-8")


def _implement(ws: Path, env: dict[str, str], scratch: Path) -> None:
    revisions = json.loads((ws / ".fixture-revisions.json").read_text(encoding="utf-8"))
    (ws / ".fixture-revisions.json").unlink()
    (ws / TARGET).mkdir(parents=True)
    # The engine refuses a target that is not a git repository. No hook
    # samples (an empty template) and a pinned identity and date keep the
    # repository small and its one commit reproducible.
    git_env = {**env, "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
               "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
               "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    _run(["git", "init", "-q", "--template=", "-b", "main"], cwd=ws / TARGET, env=git_env)
    _run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=ws / TARGET, env=git_env)
    target = ["--target", TARGET, "--name", PACKAGE]
    proposal = _cli(IMPLEMENTATION_SKILLS[0])
    plan = scratch / "plan.json"
    plan.write_text(_run([*proposal, "plan", *target], cwd=ws, env=env), encoding="utf-8")
    _json([*proposal, "materialize", *target, "--stage", "scaffold", "--plan", str(plan),
           "--seed", "7"], cwd=ws, env=env, expect=("materialized",))

    skills = list(zip(IMPLEMENTATION_SKILLS, (revisions["proposal"], revisions["experiments"])))
    # Every holder is created before any item is settled. In 0.13.0 a skill
    # read its sibling's item-holding holder as an undeclared checklist and
    # refused (`HOLDER_UNDECLARED`); a holder that already exists under the
    # skill's own declared name resolves as declared. This is the order a
    # 0.13.0 workspace had to follow to hold both, so it is the one recorded.
    for skill, revision in skills:
        sequence = json.dumps([{
            "text": f"the verification notebook runs ({skill})",
            "witness": {"kind": "notebook", "operand": "Notebooks/verification.ipynb"},
        }])
        _json([*_cli(skill), "position", *target, "--session", SESSION, "--revision", revision,
               "--sequence", "-", "--target-level", "local"],
              cwd=ws, env=env, stdin=sequence, expect=("written",))
    for skill, _revision in skills:
        question = "Which window length does the first pass use?"
        _json([*_cli(skill), "discuss", *target, "--about", "1", "--question", question],
              cwd=ws, env=env, expect=("open",))
        _json([*_cli(skill), "discuss", *target, "--about", "1", "--question", question,
               "--answer", "A fixed window of five observations."],
              cwd=ws, env=env, expect=("answered",))
        # `--under "# Agreed"`, not the holder's `## Ladder`: the position
        # block sits directly under `## Ladder`, and `settle` inserts at the
        # first non-blank line after its heading -- inside the block, which
        # then no longer parses (`POSITION_ITEM_MALFORMED` on `verify`, in
        # 0.13.0 and still on 0.14.0 at the time of writing). A fixture built
        # on that would test a holder no engine can read.
        _json([*_cli(skill), "settle", *target, "--session", SESSION, "--about", "1",
               "--text", f"the first pass uses a fixed window of five observations ({skill})",
               "--under", "# Agreed"], cwd=ws, env=env, expect=("written",))


def _cli(skill: str) -> list[str]:
    return [sys.executable, f"skills/{skill}/scripts/implementation_cli.py"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _kept_files(ws: Path) -> list[str]:
    """Every file the workspace made, i.e. not an untouched framework file."""
    baseline = json.loads((ws / ".papersmith" / "manifest.json").read_text(encoding="utf-8"))["files"]
    kept: list[str] = []
    for path in sorted(ws.rglob("*")):
        relpath = path.relative_to(ws).as_posix()
        if "__pycache__" in path.parts or relpath.startswith("node_modules"):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if relpath not in ALWAYS_KEPT and baseline.get(relpath) == _sha256(path):
            continue
        kept.append(relpath)
    return kept


def _write_snapshot(ws: Path, out: Path) -> None:
    kept = _kept_files(ws)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for relpath in kept:
            data = (ws / relpath).read_bytes()
            info = tarfile.TarInfo(relpath)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "workspace.tar.gz", "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(buffer.getvalue())
    listing = "".join(f"{_sha256(ws / relpath)}  {relpath}\n" for relpath in kept)
    (out / "contents.sha256").write_text(listing, encoding="utf-8")


def build(out: Path) -> None:
    node_modules = ROOT / "node_modules"
    if not node_modules.is_dir():
        raise SystemExit("node_modules is missing; run `npm ci` first (the deliberation engines need it)")
    with tempfile.TemporaryDirectory(prefix="papersmith-v0_13_0-") as raw:
        scratch = Path(raw)
        kit = scratch / "kit"
        ws = scratch / "workspace"
        kit.mkdir()
        _extract_release(kit)
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("PAPERSMITH_", "PROPOSAL_DELIBERATION_",
                                    "DELIBERATION_", "IMPLEMENTATION_"))}
        env.update(PYTHONPATH=str(kit / "src"), PAPERSMITH_KIT_ROOT=str(kit),
                   PYTHONDONTWRITEBYTECODE="1")
        _run([sys.executable, "-m", "papersmith.cli", "init", str(ws), "--no-env", "--no-npm",
              "--title", "Fixture workspace", "--topic", "generic", "--remote", "local"],
             cwd=scratch, env=env)
        version = (ws / ".papersmith" / "version").read_text(encoding="utf-8").strip()
        if version != "0.13.0":
            raise SystemExit(f"{BASE_COMMIT} initialized a {version!r} workspace, not 0.13.0")
        (ws / "node_modules").symlink_to(node_modules)
        try:
            _deliberate(ws, env)
            _implement(ws, env, scratch)
        finally:
            (ws / "node_modules").unlink()
        if out.exists():
            for name in ("workspace.tar.gz", "contents.sha256"):
                (out / name).unlink(missing_ok=True)
        _write_snapshot(ws, out)
        shutil.rmtree(ws)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.out.resolve())
    print(f"wrote {args.out / 'workspace.tar.gz'} and {args.out / 'contents.sha256'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

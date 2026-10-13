"""Which framework build a workspace came from, and whether it may be used.

``init`` and ``upgrade`` copy whatever kit :mod:`papersmith.kit` resolves. From
an editable install that is the live checkout, uncommitted edits included, and
until 0.14.0 nothing recorded which commit a workspace was built from: two
workspaces at the same version could carry different bytes and nobody could
tell which.

This module answers two questions about a resolved kit root:

- **What is it?** :func:`describe` returns the version, the commit, whether the
  shipped paths carry uncommitted changes, and which resolution branch found it
  (``checkout``, ``bundled`` or ``override``). A *built* kit — one carrying
  ``kit-manifest.json``, as the bundled ``_kit/`` does — answers from the commit
  and dirty flag ``scripts/build-kit.py`` captured; a *source tree* is asked
  git directly.
- **May it be used?** :func:`require_admissible` refuses a dirty source, and
  refuses one whose git state cannot be read, unless the caller passed
  ``--allow-dirty-kit`` (or set ``PAPERSMITH_ALLOW_DIRTY_KIT=1``). Unknown is
  treated as dirty, not as clean: the point of the record is that it can be
  trusted, and a guess cannot.

A built kit with no captured provenance (built before 0.14.0, or from a tree
with no git) is admitted with an unknown commit. Its bytes are a frozen
snapshot named file by file in its manifest, not live edits, so what the guard
exists to stop cannot happen through it.

Both commands write the answer to ``.papersmith/kit-source.json`` after they
have written their files, and ``status`` reports it.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..errors import UserError
from . import config, fs, manifest

KIT_SOURCE_RECORD = ".papersmith/kit-source.json"
ALLOW_DIRTY_ENV = "PAPERSMITH_ALLOW_DIRTY_KIT"
RECORD_SCHEMA = 1
LEGACY_DETAIL = "unknown (recorded before 0.14.0)"

#: The paths whose uncommitted changes would reach a workspace: every kit entry
#: ``init`` copies, plus the package that renders the projections and declares
#: the version. Edits elsewhere in a checkout (notes, tests, task files) never
#: reach a workspace and do not make the kit dirty.
SHIPPED_PATHSPECS = (*manifest.KIT_ENTRIES, "src/papersmith")

_GIT_TIMEOUT = 30.0
_LISTED = 5


@dataclass(frozen=True)
class KitSource:
    version: str
    commit: str | None
    dirty: bool | None  # None: could not be determined
    source: str  # "checkout" | "bundled" | "override"
    built: bool  # True when answered from a kit-manifest, not from git
    reason: str | None = None  # why commit or dirty is unknown
    changes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GitState:
    commit: str | None
    dirty: bool | None
    reason: str | None
    changes: tuple[str, ...] = ()


def _git(root: Path, *args: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def git_state(root: Path) -> GitState:
    """The commit and dirty flag of a source tree, or why they are unknown.

    Never raises: a missing ``git``, a tree outside any repository, a timeout
    or a refusing repository (``safe.directory``) all come back as an unknown
    state with the reason, which the caller treats as dirty.
    """
    try:
        code, out, err = _git(root, "rev-parse", "--verify", "HEAD")
        if code != 0:
            detail = err.strip().splitlines()
            return GitState(None, None, "git could not name a commit for this tree"
                            + (f" ({detail[-1]})" if detail else ""))
        commit = out.strip()
        code, out, err = _git(root, "status", "--porcelain", "--untracked-files=all",
                              "--", *SHIPPED_PATHSPECS)
        if code != 0:
            detail = err.strip().splitlines()
            return GitState(commit, None, "git could not report this tree's changes"
                            + (f" ({detail[-1]})" if detail else ""))
    except FileNotFoundError:
        return GitState(None, None, "git is not installed")
    except (OSError, subprocess.SubprocessError) as exc:
        return GitState(None, None, f"git could not run: {exc}")
    changes = tuple(line[3:] for line in out.splitlines() if len(line) > 3)
    return GitState(commit, bool(changes), None, changes)


def describe(kit_root: Path, source: str) -> KitSource:
    """Version, commit and dirty flag of the kit at ``kit_root``."""
    version = manifest.kit_version(kit_root)
    built = manifest.load_kit_manifest(kit_root)
    if built is not None:
        commit = built.get("commit")
        dirty = built.get("dirty")
        commit = commit if isinstance(commit, str) and commit else None
        dirty = dirty if isinstance(dirty, bool) else None
        reason = None
        if commit is None or dirty is None:
            reason = "the kit manifest carries no build provenance"
        return KitSource(version, commit, dirty, source, True, reason)
    state = git_state(kit_root)
    return KitSource(version, state.commit, state.dirty, source, False, state.reason,
                     state.changes)


def allowed_by_environment() -> bool:
    return os.environ.get(ALLOW_DIRTY_ENV, "").strip() == "1"


def require_admissible(kit: KitSource, *, verb: str, allow_dirty: bool) -> bool:
    """Refuse a dirty or unknown kit source; return whether an override was used.

    Raised before the caller writes anything, the same split ``upgrade``'s
    downgrade guard draws: by the time files are copied, the dirty bytes are
    the workspace's state.
    """
    allowed = allow_dirty or allowed_by_environment()
    if kit.dirty is True:
        if allowed:
            return True
        if kit.built:
            what = (f"the kit at {_where(kit)} was built from a tree with uncommitted "
                    "changes")
        else:
            listed = ", ".join(kit.changes[:_LISTED])
            more = len(kit.changes) - _LISTED
            what = (f"the kit at {_where(kit)} has uncommitted changes under its shipped "
                    f"paths: {listed}" + (f" (+{more} more)" if more > 0 else ""))
        raise UserError(
            f"refusing to {verb} from an unreleased kit: {what}. A workspace built from "
            "them would carry bytes no commit names. Commit or stash them, or re-run "
            "with --allow-dirty-kit to proceed and record the workspace as built from "
            "a dirty kit")
    if kit.dirty is None and not kit.built:
        if allowed:
            return True
        raise UserError(
            f"refusing to {verb}: cannot determine the git state of the kit at "
            f"{_where(kit)} ({kit.reason}), so nothing would record which framework "
            "commit this workspace came from, or whether it carries uncommitted edits. "
            "Re-run with --allow-dirty-kit to proceed with the commit recorded as unknown")
    return False


def _where(kit: KitSource) -> str:
    return f"{kit.source} source" if not kit.commit else f"{kit.source} source ({kit.commit[:12]})"


def record(kit: KitSource, *, allowed_dirty: bool) -> dict:
    """The record a run writes, as a dict (written by :func:`write_record`)."""
    payload: dict = {
        "schema": RECORD_SCHEMA,
        "version": kit.version,
        "commit": kit.commit,
        "dirty": kit.dirty,
        "source": kit.source,
        "recordedAt": config.utc_timestamp(),
    }
    if kit.reason:
        payload["reason"] = kit.reason
    if allowed_dirty:
        payload["allowedDirty"] = True
    return payload


def write_record(workspace: Path, kit: KitSource, *, allowed_dirty: bool) -> tuple[dict, bool]:
    payload = record(kit, allowed_dirty=allowed_dirty)
    written = fs.write_text(workspace / KIT_SOURCE_RECORD,
                            json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload, written


def read_record(workspace: Path) -> dict:
    """What ``status`` reports: the record, or why there is none.

    A workspace created before 0.14.0 has no record; the next ``upgrade``
    writes one, so no migration exists for it.
    """
    path = workspace / KIT_SOURCE_RECORD
    if not fs.exists(path):
        return {"recorded": False, "detail": LEGACY_DETAIL}
    text = fs.read_text(path)
    try:
        data = json.loads(text) if text is not None else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return {"recorded": False, "detail": f"unreadable record at {KIT_SOURCE_RECORD}"}
    return {"recorded": True, **{key: data.get(key) for key in (
        "version", "commit", "dirty", "source", "recordedAt", "allowedDirty", "reason")
        if key in data}}


def describe_record(entry: dict) -> str:
    """One human line for ``status``."""
    if not entry.get("recorded"):
        return entry.get("detail", LEGACY_DETAIL)
    commit = entry.get("commit")
    at = f"at {commit[:12]}" if isinstance(commit, str) and commit else "at an unknown commit"
    dirty = entry.get("dirty")
    state = "clean" if dirty is False else "dirty" if dirty is True else "dirty state unknown"
    suffix = ", allowed by --allow-dirty-kit" if entry.get("allowedDirty") else ""
    return f"{entry.get('version')} {at} ({entry.get('source')}, {state}{suffix})"

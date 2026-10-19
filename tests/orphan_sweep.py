"""orphan_sweep: removes scratch directories a killed test run left behind.

A suite that needs a scratch forge allocates it with `allocate()`: a
directory under this checkout's own temporary root, named with
`OWNED_PREFIX` and holding `OWNER_MARKER` before anything is copied into it.
`addCleanup` removes it on a normal run, but `addCleanup` never runs when
the process is killed -- a session limit, a timeout or a cancelled agent all
kill it -- and the next run's `sweep()` removes what survived.

Ownership is the marker, never a name, an age or git's ignorance of a path.
`implementations/` and `skills/*/scripts` also hold an operator's own
repositories, whose names can look exactly like a fixture's, so nothing
there is ever swept: a fixture a killed run left inside the live repository
stays until someone removes it by hand. Within the temporary root only
direct children with the prefix and an exact, regular marker file go, and
only once they are older than `MIN_AGE_SECONDS`, because a sibling process
may still be using a fresh one. The root sits at a predictable path in the
shared temporary directory, so it is created private (mode 0700) and used
only while it stays private and this user's: one another user created first
is refused, never written into or swept. A symlinked root, candidate or
marker is refused, and `shutil.rmtree` does not follow links inside a
payload.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
import time
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parents[1]

#: This checkout's own temporary root, namespaced by the checkout's path so
#: two checkouts never sweep each other's scratch directories.
SUITE_TEMP_ROOT = Path(tempfile.gettempdir()).resolve() / (
    "papersmith-suite-" + hashlib.sha256(os.fsencode(FORGE_ROOT)).hexdigest()[:20])

OWNED_PREFIX = "_papersmith-test-"
OWNER_MARKER = ".papersmith-test-owner"
OWNER_CONTENT = b"papersmith-suite-scratch:v1\n"

#: An orphan's owner is dead; a sibling's scratch directory is live. One hour
#: is far above any single test's lifetime and far below the gap between
#: sessions.
MIN_AGE_SECONDS = 3600


def _private_directory(path: Path) -> bool:
    """`path` is a directory this user owns, reached through no symlink,
    that no other user can enter."""
    if path.resolve() != path.absolute():
        return False
    entry = path.lstat()
    return (stat.S_ISDIR(entry.st_mode) and entry.st_uid == os.getuid()
            and not entry.st_mode & 0o077)


def _owned(directory: Path) -> bool:
    """`directory` holds the exact marker, as a regular file."""
    marker = directory / OWNER_MARKER
    if not stat.S_ISREG(marker.lstat().st_mode):
        return False
    with marker.open("rb") as stream:
        return stream.read(len(OWNER_CONTENT) + 1) == OWNER_CONTENT


def allocate(label: str = "forge-") -> Path:
    """A fresh, marked scratch directory under `SUITE_TEMP_ROOT`; the caller
    still registers its own cleanup. `label` only names it. The marker is
    written before the caller can copy anything in, so a copy interrupted
    halfway is still owned and still swept."""
    root = SUITE_TEMP_ROOT
    if root.resolve() != root.absolute():
        raise OSError(f"{root} must not be reached through a symlink")
    root.mkdir(mode=0o700, exist_ok=True)
    if not _private_directory(root):
        raise OSError(f"{root} must be a directory only this user can enter; "
                      "remove it, or point TMPDIR at a private directory")
    safe = "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "_" for c in label)
    path = Path(tempfile.mkdtemp(prefix=OWNED_PREFIX + safe, dir=root))
    (path / OWNER_MARKER).write_bytes(OWNER_CONTENT)
    return path


def sweep(min_age_seconds: float = MIN_AGE_SECONDS, now: float | None = None) -> list[str]:
    """Removes the owned scratch directories older than `min_age_seconds`
    under `SUITE_TEMP_ROOT`, and nothing anywhere else. Returns the absolute
    paths it removed: one that vanished or could not be removed is not
    reported, and does not stop the others."""
    now = time.time() if now is None else now
    root = SUITE_TEMP_ROOT
    try:
        if not _private_directory(root):
            return []
        children = sorted(root.iterdir())
    except OSError:
        return []
    removed: list[str] = []
    for child in children:
        if not child.name.startswith(OWNED_PREFIX):
            continue
        try:
            entry = child.lstat()
            if not stat.S_ISDIR(entry.st_mode) or not _owned(child):
                continue
            if now - entry.st_mtime < min_age_seconds:
                continue
            shutil.rmtree(child)
        except OSError:
            continue
        removed.append(str(child))
    return removed


def sweep_and_report() -> None:
    """`setUpModule` entry point: sweeps, and says what it removed. Silence
    means nothing was left behind, which is the normal case."""
    if os.environ.get("FORGE_SKIP_ORPHAN_SWEEP"):
        return
    for path in sweep():
        print(f"orphan_sweep: removed {path} (left by a killed run)")

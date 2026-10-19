from __future__ import annotations

import shutil
import sys
from pathlib import Path
from impl_gitops import git
from impl_layout import FORGE_ROOT, WORKSPACE
from impl_refusals import Refused


#: The directory this skill appends its own ledger to, relative to a product
#: root. Named here rather than imported from the position module because this
#: guard must not depend on the thing it is excusing.
LEDGER_DIRECTORY = ".implementation"


def _is_own_bookkeeping(porcelain_line: str) -> bool:
    """Whether one `git status --porcelain` line is this skill's own ledger.

    The guard exists so the skill never mutates a repository carrying somebody
    else's uncommitted work. Its own append-only ledger is not somebody else's
    work, and counting it produced a measured deadlock: every ledger-appending
    command (`position`, `discuss`, `gate`, `close`, `step`) leaves the tree
    dirty, so the next clean-requiring command (`plan`, `apply`, `step`)
    refuses. Measured on a scratch target -- one step ran, the second returned
    `DIRTY_WORKTREE` with `M <product>/.implementation/position.jsonl` as the
    only entry, and three ran back to back once that path was excluded.

    This excuses the path, never the question of whether the ledger belongs in
    the index at all. That is a separate decision, and this guard behaves the
    same either way -- which is the point: a repository that ignores its ledger
    and one that commits it must not disagree about whether a step may run.

    Porcelain paths are repository-relative. A rename carries two of them
    (`old -> new`) and both are checked, because a half-matched rename is not
    this skill's own bookkeeping.
    """
    payload = porcelain_line[3:] if len(porcelain_line) > 3 else ""
    sides = payload.split(" -> ") if " -> " in payload else [payload]
    return bool(sides) and all(
        LEDGER_DIRECTORY in Path(side.strip().strip('"')).parts
        for side in sides if side.strip())


def require_clean_worktree(target: Path) -> None:
    dirty = [line for line in git(target, "status", "--porcelain").splitlines()
             if line.strip() and not _is_own_bookkeeping(line)]
    if dirty:
        raise Refused(
            "DIRTY_WORKTREE",
            "The target working tree has uncommitted or untracked changes. "
            "Commit or stash them first; this skill never mutates a dirty repository.",
        )


def own_bookkeeping_snapshot(target: Path) -> dict[str, bytes | Path | None]:
    """The ledger files `require_clean_worktree` let through, as they are now.

    The guard excuses this skill's ledger, so a mutation can begin with it
    modified, deleted or untracked, and the rollback that resets and cleans
    the tree after a failed mutation would revert or delete exactly that
    (#80). Take this before the mutation and hand it to
    `restore_starting_point`. Keyed by repository-relative path: a file's
    bytes, a symlink's target (a `Path`), or None where the tree holds
    nothing (a deletion, the old side of a rename). A ledger the repository
    ignores is not listed, because neither reset nor clean touches it.
    """
    fields = iter(git(target, "status", "--porcelain", "-z", "--untracked-files=all").split("\0"))
    snapshot: dict[str, bytes | Path | None] = {}
    for entry in fields:
        if len(entry) < 4:
            continue
        # `-z` prints a rename or copy as `XY new\0old\0`, unquoted.
        paths = [entry[3:]]
        if "R" in entry[:2] or "C" in entry[:2]:
            paths.append(next(fields, ""))
        if all(LEDGER_DIRECTORY in Path(path).parts for path in paths):
            for path in paths:
                file = target / path
                if file.is_symlink():
                    snapshot[path] = file.readlink()
                elif file.is_file():
                    snapshot[path] = file.read_bytes()
                else:
                    snapshot[path] = None
    return snapshot


def restore_starting_point(target: Path, ledger: dict[str, bytes | Path | None]) -> None:
    """Throw away what a failed mutation wrote, keeping the ledger (#80).

    The tree was clean apart from the ledger when the mutation began, so
    resetting and cleaning it removes what the mutation wrote. The ledger
    files in `ledger`, from `own_bookkeeping_snapshot`, are then put back as
    they were: a file's bytes or a symlink's target, not whether they were
    staged.
    """
    git(target, "reset", "-q", "--hard", check=False)
    git(target, "clean", "-qfd", check=False)
    # Clear every ledger path of what the reset left there before writing any
    # back, parents first. The reset can rebuild a committed directory where
    # a file stood, or put a committed symlink back over a directory; clearing
    # a path beneath that symlink first would delete through it.
    for path in sorted(ledger, key=lambda name: len(Path(name).parts)):
        file = target / path
        if file.is_symlink() or file.is_file():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(file)
    for path, kept in ledger.items():
        if kept is None:
            continue
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(kept, Path):
            file.symlink_to(kept)
        else:
            file.write_bytes(kept)


def resolve_target(raw: str) -> Path:
    target = Path(raw).expanduser().resolve()
    try:
        target.relative_to(WORKSPACE.resolve())
    except ValueError:
        raise Refused(
            "OUTSIDE_WORKSPACE",
            f"Target must live under {WORKSPACE}. Clone the repository there first — "
            "the forge's own environment is never a workspace for generated code.",
        )
    if not (target / ".git").exists():
        raise Refused("NOT_A_GIT_REPO", f"{target} is not a git repository.")
    return target


def require_non_forge_interpreter() -> None:
    prefix = Path(sys.prefix).resolve()
    try:
        prefix.relative_to((FORGE_ROOT / "skills").resolve())
    except ValueError:
        return
    raise Refused(
        "FORGE_INTERPRETER",
        "This process is running inside one of the forge's own virtualenvs. "
        "Re-run with a system interpreter so the target venv never inherits it.",
    )

#!/usr/bin/env python3
"""A fast iteration tier: run only the tests a change plausibly touches.

**Why this exists.** The full suite is one process and takes about twenty
minutes. That is the right price for the merge gate and the wrong price for the
edit-run loop, where the author wants an answer in under a minute. This script
selects a small set of test files from the working tree's own changes and runs
just those, plus a fixed set of cheap guards that catch the repository-wide
drift (version sources, generated roster, forge gate shape, collection errors,
personal-context leaks) that a narrow selection would otherwise never notice.

**What it selects.** By default the changed files are the uncommitted work only:
`git diff --name-only HEAD` (staged and unstaged) plus untracked files.
`--since REF` additionally includes `git diff --name-only REF...HEAD`, for
work already committed on a branch. Then:

* a changed `tests/test_*.py` is selected as-is;
* every other changed file yields path-ish tokens (its repo-relative path, its
  file name only when exactly one tracked file has that basename, the dotted
  module path for files under `src/` and `skills/_core/`, and `skills/<name>` for a skill file), and a test file is selected when its
  text contains any token. Bare stems such as `init` or `core` are deliberately
  NOT tokens: they match almost everything and would turn this into the full
  suite;
* the guard set is always added.

**Why documents select nothing.** A changed non-code file (`.md`, `.json`,
`.txt`, `.toml`, `.yml`, `.yaml`, `.gitkeep`, or anything under `odd/`, `docs/`,
`openspec/`) produces no mention tokens. A document is named by half the suite,
so a text match against it carries no signal and selects dozens of unrelated
files; the effect of `package.json`, `CHANGELOG.md` or `README.md` is already
covered by the guard set. A changed test file is still selected as a changed test.

**Slow tests.** `SLOW_TESTS` lists a few individually measured tests (about
170 s together). They are passed to pytest with `--deselect` and printed with
their measured seconds; `--with-slow` includes them, and the full gate always does.

**What it cannot know.** This is a textual heuristic. It misses a test that
exercises a module only indirectly (through a CLI, a fixture, a generated file
or a re-export), and it cannot see a test that never names the thing it covers.
That is the reason the full gate still runs before merge. A green fast tier
means "the obvious tests pass", never "the suite is green", and this script
says so on its last line every time.

Usage:
    python3 scripts/fast_tests.py                # changed tests + guards
    python3 scripts/fast_tests.py --since origin/main  # also include committed work
    python3 scripts/fast_tests.py --with-slow    # include the deselected slow tests
    python3 scripts/fast_tests.py --guards-only  # only the guard set
    python3 scripts/fast_tests.py --list         # show selection and why; run nothing
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path, PurePosixPath

FORGE = Path(__file__).resolve().parent.parent

#: Cheap, repository-wide drift detectors. Always run, whatever changed. An
#: entry may be a pytest node id (`file::Class`); its file part must exist.
GUARDS: tuple[str, ...] = (
    "tests/test_version_sources.py",
    "tests/test_papersmith_generators.py",
    "tests/test_workspace_commands_e2e.py",
    "tests/test_forge_gate.py",
    "tests/test_suite_collects.py",
    "tests/test_no_personal_context_dependency.py",
    "tests/test_agents.py",
    "tests/test_proposal_implementation.py::ReportFirstSectionProseTests",
)

#: Measured slow tests (node id, seconds on the author's tree). Deselected by
#: default so one of them cannot turn a file selection into a multi-minute run;
#: `--with-slow` puts them back. The full gate always runs them.
SLOW_TESTS: tuple[tuple[str, int], ...] = (
    ("tests/test_proposal_implementation.py::StepCommandTests::"
     "test_a_step_killed_mid_run_leaves_a_started_line_with_no_partner", 120),
    ("tests/test_implementation_domain_mutation.py::PerLeafChangeMutationTests::"
     "test_every_leaf_moves_exactly_its_measured_case_set", 35),
    ("tests/test_skill_audit.py::UsageReferenceTests::"
     "test_every_documented_invocation_runs", 16),
)

#: Above this many selected files the run is probably not "fast" any more.
MAX_FAST_FILES = 12

#: A file of these kinds, or anything under these directories, is documentation
#: or configuration: it produces no mention tokens (see the module docstring).
NON_CODE_SUFFIXES = (".md", ".json", ".txt", ".toml", ".yml", ".yaml", ".gitkeep")
NON_CODE_DIRS = ("odd", "docs", "openspec")

REMINDER = "fast tier only - run `npm run test:all` (or let CI run) before merging"


# --------------------------------------------------------------------------
# Pure selection
# --------------------------------------------------------------------------

def _is_test_file(path: str) -> bool:
    p = PurePosixPath(path)
    return p.parts[:1] == ("tests",) and len(p.parts) == 2 \
        and p.name.startswith("test_") and p.suffix == ".py"


def _dotted(parts: tuple[str, ...]) -> str | None:
    """Dotted module path for a `.py` path's parts, or None for other files."""
    if not parts or not parts[-1].endswith(".py"):
        return None
    stem = parts[-1][:-3]
    body = parts[:-1] if stem == "__init__" else (*parts[:-1], stem)
    # A single segment (`papersmith` from src/papersmith/__init__.py) is a bare
    # stem in disguise and matches nearly every test, so it is not a token.
    return ".".join(body) if len(body) > 1 else None


def is_non_code(path: str) -> bool:
    p = PurePosixPath(path)
    return p.name.endswith(NON_CODE_SUFFIXES) or (p.parts[0] in NON_CODE_DIRS if p.parts else False)


def path_tokens(path: str, basename_counts: dict[str, int] | None = None) -> list[str]:
    """Path-ish tokens that identify `path` inside another file's text.

    The bare file name is a token only when exactly one tracked file has that
    basename (`basename_counts`); `README.md`, `__init__.py` and friends would
    otherwise match half the suite.
    """
    if is_non_code(path):
        return []
    p = PurePosixPath(path)
    tokens = [p.as_posix()]
    if (basename_counts or {}).get(p.name) == 1:
        tokens.append(p.name)
    parts = p.parts
    if parts[:1] == ("src",):
        dotted = _dotted(parts[1:])
        if dotted:
            tokens.append(dotted)
    if parts[:2] == ("skills", "_core"):
        for dotted in (_dotted(parts), _dotted(parts[1:])):
            if dotted:
                tokens.append(dotted)
    if parts[:1] == ("skills",) and len(parts) > 2:
        tokens.append(f"skills/{parts[1]}")
    return list(dict.fromkeys(tokens))


def select_tests(changed: list[str], texts: dict[str, str], *,
                 basename_counts: dict[str, int] | None = None,
                 guards: tuple[str, ...] = GUARDS,
                 guards_only: bool = False) -> dict[str, str]:
    """Ordered {test: reason}. `texts` maps each existing test file to its text;
    `basename_counts` maps a file name to how many tracked files carry it."""
    picked: dict[str, str] = {}
    if not guards_only:
        for path in changed:
            if _is_test_file(path) and path in texts:
                picked.setdefault(path, "changed test")
        for path in changed:
            if _is_test_file(path):
                continue
            tokens = path_tokens(path, basename_counts)
            for test in sorted(texts):
                if test in picked:
                    continue
                hit = next((t for t in tokens if t in texts[test]), None)
                if hit:
                    picked[test] = f"mentions {hit}"
    for guard in guards:
        picked.setdefault(guard, "guard")
    # A class-level entry is redundant once its whole file is selected.
    for key in [k for k in picked if "::" in k]:
        if key.split("::")[0] in picked:
            del picked[key]
    return picked


def slow_to_deselect(picked: dict[str, str], *, with_slow: bool,
                     slow: tuple[tuple[str, int], ...] = SLOW_TESTS
                     ) -> list[tuple[str, int]]:
    """Slow tests that live in a selected file (or under a selected node id)."""
    if with_slow:
        return []
    return [(node, secs) for node, secs in slow
            if any(node == k or node.startswith(k + "::") for k in picked)]


def size_warning(picked: dict[str, str]) -> str:
    files = {k.split("::")[0] for k in picked}
    if len(files) <= MAX_FAST_FILES:
        return ""
    return (f"warning: {len(files)} test files selected (more than "
            f"{MAX_FAST_FILES}); consider --guards-only")


# --------------------------------------------------------------------------
# Thin shell: git, files, subprocess
# --------------------------------------------------------------------------

def _git(root: Path, *args: str) -> list[str] | None:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def changed_files(root: Path, since: str | None = None) -> list[str]:
    """Uncommitted work (staged + unstaged + untracked); with `since`, also the
    commits in `since...HEAD`."""
    queries = [
        ("diff", "--name-only", "HEAD"),
        ("ls-files", "--others", "--exclude-standard"),
    ]
    if since:
        queries.append(("diff", "--name-only", f"{since}...HEAD"))
    seen: dict[str, None] = {}
    for query in queries:
        for line in _git(root, *query) or []:
            seen.setdefault(line, None)
    return list(seen)


def base_description(since: str | None) -> str:
    if since:
        return f"uncommitted work + {since}...HEAD"
    return "uncommitted work (HEAD)"


def tracked_basename_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in _git(root, "ls-files") or []:
        name = PurePosixPath(line).name
        counts[name] = counts.get(name, 0) + 1
    return counts


def read_test_texts(root: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in sorted((root / "tests").glob("test_*.py")):
        texts[f"tests/{path.name}"] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def existing_guards(root: Path, guards: tuple[str, ...] = GUARDS) -> tuple[str, ...]:
    return tuple(g for g in guards if (root / g.split("::")[0]).exists())


def resolve_interpreter(root: Path) -> tuple[str, str]:
    """The gate's interpreter (derived from setup_env.py), else sys.executable."""
    setup = root / "scripts" / "setup_env.py"
    if setup.exists():
        try:
            spec = importlib.util.spec_from_file_location("papersmith_setup_env", setup)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            candidate = module.MAMBA_ROOT / "envs" / module.ENV_NAME / "bin" / "python"
            if candidate.exists():
                return str(candidate), "gate interpreter"
        except Exception:  # a broken setup script must not stop the fast tier
            pass
    return sys.executable, "sys.executable (gate interpreter not found)"


def pytest_command(python: str, targets: list[str],
                   deselect: list[str] | tuple[str, ...] = ()) -> list[str]:
    cmd = [python, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
           *targets]
    for node in deselect:
        cmd += ["--deselect", node]
    return cmd


def format_selection(picked: dict[str, str]) -> str:
    width = max((len(t) for t in picked), default=0)
    return "\n".join(f"{t.ljust(width)}  <- {why}" for t, why in picked.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fast test tier: changed-file tests plus guards.")
    parser.add_argument("--guards-only", action="store_true",
                        help="run only the guard set")
    parser.add_argument("--with-slow", action="store_true",
                        help="include the measured slow tests (deselected by default)")
    parser.add_argument("--list", action="store_true",
                        help="print the selection and why; run nothing")
    parser.add_argument("--since", metavar="REF",
                        help="also include commits in REF...HEAD "
                             "(e.g. origin/main or HEAD~1)")
    parser.add_argument("--root", type=Path, default=FORGE,
                        help="repository root (default: this repository)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    changed = [] if args.guards_only else changed_files(root, args.since)
    picked = select_tests(changed, read_test_texts(root),
                          basename_counts=tracked_basename_counts(root),
                          guards=existing_guards(root),
                          guards_only=args.guards_only)

    if not args.guards_only:
        print(f"base: {base_description(args.since)}")
    print(format_selection(picked) if picked else "(nothing selected)")
    if not args.guards_only and all(why == "guard" for why in picked.values()):
        print("nothing but guards selected: no changed file maps to a test")

    warning = size_warning(picked)
    if warning:
        print(warning)
    deselected = slow_to_deselect(picked, with_slow=args.with_slow)
    if deselected:
        print(f"deselected {len(deselected)} slow test(s); the full gate still runs them "
              "(use --with-slow to include):")
        for node, secs in deselected:
            print(f"  ~{secs}s  {node}")
    print(f"selected: {len({k.split('::')[0] for k in picked})} test file(s)")

    code = 0
    if not args.list and picked:
        python, label = resolve_interpreter(root)
        print(f"interpreter: {python} [{label}]", flush=True)
        code = subprocess.run(pytest_command(python, list(picked), [n for n, _ in deselected]), cwd=root).returncode
    print(REMINDER)
    return code


if __name__ == "__main__":
    sys.exit(main())

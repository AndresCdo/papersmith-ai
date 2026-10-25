#!/usr/bin/env python3
"""Keep papersmith's issue and PR backlog grouped by root, and machine-checked.

Repository-only maintainer tooling (never shipped to workspaces). The protocol
it serves is ``maintainer/skills/backlog-steward/SKILL.md``; the root map it
checks is ``maintainer/backlog/roots.json``.

Commands:

* ``snapshot``  -- write the open issues and PRs (via ``gh``) to a JSON file.
* ``check``     -- every open issue sits in exactly one root, every listed issue
  is still open, every open PR links issues of a single root. Exit 1 on drift.
* ``stale``     -- list issues whose cited files or line numbers no longer exist
  in this checkout: a hint that the code moved or the defect is gone, never a
  verdict.
* ``render``    -- print the tracker issue body from the root map.
* ``pr-link``   -- refuse a PR body that links no issue (the CI gate).

Standard library only, so it runs on a bare CI runner.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = REPO / "maintainer" / "backlog" / "roots.json"
REQUIRED_ROOT_FIELDS = ("fix", "state", "tier")

_COMMENT = re.compile(r"<!--.*?-->", re.S)
#: The repository whose issues count. GitHub accepts `owner/repo#N` for its own
#: repository, so a qualified reference counts only when it names this one.
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "LIAUNAL/papersmith-ai")

# A keyword, an optional colon, then one or more `#N` or `owner/repo#N`
# separated by whitespace, commas or "and".
_REF = r"(?:[\w.-]+/[\w.-]+)?#\d+\b"
_LINK = re.compile(
    rf"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?)\b:?((?:(?:\s+|\s*,\s*|\s+and\s+){_REF})+)",
    re.I,
)
_NUMBER = re.compile(r"(?:([\w.-]+/[\w.-]+))?#(\d+)")
_PATH = re.compile(
    r"`([\w./-]+\.(?:py|ts|tsx|mjs|js|json|sh|md|yml|yaml|toml|cjs))(?::(\d+)(?:\s*[-–]\s*(\d+))?)?`"
)


def issue_refs(body: str | None, repo: str = REPO_SLUG) -> list[int]:
    """Issue numbers of `repo` a PR body links with Closes/Fixes/Resolves/Refs."""
    text = _COMMENT.sub("", body or "")
    found = set()
    for match in _LINK.finditer(text):
        for owner, number in _NUMBER.findall(match.group(1)):
            if not owner or owner.lower() == repo.lower():
                found.add(int(number))
    return sorted(found)


def check_roots(roots: dict, issues: list[dict], prs: list[dict]) -> list[str]:
    """Problems that make the root map disagree with the live backlog."""
    problems: list[str] = []
    owner: dict[int, list[str]] = {}
    for root in roots.get("roots", []):
        missing = [f for f in REQUIRED_ROOT_FIELDS if f not in root]
        if missing:
            problems.append(f"root {root.get('key')} lacks {', '.join(missing)}")
        for number in root.get("issues", []):
            owner.setdefault(number, []).append(root["key"])

    open_numbers = {i["number"] for i in issues}
    for number in sorted(open_numbers):
        keys = owner.get(number, [])
        if not keys:
            problems.append(f"#{number} is open but sits in no root")
        elif len(keys) > 1:
            problems.append(f"#{number} sits in more than one root: {', '.join(keys)}")
    for number in sorted(set(owner) - open_numbers):
        problems.append(f"#{number} is listed in root {owner[number][0]} but is not open")

    for pr in sorted(prs, key=lambda p: p["number"]):
        refs = issue_refs(pr.get("body"))
        if not refs:
            problems.append(f"PR #{pr['number']} links no issue (Closes/Fixes/Resolves/Refs #N)")
            continue
        keys = sorted({k for n in refs for k in owner.get(n, [])})
        if len(keys) > 1:
            problems.append(f"PR #{pr['number']} spans more than one root: {', '.join(keys)}")
    return problems


def _repo_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True
        ).stdout
        files = out.splitlines()
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return [
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)
    ]


def stale_refs(body: str | None, root: Path, files: list[str] | None = None) -> list[str]:
    """Cited paths (and `path:line` / `path:a-b`) this checkout cannot satisfy."""
    files = files if files is not None else _repo_files(root)
    stale: list[str] = []
    seen = set()
    for match in _PATH.finditer(body or ""):
        path, first, last = match.groups()
        cited = match.group(0).strip("`")
        if cited in seen:
            continue
        seen.add(cited)
        candidates = [f for f in files if f == path or f.endswith("/" + path.lstrip("./"))]
        if not candidates:
            stale.append(f"{path} (no such file)")
            continue
        line = int(last or first or 0)
        if not line:
            continue
        lengths = []
        for candidate in candidates:
            try:
                lengths.append(len((root / candidate).read_text(errors="replace").splitlines()))
            except OSError:
                lengths.append(0)
        if max(lengths) < line:
            stale.append(f"{cited} (file has {max(lengths)} lines)")
    return stale


def render(roots: dict, issues: list[dict], prs: list[dict]) -> str:
    """The tracker issue body: roots by tier, each with its issues and PRs."""
    titles = {i["number"]: i["title"] for i in issues}
    links: dict[int, list[int]] = {}
    for pr in prs:
        for number in issue_refs(pr.get("body")):
            links.setdefault(number, []).append(pr["number"])
    lines = [
        "# Backlog roots",
        "",
        "Generated by `python3 maintainer/backlog.py render` from "
        "`maintainer/backlog/roots.json`. Edit the map, not this body.",
        "",
    ]
    if roots.get("pinned_commit"):
        lines += [f"Triaged against `{roots['pinned_commit']}`.", ""]
    by_tier: dict[int, list[dict]] = {}
    for root in roots.get("roots", []):
        by_tier.setdefault(root.get("tier", 9), []).append(root)
    for tier in sorted(by_tier):
        lines += [f"### Tier {tier}", ""]
        for root in by_tier[tier]:
            lines.append(f"**{root['key']}** — {root.get('title', '')} · state: {root.get('state', '?')}")
            lines.append(f"Fix: {root.get('fix', '')}")
            pr_numbers = sorted({p for n in root.get("issues", []) for p in links.get(n, [])})
            if pr_numbers:
                lines.append("PRs: " + ", ".join(f"#{p}" for p in pr_numbers))
            if root.get("proof"):
                lines.append(f"Proof: {root['proof']}")
            for number in root.get("issues", []):
                mark = "x" if number not in titles else " "
                lines.append(f"- [{mark}] #{number} {titles.get(number, '(closed)')}")
            lines.append("")
    return "\n".join(lines)


def _gh_json(*args: str) -> list[dict]:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def live_snapshot() -> dict:
    fields = "number,title,body"
    return {
        "issues": _gh_json("issue", "list", "--state", "open", "--limit", "1000", "--json", fields),
        "prs": _gh_json("pr", "list", "--state", "open", "--limit", "1000", "--json", fields),
    }


def _load_snapshot(path: str | None) -> dict:
    return json.loads(Path(path).read_text()) if path else live_snapshot()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot", help="write open issues and PRs to a JSON file")
    snap.add_argument("output")
    for name in ("check", "stale", "render"):
        p = sub.add_parser(name)
        p.add_argument("--snapshot", help="JSON from `snapshot` (default: query gh live)")
        p.add_argument("--roots", default=str(DEFAULT_ROOTS))
    link = sub.add_parser("pr-link", help="refuse a PR body that links no issue")
    group = link.add_mutually_exclusive_group(required=True)
    group.add_argument("--body-env", help="environment variable holding the PR body")
    group.add_argument("--body-file")
    args = parser.parse_args(argv)

    if args.command == "pr-link":
        body = os.environ.get(args.body_env, "") if args.body_env else Path(args.body_file).read_text()
        refs = issue_refs(body)
        if not refs:
            print(
                "This PR links no issue. Add `Closes #N` (or Fixes/Resolves) for the issue it "
                "resolves, or `Refs #N` for a partial step; a reference inside an HTML comment "
                "does not count.",
                file=sys.stderr,
            )
            return 1
        print("linked: " + ", ".join(f"#{n}" for n in refs))
        return 0

    if args.command == "snapshot":
        Path(args.output).write_text(json.dumps(live_snapshot(), indent=2))
        return 0

    snapshot = _load_snapshot(args.snapshot)
    issues, prs = snapshot["issues"], snapshot["prs"]
    if args.command == "stale":
        files = _repo_files(REPO)
        for issue in sorted(issues, key=lambda i: i["number"]):
            refs = stale_refs(issue.get("body"), REPO, files)
            if refs:
                print(f"#{issue['number']} {issue['title']}")
                for ref in refs:
                    print(f"    {ref}")
        return 0

    roots = json.loads(Path(args.roots).read_text())
    if args.command == "render":
        print(render(roots, issues, prs))
        return 0
    problems = check_roots(roots, issues, prs)
    for problem in problems:
        print(problem)
    if not problems:
        print(f"ok: {len(issues)} open issues and {len(prs)} open PRs sit in {len(roots['roots'])} roots")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

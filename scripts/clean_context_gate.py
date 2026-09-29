#!/usr/bin/env python3
"""Run the declared gate twice under different personal contexts, and refuse to
call the two results equal unless they are.

**Why a differential, and not a flag.** The first version of this control pointed
`ENGRAM_BIN` at a nonexistent path and unset `ENGRAM_URL`, then re-ran the gate
and required "the same result as with the provider present". It could not fail:
nothing in the tracked tree reads either variable, and the gate spawns no agent,
so both runs were identical by construction. A control that cannot fail is worse
than no control, because it is read as evidence.

**What this does instead.** The declared gate runs under two `HOME`s that differ
only in the personal agent context they contain:

* an **empty** home — a bare `mktemp -d`;
* a **decoy** home — the same, populated with the shapes a developer's machine
  carries: `.pi/agent/settings.json`, `.pi/agent/mcp.json`, `.agents/skills/`,
  `.claude/skills/`, `.config/opencode/`, `.engram/`.

If any part of the gate reads the operator's personal context, the two runs
differ, and this script exits non-zero naming the difference. If none does, the
two runs agree and the property holds.

**Both homes are synthetic, which is the point.** Comparing "the operator's real
home" against "an empty one" would be trivially green on CI, where the home is
already bare. A decoy is present on every machine, so the control fires
everywhere: a test that reads `~/.pi` or `~/.agents` fails here on a laptop and
on a runner alike.

**Cost.** The declared gate runs twice. That is the price of a control that can
fail, and it is paid deliberately.

Usage:
    python3 scripts/clean_context_gate.py                # the whole declared gate
    python3 scripts/clean_context_gate.py --half node     # just the Node half
    python3 scripts/clean_context_gate.py --half python   # just the Python half
    python3 scripts/clean_context_gate.py --keep          # keep the temp homes
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FORGE = Path(__file__).resolve().parent.parent

#: Personal agent context, as files. Each entry is what a developer's machine
#: carries and what a verification path must therefore be able to ignore. They
#: are deliberately plausible rather than empty: an empty decoy would prove only
#: that the gate does not read a directory that does not exist.
DECOY_FILES: dict[str, str] = {
    ".pi/agent/settings.json": json.dumps(
        {"defaultModel": "decoy-model", "packages": ["npm:gentle-engram"]}, indent=2),
    ".pi/agent/mcp.json": json.dumps(
        {"mcpServers": {"engram": {"command": "engram", "args": ["mcp"]}}}, indent=2),
    ".pi/agent/gentle-ai/persona.json": json.dumps({"mode": "decoy"}, indent=2),
    ".agents/skills/decoy-skill/SKILL.md": (
        "---\nname: decoy-skill\ndescription: A personal skill that no test may read.\n---\n\n"
        "If a test's outcome changes because this file exists, the verification "
        "path depends on the operator's personal context.\n"),
    ".claude/skills/decoy-skill/SKILL.md": "---\nname: decoy-skill\n---\n\nPersonal skill.\n",
    ".config/opencode/skills/decoy-skill/SKILL.md": "---\nname: decoy-skill\n---\n\nPersonal.\n",
    ".engram/config.json": json.dumps({"data_dir": "/decoy/.engram"}, indent=2),
    ".gemini/skills/decoy-skill/SKILL.md": "---\nname: decoy-skill\n---\n\nPersonal.\n",
}

#: A failing test, in either half's vocabulary. pytest reports `FAILED path::test`
#: and `ERROR path`; `node --test` reports TAP `not ok N - name`. Collected as a
#: set, because two runs that fail the same tests in a different order have not
#: disagreed about anything that matters.
PYTEST_FAILURE = re.compile(r"(?m)^(FAILED|ERROR) (\S+)")
#: pytest reports a subtest failure on its own line, and `^(FAILED|ERROR)` does not
#: match it. Measured the hard way: without this pattern a run reported three
#: failing tests where pytest counted six, so two runs differing only in a
#: subfailure were called equal -- an under-observing control.
PYTEST_SUBFAILURE = re.compile(r"(?m)^SUBFAILED\(([^)]*)\) (\S+)")
TAP_FAILURE = re.compile(r"(?m)^not ok \d+ - (.+?)\s*$")


def declared_gate() -> list[list[str]]:
    """The gate's stages, read from `package.json` rather than restated here.

    A restated command string has to be edited alongside the defect it was meant
    to catch, which is the silence `tests/test_forge_gate.py` exists to close.
    """
    scripts = json.loads((FORGE / "package.json").read_text(encoding="utf-8"))["scripts"]
    stages = [stage.strip() for stage in scripts["test:all"].split("&&")]
    return [stage.split() for stage in stages]


def half_stages(half: str) -> list[list[str]]:
    stages = declared_gate()
    if half == "all":
        return stages
    keep = "test:node" if half == "node" else "test:py"
    selected = []
    for stage in stages:
        delegated = re.fullmatch(r"npm (?:run )?(\S+)", " ".join(stage))
        if delegated and delegated.group(1) == keep:
            selected.append(stage)
    if not selected:
        raise SystemExit(f"the declared gate delegates to {keep} nowhere: {stages}")
    return selected


def build_decoy_home(root: Path) -> Path:
    home = root / "decoy-home"
    for relative, content in DECOY_FILES.items():
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return home


def build_empty_home(root: Path) -> Path:
    home = root / "empty-home"
    home.mkdir(parents=True, exist_ok=True)
    return home


def run_gate(home: Path, stages: list[list[str]], log: Path) -> tuple[int, str]:
    """Run every stage under `home`, in order, stopping at the first failure --
    the same `&&` semantics the declared gate itself has."""
    environment = dict(os.environ, HOME=str(home))
    environment.pop("XDG_CONFIG_HOME", None)
    lines = [f"# HOME={home}"]
    code = 0
    with log.open("w", encoding="utf-8") as handle:
        for stage in stages:
            handle.write(f"# $ {' '.join(stage)}\n")
            handle.flush()
            done = subprocess.run(stage, cwd=str(FORGE), env=environment,
                                  stdout=handle, stderr=subprocess.STDOUT, text=True)
            lines.append(f"# $ {' '.join(stage)} -> exit {done.returncode}")
            code = done.returncode
            if code != 0:
                break
    return code, "\n".join(lines)


def failure_signature(log_text: str) -> list[str]:
    """The set of tests that failed, in either half's vocabulary.

    Derived from the output rather than from a count: two runs that both fail
    three tests, but not the same three, have disagreed, and a count would call
    them equal.
    """
    found = {f"{kind} {target}" for kind, target in PYTEST_FAILURE.findall(log_text)}
    found |= {f"SUBFAILED {subject} {test}" for subject, test in PYTEST_SUBFAILURE.findall(log_text)}
    found |= {f"not ok {name}" for name in TAP_FAILURE.findall(log_text)}
    return sorted(found)


def compare(left: dict, right: dict) -> list[str]:
    """Every way two runs disagree, as human-readable lines. Empty means equal.

    Takes dicts (`{"home", "code", "failures"}`) rather than reading files, so
    the inversion control below drives this exact function against a planted
    disagreement instead of re-implementing the comparison.
    """
    differences = []
    if left["code"] != right["code"]:
        differences.append(
            f"exit code differs: {left['home']} -> {left['code']}, "
            f"{right['home']} -> {right['code']}")
    only_left = sorted(set(left["failures"]) - set(right["failures"]))
    only_right = sorted(set(right["failures"]) - set(left["failures"]))
    for name in only_left:
        differences.append(f"fails only under {left['home']}: {name}")
    for name in only_right:
        differences.append(f"fails only under {right['home']}: {name}")
    return differences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--half", choices=("all", "node", "python"), default="all")
    parser.add_argument("--keep", action="store_true",
                        help="keep the temporary homes and logs for inspection")
    args = parser.parse_args(argv)

    stages = half_stages(args.half)
    root = Path(tempfile.mkdtemp(prefix="clean-context-gate-"))
    try:
        empty = build_empty_home(root)
        decoy = build_decoy_home(root)
        print(f"[clean-context] gate: {' && '.join(' '.join(s) for s in stages)}")
        print(f"[clean-context] homes: {empty} (empty) vs {decoy} (decoy)")

        empty_code, empty_note = run_gate(empty, stages, root / "empty.log")
        decoy_code, decoy_note = run_gate(decoy, stages, root / "decoy.log")
        empty_result = {"home": "empty", "code": empty_code,
                        "failures": failure_signature((root / "empty.log").read_text("utf-8"))}
        decoy_result = {"home": "decoy", "code": decoy_code,
                        "failures": failure_signature((root / "decoy.log").read_text("utf-8"))}

        print(empty_note)
        print(decoy_note)
        for result in (empty_result, decoy_result):
            print(f"[clean-context] {result['home']}: exit {result['code']}, "
                  f"{len(result['failures'])} failing test(s)")

        differences = compare(empty_result, decoy_result)
        if differences:
            print("\n[clean-context] FAIL: the gate's result depends on the "
                  "personal context it ran under, so it does not verify a machine "
                  "that has none:")
            for line in differences:
                print(f"  {line}")
            return 1

        print("\n[clean-context] OK: the gate's result is identical under an "
              "empty home and under one carrying personal agent context. The "
              "verification path does not read the operator's context.")
        return 0
    finally:
        if args.keep:
            print(f"[clean-context] kept: {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

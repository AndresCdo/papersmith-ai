# Feature: `papersmith init` reports its own progress

## Objective
`papersmith init` shows a progress bar, streams the log of the child processes it
runs (`npm install`, `scripts/setup_env.py install`) and prints an estimate of
the time left, while every programmatic caller keeps the byte-identical, silent
behaviour it has today.

## Problem
`initialize()` runs its long steps with `subprocess.run(capture_output=True)`:
for minutes the operator sees nothing at all, and the only signal is the final
summary. The environment step can take up to `PROVISION_TIMEOUT` (3600 s), so
"nothing for an hour" is a real state, not a hypothetical one.

## Design decisions
1. **The reporter is injected, and the default is silent.** `initialize(...,
   report=None)` means "no reporting"; the CLI builds the reporter from its own
   stream. This is not decoration: the MCP server spawns `papersmith init` as a
   child (`mcp/registry._build_init` → `ChildPlan(kind="cli")`) and captures its
   stdout, and the test suite calls `initialize()` directly. A reporter that
   wrote to stdout by default would corrupt both.
2. **Three modes, chosen by the stream.** `bar` when stdout is a TTY; `silent`
   otherwise (pipelines, MCP child, tests); `plain` only when explicitly asked
   for with `--progress`, one line per step plus the child's log — for CI, where
   a bar is noise but the log is the point.
3. **The estimate is calibrated, and says so.** The first estimate is the
   declared prior; once a step finishes, its measured time replaces its prior
   and the remaining priors are scaled by the observed pace. A running step that
   exceeds its own share grows the estimate live instead of leaving a number
   that cannot come true. The priors are priors: the environment step is a
   download whose duration nobody can know in advance.
4. **Child output is streamed, not captured.** A `Popen` line loop forwards each
   line to the reporter and keeps the tail, so the existing failure messages
   ("npm install failed: …", "environment provisioning failed: …") keep the same
   text and `initialize`'s return value is unchanged.
5. **Stdlib only**, like the rest of the CLI. No `tqdm`, no colour library.

## Slices
- **S1** `src/papersmith/core/progress.py`: `Step`, `Reporter` (plan/start/done/
  log/finish/remaining), `run_streaming()`. TDD with an injected clock.
- **S2** `init.py` builds the plan (excluding the steps it was told to skip),
  wraps each phase, and routes the two child steps through `run_streaming`.
- **S3** `init --progress` (+ the TTY auto-detection), README, CHANGELOG.

## Checks
`.venv/bin/python -m pytest tests/test_init_progress.py -q`; then the existing
init/CLI/MCP suites for regressions (silent default, same summary keys), the
README guards, and the fast tier. Kit rebuild is not needed (no `skills/` file
changes) unless the README's CLI table changes.

## Evidence

- **RED** before the module existed: `ImportError: cannot import name 'progress'`.
- **GREEN**: `tests/test_init_progress.py` 15 passed. One of them was wrong on the
  first run — it expected the closing line to carry the step count while
  `finish()` printed the summary after the bar; the implementation was simplified
  to one final line rather than the test loosened.
- **Regression**: four `EnvironmentProvisioningTests` broke on the new signature
  (`_run_env_install(root)` → `(root, report)`), so the reporter argument is
  optional in both private helpers and the two stubs in
  `tests/test_papersmith_init.py` take it. `test_papersmith_init.py` is back to
  its two pre-existing failures, both measured at `HEAD` earlier in the session
  (`WORKSPACE_ESCAPE` in the MCP init tool, and the pip editable-install path).
- **End to end, real CLI**: `init --no-npm --no-env --progress` printed
  `[4/5] projecting the harness surface (0s)` … `[5/5] done in 0s` — the plan
  excludes the steps the run was told to skip.
- **Bar in a real terminal**: run under `script -q /dev/null`, `isatty` is true
  and eleven frames render from `[....................] 0/5 copying the kit  left 3s`
  to `[####################] 5/5 done in 0s`, with the carriage returns present.
- **The silent path holds**: `tests/test_mcp_stdout_guard.py`,
  `test_mcp_tools.py`, `test_mcp_registry.py`, `test_mcp_e2e.py` and
  `test_cli_paper_e2e.py` — 68 passed. The MCP server's child invocation keeps a
  clean stdout.
- **Guards**: README vocabulary floor, derived-count sweep and the capability
  table — 12 passed. `sync-repo-harness.py --check` clean (92 files). Fast tier
  `7 failed, 263 passed, 345 subtests` where the seven are the known
  pre-existing set (5 × `GateInterpreterTests`, 2 × `test_papersmith_init`).
- `leaks_in` on the two new/changed files: clean. `init.py` carries `kaggle`
  five times **at `HEAD`** already, and it is outside the guard's surface
  (shipped skill files), so nothing was introduced here.
- Version moved to **0.9.0** in the three literals with its `## 0.9.0` section:
  `test_version_sources.py` fails on a shipped change since `v0.8.0` without the
  move, which is the repository's own rule rather than a preference.

## Next step
Not merged and not pushed: this work unit is committed on `feat/init-progress`
and merge/push is the operator's decision.

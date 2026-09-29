# Feature: Merge `fix/harness-skills-wiring` into `feat/command-center`

Status: in progress
Branch: `integration/command-center`
Created: 2026-05-18
Base: `feat/command-center` @ `876bd07` + merge of `fix/harness-skills-wiring` @ `b0b0cce`

## Goal

Land one integration branch that holds both the CI provisioning repair
(`fix/harness-skills-wiring`) and the Paper Command Center (`feat/command-center`),
with every declared gate green in the environment the gate itself names, so the
branch can be reviewed once and then delivered to `main` under ordinary
repository policy.

## Operator decisions (recorded)

1. **Merge shape.** A new `integration/command-center` branch, not a merge into
   either feature branch and not two ordered PRs. Both feature branches stay
   untouched for a later decision.
2. **Provisioning fix location.** The dependency repair goes on the integration
   branch only. `fix/harness-skills-wiring` keeps its current tip.
3. **Vocabulary leak.** Repair by deriving the names from the workspace
   inventory (the `skills/_core/implementation` precedent), not by widening the
   guard's exemption.

## Measured state before the merge

| Check | Result |
| --- | --- |
| Merge base | `4d70ad8` |
| Divergence | `feat/command-center` = `main` + 8; `fix/harness-skills-wiring` = `main` + 1 |
| Conflict check | `git merge-tree --write-tree fix/harness-skills-wiring feat/command-center` -> `090756d...`, exit 0 |
| File overlap | none (harness touches `test.yml`, `setup_env.py`, `test_proposal_implementation.py`) |
| Merge diff vs `main` | 45 files, +9083 (command center) + 3 files (harness) |

Gate runs under `.micromamba/envs/papersmith/bin/python -m pytest
--continue-on-collection-errors`, in throwaway worktrees:

| Tree | Result |
| --- | --- |
| `fix/harness-skills-wiring` | 10 failed / 2215 passed |
| `feat/command-center` (non-CC modules) | 18 failed / 2210 passed |
| merged | 26 failed / 5311 passed / 1 collection ERROR |

The merge repairs 2 failures that exist on `feat/command-center`
(`HolderUndeclaredMutationTests` x2, closed by the harness `_scratch_engine`
fix) and adds 3 of its own.

Attribution caveat: the 5 `test_forge_gate.py::GateInterpreterTests` failures
appear in all three runs because the gate path is repository-relative and a bare
worktree has no provisioned environment inside it. They are harness artifacts,
not merge effects.

## Blocking findings

- **P0 -- the merged CI cannot collect the new tests.** `scripts/setup_env.py`
  installs neither `fastapi` nor `uvicorn`, `watchfiles`, `pydantic`;
  `pyproject.toml` declares `dependencies = []`, so `pip install -e .` adds
  nothing. Measured: `ModuleNotFoundError: No module named 'fastapi'` while
  collecting `tests/test_command_center_server.py`, plus
  `test_suite_collects.py::test_every_test_module_loads` and two CC tests.
  Beyond CI: `requirements.txt` is a `manifest.KIT_ENTRIES` member, so every
  initialized workspace receives CC dependencies its shipped `setup_env.py`
  never installs.
- **P1 -- the guard cannot see the new tree.** `IMPORT_SCOPE_PATHSPECS` in
  `tests/test_forge_gate.py` reaches `skills/*/scripts/*.py`, never
  `skills/_core/command_center/*.py`, so the missing `fastapi` import is
  invisible to the derivation built to catch it.
- **P1 -- shipped surface leaks repository vocabulary.**
  `ReportFirstSectionProseTests::test_the_whole_forge_borrows_no_repository_s_vocabulary`
  fails on `feat/command-center` (pre-existing) with `['kaggle'] != []` in
  `skills/_core/command_center/health_inspector.py:56,83`,
  `state_extractor.py:659`, and `static/assets/index-Du6DExVG.js`.
- **P2 -- review workload and CI reachability.** `.github/workflows/test.yml`
  triggers on `pull_request: branches: [main]` only, so a PR between feature
  branches runs no CI; the CC slice is 9083 lines / 45 files in one PR.
- **P2 -- noise.** `docs/how-papersmith-works.html` is untracked and excluded
  from every scope.

## Task list

- [x] T0 -- Tracking and branch. `odd/tasks/merge-command-center.md` plus its
  Engram mirror `odd/merge-command-center/tasks`; `integration/command-center`
  created from `feat/command-center`.
  - Evidence: this document's work-unit commit on the branch.
- [x] T1 -- Merge `fix/harness-skills-wiring` into `integration/command-center`.
  - No conflicts: the `ort` strategy merged cleanly and the merge commit carries
    exactly the 3 harness files against its first parent.
  - Evidence: `fb5da52`; `.github/workflows/test.yml` (22), `scripts/setup_env.py`
    (6), `tests/test_proposal_implementation.py` (21); +29/-20.
- [x] T2 -- P0 provisioning repair on the integration branch.
  - `scripts/setup_env.py` gained `fastapi`, `uvicorn`, `watchfiles`, `pydantic`
    in `CONDA_BASE_PACKAGES`, with the derivation stated in the comment (the
    shipped `requirements.txt` names them; the shipped skill imports them).
  - Evidence: `50cfcb3`; provisioning re-run through the script itself
    (`python3 scripts/setup_env.py install --no-ingestion`) installed
    fastapi 0.141.1, uvicorn 0.54.0, watchfiles 1.3.0, pydantic 2.13.5 into
    `.micromamba/envs/papersmith`.
- [x] T3 -- P1 gate scope.
  - `IMPORT_SCOPE_PATHSPECS` gained `skills/_core/*/*.py`, so the derivation
    reaches the engine shelves. Proven by running the widened lock against the
    tree BEFORE the T2 repair:

    ```
    AssertionError: the interpreter the gate names cannot import 2
    distribution(s) this forge's own code requires: fastapi (e.g.
    skills/_core/command_center/server.py); uvicorn (e.g.
    skills/_core/command_center/server.py)
    ```

    and after it: `tests/test_forge_gate.py tests/test_suite_collects.py
    tests/test_command_center_server.py` -> 32 passed. The eight
    command-center modules plus the collection check -> 83 passed.
  - `watchfiles` stays out of the derived set on purpose: its import sits under
    `try/except ModuleNotFoundError`, which declares it optional there. That is
    why it is named in `scripts/setup_env.py` instead.
  - Evidence: `789e2be`.
- [ ] T4 -- P1 vocabulary repair.
  - Derive the `kaggle-accounts` skill/script table and the `kaggle-inbox`
    directory from the workspace's own inventory; rebuild the committed SPA so
    the bundle no longer carries the token.
  - Evidence: prose guard green; `vite build` reproduces the asset hashes.
- [ ] T5 -- Materialize and run the full gate in a proper environment (main
  checkout with `node_modules` and the provisioned env):
  `npm ci && npm test && .micromamba/envs/papersmith/bin/python -m pytest`.
  - Evidence: raw output recorded verbatim.
- [ ] T6 -- Judgment Day on the frozen merged tree, before any delivery.
  - Two blind judges, identical criteria, read-only, one exhaustive sweep each
    (two permitted: more than 400 changed lines). The findings above are NOT
    injected into the judge prompts; independent rediscovery is the verification.
  - Criteria: does the merged tree keep every declared gate green in the
    environment the gate names, and does every shipped contract stay coherent
    (manifest <-> provisioning <-> guard scope <-> shipped surface)?
  - At most two scoped fix/re-judgment rounds; terminal
    `JUDGMENT: APPROVED` or `JUDGMENT: ESCALATED`.
- [ ] T7 -- Delivery and close-out. PR `integration/command-center` -> `main`
  (base must be `main` so CI runs); record commit identities and raw gate output
  here; remove worktrees; mirror to Engram. Commit, push, PR and merge stay the
  operator's decision.

## Non-goals

- No modification of `main`, `fix/harness-skills-wiring`, or
  `feat/command-center` beyond reading them.
- No SDD/OpenSpec change: this is ODD.
- No new command-center features and no refactor of the CC surface beyond what
  T3 and T4 require to make the gate green.
- No `docs/how-papersmith-works.html` in any commit.

## Risks

- **Partial-collection green.** A suite that reports OK over the modules it
  managed to reach is indistinguishable from a green suite. T5 must be read for
  collection errors, not only for a pass count.
- **Rebuild drift.** T4 changes frontend source, so the committed bundle in
  `skills/_core/command_center/static/` must be regenerated in the same commit.
- **Guard widening (T3) may surface further gaps** in other skill trees that the
  narrower pathspec never reached. Each new gap is a decision point, not a
  silent exclusion.

## Close-out

(to be completed at T7)

- Gate evidence:
- Judgment Day verdict:
- Commit identities:

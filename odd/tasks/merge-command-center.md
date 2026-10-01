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
  optional, operator-side Engram mirror `odd/merge-command-center/tasks`;
  `integration/command-center` created from `feat/command-center`.
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
- [x] T4 -- P1 vocabulary repair.
  - **Operator decision (round 1):** the core-skill roster cannot be derived
    as-is, because seven skills ship a front door (`remote_cli.py` and
    `audit_cli.py` were invisible to the five-row tuple) and nothing else
    declares the five. Chosen: derive all seven and accept the payload change.
  - `health_inspector.front_door_skills(root)` derives the roster from the
    workspace's own `skills/*/scripts/*_cli.py`. The `SKILL_GATES` entry that
    carried the name was the `.get(skill, ())` default spelled out.
  - `state_extractor.inbox_directory(root)` reads the declaration the owning
    skill already makes (`INBOX_NAME`), parsed with `ast`; the payload gained
    `inbox.directory` and the SPA renders its label from that field.
  - The committed bundle was rebuilt (`vite build`), so the asset hash moves
    from `index-Du6DExVG.js` to `index-CUXqyhFi.js`; the CSS hash is unchanged,
    which is evidence the change reached only what it should.
  - The guard caught this work's own first draft: an explanatory comment named
    the word. Rewritten, not admitted -- shipped prose carries vocabulary
    exactly as data does.
  - Trade recorded in the code: a front door that was DELETED leaves nothing to
    derive from, so the CLI dimension can no longer report it missing.
    `skill_manifests` still walks the inventory, so a missing `SKILL.md` is
    still reported, and a workspace with no `skills/` now raises a warning.
  - Evidence: `1a79063`; the prose guard goes from 1 failed / 3 subfailures to
    **16 passed / 284 subtests**; the six command-center modules run 71 passed.
- [x] T5 -- Full gate in a properly provisioned environment.
  - First run: **2 failed / 5353 passed** -- T4's three subfailures gone, and
    two real branch defects surfaced, both failing identically under a real and
    an empty `HOME`, so neither was an environment artifact:
    - `test_mcp_registry`: `papersmith ui` landed and the MCP registry never
      learned it. `CLI_COMMANDS` gains `ui` in the parser's own order, and
      `CLI_DISPOSITIONS` gains `ui: out` -- it starts a server and opens a
      browser, so it is an operator's command, never a tool an agent calls
      mid-turn. The second lock went red only after the first fix, which is the
      guard chain working. Evidence: `4bd6103`.
    - `test_version_sources`: 18 shipped files had changed since `v0.5.1` with
      the version unmoved. `package.json` and `papersmith.__version__` move to
      `0.6.0` together and `CHANGELOG.md` gains the `## 0.6.0` section the lock
      requires -- a minor bump, per the semver policy the changelog states.
      Evidence: `52c905e`.
  - Final run: `npm run test:all` -> **exit 0, 5355 passed, 8 skipped, zero
    failures**, 14m59s, no collection errors.
  - Left alone deliberately: `package-lock.json` states `0.1.0`, was already
    stale before this work, and no test reads it.
- [x] T6 -- Judgment Day on the combined tree (shared with the engram feature's
  E6, per operator decision 6).

  **Verdict: `JUDGMENT: APPROVED`.**

  - **Frozen candidate:** `81f4c3a`, `git diff main..81f4c3a` = 68 files,
    +10831/-37, sha256 `845b82ce...`. **The verdict binds to the post-fix
    revision `a162749`** (`git diff main..a162749` sha256 `9ebafb86...`).
  - **Frozen ledger:** `.scratch/jd-combined/ledger.jsonl`, sha256
    `8ed2c0f8afe408d5aa500f5965f40211bf3f794061dfec8262e5e5984aec56f4`,
    unchanged through both rounds. 14 rows: 3 CRITICAL, 6 WARNING, 5 SUGGESTION.
  - **Discovery:** two blind judges, identical criteria, one exhaustive read-only
    sweep each. Four defects were found independently by BOTH: the
    `papersmith ui` interpreter path, the unexecutable `run-wiring-smoke`
    endpoint, the hand-restated gate roster, and the dangling `.pi/README.md`
    citation.
  - **Round 1** (5 commits, `c2d8c22`..`1227799`): the three severe rows, plus
    the two corroborated warnings the operator expanded the batch to cover.
  - **Resolutions:**

    | Row | Raised by | Re-judged by | Outcome |
    | --- | --- | --- | --- |
    | `JD-A-001` | judge A | judge B | `verified` |
    | `JD-A-002` | judge A | judge B | `verified` |
    | `JD-B-001` | judge B | judge A | `corroborated` (round 1) |
    | `JD-B-001` | judge B | fresh validator | `verified` (round 2) |

  - **Round 2** (`a162749`, test-only, **no source changed**): `JD-B-001`'s
    re-judge confirmed the defect and the fix of its stated mechanism, and
    declined to certify the *outcome* because every piece of evidence was
    stub-level -- no server ever started, and nothing observed that anything
    CREATES the derived path. It named two things it needed; both were added.
    That no source changed is itself the finding: the fix was right and the
    evidence was missing.
  - **Two of two rounds used; no severe row survived either.**
  - **Measured evidence:** the differential control on the fixed tree reports
    both halves `exit 0`, zero failing tests, identical under an empty home and
    under a decoy home carrying personal agent context (24m57s). The round-2
    end-to-end test was observed by hand: init 0.05s, first HTTP 200 at 0.36s,
    clean exit 0 after SIGTERM.
  - **Open informational rows** (never scheduled fixes; recorded for delivery):
    `JD-A-003`/`JD-B-005` the `run-wiring-smoke` endpoint needs a script no
    workspace receives; `JD-A-004`/`JD-B-006` the quality-gate roster is restated
    in three places; `JD-A-005` `--export-static` needs the full web stack just
    to copy files; `JD-B-007` the port scan overflows past 65535; `JD-B-008` the
    0.6.0 changelog omits the harness-symlink and dependency changes, and
    `package-lock.json` still reads `0.1.0`.
  - **Process correction, for the record:** both ledgers contain a `JD-B-001`
    (the engram plan's, and this one's). Prompts carried each row's JSON with its
    location, so no reference was ambiguous, but the IDs are not lineage-unique
    and the next review should number rows per lineage.
- [~] T7 -- Delivery and close-out. **Pending CI**: ticked only as far as this
  repository can record. PR `integration/command-center` -> `main` (base must be
  `main` so CI runs); commit identities and gate evidence are below. The CI
  result and PR number live in the PR description, because writing them here
  would need a commit after the push and re-trigger CI. This marker is therefore
  permanent in the repository; the operator may resolve it in a later, unrelated
  docs change. The Engram mirror is optional and operator-side (engram-optional
  decision 5), not a delivery requirement. Worktree removal is post-merge,
  operator-side. Commit, push, PR and merge stay the operator's decision.
  - **Delivery decisions:** strategy `exception-ok` -- one PR carrying an
    accepted `size:exception` (about 11.6k authored lines against the ~400-line
    budget), merged with a true merge commit; squash and rebase-merge are both
    forbidden because they rewrite the SHAs this document records. One slicing
    pass was considered and rejected: each slice's tree differs from the one the
    gate and Judgment Day reviewed. Rollback scope: revert the merge commit.
  - **`origin/main` moved** from `a67d616` to `52583d7` (novelty-screener,
    sota-grapher, sota-graph) between the verdict and delivery. It was merged in
    as `8b51aaf`, cleanly. The gate on that tree showed 11 failures, 8 of them
    inherited from `main`'s own commit (roster not updated for `sota-graph`; the
    word `ceiling` in the new skill trips the forge vocabulary guard) and 3
    wiring-smoke timeouts that pass in isolation in 34s. Fixed in `84a3d5c` and
    `febfc83`; the timeouts are not root-caused.

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

- Gate evidence: `npm run test:all` -> exit 0, 5355 passed, 8 skipped, zero
  failures, 14m59s (T5), and the differential control identical under an empty
  and a decoy home, 24m57s (T6), both on the pre-merge tree. After merging
  `main` (`8b51aaf`): full pytest 5400 passed / 11 failed, 8 inherited and fixed
  (see T7); the 112 tests touching the new content pass. S2 needs no fresh full
  gate: its delta is covered by `tests/test_version_sources.py` (6 passed),
  `npm ci --dry-run` (up to date) and the PR's CI.
- Judgment Day verdict: `JUDGMENT: APPROVED` on the combined tree, bound to
  `a162749` (T6). The delivery plan for this PR was separately judged
  `APPROVED` after two fix rounds.
- Commit identities: `a162749` (verdict binding), `ace28d2` (verdict record),
  `8b51aaf` (merge of `origin/main`), `84a3d5c` (generators roster), `febfc83`
  (sota-graph wording), `90f58e4` (0.6.0 changelog and lockfile root version).
  The close-out commit that records these cannot name its own SHA.

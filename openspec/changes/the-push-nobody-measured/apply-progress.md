# Apply Progress: the-push-nobody-measured

Mode: **Strict TDD** (`openspec/config.yaml` sets `strict_tdd: true`). RED before GREEN for
every lock; mutations chosen per `design.md`'s Testing Strategy table, each proven reachable-red
before the corresponding production line existed.

## Phase 0 — Correction (0.1-0.6): DONE

Amended both `spec.md` and `design.md` to carry the operator's post-design ruling: the measured
clause states an **exact count relative to the cache** ("the pin is N commits beyond the last
state this clone recorded for `<remote>`"), never "at least N" (floor) and never "no more than N
to push" (ceiling). Swept every location in both files, including three spots not explicitly
enumerated in the task list (`design.md`'s Decision 1 rationale, the zero-case template
rationale, and the File Changes table row) that would otherwise have left the documents
internally contradictory.

## Phase 1 — Timeout Budget Measurement (1.1-1.2): DONE

**1.1 — measurement, taken for real on the apply machine.**

- Machine: macOS 26.5.2 (Darwin 25.5.0, arm64).
- Repositories measured: this repository (`papersmith-ai`, 1,131 commits at measurement time)
  and the largest other git repository already on this disk (`AgentPt`, 48 commits; the other
  two candidates on disk, `Teoria-Aprendizaje-de-Maquina` at 9 commits and `cobro-unal` at 6,
  were smaller).
- Method: one warm-up run per call (discarded), then five consecutive timed runs per call, using
  `time.perf_counter()` around a real `subprocess.run` (wall-clock `real` time from the shell's
  own `/usr/bin/time -p` was too coarse at this scale — it rounded every sample to `0.00s` — so
  the measurement switched to Python's `perf_counter()`, millisecond precision).
- Raw results (milliseconds, five samples each):

  | Repository (commits) | Call | min (ms) | max (ms) | samples (ms) |
  |---|---|---|---|---|
  | papersmith-ai (1,131) | `git config --local --get-regexp '^remote\..*\.url$'` | 4.600 | 4.745 | [4.745, 4.651, 4.600, 4.672, 4.606] |
  | papersmith-ai (1,131) | `git rev-parse --verify --quiet refs/remotes/origin/main^{commit}` | 5.478 | 6.198 | [6.198, 6.180, 5.576, 5.548, 5.478] |
  | papersmith-ai (1,131) | `git rev-list --count refs/remotes/origin/main..HEAD --` | 5.553 | 5.687 | [5.571, 5.555, 5.553, 5.687, 5.587] |
  | AgentPt (48) | `git config --local --get-regexp '^remote\..*\.url$'` | 4.505 | 4.662 | [4.662, 4.505, 4.598, 4.660, 4.565] |
  | AgentPt (48) | `git rev-parse --verify --quiet refs/remotes/origin/main^{commit}` | 5.117 | 5.401 | [5.150, 5.147, 5.117, 5.401, 5.203] |
  | AgentPt (48) | `git rev-list --count refs/remotes/origin/main..HEAD --` | 5.314 | 5.453 | [5.315, 5.335, 5.314, 5.348, 5.453] |

- **Max across every call and both repositories: 6.198ms** (`git rev-parse --verify --quiet`,
  this repository).

**1.2 — derived constant.**

`PIN_WEIGHT_TIMEOUT_SECONDS = 5.0` (seconds). Multiple: `5.0s / 0.0062s ≈ 806x` the observed
worst case — deliberately far wider than `PIN_PUBLISHED_TIMEOUT_SECONDS`'s ~1.15x its own
measured worst case, per Decision 5's rule, because this budget cannot fully sample history size
on a machine that is not this one, and undershooting produces only `unmeasurable` (a first-class,
documented outcome), never a wrong verdict — the opposite failure mode `PIN_PUBLISHED_TIMEOUT_SECONDS`
guards against. Small round number, seconds not minutes, unambiguously below
`GIT_TIMEOUT_SECONDS` (120.0). Wall-clock worst case for the reader is three times this constant
(15.0s), one `_run_git()` timeout per call, three calls — stated in the constant's own comment at
`jobfolder.py` (immediately below `PIN_PUBLISHED_TIMEOUT_SECONDS`).

Cross-referenced from `PIN_WEIGHT_TIMEOUT_SECONDS`'s own comment in
`skills/remote-execution/scripts/jobfolder.py`, and from `design.md`'s Open Questions (closed).

## Phase 2 — RED: Anchor Resolution and Weight-Reader Tests (2.1-2.11): DONE

All 11 tests added to `tests/test_remote_execution.py`, confirmed reachable-red (failing with
`AttributeError: ... has no attribute '_unpushed_weight_from_cache'` / `no attribute
'PIN_WEIGHT_TIMEOUT_SECONDS'` / `TypeError: ... unexpected keyword argument 'target'`) before any
Phase 3/5 production code existed.

## Phase 3 — GREEN: Weight Reader Implementation (3.1-3.4): DONE

`PIN_WEIGHT_TIMEOUT_SECONDS`, `_CachedWeight`, `_WEIGHT_UNMEASURABLE_REASONS`, and
`_unpushed_weight_from_cache()` added to `jobfolder.py`, immediately above
`_verify_commit_reachable`, per Decisions 1-3 and 6's reason table.

**One implementation correction found only by running real git, not by design review:**
`git config --get-regexp` and `git config --get` share the same exit-code convention — a
non-zero exit (1) with **empty** output signals "no key matches the pattern", not a failure. A
naive single `try/except` reading (as Decision 3's docstring literally describes: one try/except
around the whole body, defaulting every failure to `anchor-unreadable`) would misclassify "zero
remotes configured" as `anchor-unreadable` instead of the semantically correct
`no-exact-url-match`, since `_run_git()` raises `JobFolderError` on any non-zero exit
unconditionally. Fixed by wrapping only the `config` call in its own inner `try/except
JobFolderError: listed = ""`, so "no matching key" degrades to an empty match list (handled by
the existing "zero matches → `no-exact-url-match`" branch) rather than the generic
`anchor-unreadable` fallback. Verified against real git (exit 1, empty stdout and stderr) before
writing the fix, not assumed.

## Phase 4 — RED: Signature Threading, Message Composition, Integration (4.1-4.5): DONE

All 5 tests added (one in `PinPublishedTimeoutBudgetTests`, one regression lock in
`PinConditionDoctrineTests`, three in `PublishedPinResolutionTests`), confirmed reachable-red.

## Phase 5 — GREEN: Signature Threading and Message Composition (5.1-5.4): DONE

- `_verify_commit_reachable` gained `target: str | Path | None = None`, keyword-only.
- `_refuse_unpublished_pin` stopped discarding `target` into `**_unused`; threads it through.
- The catch-all branch (`except (JobFolderError, OSError)`) now extracts `base` as a name, calls
  `_unpushed_weight_from_cache(target, commit, repo_url, repo_ref)`, and branches on
  `weight.measured` (never `weight.commits`) between the two message shapes. `remedy` and
  `unauthenticated` keep their pre-change literals byte-for-byte; the weight/reason clause is
  appended strictly after `remedy`, never spliced ahead of or interleaved within it.
- 5.4 verification: 2.1-2.11 and 4.1-4.5 all green; full `tests/test_remote_execution.py` run
  (790 tests) shows zero regressions.

**Two implementation-only corrections found only by running real git fixtures, neither a
deviation from `design.md`'s architecture:**

1. `CommitReachabilityTests._real_repositories()`'s `origin`/`target` pair uses whatever branch
   `git init`'s `init.defaultBranch` resolves to on this machine (`master` here, not `main` —
   this repository's global git config sets no override). Two of the new reader-only tests
   originally hardcoded `repo_ref="main"`, which does not exist as a remote-tracking ref for that
   fixture; fixed by resolving the fixture's actual branch name via `git symbolic-ref --short
   HEAD` instead of assuming a name. `PublishedPinResolutionTests`'s own fixture is unaffected —
   it pushes with an explicit `HEAD:refs/heads/main` refspec regardless of the local default
   branch.
2. `git status --porcelain` rewrites `.git/index` to refresh its own "racily clean" cached stat
   entries on a repository whose files were all touched within the same wall-clock second (which
   every fixture in this suite is) — every call, not just the first. A test asserting
   `.git/index`'s mtime is unchanged by the reader must not sandwich the reader between two
   `status` calls measured naively; the fix reads the "before" mtime immediately AFTER a `status`
   call (not before it) and takes the "after" mtime immediately after the reader runs, with no
   intervening `status` call. Verified stable across repeated runs before trusting it.

## Phase 6 — Documentation: SKILL.md (6.1-6.2): DONE

Added a new paragraph plus a two-item list to the reachability-probe section (after the existing
refusal paragraph at the pre-change `:858-863`, before the timeout paragraph at the pre-change
`:865-871`), describing both refusal shapes and stating plainly that the count is exact about the
local cache from the last fetch, making no claim about the remote's state now. Refers to the
condition only by context already established earlier in that section (the section header already
names `` `pin-published` ``); introduces no new ordinal or count language anywhere.
`PinConditionDoctrineTests` and `PinConditionOrdinalGuardTests` (10 tests) pass against the
updated file.

## Phase 7 — Full Verification (7.1-7.5): DONE

- **7.1** `.micromamba/envs/papersmith/bin/python -m pytest tests/test_remote_execution.py`:
  **790 passed, 10 warnings, 76 subtests passed** (0 failed). All 18 new locks green;
  `tests:12124`/`tests:19626`'s existing assertions pass unedited.
- **7.2** `npm run test:all` (both suites — `node:test` and pytest): see `## Full Suite Result`
  below.
- **7.3** `except GitTimeoutError` branch (`jobfolder.py`) diffed byte-for-byte against
  `git show HEAD:...` — **identical**, confirmed programmatically (`before == after`), not by
  eye.
- **7.4** `PIN_CONDITIONS` diffed byte-for-byte against `git show HEAD:...` — **identical**.
- **7.5** `ruff check .`: ruff was not installed (`openspec/config.yaml` already noted
  "binary not installed"); installed via `brew install ruff` (0.16.9) to actually run the check
  rather than skip it. Repository-wide: 150 pre-existing findings, unrelated to this change.
  Scoped to the touched files: `ruff check skills/remote-execution/scripts/jobfolder.py` —
  **all checks passed, zero findings**. `ruff check tests/test_remote_execution.py` — 4 findings,
  and all 4 are byte-identical (same line numbers, same rule) to the findings on the pre-change
  baseline (`git show HEAD:tests/test_remote_execution.py`), confirmed by running ruff against
  both and diffing — **zero new findings introduced** by this change.

## Full Suite Result

`npm run test:all`: **exit code 0**. `node:test`: 653 passed, 0 failed (unchanged from the
baseline — this change touches no Node-side code). `pytest`: **5,181 passed, 4 skipped, 0
failed** in 764.40s — the baseline (5,163 passed / 4 skipped / 0 failed) plus exactly the 18 new
locks this change adds, zero regressions. Neither suite was skipped.

## Phase 8 — Record-Keeping (8.1-8.3): DONE

- **8.1** `design.md`'s Open Questions: both items marked `[x]` CLOSED — the anchor-direction
  question (Phase 0, operator ruling) and `PIN_WEIGHT_TIMEOUT_SECONDS`'s value (this phase,
  measured above).
- **8.2** This document.
- **8.3** See `## Success Criteria Check` below.

## Success Criteria Check (against `proposal.md` lines ~226-237)

- [x] When the weight is measurable, the `pin-published` refusal states it **and** names the
      remedy — observed via `PublishedPinResolutionTests.test_measured_shape_names_the_exact_cache_relative_count_and_keeps_the_remedy`.
      Note: the proposal's own wording here still says "as a floor" — superseded by the
      operator's post-proposal ruling (same ruling that amended `spec.md`/`design.md` in Phase
      0); the actually-implemented and actually-specified behavior states an exact cache-relative
      count, not a floor. Not amended in `proposal.md` itself, since Phase 0's task list scoped
      the correction to `spec.md` and `design.md` only.
- [x] When not, the refusal states what is known and prescribes nothing — asserted against a
      repository with no matching remote (`test_no_configured_remote_is_unmeasurable_no_remedy`,
      and the near-miss/ambiguous/no-tracking-ref variants).
- [x] The `GitTimeoutError` refusal still names no remedy and is byte-unchanged — confirmed both
      by a dedicated lock (`test_the_weight_reader_is_never_called_on_the_timeout_branch`) and by
      a byte-for-byte diff against the pre-change file (7.3).
- [x] The weight reader makes no network call and transfers no bytes — asserted, not assumed
      (`test_the_reader_opens_no_network_connection_and_moves_no_bytes`: argv allowlist plus a
      `.git/objects` and `FETCH_HEAD` census).
- [x] The weight read has its own module constant, distinct from both existing timeout constants,
      with its measurement in its comment — `PIN_WEIGHT_TIMEOUT_SECONDS`, see Phase 1 above.
- [x] `PIN_CONDITIONS` is unchanged and the doctrine and ordinal guards are green — 7.4 and the
      10 `PinConditionDoctrineTests`/`PinConditionOrdinalGuardTests` passing.
- [x] `tests:12124` and `tests:19626` are green without edits — confirmed in the same full-file
      run (7.1); neither test was touched.
- [x] `npm run test:all` is green, with every new lock proven reachable-red — see `## Full Suite
      Result` above for the exact observed outcome.
- [x] `SKILL.md`'s probe section documents both shapes and says the anchor is a cache — Phase 6.

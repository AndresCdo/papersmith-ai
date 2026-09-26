# Tasks: The Product the History Never Took

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~188 (helper 25, constants 18, engine helper 22, wiring 8, docstring 5, fixture 10, tests 95, docs 5) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Ship `ignored`/`ignoredNote` on `wrote`, wired into both surfaces, with the full mutation-proof test suite and both documentation edits | PR 1 (single) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_proposal_implementation.py -k StepWriteScopeTests` | `npm run test:all` (both suites; `test:node` then `test:py`) | Revert `STEP_WROTE_IGNORED`, `WROTE_PROSE_KEYS`, `_step_wrote_ignored`, the `cmd_step` wiring, `impl_gitops.repository_ignored`, and the two doc edits — no ledger data is stranded (older events simply lack the key) |

Single slice, well under the 400-line budget. No chain decision is needed before `sdd-apply`.

---

## Phase 1: Test Fixture Infrastructure

- [x] 1.1 In `tests/test_proposal_implementation.py`, give `StepWriteScopeTests._box` (`:36235`) a keyword-only `ignore=` parameter defaulting to the current three unanchored rules (`"__pycache__/"`, `".ipynb_checkpoints/"`, `".implementation/"`), so all six existing calls stay byte-identical.
  - Acceptance: `_box`'s signature is `def _box(self, suffix, steps, *, ignore=("__pycache__/", ".ipynb_checkpoints/", ".implementation/")):` and every existing caller in the file is unchanged.
  - Check: `git diff --stat tests/test_proposal_implementation.py` shows only the `_box` signature line changed; no existing test in the class fails when run standalone.

- [x] 1.2 In the embedded `steps.py` fixture inside `StepWriteScopeTests`, add two new step functions: `delete_own` (deletes a pre-existing, mtime-zeroed file under the step's declared `Results/own` root) and `write_neighbour` (writes `Results/neighbour/b.json`, outside the declared root). Reuse the existing `write_own` step for locks that only need a fresh write.
  - Acceptance: both functions exist in the fixture's embedded `steps.py` string/module, alongside the pre-existing `write_own`, and neither is wired into any `__steps__` declaration used by an existing (pre-this-change) test.
  - Check: a standalone smoke run of the fixture (e.g. instantiate `_box` with each new step and inspect the on-disk result) shows `delete_own` removes the pre-created file and `write_neighbour` creates `Results/neighbour/b.json`.

---

## Phase 2: RED — Failing Tests for Every Lock

Every task in this phase MUST be run and observed failing (for the right reason — missing attribute/key, not a typo) before Phase 3 begins. Purge `__pycache__` and set `PYTHONDONTWRITEBYTECODE=1` before each RED run (`find . -name __pycache__ -type d -exec rm -rf {} +`).

- [x] 2.1 **[Lock 1 — path base is repository-relative]** Add a test to `StepWriteScopeTests` using `_box(ignore=(..., "/Method/Results/own/"))` (product-anchored rule) with step `write_own`. Assert `wrote["ignored"] == ["Results/own/a.json"]` **and** `wrote["status"] == "own"` (proves the parallel field, not a fifth status). This is spec scenario "A real written path under a content-only ignore rule is caught" and "A product-anchored ignore rule matches the joined path".
  - Acceptance: test fails RED with `KeyError: 'ignored'` (the field does not exist yet).
  - Check: run `.micromamba/envs/papersmith/bin/python -m pytest tests/test_proposal_implementation.py -k <new_test_name> -v`; observe the exact failure reason, not just non-zero exit.

- [x] 2.2 **[Lock 2 — non-zero exit means nothing ignored]** Add a test using the default `_box` ignore set with step `write_own` over the tracked `a.json`. Assert `proc.returncode == 0`, `wrote["ignored"] == []`, `wrote["status"] == "own"`, and `assertNotIn("ignoredNote", wrote)`. This is the only row that exercises `check-ignore` exit 1 (clean, tracked write) and satisfies spec requirement "A Clean, Tracked Write Reports An Empty Result And Never Raises".
  - Acceptance: test fails RED with `KeyError: 'ignored'`.
  - Check: same pytest invocation pattern as 2.1.

- [x] 2.3 **[Lock 3 — the check exists at all]** No new test — this lock is proven by 2.1 and 2.2 together (an empty field and an absent field are both falsy to a weak assertion; only the pair distinguishes them). Confirm in review that 2.2 asserts presence-and-equal-to-`[]`, never mere absence.
  - Acceptance: 2.2's assertion reads `self.assertIn("ignored", wrote)` (or equivalent) plus `self.assertEqual(wrote["ignored"], [])`, not only `assertFalse(wrote.get("ignored"))`.
  - Check: read the assertion text directly; no separate run needed.

- [x] 2.4 **[Lock 4 — the reading is durable]** Add a test reusing 2.1's fixture; read `Method/.implementation/position.jsonl` after the run, take the terminal event, and assert `terminal["wrote"]["ignored"] == ["Results/own/a.json"]` and `assertNotIn("ignoredNote", terminal["wrote"])`. Mirrors `test_the_reading_is_written_into_the_terminal_ledger_event` (`:36338-36351`).
  - Acceptance: test fails RED with `KeyError: 'ignored'` when reading the terminal event's `wrote` block.
  - Check: run the new test in isolation; confirm the ledger file path and JSON-lines parsing match the existing helper pattern in the class.

- [x] 2.5 **[Lock 5 — the consequence prose is real]** Add a test reusing 2.1's fixture; assert `wrote["ignoredNote"] == impl.STEP_WROTE_IGNORED` by identity against the module constant (mirrors `test_a_step_declaring_no_roots_is_graded_against_nothing` at `:36336`, which does the same against `impl.PRODUCES_UNDECLARED_CONSEQUENCE`).
  - Acceptance: test fails RED with `AttributeError: module 'impl' has no attribute 'STEP_WROTE_IGNORED'`.
  - Check: run in isolation; confirm the failure is the missing attribute, not a missing key.

- [x] 2.6 **[Lock 6 — removals are checked, not dropped]** Add a test using step `delete_own` (from Task 1.2) with `_box(ignore=(..., "/Method/Results/own/"))` so the pre-created file is both ignored and untracked, then deleted by the step. Assert `wrote["ignored"] == ["Results/own/old.json"]` (or the fixture's chosen filename) even though the file no longer exists on disk. Satisfies spec requirement "Removed Paths Are Included, Not Only Added Or Modified Paths".
  - Acceptance: test fails RED with `KeyError: 'ignored'`.
  - Check: confirm via `git status`/disk inspection inside the test that the file is genuinely absent when the assertion runs, so the lock proves what it claims.

- [x] 2.7 **[Lock 7 — scope is `inside` only]** Add a test using step `write_neighbour` (from Task 1.2) with `_box(ignore=(..., "/Method/Results/neighbour/"))`. Assert `status == "foreign"`, `outside == ["Results/neighbour/b.json"]`, and `ignored == []` — proving the check never evaluates `wrote.outside`. Satisfies spec requirement "Scope Is Limited To A Step's Own Declared-And-Written Paths (`inside`)".
  - Acceptance: test fails RED with `KeyError: 'ignored'` (the field must exist and be empty, not merely absent, for this to be a real lock).
  - Check: run in isolation; confirm `status`/`outside` already read correctly today (pre-existing behavior) and only `ignored` is new.

- [x] 2.8 **[Lock 8 — the prose borrows no target vocabulary]** Add a unit test (no fixture needed): `assertEqual(leaks_in(impl.STEP_WROTE_IGNORED), [])`, following the measured precedent at `:36705-36717`.
  - Acceptance: test fails RED with `AttributeError: module 'impl' has no attribute 'STEP_WROTE_IGNORED'`.
  - Check: run in isolation.

- [x] 2.9 Run the full new-test set together (`pytest tests/test_proposal_implementation.py -k StepWriteScopeTests`) and confirm every new test from 2.1–2.8 fails, and every pre-existing test in the class still passes.
  - Acceptance: pytest output shows N new failures (expected) and 0 regressions among pre-existing `StepWriteScopeTests` tests.
  - Check: capture and read the actual pytest summary line, not `git diff --stat`.

---

## Phase 3: GREEN — Implement the Capability

- [x] 3.1 In `skills/_core/implementation/impl_gitops.py`, add `repository_ignored(target: Path, paths: list[str]) -> set[str]`, placed after `present_files` (`:23-50`) and before `text_files` (`:53`). One `subprocess.run(["git", "check-ignore", "--stdin", "-z"], cwd=target, ..., check=False)`, stdin fed the joined paths NUL-separated, stdout parsed unconditionally regardless of return code (0 → matched paths; 1/128 → empty; catch `OSError` → empty). Never routes through `impl_gitops.git()`. Docstring per design's Interfaces/Contracts block, explaining the non-zero-exit reading and that an empty `paths` spawns nothing.
  - Acceptance: matches Decision D2/D3's signature, argument order (`target` first, matching every other function in this module), and exit-code contract table exactly. `check=False` is written explicitly.
  - Check: unit-exercise the function directly against a scratch git repo with a mix of ignored/tracked/nonexistent paths (can be done ad hoc before the fixture tests run it indirectly).

- [x] 3.2 In `skills/_core/implementation/engine/implementation_engine.py`, add `STEP_WROTE_IGNORED` as a module-level constant beside `STEP_WROTE_OWN` (`:10674`), `STEP_WROTE_NOTHING` (`:10682`), `STEP_WROTE_FOREIGN` (`:10689-10695`). Register matches `STEP_WROTE_FOREIGN`: state the defect, that it is found only by hand, name both explanations (rule reaches too far / product belongs somewhere the repository keeps), and say the reading never repairs it. Draft text is in design D5; finish wording here.
  - Acceptance: the constant's text contains **zero** case-insensitive occurrences of the word "proposal" (Constraint 1, `test_implementation_domain_lock.py:833-894`, `L1_EXPECTED_COUNT`), and borrows no target-module vocabulary (Constraint 2, verified by Task 2.8/3.7).
  - Check: `python -c "import re; print(len(re.findall(r'\bproposal\b', open('skills/_core/implementation/engine/implementation_engine.py').read(), re.IGNORECASE)))"` must print the same count as before this task (do not increment it).

- [x] 3.3 In the same file, add `WROTE_PROSE_KEYS = ("note", "ignoredNote")` as a named tuple constant near `STEP_WROTE_IGNORED`.
  - Acceptance: the tuple is a literal roster (not a `key.endswith("Note")` suffix test — design explicitly refuses that shape).
  - Check: read the diff; confirm no string-suffix comparison was introduced anywhere in the wiring.

- [x] 3.4 Add module-level helper `_step_wrote_ignored(target: Path, name: str, inside: list[str]) -> list[str]` beside `_step_wrote` (`:10719`). Short-circuits to `[]` when `inside == []` (no subprocess). Otherwise joins `f"{name}/{path}"` for each entry (literal `"/"`, never `Path(name) / path`), calls `impl_gitops.repository_ignored(target, joined)`, and maps the answer back to `inside`'s original product-relative spelling and order (membership-based mapping, not string-stripping). Import `repository_ignored` at the top of the file (near `:61`). Also amend `_step_wrote`'s own docstring with a sentence naming `ignored`, saying it is joined on by `cmd_step`, and saying why it is not computed inside `_step_wrote` itself (paid cost of Decision D1).
  - Acceptance: `_step_wrote`'s signature and body are otherwise byte-identical (stays pure — no `target`/`name` params added to it). `_step_wrote_ignored` performs no filesystem existence check anywhere (Decision D6).
  - Check: `rg '_step_wrote\(' skills/_core/implementation/engine/implementation_engine.py` still shows exactly one call site (`cmd_step`); `rg 'Path\(name\)' skills/_core/implementation/engine/implementation_engine.py` returns nothing for this new code.

- [x] 3.5 In `cmd_step`, between `:16809` and `:16811` (immediately after the existing `_step_wrote(...)` call at `:16808`), call `_step_wrote_ignored(target, name, wrote["inside"])` and fold the result into the local `wrote` dict as `wrote["ignored"]` (always present, `[]` when clean) and `wrote["ignoredNote"] = STEP_WROTE_IGNORED` (only when `ignored` is non-empty — do not set the key at all otherwise).
  - Acceptance: both the ledger event build (`:16811-16822`) and the return dict build (`:16825-16834`) read from this same local `wrote`, so one assignment reaches both surfaces without touching either dict-construction site directly.
  - Check: re-read `cmd_step`'s body after the edit; confirm `ignored`/`ignoredNote` are set exactly once, before either dict is constructed.

- [x] 3.6 Change the ledger-event strip at `:16821` from `if key != "note"` to `if key not in WROTE_PROSE_KEYS`.
  - Acceptance: the existing assertion `assertNotIn("note", terminal["wrote"])` (`:36350-36351`) still passes unmodified; `ignoredNote` is now also stripped from the ledger event whenever it is present.
  - Check: covered by Task 2.4's assertion (`assertNotIn("ignoredNote", terminal["wrote"])`) turning GREEN.

- [x] 3.7 Re-run Task 2.8's `leaks_in(impl.STEP_WROTE_IGNORED)` check against the final constant text from Task 3.2, and adjust wording if it fails, before moving on.
  - Acceptance: `leaks_in(impl.STEP_WROTE_IGNORED) == []`.
  - Check: `pytest tests/test_proposal_implementation.py -k <lock_8_test_name> -v` passes.

- [x] 3.8 Purge `__pycache__` (`find . -name __pycache__ -type d -exec rm -rf {} +`), then run every test added in Phase 2 and confirm all turn GREEN, with zero regressions in pre-existing `StepWriteScopeTests` tests.
  - Acceptance: `pytest tests/test_proposal_implementation.py -k StepWriteScopeTests` reports 0 failures.
  - Check: capture the actual pytest summary; do not infer pass/fail from `git diff --stat`.

---

## Phase 4: Mutation Verification — Prove Each Lock Survives Its Named Mutation

For every sub-task below: apply the exact named mutation, purge `__pycache__`, run the associated test and confirm it now FAILS, then revert the mutation, purge `__pycache__` again, and confirm the test PASSES again. `git diff --stat` does not prove a mutation landed — read the actual diff or grep the anchor before trusting the run.

- [x] 4.1 **[Lock 1]** Delete the `f"{name}/"` join in `_step_wrote_ignored` (pass `path` unjoined to `repository_ignored`). Confirm Task 2.1's test now fails (its fixture rule is anchored `/Method/Results/own/`, which cannot match the unjoined `Results/own/a.json`). Revert.
  - Acceptance: test fails with the mutation in place, passes after revert.
  - Check: `grep -n 'f"{name}/' skills/_core/implementation/engine/implementation_engine.py` confirms the join line exists after revert.

- [x] 4.2 **[Lock 2]** Flip `check=False` to `check=True` in `impl_gitops.repository_ignored` (or route through `impl_gitops.git()`). Confirm Task 2.2's test now fails/raises on the clean, tracked-write case (exit 1). Revert.
  - Acceptance: mutation raises `CalledProcessError` or `Refused("GIT_FAILED")` where the test expects a clean `[]`; reverted code passes again.
  - Check: read the exception type/message during the mutated run to confirm it is the exit-code branch failing, not an unrelated error.

- [x] 4.3 **[Lock 3]** Comment out the call to `_step_wrote_ignored` in `cmd_step` entirely (field never set). Confirm this is caught by Task 2.1/2.2 (both fail with `KeyError: 'ignored'`), proving neither row alone would be a sufficient lock without the other. Revert.
  - Acceptance: both tests fail with the call removed; both pass after revert.
  - Check: same pytest invocation as 2.1/2.2.

- [x] 4.4 **[Lock 4, mutation A]** Move the `wrote["ignored"] = ...` assignment to after the event dict is built (`:16822`), so it only reaches the return, never the ledger. Confirm Task 2.4's test now fails (ledger event lacks `ignored`) while Task 2.1's test (return value) still passes. Revert.
  - Acceptance: 2.4 fails, 2.1 passes, under the mutation; both pass after revert.
  - Check: read the terminal ledger event JSON directly during the mutated run.

- [x] 4.5 **[Lock 4, mutation B]** Revert Task 3.6's strip change back to `if key != "note"` (leaving `ignoredNote` prose in the ledger). Confirm Task 2.4's `assertNotIn("ignoredNote", terminal["wrote"])` now fails. Revert the mutation (restore `WROTE_PROSE_KEYS`).
  - Acceptance: test fails under the mutation, passes after revert.
  - Check: read the terminal ledger event JSON directly during the mutated run; confirm `ignoredNote` is literally present.

- [x] 4.6 **[Lock 5]** Replace `STEP_WROTE_IGNORED`'s text with `""`. Confirm Task 2.5's identity assertion still technically "passes" only if it asserts identity — reconfirm the test is written as `assertEqual(wrote["ignoredNote"], impl.STEP_WROTE_IGNORED)`, which trivially holds even at `""`. This row's real assurance is that no test in this suite asserts a *non-empty* string; the identity assertion protects against drift between the field and the constant, not against an empty constant. State this explicitly in the test's docstring/comment. Revert the constant text to its real prose.
  - Acceptance: the identity assertion is present and the constant's final text is non-empty, doctrine-bearing prose (Task 3.2's output), not the mutated empty string.
  - Check: read `impl.STEP_WROTE_IGNORED` after revert; confirm it is the full drafted sentence, not `""`.

- [x] 4.7 **[Lock 6]** Add an existence guard to `_step_wrote_ignored` (e.g. `if (target / name / p).exists()`) before including a path in the query. Confirm Task 2.6's test (deleted file) now fails because the guard silently drops it. Revert.
  - Acceptance: test fails under the mutation, passes after revert.
  - Check: confirm the guard is fully removed after revert — `grep -n '\.exists()' skills/_core/implementation/engine/implementation_engine.py` shows no match introduced by this change.

- [x] 4.8 **[Lock 7]** Change `_step_wrote_ignored`'s call site to pass `changed` (the full changed-paths list) instead of `wrote["inside"]`. Confirm Task 2.7's test now fails or misbehaves once a foreign write is evaluated (or, at minimum, that scope has silently widened — assert the test still distinguishes `inside`-only scope before and after). Revert.
  - Acceptance: mutation changes what Task 2.7 observes (foreign path evaluated); reverted code restores `inside`-only scope.
  - Check: re-read `cmd_step`'s call to `_step_wrote_ignored` after revert — confirm it passes `wrote["inside"]` literally.

- [x] 4.9 Purge `__pycache__` one final time, run the entire `StepWriteScopeTests` class end to end, and confirm all tests (Phase 2's new ones and every pre-existing test) are GREEN with no mutations left in place.
  - Acceptance: `pytest tests/test_proposal_implementation.py -k StepWriteScopeTests` reports 0 failures.
  - Check: capture and read the actual pytest summary output.

---

## Phase 5: Documentation

- [x] 5.1 Update `skills/proposal-implementation/SKILL.md:3014`'s `step` row: the `wrote` sub-key enumeration gains `ignored` and `ignoredNote`, states that `ignored` is computed over `inside` only, and states that the ledger event carries the paths without the prose.
  - Acceptance: the row reads all of `status`, `declared`, `inside`, `outside`, `ignored`, `note`, and (conditionally) `ignoredNote` — matching the spec requirement "The Documented Sub-Key Enumeration Names The New Field".
  - Check: manual read-back of the updated row against the spec scenario "The documented enumeration lists the new field". No derived guard checks this — it is a task, never a test (Decision D7).

- [x] 5.2 Update `skills/proposal-implementation/references/usage.md:2275-2290`'s `wrote` narrative paragraph with the same fact in its own register — including that the reading is written into the terminal ledger event without the prose sentence.
  - Acceptance: a reader of `usage.md` alone, without consulting `SKILL.md`, learns that `ignored`/`ignoredNote` exist, what they mean, and that the ledger drops the prose.
  - Check: manual read-back; confirm this edit did not stop at `SKILL.md` alone (the repository has already measured that failure shape once — `the-correction-reached-skillmd-and-stopped`).

---

## Phase 6: Empirical Confirmation and Final Verification

- [ ] 6.1 Empirically confirm Decision D3's stated-but-unverified claim: that `git check-ignore`'s default (index-consulting) behavior reports an already-**tracked** path as not-ignored even when a rule matches it. Use the existing fixture machinery (a tracked file, plus a rule that would match it if untracked) in a scratch scenario, not by inspecting git's source or documentation alone.
  - Acceptance: the observed behavior is recorded (in a code comment near `repository_ignored`'s docstring, or in this task's completion note) as either confirming or contradicting D3's stated rationale for omitting `--no-index`. If it contradicts, correct D3's rationale in `impl_gitops.py`'s docstring in place — do not leave it as an unverified claim.
  - Check: the empirical test's exact command and observed exit code / stdout are recorded, not merely "should be fine".

- [ ] 6.2 Run the domain word-count lock explicitly: `pytest tests/test_implementation_domain_lock.py`.
  - Acceptance: the suite is green, and specifically `test_l1_residue_pin_equals_the_measured_s0_baseline_minus_its_one_recorded_shrink` (`:833-894`) passes with `L1_EXPECTED_COUNT` unchanged.
  - Check: read the actual pytest output; a green run here is the only proof that Task 3.2's constant introduced zero new occurrences of "proposal".

- [ ] 6.3 Run the full project suite: `npm run test:all` (runs `test:node` then `test:py` — both, never one alone; this repository has previously hidden a regression by running only one).
  - Acceptance: both suites report 0 failures.
  - Check: read the actual combined output; do not infer success from partial output or from Phase 3/4's targeted pytest runs alone.

- [ ] 6.4 Final read-back: confirm every Success Criterion in `proposal.md` is satisfied by the landed diff (status still `"own"`, empty-and-not-absent on clean writes, ledger durability, product-anchored fixture proof, identity-asserted constant, `SKILL.md:3014` updated, RED-before-GREEN discipline observed, `npm run test:all` green).
  - Acceptance: each checkbox in `proposal.md`'s "Success Criteria" section can be marked true against a concrete task above.
  - Check: cross-reference this file's completed tasks against `proposal.md`'s list; no criterion is left unmapped.

---

## Notes for `sdd-apply`

- Every line number cited above was re-verified against disk on 2026-09-26 by `sdd-design`; re-verify again before editing, since this engine's line numbers have moved between phases before (design's own "Citations re-verified" section documents two corrections it made to the inherited proposal).
- `tests/forge_vocabulary.py` is referenced for its shape only (`repository_ignored:220-250`) and MUST NOT be imported from `skills/_core/`; no task above edits it.
- `implementations/**` is out of scope and read-only for this change; no task above touches it.
- Guards that MUST stay untripped throughout: `KitDemandsEveryStepKeyTests` (`:37116-37144`), `VerifyStatusRosterTests` (`:16479-16487`), `test_the_returned_response_dict_never_gains_suite_digest` (`:30172-30173`), and the `own` assertions (`:36303-36308`). None of the tasks above add a top-level key to `cmd_step`'s return, add a new `verify` status, or touch `cmd_verify`/`STEP_KEYS`, so none of these guards should fire; if one does, stop and re-read the relevant design decision before proceeding.

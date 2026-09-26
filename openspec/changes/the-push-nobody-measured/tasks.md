# Tasks: the-push-nobody-measured

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~220-325 (proposal's own ~40-60 `jobfolder.py` + ~10-20 `SKILL.md` + ~120-200 tests, plus ~15-25 for the Phase 0 spec/design correction) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

Chaining is not needed: the proposal's own measured estimate lands well under the 400-line
guard as a single slice, and nothing in this task list changes that (Phase 0's spec/design
correction is prose-only, no code). `Chain strategy: pending` because no chain was requested,
not because a chain choice is outstanding.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | The whole change: corrected spec/design wording, the measured timeout budget, the local weight reader, signature threading, message composition, `SKILL.md` docs, full verification | PR 1 (only PR) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_remote_execution.py` | `npm run test:all` (both suites; this repository has two and running one has hidden a regression before) | One commit against `main`, reverting independently — nothing is written to disk by this change, and the refusal's firing conditions never move, so reverting restores the unconditional remedy sentence exactly as it stood before |

### Parallelization Notes

- **Phase 0** (0.1–0.6) is prose-only and can be split across files in parallel (spec.md vs
  design.md edits touch different files), but **all of it must land before any Phase 2/4 RED
  test is written**, because those tests assert the corrected wording.
- **Phase 1** is strictly sequential: 1.2 consumes 1.1's measured numbers. Its failure path is a
  hard stop — if 1.1 cannot be completed, do not start 1.2 or Phase 3.
- **Phase 2** (2.1–2.11) tasks are logically independent of each other (each adds one test) but
  land in the same test file, so treat them as sequential edits in practice even though none
  depends on another's assertions. All of Phase 2 precedes Phase 3 (RED before GREEN).
- **Phase 3** is sequential: 3.1 depends on Phase 1's chosen value; 3.2 and 3.3 precede 3.4; 3.4
  is verified against all of Phase 2.
- **Phase 4** (4.1–4.5) tasks are independent of each other and can be written in parallel with
  late Phase 2 work, but all of Phase 4 precedes Phase 5 (RED before GREEN, same rule as Phase 2).
- **Phase 5** is sequential: 5.1 → 5.2 → 5.3 → 5.4 (5.3 needs both signatures threaded; 5.4 is the
  regression check against Phase 2 and Phase 4).
- **Phase 6** depends only on Phase 0's corrected wording — it can run in parallel with Phases
  1–5 once Phase 0 is done.
- **Phase 7** and **Phase 8** are strictly sequential and last: they verify and record what the
  earlier phases produced.

## Phase 0: Correction — Close the Anchor-Direction Ruling

The operator ruled on design.md's open question about the direction of "at least" **after**
design.md was written. The ruling: the pin's distance is stated **exactly**, about the cache —
not "at least N" (a floor) and not "no more than N to push" (a ceiling) — because
`count(anchor..pin)` is only exact about the anchor; in the ordinary drift direction it
over-states the actual push, so neither floor nor ceiling language about the push is honest.
These edits must land before any RED test that asserts on refusal wording.

- [ ] 0.1 Amend `openspec/changes/the-push-nobody-measured/specs/remote-execution-pin-published/spec.md`'s
      requirement **"A measured weight is reported as a floor, never an exact figure"**
      (~lines 90-101). Rename it to **"A measured weight states an exact distance from the
      cache, and claims nothing about the remote now"**. Replace the MUST/scenario body so the
      refusal states the exact commit count between the cached anchor and the pinned commit,
      MUST NOT use floor language ("at least N") or ceiling language ("no more than N"), and
      MUST NOT claim or imply anything about the remote's current state. (Spec: R4)
- [ ] 0.2 Amend the same spec.md's requirement **"The stated weight is documented as a cache,
      not the remote's current state"** (~lines 135-148). Keep the cache-caveat MUST, but add:
      the wording MUST NOT imply a specific direction or magnitude of drift between the cache
      and the remote's current state, and MUST NOT license any conclusion about how much (if
      anything) remains to be pushed. Update the "SKILL.md states the cache caveat" scenario
      (~142-148) to drop "a floor derived from a local cache" in favor of "an exact count
      derived from a local cache ... and makes no claim about the remote's state now". (Spec: R6)
- [ ] 0.3 Sweep the rest of spec.md for the now-superseded floor phrasing and align it with 0.1's
      wording, so the spec does not contradict itself:
      - The shape definition under "The refusal takes exactly one of two shapes" (~55-67):
        replace "states the measured weight, as a floor, and names the existing remedy" with
        "states the measured weight, as an exact cache-relative count, and names the existing
        remedy".
      - Both magnitude scenarios (~68-82, "small number of commits/bytes" and "large number of
        commits/bytes"): replace "names the measured weight as a floor" with "names the measured
        weight as an exact cache-relative count" in both.
      - The "SKILL.md documents both refusal shapes" requirement's scenario (~246-252): replace
        "states that the measured weight is a floor" with "states that the measured weight is an
        exact count derived from the local cache, with no claim about the remote's state now".
      (Spec: R3, R13)
- [ ] 0.4 Amend `openspec/changes/the-push-nobody-measured/design.md`'s Decision 6 message-composition
      code block (~line 239). Remove `"at least"` from the measured-shape literal; keep "beyond
      the last state this clone recorded for that remote"; replace the closing caveat sentence
      ("...so the remote may hold more than it shows") with wording stating the count is exact
      about the cached record and makes no claim about the remote's state now. Suggested literal
      (apply may finalize exact phrasing, honoring 0.1/0.2's constraints):
      ```python
      f". Measured locally, no bytes moved: the pin is "
      f"{weight.commits} commit{plural} beyond the last state this "
      f"clone recorded for that remote ({weight.anchor_ref} at "
      f"{weight.anchor_commit[:12]}, from the last fetch). That count is "
      "exact about this clone's cached record and makes no claim about "
      "the remote's state now."
      ```
- [ ] 0.5 Amend design.md's "On the word 'at least'" rationale paragraph (~lines 280-284) and the
      Testing Strategy table's lock 1 description (~line 357, "names the count as a floor and
      keeps the remedy") so both describe the exact-cache-relative wording from 0.4 instead of
      floor language, keeping the table's mutation column ("emit the bare count without the
      cache-relative clause") intact.
- [ ] 0.6 Amend design.md's "Disagreements with disk" item 2 (~lines 413-420) and the first
      "Open Questions" bullet (~lines 398-402): mark the anchor-direction question **CLOSED**,
      citing the operator's ruling verbatim (cache-relative exact clause; not "at least N", not
      "no more than N to push"), replacing "Flagged, not assumed" with the resolution.

## Phase 1: Timeout Budget Measurement (Design Decision 5)

Prerequisite and blocking: no constant, no reader, no lock 8/11 test is written until this
measurement is taken. This is the task's explicit failure path, not a footnote.

- [ ] 1.1 Run Decision 5's measurement procedure on the apply machine. Five consecutive
      warm-cache timings each of: (a) `git config --local --get-regexp '^remote\..*\.url$'`,
      (b) `git rev-parse --verify --quiet refs/remotes/origin/main^{commit}`, (c)
      `git rev-list --count refs/remotes/origin/main..HEAD --`, against this repository, plus —
      only if one is already on disk — the largest other available git repository (identify it
      by `git rev-list --count HEAD`). Record OS/hardware, min/max per call, and the max across
      all three calls, in `apply-progress.md`.
      **Acceptance**: raw numbers recorded with repository identity and machine identity.
      **Failure path**: if git is unavailable on the apply machine, or the timing harness cannot
      run, STOP here. Do not proceed to 1.2, 3.1, or any test asserting on
      `PIN_WEIGHT_TIMEOUT_SECONDS`. Report `blocked` with the reason.
- [ ] 1.2 From 1.1's recorded max, choose `PIN_WEIGHT_TIMEOUT_SECONDS`'s value per Decision 5's
      multiple-and-rationale rule: a small round number, seconds not minutes, unambiguously below
      `GIT_TIMEOUT_SECONDS = 120.0` (`jobfolder.py:2175`), with a stated multiple and the reason
      the multiple must be larger than `PIN_PUBLISHED_TIMEOUT_SECONDS`'s (this constant governs a
      local walk whose cost the measurement cannot fully sample, and undershooting only produces
      `unmeasurable`, not a wrong answer). Draft the comment text, including the "wall-clock worst
      case is three times this constant" note (one `_run_git()` timeout applies per call).
      **Blocked** if 1.1 did not complete.

## Phase 2: RED — Anchor Resolution and Weight-Reader Tests

Every task below adds a failing test to `tests/test_remote_execution.py` **before** the
production code in Phase 3 exists, and each names the mutation a weaker lock would survive
(design's Testing Strategy table). All of Phase 2 precedes Phase 3.

- [ ] 2.1 [RED] Add a test that the measured shape names the count as the exact cache-relative
      distance (0.1/0.4's wording) and keeps the remedy, using
      `PublishedPinResolutionTests.published_target()` (`:19558`) +
      `.commit_local_only()` (`:19578`), remote URL passed byte-identically. Mutation to survive:
      emitting the bare count without the cache-relative clause (lock 1, updated per Phase 0).
      (Spec: R3, R4)
- [ ] 2.2 [RED] Add a test that a **measured zero** still takes the measured shape (published
      target, pin = the published tip, probe forced to fail locally). Mutation to survive:
      `if weight.commits:` in place of `if weight.measured:` — every nonzero case must survive,
      only the zero case must fail (lock 2; this is the lock that pays for Decision 3's frozen
      `_CachedWeight`). (Spec: R3, R4)
- [ ] 2.3 [RED] Add a test that no configured remote → unmeasurable, no remedy, using
      `CommitReachabilityTests._real_repositories()` (`:11720`). Mutation to survive: falling
      back to `origin` when no URL matches (lock 3). (Spec: R3, R5)
- [ ] 2.4 [RED] Add a test that a near-miss URL spelling (remote configured as `<url>.git` while
      `--repo-url` lacks the suffix) resolves to unmeasurable. Mutation to survive: normalizing
      by stripping `.git` before comparing (lock 4). (Spec: R5)
- [ ] 2.5 [RED] Add a test that two remotes sharing one byte-identical URL resolve to
      unmeasurable and name the `ambiguous-url-match` reason. Mutation to survive: taking the
      first match (lock 5). (Spec: R5, R7)
- [ ] 2.6 [RED] Add a test that every internal weight-reader failure (patched `_run_git` raising
      `OSError` for every call after `init`) degrades to the careful unmeasurable shape — never a
      crash, never a distinct refusal. Mutation to survive: letting the reader's `except`
      re-raise instead of returning unmeasurable (lock 9). (Spec: R7)
- [ ] 2.7 [RED] (Threat Matrix: Push state) Add a test that a remote with an exact-URL match but
      **no** `refs/remotes/<name>/<branch>` yet (first push, no tracking ref) resolves to
      unmeasurable with reason `anchor-unreadable`. (Spec: R5, R7)
- [ ] 2.8 [RED] (Threat Matrix: Git repository selection) Add a test that every `_run_git()` call
      the reader makes uses `cwd=target` — the already-resolved `Path` from
      `verify_pin_preconditions` (`:3069`) — never a raw `git -C` argument, and never a fallback
      to the process cwd when `target=None`. (Spec: R2)
- [ ] 2.9 [RED] Add a test that the reader opens no network connection and moves no bytes: an
      argv allowlist restricted to `{config, rev-parse, rev-list}`, plus a before/after census of
      `.git/objects` and the absence of a new `FETCH_HEAD`, using `_real_repositories()` with
      `_run_git` calls recorded. Mutation to survive: having the reader call `ls-remote` (lock 7).
      (Spec: R2)
- [ ] 2.10 [RED] (Threat Matrix: Commit state) Extend 2.9's census to assert `.git/index` mtime
      and `git status --porcelain` output are unchanged before/after the reader runs. (Spec: R2)
- [ ] 2.11 [RED] Add a test that `PIN_WEIGHT_TIMEOUT_SECONDS` is a distinct module constant from
      `GIT_TIMEOUT_SECONDS` and `PIN_PUBLISHED_TIMEOUT_SECONDS`, and that only the reader's three
      `_run_git()` calls receive it (per-call census), shaped after
      `PinPublishedTimeoutBudgetTests` (`:20492`). Mutation to survive: passing it to the local
      `init` call too (lock 8). **Blocked** if Phase 1 did not complete. (Spec: R12)

## Phase 3: GREEN — Weight Reader Implementation

- [ ] 3.1 In `skills/remote-execution/scripts/jobfolder.py`, after `PIN_PUBLISHED_TIMEOUT_SECONDS`
      (`:2212`), add `PIN_WEIGHT_TIMEOUT_SECONDS: float` with the comment drafted in 1.2. **Blocked**
      if Phase 1 did not complete. (Spec: R12)
- [ ] 3.2 In `jobfolder.py`, before `_verify_commit_reachable` (`:2332`), add the frozen
      `@dataclass class _CachedWeight` (`measured: bool`, `commits: int = 0`,
      `anchor_ref: str = ""`, `anchor_commit: str = ""`, `reason: str = ""`) exactly per design
      Decision 3, preserving the docstring's "measured zero is a real answer" argument verbatim.
      (Spec: R4)
- [ ] 3.3 In the same location, add the module-level `_WEIGHT_UNMEASURABLE_REASONS` mapping with
      the four codes `no-local-repository`, `no-exact-url-match`, `ambiguous-url-match`,
      `anchor-unreadable` and their clauses, exactly per design Decision 6's table. (Spec: R6, R7)
- [ ] 3.4 Implement `_unpushed_weight_from_cache(target, commit, repo_url, repo_ref) -> _CachedWeight`
      per design Decisions 2 and 3: `git config --local --get-regexp '^remote\..*\.url$'` →
      byte-identical URL match (0 or 2+ matches → unmeasurable) → `refs/remotes/<name>/<branch>`
      from `repo_ref` with a leading `refs/heads/` stripped (a `repo_ref` still `refs/`-prefixed
      after that removal → unmeasurable) → `git rev-parse --verify --quiet <ref>^{commit}` →
      `git rev-list --count <anchor>..<commit> --`. Every call uses `cwd=target`,
      `timeout=PIN_WEIGHT_TIMEOUT_SECONDS`, and the whole body is wrapped in one
      `try: ... except (JobFolderError, OSError): return unmeasurable(...)` so nothing escapes.
      **Verify**: run 2.1–2.11 and confirm all GREEN. (Spec: R2, R5, R7)

## Phase 4: RED — Signature Threading, Message Composition, and Integration

All of Phase 4 precedes Phase 5 (RED before GREEN).

- [ ] 4.1 [RED] Add a test that the `GitTimeoutError` refusal is byte-identical to its pre-change
      text, with `_unpushed_weight_from_cache` `Mock`-patched and asserted `not_called` when that
      branch fires. Mutation to survive: moving the reader above both branches, or wrapping both
      branches in a shared `except JobFolderError` (lock 6). (Spec: R1, R8)
- [ ] 4.2 [RED] Add an end-to-end test through `generate-job`, measured shape, real git and real
      subprocess, using `PublishedPinResolutionTests.generate()` (`:19587`), asserting the
      operator-facing stderr text matches Phase 0's corrected cache-relative wording. Mutation to
      survive: composing the message anywhere other than the one raise site inside the catch-all
      branch (lock 10). (Spec: R1, R3, R4, R9)
- [ ] 4.3 [RED] Add a test confirming `tests:12124` and `tests:19626`'s existing assertions on the
      `"could not be confirmed reachable"` prefix continue to pass **without editing those two
      tests**, exercised in the same suite run as 4.2. (Spec: R9)
- [ ] 4.4 [RED] Add a test that `PIN_CONDITIONS` (`:2607-2608`) is unchanged in membership, order,
      and length, and that `PinConditionDoctrineTests` (`:12779`) and
      `PinConditionOrdinalGuardTests` (`:12951`) — which scan `SKILL.md`, `jobfolder.py`,
      `remote_cli.py`, and the test module itself — stay green against every new sentence this
      change adds, all referring to `` `pin-published` `` by id only. (Spec: R10, R11)
- [ ] 4.5 [RED] Add a test asserting the ~18 direct `_verify_commit_reachable(...)` call sites in
      `tests/test_remote_execution.py` (`:11575, :11612, :11633, :11662, :11688, :11710, :11801,
      :11835, :12118, :12145, :20548, :20588, :20608, :23036, :23041, :23084, :23093, :23121,
      :23137, :23148, :23168`) remain unmodified and still pass: with `target` keyword-only and
      defaulted to `None`, each takes the `no-local-repository` unmeasurable path.

## Phase 5: GREEN — Signature Threading and Message Composition

- [ ] 5.1 In `jobfolder.py`, add `target: str | Path | None = None` as a keyword-only parameter to
      `_verify_commit_reachable` (`:2332`), per design Decision 4. (Spec: R2)
- [ ] 5.2 In `jobfolder.py`, stop `_refuse_unpublished_pin` (`:2847-2878`) from discarding `target`
      into `**_unused` (`:2854`): add `target: Path | None = None` as an explicit keyword-only
      parameter, and add `target=target` to the inner call to `_verify_commit_reachable`
      (`:2872-2878`), matching the `repo_credential_path` threading pattern at `:2866-2870`. No
      production call site changes — `verify_pin_preconditions()` (`:3074-3084`) already passes
      `target=resolved_target` uniformly. (Spec: R2)
- [ ] 5.3 In `jobfolder.py`'s catch-all branch (`:2579-2596`), call
      `_unpushed_weight_from_cache(target, commit, repo_url, repo_ref)` before composing the
      message, and branch on `weight.measured` to select between the two message shapes, using
      Phase 0.4's amended literals (no "at least"; exact cache-relative count; no claim about the
      remote now). Keep `remedy` and `unauthenticated`'s existing literals byte-for-byte, and
      append the weight/reason clause strictly after `remedy` — never spliced ahead of or
      interleaved within existing content. (Spec: R1, R3, R4, R6, R9)
- [ ] 5.4 **Verify**: run 4.1–4.5 and confirm all GREEN; re-run 2.1–2.11 and confirm no regression
      from the signature/message changes.

## Phase 6: Documentation — SKILL.md

- [ ] 6.1 In `skills/remote-execution/SKILL.md`, after the existing refusal paragraph (`:858-863`)
      and before the timeout paragraph (`:865-871`), add prose documenting both refusal shapes:
      measured (exact cache-relative count + remedy) and unmeasurable (no remedy). State plainly
      that the count is exact about the local cache from the last fetch and makes no claim about
      the remote's state now. Refer to the condition only as `` `pin-published` ``, never by
      position or by the total count of conditions. (Spec: R6, R10, R13)
- [ ] 6.2 [Check] Run `PinConditionDoctrineTests` (`:12779`) and `PinConditionOrdinalGuardTests`
      (`:12951`) against the updated `SKILL.md` and confirm green.

## Phase 7: Full Verification

- [ ] 7.1 Run `.micromamba/envs/papersmith/bin/python -m pytest tests/test_remote_execution.py`
      (fast inner loop). Confirm every new lock (2.1–2.11, 4.1–4.5) is green, and confirm
      `tests:12124`/`tests:19626` pass unedited.
- [ ] 7.2 Run `npm run test:all` (both suites — Node `node:test` and pytest). Confirm green
      end to end; do not skip either suite.
- [ ] 7.3 Diff `skills/remote-execution/scripts/jobfolder.py:2559-2578` (the `except
      GitTimeoutError` branch) against its pre-change text and confirm byte-for-byte equality.
- [ ] 7.4 Confirm `PIN_CONDITIONS` (`:2607-2608`) is byte-unchanged and no new tuple member exists.
- [ ] 7.5 Run `ruff check .` (per `openspec/config.yaml`) and resolve any new findings in the
      touched `jobfolder.py` region.

## Phase 8: Record-Keeping / Close-out

- [ ] 8.1 Update `design.md`'s "Open Questions": mark the timeout-value question resolved with
      the value chosen in 1.2, and confirm the anchor-direction question (closed in 0.6) stays
      marked closed.
- [ ] 8.2 Record 1.1's raw measurement numbers and 1.2's derived-constant rationale in
      `apply-progress.md`, cross-referenced from `PIN_WEIGHT_TIMEOUT_SECONDS`'s comment.
- [ ] 8.3 Check the proposal's Success Criteria (`proposal.md` lines ~226-237) against the
      actually-implemented behavior and mark each item observed-true or honestly unmet.

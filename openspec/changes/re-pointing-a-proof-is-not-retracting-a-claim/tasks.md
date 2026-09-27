# Tasks: re-pointing-a-proof-is-not-retracting-a-claim

## Requirement Key

Short references used on task lines below, numbered in the order they appear in
`specs/implementation-witness-rebinding/spec.md`:

| # | Requirement |
|---|-------------|
| R1 | Replacing an Existing Witness Leaves the Mark and the Rest of the Holder Untouched |
| R2 | Re-Pointing Is Mark-Blind |
| R3 | `--replace` Is Only Valid Alongside `--attach` |
| R4 | `--replace` Requires an Existing Witness to Replace |
| R5 | A No-Op Replacement Is Refused, Not Silently Written |
| R6 | `SETTLE_ALREADY_WITNESSED` Still Fires Without `--replace`, and Now Names Its Exit |
| R7 | The Previous Witness Is Recorded as Evidence |
| R8 | Re-Pointing Performs No Test-Suite Measurement |
| R9 | The Gating Surface Is Unchanged |
| R10 | The Three New Refusals Classify as Invocation Defects |
| R11 | Existing `--attach` Refusals Still Take Precedence |
| R12 | The Sealed Golden Delta Is a Declared Consequence, Not a Surprise |

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~360 (design's measured per-file total: engine code ~45, engine docstrings/help ~75, `SKILL.md` ~18, `usage.md` ~55, tests ~170; generated `digests.json` excluded). Proposal's own independent range: 300-420 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR, with a declared two-slice contingency named below (not chosen upfront) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

This forecast is carried forward from the design's own measurement (`design.md`
*Review budget*), not re-derived here. The design rated the same number Medium
risk under a 400-line budget and named its cut in advance; that cut is restated
below as a contingency, not re-decided.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | The whole change: `--attach --replace`, its three refusals, the recorded `replacedWitness`, the classification and count-sentence moves it forces, the one seal delta, the closure/narrative documentation, and full verification | PR 1 (only PR, intended) | `python3.12 -m unittest tests.test_proposal_implementation` | `npm run test:all` (`node --test tests/**/*.mjs` plus `.micromamba/envs/papersmith/bin/pytest`) — this repository has two suites and running one alone has hidden a regression before | One commit against `main`, reverting independently: the flag is additive, `replacedWitness` appears only on events this change can write, and a reverted engine simply refuses `SETTLE_ALREADY_WITNESSED` again. No `AGREED.md` in this repository is edited by the change itself |

### Named Contingency — the Declared Cut (do not re-derive; invoke only if the real count passes 400)

If the measured diff passes the 400-line budget before the narrative documentation
lands, cut exactly here — this boundary is the design's own, restated:

- **Slice 1 — the flag and everything the suite forces to move with it.** Phases
  1-5 below: engine code, its docstrings/argparse help, the three
  `GATING_REFUSALS` entries, locks 1-9, the count-test rename, the three
  count sentences (`SKILL.md:3060`, `SKILL.md:3078`, `usage.md:2460`), and the
  seal recapture. Stands alone: `npm run test:all` green, the flag works, the
  refusals name their exits. The count sentences are **not** deferrable to
  Slice 2 — `test_the_doctrine_states_the_split_the_roster_actually_holds`
  reads them off disk, so they are engine work wearing a markdown file's
  clothes, and Phase 5 keeps them with the classification commit.
- **Slice 2 — the narrative.** Phase 6 below: `SKILL.md`'s closure paragraph,
  the settle row, `usage.md`'s worked replace path, and locks 11-12. Stands
  alone: documentation plus its own locks, no engine change.

They should not land far apart if split: Slice 1 ships a capability whose only
written argument lives in a docstring, and the Slice 2 amendment is what makes
the flag legitimate rather than merely present.

### Parallelization Notes

- **Phase 0** is read-only provenance verification and can run any time,
  independent of every other phase.
- **Phase 1** (RED tests) must all land before Phase 2 (GREEN) touches the
  refusal ladder — strict TDD is on (`openspec/config.yaml: strict_tdd: true`).
  Tasks 1.1-1.9 are independent of each other in intent but land in the same
  test file, so treat them as sequential edits.
- **Phase 2** is sequential: 2.1 (conflict check) -> 2.2 (renderer) -> 2.3
  (refusal ladder + splice) -> 2.4 (event/response keys) -> 2.5 (wording) ->
  2.6 (argparse) -> 2.7 (docstring roster). Each reads state the previous task
  put in place.
- **Phase 3** (classification + the two inherited count tests) MUST land in
  the same commit as Phase 2 — the design is explicit that this is not
  deferrable.
- **Phase 4** (seal regeneration) runs only after Phase 2 and Phase 3 are
  green locally; it is a procedural step, not a written lock.
- **Phase 5** is the Slice 1 verification gate.
- **Phase 6** (Slice 2 narrative) depends only on Phase 2's landed behavior
  and Phase 3's landed count sentences; it does not depend on Phase 4.
- **Phase 7** (full verification) is last and depends on everything before it.
- **Phase 8** (release hygiene) runs once, after all functional and
  documentation changes are committed, so the version moves exactly once for
  whichever commit is last under `skills/`.
- **Phase 9** (record-keeping) is last.

## Phase 0: Provenance — the Already-Shipped Note Stays Accurate

Read-only verification. `d747e23` is documentation of a released change, not
work to plan or redo; this phase only confirms the record has no hole.

- [x] 0.1 Confirm commit `d747e23` (`feat(remote-execution): hand the run's
      mode and units to the kernel`) exists in `git log` and is reachable from
      tags `v0.3.0`, `v0.3.1`, and `v0.4.0` (`git tag --contains d747e23` or
      equivalent ancestry check). Read
      `openspec/changes/re-pointing-a-proof-is-not-retracting-a-claim/proposal.md`
      lines ~326-343 ("Already shipped, recorded here so the record has no
      hole") and confirm the commit hash, the file/line citations
      (`skills/remote-execution/assets/runner_invoke.py:123-124`, `:150-182`,
      `:184-207`, `:363` — read-only) and the release-tag claim all still
      match disk. If any drift is found, correct
      `openspec/changes/re-pointing-a-proof-is-not-retracting-a-claim/proposal.md`
      in place; otherwise no edit is made. **Acceptance**: the section's
      claims are verified true or corrected; nothing in scope is planned or
      redone from it.

## Phase 1: RED — New Locks for `settle --attach --replace`

Every task below adds a failing test to `tests/test_proposal_implementation.py`
**before** the production code in Phase 2 exists. Fixtures reuse
`SettleAttachCommandTests._box` / `_settle` (`tests:24574-24603`), whose argv
builder already emits a bare flag for a `True` value, so `--replace` needs no
helper change. Add a new `SettleReplaceCommandTests` class immediately after
`SettleAttachCommandTests` (`tests:24574-24639`) to hold these. Each task names
the mutation a weaker lock would survive (design's Testing Strategy table) —
run the mutation, observe red, and paste the observed failure before writing
the task off as done; a green-on-first-run lock is not proven reachable-red.

- [x] 1.1 [RED] A ticked, witnessed line re-points: `settle --attach --witness
      test_b --replace --text <line>` returns `test_b` as the witness, and
      the fixture's whole holder file is asserted byte-identical to the
      expected file via `read_bytes()` equality — never a regex on the line.
      Use a fixture line with a `*` bullet and doubled internal spacing so the
      comparison cannot pass by coincidence. **Mutation to survive**: rebuild
      the line as `f"- [x] {text} \`{witness}\`"` instead of splicing at
      `span("witness")` — a lock asserting only "the new witness is present
      and the mark is still `[x]`" survives that mutation; only the whole-file
      byte comparison fails. (Spec: R1)
- [x] 1.2 [RED] An **unticked**, witnessed line re-points and stays `[ ]`,
      using a fixture line matching `implementations/Domain_Adaptation/MIL-CREDA/AGREED.md:146`'s
      shape (an unticked line carrying a witness token) — the target file
      itself stays untouched. **Mutation to survive**: add
      `if located.group("mark") != "x": raise` (a plausible "only re-point
      what is proven" guard). Lock 1.1 survives that mutation entirely; only
      this unticked fixture fails. This is the lock that pays for the spec's
      mark-blindness requirement. (Spec: R2)
- [x] 1.3 [RED] `SETTLE_NOTHING_TO_REPLACE` fires on a located line carrying
      no witness, **and the holder file is unchanged afterwards** (byte
      comparison, not just an exit-code assertion). The refusal's detail names
      the located line and states that plain `--attach` (no `--replace`) is
      the create path. **Mutation to survive**: delete the `if not existing`
      check so `--replace` degrades to a plain create — an exit-code-only
      lock survives a variant that refuses *after* writing; the byte
      comparison is what closes that gap. (Spec: R4)
- [x] 1.4 [RED] `SETTLE_WITNESS_UNCHANGED` fires on a same-token call, **and
      no ledger event is appended** — assert `position.jsonl`'s line count is
      identical before and after the call, not merely the exit code.
      **Mutation to survive**: make it a silent no-op that still returns
      `status: "written"` — an exit-code-only lock survives a no-op that
      refuses *and still appends* an event; the ledger census is what the
      spec's own argument for this refusal requires. (Spec: R5)
- [x] 1.5 [RED] `SETTLE_REPLACE_CONFLICT` fires for `--replace` given alone
      (no `--attach`), and for `--remove --replace`. **Mutation to survive**:
      move the check below `SETTLE_WITNESS_REQUIRED` — the `--replace`-alone
      case would still survive that (no `--attach`, so `WITNESS_REQUIRED`
      cannot fire either); only the `--remove --replace` case pins the check's
      position ahead of the mode-specific conflict codes. (Spec: R3)
- [x] 1.6 [RED] All three new codes (`SETTLE_REPLACE_CONFLICT`,
      `SETTLE_NOTHING_TO_REPLACE`, `SETTLE_WITNESS_UNCHANGED`) are present in
      `GATING_REFUSALS` and explicitly classified `INVOCATION_DEFECT` — assert
      the classification kind directly, not only presence.
      `reachable_refusal_codes()` (`tests:33581`) already proves presence by
      construction; this lock's own assertion must fail for a readable reason
      if one of the three is classified `WORK_STATE` instead (which would
      also make `test_every_work_state_publishes_something_runnable`,
      `tests:33713`, fail for a missing builder — assert the kind explicitly
      so the cause is legible rather than inferred). (Spec: R10)
- [x] 1.7 [RED] `SETTLE_ALREADY_WITNESSED` still fires without `--replace`
      (regression: this condition MUST NOT change), and its detail contains
      the literal substring `--replace`. Two separate mutations, each caught
      by a different half of this lock: (a) invert the guard to
      `if existing and replace:` — caught by the existing byte-unchanged
      regression lock at `tests:24626-24639`, left untouched by this change;
      (b) ship the flag but leave the old sentence unedited — caught **only**
      by this task's detail-substring assertion, and only if it asserts the
      exact token `--replace`, not merely that the detail is non-empty.
      (Spec: R6)
- [x] 1.8 [RED] Replacement succeeds when the new witness names **no real
      test that exists in `tests/`**, and no read of `tests/` occurs on this
      path. Write a fixture `tests/` directory containing a *different*
      function than the one named, then assert exit 0 **and** that a
      subsequent `agreements_state()` call reports the line under
      `witness.disagrees` — proving the engine wrote a token it never
      measured. Mirrors `tests:25770-25786`. **Mutation to survive**: add an
      existence check inside the branch — a lock asserting only "the command
      succeeds" on a box whose `tests/` happens to contain the real function
      survives that; the mismatched fixture is what fails. (Spec: R8)
- [x] 1.9 [RED] `call_site_functions("agreements_state") == {"holder_resolution",
      "cmd_close", "cmd_verify"}` (reusing
      `AgreementWitnessSingleWritePathTests.call_site_functions`,
      `tests:25918-25934`), asserted as a full-set equality, not a membership
      check. **Mutation to survive**: add `agreements_state(target, name)`
      inside `cmd_gate` — a lock asserting only `"cmd_gate" not in the set`
      survives a new call added to `cmd_probe` instead; only the full-set
      equality catches either. (Spec: R9)

## Phase 2: GREEN — the `--replace` Modifier Inside the Existing `--attach` Branch

No second mode, no second located-line loop, no second splice, no second
renderer — the design's whole argument is that this branch already owns every
piece but one refusal. Implement in this order so each task's precondition is
satisfied by the one before it.

- [x] 2.1 In `skills/_core/implementation/engine/implementation_engine.py`, at
      `:14779-14782` where `attach`/`remove`/`reverse`/`done` are already read
      from `args`, add `replace = bool(getattr(args, "replace", False))`. At
      `:14791` (between the existing `SETTLE_ATTACH_CONFLICT` block at
      `:14784-14789` and the `witness = getattr(...)` resolution), add the
      `SETTLE_REPLACE_CONFLICT` check: `if replace and not attach: raise
      Refused("SETTLE_REPLACE_CONFLICT", ...)` naming both exits (add
      `--attach`, or drop `--replace`). This placement changes no existing
      refusal's firing order — nothing between `:14784` and `:14829` reads
      `replace` today. **Verify**: 1.5 goes GREEN; existing
      `SettleAttachCommandTests`, `SettleRemoveCommandTests`,
      `SettleReverseCommandTests`, `SettleDoneCommandTests` stay green
      unmodified. (Spec: R3)
- [x] 2.2 In the same file, at `:14938-14940` beside `heading`, `supersedes`
      and `collides`, initialise `replaced_witness = None`. It must be in
      scope for the ledger append and response construction outside every
      mode branch.
- [x] 2.3 In the same file's `--attach` branch, after
      `target_path, data, span = candidates[0]` (`:14961`) and the existing
      `AGREEMENT_LINE` match (`:14963-14964`), replace the single
      `SETTLE_ALREADY_WITNESSED` refusal at `:14965-14970` with the four-line
      ladder: `existing and not replace` -> `SETTLE_ALREADY_WITNESSED` (detail
      now names `--replace`, see 2.5); `replace and not existing` ->
      `SETTLE_NOTHING_TO_REPLACE`; `replace and existing == witness` ->
      `SETTLE_WITNESS_UNCHANGED`; otherwise `replaced_witness = existing`.
      Call `_render_settled_line(text, witness, raw_line=raw_line,
      replacing=replace)` (renderer change in 2.4) and feed the result to the
      existing `impl_position.splice` call — no second splice. **Verify**: 1.3
      and 1.4 go GREEN. (Spec: R4, R5, R11)
- [x] 2.4 In the same file, give `_render_settled_line`
      (`:14014-14053`) a keyword-only `replacing: bool = False` parameter.
      Inside the existing `raw_line is not None` branch, when `replacing` is
      true, re-match `AGREEMENT_LINE` against the decoded body, take
      `span("witness")`, and substitute only those characters — the backticks,
      the leading space, the bullet, the mark, and the claim text are never
      re-emitted. Add the docstring's third case per the design's Interfaces
      block, naming that the witness group always participated when
      `replacing` is true because `SETTLE_NOTHING_TO_REPLACE` (2.3) refused
      otherwise — the guard is that refusal and its lock (1.3), not a
      defensive re-check here. **Verify**: 1.1 and 1.2 go GREEN;
      `AgreementWitnessSingleWritePathTests` (`tests:25936-25946`) stays green
      unmodified — this design adds no second renderer. (Spec: R1, R2)
- [x] 2.5 In the same file, amend `SETTLE_ALREADY_WITNESSED`'s detail text
      (still raised at the same site, same condition) to add one clause
      naming `--replace` as the exit: `"…already carries witness 'test_a';
      --attach adds a witness, it never replaces one. To re-point this line
      at a different test, add --replace."` The firing condition is
      byte-unchanged (`if existing and not replace:` — identical to
      `if located.group("witness"):` whenever `replace` is falsy). **Verify**:
      1.7 goes GREEN; the existing regression lock at `tests:24626-24639`
      (code + byte-unchanged file) stays green unmodified. (Spec: R6)
- [x] 2.6 In the same file, at `:14791`-adjacent argparse construction for
      `settle` (`:20607`), add `--replace` as `action="store_true"` with help
      text naming what it does. At `:20669-20718`, amend the `--witness` help
      (`:20682-20684`, retiring *"`--attach` never replaces one"*) and the
      `--attach` help to name the replace path.
- [x] 2.7 In the same file's `cmd_settle` docstring (`:14335-14347` head,
      `:14583-14733` numbered roster): add one clause to the head naming that
      `--attach` takes `--replace` (*"all five modes"* stays true, unedited).
      In the roster, item 3 (the conflict-code list) gains
      `SETTLE_REPLACE_CONFLICT`; item 17 (`:14719-14726`, currently *"there is
      no separate flag that does"*) is rewritten to describe the replace
      path; a new item 18 covers `SETTLE_NOTHING_TO_REPLACE` and
      `SETTLE_WITNESS_UNCHANGED`, and the current item 18 becomes item 19.
      Items 1-17 keep their existing numbers — this insertion point was chosen
      specifically so twelve items do not renumber.
- [x] 2.8 In the same file, at the `kind: "settle"` ledger event
      (`:15167-15174`) and the response construction (`:15176-15183`), add two
      keys to each — `replace: replace` and `replacedWitness:
      replaced_witness` — placed beside the existing `attach`/`remove`/
      `reverse`/`done` flags so the mode-flag run stays contiguous. Both keys
      are unconditional: present (and `None`/`False` as applicable) on every
      `settle` call, not only the replace path. **Verify**: the ledger-event
      half of 1.4's assertion and the response half of the happy-path locks
      (1.1, 1.2) confirm `replace`/`replacedWitness` appear correctly; add one
      direct assertion that a successful replacement's event and response
      both carry `replace: true` and `replacedWitness: "test_a"` (spec
      scenario "The ledger event and the response both name the displaced
      token"). (Spec: R7)

## Phase 3: Classification and the Two Inherited Count Tests

This phase MUST land in the same commit as Phase 2 — not deferred, not a
follow-up. The design is explicit: an unclassified reachable code reddens the
whole suite by construction, and the two count tests below go red the moment
classification lands, whether or not anyone remembers to update them.

- [x] 3.1 In `implementation_engine.py`'s `GATING_REFUSALS` table
      (`:19033-19058`, the settle block — corrected from the proposal's
      `:19039-19055`, which clipped five entries at each end), add
      `SETTLE_REPLACE_CONFLICT`, `SETTLE_NOTHING_TO_REPLACE`, and
      `SETTLE_WITNESS_UNCHANGED`, each classified `INVOCATION_DEFECT` beside
      `SETTLE_ALREADY_WITNESSED` (`:19047`). Add no entry to
      `_WORK_STATE_RESOLUTIONS` (`:19776`) — `refusal_resolution`
      (`:20121`) returns `None` for a non-`WORK_STATE` code at
      `:20148-20149`, before the builder lookup at `:20150`, so the three new
      codes owe no builder. **Verify**: 1.6 goes GREEN;
      `test_no_invocation_defect_publishes_a_resolution` (`tests:33730`) stays
      green unmodified. (Spec: R10)
- [x] 3.2 In `tests/test_proposal_implementation.py`, rename
      `test_the_derivation_finds_the_measured_one_hundred_and_twenty_one`
      (`tests:33624-33676`) to
      `test_the_derivation_finds_the_measured_one_hundred_and_twenty_four` —
      rename, not a second method; two methods differing only in a number is
      the exact shape that once dropped five tests silently in this file.
      Change the assertion from `len(reachable_refusal_codes()) == 121` to
      `== 124`, and add one docstring sentence recording this change's
      measured delta (+3: the three codes from 3.1).
- [x] 3.3 In the same commit as 3.1, update the three count sentences
      `test_the_doctrine_states_the_split_the_roster_actually_holds`
      (`tests:33740-33793`) reads off disk: `SKILL.md:3060` ("One hundred and
      twenty-one distinct codes are reachable from the ten gating commands")
      -> "one hundred and twenty-four"; `SKILL.md:3078` ("(50 codes)") ->
      "(53 codes)"; `usage.md:2460` ("Fifty codes, and nothing is published
      beside them") -> "Fifty-three codes". Do **not** touch `SKILL.md:3082`
      or `usage.md:2465` (the work-state sentences, "seventy-one codes") —
      that count does not move. **Verify**: 3.2's renamed test and
      `test_the_doctrine_states_the_split_the_roster_actually_holds` both go
      GREEN; run both together, since this test's own docstring warns that a
      stale count on one side used to pass while the other side was right.
- [x] 3.4 Confirm `test_the_roster_classifies_nothing_a_gating_command_cannot_raise`
      (`tests:33691`) stays green unmodified — it is the reverse-direction
      check, and 3.1 adds no raise site that is not already reachable from
      `cmd_settle`.

## Phase 4: Seal Digest Regeneration (Slice 1 close-out)

Procedural, not a written lock. `tests/seal/cases.json:395` (the one existing
`settle` case, the default create path) is not in `unsealed.json`; adding
always-present `replace`/`replacedWitness` keys moves its stdout digest
regardless of whether `--replace` is exercised by that case.

- [x] 4.1 Run `.venv/bin/python tests/seal_capture.py` (the only writer of
      `tests/seal/digests.json`; deliberately excluded from `unittest
      discover` per its own docstring). It rewrites the whole file after
      running every case twice in two independently built corpora and
      refuses to write on an unexpected disagreement.
- [x] 4.2 Read the resulting `git diff -- tests/seal/digests.json`. Confirm
      **exactly one** entry changed — the `settle` case — and that
      `__corpus_fingerprint__` is unchanged (`tests/seal/corpus.py` is not
      edited by this change). **Acceptance criterion, stated as a stop
      condition**: a second moved entry is an unexplained seal failure, not a
      bulk regeneration to accept — if the diff shows more than one changed
      entry, STOP and report `blocked`, do not proceed to Phase 5. The
      regenerated `digests.json` is a generated golden: excluded from the
      authored review-line count, included in the commit. (Spec: R12)

## Phase 5: Slice 1 Verification Gate

- [x] 5.1 Run `python3.12 -m unittest tests.test_proposal_implementation`.
      Confirm every Phase 1 lock (1.1-1.9) is GREEN, confirm 3.2's renamed
      test and `test_the_doctrine_states_the_split_the_roster_actually_holds`
      are GREEN, and confirm no previously-green test in this module
      regressed.
- [x] 5.2 **The cut WAS invoked** — the real diff (602 lines) passed the
      400-line budget. Slice 1 landed as commit `8f171c8`: flag works,
      refusals name their exits, and the seal digest was individually read
      and found unmoved (zero changed entries, not one — see 9.1/9.3 and
      the proposal's own success-criteria note for why).

## Phase 6: Documentation — the Narrative (Slice 2 if split)

- [x] 6.1 In `skills/proposal-implementation/SKILL.md:2996-3004` (the
      closure paragraph for *"`settle`'s class is closed at five modes"*),
      add the third case the closure criterion never examined: re-pointing a
      witness is `--attach`'s own write with one refusal lifted, spelled as a
      modifier rather than a sixth mode, because the only composition that
      would reach the same end state (reverse, place, attach, done) is not
      equivalent — it destroys a tick the agreement never lost and writes a
      `## Reversed` entry for something never reversed. Confirm
      `SettleFiveModesClassStatedOnceTests` (`tests:25829-25866`) still
      passes — both substring anchors it asserts (`:25851-25852`) sit in
      sentences this task does not touch. (Spec: — narrative decision,
      proposal *Decision block*)
- [x] 6.2 In the same file's `settle` row (`:3015`), add `--replace` to *What
      it writes* and the three new codes to *Refuses on*.
- [x] 6.3 [RED then GREEN] Add a lock extending
      `test_the_settle_row_documents_remove_and_reverse` (`tests:25854-25866`)
      to also assert the settle row's *Refuses on* cell names
      `SETTLE_REPLACE_CONFLICT`, `SETTLE_NOTHING_TO_REPLACE`, and
      `SETTLE_WITNESS_UNCHANGED` — write it failing first, then satisfy it
      with 6.2.
- [x] 6.4 In `skills/proposal-implementation/references/usage.md:1351-1403`
      (the `### --attach` section), add the replace path: prose, a runnable
      example, and a response block. **The example MUST show the
      operator-facing surprise explicitly**: `--text` matches
      `AGREEMENT_LINE`'s text group, which stops before the trailing
      `` `test_<id>` `` token (`:14146`, `:321-322`) — so re-pointing
      `- [x] the claim \`test_a\`` is `--text "the claim"`, never
      `--text "the claim \`test_a\`"` (which matches zero lines and refuses
      `SETTLE_TEXT_ABSENT`). Name the three new refusals. Retire
      `:1383`'s *"`--attach` never replaces one, only adds"* sentence, and
      restate the mark rule as inherited from `--attach` rather than
      restated. At `:1342-1349` (the single-write-path paragraph), name the
      third route into the witness token.
- [x] 6.5 In the same file, update the count sentence at `:2460` to match
      3.3's `SKILL.md` change ("Fifty-three codes"). Do **not** touch
      `:2465` (the work-state count, unchanged at seventy-one).
- [x] 6.6 [RED then GREEN] Extend
      `SettleRemoveReverseUsageDocumentedTests` (`tests:25789-25826`)'s
      pattern with a lock reading the `### --attach` section body between
      headings, asserting both that `--replace` and the three codes appear
      **and** that the retired sentence (*"never replaces one, only adds"*)
      is absent — a positive-only assertion would survive leaving `:1383`
      standing; the negative assertion is what makes the
      prose-outlives-mechanism risk enforceable.
- [x] 6.7 [Read-only confirmation] Read
      `skills/experimental-implementation/references/usage.md:36` (read-only
      — this file is not edited by this change) and confirm *"`settle`'s five
      modes"* is still true under the modifier decision (it is: no sixth mode
      was added). Leave it unedited. This is recorded here, and in
      `design.md`'s *Disagreements with disk* item 6, precisely so a later
      sweep does not "fix" a sentence that is already correct.

## Phase 7: Full Verification

- [x] 7.1 Ran the fast inner loop (`.micromamba/envs/papersmith/bin/pytest
      tests/test_proposal_implementation.py` — the bare `python3.12 -m
      unittest` invocation fails to resolve `domain_profile`/`pytest`
      outside pytest's own sys.path setup, confirmed via `git stash` to be
      an environment artifact identical on clean HEAD, not a regression;
      see 9.3's sibling note). Every new lock (1.1-1.9, 6.3, 6.6) green, and
      all four inherited locks green.
- [x] 7.2 Ran `npm run test:all` on the fully committed final state (all
      three commits landed): **653/653 Node tests, 5277 passed + 4 skipped
      Python tests, 0 failures, exit 0** (770s). Two earlier `npm run
      test:all` runs during apply showed 9 and 15 failures respectively —
      the first before the `test_implementation_domain_lock.py` pin fix
      (Phase 7's own discovery, see 9.1/9.3), the second contaminated by a
      concurrent `git stash --keep-index` verification step running against
      the same working tree; neither is a real regression in the delivered
      state, both explained rather than hidden.
- [x] 7.3 Diff `implementation_engine.py:15163-15164` and the
      `impl_position.splice` call path against pre-change text and confirm
      byte-for-byte equality — one splice, one compare-and-swap, as today.
- [x] 7.4 Confirm `agreements_state` (`engine:374`) is still called from
      exactly `:570` (`holder_resolution`), `:16536` (`cmd_close`), and
      `:17582` (`cmd_verify`) — no new call site — and that
      `AGREEMENT_DISAGREES`'s single raise site and doctrine comment
      (`:16529-16546`) are byte-unchanged.
- [x] 7.5 Run `ruff check .` (per `openspec/config.yaml`) and resolve any new
      findings in the touched `implementation_engine.py` region.

## Phase 8: Release Hygiene — the Version Moves Once

`skills/` is a shipped root (`tests/test_version_sources.py`'s
`SHIPPED_ROOTS`), and this change edits
`skills/_core/implementation/engine/implementation_engine.py`,
`skills/proposal-implementation/SKILL.md`, and
`skills/proposal-implementation/references/usage.md`. Both
`ReleaseHygieneTests` in that file will fail if the version does not move.
Run this phase once, after every functional and documentation change above is
committed, regardless of whether Phase 6 landed as part of the same commit or
a later one.

- [x] 8.1 Bump `package.json`'s `"version"` field and
      `src/papersmith/__init__.py`'s `__version__` together, to the same new
      value (a patch bump — additive capability, no breaking change; the
      current value on disk is `0.4.0`). `pyproject.toml` reads
      `papersmith.__version__` dynamically and needs no edit.
- [x] 8.2 Add a new `## <version>` section to the top of `CHANGELOG.md`,
      above `## 0.4.0`, describing `settle --attach --replace`: what it
      writes, what it records, the three refusals, and the one declared seal
      delta — matching this file's own register (see the `## 0.4.0` entry
      immediately below it for tone).
- [x] 8.3 Run `python3.12 -m unittest tests.test_version_sources` and confirm
      `VersionSourcesAgreeTests` and `ReleaseHygieneTests` (including
      `test_the_changelog_documents_the_current_version`) are green.

## Phase 9: Record-Keeping / Close-out

- [x] 9.1 Checked the proposal's Success Criteria (`proposal.md` lines
      ~300-309) against the actually-implemented behavior; each item marked
      observed-true or honestly unmet in place. Eight of nine are observed
      true. One is honestly unmet: the declared one-entry seal delta did not
      materialize (Phase 4 finding) — the sealed `settle` case already
      refuses `SETTLE_NOT_DISCUSSED`, pre-existing and unrelated to this
      change, before reaching the response path the new keys touch, so
      `digests.json` recaptured byte-identical (zero entries moved).
- [x] 9.2 The Named Contingency (two-slice cut) **was invoked** — the real
      diff passed 400 lines. Commits, in order on `main`:
      - `8f171c8` `feat(proposal-implementation): add settle --attach
        --replace` — Slice 1 (Phases 1-5): `implementation_engine.py`, the
        `SettleReplaceCommandTests` class + renamed count test in
        `test_proposal_implementation.py`, the two non-deferrable count
        sentences in `SKILL.md`/`usage.md`, and the unplanned-but-required
        `tests/test_implementation_domain_lock.py` pin update (see 9.1's
        sibling finding and the proposal's own success-criteria note). 417
        insertions, 63 deletions across 5 files.
      - `ae18775` `docs(proposal-implementation): document settle --attach
        --replace` — Slice 2 (Phase 6): `SKILL.md`'s closure paragraph and
        settle row, `usage.md`'s `### --attach` narrative, and the two
        Phase 6 doc-lock tests. 115 insertions, 7 deletions across 3 files.
      - `158736e` `release: 0.5.1` — Phase 8 (release hygiene, not part of
        the two-slice cut): `package.json`, `src/papersmith/__init__.py`,
        `CHANGELOG.md`. 35 insertions, 2 deletions.
- [x] 9.3 Final measured changed-line count (additions + deletions,
      generated `digests.json` excluded — it did not change): **602** for
      the core capability (Slices 1+2: 480 + 122), against the design's
      ~360-line forecast — a **+67% drift**. Per-file, against the design's
      *Review budget* table: `implementation_engine.py` ~120 est.
      (code+docstrings/help combined) vs **196** actual (+76, this file's
      own long-form docstring/argparse-help register, as the design itself
      flagged as a risk); `SKILL.md` ~18 est. vs **16** actual (on target);
      `usage.md` ~55 est. vs **82** actual (+27, the worked `--attach
      --replace` example and response block ran longer than forecast);
      `tests/test_proposal_implementation.py` ~170 est. vs **287** actual
      (+117, ten `SettleReplaceCommandTests` methods at this file's own
      fixture-per-test density, plus the two Phase 6 doc-lock tests, plus
      the renamed count test and its docstring sentence). One driver the
      design's own forecast could not have named: **+21** lines in
      `tests/test_implementation_domain_lock.py`, a file outside this
      change's originally declared scope, required because the engine
      prose additions moved nine pinned word-occurrence counts — not
      optional, not deferred, following that file's own established
      per-change convention.

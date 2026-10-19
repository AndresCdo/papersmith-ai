# Tasks: A Revision Is Its Bytes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~980 (engine ~150, docs ~20, tests ~560, this change ~250) |
| 400-line budget risk | Medium: production code is ~150 lines in one file; the rest is tests and this change |
| Chained PRs recommended | No |
| Suggested split | One PR, two commits: the fix, then this change |
| Delivery strategy | single PR |
| Chain strategy | none |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: none
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Byte identity, diagnostics, docs, tests | PR 1 | `pytest tests/test_implementation_revision_identity.py` | the proposal and experimental CLIs | revert the fix commit |
| 2 | This change (the spec exception) | PR 1 (same) | none: documentation | none | revert this change's commit |

One PR: unit 2 records the exception unit 1 needs, so neither ships alone.

## Phase 1: RED (strict TDD)

- [x] 1.1 `test_revision_identity_distinguishes_distinct_raw_document_bytes`,
  `test_revision_identity_matches_hash_of_persisted_bytes`,
  `test_revision_identity_compatibility_preserves_existing_records`, the
  zero-byte test, the reader tests and the experimental-host test, run
  against the unfixed engine: 21 failed, 3 passed.
- [x] 1.2 The gate test (`GateCommandTests`) and the close test
  (`CloseCommandTests`) against the unfixed engine: the gate records a launch
  under a token minted over other bytes, and close closes a position bound to
  other bytes.
- [x] 1.3 The second-document ruling test (`PerDocumentCitationImpactClassTests`)
  against the unfixed engine: fails on the stored digest.

## Phase 2: GREEN

- [x] 2.1 `RevisionText`, `revision_identity`, `matches_text_only`; the
  reader returns the carrier.
- [x] 2.2 The nine identity sites hash through `revision_identity`.
- [x] 2.3 `textOnlyMatch` in `position_state`, present only when not empty.
- [x] 2.4 The text-only causes in `admissibility_record`, gate and close.
- [x] 2.5 `_bound_to` resolves a zero-byte revision.
- [x] 2.6 Domain-lock pin: `before` 261→263, changelog line.

## Phase 3: Docs and regression

- [x] 3.1 `SKILL.md`'s stale-position row and `usage.md`'s identity paragraph.
- [x] 3.2 This change: proposal, design, tasks, delta spec.
- [x] 3.3 Both seal comparators, the token re-derivation test, the pair,
  experimental and proposal suites, without recapturing a golden.
- [x] 3.4 Ruff: no new finding against the base.
- [x] 3.5 Independent review; at most two fix cycles. Cycle 1: close never
  named the text-only cause. Cycle 2: the cause omitted a byte edit that
  decoding folds (a literal U+FFFD replaced by an undecodable byte). Both
  fixed, each with a test.

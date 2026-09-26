# Archive Report: The Product the History Never Took

**Change**: `the-product-the-history-never-took`
**Archive Location**: `openspec/changes/archive/2026-09-26-the-product-the-history-never-took/`
**Archive Date**: 2026-09-26
**Status**: Archived — implementation complete, verified, all tasks closed

## Specifications Synced

| Domain | Action | Details |
|--------|--------|---------|
| `implementation-product-shipped` | Created | New spec merged to `openspec/specs/implementation-product-shipped/spec.md` |

**Mechanics**: Delta spec at `openspec/changes/the-product-the-history-never-took/specs/implementation-product-shipped/spec.md` was mechanically copied (no main spec existed) to `openspec/specs/implementation-product-shipped/spec.md`. Verification: empty `diff -r` output (byte-identical copy).

## Archive Contents

### Artifacts Preserved

- **proposal.md**: Present. Defines the problem (steps can write products the repository ignores), the success criteria, and out-of-scope decisions.
- **design.md**: Present. Records all architecture and implementation decisions (D1–D7), including the seam at `_step_wrote`, the exit-code contract for `check-ignore`, and the mutation-proof test strategy.
- **specs/**: Present. Single domain folder `implementation-product-shipped/` containing the delta spec (now synced to main specs).
- **tasks.md**: Present. **34/34 tasks completed** (100%). Closing ruling appended confirming all success criteria satisfied: zero unexpected test failures across 5840 tests (one pre-existing guard correctly fires on version non-bump, as intended).

### Task Completion Summary

- **Phase 1** (Test Fixture Infrastructure): Tasks 1.1–1.2 ✓
- **Phase 2** (RED — Failing Tests): Tasks 2.1–2.9 ✓
- **Phase 3** (GREEN — Implementation): Tasks 3.1–3.8 ✓
- **Phase 4** (Mutation Verification): Tasks 4.1–4.9 ✓
- **Phase 5** (Documentation): Tasks 5.1–5.2 ✓
- **Phase 6** (Empirical Confirmation): Tasks 6.1–6.4 ✓ (with closing ruling on 6.3 and 6.4)

## Implementation Status

**Completed**: All work landed in six commits after tag `v0.3.1`:
- `adffb0e` — fixture infrastructure and RED test setup
- `3bab010` — GREEN implementation
- `87014e1` — mutation verification and domain lock
- `240b8e5` — documentation updates to SKILL.md and usage.md
- `aade456` — test implementation and record M5 pin growth
- `628ac22` — track the-product-the-history-never-took's planning artifacts
- `2252f07` — verify task state and record the ruling on 6.3/6.4

**Changes**: `~188 authored lines` (helper 25, constants 18, engine helper 22, wiring 8, docstring 5, fixture 10, tests 95, docs 5). Low risk profile; single PR delivered.

### Key Behavior Added

1. **New helper** `impl_gitops.repository_ignored(target, paths)`: Queries `git check-ignore` to identify which paths the repository declares it does not ship. Handles non-zero exit code (1/128 read as empty; OSError caught as empty). No filesystem existence check; works on deleted paths.

2. **New field** `ignored` on the `wrote` block: List of paths from `wrote["inside"]` that match `.gitignore` rules. Always present, `[]` when clean. Computed over declared, written paths only (not over `outside`).

3. **New consequence constant** `STEP_WROTE_IGNORED`: Doctrine prose explaining the incident (step declared, wrote, and owns a product the repository is told to ignore). Listed in the`note`/`ignoredNote` prose-key roster. Borrows zero target-module vocabulary (verified by domain word-count lock).

4. **Surfaces updated**: Both `cmd_step`'s return dict and terminal ledger event now report `ignored` (always present) and `ignoredNote` (only when non-empty). Ledger event strips prose keys so the event carries paths only.

## Verification Status

**Per orchestrator launch context**: "verify returned no divergences from spec or design. It reproduced the gate figures independently and re-applied three of the eight named mutations, each going red and restoring green."

**Test Results**: `npm run test:all` reported **1 failed, 5187 passed, 4 skipped** (pytest) and **653 passed, 0 failed** (node):
- Single failure: `tests/test_version_sources.py::ReleaseHygieneTests::test_shipped_changes_since_the_last_release_moved_the_version` — a pre-existing guard firing correctly because shipped files changed since `v0.3.1` but version remained `0.3.1`. By design, this gate cannot pass before the release bump (scope of the next phase). **Not a defect.**
- All 5840 other tests passed (5187 pytest + 653 node).
- Zero unexpected failures; zero regressions.

**Mutation Evidence**: Eight mutation sub-tasks (4.1–4.8) each applied a distinct, named mutation to a specific defect and confirmed the corresponding lock test failed red with it in place and passed green after revert. Mutations tested:
- Lock 1: path-base repository-relative join
- Lock 2: non-zero exit read as clean (not error)
- Lock 3: field presence in both surfaces
- Lock 4A: ledger event durability
- Lock 4B: prose stripped from ledger
- Lock 5: identity assertion on constant text
- Lock 6: deleted paths included
- Lock 7: scope limited to `inside` only

**Unresolved Findings**: None. All known defects from proposal/design resolved by implementation; all success criteria verified; all guards green except the one correctly deferred.

## Unfinished Work

None. All 34 tasks ticked. Implementation complete, verified, and closed.

## Source of Truth Updated

The following spec now reflects the new behavior:
- `openspec/specs/implementation-product-shipped/spec.md` (newly created)

The new capability `implementation-product-shipped` is now documented in the main spec tree and available for future phases to reference.

## Mechanical Verification

**Spec sync**: `diff -r "openspec/changes/the-product-the-history-never-took/specs/implementation-product-shipped/spec.md" (temporary copy)` returned empty (0 lines).

**Archive move**: `diff -r (pre-move snapshot) "openspec/changes/archive/2026-09-26-the-product-the-history-never-took"` returned empty (0 lines). Source folder removed cleanly. Archive folder created and verified byte-identical to pre-move snapshot (exclusive of this archive-report.md, which is additive).

## SDD Cycle Summary

This change closed the gap between documentation of a step's product and the repository's actual ignore rules. The implementation is:

- **Honest**: Reports what the repository actually ignores; never hides or silences findings.
- **Durable**: Ledger event carries the paths durably; reads in the terminal event are not transient stdout.
- **Safe**: No new refusals; the reading records and continues (exit-code contract matches Decision D2/D3 reasoning).
- **Verified**: Eight mutation-proof locks guard each aspect of correctness; all 5840 tests pass (except one deferred version-bump gate).
- **Complete**: All proposal success criteria satisfied; all design decisions realized and tested; all tasks executed.

The change is now archived, specifications updated, and ready for the release phase that will follow.


# Feature: Cross-skill consistency fixes (multi-paper safe)

Status: in progress
Branch: `fix/cross-skill-consistency`
Created: 2026-10-11

## Objective

Fix the cross-skill inconsistencies observed on v0.13.0 during one end-to-end run
(init → plausibility → proposal-deliberation → proposal-implementation →
paper-ingestion → experimental-deliberation → experimental-implementation).
Every change is general, backward compatible, and reachable through
`papersmith upgrade` for live v0.13.0 workspaces.

## Constraints

- Nothing paper-specific in `skills/`; guards stay fail-closed (fix logic, never bypass).
- Verify each item against current code first: real → fix; intended → document where users meet it.
- Per item: generic fixture, RED test, GREEN fix, full suite green (Node + Python), docs + CHANGELOG.
- Backward compatibility: never invalidate receipts, ledgers, seals, managed revisions, locks, holders.
  Shape/format changes need an `upgrade` migration + a test upgrading a populated v0.13.0 fixture;
  `papersmith audit --check-drift` clean afterwards.
- Commits: one work unit per item/group, Conventional Commits, no AI attribution, tests+docs in same commit.
- Priority: A → D → B → C → E. Version bump + "Behaviour changes" CHANGELOG section.
- Delivery strategy: `ask-on-risk` (forecast far above 400 lines; push/PR remain user decisions).
- RDD: off (global) — ordinary checks only.

## Checks

- `npm run test:node`, `npm run test:py` (or `test:py:par`).
- E2E smoke on fresh `papersmith init` workspace; upgrade of populated v0.13.0 fixture + `audit --check-drift`.

## Task list

Route legend: D = delegated writer, I = inline.

- [x] T0 — Exploration (D, mapping trigger): two explorers. All A1–A8 and D1–D5 confirmed real in code.
  Key map: engine `skills/_core/implementation/engine/implementation_engine.py` (E); migrations `src/papersmith/core/migrations.py` REGISTRY; no populated old-workspace fixture exists yet; full py suite ~20 min.
- [x] A1 — adopted finding terminal state (D, writer trigger: engine + tests + docs + goldens)
- [x] A2 — sibling holder collision (D, writer trigger: engine + profile loader + tests + docs)
- [x] A3 — probe pilot ladder with in-package baselines (D, writer trigger: engine + 2 test files + docs)
- [x] A4 — scaffold seal file provenance exemption (D, writer trigger: engine + 2 test files + docs)
- [x] A5 — close for proposal-only targets / witness-less agreements (D, writer trigger: engine + 2 test files + 4 docs + seals)
- [ ] A6 — deliberation validation parity (code spans)
- [ ] A7 — shared experiment heading convention
- [ ] A8 — per-lineage `__implementation__` binding (verify)
- [ ] D1 — kit provenance record + dirty-kit guard
- [ ] D2 — migration support policy
- [ ] D3 — engine state gitignore decision
- [ ] D4 — plausibility metadata cache inside sota-pool
- [ ] D5 — no bytecode in kit copy
- [ ] B1–B13
- [ ] C1–C14
- [ ] E1–E10
- [ ] F — final verification: full suite, E2E smoke, upgrade fixture, outcome table

## Progress / evidence

- A1 (real): `finding_adoption` + `adopted_record` in the engine; `admit`, `verify` audit
  (`remediesWithoutValidation`, `localRemediesNotWritten`), `migration_state`,
  `remedy_compatibility` and `handoff` share one adoption read. Adopted finding: admissible with
  optional `adopted` verdict, introduces nothing, owes only `migration`; `changed-unrecognized`
  stays inadmissible. Optional keys omitted when empty; no migration needed.
  Tests: `AdoptedFindingTerminalStateTests` (5) RED (2F/3E) -> GREEN; mutation of each reader
  and of the fail-closed branch reddens. Seal goldens regenerated via capture scripts
  (seal: admit-e1, verify-a, verify-b; experiments_seal: verify-a, verify-b, plus unsealed
  `propose` timestamp noise). Domain-lock pins unchanged. Version 0.14.0 + CHANGELOG.
  Commit: `fix(implementation): an adopted finding reaches a terminal state` (the commit carrying this line)
- A2 (real): `holder_resolution` set the sibling skill's declared holder against this skill as an
  undeclared candidate (both directions). Fix: `impl_domain_profile.declared_holder_filenames`
  derives every holder filename declared by `<skills root>/*/impl_profile.py` (only
  `PROFILE["holder"]["filename"]`; unreadable/malformed contributes nothing = fail-closed); the
  engine's `sibling_holder_filenames()` subtracts its own name, and `holder_resolution` excludes
  those from the candidate count (`byShape` stays verbatim; new `siblings`/`candidates` keys).
  `HOLDER_UNDECLARED` detail/question never offer a sibling's holder for renaming and name any
  recognized sibling holder as left alone. `agreements_state` read untouched.
  Tests: `DeclaredHolderFilenamesTests` (3, new file), HolderCollisionTests +2 new, 3 rewritten
  (they encoded the defect: `..._is_undeclared_here`, `test_reconcile_never_writes_into_the_
  siblings_declared_holder`, `test_sequence_replace_never_overwrites_...` -- sibling bytes still
  asserted unchanged), HolderResolutionTests +2 (inverse direction). RED 9F -> GREEN; mutation
  (exclusion disabled -> 6 red; shape filter loosened -> 1 red). Seals unchanged; domain-lock pins
  unchanged (comments reworded). Commit `b00042f`.
  A2 follow-up (read face, coordinator-directed): `agreements_state` sets sibling-declared files
  aside (listed under `siblingHolders`, key present only when one exists) -- covers `verify`,
  `close`, and `holder_resolution` (`byShape` now excludes siblings; `siblings` carried from it;
  the interim `candidates` key removed). `position_state`'s by-shape fallback skips them too
  (covers `verify`, `probe`, `gate`, `close`, `discuss`, `settle`, `offer`, `step`). Left as
  deliberate inventories: `_agreement_collides` (overlap report) and `cmd_position`'s write-side
  scan (`holder_digests`, legacy `--repair-header`). Tests: `SiblingHolderReadTests` (3, proposal
  direction), HolderCollisionTests +2 (experimental direction, one via the sibling's real launcher);
  RED 5F -> GREEN; mutation (agreements exclusion off -> 8 red; position exclusion off -> 3 red).
  Commit: `fix(implementation): a sibling's holder is never read as this skill's` (the commit carrying this line)
- A3 (real): `cmd_probe` set `nothing-to-compare` first and the pilot rungs fired only from
  `benchmark`/`piloted`. Fix: `flow_short`/`flow_undecided` computed once from `pilot` and read by
  the existing rungs and by a new post-ladder branch that turns `nothing-to-compare` into
  `pilot-first`/`pilot-decisions` while either holds (rung literals kept so the next-step scrapers
  still derive the set). Publication path unchanged (roster + per-step `toDiscuss`), now reached.
  Tests: `PilotLadderWithoutBaselinesTests` (proposal 4, experimental 2 via its own launcher and
  `Experimental_AGREED.md`): RED 2F + 2F -> GREEN; the e2e test answers each published placement
  question via its own `discuss` command and returns to `nothing-to-compare`. Mutation (decisions
  branch disabled) -> 2 red. Domain-lock pins unchanged (two comment rewordings). Seals unchanged.
  Commit: `fix(implementation): comparability no longer hides the pilot ladder` (the commit carrying this line)
- A4 (real): `cmd_verify` exempted only `__init__.py`, so the kit seal `src/<Package>/report_digest.py`
  (no `__provenance__` by design) fed `missingProvenance` -> `fidelity: drift` on a fresh scaffold.
  Fix: `kit_owned_package_files(name)` derives the set from `scaffold_destinations` x
  `scaffold_kit_source` (inside `src/<Package>/`); `is_unmodified_kit_file` exempts a file only when
  its bytes equal today's kit source (scaffold substitutions; refuses if the kit carries `{{SEED}}`)
  OR the `writtenSha256` of a `materialized`/`scaffold` receipt entry (covers seals written by an
  earlier release, and the experimental skill, which ships no kit). `adopted`/`authored` entries do
  not count; any other bytes report. New constant `RECEIPT_KIND_ENGINE` replaces the two writer
  literals (same value; receipt shape unchanged; no migration).
  Tests: `ScaffoldSealProvenanceTests` (6) RED 4F -> GREEN; `SiblingScaffoldSealProvenanceTests`
  (experimental, 2) RED 1F -> GREEN. Mutations: drop byte check -> 2 red; drop kind check -> 1 red;
  drop kit-bytes path -> 1 red. Domain-lock pins unchanged. Seals unchanged.
  Commit: `fix(implementation): the kit's own seal owes no provenance` (the commit carrying this line)
- A5 (real, option (a)): facts measured on a generic fixture before the fix: (1) a hand-ticked
  witness-less line counts as `settled` (listed under `witness.unwitnessed`, never `disagrees`), and
  `close` gates on agreements only via `AGREEMENT_DISAGREES`, so `agreements: open` never blocked close
  but could only reach `settled` by a hand edit; (2) with empty `__levels__`, `position --sequence`
  accepts any `--target-level`, but every witness kind is an execution one (step/notebook/record/
  rehearsal/shard), so a no-flow target could install a position only by naming a nonexistent witness
  (verified: a fake `@rehearsal job1` item let `close` pass). Fix: `_declared_flow` (levels, steps,
  records, shard root, any job folder); `close` owes a position only when it is non-empty or a block
  exists -- otherwise skips the ladder's `POSITION_ABSENT` and the refresh, keeps
  `AGREEMENT_DISAGREES`/`DISCUSSION_UNANSWERED`, binds the empty sequence, reports
  `positionOwed: false`; `POSITION_ABSENT` detail names the declared flow. `settle --done
  --unwitnessed --reason` ticks a witness-less line, logging reason+session in the ledger event
  (keys only on that act); `agreements_state` adds `witness.decided` (ledger-joined by holder path +
  exact text) and `witness.handTicked`, both only when non-empty, neither counted witnessed. New
  codes `SETTLE_UNWITNESSED_CONFLICT`, `SETTLE_WITNESS_PRESENT` (invocation), `SETTLE_REASON_REQUIRED`
  (work state, question). Roster 124 -> 127 (53 -> 55, 71 -> 72), docs counts moved. No migration:
  all new keys additive and legacy hand ticks read as before.
  Tests: `CloseWithoutDeclaredFlowTests` (6), `SettleDoneUnwitnessedTests` (9) RED 19F -> GREEN;
  experimental `SettleDoneUnwitnessedSiblingTests` (2, written after the engine change, proven by
  mutation). Two existing tests encoded the defect on a no-flow box (`CloseCommandTests` absent
  subtest, `RefusalPayloadPublishesItsExitTests` work-state test) -- now declare a job folder.
  Mutations: holder key dropped -> 1 red; jobs ignored -> 1 red; witness-present check off -> 1 red;
  decided read off -> 1 red; reason check off -> 2 red. Domain-lock pins unchanged (rewording).
  Seals: `close-e1` (both corpora) +174 bytes = the new detail text only; experiments `propose`
  timestamp noise reverted.
  Commit: `fix(implementation): close needs no position without a flow, and witness-less agreements close by record` (the commit carrying this line)

## Next step

A6 next. Common writer rules: scratchpad common.md (mirrored in each delegation prompt).

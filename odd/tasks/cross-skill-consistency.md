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
- [x] A6 — deliberation validation parity (code spans) (D, writer trigger: 3 engine files + 5 test files + 4 docs)
- [x] A7 — shared experiment heading convention (D, writer trigger: 2 profiles + engine + resolver + 2 TS + 3 test files + 4 docs)
- [x] A8 — per-lineage `__implementation__` binding (verify) (D, writer trigger: engine + 2 test files + 2 docs)
- [ ] D1 — kit provenance record + dirty-kit guard
- [ ] D2 — migration support policy
- [ ] D3 — engine state gitignore decision
- [ ] D4 — plausibility metadata cache inside sota-pool
- [ ] D5 — no bytecode in kit copy
- [ ] B1–B13
- [ ] C1–C14
- [ ] E1–E10
- [ ] F — final verification: full suite, E2E smoke, upgrade fixture, outcome table

## Found along the way (to resolve before F)

- X1 — `derive_successor` refuses deleting a document's first section (single newline after artifact marker); pre-existing, now visible at preview (found in A6).
- X2 — `skills/experimental-deliberation/references/usage.md` says `## Paper Guide Reference`; renderer writes `## Reference Sources` (found in A6).
- X3 — `tests/test_implementation_pair.py` mutates the real engine file in place; flaky under parallel runs (found in A2).
- X4 — unguarded legacy deliberation `write` action publishes without candidate validation (found in A6; not a deliberation entry point).

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
- A6 (real): `validateStandaloneAtxMarkers` read a backtick code span as a fused heading, and the
  three points ran three validation sets (v1: canonical form only; preview: `candidate-validator.ts`
  only; accept: `derive_successor`'s full pre-publish set). Fix: `maskInlineCodeSpans` (CommonMark,
  one line, exact-length close, backslash escapes, non-`#`/non-space placeholder) before the fused
  test; `validateSuccessorManifest` factored out of `deriveSuccessorProposal` and exported as
  `successorCandidateRefusal` (dry run, same source bytes/digest/patches), joined into
  `validateCandidate`'s `ok` (`results.prePublish`, `candidateValidation`, `prePublishApplicable` --
  false only for a marker-less in-memory state); `initialCandidateRefusal` (= `validateInitialCandidate`)
  run by `InitialRevisionCreationService` -> `INITIAL_REVISION_CANDIDATE_VALIDATION_FAILED`, projected
  with `nextAction: repair_candidate_markdown`. Audit: after the fix the only accept-only checks are
  state/IO ones (collision, staleness, source ownership); flat-domain definitions are relative to a
  predecessor (not applicable at v1). Not unified: the unguarded legacy `write` action publishes
  without candidate validation (not a deliberation entry point); deleting the FIRST section is refused
  by `derive_successor`'s block-boundary check (marker line + one newline) -- pre-existing, now
  surfaced at preview; one composite-successor test switched to deleting the last section.
  Tests: `tests/deliberation-validation-parity.test.mjs` (10, both skills; RED 8F -> GREEN),
  `proposal-workspace.test.mjs` code-span cases (9), `experimental-deliberation-initial-revision`
  public-surface cases (2; RED 1F -> GREEN). Mutations: no mask -> 7 red; space placeholder -> 1 red;
  no escape handling -> 1 red; any-length close -> 2 red; preview skip -> 2 red; v1 skip -> 2 red.
  Domain-profile lock "proposal" residue 169 -> 171 (+`candidate-validator.ts`): two module
  specifiers, recorded in the test. No migration; no seal change.
  Checks: typecheck clean; test:node 702/702; test:fast 3241 passed.
  Commit: `fix(deliberation): one validation verdict at v1, preview and accept; code spans are not headings` (the commit carrying this line)
- A7 (real): experimental-implementation located experiments only by `^## (\d+)$` and counted only
  digit prose citations; experimental-deliberation writes `## Experiment [exp:E1]` and `(Exp. E1)`.
  Fix: one convention file `skills/_core/conventions/experiments.json` (identifier, `declares`,
  `cites`, `proseReference`), read by `experimental-deliberation/experiment-convention.ts` (own
  module: reading it inside `reference-experimental.ts` raced the profile load through
  `domain-profile.ts`) and by `experimental-implementation/impl_profile.py`
  (`EXPERIMENT_CONVENTION`). Locator: any heading carrying `[exp:<id>]`, block to the next heading
  of same/higher level; legacy `## N` (bare, or wrapping `[exp:EN]`) still read. New optional
  `block_locator.block_aliases` (resolver: bool when declared; off by default -> proposal unchanged):
  ids one block declares together are one locus in `compose`. Citation pattern group 1 = shared
  prose form, groups 2-3 = legacy digits. `[claims:N]` crossings unchanged. Migration: reader-side
  compatibility only (no revision/artefact shape change; provenance ids are echoed, never checked).
  Tests: `SharedExperimentConventionTests` (17; RED 7F -> GREEN), node shared-file test (mutations:
  hardcoded marker / hardcoded prose -> red). Mutations: aliases off -> 1 red. Re-anchored (approved):
  `tests/test_experimental_implementation_mutation.py` `MUTATIONS["findings.citation_pattern"]`
  (pinned the old literal). Domain-lock pins unchanged (two comments reworded). Seals unchanged.
  Checks: typecheck clean; test:node 703/703; test:fast 3262 passed.
  Commit: `fix(experimental): one experiment heading convention shared by both experimental skills` (the commit carrying this line)
- A8 (real, verified by reproduction): both hosts read `src/<Package>/__init__.py`'s single
  `__implementation__`; `revision` was read as the loading host's document 0. Measured on a generic
  target: bound to `r01.md`, experimental `verify` -> `fidelity: unknown`, `latestRevision: None`;
  bound to `experiments-x-v01.md`, proposal `verify` -> the same. The "benchmark" binding is not a
  separate declaration (`benchmark.revision` = `__implementation__["revision"]`). Engine never writes
  the value (agent/human authors it). Fix: `_unbound_after_lineage` in the one reader
  (`resolve_implementation_declaration`) narrows a mapping to `DOCUMENTS[0]["label"]` (mapping kept as
  `revisionByDocument`); bare string = this host's document 0 (unchanged under both hosts); missing
  label -> unanswered revision (undeclared with empty premises, detail names the label; else
  `OBJECT_MAP_NOT_APPROVED` names `revision`); non-string under the label -> undeclared. Template
  comment derives directory and label from the profile (was hardcoded `proposals/`); value stays
  `""`. No workspace migration (declarations live in targets under `implementations/`).
  Tests: `PerLineageImplementationBindingTests` (4, experimental; RED 3F against HEAD),
  `ResolveImplementationDeclarationTests` +5 (proposal; RED 5F against HEAD). Domain-lock pins unchanged
  (wording adjusted). Seals unchanged. No re-anchored tests in A8.
  Checks: related suites 2047 passed; test:fast 3268 passed.
  Commit: `fix(implementation): each skill binds its own document lineage in __implementation__` (the commit carrying this line)

## Next step

D1 next. Common writer rules: scratchpad common.md (mirrored in each delegation prompt).

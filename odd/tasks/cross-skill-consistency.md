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
- [x] D1 — kit provenance record + dirty-kit guard (D, writer trigger: 7 src files + build-kit + 4 scripts + tests + 4 docs)
- [x] D2 — migration support policy (I within this writer: docs only)
- [x] F-prep — populated v0.13.0 workspace fixture + upgrade test (D, writer trigger: generator + fixture + test + src fix + docs)
- [x] D3 — engine state gitignore decision (D, writer trigger: generators + manifest + upgrade + template + 2 test files + docs)
- [x] D4 — plausibility metadata cache inside sota-pool (D, writer trigger: paper_cli + paper_resolve + 2 agents + 2 SKILL.md + test)
- [x] D5 — no bytecode in kit copy (I/D within this writer: 2 src files + 1 test file + docs)
- [ ] B1–B13
  - [x] B1 — section labels in `verify` drift (D, writer trigger: engine + resolver + 2 profiles + convention + 2 test files + 4 docs + seal)
  - [x] B4 + X6 — settle ordering, reverse heading, tick correction path (D, writer trigger: impl_position + engine + 3 test files + 3 docs)
  - [x] B8 — attainedLevel bounded by the aim when nothing leveled ran (D, writer trigger: impl_position + engine + 2 test files + 2 docs)
  - [x] B10 — prose check skips engine-written holder structures (D, writer trigger: engine + test + doc)
  - [x] X8 — launchers refuse a sibling's inherited profile; profile test stops leaking it (D, writer trigger: 2 launchers + test + 3 docs)
  - [x] X3 — D5 mutation test runs on a scratch engine copy (D, same writer: 1 test file + CHANGELOG)
  - [x] B7 — executed kit notebooks are not structure drift (D, writer trigger: engine + test + 2 docs)
  - [x] B11 — step digest scope kept and stated on every unmeasured `@step` item (D, writer trigger: engine + test + 2 docs)
  - [x] B12 — cost forecasts state the parallelism of their duration (D, writer trigger: engine + test + 2 docs)
  - [x] B3 — `RESOLVE_TARGET` matches whole heading tokens; level marks name an outer section (D, writer trigger: resolver + gate + CLI + 2 SKILL.md + 2 usage.md + 3 test files)
  - [x] B13 — successors flag an inherited link to another revision's companion artifacts (D, writer trigger: naming + orchestrator + projection + types + 3 docs + test)
  - [x] B2 — `papersmith status` stage from engine receipts (D, writer trigger: status.py + test + README + CHANGELOG)
  - [x] B5 — fresh target clean through env/plan/apply/materialize (D, writer trigger: engine + forge harness + 2 SKILL.md + usage + new test file)
  - [x] B6 — declared array backend, neutral kit helpers, env torch variants (D, writer trigger: engine + 3 kit files + 2 SKILL.md + usage + 2 test files + seals)
  - [x] B9 — default run profile resolves the target and its venv (D, writer trigger: executor + template + README + test)
  - [x] X8c — launcher refuses a sibling profile from any skills tree (D, writer trigger: 2 launchers + test + 2 docs)
- [ ] C1–C14
  - [x] C4 — v1 headings drop terminal punctuation; derivation documented (D, writer trigger: renderer + 3 test files + 4 docs)
  - [x] C1 — instruction cap enforced on the CLI, documented, `instructionBudget` (D, writer trigger: workspace + test + 4 docs)
  - [x] C6 — `CREATE_INITIAL_REVISION --dry-run` (D, writer trigger: creation + workspace + cli + test + 4 docs)
  - [x] C2 — source window reported, warned, widenable (D, writer trigger: workspace + test + 4 docs)
  - [x] C3 — declared parameters table (D, writer trigger: preservation + test + 2 docs)
  - [x] C7 — successor receipt `rationale`/`decider` (D, writer trigger: workspace + orchestrator + types + test + 4 docs)
  - [x] C5 — `ADOPT_INITIAL_REVISION` rename + record (D, writer trigger: creation + renderer + receipt + workspace + cli + 2 tests + 4 docs)
  - [x] C9 — explicit empty ruling `admit --no-findings` (D, writer trigger: engine + test + 2 docs + 2 re-anchored tests)
  - [x] C8 — prose findings via `remedy_in_prose` (D, writer trigger: engine + 2 kit files + test + 3 docs)
  - [x] C10 — remedy control detection follows attributes and helpers (D, writer trigger: engine + test + doc)
  - [x] C14 — `[out-of-scope:<id>]` subtracted from `agree`'s untested (D, writer trigger: engine + resolver + profile + convention + test + 3 docs)
  - [x] C13 — `paper-ingestion --force-ocr` / `force_ocr` (D, writer trigger: script + 2 test files + SKILL.md + README)
- [x] E1–E10
  - [x] E4 — `walk --commit-template` (D, writer trigger: engine + new test file + 3 docs)
  - [x] E5 — `status`/`audit` collect projection notes; `--verbose` prints them (D, writer trigger: 3 src files + new test file + README)
  - [x] E6 — (completed by E6a/E6b below) partial: `check_atlas.py --pool` quote fidelity + resolver limits documented (D, writer trigger: script + test + SKILL.md); arXiv/Crossref year fix and grapher command wiring blocked on edit surface
  - [x] E2 — holder name in proposal-implementation docs (inline: 2 doc files + drift test)
  - [x] E3 — sealed set documented + refusal lists it (inline: engine + 2 docs + test)
  - [x] E1, E7, E8 — implement bridge coverage + alias note; absolute profile; session ids (inline/serial: bridge + test + 4 docs)
  - [x] E6b — grapher agent runs check_atlas with --pool (inline: agent + projections + test)
  - [x] E6a — arXiv/Crossref year (inline: resolver + test + SKILL.md)
  - [x] E9 — inline fallback section in 8 delegating skills (inline: 8 docs + drift test)
  - [x] E10 — `papersmith ingest` non-PDF refusals name the deliberation seeding routes (D, resumed after interruption: ingest.py + test + SKILL.md + README + CHANGELOG)
- [ ] F — final verification: full suite, E2E smoke, upgrade fixture, outcome table

## Found along the way (to resolve before F)

- [x] X1 — `derive_successor` refuses deleting a document's first section (single newline after artifact marker); pre-existing, now visible at preview (found in A6). Fixed; see Progress.
- [x] X2 — `skills/experimental-deliberation/references/usage.md` says `## Paper Guide Reference`; renderer writes `## Reference Sources` (found in A6). Fixed; see Progress.
- X3 — `tests/test_implementation_pair.py` mutates the real engine file in place; flaky under parallel runs (found in A2).
- X4 — unguarded legacy deliberation `write` action publishes without candidate validation (found in A6; not a deliberation entry point).
- X5 — one `upgrade` across a release left the routing docs naming the old version (rendered before the
  marker moved), so `audit --check-drift` reported generator drift until a second upgrade (found in F-prep;
  fixed there).
- X6 — `settle --under "## Ladder"` (the documented example) on a fresh holder inserts the item at the first
  non-blank line after the heading, which is inside the position block that `position` installs directly
  under `## Ladder`; the holder then no longer parses (`verify` -> `POSITION_ITEM_MALFORMED`). Reproduced on
  0.13.0 and on the current engine (found in F-prep; engine `skills/_core/implementation`). Fixed with B4.
- X7 — 0.13.0 only (fixed by A2): with `AGREED.md` holding a plain item, the experimental skill refused
  `position` with `HOLDER_UNDECLARED`; the fixture creates both holders before settling for that reason.
- X8 — test-order leak, pre-existing on 445756a (found in B1-B10 verification): running
  `tests/test_implementation_profile.py` before `tests/test_upgrade_v0_13_0_workspace.py` in one process
  fails `test_each_implementation_skill_still_reads_its_own_holder[experimental-implementation]` (it reads
  `AGREED.md`): a profile test leaves `IMPLEMENTATION_DOMAIN_PROFILE` in `os.environ`, the fixture test passes
  `os.environ` to the experimental CLI, and the launcher only `setdefault`s it. Each file passes alone; the
  change-selected `npm run test:fast` tier hits it. Not fixed (outside B1/B4/B8/B10).
- [x] X8b — the change-selected tier (`fast_tests.py --since 8e3f813`, 23 files, one process) still failed
  `test_each_implementation_skill_still_reads_its_own_holder[experimental-implementation]` after X8. Fixed; see Progress.
- [x] X10 — `tests/test_implementation_core.py` and `tests/test_proposal_implementation.py` run together under
  `-n 8 --dist loadfile` interfere: `WorkspaceGuardTests.setUp`'s `implementations/_core_guard_*` directory
  vanishes (`FileNotFoundError`), and one such run errored 1801 proposal tests at setup. Reproduced with the
  B12 changes stashed (found in B12). Each file passes alone. Same family under `-n 8 --dist loadfile`
  with `test_proposal_implementation.py` in the run: `test_experiments_seal.py`'s `verify-a` case
  intermittently prints nothing (`HolderRenameDeclaredDeltaTests`) or a different digest
  (`ThreatMatrixTests::test_a_stray_parent_env_var_produces_an_identical_digest`); the file passes alone
  (29 passed). Its scratch target also lives under `implementations/`. Fixed; see Progress.
- Fixture script: `scripts/build-v0_13_0-fixture.py`'s `--under "# Agreed"` comment now says it keeps the
  0.13.0 heading on purpose and that X6/B4 fixed `## Ladder` in 0.14.0 (comment only; fixture not
  regenerated). Commit: `docs(fixture): the 0.13.0 settle workaround comment names the 0.14.0 fix`.
- [x] X9 — `verify` crashes (traceback, exit 1) when a file under `<Name>/Notebooks/` is not valid JSON:
  `notebooks_state` calls `notebook_seals(json.loads(...))` unguarded (found in B7). Fixed; see Progress.

- [x] X11 — README `experimental-implementation` section gave stale line counts for the launcher (24; real 65)
  and profile (278; real 352). Counts dropped; launcher row names the sibling refusal (inline: README + CHANGELOG).
- [x] X12 — `upgrade-project` SKILL.md does not describe the `.gitignore` marked framework block (since ec06f30).
  Section added (inline: SKILL.md + CHANGELOG).
- [x] X13 — deliberation refusal `INITIAL_IDEA_SINGLE_SENTENCE` says "Provide a non-empty idea".
  Own message naming the two-sentence requirement (inline: engine + test + CHANGELOG).
- [x] X14 — the deliberation bridge has no route to `ADOPT_INITIAL_REVISION` (since 340dc26).
  `--action adopt` added (inline: bridge + test + README + CHANGELOG).
- [x] X15 — (found in F; fixed, see Progress) experimental-deliberation v1 pastes `proposals/` revisions verbatim, and every managed
  proposal revision carries the reserved `proposal-workspace:artifact` marker. Since A6, v1 runs the pre-publish
  validation, so `CREATE_INITIAL_REVISION` is refused `INITIAL_REVISION_CANDIDATE_VALIDATION_FAILED`
  (`initial-candidate-limit`) whenever a managed proposal falls inside the source window, which is the normal flow;
  the message says to repair a source that cannot be repaired. On main the same call created a v1 holding the pasted
  markers, and no successor could ever be accepted from it (`continuity-source-unowned`). The 0.13.0 fixture's
  `experiments-smoothing-window-sweep-v01.md` holds 2 pasted markers, so after upgrade its lineage cannot take a
  successor (preview answers a bare `CANDIDATE_VALIDATION_FAILED`, `nextAction: inspect_error`). Workaround seen in F:
  `sourceWindowBytes` small enough to leave `proposals/` unread. See "Final verification".
  Fix (route D, delegated writer; trigger: engine + 2 tests + 4 docs): the source window neutralises every reserved
  marker it loads (`neutralizeReservedMarkers`: marker comment lines removed, other reserved-name occurrences
  defanged, NUL dropped; `sourceWindow.sources[].reservedMarkersRemoved`), for both deliberation skills and a chat's
  first turn. Validation unchanged and fail-closed. Legacy v1 (bytes untouched): a successor keeping copied markers is
  refused `successor-copied-artifact-marker` naming the enclosing sections and the repair; read-only patch fields
  (`oldText`, `anchor`) and the accept turn's continuity read accept exact copied marker lines only, so a successor
  replacing those sections is published. Preview pre-publish refusals now carry `nextAction: repair_candidate` and a
  blocker. Chosen over engine-side automatic stripping because that would make the written candidate differ from the
  previewed patches and the untouched-region invariant. Tests: `tests/deliberation-source-reserved-markers.test.mjs`
  (6; RED observed for the fresh experiments/proposal paths and the legacy refusal/repair), and
  `tests/test_upgrade_v0_13_0_workspace.py::...::test_the_experiments_revision_takes_a_successor_after_upgrade` (RED
  with the engine stashed: `inspect_error`; GREEN: refused with both `-r01.md`/`-r02.md` sections named, then the
  two-section repair published with one marker). Mutation: reverting the continuity read turns the repair test red.
- [ ] X16 — (found in F, open) on a target both implementation skills share, each skill's aggregate `fidelity.status`
  is `drift`: a module bound to the other skill's lineage is listed under `staleModules` with "bound to an older
  revision, but none of its sections moved", while `fidelityByDocument` is `ok` for both documents. Not checked
  against main.
- X17 — (found in F, pre-existing on main, verified) a `position` refused `POSITION_TARGET_LEVEL_REQUIRED` (exit 2)
  still creates the empty holder skeleton (`# Agreed` / `## Ladder`).
- X18 — (found in F) `settle --done --unwitnessed` needs the line to exist already, and placing a new line needs
  `--about` (a discussion). A scoping decision with no position sequence therefore has no command route to its
  line, which has to be written by hand at the gate. Not a refusal defect; a documentation gap to triage.

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

- D1 (real): `kit.resolve_kit_origin` names the branch (`override`/`checkout`/`bundled`); new
  `core/provenance.py`: `describe` (built kit -> `kit-manifest.json` `commit`/`dirty`; source tree ->
  `git rev-parse HEAD` + `git status --porcelain --untracked-files=all` over KIT_ENTRIES +
  `src/papersmith`), `require_admissible` (dirty -> refuse; unknown source tree -> refuse; built kit
  without provenance admitted, commit null), `write_record`/`read_record`. `init` decides before
  creating the destination; `upgrade` before the downgrade guard (`--plan-migrations` exempt, writes
  nothing). Record `.papersmith/kit-source.json` written after the manifest on every init/upgrade;
  `status` `framework.kit_source` + `Kit source:` line; legacy -> "unknown (recorded before 0.14.0)",
  upgrade writes it (no migration). `--allow-dirty-kit` on init/upgrade, MCP `allow_dirty_kit` on
  both tools, env `PAPERSMITH_ALLOW_DIRTY_KIT=1` (set in tests/conftest.py; Node harnesses pass the
  flag). `build-kit.py` embeds commit/dirty. Maintainer scripts that build from the working tree pass
  the flag (user-approved surface): sync-repo-harness.py, cli-paper-smoke.sh,
  cli-paper-wiring-smoke.sh, cli-paper-live-smoke.sh. CI: test.yml runs pytest (conftest override);
  publish.yml builds the kit from a fresh checkout and inits from the wheel (bundled, clean) -- no
  caller there hits the refusal.
  Tests: `tests/test_kit_provenance.py` (24; RED = ImportError, module absent -> GREEN). Mutations:
  dirty refusal off -> 8 red; unknown refusal off -> 3 red; untracked ignored -> 1 red; env override
  off -> 1 red. Re-anchored: `test_papersmith_upgrade.py:236`, `test_upgrade_migrations.py:79`
  (`upgrade_module.resolve_and_validate` -> `kit_module.resolve_and_validate`; upgrade no longer
  imports it). Checks: related files 322 passed; test:fast 2103 passed; node harness files 17/17,
  0 skipped; `sync-repo-harness --check` clean; wiring + offline smokes rc=0 on the dirty checkout
  without the env var (temporary `.venv` link, removed).
  Commit: `fix(init): record which kit a workspace came from and refuse a dirty one` (the commit carrying this line)

- D5 (real): `bridges.python.run_script` and `core.executor` (`_local_job`, the Kaggle submit
  child) inherited `os.environ` unchanged; a bridged script importing a sibling left
  `skills/<skill>/scripts/__pycache__/` in the workspace. New `script_environment(extra)` sets
  `PYTHONDONTWRITEBYTECODE=1` (caller `extra` applied last) and backs all three sites; the ssh
  branch is left alone (ssh forwards no environment). MCP bridge and UI child already set it.
  Tests: `tests/test_no_bytecode_in_workspace.py` (4) RED 4F (child saw `None`/`False`; env key
  missing) -> GREEN, including a real bridged run asserting no `__pycache__` anywhere under the
  workspace. No migration.
  Commit: `fix(bridges): scripts the CLI launches write no bytecode into the workspace` (the commit carrying this line)

- D2 (real): the 0.8.0 CHANGELOG note told users to re-init. Verified what `upgrade` accepts:
  any orderable recorded version <= kit (files + convergence migrations); missing marker proceeds,
  gated migrations `undetermined` (`test_a_workspace_with_no_recorded_version_is_never_a_downgrade`,
  `test_a_missing_recorded_version_leaves_a_gate_undetermined`); unorderable or newer marker refuses
  unless `--allow-downgrade` (`test_versions_that_cannot_be_ordered_refuse_rather_than_guess`).
  REGISTRY today holds only convergence migrations; `RETIRED_STATIC` retires only `PI.md`, so
  0.8.0's `.antigravity/` files survive upgrade. Policy written: supported floor 0.12.0 (first
  release with artifact migrations); from 0.14.0 every shape change ships a migration or a
  compatibility read in the same release, stated under Behaviour changes; re-init never the answer.
  Files: `docs/releasing.md` ("Workspace support policy"), `skills/upgrade-project/SKILL.md`
  ("Which workspaces can be upgraded"), README.md (upgrade paragraph), CHANGELOG 0.14.0 `### Changed`
  (0.8.0 entry untouched). No test: the policy is a release obligation, not runtime behaviour; the
  runtime claims it repeats are already pinned by the tests named above.
  Commit: `docs(upgrade): a live workspace is upgraded, never re-initialized` (the commit carrying this line)

- D1/D5/D2 full-suite check (after 4d0071b-equivalent tree): `npm run test:node` 703/703, tree clean
  afterwards; `npm run test:py:par` 5969 passed, 13 skipped, 3 failed -- all `.venv/bin/python`
  absent on this machine (the two known ones plus `UsageReferenceTests::
  test_every_documented_invocation_runs` subtest for the self-guarded-facts inversion, which exits 2
  with the same `.venv` error on base 0426dbc too).

- F-prep (fixture, plus finding X5 fixed): `scripts/build-v0_13_0-fixture.py` extracts `git archive 55dcb4e`
  (0.13.0, untagged) and drives that tree's own CLI/engines: `init --no-env --no-npm`, proposal v1 + one
  successor (`--serve` resolve/preview/accept), experiments v1, target `implementations/Smoother` (`plan`,
  `materialize --stage scaffold --seed 7`, both skills' `position --sequence` installs, `discuss` Q+A,
  `settle`). Snapshot = workspace minus manifest-baselined untouched framework files (+ `.gitignore`,
  version marker always kept), stored as deterministic `workspace.tar.gz` (43 KB, 54 members incl. the
  target's `.git`) + `contents.sha256`; an archive because the workspace's own `.gitignore` would hide
  content from this repo's git. Documented in `tests/fixtures/README.md` and `docs/releasing.md`.
  Test `tests/test_upgrade_v0_13_0_workspace.py` (8 tests): RED on the current branch = 1 failure,
  `audit --check-drift` -> `generator drift: CLAUDE.md, OPENCODE.md, .pi/APPEND_SYSTEM.md,
  .agents/AGENTS.md` (also reproduced on a full, unstripped 0.13.0 workspace). Fix: `upgrade` re-renders
  the generated files once the version marker moves. GREEN 8/8; digests: only `.papersmith/{config.json,
  manifest.json,version}` change; both migrations satisfied; consistency audit PASS (both domains); both
  `verify` runs read their own holder. Related upgrade files 78 passed.
  Commit: `fix(upgrade): one upgrade of a populated 0.13.0 workspace ends drift-clean` (the commit carrying this line)

- D3 (real, plus a sibling): decision = engine state is content. Derived from code: every root-level
  engine dir is a deliberation `artifact.sidecarRoot` (`.proposal-deliberation`, `.experimental-deliberation`);
  paper-writing (`paper/.paper-writing`), implementation/remote-execution (`implementations/<t>/...`),
  plausibility (`sota-pool/`) and the kaggle store (own `store/.gitignore`) already sit under ignored paths.
  `backup/<directory>/` (SKILL.md reconciliation destination) also holds revisions + sidecars. Template now
  ignores all four. Sibling found: `upgrade` re-rendered `.gitignore` wholesale (`apply_generated`), clobbering
  user lines; `status`/`audit --check-drift` reported any user edit as drift. Fix: managed block
  (`generators.MANAGED_BLOCK_*`, `merge_managed`, `managed_view`): upgrade rewrites the block, keeps lines
  outside; drift (check_generated + manifest digest) measured on the block; markerless (<=0.13.0) file replaced
  whole when its digest equals the manifest baseline, else block + every line not already carried kept below;
  malformed markers -> untouched, reported unsynchronized, baseline UNSYNCHRONIZED (stays drift). No REGISTRY
  migration: upgrade's per-run re-render is the convergence (content compare, idempotent).
  Tests: `tests/test_workspace_gitignore.py` (12; profiles read via the engine's `artifact-naming.ts`, engine run
  + `git status`, managed block, 0.13.0 fixture conversions). RED 12F (after constants only) -> GREEN.
  Mutations: keep-outside off -> 5 red; baseline check off -> 1; check_generated view off -> 1; manifest view
  off -> 2; malformed guard off -> 1. Fixture test: `.gitignore` added to `INTENDED_CHANGES`. Related suites
  246 passed. Docs gap (outside surface): `skills/upgrade-project/SKILL.md` does not mention the block.
  Commit: `fix(workspace): engine state is ignored and upgrade keeps a workspace's own .gitignore lines` (the commit carrying this line)

- D4 (real): `cmd_resolve` always cached under `resolve_paper_dir(args.paper)` (default `<root>/paper`), and both
  plausibility agents called it without `--paper`. Choice: a `--cache-dir` flag the callers pass, not "resolve
  never creates paper/": the latter would drop the cache entirely (nowhere in `sota-pool/`) and change
  paper-writing's pre-scaffold behaviour, and a role-derived default is impossible (paper-writing also uses
  `--role resolution`). Doctrine: the requirement is answered through the skill's own documented invocation
  (the agents name the pool they already write into), and the cache key/layout is derived from the one
  `metadata_digest` keying (`cache_metadata_in`; `cache_metadata` delegates via `metadata_dir`). `--paper` and
  `--cache-dir` are an argparse mutually exclusive group; containment reuses `_resolve_repo_path`
  (`PAPER_OUTSIDE_REPOSITORY`), checked before any request. Existing `paper/.paper-writing/metadata/` caches: no
  migration (valid paper-writing caches, unchanged key). Harness agent projections regenerated with
  `scripts/sync-repo-harness.py` (`--check` clean, 95 files).
  Tests: `tests/test_plausibility_resolve_cache.py` (4; invocation parsed from each agent file, run against the
  workspace's shipped `paper_cli.py` with the `OPENER` seam). RED 3F (+1 subtest) -> GREEN. Mutations: cache-dir
  ignored -> 3 red; containment dropped -> 1 red. test:fast 2018 passed, 1 failed (known `.venv` env failure).
  Commit: `fix(plausibility): resolve caches in sota-pool, never starting a paper tree` (the commit carrying this line)

- B1 (real, verified by reproduction): `revision_sections` matched only `^#{1,6}\s+(\d+)[.)]?\s`; on a
  generic revision with `### O1.`/`### O2.` headings it returned `{}` and `changed_sections` `[]`; `### 3.1`
  and label-only `## 3` (the legacy experiments form) were not sections either. The deliberation engine
  imposes no heading form (`document-index.ts` indexes any ATX heading; `initial-revision-renderer.ts`
  emits the idea-derived `##` heading and `### <decisionId>`), so `verify` now recognizes labelled headings
  and `proposal-deliberation` documents the labels. Fix: one convention file
  `skills/_core/conventions/sections.json` (`label` `[A-Za-z]*[0-9]+(?:\.[0-9]+)*`, `closer` `[.):]`), read by
  both implementation profiles and handed to the engine as optional `documents[0].section_heading`
  (experimental adds `marker` = the `[exp:<id>]` heading from experiments.json); resolver validates it
  (`IMPLEMENTATION_DOMAIN_PROFILE_INVALID_SECTION_HEADING`). Nesting: a labelled heading closes open
  sections of the same or a deeper level; deeper labelled headings stay part of their parents line for
  line (parent digest identical to the old reader's, asserted); an unlabelled heading never closes the
  outermost section, only nested deeper ones. The engine first read the JSON itself; 17 mutation tests copy
  only `_core/implementation` into scratch trees, so the read moved into the profiles (the A7 pattern).
  Tests: `SectionHeadingConventionTests` (7, proposal; RED 4F, 3 pins of the old numbered reading),
  `ExperimentSectionsTests` (4, experimental; RED 2F; resolver refusal with 5 subtests; both profiles hand
  over the identical convention). Mutations: no parent lines -> 1 red; unlabelled-closing off -> 1 red;
  marker off -> 2 red; marker group check off -> red. Re-anchored: `SharedExperimentConventionTests.
  _relocated_profile` (scratch tree also needs `sections.json`). Domain-lock pins unchanged (comments
  reworded). Seal: experiments `verify-a-declared`, `verify-b-declared`, `verify-b-undeclared`, `verify-t`
  regenerated via `tests/experiments_seal_capture.py`; output diff = only `changedSections`/
  `touchedSections`/`reason`/`armsReached` (the corpus's bare `## N` sections now read); `propose` timestamp
  noise reverted. `tests/seal` unchanged. No migration (reader-side; no artefact shape change). Upgrade
  fixture test 8/8.
  Commit: `fix(implementation): verify reads the section labels a revision carries` (the commit carrying this line)

- B4 + X6 (real, all four reproduced on a fresh target via the CLI): (a) `locate_headings` returned the
  section's FIRST checklist line, so items read newest first; (X6) on the holder `position` creates, that
  line is the block's own `- [ ] 1.` item, so `settle --under "## Ladder"` wrote inside the block and the
  next `verify`/`settle` refused `POSITION_ITEM_MALFORMED`; (b) `--reverse` refused `SETTLE_HEADING_ABSENT`
  without a hand-written `## Reversed`; (c) nothing un-ticks. Decision: chronological. Fix:
  `impl_position._first_bullet_insertion` now returns the offset past the section's LAST checklist item,
  skipping the position block's lines (`_block_lines`, read from the two markers line by line, never
  refusing); a section whose only items are the block's gets the item past `<!-- /position -->`; prose-only
  sections keep the first-non-blank fallback. No existing line moves (0.13.0 holders keep their
  newest-first run; new items follow it). `cmd_settle`: create path prefixes `\n` when appending past an
  unterminated last line; `--reverse` with no `## Reversed` appends `\n## Reversed\n\n<entry>` at the end
  of the file in the same splice (ambiguity still refuses). (c) is intended and now documented with the
  correction path: `--reverse` works on a ticked line (verified) and a fresh `--under` placement follows;
  docstring paragraphs that argued for the old refusals replaced.
  Tests: `SettleOrderingAndCorrectionTests` (5, CLI end to end incl. `verify` on the fresh holder and a
  0.13.0-shaped holder byte check; RED 5F -> GREEN), `LocateHeadingsTests` +1 (block). Re-anchored (pinned the
  old behaviour): `LocateHeadingsTests.test_a_section_that_opens_with_prose_inserts_before_the_first_bullet`
  -> `..._after_the_last_bullet`, `test_a_bullets_first_section_is_unchanged_by_the_prose_skip` ->
  `..._appends_after_its_last_bullet`, `SettleCommandTests.test_settle_writes_exactly_one_unticked_line_
  byte_identical_otherwise` (expected position), `SettleReverseCommandTests.test_reverse_refuses_heading_
  absent` -> `test_reverse_opens_the_heading_when_absent`. Mutations: block skip off -> 3 red; first item
  instead of last -> 3 red; no block fallback -> 2 red. Domain-lock pins SHRANK deliberately (against,
  command, measured, rather, something; justified in the test). Seals unchanged. Upgrade fixture 8/8. No
  migration (write-side placement only; holder and ledger shapes unchanged). Out of surface, left as is:
  `scripts/build-v0_13_0-fixture.py`'s comment explaining why the fixture settles under `# Agreed` (still
  true of 0.13.0, which builds it).
  Commit: `fix(implementation): settle appends in order, never inside the position block` (the commit carrying this line)

- B8 (real, reproduced on HEAD via the CLI): `__levels__ = ['local','pilot','full']`, one two-state
  `@rehearsal` item, `position --target-level pilot` -> `verify` `position.attainedLevel: 'full'`. Cause:
  `impl_position.attained_level` answered the ladder's top for a sequence with no leveled item (documented
  "vacuous" boundary). Fix: with no leveled item it returns `evidence["targetLevel"]` when on the ladder, else
  `None`; sequences with leveled items unchanged (leveled evidence is what ran). The rung-skip guard is
  unaffected (it compares an aim with this answer); `_position_attained_level` (refusal resolution) now
  passes the block's own target. Consequence (documented under Behaviour changes): `gate`/the launch menu read
  the same value, so an all-two-state position aimed below `levels[-2]` on a 3+ rung ladder refuses
  `RUNG_NOT_ATTAINED` (exit: re-seal at the launch rung, which the skip guard allows).
  Tests: `AttainedLevelNeverOverstatesTests` (1, e2e; RED `'full'` on HEAD via the probe, then GREEN),
  `UnreachableLadderTests.test_an_all_two_state_aim_below_the_launch_rung_does_not_launch` (new).
  Re-anchored (pinned the vacuous top): `AttainedLevelTests.test_a_sequence_with_no_leveled_item_attains_
  the_whole_ladder` -> `..._attains_the_aim_never_more` (RED 3F before the fix),
  `ShardlessRungDiagnosisTests.test_a_two_state_shard_item_is_not_a_rung_fact_at_all` and
  `UnreachableLadderTests.test_dropping_the_level_marker_is_the_other_exit` (evidence now carries the aim, as
  `position_state` supplies it), `LaunchAvailableTests.test_vacuous_attainment_at_the_top_rung_is_sufficient`
  (docstring only). Domain-lock pins unchanged. Seals unchanged. No migration.
  Commit: `fix(implementation): attainedLevel never exceeds the aim when nothing leveled ran` (the commit carrying this line)

- B10 (real; witness-token hit reproduced end to end: position -> discuss -> settle -> `settle --attach
  --witness test_seed_is_seven` -> successor + re-bind -> `verify` `prose.unresolvedSymbols` names
  `test_seed_is_seven` in `Method/AGREED.md`). The engine writes three structures into a holder: the
  position block (its opener names the derived-from revision, which is the stale-revision hit when the
  block was not refreshed), the trailing witness token (`AGREEMENT_LINE`'s `witness` group) and `## Reversed`
  entries. `prose_of` read every `.md` line. Fix: `holder_prose(path)` for `.md` files named by
  `HOLDER_FILENAME` or `sibling_holder_filenames()`: skips the block opener/closer lines, strips the witness
  group from agreement lines (their text still read), skips the `## Reversed` section (to the next `## `
  heading, `_SECTION_BODY`'s boundary). Other files unchanged.
  Tests: `ProseSkipsEngineWritesTests` (3: own holder, sibling holder, identical bytes in `docs/notes.md`
  all reported). RED 2F -> GREEN. Mutations: Reversed skip off -> 2 red; marker skip off -> 2 red; witness
  strip off -> 2 red; blanket file skip -> 2 red (user prose test). Domain-lock pins unchanged (reworded).
  Seals unchanged. No migration (report-only keys).
  Commit: `fix(implementation): the prose check skips what the engine wrote into a holder` (the commit carrying this line)

- X8 (real; reproduced: `pytest tests/test_implementation_profile.py tests/test_upgrade_v0_13_0_workspace.py
  -p no:randomly` -> 1 failed, the experimental skill reading `AGREED.md`). Leak source:
  `LauncherExposesNoEngineAttributeTests._launcher_module` exec'd the launcher in-process, whose `setdefault`
  stayed in `os.environ`. Fix: (1) both byte-identical launchers refuse `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING`
  (exit 2, stderr, before the engine loads) when the inherited value resolves to `<skills root>/<other>/
  impl_profile.py`; any other explicit value (fixture profile) still wins; (2) the test loads the launcher
  under `seeded_profile`, which restores the variable.
  Tests: `InheritedSiblingProfileTests` (5; sibling pairs derived from `skills/*/scripts/implementation_cli.py`)
  and `test_loading_the_launcher_leaves_the_environment_as_it_found_it`. RED 4F -> GREEN; the ordered pair
  run is green (80 passed). Docs: proposal usage.md, experimental SKILL.md, profile docstring ("24 bytes"
  removed). Out of surface, stale: README.md:2412 calls the launcher "24 líneas". No migration.
  Commit: `fix(implementation): a launcher refuses the other skill's inherited profile` (the commit carrying this line)

- X3 (real; `AmbiguousFamilyMutationProvesReachabilityTests.setUp` wrote the mutation into the shipped engine
  and restored it in a cleanup). Fix: setUp copies `skills/_core/implementation` into a scratch forge with the
  real nesting (`impl_layout.FORGE_ROOT` = engine `parents[4]`; target box under `<scratch>/implementations`),
  writes the mutation there, copies the launcher, symlinks `skills/remote-execution`, and runs the scratch
  launcher. New `test_the_real_engine_is_never_rewritten` (sha read at module import + no `MUTATED`):
  RED on the old setUp -> GREEN. Still red under its mutation: writing the unmutated source into the scratch
  engine reddens `test_the_ambiguous_case_silently_succeeds_under_the_mutation` (observed 1 failed).
  `pytest tests/test_implementation_pair.py -n 8 --dist loadfile`: 39 passed, `git diff skills` empty.
  Test-only; no migration.
  Commit: `test(implementation): the D5 mutation runs on a scratch copy of the engine` (the commit carrying this line)

- B7 (real; the drift reader `_kit_structure_gaps` compared full bytes, so an in-place execution of
  `verification.ipynb`/`probe.ipynb` drifted). Fix: `notebook_source_sha256` (ordered cell type + joined
  source; `None` when unreadable); stages, `--authored`, `--adopt` record `writtenSourceSha256` for `.ipynb`
  destinations; `recorded_bytes_match` accepts the full-byte digest OR the source digest; a legacy entry
  (no key) of kind `materialized` rebuilds its kit body (scaffold: recorded SEED; harness) and trusts its
  source digest only if the body hashes to `writtenSha256`; anything else = full bytes only.
  Tests: `ExecutedKitNotebookIsNotDriftTests` (11). RED 6F -> GREEN. Mutations: source dropped from digest
  -> 2 red; cell type dropped -> 1 red; `--authored` not recording -> 1 red; legacy rebuild off -> 2 red;
  rebuild hash check off -> 1 red. `pytest tests/test_proposal_implementation.py -n 8 --dist loadfile`:
  1791 passed, 2 skipped. Domain-lock pins unchanged (reworded). Seals unchanged. Additive key: no migration.
  Commit: `fix(implementation): executing a kit notebook is not structure drift` (the commit carrying this line)

- B11 (real, and the scope is intended): `suite_digest` walks every `.py` under `src/` and `tests/` plus
  `SUITE_ENVIRONMENT_MANIFESTS`; `_step_verdicts` folds a stale digest to `None`, so a test-only edit turned
  every earlier `@step` mark unmeasured with no explanation. Narrowing is not sound: `cmd_step` runs an
  arbitrary `module.function` (`impl_steps.run_step`, cwd = target), which may run pytest, read `tests/`
  or spawn anything; the engine cannot derive what it executes. Kept fail-closed, documented, and stated
  where it is met: `STEP_DIGEST_SCOPE` + `_step_unmeasured_entry` add `reason` (no verdict vs. last run no
  longer counts, with the exact `step` command) and `digestScope` to unmeasured `@step` items (copies; the
  `sequence` entry keeps its shape). Tests: `UnmeasuredStepNamesItsScopeTests` (4; one checks the stated
  scope against `suite_digest` itself). RED 2F -> GREEN. Seals unchanged (no sealed case carries an
  unmeasured `@step`). Domain-lock pins unchanged (reworded). Related files `-n 8 --dist loadfile`: 2050
  passed, 1 failed (`test_experiments_seal.py::...stray_parent_env_var...`, passes alone and with the file;
  a parallel flake, also passes on the stashed base). No migration (additive keys).
  Commit: `fix(implementation): an unmeasured step mark names its digest scope` (the commit carrying this line)

- B12 (real): `_projected_cost` (behind `probe`'s `search.costForecast` via `search_cost_forecast` and the
  benchmark's `projectedCost`) scaled `reduction.seconds`/`wallSeconds` linearly with no notion of
  concurrency; the kit `probe.ipynb` harness times seeds in one process. No pilot measurement of
  parallelism existed anywhere. Fix: `_projection_parallelism` adds `parallelism`/`contention`/`basis`:
  a record whose `reduction.parallelism` is a positive int -> that value, `contention: "included"`
  (projection holds at that parallelism only); otherwise `parallelism: null`, `contention: "unmeasured"`,
  `basis` = single-process, and no contention factor invented; a malformed value is echoed as
  `parallelismMalformed`. Tests: 4 in `DistributionTests` (one subTest per malformed shape). RED 9F -> GREEN.
  Mutations: bool guard off -> 1 red; labelling dropped -> 2 red. Seals unchanged. Domain-lock pins
  unchanged (reworded; the literal `included` avoids moving the `measured` pin). `pytest
  tests/test_proposal_implementation.py` (single process): 1799 passed, 2 skipped; seal files 73 passed;
  `test_implementation_core.py` alone 139 passed. No migration (records are read, never rewritten).
  Commit: `fix(implementation): a cost forecast states the parallelism it was taken at` (the commit carrying this line)

- B3 (real): `resolveSuccessorTarget` tested each query word with `heading.includes(term)` (substring; `O1`
  hit `O10`), gave an exact heading no edge over a longer one carrying the same words, and
  `collapseNestedSuccessorCandidates` always dropped an outer candidate containing another, so `## Data`
  was unreachable once `### Synthetic data` existed. Fix (`target-resolver.ts`): tokens per heading
  (dotted identifiers whole; hyphen/underscore parts added), exact-heading bonus `EXACT_HEADING=6` (over
  the gate margin of 4; label stripped via `_core/conventions/sections.json`, stopwords ignored), a
  leading `#{1,6} ` makes the query level-restricted and literal, collapse removed (gate decides; ties
  block), ties ordered by document position. `ambiguity-gate.ts` prints `<level marks> <real path>` and
  an outer-section hint when candidates nest; `cli.mjs` returns `candidates` on a blocked locus.
  Non-successor `resolveTargets` (entry ids, labels, tags) untouched. Tests:
  `tests/deliberation-heading-target.test.mjs` (13; RED 11F on the base -> GREEN). Mutations: substring
  back -> 3 red; bonus 0 -> 4 red; level filter off -> 1 red. Re-anchored:
  `proposal-deliberation-v2-successor-acceptance-e2e.test.mjs` (pinned innermost collapse: bare
  `Framing` now names `# 2 Framing`; query is `Framing average`), and
  `proposal-deliberation-v2-revision-lifecycle.test.mjs` (copies the engine alone; now also copies
  `_core/conventions`, as the kit ships it). `npm run test:node`: 716 passed. `npm run test:fast`: 3237
  passed, 1 failed (`test_upgrade_v0_13_0_workspace.py::...reads_its_own_holder[experimental-implementation]`
  reads `AGREED.md`: an implementation-profile leak between files in that run; the file passes alone, 8
  passed, and with each implementation test file in turn; the identical 23-file selection on the base
  8e3f813 fails the same subtest, so it predates B3/B13/X1/X2). No
  migration (resolution only; a blocked result gains an additive key).
  Commit: `fix(deliberation): a locus query matches whole heading words and can name an outer section` (the commit carrying this line)

- B13 (real): no code writes the companion-picture line. `proposal-deliberation/SKILL.md` ("The graph")
  has the deliberation link `proposals/<revision>.graph.html` from the revision's own text, and
  `deliberation-publish` renders it; plausibility's grapher only writes `sota-pool/atlas.html`. A successor
  copies every byte outside its locus, so the link kept naming the source's picture. Fix (flag, never
  rewrite or regenerate): `artifact-naming.ts` `scanCompanionReferences` (stem + revision + any suffix but
  `.md`, built from the profile's naming parts) and `staleCompanionReferences` (references naming a
  revision other than the successor; `inherited` = present in the source); `orchestrator.publish` adds
  `staleCompanionReferences` to the preview, the published result and the receipt (key only when
  non-empty); `proposal-workspace.ts` projects it on both public results. Tests:
  `tests/deliberation-stale-companion-reference.test.mjs` (4; RED 2F -> GREEN; the receipt carrying the key
  is read back through `loadDerivedState`). Mutations: own revision not excluded -> 1 red; `.md` counted
  -> 1 red; `inherited` constant -> 1 red. Docs: proposal SKILL.md (graph section), both usage.md.
  `npm run test:node`: 721 passed (2 failing = the uncommitted X1 RED file). `test_upgrade_v0_13_0_workspace.py`:
  8 passed. No migration (optional receipt key; old receipts validate unchanged).
  Commit: `fix(deliberation): a successor flags an inherited link to another revision's companion artifacts` (the commit carrying this line)

- X1 (real, reproduced with a generic three-section document): deleting `# 1 Intro` refused at preview with
  `CANDIDATE_VALIDATION_FAILED` / `successor-markdown-block-safety` ("fuses Markdown blocks"); deleting the
  middle section passed. Cause: `validateSuccessorManifest`'s removal join wants `\n\n` across
  `before`/`after`, and `before` is the artifact marker, which ends in one `\n`. Fix
  (`proposal-workspace.ts`): a removal whose `before` is exactly `ARTIFACT_MARKER` is a clean join; every
  other left side keeps the blank-line rule. Tests: `tests/deliberation-first-section-delete.test.mjs` (3:
  publish of a first-section delete with exact bytes; the bare manifest check admits it and still refuses
  the same join after prose, also at preview; middle deletion unchanged). RED 2F -> GREEN. Mutation (admit
  any left side ending in `\n`) -> 1 red. Docs: both usage.md Delete sections. `npm run test:node`: 723
  passed. No migration.
  Commit: `fix(deliberation): a successor can delete the document's first section` (the commit carrying this line)

- X2 (real): `usage.md:103` named `## Paper Guide Reference`; `initial-revision-renderer.ts` writes
  `DOMAIN.artifact.sourceReferenceHeading`, which the experimental profile declares as `Reference Sources`
  (SKILL.md already agreed). No other heading in usage.md drifted (only the engine-written `## Changes`,
  which matches the profile's change header). The drift test can catch this class, so it was extended:
  `experimental-deliberation-usage-doc-drift.test.mjs` keeps the v1 the worked example renders and checks
  every prose ``"`## X` heading"`` / ``"`## X` block"`` claim in usage.md and SKILL.md against that v1's
  heading lines and the profile's `changeHeader` (placeholders such as `### <path>` skipped). RED on the old
  doc (names `## Paper Guide Reference`) -> GREEN after the doc fix; mutation (`## Changes` block renamed in
  the doc) -> red. No code change, no migration.
  Commit: `docs(experimental-deliberation): the usage guide names the heading v1 writes` (the commit carrying this line)

## Next step

D3 next (D1, D5, D2 done). Common writer rules: scratchpad common.md (mirrored in each delegation prompt).

- X9 (real; reproduced RED: `verify` exit 1 with a traceback for 4/4 subtests -- `{ not json` at
  `notebooks_state`'s seal read, `[]` and `"a string"` at `prose_of`'s `.get` on a non-mapping, `\xff\xfe` at a
  UTF-8 decode). Siblings found by the same derivation: `notebook_execution`, `notebook_sources` and
  `_notebook_cells` caught the decode errors but crashed on a non-mapping top level. Fix: one shared
  `read_notebook_document` (UTF-8 JSON with a mapping at the top level, else `None`) used by all four readers;
  `prose_of` skips a non-mapping document or cell. Fail-closed: the file reads `unreadable`, `sealed: false`,
  `sourcesMatch: null`, listed in `unsealed`, notebooks `drift`, validation `incomplete`.
  Route: inline (1 engine file + 1 test + 1 doc). Tests: `ExecutedKitNotebookIsNotDriftTests::
  test_verify_reports_an_unreadable_notebook_instead_of_crashing` (4 subtests) RED 4F -> GREEN; the B7 test's
  docstring no longer defers the crash. Domain-lock pins unchanged (comments reworded). Seals unchanged
  (`test_implementation_seal.py` + `test_experiments_seal.py`: 73 passed). `test_proposal_implementation.py` +
  `test_experimental_implementation.py` + domain lock: 1935 passed, 2 skipped. Docs: proposal usage.md notebook
  status table. CHANGELOG Fixed + Behaviour changes. No migration (report-only).
  Commit: `fix(implementation): verify reports a notebook that is not a notebook instead of crashing` (the commit carrying this line)

- X8b (real; reproduced on the 23-file selection and minimally with
  `pytest tests/test_proposal_implementation.py::MaterializeBenchmarkDeclarationTests tests/test_upgrade_v0_13_0_workspace.py`
  -> 1 failed). Found with a scratch leak-watch plugin diffing `os.environ`, cwd and `sys.modules` around every
  test of the selection: the only profile leak was `MaterializeBenchmarkDeclarationTests.setUpClass` importing
  `skills/proposal-implementation/scripts/materialize.py`, whose import-time `os.environ.setdefault` left the
  proposal profile in the process. The upgrade test then passed `os.environ` to the workspace copy's experimental
  launcher; X8's sibling guard compares skills roots, and the repository's proposal profile lives under a different
  root than the workspace copy, so the explicit value won. Fixes: (1) the class restores the variable around the
  import (+ `test_importing_the_script_leaves_the_environment_as_it_found_it`, RED without the restore); (2) the
  upgrade test strips an inherited `IMPLEMENTATION_DOMAIN_PROFILE` from its child env; (3) systemic guard in
  `tests/conftest.py`: autouse function- and module-scoped fixtures restore `os.environ` and cwd (and, per module,
  the cached `impl_domain_profile`) only when changed. `tests/test_process_state_isolation.py` proves it in a child
  pytest run (leaks via body, setUp, setUpClass, setUpModule; control run without the conftest fails): RED with
  the HEAD conftest and with the module scope removed -> GREEN. Engine: its per-process caches live inside one CLI
  process, so nothing carries across launcher calls for users. Not fixed (outside surface): the launchers' sibling
  guard misses a sibling profile from another skills tree (`skills/*/scripts/implementation_cli.py`).
  Verification: `fast_tests.py --since 8e3f813` (now 28 files): 3364 passed, 3 skipped; the original 23-file
  list, one process: 3239 passed, 3 skipped, 0 failed. Route: inline. Test-only; no CHANGELOG entry, no migration.
  Commit: `test(implementation): no test file leaves process state for the next` (the commit carrying this line)

- X10 (real; three shared-path root causes, found by reading every write the colliding files make outside
  their own scratch roots and by a scratch deletion-watch plugin on a `-n 8 --dist loadfile` run):
  (1) five mutation tests still wrote a broken engine into the shipped
  `skills/_core/implementation/engine/implementation_engine.py` and restored it in a cleanup -- X3 had moved only
  one: `tests/test_implementation_pair.py` `CitationPatternMutationTests` (Y9), `DriftControlFoldMutationTests`
  (Y4-Y7), `LocalReachRevertMutationTests` (Z9), and `tests/test_proposal_implementation.py`
  `SettleHeadingAbsentMutationTests`. A concurrent reader saw a truncated or mutated engine: the experiments seal's
  `verify-a` printing nothing or a different digest. (2) `tests/orphan_sweep.py` (run by
  `test_proposal_implementation.py`'s `setUpModule`) listed `implementations/_*` and then stat'ed each entry; a
  sibling's own cleanup removing `_core_guard_*` in between raised `FileNotFoundError` in `setUpModule`, erroring
  every test of the file (the 1801). (3) three tests dropped modules into the shipped
  `skills/remote-execution/scripts/` (`TwoDocumentLifecycleTests`' capacity adapter, `BackendResolutionTests`'
  fixture backend and escape marker); measured in the first full parallel run of this task as
  `WorkspaceToolsResolverTests` reading a kit manifest that named `adapters/pairlifecycle<pid>.py` after it was
  removed. Fixes: new `tests/scratch_forge.py` (`build`: copies `_core/implementation` with the real nesting, the
  launcher, links or copies `remote-execution`, own `implementations/`); X3's setUp, the five mutation tests and the
  lifecycle class run there; `BackendResolutionTests` points the loaded `remote_cli.__file__` at a scratch
  `scripts/` copy; the sweep skips an entry that vanished. Guards: `assert_real_engine_untouched` in each mutation
  test and an equivalent assertion in the settle test (RED 7/7 on the in-place mechanism -> GREEN, engine diff
  empty); `tests/test_shipped_engine_is_never_written.py` (AST scan of every test module for
  `ENGINE.write_text/write_bytes`; finds 6 sites in HEAD's pair file and 1 in the proposal file);
  `test_a_fixture_its_owner_removes_mid_sweep_is_not_an_error` (RED FileNotFoundError -> GREEN). Every mutation
  test still asserts its mutated behaviour, so each still proves the scratch engine ran the mutation.
  Verification: `npm run test:py:par` twice: 3 failed, 6048 passed, 13 skipped (both runs), the 3 being exactly the
  known `.venv` environmental failures (`test_skill_audit` inversion test + its usage subtest,
  `test_cli_paper_e2e` wiring smoke); `git status skills implementations` clean after each run. Route: delegated
  writer (this one). Test-only; no CHANGELOG entry, no migration.
  Commit: `test(implementation): each test file runs in its own scratch paths under parallel runs` (the commit carrying this line)

- B2 (real, reproduced): `_proposal_status` probed only `proposals/deliberated/` and `proposals/accepted/`, which no
  current code writes, so every engine-published revision printed `(draft)`. Fix: `_revision_stage` reads the
  latest revision's publication receipt (`.proposal-deliberation/receipts/<file>.json`, the engine's
  `receiptPath`): committed and `documentShaAfter` == sha256 of the document -> `published`; receipt but different
  bytes -> `edited-after-publication`; none/uncommitted/unreadable/foreign -> `draft`. Legacy folders read first
  (fallback for old workspaces). JSON gains `proposal.receipt`. Engine `latest` is probed only when it is a bare
  filename. A test pins `PROPOSAL_DIRECTORY`/`PROPOSAL_SIDECAR_ROOT` to `profile.ts`. Real run on the extracted
  0.13.0 fixture (repo `node_modules` linked): `Proposal: ...-r02.md (published)`.
  Tests: `ProposalStageFromEngineStateTests` (7) RED 4F -> GREEN; mutations (COMMITTED check off -> 1 red; legacy
  fallback off -> 2 red). test:fast 195 passed. No migration (reader-side only).
  Commit: `fix(status): a proposal's stage comes from its publication receipt` (the commit carrying this line)

- B5 (real, reproduced on a `git init` target via the CLI): `env` -> `plan` refused `DIRTY_WORKTREE` (`?? .venv/`);
  `pip install -e .` leaves `src/<dist>.egg-info/` untracked; `plan` A -> `apply` -> `materialize --plan A` refused
  `PLAN_STALE` (apply carried out A's `createDirs`). Decision: the coordinator's "scaffold `.gitignore` exists before
  `env`" cannot hold literally, since writing a tracked `.gitignore` is itself an untracked file that dirties the
  tree before `plan` (and the scaffold only lands at `materialize`, after `plan`). Fix: `env` appends
  `ENV_PRODUCT_IGNORES` (`.venv/`, `*.egg-info/`) to the clone's `.git/info/exclude` (resolved via
  `git rev-parse --git-path`) before building anything; JSON gains `excluded`. `DIRTY_WORKTREE` unchanged (a
  stray untracked file still refuses, tested). `apply`/`materialize --stage scaffold` `.gitignore` blocks (and
  the forge harness `scripts/materialize.py`) also carry `*.egg-info/` via `authored_ignore_lines`; not added to
  `IGNORE_ENTRIES`, so existing targets' scaffold gaps/`verify` are unchanged. `PLAN_STALE` kept; `materialize`'s
  refusal detail now says it is expected once `apply` has run; lifecycle documented (usage.md "The plan, apply and
  materialize lifecycle", SKILL.md Flow A steps 2 and 5, env row; experimental SKILL.md step 1).
  Tests: `tests/test_implementation_fresh_target_lifecycle.py` (8, CLI end to end) RED 6F -> GREEN; mutations
  (exclude call removed -> 4 red; extras emptied -> 1 red). Domain-lock pins unchanged (prose reworded).
  test:fast 4138 passed, 4 skipped. No migration.
  Commit: `fix(implementation): env leaves a fresh target clean for plan` (the commit carrying this line)

- B6 (real): `backend_state` inferred only from imports, so the kit's numpy-importing `tests/conftest.py`/`sweep.py`
  made any torch target `mixed` -> `probe` `convert`; the scaffold pyproject (template and `_DEFAULT_PYPROJECT`)
  listed numpy only; `env` had no torch handling. Fix: `__backend__` literal in `src/<Package>/__init__.py`
  (`BACKEND_DECLARATION`, read with `read_declaration`): `"numpy"` -> numpy; a `TENSOR_BACKENDS` key -> `tensor` when
  a package file imports it, else `declared-unmet`; anything else -> `unrecognized-backend` + `declarationError`
  (fail closed, never trainable); absent/`None` -> legacy import inference unchanged. `backend` gains
  `declared`/`source`. Kit conftest/sweep use `random.Random` + `SEED`/`configuration_seed` (no array import);
  pyproject `dependencies = []` with guidance. `env --torch cpu|gpu [--torch-version X]` (`torch_provisioning`):
  cpu -> `--extra-index-url https://download.pytorch.org/whl/cpu torch==X+cpu`, X from the flag or the single exact
  manifest pin, else `TORCH_VERSION_REQUIRED` (also for a non-release version string); gpu -> `torch[==X]`; JSON
  gains `torch`. Not added to the authored package `__init__.py` (optional; keeps scaffold bytes and seals).
  Tests: `tests/test_implementation_backend_declaration.py` (17 + subtests) RED 20F -> GREEN; mutations (declaration
  read off -> 6 red; unmet branch off -> 1 red). Re-anchored: `RngFixtureRequestedByTemplateTests.
  test_the_stub_receives_the_fixture_conftest_actually_seeds` (pinned the numpy generator the neutral conftest no
  longer yields). Seals: `probe` in both corpora regenerated via the capture scripts (+47 bytes each = the two new
  keys); experiments `propose` timestamp noise reverted. Domain-lock pins unchanged (prose reworded). No migration.
  Commit: `fix(implementation): the array backend is declared, not inferred from a helper` (the commit carrying this line)

- B9 (real): the init template's `smoke_and_invariants` ran `pytest implementations/{paper_slug}/...` with
  `{paper_slug}` = workspace folder name and `pytest` from PATH. Fix (`src/papersmith/core/executor.py`): placeholders
  `{target}` (`implementations/<name>`) and `{target_python}` (that target's `.venv` interpreter, POSIX/Windows);
  `resolve_target` picks the only `implementations/` directory or `--implementation <name>` (new `run` flag and
  `run_profile(implementation=)` kwarg); none/several/unknown name, or no `.venv` when `{target_python}` is named,
  raises `UserError` naming the fix before dispatch or ledger write; `--dry-run` records `target_resolution`
  (`resolved`/`unresolved`) instead of refusing (keeps `scripts/cli-paper-*smoke.sh` dry-runs green). Template:
  `{target_python} -m pytest {target}/tests/test_invariants.py`, `PYTHONPATH: "{target}/src"`; remote profiles name
  `{target}` (no local venv required). Profiles naming neither placeholder are unchanged (tested). `papersmith.yaml`
  is user-owned (`manifest.py` never-overwrite list), so no migration: a pre-0.14.0 profile naming
  `implementations/{paper_slug}` runs unchanged when that directory exists and otherwise refuses with the edit.
  Tests: `DefaultProfileResolvesTheTargetTests` (11) RED 9F -> GREEN (the remote and two legacy tests were added
  with their guards; RED shown by mutation: legacy guard off -> 1 red; venv check off -> 1 red). Related e2e files
  191 passed, 1 failed = known `.venv` wiring smoke. test:fast 220 passed.
  Commit: `fix(run): the default profile runs the target's own interpreter against the target` (the commit carrying this line)

- X8c (real, reproduced by the new tests): the launcher guard refused a sibling profile only when its skills root
  equalled the launcher's, so the other skill's `impl_profile.py` from a copied skills tree ran (the experimental
  launcher would read `AGREED.md`). Fix (both launchers, still byte-identical): `_declared_skill` loads the named
  profile (`importlib`, fresh module) and takes the skill directory of its `PROFILE["cli"]["path"]`; refuse when it
  differs from this launcher's skill, in addition to the existing same-tree path rule (kept so an unloadable sibling
  in this tree still refuses). An unreadable profile declares nothing in the launcher and the engine's own load
  refuses it. Own profile from another tree and fixture profiles naming this launcher still run (tested).
  Tests: `InheritedSiblingProfileTests` +3 (other-tree sibling both directions, a profile at an arbitrary filename
  declaring the sibling's launcher, own profile from another tree) RED 3F -> GREEN; mutation (declared clause off ->
  3 red). test:fast 3218 passed, 3 skipped. No migration.
  Commit: `fix(implementation): the launcher refuses a sibling's profile from any skills tree` (the commit carrying this line)

- C4 (real, one part; two parts intended): `renderFromIdea` kept each sentence's terminal punctuation in the
  derived headings (`# Idea.`). Fix (`initial-revision-renderer.ts` `asHeading`): title and section heading drop
  their terminal `.!?` run; an all-punctuation sentence keeps its bytes (slug unchanged, `'???'` -> `concept`).
  Intended and now documented (both SKILL.md, both usage.md): heading from the second sentence (the
  single-sentence refusal depends on it) and the verbatim idea body (the headings are capped labels). The
  proposal usage example was a single sentence the engine refuses; now two (driven: created). Experimental
  usage response re-driven (title/heading/sha). Tests: `tests/deliberation-initial-title-derivation.test.mjs`
  (5) RED 4F -> GREEN; re-anchored `renderFromIdea composes v1 markdown...` (pinned `# ... .`) and the parity
  test's `SECTION` (`## Then compare the arms.`). test:node 729/729 after re-anchor; test:fast 3262 passed.
  Route: delegated writer (engine + 3 test files + 4 docs). No migration (existing revisions never rewritten).
  Commit: `fix(deliberation): v1 headings drop their sentence's terminal punctuation` (the commit carrying this line)

- C1 (real): the 65,536 cap lived only in the TypeBox schema (`proposal-workspace.ts`), which the CLI host
  never validates (`cli.mjs` calls `tool.execute` directly), so `cli.mjs` accepted any length and no doc stated a
  cap. Fix: exported `MAX_INSTRUCTION_CHARACTERS` feeds the schema and a guard at the top of `execute`
  (`INSTRUCTION_TOO_LONG`, `nextAction: shorten_instruction`, nothing written, both hosts); `instructionBudget`
  `{limit, used, remaining}` on the successor preview and on v1's `created` result. Docs: both SKILL.md (step /
  Limits), both usage.md (preview + v1 responses; v1 numbers re-driven). Tests:
  `tests/deliberation-instruction-budget.test.mjs` (5) RED 4F -> GREEN (at-cap case passes before and after by
  design). Observed along the way: v1 creation from a ~65k-character idea takes ~35 s (not addressed).
  test:node 734/734; typecheck clean. No migration.
  Commit: `fix(deliberation): the instruction cap is enforced on the CLI and reported` (the commit carrying this line)

- C6 (real): no preview existed for v1 and a success leaves the permanent creation lock. Fix: `dryRun` on
  `InitialRevisionCreationService.execute` returns `status: 'preview'` after every refusal and before the lock and
  publish; `proposal-workspace.ts` projects it (`dryRun: true`, filename, metadata, `markdown`, `instructionBudget`)
  and predicts the lock refusal via the new read-only `initialRevisionLockState` (lock never touched); `dryRun`
  on any other operation -> `DRY_RUN_UNSUPPORTED` (fail-closed, nothing runs); `cli.mjs --dry-run` sets the field on
  every tool request (STATUS/RESOLVE_TARGET unaffected). Docs: both SKILL.md (operations table), both usage.md
  ("Dry run first", proposal example driven). Tests: `tests/deliberation-initial-revision-dry-run.test.mjs` (6)
  RED 4F -> GREEN (single-sentence and STATUS cases pass before and after by design). Core comment reworded
  ("stops" is a domain-north word, `proposal-deliberation-domain-profile-lock`). test:node 740 (739 + that fix).
  No migration.
  Commit: `feat(deliberation): CREATE_INITIAL_REVISION previews with --dry-run, no lock, no write` (the commit carrying this line)

- C2 (real; the SKILL.md rules were also stale): `loadGuideDirectoryFragments` read nested then flat Markdown per
  source, sources in declaration order, 4000 bytes total, cutting and skipping silently; the experimental SKILL.md
  still said only `<folder>/<folder>.md` loads and `proposals/` gives presence only. Fix: `loadSourceWindow(root,
  limit)` (same walk and limit; also inventories what it did not read) feeds both the chat path (fixed 4000) and
  CREATE_INITIAL_REVISION, whose created/preview/refusal results carry `sourceWindow` and a
  `SOURCE_WINDOW_TRUNCATED` warning; `sourceWindowBytes` 1..262144 (`MAX_SOURCE_WINDOW_BYTES` = the managed write
  limit), `SOURCE_WINDOW_INVALID` / `SOURCE_WINDOW_UNSUPPORTED` otherwise. Docs: both SKILL.md, both usage.md ("The
  source window", driven example). Tests: `tests/deliberation-source-window.test.mjs` (9) RED 9F -> GREEN, including
  the experiments data-paper-first case. test:node 749/749; typecheck clean. No migration.
  Commit: `fix(deliberation): the first revision's source window is reported, warned and widenable` (the commit carrying this line)

- C3 (real): `preservation-experimental.ts` exempted only baselines tables (first header cell `Baseline(s)`) from
  `report-table-fabricated-value`, so a plan's own settings could not be tabulated. Fix: `PARAMETER_COLUMNS`
  (`parameter(s)`, `hyperparameter(s)`, whole first header cell, case-insensitive) marks a parameters table, skipped
  by the rule (and by the baseline rules); still a `report-table` atom. Fail-closed kept: partial matches and other
  columns stay under the rule; undeclared tables unchanged. Docs: experimental SKILL.md (three exemptions,
  non-negotiable), usage.md (example block gains a parameters table; block checked: no violations). Tests:
  `tests/experimental-deliberation-parameters-table.test.mjs` (8) RED 5F -> GREEN (the three fail-closed/atom cases
  pass before and after by design). test:node 757/757. No migration.
  Commit: `fix(experimental-deliberation): a declared parameters table carries the plan's fixed settings` (the commit carrying this line)

- C7 (real): the successor receipt (`orchestrator.ts`, `createRevisionReceipt`) recorded only `instructionHash`.
  Fix: optional `rationale` (1..2000 chars, non-blank) and `decider` (`agent`|`human`) on CREATE_SUCCESSOR, validated
  at the top of `execute` (`decisionRecordBlocker`: `DECISION_RECORD_INVALID`, or `DECISION_RECORD_UNSUPPORTED` on
  other operations; nothing runs) and recorded verbatim in the receipt only when supplied (`RevisionReceipt` gains
  the two optional fields; `validatePublicationReceipt` ignores extra keys, so old receipts validate unchanged --
  tested with the consistency audit). Docs: both SKILL.md, both usage.md. Tests:
  `tests/deliberation-successor-decision-record.test.mjs` (7) RED 6F -> GREEN (the no-fields case passes before and
  after by design). Core comment reworded to keep the pinned "proposal" residue at 171. Additive shape: no migration.
  Commit: `feat(deliberation): successor receipts record an optional rationale and decider` (the commit carrying this line)

- C5 (real, reproduced): a hand-adopted v1 (marker + rename) audited `MISSING_MANIFEST` and never met the gate.
  Fix: `ADOPT_INITIAL_REVISION` (`adoptInitialRevision`, `initial-revision-creation.ts`; routed in
  `proposal-workspace.ts`, accepted by `cli.mjs`). Shared `initialRevisionGate` (canonical form + pre-publish
  validation) now serves CREATE and ADOPT. rename mode: unmanaged `.md` -> creation port (lock, O_EXCL, state,
  receipt `operation: CREATE_INITIAL_REVISION` + additive `adoptedFrom`), slug from the first `# ` title; source left
  in place (`nextAction: move_adopted_source_to_backup`). record mode (explicit repair, no silent rewrite): a marked
  first revision with no receipt gets state + receipt, bytes untouched, no lock; a receipt present ->
  `ADOPTION_ALREADY_RECORDED`; a failing gate -> no record and the revision keeps reading (tested via STATUS).
  `--dry-run` supported. Docs: both SKILL.md (branch 3, operations table, Limits), both usage.md ("Adopting an
  existing document as v1", driven examples). Tests: `tests/deliberation-initial-revision-adoption.test.mjs` (12)
  RED 12F -> GREEN; mutation (record-mode gate removed -> 1 red). Re-anchored the operation-surface test's
  `ACCEPTED_OPERATIONS` (pins the set by design). Core comment reworded ("stops"). Additive receipt key: no migration.
  Not done (outside surfaces): `src/papersmith/bridges/deliberation.py` exposes no adopt verb.
  Commit: `feat(deliberation): ADOPT_INITIAL_REVISION gives an adopted v1 the created v1's state, receipt and gate` (the commit carrying this line)

- C14 (verified, real; blocked on edit surface): `cmd_agree` (`skills/_core/implementation/engine/implementation_engine.py`
  ~:10064) computes `untested = declared - crossed` in `crossing_state` (~:9427) and only clears an entry through the
  request-scoped `--acknowledge untested:<id>` argv; no machine-readable out-of-scope declaration exists in either
  document or in `skills/_core/conventions/experiments.json`. Adding one needs the implementation engine (reader) and
  the experimental-implementation docs, outside this writer's surfaces. Candidate paths:
  `skills/_core/implementation/engine/implementation_engine.py`, `skills/_core/conventions/experiments.json`,
  `skills/experimental-implementation/SKILL.md`, `skills/experimental-implementation/references/usage.md`,
  `skills/experimental-deliberation/SKILL.md`, `tests/test_experimental_implementation_*.py` (new test), CHANGELOG.md.
  Proposed shape: an `outOfScope` marker in the convention (e.g. `[out-of-scope:N]`) read from the experiments
  document and subtracted from `untested` (absent = today's behaviour); watch `tests/test_implementation_domain_lock.py`.

- C5 follow-up: the full parallel run showed two skill-audit tests pinning the deliberation host's refusal roster at 9
  (`RefusalProbeTests::test_the_refusal_yields_the_accepted_set`, `NewlyCoveredSubjectRosterTests` experimental case);
  both re-anchored to 10 with the reason (the adoption operation), without spelling the operation name (the file
  forbids operation literals). `tests/test_skill_audit.py`: 385 passed, 2 failed = the known `.venv` cases.
  Commit: `test(skill-audit): the deliberation roster counts the adoption operation` (the commit carrying this line)

- C9 (real): `cmd_admit` refused `NO_FINDINGS` on `FINDINGS = []`, so `verify` could only read `audit: none`.
  Fix: `admit --no-findings` (explicit, never default) writes an empty ruling (`findings: {}`, additive
  `noFindings: true`) bound to the revision bytes (`_admit_no_findings`); `verify` reads it through
  `admissibility_ruling` as `audit: ok` + additive `noFindings`, and as `incomplete` once stale. Without the flag
  `NO_FINDINGS` still refuses (detail names the flag); the flag with findings declared refuses `FINDINGS_DECLARED`
  (invocation defect). Docs: proposal-implementation SKILL.md step 11, usage.md (`admit` section + refusal table;
  also corrected the `MALFORMED_FINDINGS` row, which said `audit: none` is what an audited clean repository answers).
  Tests: `tests/test_implementation_empty_ruling.py` (6) RED 6F -> GREEN. Re-anchored: roster counts
  (`GatingRefusalRosterTests` 127 -> 128, invocation 55 -> 56, doctrine sentences), domain-lock pins `command`
  275->276 and `incomplete` 28->29 (payload key and status literal). Additive shape: no migration.
  Verification: focused 6 passed; domain lock 28 passed; roster 19 passed; `npm run test:fast` 3367 passed.
  Commit: `feat(implementation): admit --no-findings records an audit that found nothing` (the commit carrying this line)

- C8 (real): the engine already tolerated an empty remedy locus (handoff `remedy-locus-missing`), but the kit's
  `test_audit.py` required non-empty `remedy_equations` and `verify` listed such a finding under
  `localRemediesNotWritten` (+ a `toDiscuss` asking for a `remedy_block` nobody can compose without a tag), so a
  prose defect could not be a finding. Fix (supported, not just documented): explicit `"remedy_in_prose": True`
  (`remedy_in_prose()`): excluded from `localRemediesNotWritten`, deferred by `handoff` as `prose-remedy`,
  admitted on the ordinary checks; `admit` rules it inadmissible beside remedy loci or with a non-`True` value.
  Kit `test_audit.py` accepts it (and refuses it beside remedy equations); kit `findings.py` documents it.
  Docs: proposal-implementation SKILL.md (remedy bullets), usage.md (deferral table), experimental SKILL.md step 5.
  Tests: `tests/test_implementation_prose_findings.py` (10) RED 6F -> GREEN. Domain-lock pin `remedy` 56->57 (the
  published `prose-remedy` code). Old targets keep their own `test_audit.py` (documented: apply the kit change +
  `materialize --authored`). Additive: no migration.
  Verification: focused 10 passed; domain lock passed; `npm run test:fast` 4179 passed, 4 failed = the uncommitted
  RED files of C10/C14 only.
  Commit: `feat(implementation): a finding may declare a correction that rewrites prose` (the commit carrying this line)

- C10 (real): `remedies_without_control` intersected bare `ast.Name` calls with `from <pkg> import` names only.
  Fix: `_package_bindings` (from-import names + `import <pkg>[.x] [as m]` roots) and `_called_roots` (bare calls +
  the root name of attribute-call chains); same-file helpers that reach the package are grown to a fixed point. Not
  accepted (test-locked): import-without-call, uncalled reference, unrelated-module call, helper that never reaches.
  Mutation: dropping the attribute half, dropping the helper half, or accepting any rooted call each turns
  `tests/test_implementation_remedy_control.py` red. Docs: proposal usage.md ("A green result needs a reachable
  red"). Tests: new file (2 tests over 10 spellings) RED 1F -> GREEN. Domain-lock pin `value` 244->246
  (`ast.Attribute.value`, code). No shape change: no migration.
  Verification: focused 2 passed; engine suites (proposal, experimental, both seals, pair) `-n 8 --dist loadfile`
  2020 passed, 2 skipped.
  Commit: `fix(implementation): remediesWithoutControl follows attribute calls and same-file helpers` (the commit carrying this line)

- C14 (real; unblocked by the widened surface): `crossing_state` computed `untested = declared - crossed` with no
  machine-readable exclusion. Fix: convention key `outOfScope: "out-of-scope"` in
  `skills/_core/conventions/experiments.json`; experimental `impl_profile.py` builds `cross_citation.out_of_scope`
  (`[out-of-scope:<id>]`) from it; `impl_domain_profile.py` validates the optional sub-key (compiles, exactly one
  group -> `..._INVALID_CROSS_CITATION_PATTERN`); engine compiles it in `_CROSS_CITATIONS`, `crossing_state`
  subtracts `(marked & declared) - crossed` from `untested` and returns `outOfScope` only when non-empty; `cmd_agree`
  echoes it on an agreed payload only when present. Absent marker = today's behaviour (all seals unchanged).
  Docs: experimental-deliberation SKILL.md (`[claims:N]` section), experimental-implementation SKILL.md step 4,
  usage.md (new `agree` section). Tests: `tests/test_experimental_out_of_scope.py` (10) RED 3F (+1 validation RED
  with the resolver change stashed) -> GREEN; mutations (no subtraction, no `& declared`, no `- crossed`) each red.
  Re-anchored: `AgreeSuggestionKeyZ11MutationTests` (its anchor pinned the agreed return literal, which gained the
  conditional spread). No pin moved. Additive: no migration.
  Verification: focused 10 passed; experiments seal 29 passed; profile/experimental suites 224 passed; node
  experimental-deliberation-references 9 passed; `npm run test:fast` 3373 passed, 1 failed (the Z11 anchor, then
  re-anchored and green).
  Commit: `feat(experimental-implementation): an experiments document can mark a proposal claim out of scope` (the commit carrying this line)

- C11 (real): `object_destinations` fixed `src/<Package>/module.py` and `object_gaps` reported it missing whenever
  absent. Fix: `package_own_modules` (package `.py` files minus `__init__.py` and kit-owned files); `object_gaps` and
  `_materialize_object_destinations` drop the default module destination once the package holds any; `materialize
  --module <name>` writes `src/<Package>/<name>.py` from the same template (`object_module_name_problem` ->
  `MODULE_NAME_INVALID`; any other mode -> `MODULE_STAGE_MISMATCH`, both invocation defects);
  `recorded_object_modules` keeps a named module drift-checked (`objectDrift`) and `--authored`-releasable.
  Targets with `module.py` unchanged (test-locked). Docs: proposal SKILL.md step 9, usage.md (objects stage +
  refusal table). Tests: `tests/test_implementation_object_stage.py` (7, via new shared helper
  `tests/implementation_lifecycle.py`) RED 5F -> GREEN. Seals: verify-a/-b/-t (proposal) and verify-a/-b/-t,
  verify-a-declared, verify-b-declared, verify-b-undeclared (experimental) recaptured with the capture scripts;
  the only output delta is `structure.objectGaps` losing `src/Seal/module.py` (and the `resolve` question listing
  the same gaps), checked by diffing the verify outputs before/after; `propose` re-recorded too but it is the
  declared non-deterministic case, excluded from comparison. Re-anchored: roster 128 -> 130 (invocation 56 -> 58);
  domain-lock pin `module` 195->198 (the flag's parser entry, `getattr`, one refusal). No migration.
  Verification: focused 7 passed; engine suites `-n 8 --dist loadfile` 2250 passed, 11 failed = seal digests,
  then recaptured: both seal files green.
  Commit: `fix(implementation): the objects stage follows the approved map instead of a fixed module.py` (the commit carrying this line)

- C12 (real): scaffold/objects substituted only `{{PKG}}`/`{{SEED}}` although usage.md's own table already said
  `{{NAME}}`/`{{REVISION}}` are answered at scaffold. Fix: `kit_substitute_body` (one path, receipt records the
  mapping); scaffold fills `NAME` + `REVISION` when known (`declared_revision`, else the approved plan's
  `boundTo.revision`; `_materialize_plan_gate` now returns the plan); objects fills `REVISION`/`NAME`/`MODULE` in
  its bodies and `_fill_scaffold_tokens` fills them into scaffold entries still byte-identical to their receipt
  (engine kind, stage scaffold), re-sealing (`writtenSha256`, notebook source digest, merged `substitutions`);
  result gains additive `filled`. Edited/adopted/authored files untouched (tested). Legacy notebook reconstruction
  now rebuilds from the recorded substitutions (identical for 0.13.0 receipts, which record only PKG/SEED). Kit:
  `admissibility.py` refuses clearly while `CURRENT_REVISION` is a placeholder; `test_smoke.py` names the missing
  module/revision (keeps the `No module named '<Pkg>.'` red FreshScaffoldStaysRed pins); `conftest.py`
  `pytest_pycollect_makemodule` turns a placeholder-caused unparsable test file into one failing item naming the
  placeholders. Kit text avoids the harness name (`MaterializeScriptStaysTestOnlyTests`). Existing kit files on
  disk and their seals untouched. Docs: proposal SKILL.md steps 5 and 9, usage.md (objects stage + token prose).
  Tests: `tests/test_implementation_kit_tokens.py` (9) RED 6F (2 more RED with only the kit edits stashed) -> GREEN.
  Pins: `module` 198->199 (the `MODULE` key), `approved` 47->48 (`return approved`); `destinations` 39->36 shrank.
  The first full run caught `SeedForcedNoneMutationTests` anchoring on the plan gate's local name; the rename was
  reverted there (amended into this commit).
  No seal moved. No migration (additive receipt keys; rewrites only engine-sealed untouched bytes).
  Verification: focused 9 passed; engine suites + upgrade + kit provenance `-n 8 --dist loadfile` 2318 passed.
  Commit: `fix(implementation): materialize fills the kit placeholders it can answer and names the rest` (the commit carrying this line)
- C13 (real): `build_converter` handed Marker only `output_format`/`mode`; Marker 2.0.0's `TableProcessor`
  rebuilds every digital table from the text layer (`tables_pdftext`, `marker/processors/table.py:80-90`) in
  both modes, falling back to OCR only below its reconstruction score; only `force_ocr` skips text-layer
  extraction (`marker/providers/pdf.py:110`, so `raw_pdftext_pages` stays empty). Fix: pure
  `marker_options(mode, force_ocr)`, `--force-ocr` flag, optional boolean `paper_ingestion.force_ocr` (non-bool
  = `ConfigError`). Confirmed `ConfigParser({...,'force_ocr':True}).generate_config_dict()['force_ocr'] is True`
  in the gate env. Tests: `ForceOcrTests` (7) RED 6F -> GREEN, no Marker load (build_converter stubbed).
  Re-anchored: `NewlyCoveredSubjectRosterTests._CASES` paper-ingestion 4->5 (the new flag in the usage line).
  Docs: SKILL.md (usage, config, "Tables from a poor text layer", gate), README (2 sites). No migration.
  Commit: `feat(paper-ingestion): force OCR on every page for a poor text layer` (the commit carrying this line)
- E4 (real): `_commit_walked_step` hard-coded the subject `f"walk: {step}"`; nothing records it (no receipt or
  ledger field; `cmd_walk`'s output never carried it). Fix: `WALK_COMMIT_TEMPLATE = "walk: {step}"`,
  `walk_commit_subject(template, step)` (refuses `WALK_COMMIT_TEMPLATE_MALFORMED` on no `{step}`, any other
  brace, a newline), `walk --commit-template`, validated before `resolve_target`. Also corrected `cmd_walk`'s
  stale docstring ("It does not commit"). Tests: `tests/test_implementation_walk_commit_template.py` (7, 6
  subtests) RED 11F -> GREEN. Domain lock unchanged (one draft wording moved `local` 37->38; reworded). Seals
  unchanged (73 passed). `npm run test:fast`: 3378 passed. Docs: proposal SKILL.md (`walk` row), usage.md
  (`walk` section), experimental SKILL.md (Flow A step 6). No migration.
  Commit: `feat(implementation): walk commits under an operator-declared subject template` (the commit carrying this line)
- E5 (real): `status` -> `manifest.workspace_framework_files` and `audit --check-drift` -> `check_generated` +
  `workspace_framework_files` called `render_files` without a `warnings` list, so `_collect_projected_agents`
  emitted the Pi `has no Pi tool` notes as a `UserWarning` on every read (reproduced on a fresh `init`).
  Fix: `workspace_framework_files(..., notes=)`; `status` collects into additive `framework.generator_notes`,
  `status --verbose` / `audit --check-drift --verbose` print `note: ...` to stderr; init/upgrade unchanged
  (still warn). Tests: `tests/test_papersmith_quiet_reads.py` (6, subprocess with `-W default` so dedup cannot
  hide a warning) RED 5F -> GREEN; the fixture test asserts init still emits the note. `npm run test:fast`:
  3440 passed, 1 known failure. Docs: README `status`/`audit` reference. No migration.
  Commit: `fix(cli): status and audit keep projection notes out of every read` (the commit carrying this line)
- E6 (real, partial): `check_atlas.py` checked shape only. Fix: `--pool <candidates.json>` adds quote fidelity:
  `evidence.origin` must name a candidate (`identifier`/`source_url`/`url`; `EVIDENCE_ORIGIN_NOT_IN_POOL`), the
  candidate must hold an abstract (`EVIDENCE_ABSTRACT_MISSING`), the quote must be a verbatim substring
  (whitespace collapsed only; `EVIDENCE_QUOTE_NOT_IN_ABSTRACT`); unreadable/malformed pool exits 2.
  `_failures(atlas)` keeps its one-arg form (command center). Opt-in flag, not auto-discovery: the merged
  `atlas.with-proposal.json` lives beside `candidates.json` and its proposal system quotes the proposal.
  Tests: `QuoteFidelityTests` (9) RED 8F -> GREEN. Resolver facts verified in
  `skills/paper-writing/scripts/paper_resolve.py`: `_parse_arxiv` hard-codes `"year": None` although the Atom
  entry carries `<published>` (real defect); `_parse_crossref` hard-codes `"year": None` (ignores
  `issued.date-parts`) and `"abstract": None` on purpose (JATS) — Crossref abstract limit is intrinsic by design;
  documented in plausibility SKILL.md with what the pool does then.
  BLOCKED (outside allowed edit surfaces): (1) `skills/paper-writing/scripts/paper_resolve.py` (+ a resolver test,
  e.g. `tests/test_paper_resolve*.py`) to read arXiv `<published>`/Crossref `issued` years — needs a check that
  existing metadata caches/digests keep verifying; (2) `.claude/agents/sota-grapher.md` (then
  `python scripts/sync-repo-harness.py`) so the grapher's own checker command passes
  `--pool sota-pool/candidates.json`; until then the guard is documented in SKILL.md but not in the agent's loop.
  Commit: `feat(plausibility): the atlas checker holds every quote to its pool abstract` (the commit carrying this line)
- E2 (real): proposal-implementation `SKILL.md` (:1059 checklist doctrine, :2939 `agreements` row, :3178 `close`
  row) and `references/usage.md` (:2445) said `AGREEMENTS.md`; the profile holder is `AGREED.md`. Engine comments
  that say "`AGREEMENTS.md`-style" left as-is (generic shape wording; domain-lock pins engine prose). Test:
  `tests/test_holder_name_doc_drift.py` (every `*AGREE*.md` spelled in `skills/*/SKILL.md` and
  `skills/*/references/*.md` must be a holder some `impl_profile.py` declares) RED 4F -> GREEN (2 passed, 60
  subtests). `npm run test:fast`: 188 passed. No migration.
  Commit: `docs(implementation): name the declared checklist holder, not AGREEMENTS.md` (the commit carrying this line)
- E3 (real): `_materialize_authored` accepts `all_kit_destinations` + `recorded_object_modules`; `_materialize_adopt`
  accepts `all_kit_destinations` only; the refusal named neither and no doc listed the paths. Fix: both refusal
  details list the accepted paths (engine, variable `allowed`; domain lock unchanged); usage.md "#### The sealed set"
  lists the paths with their stage + the `--module` and merge-anchor/`wiring.py` notes; SKILL.md `materialize` row
  points at it; `NOT_A_KIT_DESTINATION` refusal-table row updated. No count written in prose
  (`DerivedScaffoldCountSweepTests` forbids it; it caught my first draft's "seventeen"). Test:
  `tests/test_materialize_sealed_set_doc.py` (doc list == engine list via subprocess; refusal names every path for
  both modes) RED 3F -> GREEN (2 passed, 2 subtests). `npm run test:fast`: 3379 passed, 1 failed (the count sweep,
  fixed) -> sweep 3 passed. No migration.
  Commit: `fix(implementation): materialize names the sealed set it accepts` (the commit carrying this line)
- E1 (real): `bridges/implementation.py` `ALIASES = {"materialize": "apply", ...}` and `REAL_COMMANDS` = 9 of the
  engine's `COMMANDS` (21, +`agree` under two documents). Not renamed (backward compatible): the alias keeps mapping
  to `apply` and `execute` writes a stderr note naming `--action apply` and the direct engine `materialize`; the
  unsupported-action `UserError` names the bridged commands, the aliases and `python3 <ENGINE_CLI> <action> ...`;
  `--action` help lists both. README `papersmith implement` (Spanish, matching the manual) lists bridged vs direct
  commands. Tests in `tests/test_papersmith_bridges.py` (4 new): bridged ⊆ engine `COMMANDS` (AST-derived), refusal
  names roster + route, alias note (and none for `apply`), README names every engine command minus the bridge;
  RED 3F -> GREEN (15 passed). MCP `papersmith.implement` description untouched (it forwards to the CLI).
- E7 (real): `IMPLEMENTATION_DOMAIN_PROFILE_NOT_ABSOLUTE` (`impl_domain_profile.py:285`) was in no doc. Added to
  proposal usage.md launcher intro, proposal SKILL.md Command Roster, experimental SKILL.md launcher paragraph,
  README bridge section + troubleshooting.
- E8 (real): `--session` had no definition. Verified in the engine: required by position/propose/gate/offer/close/
  step/settle/defect (parser :21702) and walk (:21918), optional on `adopt --apply`; stamped verbatim into events,
  never validated; `close`'s `prior_close` keys on it; `offer` interpolates it unquoted into published commands
  (:17123, :17365). Defined in usage.md "### Session ids"; pointers from proposal SKILL.md roster, experimental
  SKILL.md, README.
  `npm run test:fast`: 4264 passed, 1 known `.venv` failure (skill_audit inversion). No migration.
  Commit: `fix(cli): the implement bridge names its coverage and the direct engine route` (the commit carrying this line)
- E6 remainder (b) (real): canonical source is the tracked `.claude/agents/sota-grapher.md` (kit entry
  `KIT_ENTRIES`; `generators.py` projects `.pi/.opencode/.agents` from it; `scripts/sync-repo-harness.py` copies
  the projections into the checkout). Edited the checker command to add `--pool sota-pool/candidates.json` + one
  sentence; `python scripts/sync-repo-harness.py` synced 3 of 95; `--check` clean (95 files). Test:
  `GrapherAgentChecksQuotesTests` in `tests/test_sota_atlas.py` (every agent line running
  `check_atlas.py sota-pool/atlas.json`, all four agent folders, carries `--pool`) RED 4 subtests -> GREEN (35
  passed). Upgrade verified: workspace `init` from the stashed (previous) tree had 0 `--pool` lines; `papersmith
  upgrade --allow-dirty-kit` rewrote `.claude/`, `.pi/`, `.opencode/` grapher files (2 lines each).
  Commit: `fix(plausibility): the grapher agent checks quotes against the pool` (the commit carrying this line)
- E6 remainder (a) (real): `_parse_arxiv`/`_parse_crossref` hard-coded `"year": None`. Cache check first: the cache
  key (`metadata_digest`) is sha256 of the raw response; `paper_bib.entry_from_record` verifies only that the blob's
  own digest equals its key; nothing else digests `year` -> old `year: null` caches keep reading, no invalidation, no
  migration. Fix: `_arxiv_year` (first 4 digits of `<published>`), `_crossref_year` (`issued`, else `published`,
  integer `date-parts[0][0]` only). Tests: `PublicationYearTests` in `tests/test_paper_resolve.py` (arXiv 4 cases,
  Crossref 10 cases incl. `[[null]]`, strings, bools; cache key == raw digest and a legacy `year: null` blob reads
  back unchanged) RED 6F -> GREEN; resolver/evidence/writing/cache files 768 passed. Doc: plausibility SKILL.md.
  Commit: `fix(paper-writing): resolve reads the year arXiv and Crossref send` (the commit carrying this line)
- E9 (real): only proposal-implementation (:152) and paper-writing (5 stretch paragraphs) covered a harness with no
  Task tool, and none said to follow the agent file. Added "## When a delegated agent cannot be spawned" to the 8
  bound skills (skill-audit, paper-writing, proposal-deliberation, experimental-deliberation,
  experimental-implementation, proposal-implementation, plausibility, paper-ingestion), naming each bound
  `.claude/agents/<name>.md`; paper-writing notes inline audits are not independent. Test:
  `tests/test_agent_inline_fallback_doc.py` (binding derived from each agent's `Skill:` line) RED 8 subtests ->
  GREEN (2 passed, 8 subtests). `npm run test:node`: 776 pass, 0 fail. `npm run test:fast`: 188 passed.
  Commit: `docs(skills): every delegating skill names its inline fallback` (the commit carrying this line)
- E10 (real): `classify_source` refused a non-PDF path ("must be a PDF path") or URL with no way forward.
  Both refusals now append `NON_PDF_ROUTES`, naming `guidance/paper-guide/` (read by
  `CREATE_INITIAL_REVISION`, proposal-deliberation SKILL.md :230) and `proposals/` + `ADOPT_INITIAL_REVISION`
  (`sourceFilename` an unmanaged `.md` in `proposals/`, SKILL.md :402); old prefixes kept. Test:
  `test_a_non_pdf_refusal_names_the_deliberation_seeding_routes` (`notes.md`, `draft.txt`, landing URL) RED 3
  subtests with only the ingest.py hunk reverted -> GREEN (7 passed). Docs: paper-ingestion SKILL.md, README
  `ingest` reference, CHANGELOG Fixed + Behaviour changes. `npm run test:fast`: 225 passed, 1 failed (expected
  `.venv` wiring-smoke). No migration.
  Commit: `fix(ingest): non-PDF refusals name where text material goes` (the commit carrying this line)
- X11 (real): `wc -l` gives 65 for both `scripts/implementation_cli.py` (byte-identical, `cmp`) and 352 for
  `experimental-implementation/impl_profile.py`; README said 24 and 278 (and "unos 300 bytes"). Dropped the
  numbers (they rot with every launcher change); the launcher row now names `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING`
  (exit 2, read from the launcher). Passive doc: structural readback only, no RED applicable.
  Commit: `docs(readme): drop the implementation launcher line counts` (the commit carrying this line)
- X12 (real): `upgrade-project` SKILL.md had no word on `.gitignore`; its "What is never overwritten" section
  implied every hand-edited file outside `PRESERVE_PATTERNS` is replaced. Added a subsection read from
  `merge_managed`/`_block_span`/`render` in `src/papersmith/generators.py`: block re-rendered, lines outside kept,
  drift on the block only, pre-0.14.0 conversion (baseline digest -> whole replace, else lines kept below),
  malformed markers -> `unsynchronized`, file untouched. Passive doc: structural readback; `sync-repo-harness.py
  --check` clean (95 files); generators/skills-e2e/gitignore tests 75 passed.
  Commit: `docs(upgrade-project): the .gitignore managed block survives user lines` (the commit carrying this line)
- X13 (real): `proposal-workspace.ts` fell through to the `INITIAL_IDEA_REQUIRED` message for every
  unhandled creation code, so a one-sentence idea read "Provide a non-empty idea in instruction." Added a branch
  for `INITIAL_IDEA_SINGLE_SENTENCE` (code and `nextAction` unchanged). Tests in
  `tests/deliberation-initial-revision-dry-run.test.mjs`: single-sentence message names "two sentences", real and
  `--dry-run` (RED 1 fail / 7 pass -> GREEN 8 pass), and an empty idea keeps its message. Domain lock and
  instruction-budget files: 27 pass. `npm run setup:harnesses && npm run typecheck`: clean. `npm run test:node`:
  778 pass, 0 fail. No migration.
  Commit: `fix(deliberation): the single-sentence refusal names the two-sentence rule` (the commit carrying this line)
- X14 (real): `bridges/deliberation.py` `REAL_OPERATIONS` lacked `ADOPT_INITIAL_REVISION`, so `--action adopt` was
  "unsupported deliberate action"; only raw `--request` reached it. Added alias `adopt` and the operation; `--revision`
  required for it (refused before the engine). First draft also dropped `--instruction` for adopt; the end-to-end
  test caught the engine CLI's `INSTRUCTION_REQUIRED` (cli.mjs:349), so `--instruction` stays required. The bridge has
  no `--dry-run`, so none was added; README documents the raw `--request` with `"dryRun": true` (verified on a
  scratch workspace: `status: preview`, `mutations: 0`, no file; then `--action adopt`: `adopted`, source kept). README
  `--action init` example now carries the `--instruction` it needs. Tests in `tests/test_papersmith_bridges.py`:
  alias shape (2 subtests), missing `--revision`/`--instruction`, engine operation enum (read from
  `proposal-workspace.ts`) subset of `REAL_OPERATIONS`, end-to-end adopt through `execute`. RED 5 failed with
  deliberation.py stashed -> GREEN 19 passed. No migration.
  Commit: `feat(cli): deliberate --action adopt reaches ADOPT_INITIAL_REVISION` (the commit carrying this line)

## Final verification

Run on 2026-10-12 against `90e5731` (branch head before this commit). The verification worker did not change any
source, skill, test or doc other than this file. Scratch workspaces were outside the repository.

**Verdict: task F stays open.** Checks 1 and 3 passed. Check 2 drove every stage end to end and showed that none of
A1–A8 reproduces, but it found two open defects (X15, X16) and two smaller notes (X17 pre-existing, X18 doc gap).
X15 blocks experimental-deliberation v1 in the normal flow.

### Check 1 — full suites

- `npm run test:node`: 778 tests, 778 pass, 0 fail.
- `npm run test:py:par`: 6185 passed, 14 skipped, 3 failed. The 3 failures are the known `.venv/bin/python`-absent
  environment failures: `tests/test_skill_audit.py::NothingWasRepairedTests::test_an_inversion_run_leaves_the_subject_byte_identical`,
  `tests/test_skill_audit.py::UsageReferenceTests::test_every_documented_invocation_runs` (subtest: the
  `audit_cli.py inversion ... self-guarded-facts.json` invocation), and
  `tests/test_cli_paper_e2e.py::TestWiringSmokeWrapper::test_wiring_smoke_script_exits_zero_on_fresh_workspace`.
- `npm run setup:harnesses && npm run typecheck`: exit 0 (`tsc -p tsconfig.json` clean).
- `python scripts/sync-repo-harness.py --check`: `harness projection: clean (95 files)`, exit 0.
- Afterwards `git status --porcelain` was empty and `git diff | grep -c MUTATED` = 0.

### Check 2 — E2E smoke on a fresh `papersmith init` workspace

`papersmith init ws --no-env --no-npm --remote local` (micromamba env `papersmith`, CLI 0.14.0), with
`PAPERSMITH_ALLOW_DIRTY_KIT` unset and **no `--allow-dirty-kit`**: `Kit source: 0.14.0 at 90e573114b55 (checkout,
clean)`. The repo's `node_modules` was symlinked in for the deliberation engines. Content was generic: a windowed
average estimator, one equation `c = d \tag{1}`, experiments E1 and E2.

- **Proposal deliberation.** v1 with `--dry-run` answered `preview`, `dryRun: true`, `mutations: 0`, and no
  `proposals/*.md` or lock was created. The real call created `...-r01.md`, and its body equals the dry-run markdown.
  r02 (resolve, preview, accept on one `--serve` process) added `## 1 Estimator` and the equation. r03 adopted the
  implementation finding by replacing it with `c = e + \kappa`, with the math removal acknowledged. Both receipts
  record `rationale`/`decider` (C7).
- **Proposal implementation on `implementations/Smoother`.** `env` gave `excluded: [.venv/, *.egg-info/]` and the
  tree stayed clean (B5). `plan` then `apply` committed the layout. `materialize` with the old plan was refused
  `PLAN_STALE`, and the detail says this is expected after `apply` (B5). `plan` again, then `materialize --stage
  scaffold` gave `materialized`, with `{{REVISION}}`/`{{NAME}}` filled and only step-9 tokens left (C12). `verify`:
  `fidelity: ok` and `missingProvenance: []` beside the kit seal (A4). `materialize --stage objects --module
  estimator` wrote `src/Smoother/estimator.py` and `filled` two scaffold files, and `objectGaps: []` (C11, C12).
  After that came the authored module, findings and tests, `admit` (A1), and `close` (A5).
- **Experimental deliberation.** v01, v02 adding `## Experiment [exp:E1]` (with `[claims:1]`, a code span, and a
  parameters table), and v03 adding `## Experiment [exp:E2]` that cites `(Exp. E1)`. All published with audit PASS.
  v01 needed `sourceWindowBytes: 87` because of X15.
- **Experimental implementation on the same target.** A per-lineage `__implementation__` mapping (A8), in-package
  steps `first`/`second` with no prior-work package (A3), a `position` into `Experimental_AGREED.md` beside a
  populated `AGREED.md` (A2), and a pilot of both steps. Between the steps came `settle`, `position` refresh and
  commits, as documented.
- **Workspace.** `papersmith status` reported `Proposal: ...-r03.md (published)` (B2) with empty stderr.
  `papersmith audit --check-drift` reported `drift: clean` with empty stderr; the notes appear only with `--verbose`
  (E5).

Per A-item, compared with the original symptom:

- **A1:** `admit --revision r02` gave `admitted`, `introducesNotation: {loose_term: [\kappa]}`, and `verify` read
  audit `incomplete` with `remediesWithoutValidation: [loose_term]` (open finding, as designed). After r03,
  `admit --revision r03` gave `admitted`, `adopted: {loose_term: {revision: r03, matched: [c = e + \kappa]}}`, and
  `verify` read audit `ok`, compatibility `ok`, migration `clear`, and `findingsWithoutEvidence: []`. Before the fix,
  the successor was ruled inadmissible and the audit never reached `ok`.
- **A2:** the experimental `position` gave `written` into `Smoother/Experimental_AGREED.md`, and `AGREED.md` was
  byte-identical. The experimental `verify` lists `siblingHolders: [Smoother/AGREED.md]` and the proposal `verify`
  lists `siblingHolders: [Smoother/Experimental_AGREED.md]`. The same target on main's engine (`git archive main`)
  refused `HOLDER_UNDECLARED` and asked to rename the sibling's `AGREED.md`.
- **A3:** with `comparable: false` and `baselines: []`, `probe` answered `pilot-first` before and after step 1, and
  `pilot-decisions` with `pilotCompleteness: complete` and 3 placement questions after both steps. Main's engine on
  the same target answered `nothing-to-compare` with pilot `complete`.
- **A4:** with a freshly scaffolded `src/Smoother/report_digest.py` present, proposal `verify` gave `fidelity: ok`
  and `missingProvenance: []`, and experimental `verify` (sibling seal) also gave `missingProvenance: []`.
- **A5:** on a proposal-only target (no flow declared), `close` gave `closed` with `positionOwed: false`. `settle
  --done --unwitnessed --reason ...` gave `written` with `unwitnessed: true`. `verify` agreements then read `settled`
  with `witness.decided: [{text, reason, session: smoke2, at}]`, and the line stays under `unwitnessed`. `close` gave
  `closed` again. Before the fix, `close` required a position no witness could produce, and a hand tick was the only
  route to `settled`.
- **A6:** v1 carrying an inline-code `` `## Results` `` was created. A proposal successor carrying it was accepted
  (`published`, audit PASS), and so were both experiments successors. Before the fix, the accept turn refused
  `atx-heading-standalone` after an `awaiting_acceptance` preview. See X15 for the v1 side effect.
- **A7:** experimental `verify` reads `src/Smoother/sweep.py` with `sections: [E1]` and `experiments: [E1]`, and
  `fidelityByDocument.experiments` is `ok`. A finding citing `E1` is not ruled absent (`unknownExperiments: []`).
  `handoff` counts the `(Exp. E1)` prose citation (`citedElsewhere: 1` for remedy `E1`). Before the fix, only
  `## N` headings and digit citations were read.
- **A8:** with `revision: {"proposal": r03}`, experimental `verify` (no `--revision`) read `fidelity: unknown`,
  `latestRevision: null`, `revisionSource: none`, and `fidelityByDocument.proposal` `ok`, never the proposal
  filename. Proposal `verify` discovered r03. With `{"proposal": r03, "experiments": v03}`, experimental discovered
  v03 and proposal kept r03. Main's engine crashed on the mapping (`TypeError ... not 'dict'` in
  `revision_discovery`).

Where a stage could not be driven as first written:

- Experimental v1 refused under the default source window (X15).
- Experimental `verify` refused `MALFORMED_FINDINGS` until the proposal finding carried `'document': 'proposal'`.
  This is the documented rule for two documents, and the proposal skill accepts the field. It is a sharing cost, not
  a defect.
- `settle` cannot place a witness-less line without a discussion, so it was written by hand at the gate (X18).
- `materialize --authored src/Smoother/sweep.py` was refused `NOT_A_KIT_DESTINATION`, as E3 documents.
- No target `pip install` was run, so no notebook was executed and no remote stages were driven.
- X16 was observed as the aggregate `fidelity: drift` on both skills.

### Check 3 — upgrade of the v0.13.0 fixture

The fixture `tests/fixtures/workspace_v0_13_0/workspace.tar.gz` was extracted to scratch (54 files), and the sha256
of every file was recorded. Recorded artifacts (first 12 hex characters):

| Artifact | sha256 |
| --- | --- |
| `.proposal-deliberation/locks/initial-revision.lock` | `3c8843112212` |
| `.proposal-deliberation/receipts/...-r01.md.json` / `...-r02.md.json` | `dba823582d0e` / `a0096e169bb1` |
| `.proposal-deliberation/state/...-r01.md.json` / `...-r02.md.json` | `6001d141e976` / `fd5fd0fa9c76` |
| `proposals/...-r01.md` / `...-r02.md` (managed revisions) | `700e79af2930` / `9a77371b5e80` |
| `.experimental-deliberation/locks/initial-revision.lock` | `28f4d7938691` |
| `.experimental-deliberation/receipts/...-v01.md.json` / `state/...-v01.md.json` | `d02e49cb7ee2` / `c45d6a99344a` |
| `experiments/experiments-smoothing-window-sweep-v01.md` | `e0ab95884b0a` |
| `implementations/Smoother/.implementation/materialization.json` (scaffold receipt) | `52d2586b4b8e` |
| `implementations/Smoother/Smoother/.implementation/position.jsonl` (ledger) | `847fcc1b737c` |
| `implementations/Smoother/Smoother/AGREED.md` / `Experimental_AGREED.md` (holders) | `5a8e43957fde` / `8de06c4731f9` |
| `implementations/Smoother/src/Smoother/report_digest.py` (seal) | `c3f00820fae0` |
| `implementations/Smoother/Smoother/Notebooks/verification.ipynb` | `a9ed76e20844` |
| `.papersmith/runs_ledger.jsonl` | `e3b0c44298fc` |

- `papersmith upgrade ws --plan-migrations` reported `none; this workspace's artifacts already match the installed
  release` and wrote nothing. `papersmith upgrade ws` (no `--allow-dirty-kit`) exited 0 with `changed files: 360`
  and `Kit source: 0.14.0 at 90e573114b55 (checkout, clean)`.
- Migrations: `REGISTRY` holds exactly two, both convergence (`applies_from=None`): `sota-pool-scaffold` and
  `atlas-render-refresh`. After the upgrade, `migrations.plan(recorded="0.13.0")` reports both `satisfied`, with
  pending and undetermined empty. This branch adds no version-gated migration: every shape change in it is additive
  or reader-side (per-item notes above). The upgrade also wrote `.papersmith/kit-source.json` (D1), converted
  `.gitignore` to the managed block (D3), and re-rendered the routing docs after the marker moved (X5).
- Bytes: 50 of 54 files are byte-identical, including every artifact in the table. The 4 changed files are exactly
  the intended ones: `.gitignore`, `.papersmith/config.json`, `.papersmith/manifest.json`, `.papersmith/version`
  (`0.13.0` -> `0.14.0`).
- Still validating: proposal STATUS lists r01/r02 as managed with `latest` r02 and no non-managed files.
  Experimental STATUS lists v01. Proposal `verify --revision r02` gives `fidelity: ok`, no `scaffoldDrift` or
  `unrecordedScaffold`, and agreements `open` on `AGREED.md`. Experimental `verify --revision v01` gives `fidelity:
  ok`, agreements on `Experimental_AGREED.md` with `siblingHolders: [AGREED.md]`, and position `open`. Structure
  `drift` comes only from the stages the fixture never ran (`objectGaps`, `harnessGaps`, `Results`/`Models` dirs).
- `papersmith audit --check-drift`: `drift: clean`, rc 0, empty stderr. `papersmith status`: workspace 0.14.0,
  `Framework drift: none`, `Pending artifact migrations: none`, `Proposal: ...-r02.md (published)`, empty stderr.
- Note (X15): the fixture's experiments v01 holds pasted proposal markers. A successor preview from it is refused
  (`CANDIDATE_VALIDATION_FAILED`), as main refused it at accept. The upgrade did not cause this.

### Outcome table

The commit hashes below were cross-checked against `git log main..HEAD` (all 68 branch commits are present). In the
behaviour-change column, "y" means an existing workspace or caller can notice the change.

| Item | Outcome | Commit(s) | Test file(s) | Behaviour change |
| --- | --- | --- | --- | --- |
| A1 | fixed | fe4907c | tests/test_proposal_implementation.py | y — an adopted finding is admissible with `adopted`; audit can reach `ok` |
| A2 | fixed | b00042f, 3c6207c | tests/test_implementation_domain_profile.py, tests/test_proposal_implementation.py, tests/test_experimental_implementation.py | y — a sibling's holder is set aside (`siblingHolders`), never `HOLDER_UNDECLARED` |
| A3 | fixed | 4b2ff0f | tests/test_proposal_implementation.py, tests/test_experimental_implementation.py | y — `probe` reaches `pilot-first`/`pilot-decisions` with nothing to compare |
| A4 | fixed | 7804d6d | tests/test_proposal_implementation.py, tests/test_experimental_implementation.py | y — the unmodified kit seal no longer reads as `missingProvenance` |
| A5 | fixed | 775850e | tests/test_proposal_implementation.py, tests/test_experimental_implementation.py | y — `close` owes no position without a flow; `settle --done --unwitnessed` |
| A6 | fixed (side effect: X15) | 5b8a045 | tests/deliberation-validation-parity.test.mjs, tests/proposal-workspace.test.mjs | y — one verdict at v1/preview/accept; code spans are not headings |
| A7 | fixed | 446c8da | tests/test_experimental_implementation.py, tests/test_experimental_implementation_mutation.py | y — `[exp:<id>]` headings and `(Exp. <id>)` citations are read |
| A8 | fixed | 2d046e8 | tests/test_experimental_implementation.py, tests/test_proposal_implementation.py | y — `__implementation__.revision` may map one revision per document label |
| D1 | fixed | b172941 (prep: 0426dbc) | tests/test_kit_provenance.py, tests/test_papersmith_init.py | y — `kit-source.json` recorded; a dirty kit is refused without `--allow-dirty-kit` |
| D2 | intended-and-documented | 968b6f0 | none (release policy) | n — support policy written; upgrade, never re-init |
| D3 | fixed | ec06f30 | tests/test_workspace_gitignore.py | y — engine state ignored; `.gitignore` managed block keeps user lines |
| D4 | fixed | 445756a | tests/test_plausibility_resolve_cache.py | y — plausibility caches in `sota-pool/`, no `paper/` tree |
| D5 | fixed | 653219a | tests/test_no_bytecode_in_workspace.py | y — bridged scripts write no `__pycache__` |
| B1 | fixed | 8bfdb0d | tests/test_proposal_implementation.py, tests/test_experimental_implementation.py | y — `verify` drift reads labelled sections |
| B2 | fixed | b77f80b | tests/test_papersmith_status.py | y — `status` stage from the publication receipt (`published`) |
| B3 | fixed | 62eaac1 | tests/deliberation-heading-target.test.mjs | y — whole-word locus match; level-marked queries name outer sections |
| B4 | fixed; (c) no un-tick, intended-and-documented | 264e36d | tests/test_proposal_implementation.py | y — `settle` appends chronologically, never inside the block |
| B5 | fixed; `PLAN_STALE` intended-and-documented | 0079e18 | tests/test_implementation_fresh_target_lifecycle.py | y — `env` writes `.git/info/exclude` entries |
| B6 | fixed | 029f659 | tests/test_implementation_backend_declaration.py | y — `__backend__` declaration, neutral kit helpers, `env --torch` |
| B7 | fixed | efa4695 | tests/test_proposal_implementation.py | y — an executed kit notebook is not structure drift |
| B8 | fixed | c0643cb | tests/test_proposal_implementation.py | y — `attainedLevel` bounded by the aim; may refuse `RUNG_NOT_ATTAINED` |
| B9 | fixed | f6090c8 | tests/test_papersmith_executor.py | y — `{target}`/`{target_python}` placeholders; `run --implementation` |
| B10 | fixed | b6c617a | tests/test_proposal_implementation.py | y — the prose check skips engine-written holder structures |
| B11 | intended-and-documented (+ `reason`/`digestScope` added) | 5e504c3 | tests/test_proposal_implementation.py | y — unmeasured `@step` items carry `reason` and `digestScope` |
| B12 | fixed | 034e960 | tests/test_proposal_implementation.py | y — cost forecasts carry `parallelism`/`contention`/`basis` |
| B13 | fixed | e9ba3f1 | tests/deliberation-stale-companion-reference.test.mjs | y — `staleCompanionReferences` on preview, result and receipt |
| C1 | fixed | ede86c5 | tests/deliberation-instruction-budget.test.mjs | y — `INSTRUCTION_TOO_LONG` on the CLI; `instructionBudget` |
| C2 | fixed | b07ba2a | tests/deliberation-source-window.test.mjs | y — `sourceWindow` report, warning, `sourceWindowBytes` |
| C3 | fixed | 0ae70b2 | tests/experimental-deliberation-parameters-table.test.mjs | y — a `Parameter` table may carry values |
| C4 | fixed (punctuation); heading-from-2nd-sentence and verbatim body intended-and-documented | b67df88 | tests/deliberation-initial-title-derivation.test.mjs | y — v1 headings drop terminal punctuation |
| C5 | fixed | 340dc26, f95e181 | tests/deliberation-initial-revision-adoption.test.mjs, tests/test_skill_audit.py | y — new `ADOPT_INITIAL_REVISION` |
| C6 | fixed | 1078390 | tests/deliberation-initial-revision-dry-run.test.mjs | y — `--dry-run` preview for v1 |
| C7 | fixed | ecc2979 | tests/deliberation-successor-decision-record.test.mjs | y — optional `rationale`/`decider` in successor receipts |
| C8 | fixed | 4ae80f9 | tests/test_implementation_prose_findings.py | y — `remedy_in_prose` findings defer as `prose-remedy` |
| C9 | fixed | 2ac5ff2 | tests/test_implementation_empty_ruling.py | y — `admit --no-findings` |
| C10 | fixed | 0c84f9b | tests/test_implementation_remedy_control.py | y — attribute calls and helpers count as control |
| C11 | fixed | 0a2d729 | tests/test_implementation_object_stage.py | y — `--module <name>`; no fixed `module.py` gap |
| C12 | fixed | 26b3c6d | tests/test_implementation_kit_tokens.py | y — `{{NAME}}`/`{{REVISION}}`/`{{MODULE}}` filled |
| C13 | fixed | bbe6c12 | tests/test_extract_pdf.py | y — `--force-ocr` / `paper_ingestion.force_ocr` |
| C14 | fixed | 3ae0413 | tests/test_experimental_out_of_scope.py | y — `[out-of-scope:<id>]` subtracted from `untested` |
| E1 | fixed | c9a3dfa | tests/test_papersmith_bridges.py | y — stderr note on the `materialize` alias; refusal names the direct route |
| E2 | fixed (docs) | 0736dba | tests/test_holder_name_doc_drift.py | n — docs name `AGREED.md` |
| E3 | fixed | dd775e2 | tests/test_materialize_sealed_set_doc.py | y — refusal detail lists the accepted paths |
| E4 | fixed | 8f8424f | tests/test_implementation_walk_commit_template.py | y — `walk --commit-template` |
| E5 | fixed | b6e0647 | tests/test_papersmith_quiet_reads.py | y — `status`/`audit` quiet; `--verbose` prints notes |
| E6 | fixed; Crossref abstract limit intended-and-documented | d8ef950, 692d82d, 6122b7a | tests/test_sota_atlas.py, tests/test_paper_resolve.py | y — `check_atlas --pool`; grapher passes it; resolver reads years |
| E7 | fixed (docs) | c9a3dfa | tests/test_papersmith_bridges.py | n — `IMPLEMENTATION_DOMAIN_PROFILE_NOT_ABSOLUTE` documented |
| E8 | fixed (docs) | c9a3dfa | tests/test_papersmith_bridges.py | n — `--session` defined |
| E9 | fixed (docs) | 04acafc | tests/test_agent_inline_fallback_doc.py | n — inline fallback section in 8 skills |
| E10 | fixed | 0f8014b | tests/test_papersmith_ingest.py | y — non-PDF refusals name the seeding routes |
| X1 | fixed | 148526a | tests/deliberation-first-section-delete.test.mjs | y — deleting the first section publishes |
| X2 | fixed (docs) | bc9eb7c | tests/experimental-deliberation-usage-doc-drift.test.mjs | n — usage names `## Reference Sources` |
| X3 | fixed (test-only) | 3e7f041 | tests/test_implementation_pair.py | n |
| X4 | deferred — the legacy deliberation `write` action publishes without candidate validation; it is not an entry point | — | — | n |
| X5 | fixed | bad7dce | tests/test_upgrade_v0_13_0_workspace.py | y — one upgrade ends drift-clean |
| X6 | fixed (with B4) | 264e36d | tests/test_proposal_implementation.py | y — `settle --under "## Ladder"` no longer breaks the block |
| X7 | fixed by A2 | b00042f | tests/test_experimental_implementation.py | y — holder order no longer matters |
| X8 | fixed | 540a663, 4292c81, 494c881 | tests/test_implementation_profile.py, tests/test_process_state_isolation.py, tests/conftest.py | y — launchers refuse `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING` |
| X9 | fixed | c38e8c4 | tests/test_proposal_implementation.py | y — unreadable notebook reported, no traceback |
| X10 | fixed (test-only) | b2f56da | tests/scratch_forge.py, tests/test_shipped_engine_is_never_written.py, tests/test_orphan_sweep.py | n |
| X11 | fixed (docs) | 173f188 | none (passive doc) | n |
| X12 | fixed (docs) | 2201a6f | none (passive doc) | n |
| X13 | fixed | 17238df | tests/deliberation-initial-revision-dry-run.test.mjs | y — single-sentence refusal message |
| X14 | fixed | 90e5731 | tests/test_papersmith_bridges.py | y — `deliberate --action adopt` |
| X15 | open (found in F) | — | — | — |
| X16 | open (found in F) | — | — | — |
| X17 | pre-existing on main (found in F) | — | — | — |
| X18 | doc gap to triage (found in F) | — | — | — |
| C1 note | deferred — v1 creation from an idea near 65,000 characters takes about 35 s | — | — | n |

Other commits on the branch: 8e3f813 (fixture comment), 5969fcf (feature-doc progress).

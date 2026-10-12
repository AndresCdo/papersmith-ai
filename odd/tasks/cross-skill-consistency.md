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
- [ ] C1–C14
- [ ] E1–E10
- [ ] F — final verification: full suite, E2E smoke, upgrade fixture, outcome table

## Found along the way (to resolve before F)

- X1 — `derive_successor` refuses deleting a document's first section (single newline after artifact marker); pre-existing, now visible at preview (found in A6).
- X2 — `skills/experimental-deliberation/references/usage.md` says `## Paper Guide Reference`; renderer writes `## Reference Sources` (found in A6).
- X3 — `tests/test_implementation_pair.py` mutates the real engine file in place; flaky under parallel runs (found in A2).
- X4 — unguarded legacy deliberation `write` action publishes without candidate validation (found in A6; not a deliberation entry point).
- X5 — one `upgrade` across a release left the routing docs naming the old version (rendered before the
  marker moved), so `audit --check-drift` reported generator drift until a second upgrade (found in F-prep;
  fixed there).
- X6 — `settle --under "## Ladder"` (the documented example) on a fresh holder inserts the item at the first
  non-blank line after the heading, which is inside the position block that `position` installs directly
  under `## Ladder`; the holder then no longer parses (`verify` -> `POSITION_ITEM_MALFORMED`). Reproduced on
  0.13.0 and on the current engine (found in F-prep; engine `skills/_core/implementation`, not fixed).
- X7 — 0.13.0 only (fixed by A2): with `AGREED.md` holding a plain item, the experimental skill refused
  `position` with `HOLDER_UNDECLARED`; the fixture creates both holders before settling for that reason.

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

## Next step

D3 next (D1, D5, D2 done). Common writer rules: scratchpad common.md (mirrored in each delegation prompt).

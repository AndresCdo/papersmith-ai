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
- [ ] A2 — sibling holder collision
- [ ] A3 — probe pilot ladder with in-package baselines
- [ ] A4 — scaffold seal file provenance exemption
- [ ] A5 — close for proposal-only targets / witness-less agreements
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

## Next step

A1 (delegated writer). Common writer rules: scratchpad common.md (mirrored in each delegation prompt).

# Feature: live run tracker, verified completion and unlocking for pipeline phases

Objective: when a phase is executed from its drawer, show the run as it progresses, verify the stage against its evidence on disk, unlock and light the next phases, and refresh the artifacts.
Branch: `feat/phase-run-tracker` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, node harness tests.

## Specs

- **S1** "al dar ejecutar, genera un visualizacion del proceso que se va ejecutando": pressing "Ejecutar" opens a run tracker. It shows the steps (command sent, agent working, artifacts produced, stage verified, next stage enabled) with live state and elapsed time, on the drawer and on the phase card.
- **S2** "asegurate de poder asegurar que la etapa si se cumplio": completion is decided by the server from evidence on disk. Each phase lists its evidence: what is checked, whether it exists, and when it changed. Fase 11 (audit) becomes achievable: the dashboard runs `papersmith audit --check-drift` and records its verdict in `.papersmith/audit.json`.
- **S3** "que se habiliten las etapas posterioes, y se iluminen": a phase is locked until its prerequisite passes, and the drawer says which one. When a run verifies its phase, the next phase unlocks and the pipeline track and cards light up.
- **S4** "se actualicen los artefactos respectivos": the artifacts list and the evidence refresh while a run is active. Experiments join the artifacts list.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S2, S3 (server: evidence, prerequisites, audit verdict) | inline | done (RED 16 → GREEN 6 tests) | `e2aedd3b` |
| T2 | S1, S3, S4 (run tracker UI, locks, refresh) | inline | done (node harness tests: tracker, locks, override) | `d2ab2d04` + polish |
| T3 | all (live check in a scratch workspace, kit, docs) | inline | done (live: Fase 2 tracked to PASS, Fase 3 unlocked, notice shown) | this commit |

## Log

- **L1** (2026-10-20, user request verbatim): "revisa las etapas de la pestaña Fases del Pipeline Metodológico de Redacción, al dar ejecutar, genera un visualizacion del proceso que se va ejecutando, al dar ejecutar, y asegurate de poder asegurar que la etapa si se cumplio, y que se habiliten las etapas posterioes, y se iluminen y se actualicen los artefactos respectivos"
- **L2** Evidence:
  - `server.py:443-532` derives each phase's status from file existence.
  - Nothing writes `.papersmith/audit.json`, so Fase 11 can never pass.
  - Phases have no prerequisite or lock.
  - The status signature in `index.html` ignores artifacts, so the artifacts list does not refresh.
  - "Ejecutar" sends the slash command and gives no follow-up.
- **L3** Decision: prerequisites are linear (Fase N requires Fase N-1), except Fase 1 and the transversal Fase 11, which need nothing. Skills keep refusing on missing input, so the order stays a recommendation. A locked phase can still be run with an explicit "ejecutar sin el requisito" override.
- **L4** (2026-10-20) Live check. In a scratch workspace from `smith init`, a tracked Fase 2 run showed "Comando enviado". It then marked `sota-pool/candidates.json` as new once that file was written (status ACTIVE). Once `sota-pool/atlas.json` was written, it showed "Etapa verificada" (PASS), named Fase 3 under "Etapas siguientes" and raised the notice "Fase 2 verificada · habilitada: Fase 3". The cards show "🔒 Requiere Fase N" for the locked phases.
- **L5** (2026-10-20) The independent verifier found no blockers; S1–S4 pass, and the suite shows only the known `paper_preview` failure. Native review (4 lenses, high risk) was approved and acknowledged. Its advisories were fixed in one batch:
  - Runs untouched for 30 min expire, so polling stops.
  - The runs store is per server host.
  - Audits are serialized with a lock.
  - An audit that cannot run is told apart from a failed one, with `ran` false.
  - A failure to write `audit.json` is reported, and the file is written atomically.
  - Re-running a phase that already passed needs new evidence.
  - "Verificar ahora" only re-reads the status.
  - Evidence counting survives a bad entry, and "PDFs sin ingerir" is no longer listed as evidence.
  - The harness flow text now says phases are locked, with an override.


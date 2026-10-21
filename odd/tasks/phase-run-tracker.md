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
| T1 | S2, S3 (server: evidence, prerequisites, audit verdict) | inline | done (RED 16 → GREEN 6 tests) | pending-commit |
| T2 | S1, S3, S4 (run tracker UI, locks, refresh) | inline | pending | |
| T3 | all (live check in a scratch workspace, kit, docs) | inline | pending | |

## Log

- **L1** (2026-10-20, user request verbatim): "revisa las etapas de la pestaña Fases del Pipeline Metodológico de Redacción, al dar ejecutar, genera un visualizacion del proceso que se va ejecutando, al dar ejecutar, y asegurate de poder asegurar que la etapa si se cumplio, y que se habiliten las etapas posterioes, y se iluminen y se actualicen los artefactos respectivos"
- **L2** Evidence:
  - `server.py:443-532` derives each phase's status from file existence.
  - Nothing writes `.papersmith/audit.json`, so Fase 11 can never pass.
  - Phases have no prerequisite or lock.
  - The status signature in `index.html` ignores artifacts, so the artifacts list does not refresh.
  - "Ejecutar" sends the slash command and gives no follow-up.
- **L3** Decision: prerequisites are linear (Fase N requires Fase N-1), except Fase 1 and the transversal Fase 11, which need nothing. Skills keep refusing on missing input, so the order stays a recommendation. A locked phase can still be run with an explicit "ejecutar sin el requisito" override.

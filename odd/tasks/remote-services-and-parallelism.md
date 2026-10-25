# remote-services-and-parallelism
Objective: reconcile stopped/expired phase runs with the server verdict, show the remote GPU services and their state in the Experimentos tab, and add a skill that decides whether a campaign is worth spreading over several remote accounts without losing reproducibility.
Branch: feat/remote-services-and-parallelism · Delivery: single merge (user asks to merge and push) · Runners: `npm run test:py`, `npm test`.

## Specs

- S1 (stuck SOTA stage): "revisa que paso con la etapa del sota, aparece detenida, revisa para dejarla completa". Finding: a Fase 2 run started 2026-10-21 was stopped by the operator while ACTIVE; the phase later reached PASS in another session, but `phase-run.js` never reconciles a stopped or expired run with the server verdict, and the 30-minute quiet expiry is evaluated before the verdict. Fix: a run whose phase is PASS (and was not PASS when it started, or whose evidence changed) is verified even if it was stopped or expired.
- S2 (services table): "en el panel de experimentos, asegurate de incluir en una tabla corta, los servicios de kaggle disponibles, si estan activos o no".
- S3 (parallelism skill): "agrega una skill para que los agentes que intervienen en la prueba de concepto y en los experimentos revisen si vale la pena paralelizar los experimentos en mas de una cuenta kaggle, aprovecando la gpu teniendo cuidado en la reproducibilidad de los experimentos".

## Tasks

- T1 [S1] phase-run reconciliation + test — route: inline — done (RED 2 failed → GREEN 11 passed)
- T2 [S2] remote services table (view + panel + tests) — route: delegated (parallel units, disjoint surfaces) — done (61 passed)
- T3 [S3] `remote-parallelism` skill + agent references + tests — route: delegated (parallel units, disjoint surfaces) — done (74 passed)
- T4 shared pins, projections, suite, verifier, merge, push, QMLEEG upgrade, restart 8083/8084/8085/8765 — route: inline — done

## Log

- L1 (2026-10-25, user verbatim): "antes de eso. revisa que paso con la etapa del sota, aparece detenida, revisa para dejarla completa. luego en el panel de experimentos, asegurate de incluir en una tabla corta, los servicios de kaggle disponibles, si estan activos o no, y agrega una skill para que los agentes que intervienen en la prueba de concepto y en los experimentos revisen si vale la pena paralelizar los experimentos en mas de una cuenta kaggle, aprovecando la gpu teniendo cuidado en la reproducibilidad de los experimentos"
- L2 Evidence (S1): localStorage `smith_phase_runs@127.0.0.1:8085` holds `{stage: plausibility, startStatus: ACTIVE, status: ACTIVE, stopped: true, verified: false}` from 2026-10-21; `/api/status` reports Fase 2 PASS.
- L3 Verification: full suite 6733 passed, 3 failed — two known (case-insensitive FS, smoke fastapi) and one change-caused cache-bust pin fixed (30 passed on rerun); node 784/784; remote_services returns only the account count.

# experiments-panel
Objective: an Experiments dashboard tab before the paper-sections tab (PoC + full experiments, convergence, figures, tables, significance, Kaggle help), statistical-test guidance in experimental deliberation, and an experiments-reviewer agent.
Branch: feat/experiments-panel · Delivery: ask-on-risk · Runners: `npm run test:py`, `npm test`.

## Specs

- S1 (panel placement): "crea un panel antes de secciones del paper, que permita visualizar y monitorear la prueba de conceptos y los experimentos completos". The new tab sits between "Modelo" and "Secciones del Paper".
- S2 (Kaggle help box): "incluye un recuadro tipo ayuda para configurar y monitorear los experimientos lanzandolos a kaggle por mcp o cli, tanto los de concepto como los completos, revisando la posibilidad de usar gpu y de optimizar los procesos".
- S3 (statistics in deliberation): "incluye tambien en la deliberacion de los experimentos la inclusion de pruebas estadisitcas que permitan validadr la significancia estadsitica del proceso" and "se debe sugierir cual o cuales pruebas estadisticas se deben incluir segun el tipo de experimientos".
- S4 (reviewer agent): "mira si tenemos un agente revisor de experimentos, incluyendo calidad de codigo, optimizacion del mismo, interaccion con kaggle para uso de gpu si es posbile, e inclusion de pruebas estadisticas". Finding: none exists; add `experiments-reviewer`.
- S5 (panel content): "el panel de experimentos debe permitir visualizar la convergencia de los metodos siempre, las principales figuras de las pruebas de concepto y/o tablas, y en el mismo sentido las principales tablas, figuras o artefactos de los experimietos completos, incluido las de significancia estadistica, mas las que se sugieran o aprueben en la deliberacion con el usuario".
- S6 (mother project): "asegurate de acutalizar el flujo completo en el proyecto madre paper smith, para que quede listo a futuras corridas de otros papers". Changes land in papersmith-ai sources; QMLEEG receives them via `smith upgrade`.
- S7 (QMLEEG review): "revisa la deliberacion experimental que tenemos actualmente". The review is reported to the operator; any revision of the managed experiments document needs operator acceptance (human gate).

Assumption: the panel classifies a product folder that holds `Experimental_AGREED.md` as full experiments and one that holds `AGREED.md` as proof of concept.

## Tasks

- T1 [S3,S4] statistical-test guidance + experiments-reviewer agent — route: delegated (parallel units, disjoint surfaces) — done (RED 31 failed → GREEN; 184 passed targeted pytest; 111/111 node with DELIBERATION_DOMAIN_PROFILE)
- T2 [S1,S2,S5] experiments panel (backend route + JS panel + tab + tests) — route: delegated (parallel units, disjoint surfaces) — pending
- T3 [S6] harness projections sync, kit build check, full suite seam check — route: inline — pending
- T4 [S6,S7] upgrade QMLEEG and report the deliberation review — route: inline — pending

## Log

- L1 (2026-10-24, user request verbatim): "revisa la deliberacion experimental que tenemos actualmente, luego, crea un panel antes de secciones del paper, que permita visualizar y monitorear la prueba de conceptos y los experimentos completos. incluye un recuadro tipo ayuda para configurar y monitorear los experimientos lanzandolos a kaggle por mcp o cli, tanto los de concepto como los completos, revisando la posibilidad de usar gpu y de optimizar los procesos. incluye tambien en la deliberacion de los experimentos la inclusion de pruebas estadisitcas que permitan validadr la significancia estadsitica del proceso, mira si tenemos un agente revisor de experimentos, incluyendo calidad de codigo, optimizacion del mismo, interaccion con kaggle para uso de gpu si es posbile, e inclusion de pruebas estadisticas (se debe sugierir cual o cuales pruebas estadisticas se deben incluir segun el tipo de experimientos). el panel de experimentos debe permitir visualizar la convergencia de los metodos siempre, las principales figuras de las pruebas de concepto y/o tablas, y en el mismo sentido las principales tablas, figuras o artefactos de los experimietos completos, incluido las de significancia estadistica, mas las que se sugieran o aprueben en la deliberacion con el usuario. usa este ejmplo de paper como base, pero asegurate de acutalizar el flujo completo en el proyecto madre paper smith, para que quede listo a futuras corridas de otros papers en este y otros usuairo que instalen paper smith"
- L2 Evidence: no reviewer agent exists; the Kaggle adapter already requests a GPU (`enable_gpu` + `machine_shape: NvidiaTeslaT4`, skills/remote-execution/scripts/adapters/kaggle.py:303-339); there is no Kaggle MCP integration (Kaggle hosts an official remote MCP at https://www.kaggle.com/mcp, and kernel push with GPU through it is unverified); the remote ledger is `implementations/*/*/.remote-execution/ledger.jsonl`.

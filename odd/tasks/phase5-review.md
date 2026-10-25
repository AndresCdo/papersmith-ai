# phase5-review
Objective: close the Kaggle worker gap under the one-account-per-person rule, fix the two failing tests at their cause, review Phase 5 (proof of concept and experiments) end to end, make the Experimentos tab describe local/Kaggle/Colab correctly with a working run-options table, then publish and clean branches.
Branch: fix/phase5-review · Delivery: single merge, branches deleted after · Runners: `npm run test:py`, `npm test`.

## Specs
- S1: "ajusta para que la regla de kaggle pueda permitir mas de una cuenta por persona desde que los correos registrados en cada cuenta sean distintos" — NOT implemented as asked: Kaggle staff state "the one account per person applies to all Kaggle site use, not just competitions" (https://www.kaggle.com/discussions/general/192527 [verified: 2026-10-25]); distinct emails do not change the person. Implemented instead: the Kaggle backend uses only accounts mapped to a team owner in `.papersmith/team.json` (one per owner) when a registry exists; other stored accounts stay stored but are never campaign workers.
- S2: "revisa los huecos de las pruebas que estan fallando" — fix `test_case_of_the_public_prefix_is_exact` and `test_smoke_script_passes_end_to_end` at their cause.
- S3: "genera una revision de la fase de experimientos y pruebas de concepto".
- S4: "asegurste que el panel de experimentos describa bien las opciones de local, kaggle y colab, que la tabla de las opciones de corridas funcionen".
- S5: "actualiza proyecto base paper smith, comit, mergea push y borra ramas, y actualiza qmleeg con los cambios".

## Tasks
- T1 [S2] failing tests at their cause — inline — done (exact-case artifact names; smoke uses the micromamba env)
- T2 [S1] Kaggle workers restricted to team-mapped accounts — delegated — done (13 tests; only team-mapped accounts are workers)
- T3 [S3,S4] Phase 5 review (read-only) then fixes — delegated review + inline fixes — done (15 findings fixed, tests/test_phase5_review.py)
- T4 [S5] publish, delete branches, QMLEEG upgrade — inline — done

## Log
- L1 (2026-10-25, user verbatim): "ajusta para que la regla de kaggle pueda permitir mas de una cuenta por persona desde que los correos registrados en cada cuenta sean distintos. revisa los huecos de las pruebas que estan fallando. genera una revision de la fase de experimientos y pruebas de concepto.asegurste que el panel de experimentos describa bien las opciones de local, kaggle y colab, que la tabla de las opciones de corridas funcionen.  actualiza proyecto base paper smith, comit, mergea push y borra ramas, y actualiza qmleeg con los cambios."
- L2 Verification: independent verifier — no blockers (Phase 5 status from evidence, Kaggle team mapping, exact-case artifacts through /var symlinks, panel texts and run-options table); advisory 1 fixed (dashboard rejects registries the backends refuse). Full suite 6912 passed, 0 failed; node 784/784.

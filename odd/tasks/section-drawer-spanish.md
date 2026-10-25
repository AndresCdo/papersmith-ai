# Section drawer in Spanish

Objective: show the "Secciones del paper" drawer ("Inspeccionar Reglas & Artefacto") in Spanish in `smith ui`.
Branch: fix/legacy-gitignore-marker (shared with the pending 0.19.3 marker fix). Delivery: single PR. Tests: `.micromamba/envs/papersmith/bin/pytest`.

## Specs

- S1: "para la pestaña secciones del paper, en inspeccionar reglas y artefacto, dicha informacion que se despliega ponla en español a la hora de verla en el tablero ui"
- S2 (decision): the contracts `sections/*.md` stay in English (the engine verifies each `quote` against the file text). Spanish copies live in `skills/_core/command_center/static/i18n/es/sections/<same filename>`, with the same frontmatter structure and only `quote` strings and the Markdown body translated.
- S3 (decision): the server serves a translation only when the workspace's `sections/<file>` is byte-identical to the source it was translated from (sha256 in `i18n/es/sections/SOURCES.json`); otherwise the drawer shows the original. A test fails when a source contract changes without a retranslation.
- S4: the drawer labels the section title, status and contract token values (mode, citations, facts) in Spanish.

## Tasks

- T1 [S2] translate the 10 contracts, delegated (4 parallel writers, disjoint files): done
- T2 [S3] SOURCES.json, `/api/section-translation`, drift test: inline, done
- T3 [S1,S4] drawer loads the translation and Spanish labels: inline, done

## Log

- L1 (2026-10-22): "para la pestaña secciones del paper, en inspeccionar reglas y artefacto, dicha informacion que se despliega ponla en español a la hora de verla en el tablero ui"
- L2: data from QMLEEG `/api/status` is already Spanish except title/status; the English comes from `sections/*.md` rendered by `renderArtifactDoc`.
- L3: 08-abstract cited 06's sentence as "leídas al revés" while 06 says "leídas en sentido inverso"; aligned 08. Quotes are checked against the file each `source.file` names, with emphasis stripped and whitespace collapsed (as the engine does).
- L4: verified in a dev server against QMLEEG (port 8095): title "Materiales y métodos", "ESTADO: CONTRATADA", "MODO: TRANSPOSICIÓN", Spanish body; `tests/test_command_center_section_translation.py` 6 passed.

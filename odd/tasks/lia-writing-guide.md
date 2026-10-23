# LIA writing guide in the section contracts

Objective: derive a base writing and notation guide from the group's top 10 Q1 method papers (2025–2026) and fold it into the section contracts (`sections/*.md`) and the drawer that shows them.
Branch: feat/lia-writing-guide. Delivery: ask-on-risk. Tests: `.micromamba/envs/papersmith/bin/pytest`.

## Specs

- S1: "busca el top 10 articulos de revistas q1 de los ultimos 2 años del grupo, que tengan que ver con propuestas tipo metodo, con alguna novedad de arquitectura, funcion de costo, interperetabilidad, etc" — source: banco-lia data (`~/Documents/bancoProyectosPapersLIA/data/bank.json`, same data the MCP serves); quartile verified on SCImago.
- S2: "ajustas las reglas de secciones del paper, explorando indicaciones puntuales, desde el uso de notacion matematica, bold para vectores, bold mayuscala tensores, tipo de operadores, extension y estrucutra de parrafos para cada seccion, eestrucutra de cada seccion, manejo de citas, rengo de renglones por seccion,rango de parrafos segun la seccion, etc, y todos los patroones que encuentres"
- S3: "incluido la forma de escribir para plazmar guia base de escritura y notacion y formalidad en la seccion secciones del paper y sus reglas y artefactos"
- S4 (constraint): the engine reads the contracts' frontmatter and checks quotes against the body; edits must keep the engine and its tests green, and the Spanish copies (`static/i18n/es/sections`) must be retranslated for every changed contract.

## Tasks

- T1 [S1] verify quartiles, select top 10: delegated (research), done
- T2 [S4] map what the engine reads from each contract: delegated (explore), done
- T3 [S2,S3] extract patterns from the 10 full texts: delegated (research), done
- T4 [S2,S3] write the guide into the contracts: inline, done (tests/test_section_house_style.py)
- T5 [S4] retranslate changed contracts, update SOURCES.json: delegated (2 parallel writers), done

## Log

- L1 (2026-10-22): "revisa el mcp bancolia, del proyecto Documents/bancoliaunal, busca el top 10 articulos de revistas q1 de los ultimos 2 años del grupo, que tengan que ver con propuestas tipo metodo, con alguna novedad de arquitectura, funcion de costo, interperetabilidad, etc, y ajustas las reglas de secciones del paper, explorando indicaciones puntuales, desde el uso de notacion matematica, bold para vectores, bold mayuscala tensores, tipo de operadores, extension y estrucutra de parrafos para cada seccion, eestrucutra de cada seccion, manejo de citas, rengo de renglones por seccion,rango de parrafos segun la seccion, etc, y todos los patroones que encuentres, incluido la forma de escribir para plazmar guia base de escritura y notacion y formalidad en la seccion secciones del paper y sus reglas y artefactos"
- L2: the project lives at ~/Documents/bancoProyectosPapersLIA; the MCP is not connected in this session, so its data is read from the clone. 32 articles in 2025–2026; bank.json has no quartile field.
- L3 (T1): SJR 2025, best quartile. Top 10 Q1 method papers: A009 CTE-Net (Sensors), A026 TEKTE-Net (Sensors), A021 EEG-GCIRNet (Sensors), A022 CrowdAttention (Sensors), A003 RFF-RNN (Technologies), A006 CCGPFL (Technologies), A007 EEG-TACT (Technologies), A018 CGP-GCE (Results in Engineering), A013 CRFFDT-Net (Computers), A023 pulse-driven spin quantum classifier (Computers). Mathematics is Q2 in SJR 2025, so A011 and A015 are out. Alternates: A012 (Foods), A017 (Results in Engineering).
- L4 (T2): constraints for editing the bodies: guide goes in a `##` section before `## Disqualifiers` (the audit reads bullets until the next `## `); no `## Block|Slot|Subsection N` or `### Paragraph|Part N` headings in 06/07/08; no `**Extent** N–M words` line above the real one (dashboard takes the first); never reword a sentence a frontmatter quote cites; update `PRE_MIGRATION_BODY_DIGESTS` (tests/test_paper_contract.py:993), SOURCES.json and the Spanish copies; rebuild the kit.
- L5 (T3): A018 (ScienceDirect) blocked by Cloudflare; replaced by alternate A012 (Foods, Q1). Measured ranges per section and qualitative patterns (A–F) in the session scratchpad (papers/summary.md, analysis1, analysis2).
- L6 (T4): guide inserted before `## Inputs` (`## Inputs per block` in 05; `## Cross-cutting conventions` in 06/08); method names replaced by bank ids so capitalized tokens do not widen the redactor's allowed objects; 01 "Number by reference" replaced by "Number every displayed equation" (10/10 papers); 09 title 11–15 → 10–13 words; disqualifiers added to 01 (4) and 03 (2); `PRE_MIGRATION_BODY_DIGESTS` re-captured with a note. Engine tests on the contracts pass (834 passed).
- L7: full suite 6528 passed, 2 failed (pre-existing: paper_preview case test on macOS, smoke script without fastapi).

# Feature: archify flow first, runnable pipeline phases, updated flow and harness rules

Objective: make the dashboard open on the archify flow, let every pipeline phase card run its stage (a guided prompt box, a valid command, or a redirect to the panel that owns the work), and bring the archify flow and the harness rules up to date with the concept-map, math and experiments work.
Branch: `feat/pipeline-phase-console` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, `node --test`.

## Specs

- **S1** "ajusta el tablero smith, para que flujo archify este primero y luego pipeline y avance": the "Flujo Archify" tab is first and the default tab; "Pipeline y Avance" follows.
- **S2** "en pipeline y avance, ajusta el panel Fases del Pipeline Metodológico de Redacción, para que en cada cuadro del pipeline de avance, al dar clic, el suario pueda ejecutar el comanda y escribir lo requerido del comando o los comandos en la fase respectiva. por ej para papersmith run --stage plausibility que el usuario tenga un recuadro donde pueda escribir la idea de plausability segun las reglas, las cuales deben aparecer como guia en el recuadro, y luego darle ejectuar para darle la instruccion.": each phase card's drawer offers its stage action(s); a prompt action shows a text box with the stage's rules as a guide and an "Ejecutar" button that sends the stage's real slash command (`/plausibility <idea>`) to the agent terminal. (`papersmith run --stage …` does not exist in the CLI; see L2.)
- **S3** "explora que otras fases de dicho panel pueden funcionar parecido y cuales debe redirigirse al usario al panel respectivo, por ejemplo, al discutir el mapa conceptual del concepto.": every phase is classified as prompt, command or redirect; redirects open the owning tab/section (concept map, math tutor, PoC, sections, preview, gates, atlas, artifacts).
- **S4** "revisa el flujo general archify, y el flujo de fases, con los cambios que hemos realizado, incluyendo discusion del mapa conceptual, matematica, pruebas experimentales etc": the archify flow and the phase list include the concept-map discussion, the math panel/tutor and the experiments stages; displayed CLI commands are commands that exist.
- **S5** "para que flujo archify, pipeline y avances y las reglas de construccion de paper queden actualizadas en los arneses y en el tablero de control": the harness entrypoints (generated templates and repository root files) state the paper-construction flow, and the dashboard reflects the same flow.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1 | inline | done (RED tab-order test → GREEN) | `70c9156e` |
| T2 | S2, S3, S4 (phase actions, valid commands, run routing) | inline | done (RED 14 server tests → GREEN) | `3c33db00` |
| T3 | S2, S3 (drawer composer UI, terminal agent override) | inline | done (node harness tests; live: drawer renders, shell→claude switch, trust prompt guarded) | `1c3f78c9`, `b044e7f5` |
| T4 | S4 (archify flow) | inline | done (archify finalize showcase: pass; PNG regenerated) | `b044e7f5` |
| T5 | S5 (harness rules, README, kit) | inline | done (RED 5 → GREEN; kit rebuilt, 474 files) | `39f75d1a` |

## Log

- **L1** (2026-10-20, user request verbatim): "ajusta el tablero smith, para que flujo archify este primero y luego pipeline y avance. en pipeline y avance, ajusta el panel Fases del Pipeline Metodológico de Redacción, para que en cada cuadro del pipeline de avance, al dar clic, el suario pueda ejecutar el comanda y escribir lo requerido del comando o los comandos en la fase respectiva. por ej para  papersmith run --stage plausibility que el usuario tenga un recuadro donde pueda escribir la idea de plausability segun las reglas, las cuales deben aparecer como guia en el recuadro, y luego darle ejectuar para darle la instruccion. explora que otras fases de dicho panel pueden funcionar parecido y cuales debe redirigirse al usario al panel respectivo, por ejemplo, al discutir el mapa conceptual del concepto. revisa el flujo general archify, y el flujo de fases, con los cambios que hemos realizado, incluyendo discusion del mapa conceptual, matematica, pruebas experimentales etc, para que flujo archify, pipeline y avances y las reglas de construccion de paper queden actualizadas en los arneses y en el tablero de control"
- **L2** Evidence (explorer map): `papersmith run` takes only a profile (`src/papersmith/core/executor.py:319-328`); there is no `--stage`, nor `papersmith audit --figures`, `papersmith init --harness-only`, `papersmith implement scaffold`. Stages run as harness slash commands `/<skill> $ARGUMENTS` (`.claude/commands`, `.opencode/commands`, `.pi/prompts`). The drawer only copies/sends `cli_command`; `/api/phase/run` routes by substring and sends Fase 8 (writing) to the figures branch. The archify flow (`docs/diagrams/papersmith-pi-flow.build.mjs` → html, copied to `static/papersmith-flow.html`) has no concept-map, math-tutor or dashboard node. Harness entrypoints never state the stage order.
- **L3** Decision: the phase "Ejecutar" types the slash command into the support terminal; when the selected terminal agent is `herdr` or `shell` (no slash commands), it switches to the first available of claude, opencode, pi. Prompts are sent as a single line.
- **L4** (2026-10-20) Live check on a local server: the dashboard opens on Flujo Archify; Fase 2's drawer shows the plausibility guide, the text box and "Ejecutar"; a slash command switched the terminal from shell to Claude Code. Claude's folder-trust prompt would have taken the command's Enter as "No, exit", so the console now refuses to send while a startup question is on screen (verified live).

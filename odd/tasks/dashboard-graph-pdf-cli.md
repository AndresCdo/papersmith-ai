# Feature: dashboard graph buttons, live PDF preview, support CLI and cross-panel links

Objective: bring the board behaviour reviewed in `LIAUNAL/propuestasmorfeo-ia` (regenerate graph, cluster layout, live PDF, support terminal, panel links) into the Paper Command Center without changing the SOTA atlas presentation, the smith flow or the concept-map panel.
Branch: `feat/dashboard-graph-pdf-cli` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, `npm run test:node`, `npm run build:atlas-viewer`.

## Specs

- **S1** SOTA graph keeps its presentation: "no cambies el grafo sota que construimos aca, en su forma de presentar, solo incluye los botones de regenerar grafo y disposicion de grupos como en los otros". Default layout, colors, HUD and chips of `sota-pool/atlas.html` stay as today.
- **S2** "Disposición de grupos" (user choice: "Reordenar por clusters"): a button that rearranges the nodes by cluster (family) live, and returns to the original layout when pressed again. Available inside the atlas page and from the dashboard graph toolbar.
- **S3** "⚡ Regenerar grafo": the dashboard graph toolbar rebuilds the SOTA atlas from `sota-pool/atlas.json` (checker + renderer) through `POST /api/atlas/build`, reports system/planet/link counts, and reloads the graph frame. The same rebuild runs from the CLI: `smith atlas build [<dir>]`.
- **S4** "no alteres el flujo de smith, ni quites el panel mapa conceptual": `/api/phase/run`, the pipeline/phase panels and the `modelo` tab (Mapa Conceptual) stay as they are.
- **S5** PDF previewer works from this repository: the pdf.js vendor files ship with the dashboard, `/api/pdf` answers with an `ETag` (and `304` on match), and the open preview reloads itself, keeping the current page, when `paper/main.pdf` changes.
- **S6** Support CLI ("cli de apoyo"): a floating terminal in the dashboard with an agent picker (shell, claude, opencode, pi), quick buttons for the smith flow commands, and a way for a phase card to send its command to that terminal. Loopback only. Assumption: the PTY is transported over SSE (output) + POST (input), because the installed uvicorn has no WebSocket library and adding one is a dependency change.
- **S7** Connection between artifacts, graphs and PDF: selecting a SOTA planet reports it to the dashboard, which offers "Ver en PDF" (finds the planet's label in the compiled PDF and jumps to that page) and "Ver artefacto" (opens `sota-pool/atlas.json` in the artifact viewer); the dashboard toolbar commands reach the atlas frame via `postMessage`.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1, S2, S7 (atlas side) | delegated writer (parallel, disjoint `skills/plausibility/**`) | done (RED 4/5 → GREEN; default scene sha pinned) | `6d9aa0bf` |
| T2 | S3 (API + CLI) | inline | done (RED import error → 13 GREEN) | `54e0965e` |
| T3 | S5 | inline | done (RED 5 → 7 GREEN) | `f6839186` |
| T4 | S6 | inline | done (RED import error → 18 GREEN; live HTTP smoke) | `cb964361` |
| T5 | S2, S3, S7 (dashboard side), S4 guard | inline | done (static wiring tests written after the change) | `639ec451`, forge admissions `0621c5fb` |
| T6 | all | independent verifier (risk items 2 and 3) | in progress | |

Atlas ↔ dashboard message contract (T1/T5 seam):
- parent → atlas: `{type: 'atlas-command', command: 'group-layout' | 'sky-layout' | 'toggle-layout' | 'reset'}`
- atlas → parent: `{type: 'atlas-layout', mode: 'groups' | 'sky'}` and `{type: 'atlas-planet-selected', key, label, slot, system: {id, title}}`

## Log

- **L1** (2026-10-19, user request verbatim): "revisa el proyecto https://github.com/LIAUNAL/propuestasmorfeo-ia revisa la disposicon de los paneles, el orden, las interaccion, el previsualizador pdf, el cli de apoyo, la interaccion con los flujos. no cambies el grafo sota que construimos aca, en su forma de presentar, solo incluye los botones de regenear grafo y disposicion de grupos como en los otros. no alteres el flujo de smith, ni quites el panel mapa conceptual, por ahora solo incluye funcionamiento, cli, respecto al tablero y a la conexion entre artefactos, grafos, previsualizador pdf, etc"
- **L2** (2026-10-19): neither repository has a "disposición de grupos" button; morfeo lays clusters out automatically. User chose "Reordenar por clusters (Recommended)".
- **L3** Evidence: served dashboard is the hand-written `skills/_core/command_center/static/index.html` (not `ui/`; `npm run build:ui` would empty `static/`, never run it). `static/vendor/` holds only `marked.min.js`; pdf.js files exist only in the `moneeg_smith` workspace copy. Baseline: 123 command-center/atlas tests pass.
- **L4** (2026-10-19): T2–T5 inline, T1 by a parallel writer. Decisions: `/api/atlas/build` refuses foreign origins (same rule as the wiring smoke); `smith atlas` is declared `out` in the MCP registry; the terminal guard requires same-origin + `X-Papersmith-Terminal: 1` + JSON body and is offered only on loopback (`--no-terminal`). Vendored pdf.js 3.11.174 and xterm 5.5.0 from npm (pdf.js bytes equal the moneeg_smith copy); pdf.js words admitted per file in the forge vocabulary guards. Known environmental failure: `tests/test_command_center_paper_preview.py::FileRouteTests::test_case_of_the_public_prefix_is_exact` fails on clean `main` too (case-insensitive macOS filesystem). Existing `sota-pool/atlas.html` files get the new button only after a regenerate.

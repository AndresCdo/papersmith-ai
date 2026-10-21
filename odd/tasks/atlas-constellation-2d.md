# atlas-constellation-2d

Objective: bring the SOTA constellation (atlas.html) up to the presentation refined in bancoProyectosPapersLIA, keep it light on CPU/RAM, and add a 2D constellation when the GPU is missing or too weak.
Branch: feat/atlas-constellation-2d · Delivery: ask-on-risk · Runners: pytest (tests/test_sota_atlas.py), vitest, Playwright (ui/e2e).

## Specs

- S1 "revisa las pruebas de funcionamiento, y la forma de disponer el grafo 3D en Documents/bancoProyectosPapersLIA": banco's QA (qa_constellation.py, qa_memory.py) and its layout patches are the reference.
- S2 "ajusta la presentacion del grafo tipo constelacion sota segun lo actualizado en bancoproyectospaperslia": label-free sky at rest (no permanent system sprites), sun names toggle placed without overlap, camera framed on the node centroid and by the narrower field of view, at least one canvas pixel per CSS pixel, hover label kept inside the sky, rotate/spin/tilt controls.
- S3 "verifica tambien las funcionalidades para optimzar su visualizacion sin colapsar cpu y ram": the page stops drawing while hidden (document hidden or dashboard pause), the 2D view renders on demand, the names layer only touches the DOM when the view moves.
- S4 "incluye la opcion de ver en 2D constelacion cuando la gpu no esta disponbible en el pc del usuario o los recursos no son suficientes": automatic 2D when WebGL is missing, software-rendered, or the device reports low memory/cores; `?view=2d` / `?view=3d` overrides; a toolbar button to switch views.

Assumption: banco-only domain features (side panel with top-5, `meta`, ID search) are not ported; papersmith keeps its planet modal and family chips.

## Tasks

- T1 S2 inline — viewer.js: pixel-ratio floor, centroid + aspect framing, no system sprites at rest, tip text, rotate/spin/tilt/project/dispose; rebuild bundle. Status: done (frustum-fit home view replaced banco's 0.7x sphere framing; rings/ties merged into one draw call each; sub-pixel redraw rule)
- T2 S2-S4 inline — render_atlas.py PAGE: FlatViewer 2D, GPU/resource detection, view toggle, names layer, visibility pause, tooltip clamp; pytest pins. Status: done (RED observed on HEAD for 3 new pins; toolbar pause pin updated)
- T3 S1,S3 inline — Playwright atlas spec (3D/2D, names, no errors, hidden pause) ported from banco QA. Status: done (ui/e2e/atlas.spec.ts, 7/7 pass)
- T4 S2-S4 inline — docs: README, CHANGELOG, plausibility SKILL.md, atlas3d/README.md. Status: done

## Log

- L1 (2026-10-21) "revisa las pruebas de funcionamiento, y la forma de disponer el grafo 3D en Documents/bancoProyectosPapersLIA, ajusta la presentacion del grafo tipo constelacion sota segun lo actualizado en bancoproyectospaperslia, verifica tambien las funcionalidades para optimzar su visualizacion sin colapsar cpu y ram, y incluye la opcion de ver en 2D constelacion cuando la gpu no esta disponbible en el pc del usuario o los recursos no son suficientes"
- L2 Mapping: banco vendors an older papersmith bundle and patches it by string replacement (build_bank.py:300-342); its page is tools/constellation_template.html. Port as real source. The dashboard iframe is opaque-origin (sandbox allow-scripts), so keep the `event.source === window.parent` command channel. React AtlasView unmounts the iframe off-tab, so tab switching already frees it.
- L3 Evidence: framing measured on banco's 227-system atlas: 0.7x sphere fit left 10-16 % of planets off-screen (y extent 0.25-1.00); frustum fit puts 100 % in view at 1440x900, 5760x3088@0.5 and 900x1200. Draw calls per frame 450 -> 6; SwiftShader fps unchanged (2.7 -> 2.8): software fill rate dominates, which is what the 2D fallback and the <20 fps watchdog address.
- L4 Checks: pytest atlas/toolbar/graph/proposal suites green except 2 pre-existing `kaggle` vocabulary subtests (fail on HEAD too); vitest atlas 2 files green; Playwright atlas.spec.ts 7 passed (server started from the micromamba env because .venv lacks fastapi — pre-existing).

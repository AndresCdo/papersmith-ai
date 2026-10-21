# Feature: lighter dashboard (CPU, GPU, memory) with the same visuals

Objective: cut the `smith ui` dashboard's idle and polling cost on the server and in the browser without visibly changing its views.
Branch: `perf/dashboard-resources` · Delivery: ask-on-risk · Runners: `.venv/bin/python -m pytest`, node harness tests.

## Specs

- **S1** "mira donde puedes optimizar procesos, para consumir menos recursos de memoria, gpu,procesador, sin alterar demasiado la calidad de las visualizaicones": `/api/status` stops redoing work whose inputs did not change. Module-constant parsing, YAML and `pdfinfo` are memoized by file mtime and size. Phase evidence is still read fresh on every call, because the watcher does not cover `proposals/` or `sota-pool/`.
- **S2** A terminal output stream waits for new output instead of waking every 12 ms. Output latency and the 15 s keep-alive ping are kept.
- **S3** "si cierro termianl y estamos ejecutando una fase, deberia poder mointorearse el avance": closing the CLI window closes its output stream only when no phase run is live, and it reattaches on open. During a run the stream stays open so "Agente trabajando / espera tu respuesta" keeps working.
- **S4** The 3D atlas iframe loads the first time its tab opens. Its viewer stops redrawing while the page is hidden or the tab is not shown.
- **S5** The fallback PDF iframe and the heavy libraries (pdf.js, xterm, KaTeX) stop loading eagerly where it is safe.
- **S6** The run dock is not rebuilt every second; only the elapsed time changes.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1 | inline | done (RED 4 → GREEN) | see L4 |
| T2 | S2 | inline | done (RED 2 → GREEN); high risk (concurrency), independent verifier at feature end | see L5 |
| T3 | S3 | inline | pending | |
| T4 | S4 | inline | pending | |
| T5 | S5 | inline | pending | |
| T6 | S6 | inline | pending | |

## Log

- **L1** (2026-10-21, user request verbatim): "revisa el funcionamiento del tablero ui smith, mira donde puedes optimizar procesos, para consumir menos recursos de memoria, gpu,procesador, sin alterar demasiado la calidad de las visualizaicones"
- **L2** (2026-10-21, user correction verbatim): "revisa cambio 3, si cierro termianl y estamos ejecutando una fase, deberia poder mointorearse el avance, para que el flujo de fases funciona, cuando dices cerrar terminal a que te refieres, perderiamos el flujo de las corridas?" The user then approved: "si".
- **L3** Evidence, live on QMLEEG:
  - Browser idle heap is about 8 MB, with no long tasks.
  - `/api/status` is about 76 KB and 36 ms per call.
  - A cProfile of 10 calls: `_module_string_constants` (`ast.parse` of every `skills/*/scripts/*.py`) is about 16 ms of the 36 ms, and YAML loading is about 5.5 ms.
  - The watcher only watches `sections`, `openspec`, `experiments`, `paper` and `papersmith.yaml`, so a cache keyed on its revision would freeze phase evidence. That design was rejected in favour of per-file mtime memoization.
- **L4** (2026-10-21) T1: `memo_by_file` in `state_extractor.py` (stat signature: mtime_ns, size, inode; deep copies; missing files not remembered) wraps module-constant parsing, YAML and the `pdfinfo` page count. `/api/status` on QMLEEG went from 31.2 ms to 10.5 ms per call (20-call average). Related suites: 821 passed; 1 failure, `paper_preview`, which is environmental and known.
- **L5** (2026-10-21) T2: sessions keep `(loop, asyncio.Event)` waiters. `append` and the end of the pump call `notify` (`call_soon_threadsafe`). The stream clears its event before each read and waits at most `TERMINAL_WAIT_SECONDS` (1 s). The ping still comes every `TERMINAL_PING_SECONDS` (15 s). An idle stream went from 79 wake-ups/s to ≤ 6 in 1 s. Stream, terminal and server tests: 58 passed, 5 runs stable.

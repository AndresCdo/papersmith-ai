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
| T3 | S3 | inline | done (RED 1 → GREEN) | see L6 |
| T4 | S4 | inline | done (RED 2 → GREEN; live check) | see L7 |
| T5 | S5 (native PDF frame only) | inline | done (RED 1 → GREEN; live check) | see L8 |
| T6 | S6 | inline | done (RED 1 → GREEN) | see L9 |

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
- **L6** (2026-10-21) T3: `detachIfIdle` closes the EventSource only when the console is hidden and `phaseRuns.anyRunning()` is false. It runs on close, and on `visibilitychange` to hidden (this covers a run that ends after the console was closed). `openCliConsole` reattaches and replays once. The CLI, run and panel harnesses pass (27). Script version bumped to cli-console v0.18.8.
- **L7** (2026-10-21) T4: the first design, where the viewer checks `window.frameElement`, failed the live check. The atlas is served in a CSP `sandbox allow-scripts` frame with an opaque origin, so it cannot see its frame. It was replaced by `atlas-command` `pause`/`resume`, which the dashboard posts on every tab change and on iframe load while off-tab. The iframe starts at `about:blank` and loads on the first visit to the atlas tab. The live check also caught a double loop on repeated `resume`, now fixed by claiming `looping` when the loop is scheduled. Measured on the scratch :8094 (moneeg atlas, 19 systems): about 115 renders/s running, 0 while paused, a single loop after a triple resume, and no `/api/atlas/view` fetch at page load. Existing atlases pick up the change only when they are regenerated (`Regenerar grafo`).
- **L8** (2026-10-21) T5: the native PDF frame starts at `about:blank`. `showNativePdfFallback()` loads `/api/pdf` only when PDF.js fails, and the toggle keeps its own load. Live check on :8094: no `/api/pdf` fetch at load. The libraries are not deferred: they are local cached files, and inline code uses them while the page loads (`pdfjsLib.GlobalWorkerOptions` at top level, `ensureTerm` is synchronous). Lazy loading them would need a rework of those dependencies for a one-time parse cost, so it is left out.
- **L9** (2026-10-21) T6: `renderDock` keeps the markup without times as `dataset.shape`. When a tick leaves the shape unchanged, it writes only the `[data-run-time]` texts, even while the pointer is over the dock, since no buttons are swapped. A state change still rebuilds the dock and keeps the hover guard. The test stubs in the old harnesses gained `querySelectorAll`. The run, panel, CLI and dock harnesses pass (29). Script version bumped to phase-run v0.18.8.
- **L10** (2026-10-21) Verification:
  - Independent verifier: S1–S6 pass with no blockers (probes: 3000-chunk jitter, 2–3 concurrent streams, close or disconnect while waiting, lock stress, real PTY `seq 20000`). It left 4 advisories.
  - Native review of the whole range: refused with `lens_context_budget_exceeded` (the 581 KB atlas bundle). With the user's choice, T1–T3 (77591f33..2aca1091) were reviewed as their own candidate in a temporary worktree (lenses resilience and reliability) and approved and acknowledged, lineage `review-8c9e2a347fd6c304`.
  - One batch fixed the advisories:
    - The iframe `onload` no longer throws `activeTab is not defined` on its initial `about:blank`.
    - The memo signature adds ctime, and a file whose mtime is less than 2 s old is never stored (same-tick rewrite).
    - `close()` notifies its streams.
    - A stream unwatches the `Session` it holds, even after the session was removed.
  - New tests pin: waiter cleanup, a prompt end on close, and a phase run started after an idle detach streaming again (R3-002/R4-001). That last one already passed, because `sendToCli` opens the console.
- **L11** (2026-10-21) Close:
  - Full suite at 6cfb1462: 6442 passed, 12 skipped. The 4 failures all also fail on main: `paper_preview` (environmental), release hygiene (needs a version bump), and the two `borrows_no_repository_s_vocabulary` subtests ('kaggle').
  - npm: 784/784 passed.
  - `/api/status` on QMLEEG under the same load: 23–25 ms with the change, 70–76 ms without.
  - Not merged or pushed; that is the user's decision.
- **L12** (2026-10-21) Second review:
  - At the user's request, the whole range was tried again and refused again (`lens_context_budget_exceeded`).
  - The range after the atlas commit (fc19c4b1..6cfb1462: T5, T6, advisory fixes) was reviewed with the resilience and reliability lenses, approved and acknowledged, lineage `review-66241b76a0fcb7a3`.
  - Two informational suggestions are left as follow-ups:
    - Reset `dock.dataset.shape` if anything else ever rewrites the dock.
    - The close-timing test's 0.5 s bound could flake on a loaded runner.
  - Only the atlas bundle commit (fc19c4b1) has no native review. It is covered by the verifier and the live check.

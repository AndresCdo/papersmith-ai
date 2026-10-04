# Feature: dashboard-interactive

Status: in progress. Branch: `feat/dashboard-interactive` (local only; push/PR not authorized).
Plan: v4, Judgment Day APPROVED 2026-10-04 (plan sha256 3d1c10a5..., cycles: v1 rejected, v2 rejected, v3 fixed to v4, scoped re-judgment clean on both judges).
TDD: strict (session config). Runners: Python `/home/carlos/Documents/projects/papersmith-ai/.micromamba/envs/papersmith/bin/pytest`; UI `cd ui && npx vitest run` (from T0a); script helpers `node --test "tests/**/*.mjs"`.
Delivery strategy: ask-on-risk; chain strategy asked when the user returns.

## Deviation from the plan (recorded)
- Branch base: the plan starts from origin/main after the harness-parity stack merge reports ALL DONE. To avoid hours of idle waiting, the branch was created from the local stack tip `feat/workspace-gitignore-skill-links` (164c41b), which contains all stack code. When the stack driver reports ALL DONE, run a local `git merge origin/main` on this branch (no remote write).

## Checklist (route per task: delegated writer unless noted)
- [x] S1 T0a UI test infrastructure
- [x] S2 T0b Visual checker + data-ready
- [x] S3 T1 Light theme, literal replacement, load fix
- [x] S4 T1-layout fixes from the checker
- [x] S5 T2a Routing and graph model
- [x] S6 T2b-1 SectionDetail extraction
- [x] S7 T2b-2 Selection and detail panel
- [x] S8 T3a History core
- [ ] S9 T3b History wiring and Host allow-list
- [ ] S10 T4 History UI
- [ ] S11 T5 Docs, CI and closure
- [ ] Judgment Day on the implementation: APPROVED

## Evidence
(appended per task: RED/GREEN commands and results, commit ids, screenshots)

### S1 T0a UI test infrastructure
- Route: delegated writer. Deps installed with `cd ui && npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @testing-library/dom` (@testing-library/dom is the peer of @testing-library/react 16).
- RED: `cd ui && npx vitest run` with src/App.test.tsx present and no vitest config -> 1 failed: `ReferenceError: document is not defined` at render().
- GREEN: after vite.config.ts `test` block, src/test/setup.ts and the `test` script: `npx vitest run` -> 1 file, 1 test passed.
- `npm run typecheck` passes with the test files present (tsconfig types unchanged, no jest-dom entry); `npm run build` passes and the bundle is byte-identical (index-CUXqyhFi.js / index-BtYy1DHB.css, no static diff).
- Commit: see git log (subject `test(ui): add the Vitest and Testing Library infrastructure`).

### S5 T2a Routing and graph model
- Route: delegated writer; one commit `feat(ui): add hash routing with an element id and a testable graph model`.
- RED: `cd ui && npx vitest run src/lib src/components/dag/graph.test.ts` -> hash.test.ts failed to load (`./hash` missing) and graph.test.ts `TypeError: buildGraph is not a function`; `npx vitest run src/App.test.tsx` with the routing tests -> 1 failed (`expected '#pipeline' to be '#pipeline?el=stage%3Adrafting'`, mount normalisation dropped the element).
- GREEN: `src/lib/hash.ts` (TABS, parseHash, formatHash with encodeURIComponent, malformed or empty `el` -> null), exported `buildGraph` and `relationKind` (edge `data.relation`), App owns `route {tab, el}` with `navigate(tab, el)` (state set directly, hash via replaceState; a tab change pushes one history entry so Back still works between tabs), mount normalisation keeps `el`. `npx vitest run` -> 7 files, 47 tests pass; `npm run typecheck` and `npm run build` pass (bundle index-sSg9iHRq.js).
- Deviation: the plan says navigate uses replaceState; a change of tab uses pushState instead (element changes within a tab use replaceState) to keep the browser Back button across tabs.

### S6 T2b-1 SectionDetail extraction
- Route: delegated writer; one commit `refactor(ui): extract SectionDetail from the section matrix`.
- Characterization first: `SectionMatrix.test.tsx` (open from Detail, close by Escape and Close) passed before the refactor (2 tests). RED: `npx vitest run src/components/sections` -> `Failed to resolve import "./SectionDetail"`. GREEN after extracting `SectionDetail.tsx` (body only: detail grid, citations, blocks, fact contract; `extentLabel` exported; the drawer keeps its chrome and the Escape listener): `npx vitest run` -> 9 files, 52 tests pass; typecheck and build pass.

### S7 T2b-2 Selection and detail panel
- Route: delegated writer; commits `feat(ui): make the pipeline diagram selectable with a detail panel` (133ec15, ~926 added / 185 deleted incl. the buildGraph move to graph.ts and the rebuilt bundle, ~740 authored lines of which ~280 are tests; above the ~400 heuristic because tests, the panel and the graph move belong to one behavior; recorded, not shrunk) and `feat(scripts): add a real-browser click check to the visual checker`.
- RED: `cd ui && npx vitest run` with the new tests and no implementation -> 4 files failed to load (`selection`, `ElementDetailPanel`, `PipelineGraph` graph prop / `./graph` missing) and 4 App tests failed (no `element-detail-panel`). GREEN: 13 files, 85 tests pass; `npm run typecheck` and `npm run build` pass (bundle index-D8e4L5fo.js / index-qFCI2pGz.css).
- Design: `lib/selection.ts` `reduceSelection` (batched rule, pure, unit tested), `dag/graph.ts` (buildGraph moved out of PipelineGraph), PipelineGraph takes `graph`, `selectedId`, `onSelect` (selection mapped onto copies in a second memo; layout runs once per state in App), ElementDetailPanel is a non-modal drawer (no backdrop so the canvas stays clickable), focus in/restore, one Escape listener.
- jsdom limits: edges are not rendered, so edge and batching tests call the ReactFlow handler props through a mocked `ReactFlow` (`PipelineGraph.edges.test.tsx`, documented in the file); user-event `mousedown` has a null `view` that d3-zoom cannot take, so tests on React Flow elements use `fireEvent.click` (keyboard tests use userEvent, they work).
- Checker: helper tests first (RED `does not provide an export named 'clickShotName'`), then `--click-check`: clicks the centre of a stage, gate and section node and the midpoint of an edge path via CDP mouse events, asserts panel title and hash `el=`, Escape closes, then focuses a node and an edge wrapper and presses Enter. Finding fixed: after about eight page loads the checker's pages stalled (Chromium kept previous pages in the back/forward cache with their EventSource open, exhausting the per-host connections; reproduced with 16 plain loads); the checker now launches with `--disable-features=BackForwardCache` and a 16-load run passes.
- Real browser: `node scripts/command-center-visual-check.mjs --out <shots>/s7 --drag-check --click-check --full-page` -> exit 0; drag-check ok at both viewports; click-check ok at both viewports for click stage (Ingestion), gate (Writing Readiness Gate), section (materials-and-methods), edge (Connection), keyboard Enter on a stage and on an edge.
- Screenshots: /tmp/claude-1000/-home-carlos-Documents-projects-papersmith-ai/69ffaf9c-7548-46f0-b18b-99d4f953cd48/scratchpad/shots/s7/ (click-stage|gate|section|edge at 1280x800 and 1600x1000, plus the full-page tab shots).

### S8 T3a History core
- Route: delegated writer; one commit `feat(command-center): add the in-memory history core`.
- RED: `.micromamba/envs/papersmith/bin/pytest tests/test_command_center_history.py -q` -> collection error `ImportError: cannot import name 'history' from 'skills._core.command_center'`. GREEN after `history.py`: 22 passed, 8 subtests passed.
- Contract: kinds section_status, section_blocks, section_words, gate (state + reasons), stage (active + progress), health (overall `summary.state` and per-harness state), smoke; sections, gates or stages that appear or vanish are a change from or to None. `page()` on a reset (other boot_id) returns the first retained entries (cursor treated as 0) so the client can reload in one call; invalid element or kind raises `HistoryQueryError` (HTTP 422 in S9). Element ids match `ui/src/components/dag/graph.ts` (`stage:`, `gate:`, `section:` + raw id).

---

# Plan v4: interactive, light-themed Paper Command Center with session history (feature `dashboard-interactive`)

Supersedes v2 (sha256 7facd233...). The v2 ledger is resolved at the end.

Repo: /home/carlos/Documents/projects/papersmith-ai. Dashboard = `papersmith ui` (src/papersmith/core/ui.py) -> FastAPI app skills/_core/command_center/server.py serving the committed Vite/React bundle skills/_core/command_center/static/ built from ui/ (`cd ui && npm run build`; outDir ../skills/_core/command_center/static, emptyOutDir).

## User request (2026-10-04)
1. Make the dashboard look right using web-development best practice; rebuild the bundle as needed.
2. Use a LIGHT theme.
3. Every element of the diagrams clickable.
4. A history of things as they happen.
Process: plan -> Judgment Day until APPROVED -> build -> Judgment Day on the implementation until APPROVED. User is away. Authorized for this feature: a local branch and local work-unit commits. NOT authorized: push, PR, any remote write.

## Verified facts
- Environment: Node v26.8.1; /usr/bin/chromium; ui/node_modules and /home/carlos/Documents/projects/papersmith-ai/.micromamba/envs/papersmith/bin/pytest exist in the main checkout (editable install points at the main checkout); httpx is installed in that env but not declared in requirements.txt.
- Bundle not stale (scratch build reproduced index-CUXqyhFi.js / index-BtYy1DHB.css).
- Stage payload keys: id, title, active, progress, detail, workers (state_extractor.py:649-656). buildGraph is module-private and memoised on state (PipelineGraph.tsx:120, :214). Edge ids `${source}->${target}` (:173-176); edge families: stage->stage (STAGE_CHAIN), stage->gate (GATE_SOURCES), gate->stage (:196-197), stage->section and section->stage (drafting/auditing).
- React Flow 12 (ui/node_modules/@xyflow/react/dist/esm/index.mjs): the node wrapper div carries tabIndex, data-id and its own onKeyDown that turns Enter/Space/Escape into select/unselect through the store (:2299-2311, :2366); edges likewise (:3018-3025, :3043). With controlled `nodes`/`edges`, those keyboard selections arrive as `select` changes on onNodesChange/onEdgesChange.
- Hash routing: readHash compares the whole fragment to tab ids; mount normalisation and selectTab write the bare tab (App.tsx:24-27, 55-69).
- Probable "Loading" cause: useWorkspaceEvents applies state only after Promise.allSettled([state, health]) (useWorkspaceEvents.ts:103-118).
- Existing theme tokens in ui/src/styles.css:5-29 (--bg, --bg-elevated, --bg-panel, --bg-input, --border, --border-strong, --text, --text-muted, --text-dim, --accent, --ok, --warn, --bad, --sealed and *-soft rgba variants) plus about 37 hard-coded colour literals (hex, rgb, rgba) outside the `:root` block: the topbar gradient (#121a25, #0d141c at styles.css:69), white-alpha tints, graph shell and node gradients, edge stroke and label fill, drawer backdrop, dialog and terminal backgrounds, shadows and status borders. PipelineGraph renders only Background, Controls and Panel (no MiniMap).
- create_app(root, *, debounce_ms, health_ttl) (server.py:131-132); main() owns --host/--port (server.py:317-354). Vite dev proxy uses changeOrigin:false (vite.config.ts:19-24) and stays that way, so the backend sees Host localhost:5173 and a browser Origin of localhost:5173 in dev; the smoke POST's origin_is_same() compares Host with Origin and keeps working only while both are localhost:5173 (changeOrigin:true would break it by rewriting Host to the backend).
- CI runs `node --test "tests/**/*.mjs"` (package.json test script, .github/workflows/test.yml); server tests call route functions directly (tests/test_command_center_server.py:21-41).

## Where the work happens
- The stack merge driver works ONLY in the separate worktree /home/carlos/Documents/projects/papersmith-ai-worktrees/stack-merge (`git -C` on that path plus fetch); it never touches the main checkout's working tree or HEAD. Concurrent `git fetch` and branch creation on the shared repository are safe.
- Start condition: the driver log shows ALL DONE -> create local branch `feat/dashboard-interactive` from origin/main in the main checkout. If the driver logs STOP, branch from the local stack tip `feat/workspace-gitignore-skill-links` and record that the base must later get a local `git merge origin/main` (no remote write). The current branch feat/harness-parity is clean and left untouched.
- Before every fresh-workspace check (T1 onward), run `python scripts/build-kit.py` so the gitignored `_kit` that `papersmith init` copies matches the branch; `_kit` is never committed and no drift test is added.
- TDD: strict. Runners: Python = absolute pytest path above; UI = Vitest (T0a); script helpers = `node --test "tests/**/*.mjs"`.
- Commits: Conventional Commits, no AI attribution lines (user's global rule), tests and docs with the behavior; the rebuilt bundle is committed with the UI source that requires it and counted as generated.

## Delivery forecast (ODD; authored lines, excluding bundle and lockfile)
T0a 150, T0b 330, T1 380, T1-layout 100 (layout defects found by the checker, counted separately), T2a 250, T2b-1 150, T2b-2 320, T3a 260, T3b 330, T4 350, T5 150; total ~2,770. Strategy ask-on-risk. No PR is authorized now, so slices are recorded as commit groups in odd/tasks/dashboard-interactive.md: S1 T0a (~150), S2 T0b (~330), S3 T1 theme + load fix + literal replacement (~380; likely near the limit, so split at the commit boundary load-fix vs theme/literals or flag as a size:exception candidate), S4 T1-layout (~100), S5 T2a (~250), S6 T2b-1 SectionDetail extraction (~150), S7 T2b-2 selection + panel (~320), S8 T3a (~260), S9 T3b (~330), S10 T4 (~350), S11 T5 (~150). Each slice is at or under ~400; the chain strategy (stacked-to-main or feature-branch-chain) is asked when the user returns. The forecast is re-counted after each task; a slice that lands above ~450 is split at its commit boundary or flagged as a size:exception candidate in the feature document.

## Decisions (user away; reversible, recorded in the feature document)
- D1 Light theme only. Keep the existing token names in styles.css (no rename churn) and replace their values with a light palette; replace ALL hard-coded colour literals in styles.css outside `:root` (about 37: white-alpha tints, graph shell and node gradients, edge stroke and label fill, drawer backdrop, dialog and terminal backgrounds, shadows, status borders, the topbar gradient) with tokens, adding tokens such as --graph-bg, --node-bg, --edge, --edge-label-bg, --overlay, --shadow, --terminal-bg, --terminal-text and *-border status tokens; theme React Flow nodes, edges and controls (Background, Controls, Panel; there is no MiniMap) through the same tokens. A Vitest guard fails when styles.css outside the `:root` block contains a hex, rgb(), rgba(), hsl(), hsla() or named-colour literal (`transparent`, `currentColor` and `inherit` allowed). Contrast test (Vitest) reads the `:root` block of styles.css with fs, parses hex and rgba tokens, alpha-composites each *-soft token over --bg-panel, and asserts WCAG AA for this explicit pair list: --text on --bg / --bg-panel / --bg-elevated / --bg-input (4.5:1); --text-muted on --bg-panel (4.5:1); --text-dim on --bg-panel (3:1, large/secondary only); each status color --ok/--warn/--bad/--sealed/--accent as badge text on its composited *-soft fill (4.5:1); --border-strong against --bg-panel (3:1 UI boundary); node text on --node-bg (4.5:1); edge label text on --edge-label-bg (4.5:1); terminal text on --terminal-bg (4.5:1).
- D2 History is in-memory per server process (ring of 1,000 immutable entries). No file persistence (backlog item). The UI states "History since the dashboard started". No server-side coalescing: entries are never mutated; the History tab groups consecutive word-count entries of the same section for display only.
- D3 UI test stack: vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom (ui devDependencies).
- D4 Host allow-list: `create_app(..., allowed_hosts: frozenset[str] | None = None)`. main() gains a repeatable `--allowed-host HOST:PORT` option. When --host is loopback (127.0.0.1, localhost, ::1) main() passes the set {"127.0.0.1:<port>", "localhost:<port>", "[::1]:<port>"} plus every --allowed-host value, compared case-insensitively; a request with a missing Host or a Host outside the set gets 421 when the set is active, and the 421 body explains how to allow the host (`--allowed-host HOST:PORT`); None (non-loopback binds, direct create_app use in tests) disables the check. origin_is_same() stays unchanged. The Vite dev proxy keeps `changeOrigin: false`; for `npm run dev` the backend is run with `--allowed-host localhost:5173` (documented), so dev Host == Origin == localhost:5173 passes both the allow-list and the smoke origin check. The same option covers port-forwarding. Tests use a raw ASGI harness (call `await app(scope, receive, send)` with asyncio), so no new dependency.
- D5 CI: the existing Node job gains `npm ci --prefix ui` and `npm test --prefix ui` so Vitest runs in CI (local commit only; takes effect when the user later pushes). Script-helper tests live under tests/ so the existing `node --test "tests/**/*.mjs"` covers them.

## Tasks
### T0a UI test infrastructure (delegated writer; slice S1)
- Add D3 deps (lockfile in the same commit); ui/vite.config.ts imports defineConfig from `vitest/config` with `test: { environment: 'jsdom', setupFiles: ['src/test/setup.ts'], globals: false, include: ['src/**/*.test.{ts,tsx}'] }`; src/test/setup.ts imports `@testing-library/jest-dom/vitest`, registers `afterEach(cleanup)` explicitly (globals are off), and stubs ResizeObserver (its callback is invoked with non-zero sizes so React Flow computes handle bounds and renders edges in jsdom), DOMMatrixReadOnly, and element offsetWidth/offsetHeight/getBoundingClientRect as React Flow needs; tsconfig `types` is NOT changed (no @testing-library/jest-dom entry); the setup import provides the matchers; `"test": "vitest run"`.
- RED->GREEN proof: a render test of App with mocked fetch and a fake EventSource asserting the tab bar renders.
- T0a verifies that `npm run typecheck` and `npm run build` pass with the test files present.

### T0b Visual checker (delegated writer; slice S2; runs before T1)
- `scripts/lib/visual-check.mjs` pure helpers (arg parsing, readiness predicate, console-message allow-list for EventSource reconnect noise, time-to-first-data computation), tested first in `tests/command-center-visual-check.test.mjs` (runs in CI via the existing glob).
- `scripts/command-center-visual-check.mjs`: launches chromium with --remote-debugging-port and a temp profile, drives CDP over the global WebSocket, opens each tab, waits for `document.body.dataset.ready` in {"1","error"} and, on the pipeline tab, for a `.react-flow__node` or the empty-state element, then two animation frames; captures PNGs at 1280x800 and 1600x1000 into a caller-given dir outside the repo; reports time-to-first-data; exits non-zero on timeout (default 20 s) or disallowed console errors. Optional `--drag-check`: performs a CDP mouse drag across the canvas and asserts no detail panel opened (used after T2b). Dev tool, not run in CI (no chromium on runners).
- `data-ready` is set by App: "1" once state is applied, "error" if the state fetch fails. This App change has its own Vitest test (RED first) and its own bundle rebuild within S2.
- Keyboard selection of a focused edge is verified by this checker over CDP (focus an edge, press Enter, assert the panel opens), used after T2b.

### T1 Look right: light theme and load fix (delegated writer; slice S3)
- RED first (hook test with a delayed health fetch): state is applied as soon as /api/state resolves, independent of health; health applied when it resolves; the "Loading" banner clears when state arrives. Then change useWorkspaceEvents.
- D1 contrast test and the no-literal guard RED first, then the light palette, the replacement of all colour literals outside `:root` with tokens, and React Flow theming.
- Hook ordering: the hook ignores the initial /api/state response if a state_update was already applied; test added (RED first).
- Run the T0b checker (S2 has already landed) on this repo and on a fresh `papersmith init` workspace in the scratchpad (after build-kit); rebuild bundle. Layout defects the checker shows are fixed in a separate slice S4 (T1-layout, counted separately), each with a test where testable, else screenshot evidence in the feature document; rebuild bundle.

### T2a Routing and graph model (delegated writer; slice S5)
- RED first: pure `parseHash(hash) -> {tab, el|null}` and `formatHash(tab, el?)` using encodeURIComponent for ids containing `:` and `->`; round-trip, unknown tab, malformed `el` tests.
- App is the single owner of the selection: `selectedEl` state initialised from the hash, updated on hashchange; `navigate(tab, el?)` sets state directly and writes the hash with history.replaceState (so selecting the same element twice works without relying on hashchange); mount normalisation preserves `el`.
- Element ids: element_id = "<kind>:<raw id>" exactly as the diagram uses; the UI always encodeURIComponent()s the value in queries and shows an inline message on 422 (formatHash tests cover a section id with spaces and unicode).
- Export `buildGraph` (pure). Tests for node ids, edge ids and relation kinds derived from id prefixes: stage->stage "next stage", stage->gate "gate input", gate->stage "gate releases", stage->section "drafts", section->stage "audited by". Unknown prefixes map to "related".

### T2b-1 SectionDetail extraction (delegated writer; slice S6)
- Extract the shared `SectionDetail` component from SectionMatrix (SectionMatrix refactor with its own tests, behaviour unchanged). Rebuild bundle.

### T2b-2 Clickable diagram and detail panel (delegated writer; slice S7)
- PipelineGraph receives `selectedId` and `onSelect(id|null)` from App. Layout memo stays on `state` only; a second memo maps layout nodes/edges to copies with `selected` from `selectedId`, so live updates keep the highlight and clicks never re-run dagre.
- ReactFlow props: elementsSelectable, nodesFocusable, edgesFocusable true; nodesDraggable false; onNodeClick/onEdgeClick -> onSelect(id); onNodesChange/onEdgesChange handle only `select` changes (this is how React Flow's own Enter/Space/Escape keyboard handling on focused nodes and edges reaches us); non-select changes are ignored; multiSelectionKeyCode={null}, selectionKeyCode={null}, deleteKeyCode={null}; onPaneClick -> onSelect(null).
- Selection reduction rule: node and edge `select` changes of one interaction (both callbacks) are collected and resolved once (queueMicrotask or a ref flushed in an effect): if any change has selected:true, select the last such id; a selected:false clears only when its id equals the current selectedId and no selected:true arrived in the same batch.
- ElementDetailPanel (drawer; Escape and close button call onSelect(null); focus moves into it and returns to the previously focused element): stage -> title, active, progress, detail, workers, plus linked gates/sections derived from the graph's edges; gate -> state, reasons, source stages; section -> the shared `SectionDetail` component (extracted in T2b-1; the drawer owns the single Escape listener); edge -> source, target, relation kind; a "Connections" list of buttons selects neighbouring edges/nodes. A selected id missing from the latest graph shows "No longer present".
- Tests (edges: if edges still do not render in jsdom, edge tests call the ReactFlow handler props directly): click selects; keyboard select while another element is selected; edge->node switches; a `select` change from onNodesChange/onEdgesChange selects/unselects (keyboard path); focus a rendered `.react-flow__node` wrapper and press Enter/Escape (exercising React Flow's own handler in jsdom); deep link opens the panel; pane click and close clear the selection and the hash; vanished element. After the slice, run the T0b checker with --drag-check plus the focus-an-edge, press Enter, assert-panel check, and record evidence. Rebuild bundle.

### T3a History core (delegated writer; slice S8)
- skills/_core/command_center/history.py, pytest first:
  - `diff_states(prev, curr) -> list[Change]` over section status, blocks written, word count, gate state (+reasons), stage active/progress; ignores generated_at and other volatile fields.
  - `diff_health(prev, curr)` over overall and per-harness status only.
  - `HistoryStore`: thread-safe ring (1,000), immutable entries {id: "<boot_id>-<seq>", boot_id, seq, ts, kind, element_id (diagram id or null for health/smoke), summary, before, after}; boot_id = uuid4 hex per process; seq monotonic from 1.
  - `page(boot_id=None, after_seq=0, element=None, kind=None, limit=200)`: oldest-first entries with seq > after_seq, limit clamped 1..500; response {boot_id, entries, has_more, reset, gap}: reset=true when the given boot_id differs from the current one (client must discard and reload from after_seq=0); gap=true when after_seq is older than the oldest retained seq (entries were evicted); has_more=true when more entries remain after this page. element validated as kind prefix in {stage,gate,section} plus a remainder of 1..200 characters without control characters (no restrictive charset; test a section id with spaces and unicode), kind against the known set; invalid values -> 422.

### T3b History wiring and Host allow-list (delegated writer; slice S9)
- server.py: `create_app(..., history_store=None, allowed_hosts=None)`; baseline state read at create_app start inside try/except: on failure the baseline is None and the first successful state becomes the baseline without entries (test: a raising extractor does not break create_app). A threading.Lock wraps measure_health's cache read/refresh; health diffs are recorded inside measure_health whenever the measured value changes (both the TTL-refresh endpoint path and the forced on_flush path), so no observed change is missed. In on_flush, history runs AFTER the state_update publish, inside its own try/except that logs and continues; wiring-smoke start/done recorded with exit code. `GET /api/history` maps to `page`; SSE event `history_append` carries each new entry.
- D4 middleware, repeatable `--allowed-host HOST:PORT` option and main() wiring; vite.config.ts keeps changeOrigin:false. Tests via the raw ASGI harness: allowed host passes, wrong host 421, missing host 421, case-insensitive match, set None passes everything; dev combination (Host and Origin localhost:5173 with --allowed-host) passes both the allow-list and the smoke origin check; the 421 response body explains how to allow the host.

### T4 History UI (delegated writer; slice S10)
- Vitest first. History tab: oldest-first storage, newest-first display; on first load and on every EventSource `open` (reconnects included) the client pages `/api/history?boot_id=<b>&after_seq=<last>` until has_more is false; reset -> discard and reload; gap -> show "Some earlier entries were dropped". Live `history_append` entries are appended when seq = last+1, otherwise trigger the same paging catch-up. Dedup by id. Filters by kind and element; consecutive word-count entries of one section are grouped for display. Entries with element_id call navigate('pipeline', element_id); null element_id rows are not links; missing elements reuse "No longer present". ElementDetailPanel gains a History section filtered by element_id. Rebuild bundle.

### T5 Docs, CI and closure (inline or delegated; slice S11)
- D5 CI step: setup-node cache-dependency-path includes both package-lock.json and ui/package-lock.json; the new tests/command-center-visual-check.test.mjs must not depend on DELIBERATION_DOMAIN_PROFILE; scripts/lib/ is new. Docs for `papersmith ui` (light theme, clickable diagram, in-memory history, Host allow-list with `--allowed-host localhost:5173` for `npm run dev` and port-forwarding, visual checker); CHANGELOG; odd/tasks/dashboard-interactive.md evidence.
- Checks: pytest tests/test_command_center_*.py, then the full pytest suite once; `npm test` at the root; `cd ui && npm run typecheck && npm test && npm run build` then `git status --porcelain skills/_core/command_center/static` empty; scripts/command-center-smoke.sh; build-kit then the T0b checker (with --drag-check) on this repo and on a fresh workspace, screenshots inspected for light theme and populated tabs including History.

## Verification loop
Per task: RED observed, GREEN, focused tests, checker where the UI changed, work-unit commit, feature document and Engram mirror updated. After T5: Judgment Day on the implementation (diff from the branch point); fix confirmed severe findings; scoped re-judgment; if exhausted, a fresh cycle on the revised implementation; repeat until APPROVED. Push/PR remain the user's decision.

## Out of scope / backlog
History persistence across restarts; extractor read-only contract changes; browser tests in CI; dark theme toggle; remote writes.

## Acceptance
- Light theme with the D1 contrast test and the no-colour-literal guard green; screenshots at both viewports show populated Pipeline, Health, Sections, Artifacts and History tabs with no disallowed console errors; time-to-first-data recorded.
- Every node and edge is clickable and keyboard-selectable (React Flow's Enter/Space on the focused wrapper); deep links round-trip; selection survives live updates; drag does not select.
- History records the listed kinds live, entries are immutable with unique ids, paging handles reset, gap and has_more, the client catches up on reconnect, history never breaks state_update, nothing is written to disk.
- Host allow-list active on loopback binds; the dev proxy (changeOrigin:false) works when the backend runs with `--allowed-host localhost:5173`, including the smoke POST; bundle equals a fresh build; all named checks pass, including Vitest in the Node CI job definition.

## Ledger resolution (v2 fresh cycle)
- Coalescing vs dedup (both, severe): entries immutable; display-only grouping (D2, T4).
- Cursor semantics (both): page() with boot_id, after_seq, has_more, reset, gap (T3a, T4).
- Host allow-list wiring and dev proxy (both): allowed_hosts parameter, main() wiring, changeOrigin:true (superseded in v4: changeOrigin stays false, see L1), raw ASGI tests (D4, T3b).
- Node helper tests outside CI and Vitest not in CI (both): tests/ location, D5 CI step.
- Slices over 400 (both): T0, T2, T3 split; S1-S8 forecast.
- gate->stage relation (both): "gate releases".
- Main checkout vs driver (both): driver confined to its worktree; start condition and fallback stated.
- Contrast pairs and alpha (both): D1 pair list and compositing; keep token names; topbar gradient.
- Keyboard activation (B): React Flow wrapper handles Enter/Space as select changes; controlled via onNodesChange/onEdgesChange; jsdom test on the wrapper.
- RTL cleanup (B): explicit afterEach(cleanup).
- Stale `_kit` for fresh-workspace checks (A): build-kit before every fresh-workspace check.
- Selection ownership, pane click and close clearing the hash (both): App owns selectedEl; navigate() with replaceState.

## Ledger resolution (v3 fresh cycle)
- L1 Dev proxy and Origin (severe): changeOrigin stays false; repeatable --allowed-host HOST:PORT; origin_is_same() unchanged; dev combination and 421-body tests; verified fact, D4 and acceptance corrected.
- L2 Colours (severe): false fact corrected; D1 replaces all ~37 literals with tokens, Vitest no-literal guard, extended contrast pairs, MiniMap mention removed, T1 forecast raised to ~380.
- L3 Selection reduction: batched resolution rule, multiSelectionKeyCode/selectionKeyCode/deleteKeyCode null, non-select changes ignored, keyboard and edge->node tests (T2b-2).
- L4 Element ids: "<kind>:<raw id>", kind prefix plus 1..200 chars without control characters, encodeURIComponent and inline 422 message, spaces/unicode test (T2a, T3a).
- L5 Ordering and slices: T0b before T1 with its own data-ready test and rebuild; slices S1-S11 re-forecast (S3 flagged as split/size:exception candidate).
- L6 Health: threading.Lock, diffs recorded inside measure_health on every measured change, create_app baseline in try/except with None baseline, raising-extractor test (T3b).
- L7 Initial fetch vs SSE ordering: hook ignores the initial /api/state if a state_update was applied; test (T1).
- L8 ResizeObserver stub invokes its callback with non-zero sizes; fallback of calling ReactFlow handler props directly; edge keyboard selection verified by the T0b checker over CDP (T0a, T2b-2, T0b).
- L9 jest-dom not added to tsconfig types; T0a verifies typecheck and build with test files present.
- L10 CI cache-dependency-path covers both lockfiles; visual-check test independent of DELIBERATION_DOMAIN_PROFILE; scripts/lib/ is new (T5).

### S2 T0b Visual checker + data-ready
- Route: delegated writer.
- RED 1: `cd ui && npx vitest run` with the two new App tests (`marks the body ready once the state is applied`, `marks the body as errored when the state fetch fails`) -> 2 failed (`expected undefined to be '1'`, `expected undefined to be 'error'`). GREEN after App sets `document.body.dataset.ready` ("1" once state is applied, "error" when no state and the load failed): 3 passed.
- RED 2: `node --test tests/command-center-visual-check.test.mjs` -> `ERR_MODULE_NOT_FOUND` for scripts/lib/visual-check.mjs. GREEN after the helpers: 8 tests pass (plain `node --test`, no DELIBERATION_DOMAIN_PROFILE).
- Live run (server already on 8099, same checkout, serves the rebuilt bundle index-oanq_LUB.js): `node scripts/command-center-visual-check.mjs --out <scratchpad>/shots/s2 --drag-check` -> exit 0, `OK 8 screenshot(s), no disallowed console errors`; time-to-first-data 139-289 ms (pipeline 275/289 ms, other tabs ~140-150 ms); drag-check ok at both viewports (the detail panel selector `[data-testid="element-detail-panel"]` does not exist yet, so the check is vacuous until S7). Negative run against a closed port: exit 1 with a timeout failure.
- Finding fixed in this slice: the first live run failed on `GET /favicon.ico` 404 (a real console error); `ui/index.html` now declares `<link rel="icon" href="data:," />` instead of widening the console allow-list.
- Screenshots: /tmp/claude-1000/-home-carlos-Documents-projects-papersmith-ai/69ffaf9c-7548-46f0-b18b-99d4f953cd48/scratchpad/shots/s2/ (pipeline|health|sections|artifacts at 1280x800 and 1600x1000).
- Bundle rebuilt: index-CUXqyhFi.js -> index-oanq_LUB.js (CSS unchanged).

### S3 T1 Light theme, literal replacement, load fix
- Route: delegated writer; two commits: `fix(ui): load the dashboard state and health independently` (4a1798a) and `feat(ui): switch the dashboard to a light theme` (aaec2ac).
- Load fix RED: `cd ui && npx vitest run src/hooks` -> 4 failed (state waited for health: `result.current.state` null while health pending; initial stale state overwrote the live state_update: `expected { marker: 'stale-initial' } to deeply equal { marker: 'live' }`). GREEN after independent fetches plus a `liveStateRef` guard: 7 tests pass overall.
- Theme RED: `npx vitest run src/styles.test.ts` (no-literal guard + D1 contrast pairs, alpha-composited, helpers in src/test/color.ts) -> 6 failed: guard found 37 colour literals outside `:root`, the extra tokens were missing, `--border-strong` vs panel 1.64:1. GREEN after the light palette, 13 new tokens (--graph-bg, --node-bg, --edge, --edge-label-bg, --overlay, --shadow, --shadow-drawer, --terminal-bg, --terminal-text, --tint, --track and *-border status tokens), all literals replaced, React Flow themed through its `--xy-*` variables on `.graph-shell`: `npx vitest run` -> 3 files, 24 tests pass; `npm run typecheck` and `npm run build` pass.
- Test file reads styles.css with node:fs (`/// <reference types="node" />` local to the test; tsconfig types unchanged).
- Visual: server restarted from this branch on port 8099 (the old PID 715753 was killed; it served stale backend code). `node scripts/command-center-visual-check.mjs --out <scratchpad>/shots/s3 --drag-check` -> exit 0, 8 screenshots, no disallowed console errors. Health tab on this branch lists `.agents/` IN_SYNC; the earlier ".antigravity absent" came from the stale server process, not a health_inspector bug.
- Screenshots: /tmp/claude-1000/-home-carlos-Documents-projects-papersmith-ai/69ffaf9c-7548-46f0-b18b-99d4f953cd48/scratchpad/shots/s3/
- Not run: the fresh `papersmith init` workspace check (deferred to T5 closure).

### S4 T1-layout fixes from the checker
- Route: delegated writer; commits `feat(scripts): add a full-page option to the visual checker` and `fix(ui): wrap the pipeline graph into rows and space the health facts`.
- Checker: `--full-page` (RED: `node --test tests/command-center-visual-check.test.mjs` -> `unknown option --full-page`; GREEN 8 pass) so tall tabs are captured whole.
- Defect 1 (Pipeline DAG shrinks to ~0.3 zoom): RED `npx vitest run src/components` -> layout.test.ts `Failed to resolve import "./layout"`. GREEN with src/components/dag/layout.ts: dagre still ranks and orders, any rank wider than MAX_PER_ROW=4 wraps into evenly sized centred rows, every row centres on one axis; tests cover wrapping, width bound, no overlaps and in-bounds, chain order, empty graph. The shell takes the graph's own aspect ratio (width 100%, maxWidth = graph width) so fitView fills the width at zoom <= 1 and the page scrolls; scroll-wheel zoom is off so the page scrolls over the canvas (Controls and drag-pan still work, every node stays reachable); node typography +1.5px; gate node height 184 after a clipped "no blocking reason" line was seen.
- Defect 2 (Health "skills wired11/11"): RED HarnessStatus.test.tsx -> `Unable to find an element with the text: skills wired` (labels and values shared one span). GREEN: `.readiness__row` with `.readiness__label` and `.readiness__value`, space-between with a divider; the HEALTHY badge no longer stretches the full width.
- Final: `cd ui && npx vitest run` -> 32 tests pass; `npm run typecheck`, `npm run build` pass; checker `--drag-check --full-page` exit 0, no disallowed console errors.
- Remaining (cosmetic): edges between ranks pass behind the nodes of intermediate rows; gates and sections share rows; the graph is about 2,700 px tall at 1600 wide (page scroll).
- Screenshots: /tmp/claude-1000/-home-carlos-Documents-projects-papersmith-ai/69ffaf9c-7548-46f0-b18b-99d4f953cd48/scratchpad/shots/s4/ (full-page pipeline|health|sections|artifacts at 1280x800 and 1600x1000).

# Feature: the dashboard's flows follow the architecture diagram

## Objective

The Paper Command Center draws a "pipeline" whose six stages (`ingestion`,
`deliberation`, `experiments`, `drafting`, `auditing`, `publishing`) exist only
inside the extractor. The architecture diagram in `docs/diagrams/` — generated
by Archify from `.archify/architecture-papersmith-pi-20261004-173559/build.mjs` —
draws the same project as **twelve numbered tramos** plus a transversal audit
lane, and nothing keeps the two in agreement.

Two flows, both derived from the diagram:

1. **General flow**: the twelve tramos, in the diagram's order, with the
   diagram's main chain as the edges.
2. **Writing flow**: one node per paper section, in rendering order.

## What already exists (verified, not assumed)

- The dashboard is a Vite + React + React Flow SPA in `ui/`, built by
  `npm run build` into `skills/_core/command_center/static/` and **tracked** in
  git (three files: `index.html` and two hashed assets).
- `papersmith ui [<dir>]` exists (`src/papersmith/core/ui.py`) with `--host`,
  `--port`, `--no-browser`, `--export-static`, `--allowed-host`. The repo has no
  *root* script to build or serve the SPA; `cd ui && npm run build` is the only
  path, and `ui/node_modules` was not installed.
- Views are hash-routed from one literal list, `ui/src/lib/hash.ts:1-10`:
  `pipeline, health, sections, artifacts, history, preview, atlases, decisions`.
- `ui/src/components/dag/graph.ts` takes the NODES from the payload
  (`state.pipeline_stages`, `state.gates`, `state.sections`) and the EDGES from
  two frontend literals: `STAGE_CHAIN` (`graph.ts:12-19`) and `GATE_SOURCES`
  (`graph.ts:21-26`). That is the drift this feature removes.
- Payload shapes, `skills/_core/command_center/state_extractor.py`:
  stage `{id, title, active, progress, detail, workers}` and section
  `{id, file, section, position, mode, status, has_contract, extent, word_count,
  blocks, facts, citations, blocks_total, blocks_written}`. `ui/src/types.ts`
  mirrors both field for field.
- `SECTION_ORDER` (the ten canonical slots, rendering order) is
  `state_extractor.py:33-44`; `get_workspace_state` already emits an ordered
  `sections` list with a `position` per section.
- The diagram's artifacts, read from its own `build.mjs` lanes: `sota-pool/`
  (`atlas.json`, `atlas.html`, `candidates.json`), `guidance/`, `proposals/`
  (`research-concept-rNN.md`), `implementations/<repo>`,
  `experiments/experiments-<slug>-vNN.md` (experimental implementation),
  `.experimental-deliberation/{state,receipts}/` (experimental deliberation),
  `skills/kaggle-accounts/store/accounts.json` (credentials, written by
  `accounts_cli.py:74`), the skill-declared inbox (`kaggle-inbox/`, read through
  `INBOX_NAME`), `paper/Figures/*`, `sections/*.md`, `paper/main.tex`.

## Design decisions

1. **The diagram is the source of the flow's shape.** The twelve tramos, their
   order and the main chain are transcribed from it once, in the extractor. A
   stage that has no observable artifact reports `active: false` with a `detail`
   that says what is missing — never an invented progress.
2. **The chain is data, not a frontend literal.** It travels in the payload as
   `pipeline_chain: [{from, to, label}]`, so the drawing cannot disagree with the
   stage list it is drawn from. `graph.ts` stops carrying `STAGE_CHAIN`.
3. **The tramo ids keep the payload's shape.** Each stage still ships
   `{id, title, active, progress, detail, workers}`, so `StageNode`, the detail
   panel and the deep links keep working; only the catalogue changes.
4. **The writing flow is the paper's sections, in rendering order.** The sections
   are already derived, ordered and rich (`status`, `word_count`,
   `blocks_written/blocks_total`, citations): the writing flow chains them and
   reuses `SectionNode` unchanged. The lane's agent steps stay where the diagram
   puts them — in the `writing` tramo of the general flow and in each section's
   `status`.
5. **One graph builder, two flows.** `PipelineGraph` gains a `flow` prop and
   `buildGraph(state, flow)` returns the nodes and edges for either. The existing
   React Flow canvas, node types and detail panel are unchanged.

## Slices

- **S1** Repair the 0.9.0 regression first: `tests/test_command_center_cli.py:93`
  still stubs `_run_env_install` with one positional argument, and `initialize`
  now passes two. It is red on `main` since `v0.9.0`.
- **S2** Extractor: the twelve tramos, `pipeline_chain`, the remapped
  `AGENT_STAGES`, and the python tests. RED first against the current six.
- **S3** Frontend: `graph.ts` reads the chain from the payload and gains
  `buildWritingGraph`; `hash.ts` + `App.tsx` gain a `writing` tab; `PipelineGraph`
  takes a `flow` prop. Vitest updated and extended, then the bundle rebuilt.
- **S4** Docs (`README.md`, this record), `CHANGELOG.md`, version `0.10.0`.

## Checks

Runners: `.venv/bin/python -m pytest tests/test_command_center_state.py
tests/test_command_center_server.py tests/test_command_center_cli.py -q`,
`cd ui && npx vitest run`, `cd ui && npx tsc -p tsconfig.json`, the bundle
rebuild (`cd ui && npm run build`), the kit rebuild (`python3
scripts/build-kit.py`) because `skills/` changed, `python
scripts/sync-repo-harness.py --check`, and the fast tier with
`--since <previous-sha>` — the plain form selects nothing once the work is
committed.

Measured before this feature: `tests/test_command_center_*.py` = 3 failures
(one of them S1, mine; two environmental: a case-insensitive filesystem and a
`watchfiles` missing from the hand-made `.venv`, fixed by installing the
declared requirement), vitest 216 passed, and the bundle current.

## Evidence

- **S1**: `tests/test_command_center_cli.py` red since `v0.9.0` with
  `TypeError: <lambda>() takes 1 positional argument but 2 were given`; fixed,
  and the command center suite went from 296 to 297 passed.
- **S2 RED**: 15 failed, 2 passed -- and the two passes are honest ones: an empty
  workspace lights nothing under either catalogue, and the stage payload's shape
  did not change. **GREEN**: 23 passed, 12 of them the per-tramo artifact cases.
- **S3**: vitest 216 -> **223 passed**, `tsc -p tsconfig.json` clean, bundle
  rebuilt (`index-CmBmY-h3.js`, 440 kB) and tracked. The bundle no longer
  contains a single stage id -- `experimental-deliberation` appears 0 times in
  it -- which is the feature: the frontend stopped carrying the catalogue.
- **End to end, against a real workspace**: a fresh `papersmith init` plus this
  checkout's `.venv` running the backend. `/api/state` returned 13 stages in the
  diagram's order, 10 chain edges and 4 gate links, and the fresh workspace
  carried the new bundle.
- **The end-to-end check paid for itself**: the first run lit `remote` on a
  workspace that had never run anything, because `_inbox` counted the scaffold's
  `.gitkeep` as an entry. The counters ignore placeholders now, with a test, and
  the second run lit exactly `harness`, `plausibility` and `audit`.
- **Baseline, measured before the change**: `tests/test_command_center_*.py` had
  3 failures, one of them S1 and mine. The other two were environmental and are
  gone or explained -- installing the `watchfiles` that `requirements.txt`
  declares (missing from this checkout's hand-made `.venv`) fixed the wiring
  health test and the SSE smoke test, and the last failure asserts a
  case-sensitive filesystem, which macOS is not.
- Guards: README vocabulary floor, derived-count sweep, capability table and
  `test_mcp_docs.py` -- 18 passed. `sync-repo-harness.py --check` clean (92
  files). Kit rebuilt, 249 files.

## Next step

Merge, then release 0.10.0 following `docs/releasing.md` -- the procedure this
cycle wrote down.

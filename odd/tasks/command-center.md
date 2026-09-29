# Feature: Paper Command Center (`papersmith ui`)

Status: in progress
Branch: `feat/command-center`
Created: 2026-05-18

## Goal

Ship an interactive local web dashboard and health/wiring control plane for an
initialized PaperSmith workspace. It must run standalone inside the paper
folder, impose no Node/npm runtime dependency there, and be reachable through
`papersmith ui`.

## Decisions already made (with the operator)

1. **Backend location.** `skills/_core/command_center/` in this repository.
   `skills/` is already a `manifest.KIT_ENTRIES` member, so the whole backend
   ships into every initialized workspace at `init`/`upgrade` with no new kit
   entry. It is runnable standalone as
   `python -m skills._core.command_center.server` from the workspace root
   (PEP 420 namespace package).
2. **UI assets.** `ui/` stays dev-only source at the repository root. The Vite
   build emits into `skills/_core/command_center/static/`, so the built SPA
   travels with the backend into the workspace. The server mounts its own
   `static/` directory; `PAPERSMITH_UI_DIST` overrides it.
3. **Dependencies.** FastAPI/Starlette, Uvicorn, watchfiles and pydantic are
   authorized. They go into the forge `requirements.txt` and the kit's
   `requirements.txt` (Python 3.11+; verified resolvable on 3.14).

## Task list

- [ ] T1 — Backend foundation: state extractor, health inspector, dependencies.
  - Write unit tests first (strict TDD where it is available for pure parsing).
  - Deliver `skills/_core/command_center/{__init__,state_extractor,health_inspector}.py`.
  - Declare deps in `requirements.txt` and `src/papersmith/_kit/requirements.txt`.
- [ ] T2 — Server + watcher + SSE.
  - Deliver `server.py` (FastAPI app, `/api/state`, `/api/health/wiring`,
    `/api/health/run-wiring-smoke`, `/api/events` SSE, static mount) and
    `watcher.py` (watchfiles, 300 ms debounce, ignore set).
  - Integration test exercises endpoints on an ephemeral port.
- [ ] T3 — CLI `papersmith ui [--port] [--host] [--no-browser] [--export-static <dir>]`.
  - Register in `src/papersmith/cli.py`; port fallback; browser open;
    SIGINT/SIGTERM teardown; spawn the workspace-local backend.
  - Tests for argument parsing and port selection.
- [ ] T4 — Frontend source + committed build.
  - `ui/` Vite + React + TS: React Flow DAG with dagre layout, health/wiring
    matrix, section matrix, artifacts, SSE hook.
  - `npm run build` emits `skills/_core/command_center/static/`; commit output.
- [ ] T5 — Smoke test + CI wrapper + docs.
  - `scripts/command-center-smoke.sh` (startup, liveness, payload contract,
    SSE reactivity, wiring smoke runner, graceful teardown).
  - pytest test that subprocess-runs it to a zero exit.
  - README section for `papersmith ui`.

## Non-goals

- No mutation of the user's paper directory: the extractor is read-only.
- No Node/npm requirement at runtime in the paper folder.
- No SDD/OpenSpec change: this is ODD, not SDD.

## Evidence

Each task records its work-unit commit below as it closes.

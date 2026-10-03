# SDD Project Context: papersmith-ai

## Session
- Init date: `2026-09-09`
- Artifact store: `openspec` (file-backed artifacts under `openspec/`)
- Strict TDD: `true` (marker in `openspec/config.yaml`; test runner present)
- Full test command: `npm run test:all` (`npm test` + `pytest`)

## Workspace
- Root: the checkout containing this file (no absolute path here: one recorded in this file told every clone it was somebody else's machine)
- Git root: recognized by `git rev-parse`
- Entrypoints: `CLAUDE.md`, `OPENCODE.md`, `PI.md`, `.agents/AGENTS.md` (all route to `openspec/project-context.md`, `guidance/paper-guide/`, `skills/*/SKILL.md`)
- No `AGENTS.md`, `GEMINI.md`, or `.cursorrules` present

## Stack signals
| Area | Signal |
| --- | --- |
| Runtime | Mixed Python (>=3.11) + Node.js (ESM, `type: module`) repository |
| Python | src-layout package `papersmith` (`src/papersmith/{core,bridges,mcp}`, `pipx install .`, entrypoint `papersmith.cli:main`) |
| Python deps | `requests`, `nbformat`, `nbclient`, `ipykernel`, `numpy`, `pytest`, `torch`, `PyMuPDF`, `PyYAML`, `jsonschema`, `kagglesdk==0.1.37`, `fastapi`, `uvicorn`, `watchfiles`, `pydantic` (the Paper Command Center server) (`requirements.txt`) |
| Node deps | `jiti`, `typebox`, `typescript`, `@types/node` (`package.json`, `tsconfig.json`); `npm run typecheck` (`tsc`); no eslint/prettier |
| Config | `pyproject.toml` (setuptools src-layout, pytest `testpaths`, ruff lint `E,F,W,I`), `papersmith.yaml` (ingestion engine/mode) |
| Measured runtime (2026-09-09, on the machine that initialized this file — a measurement, never a requirement) | `node v26.8.1`, `.venv` Python `3.14.7`, `pytest 9.1.0` |
| Repo markers | `requirements.txt`, `tests/`, `skills/`, `src/`, `docs/`, `guidance/`, `scripts/`, `openspec/`, `papersmith.yaml`, `tsconfig.json` |

## Architecture
- `src/papersmith/core/` — init, status, ingest, upgrade, executor, ledger
- `src/papersmith/bridges/` — Node, Python, deliberation, remote-execution bridges
- `src/papersmith/mcp/` — stdio Model Context Protocol server exposing workspace and paper-writing verbs
- `skills/` — canonical skill tree (`experimental-deliberation`, `experimental-implementation`, `figure-review`, `kaggle-accounts`, `paper-ingestion`, `paper-writing`, `plausibility`, `proposal-deliberation`, `proposal-implementation`, `remote-execution`, `skill-audit`), projected into `.claude/skills`, `.opencode/skills`, `.pi/skills`, `.antigravity/skills`, `.agents/skills` by `npm run setup:harnesses`
- `guidance/paper-guide/` — domain guidelines; `scripts/setup_env.py` — isolated runtime provisioning
- CI (`.github/workflows/test.yml`): Node suite (`npm ci` + `npm test`) and Python suite provisioned by `python3 scripts/setup_env.py install --no-ingestion`, run by `python3 scripts/clean_context_gate.py`: it runs the declared gate (`npm run test:all`, whose `test:py` names `.micromamba/envs/papersmith/bin/pytest`) twice, under an empty HOME and under a synthetic developer HOME, and fails if the two runs differ or if the empty-HOME run fails

## SDD config summary
- `openspec/config.yaml` exists with `strict_tdd: true`
- `apply.test_command` and `verify.test_command` both point to `npm run test:all`
- `openspec/changes/` holds active changes; `openspec/changes/archive/` holds completed changes
- `openspec/specs/` is the (currently empty) source-of-truth directory
- `.atl/skill-registry.md` indexes project/user skills (refreshed 2026-09-09)

## Persistence conventions
- `openspec/changes/<change>/` stores proposal, spec, design, tasks, and verify artifacts
- `openspec/changes/archive/YYYY-MM-DD-<change>/` stores completed changes (audit trail, never modified)
- `openspec/specs/<domain>/spec.md` is the merged source of truth (populated by sdd-archive)

## Notes
- The artifact store is file-backed only (`openspec`), and `openspec/config.yaml`'s
  `store:` key is where that is declared. Changed 2026-05-18: this file named a
  memory provider as half the store, which made its own instructions
  unexecutable on a machine that has none, and `papersmith init` ships no
  `openspec/` at all, so that half reached nobody. `tests/test_no_personal_context_dependency.py`
  derives its expectation from the configuration key and refuses a
  provider-shaped store, a provider mirror declaration, or a provider call in
  tracked code.
- This refresh supersedes the stale 2026-07-16 record (pointed at a `/Users/diego/...` root, `node v26.4.0`/`python3 3.9.6`, and a `.venv/.../unittest` command that no longer matches `package.json` or CI; the Python suite runs under `pytest`).
- `ruff` is configured in `pyproject.toml` but its binary is not installed in `.venv` or on PATH; no type checker, formatter, or coverage tool is configured.
- No application code was modified during init.

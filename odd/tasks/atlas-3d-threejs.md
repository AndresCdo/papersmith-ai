# Feature: 3D SOTA atlas with embedded three.js

## Context
The user wants `sota-pool/atlas.html` to look like the codebase-memory-mcp 3D
graph viewer (dark WebGL scene, glowing nodes, orbit controls). That viewer is a
compiled React + three.js app bundled inside its binary and reads only its own
code-graph API, so it cannot load `atlas.json`. Decision (user): re-render the
atlas in 3D with **three.js embedded** in the single HTML file.

Constraints kept from the current contract (`skills/plausibility/SKILL.md:85-104`,
`.pi/agents/sota-grapher.md:47-53`, `tests/test_sota_atlas.py`):
- one self-contained `atlas.html`, no CDN, no network at view time, no `<script src`;
- deterministic output: same atlas, same sky, byte-identical runs;
- renderer stays Python stdlib-only (the JS bundle is a versioned asset);
- details panel with abstract quote, family filter, cross-system link highlight.

Contract change: the inline `<svg>` plane becomes a WebGL scene; the test that
counts one `<svg>` and the docs that say "inline SVG" change accordingly.

## Tasks
1. [done] Vendored viewer bundle: three.js + OrbitControls + viewer source, reproducible esbuild script, minified IIFE asset, third-party notice — `ab18bc4`, forge-vocabulary admission `ec1b5eb`
2. [done] Test-first 3D contract in `tests/test_sota_atlas.py` (RED), then `render_atlas.py` emits deterministic 3D positions + data island + inline bundle (GREEN) — `0cf99e4`
3. [done] Docs: `SKILL.md`, CHANGELOG (the `sota-grapher` agent names no SVG/plane, so no agent or projection change) — `485ecd2`
4. [done] Verification: full suites, sample render, real-browser check

## Evidence
- Delegation fallback: writer/verifier subagents refused to start (session root
  `papers_smith/` is not a Git clone), so implementation and checks ran inline.
- RED: 4 new renderer tests failed for the missing data island/bundle; GREEN:
  `tests/test_sota_atlas.py` 20 passed.
- Bundle: 577 KB, `</script` absent, two builds same sha256.
- Forge floor: the bundle carries the three.js object key `transfer`; admitted
  per file in `FORGE_FLOOR_SURFACE_ADMISSIONS` (both admission tests pass).
- `sync-repo-harness.py --check`: clean (92 files). `npm run test:node`: 663 pass, 0 fail.
- Real browser (Chrome headless, SwiftShader WebGL, CDP): 25-system synthetic
  atlas renders with no console errors; family filter dims; modal escapes
  markup; fly-to close-up shows tilted orbits, arcs and dashed family ties.
- Full Python suite (`.venv`, `--ignore=tests/test_command_center_server.py`
  because it cannot be collected without `fastapi`): 5513 passed, 9 skipped,
  12 failed. None is caused by this branch:
  - 11 fail identically on a clean `main` worktree: 3 command-center tests
    (no `fastapi`), 5 `test_forge_gate::GateInterpreterTests` (the
    `.micromamba/envs/papersmith` interpreter does not exist),
    `test_suite_collects::test_every_test_module_loads`, and two
    `test_papersmith_init` workspace tests.
  - `test_command_center_smoke::test_smoke_script_passes_end_to_end` fails here
    on `ModuleNotFoundError: fastapi` at
    `skills/_core/command_center/server.py:28`, a module this branch does not
    touch (on the `main` worktree it did not reach that point).

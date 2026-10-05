# Feature: the Pi entrypoint Pi actually reads, plus the skill-description budget

## Objective
Make the `pi` harness's project prompt a file Pi actually loads, and bring every
skill description under Pi's 1024-unit limit so no harness has to warn.

## Problem (re-verified 2026-10-05 against Pi 1.0.2, not inherited from prose)

- `PI.md` is generated as the `pi` tool's static entrypoint
  (`generators.TOOL_OUTPUTS["pi"]`, `render_files` `TEMPLATES["pi"] -> pi.md.tpl`)
  and is documented as Pi's entrypoint in `.pi/README.md:20`, `README.md:326,410,543`,
  `openspec/project-context.md:12`, `docs/harness-support-matrix.md:135-136`,
  `scripts/cli-paper-wiring-smoke.sh:12,69`, six spots in
  `skills/paper-writing/SKILL.md` and one in `skills/proposal-implementation/SKILL.md`.
  **Pi never reads it.**
- Evidence: `dist/core/resource-loader.js:116` — project context candidates are
  exactly `AGENTS.override.md, AGENTS.md, AGENTS.MD, CLAUDE.md, CLAUDE.MD`;
  `grep -c 'PI\.md' resource-loader.js` returns 0.
  `discoverAppendSystemPromptFile()` (same file, ~949) returns
  `<cwd>/.pi/APPEND_SYSTEM.md` when the project is trusted, else the global one,
  and never combines them. In this repository Pi therefore loads `CLAUDE.md`
  as its project context and has no append file at all.
- `skills/paper-writing/SKILL.md` (1680 UTF-16 units) and
  `skills/remote-execution/SKILL.md` (1814) exceed Pi's
  `MAX_DESCRIPTION_LENGTH = 1024` (`dist/core/skills.js:11`). Pi warns and loads
  anyway; the repo still ships a description that does not fit the runtime that
  reads it.

## Already closed, do not redo
- D3 (`.gitignore` and `src/papersmith/templates/gitignore.tpl` not ignoring the
  four skill links) is fixed upstream: the template now lists `.claude/skills`,
  `.opencode/skills`, `.pi/skills`, `.agents/skills`.
- The 2026-10 stash's `.pi/settings.json` skill-discovery approach is obsolete:
  upstream settled on the `.pi/skills` symlink plus generated `.pi/prompts/`.
  `stash@{0}` (base `a67d616`) holds intent for D1/D2 only; nothing from it
  applies as a patch to current `main`.

## Decisions
- **D1 shape**: rename the `pi` static output `PI.md` -> `.pi/APPEND_SYSTEM.md`,
  carrying the same routing content and the generated `## Agents` roster.
  Rejected: a root `AGENTS.md` (would silently change the context of every other
  harness that reads it), and keeping `PI.md` as a pointer (two files that say
  the same thing, which is the drift this repo already argues against).
- **Existing workspaces**: `upgrade` creates the new path and removes the stale
  `PI.md`; a leftover `PI.md` is reported as surplus so it does not linger
  unnoticed.
- **D2 wording**: reuse the text measured and independently verified on
  2026-09-28 (`paper-writing` 1015, `remote-execution` 923), and add
  `tests/test_skill_descriptions.py` — the budget guard measured in UTF-16
  units, because that is the unit JS `length` uses and therefore the unit that
  defines the ceiling. The provenance date `since 2025-07-11` must return to
  `remote-execution`'s body: it lived only in the description.
- **Release mechanics**: any change under `src/` since the last tag forces a
  version bump, a `## <version>` CHANGELOG section and a kit rebuild
  (`python3 scripts/build-kit.py`). Version is `0.7.1`, last tag `v0.7.0`.

## Mode
TDD strict where a runner exists; docs-only steps verified structurally.
Runners: focused `.venv/bin/python -m pytest <file>`, tier `python3 scripts/fast_tests.py`,
node `npm run test:node`, full `.venv/bin/python -m pytest` (CI gate), projections
`python scripts/sync-repo-harness.py --check`, browser check for the diagram.
Delivery: one branch, work-unit commits, Conventional messages, no AI attribution.
Push, PR and merge stay the user's decision.

## Tasks
1. [ ] `tests/test_skill_descriptions.py` (RED) then the two compressed
       descriptions plus the provenance date back in the body (GREEN)
2. [ ] Rename the `pi` static output and its template; update `TOOL_OUTPUTS`,
       the audit surplus table, the pinned expected-path sets and the kit
3. [ ] `upgrade`: create `.pi/APPEND_SYSTEM.md`, remove the stale `PI.md`
4. [ ] Tests: generators, init, upgrade, workspace agents e2e, workspace commands
       e2e, harness parity, executor pin, wiring smoke script
5. [ ] Docs: `README.md`, `README.es.md`, `.pi/README.md`,
       `openspec/project-context.md`, `docs/harness-support-matrix.md`, the seven
       skill prose references, `CHANGELOG.md`, version literals
6. [ ] Regenerate the Archify diagram (label + pin) and re-validate it
7. [ ] Verification: fast tier, node suite, full pytest, `sync-repo-harness.py
       --check`, kit rebuild, real-browser check

## Evidence
(pending)

## Next step
Confirm the D1 shape with the operator if it is not already implied by their
"apply the stash fix" answer, then start with task 1's RED guard.

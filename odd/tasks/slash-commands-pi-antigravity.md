# Feature: slash commands for Pi and Antigravity

## Objective
`papersmith init` / `upgrade` project slash commands for Pi and Antigravity, as they already do for Claude Code and OpenCode.

## Problem
`COMMAND_TOOLS = ("opencode", "claude")` (src/papersmith/generators.py:120). Antigravity and Pi get none; their docs say so. Antigravity's skills link is `.antigravity/skills`, which is not its documented path.

## Decisions (Judgment Day APPROVED, plan: scratchpad commands-plan.md)
- Pi: project prompt templates `.pi/prompts/<name>.md`, reuse `command.md.tpl` (`$ARGUMENTS` supported).
- Antigravity: skills at `.agents/skills` (invoked `/name`); KEEP `.antigravity/skills` and ADD `.agents/skills`. Workflows (`.agents/workflows`) are deprecated 2026-11-01, so not generated.
- `HARNESS_SKILL_LINKS` becomes explicit (tool, relpath) pairs (the tool name must not be derived from the path; manifest.py:203).
- Health check requires links/commands only for enabled tools; health_inspector stays stdlib-only (guarded import + fallback table).
- Unverified: `.agents/skills` in real Antigravity; Pi trust prompt for `.pi/prompts`. Confirm before release; if Antigravity is unconfirmed, ship Pi alone.

## Mode
TDD strict (source: user config), runner: `npm run test:fast` (focused: `.micromamba/envs/papersmith/bin/pytest <file>`), full: `npm run test:py`. Branch is stacked on chore/release-0.7.1 (PR #27, open, green). Forecast ~350-450 authored lines incl. tests/docs. Delivery: one PR, ask-on-risk.

## Tasks
- [x] T1 manifest: explicit (tool, relpath) pairs; antigravity gets both links; RED tests in tests/test_papersmith_init.py (route: delegated writer)
- [ ] T2 Pi commands: COMMAND_TOOLS + per-tool prefix map + DYNAMIC_PREFIXES; RED tests in generators/commands e2e/agents e2e
- [ ] T3 health_inspector (per-tool links + commands dir map, guarded manifest import), watcher; tests in test_command_center_health.py
- [ ] T4 scripts: cli-paper-wiring-smoke.sh, sync-repo-harness.py, setup-harnesses.sh, .gitignore
- [ ] T5 docs/templates/generated files/CHANGELOG (pi.md.tpl, antigravity-rules.md.tpl, opencode.md.tpl, PI.md, .antigravity/rules.md, .pi/README.md, README.md, README.es.md, openspec/config.yaml, openspec/project-context.md)
- [ ] T6 verify: test:fast, kit rebuild, scratch `papersmith init`, clean-context gate tests

## Progress / evidence
- T1 (route: delegated writer, strict TDD). RED: `pytest tests/test_papersmith_init.py -q` -> 2 failed (`test_initialize_wires_harness_skill_symlinks`, `test_link_harness_skills_antigravity_wires_both_documented_and_legacy_paths`: `['.antigravity/skills'] != ['.agents/skills', '.antigravity/skills']`). GREEN: same file -> 23 passed; `npm run test:fast` -> 182 passed. Only consumer of HARNESS_SKILL_LINKS is `link_harness_skills`; scripts/setup-harnesses.sh and tests' HARNESS_LINKS literal (script-driven) left for T4. Commit: 191c9fc

## Next step
T2.

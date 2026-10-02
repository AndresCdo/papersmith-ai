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
- [x] T2 Pi commands: COMMAND_TOOLS + per-tool prefix map + DYNAMIC_PREFIXES; RED tests in generators/commands e2e/agents e2e
- [x] T3 health_inspector (per-tool links + commands dir map, guarded manifest import), watcher; tests in test_command_center_health.py
- [x] T4 scripts: cli-paper-wiring-smoke.sh, sync-repo-harness.py, setup-harnesses.sh, .gitignore
- [ ] T5 docs/templates/generated files/CHANGELOG (pi.md.tpl, antigravity-rules.md.tpl, opencode.md.tpl, PI.md, .antigravity/rules.md, .pi/README.md, README.md, README.es.md, openspec/config.yaml, openspec/project-context.md)
- [ ] T6 verify: test:fast, kit rebuild, scratch `papersmith init`, clean-context gate tests

## Progress / evidence
- T1 (route: delegated writer, strict TDD). RED: `pytest tests/test_papersmith_init.py -q` -> 2 failed (`test_initialize_wires_harness_skill_symlinks`, `test_link_harness_skills_antigravity_wires_both_documented_and_legacy_paths`: `['.antigravity/skills'] != ['.agents/skills', '.antigravity/skills']`). GREEN: same file -> 23 passed; `npm run test:fast` -> 182 passed. Only consumer of HARNESS_SKILL_LINKS is `link_harness_skills`; scripts/setup-harnesses.sh and tests' HARNESS_LINKS literal (script-driven) left for T4. Commit: a909de0
- T2 (route: delegated writer, strict TDD). RED: generators/commands-e2e/agents-e2e files -> 5 failed (`test_generators_are_clean_after_init`, `test_command_derivation_is_scoped_to_the_command_tools`, `.pi/prompts` subtest of `test_init_projects_eleven_commands_per_command_harness`, `test_orphan_removal_is_baselined_dynamic_paths_only`, `test_an_already_deleted_orphan_clears_instead_of_stranding`). GREEN: same files -> 93 passed; `npm run test:fast` -> 243 passed. init.py topology needs no change (fs writes create parents; e2e creates `.pi/prompts`). tests/test_workspace_agents_e2e.py: PI.md "no generated slash commands" assertion dropped until T5 rewords the template (Antigravity keeps it). Commit: 5a21a73
- T3 (route: delegated writer, strict TDD). RED: `pytest tests/test_command_center_health.py -q` -> 3 failed, 11 passed (missing `.agents/skills` not reported; Pi expects `.pi/prompts`; unenabled tool still measured). GREEN: same file -> 14 passed; `npm run test:fast` -> 3094 passed, 3 skipped. health_inspector reads `HARNESS_SKILL_LINKS` via guarded import with a duplicated fallback table, enabled tools come from `.papersmith/config.json` `active_tools` (all tools when no config), commands dir is a per-harness map. watcher: added `.agents` to watch targets and health prefixes. Commit: 7869ef3 (message-identical content; hash recorded after amend)
- T4 (route: delegated writer, strict TDD). RED: `pytest tests/test_workspace_commands_e2e.py -k projection_script` -> 1 failed once the test deleted the init-made links and expected `.agents/skills` from the script alone. GREEN: same -> passed. Also: `.gitignore` ignores `.agents/skills`; `scripts/setup-harnesses.sh` links it; smoke link loop + `.pi/prompts` filename parity updated, `bash scripts/cli-paper-wiring-smoke.sh` -> `wiring smoke: ok`; `sync-repo-harness.py` covers `.pi/prompts` and pi (also passes `run_env=False` so it no longer provisions a micromamba env), regenerated 11 `.pi/prompts/*.md` plus pre-existing `plausibility.md` drift in `.claude/commands` and `.opencode/commands`; `--check` -> `clean (34 files)`. `tests/test_harness_parity.py` flagged `.agents/` as untracked-empty, so a hand-written `.agents/README.md` was added. `tests/test_no_personal_context_dependency.py` + commands e2e -> 82 passed (gate unaffected). `npm run test:fast` -> green after the parity fix (see commit).

## Next step
T5 (docs/templates/CHANGELOG), then T6.

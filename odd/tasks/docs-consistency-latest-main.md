# Documentation consistency and install-from-main

Objective: make the README and sibling docs agree with the code at 0.7.0, and make the install instructions always point at the latest `main`, never a tag.
Authorized scope: README.md, README.es.md, CLAUDE.md, OPENCODE.md, openspec/project-context.md, docs/mcp.md. No code changes.
Checks: `npm run test:fast` (docs guards), grep for stale counts/pins.
TDD: not applicable (documentation); runner for guards: `npm run test:fast`.
Route: inline, mechanical edits from a read-only audit (mapper delegated; evidence recorded below).

## Tasks
- [x] T1 Install: README step 1 installs from the default branch; remove the `@v0.2.0` pin and the paragraph that argues for pinning (A1-A3)
- [x] T2 README header: badge owner (Daprosero), Node badge >=21 per CI comment, command count (A4, B3, B9)
- [x] T3 Counts: README.es.md (12 CLI commands, 11 skills, 19 agents), README MCP catalogue 22 -> 38 tools (15 read-only, 23 mutating), nine -> eleven SKILL.md, CLAUDE.md/OPENCODE.md ten -> eleven skills (B1, B2, B5, B7)
- [x] T4 Tests and CI wording: drop stale 4172/647 counts, project-context CI description matches the gate (B4, B6)
- [x] T5 CLI flag tables: `init --no-env`, `upgrade --allow-downgrade`; first-ingestion note about `init` provisioning (A5, B8)
- [x] T6 Verify: guards pass, grep shows no stale pin/count; commit, PR

## Evidence
Truth derived from code: 11 skills/*/SKILL.md, 19 .claude/agents, 11 .claude/commands, 12 CLI subcommands, 38 MCP tools (registry TOOLS), version 0.7.0, `init --help`, `upgrade --help`.
Left alone on purpose: dated measurements ("Medido el 2026-09-13", 2026-10-01); "ocho comandos" refers to FORGE_DEFECT_OPEN, unrelated.

## Verification
`npm run test:fast`: 158 passed, 1 failed: `test_version_sources.py::...::test_shipped_changes_since_the_last_release_moved_the_version`. Not caused by this change: it fails on `main` too, because PR #25 changed `scripts/clean_context_gate.py` after the `v0.7.0` tag and the version is still 0.7.0. CI does not see it (checkout has no tags, the test skips). The next release needs a version bump.

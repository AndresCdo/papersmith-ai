# Feature: Antigravity uses only documented locations

## Objective
New workspaces wire Antigravity through documented locations only: skills at `.agents/skills`, the rules/routing entrypoint at `.agents/AGENTS.md` (fallback `.agents/rules/papersmith.md`), and no `.antigravity/*`.

## Problem
`.antigravity/rules.md` and `.antigravity/skills` have no source in Antigravity's docs (docs/harness-support-matrix.md). New workspaces still get both from `init`.

## Decisions (Judgment Day APPROVED: round 1 + scoped re-judgment; plan v3 = scratchpad ag_plan_v3_frozen.md)
- User scope decision (pre-1.0): only NEW workspaces matter; no legacy handling, no upgrade notice, no preservation guarantee, no audit informational finding.
- A0 gate decides the file from RAW docs text: (a) `.agents/AGENTS.md` if loaded/always-on and not mis-parsed by pi-subagents; (b) `.agents/rules/papersmith.md` only with a raw-text confirmed `trigger`; (c) otherwise STOP with no generator change and report.
- A1 is one atomic commit (generator path + TOOL_OUTPUTS, init topology, three rosters, inspector HARNESSES/_structural_drift, watcher, smoke script, every pinned test). Split only along a green boundary if > ~400 authored lines.
- Known behavior to document: a user-authored `.agents/AGENTS.md` in a new workspace without antigravity is reported as surplus by `audit --check-drift`.
- Out of scope (flagged): workspace `gitignore.tpl` lacks entries for generated skills links.

## Mode
TDD strict (source: user config + project), runner: focused `.micromamba/envs/papersmith/bin/pytest <file>`, tier `npm run test:fast`, full `npm run test:py` before the PR; rebuild the bundled kit (`python scripts/build-kit.py`) before init/upgrade proofs. Commits: Conventional, NO AI attribution. Branch feat/antigravity-documented-paths is stacked on feat/harness-parity (PRs #29-#34 still open). Push/PR/merge are the user's decision.

## Tasks
- [x] A0 gate: raw-text Antigravity rules docs + pi-subagents loader; choose outcome (a)/(b)/(c); record in the matrix doc (docs commit)
- [x] A1 atomic code+tests commit (only on outcome a or b) - commit 14711d1
- [ ] A2 (mostly done inside A1, forced by tests) repo checkout: `git mv .antigravity/rules.md`, drop `.gitignore` line, remove local symlink
- [ ] A3 docs: README row/prose, `.agents/README.md`, matrix doc, SKILL.md mentions, CHANGELOG, openspec mentions, `.pi/README.md`

## Progress / evidence
(branch created from feat/harness-parity tip add8402)
- A0 DONE (delegated direct, read-only research + docs commit). OUTCOME (a): generate `.agents/AGENTS.md`, plain Markdown, NO frontmatter.
  - R confirmed from raw `https://antigravity.google/docs/rules.md` (2026-10-03, curl, 200 text/markdown): `<dir>/.agents/AGENTS.md` is in the directory-scoped load list; "AGENTS.md and GEMINI.md do not use frontmatter ... keeps it continuously active (`always_on`) for its directory scope".
  - P: pi-subagents (commit ad56bf9) `src/agents/agents.ts:2156` `if (!frontmatter.name || !frontmatter.description) { continue; }` skips silently (no diagnostic); `frontmatter.ts:69` no throw without `---`; existing `.agents/README.md` already skipped, unaffected.
  - T confirmed (`trigger: always_on`), fallback only.
  - Limitations recorded in docs/harness-support-matrix.md: (3) rules are cumulative, "more specific directory rules take priority", no order between same-level AGENTS.md/GEMINI.md/.agents/AGENTS.md; per-surface lists omit `.agents/AGENTS.md` (only the directory-scoped section lists it).
  - No earlier matrix claim contradicted.

- A1 DONE (delegated direct writer, commit 14711d1, ~112 changed lines, one commit). RED: 14 failing tests across harness_parity/init/generators/agents_e2e/commands_e2e/command_center_health after pinning tests to `.agents/AGENTS.md`. GREEN: focused 190 passed; `npm run test:fast` 4417 passed, 5 skipped; `scripts/cli-paper-wiring-smoke.sh` ok; `sync-repo-harness.py --check` clean (92 files). Throwaway init: `.agents/AGENTS.md` + `.agents/skills` present, no `.antigravity`, wiring summary unchanged, `--tools claude` creates no `.agents`, upgrade idempotent, `audit --check-drift` clean.
  - Forced into A1 (test_every_tracked_dot_directory_citation_resolves_in_a_workspace needs a tracked, resolvable path): `git mv .antigravity/rules.md .agents/AGENTS.md` (one-line fix), local `.antigravity/skills` symlink removed, `.gitignore` line dropped, and the `.antigravity/rules.md` mentions in skills/paper-writing and skills/proposal-implementation SKILL.md now name `.agents/AGENTS.md`. Remaining A2: none beyond verification; A3 docs still pending.

## Next step
A3 docs (README row/prose, `.agents/README.md`, matrix doc, CHANGELOG, openspec, `.pi/README.md`).

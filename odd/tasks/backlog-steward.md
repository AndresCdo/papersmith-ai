# Feature: a backlog steward that reviews, groups and resolves papersmith's issues and PRs

Objective: bring gentle-ai's issue/PR practice (root-class triage, evidence-gated closure, issue-first PRs, bounded dual review) into papersmith as repo-only maintainer tooling, then use it on the live backlog (55 issues, PRs #94–#99).
Branch: `feat/backlog-steward` · Delivery: ask-on-risk · Runner: `.micromamba/envs/papersmith/bin/pytest` (focused), `python3 scripts/clean_context_gate.py` (CI gate).

## Specs

- **S1** "revisa el repo https://github.com/Gentleman-Programming/gentle-ai, verifica agentes o skills para resolver issues y pr. revisa como los agrupa testea y acepta." Findings recorded in L2.
- **S2** "explora como podemos llevar y mejorar esas mismas ideas, agentes o skills para que en papersmith revisemos, agrupemos y resolvamos issues y pr": a repo-only maintainer kit under `maintainer/` (never `skills/` or `.claude/agents`, which ship to users through `KIT_ENTRIES`):
  - a protocol skill `maintainer/skills/backlog-steward/SKILL.md` (buckets, root clusters, repro-first, closure rules, PR acceptance, bounded dual review);
  - `maintainer/backlog.py`, stdlib-only: `check` validates `maintainer/backlog/roots.json` against live GitHub (every open issue in exactly one root, every open PR linked to issues of a single root), `stale` flags issues whose cited paths/symbols no longer exist on the checkout, `render` prints the tracker issue body, `pr-link` validates a PR body's issue reference;
  - a CI job requiring a `Closes|Fixes|Resolves|Refs #N` reference in every PR body.
- **S3** "implementa la mejor opcion y usalo para resolver los issues y pr en papersmith": triage every open issue into `roots.json`, restore green CI (#108), evaluate PRs #94–#99 against their roots, fix the contained bug roots with repro tests, close stale/already-fixed issues with evidence. Assumption: pushing, merging, closing and commenting on GitHub wait for one explicit operator confirmation of the prepared batch.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S2 (kit: skill, backlog.py, tests, CI pr-link job, routing docs) | inline | pending | |
| T2 | S3 (triage: roots.json, stale scan, evidence per issue) | delegated read-only explorers (mapping trigger: 55 issue bodies) + inline roots.json | pending | |
| T3 | S3 (#108 green CI) | inline | pending | |
| T4 | S3 (PRs #94–#99: rebase on green main, focused tests, dual review) | per-action reviewers | pending | |
| T5 | S3 (contained bug roots, repro-first) | parallel writers in worktrees (disjoint roots) | pending | |
| T6 | S3 (GitHub batch: tracker issue, closures, merges) | inline, after confirmation | pending | |

## Log

- **L1** (2026-10-25, user verbatim): "revisa el repo https://github.com/Gentleman-Programming/gentle-ai, verifica agentes o skills para resolver issues y pr. revisa como los agrupa testea y acepta. luego, explora como podemos llevar y mejorar esas mismas ideas, agentes o skills para que en papersmith revisemos, agrupemos y resolvamos issues y pr, luego de explorar y planear, implementa la mejor opcion y usalo para resolver los issues y pr en papersmith"
- **L2** gentle-ai findings: `systemic-issue-triage` (buckets A covered / B duplicate / C root cluster / D feature / E unclear; "N issues never justify N patches"), `issue-root-resolution` (meta-issue #2471: 438 issues → 20 roots in tiers; close only on A fixed-with-commit+test, B superseded decision, C code gone, D duplicate of fixed; mechanism is a hypothesis, a repro that passes on main disproves the diagnosis), `branch-pr` + `.github/workflows/pr-check.yml` (issue reference + `status:approved` + one `type:*` label), `chained-pr` (400-line budget, dormant in practice), `judgment-day` (two blind judges, fix only confirmed findings, ≤2 rounds, APPROVED|ESCALATED, no merge authority). Weaknesses to improve: the meta-issue is hand-maintained prose that drifts; the size gate is dormant; nothing machine-checks that every issue sits in one root.
- **L3** papersmith state at `06d27b33`: CI red on main since 2026-10-21 (#108); fork PRs #94–#99 never ran CI (runs `action_required`, awaiting maintainer approval); 35 issues (#52–#86) come from a v0.13.0 audit, so staleness must be checked against current main.

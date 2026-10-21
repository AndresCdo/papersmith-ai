# Papersmith AI — Claude Code Entrypoint

Minimal harness entrypoint. This file does not duplicate guidance; it only routes
to the canonical sources of truth so a single set of docs drives every harness.

## Canonical context

- **Project context**: `openspec/project-context.md`
- **Domain guidelines**: `guidance/paper-guide/` (user drop-zone; loaded automatically by `proposal-deliberation`, optional at rest)
- **Available capabilities (skills)**: `skills/*/SKILL.md`
- **Release procedure**: `docs/releasing.md`

## Skills

Skills live once at the repository-root `skills/` tree and are projected into
`.claude/skills` by `npm run setup:harnesses`. Read each skill's `SKILL.md`
before invoking it; it is the source of truth for that capability.

## Slash commands

Every top-level skill is projected as a Claude Code slash command under
`.claude/commands/` by `python scripts/sync-repo-harness.py`. Each command body
loads its `skills/<name>/SKILL.md` and takes your text as `$ARGUMENTS`. That
directory is a derived artifact — regenerate it with the script (`--check` reports
drift and exits non-zero) instead of editing it by hand.

## Paper construction flow

These are the eleven phases the command center (`papersmith ui`) shows under
"Pipeline y Avance", in order. Each phase card runs its stage: a slash command
`/<skill> <text>` typed into an agent, a `papersmith` command, or a link to the
panel that owns the work. The dashboard locks each phase until the one before
it is verified from its evidence on disk, with an explicit override, and every
skill refuses when its input is missing.

1. **Harness**: `papersmith status .` and `papersmith audit . --check-drift`;
   `/upgrade-project` when the workspace runs an older release.
2. **Plausibility**: `/plausibility <the idea in at least two sentences>`. It
   scouts about 25 SOTA references, draws `sota-pool/atlas.html` and grades the
   claims. Nothing is ingested until the operator accepts the report.
3. **Ingestion**: `/paper-ingestion <PDF or URL>` (or `papersmith ingest`)
   turns the accepted top 5 into Markdown under `guidance/`, with equations
   as LaTeX.
4. **Proposal deliberation**: `/proposal-deliberation` keeps managed revisions
   `proposals/research-concept-<slug>-rNN.md`. Mathematics goes in
   `$$ … \tag{N} $$` display blocks.
   - **Concept map and mathematics**: before implementing a revision, discuss
     its pillars, hypotheses and concept layers (dashboard: Mapa Conceptual &
     Modelo) and its equations with `/math-tutor`, the Socratic tutor that
     also reads hand-written pages.
5. **Proof of concept and experiments**: `/proposal-implementation` builds the
   proof of concept, `/experimental-deliberation` writes the protocol in
   `experiments/`, and `/experimental-implementation` runs its measurements.
   Use `/kaggle-accounts` and `/remote-execution` when they run remotely.
   Only the operator authorizes a launch.
6. **Scaffolding**: `/paper-writing` opens the `paper/` tree and its section
   contracts.
7. **Declarations**: `/paper-writing mark …` records each decision of the
   paper (authorship, funding, data and code, ethics, language, style).
8. **Writing**: `/paper-writing` writes one named block at a time. Every
   claim needs a source that holds it (`resolve`).
9. **Figures**: `/figure-review <figure id>` checks a compiled
   `paper/Figures/<id>.pdf`.
10. **Paper**: compile `paper/main.tex` to `paper/main.pdf` (dashboard:
    Previsualización PDF).
11. **Audit** (transversal): `papersmith audit .` and `/skill-audit <subject>`.
    Audits report; they never repair.

The human gates are plausibility acceptance, proposal and experimental
acceptance, and launch authorization. An agent never passes a gate on the
operator's behalf.

# Papersmith AI — Pi runtime append

Pi appends this file to the project system prompt, and a trusted project copy
takes precedence over the operator's own `~/.pi/agent/APPEND_SYSTEM.md` — the two
are never combined. It does not duplicate guidance; it only routes to the
canonical sources of truth so a single set of docs drives every harness.

## Canonical context

- **Project context**: `openspec/project-context.md`
- **Domain guidelines**: `guidance/paper-guide/` (user drop-zone; loaded automatically by `proposal-deliberation`, optional at rest)
- **Available capabilities (skills)**: `skills/*/SKILL.md`

## Skills

Skills live once at the repository-root `skills/` tree and are projected into
`.pi/skills` by `npm run setup:harnesses`. Read each skill's `SKILL.md`
before invoking it; it is the source of truth for that capability.

## Invoking skills

Every top-level skill under `skills/` is also generated as a Pi prompt template
in `.pi/prompts/<name>.md`, so it can be invoked as `/<name>`. Each template
loads that skill's `SKILL.md` and passes your text through as `$ARGUMENTS`. The
directory is a framework artifact: regenerate it with `python scripts/sync-repo-harness.py`
(`--check` reports drift), so do not edit it by hand.

## Agents

Subagent definitions are projected from `.claude/agents/` into `.pi/agents/` by
`python scripts/sync-repo-harness.py`. Pi core has no sub-agents: those files are
read only when the third-party `pi-subagents` package is installed. Edit the
source in `.claude/agents/`, never the projection.

## Safety extension

`.pi/extensions/refuse-offpath-push.js` is generated. It registers a `tool_call`
handler that relays `bash` commands to
`skills/remote-execution/scripts/hooks/refuse_offpath_push.py` and blocks only
when the guard exits with status `2`; it fails open when the guard, python or
the event is unusable. It is a tripwire, not a gate. See `docs/guard-hooks.md`.

## Paper construction flow

These are the eleven phases the command center (`papersmith ui`) shows under
"Pipeline y Avance", in order. Each phase card runs its stage: a slash command
`/<skill> <text>` typed into an agent, a `papersmith` command, or a link to the
panel that owns the work. Every skill refuses when its input is missing, so the
order is a recommendation and not a lock.

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

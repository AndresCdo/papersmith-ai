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

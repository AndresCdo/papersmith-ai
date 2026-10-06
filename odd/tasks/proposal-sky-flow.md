# Feature: the proposal's sky becomes a step of the flow, not an appendix

## Objective

The graph that overlays the proposal on the SOTA constellation exists, works and
is documented — and no flow runs it. `skills/proposal-deliberation/SKILL.md:71`
describes the three-step chain (`merge_proposal_sky.py` → `check_atlas.py` →
`render_atlas.py --title`), the tool has tests, and the artifact is never
produced by anything the repository can point at.

Three surfaces have to carry it, and none of them does today:

1. **The architecture diagram** (`.archify/architecture-papersmith-pi-20261004-173559/build.mjs`,
   rendered to `docs/diagrams/papersmith-pi-flow.{html,png}`) draws carril 3 as
   `/proposal-deliberation` → `cli.mjs --serve` → `Aceptación humana` →
   `deliberation-publish` → `proposals/` with detail `research-concept-rNN.md`.
   `atlas.html` appears only in the plausibility lane, in the `sota-pool/` node.
2. **The dashboard's general flow** transcribes that diagram:
   `skills/_core/command_center/state_extractor.py:53` `PIPELINE_STAGES`, where
   `plausibility` is lit by `SOTA_POOL_ARTIFACTS` (`:107`) and `proposal` by
   `_count_matching(root / "proposals", "*.md")` (`:755`). No dashboard code
   mentions `graph.html` or `atlas.with-proposal.json`.
3. **The agents**: `deliberation-publish` is the only delegated stretch of the
   deliberation and the only agent mapped to the `proposal` tramo
   (`AGENT_STAGES`, `:125`). Its definition mentions neither graph nor sky nor
   atlas, and no agent in `.pi`, `.claude`, `.agents` or `.opencode` references
   `merge_proposal_sky.py` or `atlas.with-proposal.json`.

## What already exists (verified, not assumed)

- The chain is real and tested: `skills/proposal-deliberation/scripts/merge_proposal_sky.py`
  (stdlib), `skills/plausibility/scripts/{check_atlas,render_atlas}.py`, and
  `tests/test_proposal_sky.py`, which holds the merger to the whole chain rather
  than to its own output. Twelve tests plus the `--title` tests shipped in 0.8.0.
- The diagram is generated, never hand-edited: `build.mjs` declares nodes with
  `n(id, lane, col, type, label, sublabel, {sources})` and edges with
  `e(from, to, label?, {variant?})`, reading agent metadata straight out of
  `.pi/agents/*.md` through `agentMeta`. The rendered `html` and `png` are the
  only tracked artifacts; `.archify/` lives in the parent directory, outside the
  repository and outside any git repository.
- `.claude/agents/` is the agents' SSOT (`generators.py:3`), a kit entry
  (`core/manifest.py:53`) and **not** a projection target of
  `scripts/sync-repo-harness.py` — that script copies back `.pi/agents/`,
  `.opencode/agents/`, `.agents/agents/`, `.pi/prompts/`, `.pi/extensions/`,
  `.claude/commands/` and `.opencode/commands/`, each with its own tool-name
  mapping and skill-path rewrite. `agentMeta` in `build.mjs` reads `.pi/agents/`.
- `scripts/build-kit.py` snapshots `skills/`, the agent definitions and the
  manifests into `src/papersmith/_kit/` and its kit manifest, which ships in
  `papersmith init` and is re-synced by `papersmith upgrade`.
- The extractor's tramo table is held by
  `tests/test_command_center_state.py::test_each_tramo_lights_up_from_its_own_artifact`:
  a `(stage_id, setup, expected)` list asserted with exact set equality, plus a
  final check that every tramo has a case.

## Design decisions

1. **The graph is the terminal stretch's work, not the arrival.** The skill's
   arrival is "the successor revision published and current, which is the only
   form the mathematics travels in", and it is declared in two places held equal
   by a test (`SKILL.md` and `profile.ts`). The graph is an artifact beside the
   revision, so the arrival does not move; the publish stretch gains the work.
2. **The overlay stays authored during the deliberation.** The stretch has no
   `Write` and no `Edit` and says so; the overlay is deliberated content (which
   SOTA papers the proposal touches and why), so it is authored by the tutor
   session that already holds the write tools. The stretch *requires* it, runs
   the chain on it, and reports it as owed when it is absent — it never invents
   a relation to have something to draw.
3. **Two artifact kinds light one tramo, and the detail names both.** The
   `proposal` tramo reports the published revisions and the sky graphs
   separately and its progress is a ratio over the pair, because a revision
   without its graph is exactly the half-done state this feature exists to make
   visible. A tramo lit by either kind alone would hide it.
4. **The graph is a node in carril 3, not a thirteenth tramo.** The twelve
   tramos are the diagram's lanes and the dashboard transcribes them one for
   one; the graph is produced inside proposal deliberation, so it belongs to
   carril 3's drawing. `PIPELINE_CHAIN` is untouched: it is tramo-to-tramo, and
   this adds no tramo.
5. **The diagram's source moves into the repository.** `.archify/…/build.mjs`
   was untracked and lived outside the repository, so the regeneration was not
   reproducible from a clone — a defect this feature would otherwise have
   inherited. The source is now `docs/diagrams/papersmith-pi-flow.build.mjs`,
   with repository-relative paths, a `locales/es.json` vendored from Archify
   3.0.1 (MIT), and the procedure in `docs/diagrams/README.md`. Re-running it
   reproduces the archived candidate (`6a7540aa…`) and the committed artifact
   (`6cd883d9…`) byte for byte, with the four gates green, from a scratch
   directory and with no dependency on the machine-specific `.archify/` folder.

## Slices

- **S1** Extractor: the `proposal` tramo observes `proposals/*.graph.html`, its
  detail names both counts, and its progress is the ratio over the pair. RED
  first: a workspace holding only a graph must light `{"proposal"}` and a
  revision alone must not report the same progress as a revision plus a graph.
- **S2** Agent: `.claude/agents/deliberation-publish.md` gains the graph to its
  stretch — require the overlay, run merge → check → render, report the HTML,
  and report the overlay as owed when it is missing. Regenerate the harness
  projections and the kit.
- **S3** Docs: `skills/proposal-deliberation/SKILL.md` pins *when* the overlay is
  authored (during the deliberation, before the change is accepted) and says the
  publish stretch runs the chain; `CHANGELOG.md`.
- **S4** Diagram: the node and its edge in `build.mjs`, the diagram regenerated
  with the four Archify gates green, and the PNG recaptured at the same framing.
- **S5** Version `0.11.0` (three literals + the `## 0.11.0` section + the pinned
  README example) because `skills/` changed since `v0.10.0`.

## Checks

Runners: `.venv/bin/python -m pytest tests/test_command_center_state.py
tests/test_command_center_cli.py tests/test_command_center_server.py -q`,
`python3 scripts/build-kit.py`, `python scripts/sync-repo-harness.py --check`,
`.venv/bin/python -m pytest tests/test_harness_parity.py tests/test_version_sources.py -q`,
the vocabulary floor over every file this touches
(`tests/forge_vocabulary.py::leaks_in`), and the fast tier with
`--since <previous-sha>` — the plain form selects nothing once the work is
committed.

The diagram's gates are Archify's own (`validate`, `deliver`, `check`,
`browser-check`), run from the parent `.archify` directory, plus the PNG capture
with `?embed=1` at 1400 px so the framing matches its predecessor.

## Evidence

- **S1** `9d63874`. RED observed and honest: the graph-only case lit no tramo
  and the detail carried no second count. GREEN: `tests/test_command_center_state.py`
  25 passed (13 subtests) and the command center suite (state + cli + server) 70
  passed. Non-vacuity is the RED itself, plus the pair assertions: a revision
  alone and a graph alone both report 0.5, the two together report 1.0, and an
  empty workspace still reports `no proposal revision`.
- **S2** `d9beaea`. The harness projections regenerated with
  `scripts/sync-repo-harness.py` (3 of 92 files: `.pi`, `.opencode`, `.agents`;
  `.claude/agents/` is the SSOT and was edited directly, and it is deliberately
  not a projection target). `--check` reports clean over 92 files;
  `test_harness_parity.py` 9 passed, 27 subtests; the vocabulary floor is empty
  for all four copies of the agent.
- **S3** `c16b34e`. Vocabulary floor empty on the skill. The insert moved every
  line after it by 10, which shifted the diagram's own source pointers
  (`SKILL.md:241,277` → `251,287`); S4 fixes them, and the equality of the two
  ranges was checked against `git show` of the pre-edit file rather than assumed
  from the count.
- **S4** `11e0648`, re-measured after independent verification and corrected
  here. The sixth-node attempt was a measurement, and it has now been re-run and
  captured so the claim can be checked rather than inherited. First attempt
  (`cols:6`, `cellW:176`, `gapX:14`): `composition/label-gap` refused the
  `proposals → sky` edge — 26px of clear space for a label needing 127px — and
  with the edge unlabelled `layout/constraint` refused the metrics themselves:
  `Label "/experimental-implementation" (~185px) is wider than component
  "expImpl" (176px)` and `Connection "canon->sync" is too short (14px; minimum
  24px)`. Second attempt, at the least aggressive metrics that satisfy both of
  those floors (`cellW:190`, `gapX:24`): one diagnostic survives,
  `composition/desktop-readability`, with `viewBoxWidth` 1370, `scale` 0.6788,
  `projectedFontPx` 5.43 against `minimumProjectedFontPx` 6, at
  `availableDiagramWidth` 930 and `budgetBasis legacy-930` for 8px source text.
  Those two numbers imply a 1240px ceiling, which the six-column figure clears
  by nothing — it is 130px above it. Every number in this paragraph is gate
  output from that reconstruction except the derived 1240. With the graph as the
  second artifact of the existing node the artifact finalizes green: `validate`,
  `deliver`, `check` and `browser-check` all pass for
  `6cd883d9a5eb4a330d06d965fbc9d6247adf803f54b538d667f1ecd78f557d08`, and the
  committed HTML is byte-identical to it. The browser gate's own measurements on
  that artifact: `viewBoxWidth` 1144, minimum projected node text 6.67px,
  containment pass at 1440×900 with a readable vertical scroll, and six
  viewport/theme combinations pass. PNG recaptured at 1400px, the same width as
  its predecessor (`?embed=1`, full page, device pixel ratio 1 forced, since the
  default capture came out at 2×).
- **S5** `04a2d75`. `tests/test_version_sources.py` and
  `test_papersmith_generators.py` 54 passed once the version moved; the guard
  had been red on the branch before it, which is the rule firing and not a
  defect. The README pin stays on `v0.10.0`, following the 0.9.0 precedent
  (verified against `d9c9922`, where the tree said 0.9.0 and the pin 0.8.0).
- **Whole branch**, run twice and last at `726ae61`: fast tier
  `--since 04f76fc` → 6 failed, 3161 passed, 3 skipped, 1112 subtests. The first
  run, at `df81838` before the verification fix, reported 3160 passed; the new
  test is the difference. All six failures are pre-existing and environmental: five `GateInterpreterTests` that need a micromamba environment
  this checkout does not have, and one that asserts a case-sensitive filesystem,
  which macOS is not. `sync-repo-harness.py --check` clean (92 files).

### What independent verification changed, and what it did not

An independent read-only pass checked this record against the code after the
branch was written. It confirmed A–E and G (the extractor's counts and strings,
the unchanged stage and chain shapes, the agent's section with its unchanged
frontmatter and its absent write tools, the three regenerated projections, the
skill's two new statements, the byte-identical arrival, and the three version
literals) and it confirmed H for everything cheaply checkable while declining
the five-minute fast-tier run. It also corrected three things in the prose
above, which is why this section exists:

1. **S4's rationale was not receipt-backed.** The rejected attempts left no
   surviving receipt in the diagram's folder — `review-2` and `review-3` failed
   on provenance, not composition — so the original wording presented an
   un-reproducible measurement as settled. The paragraph above now quotes the
   diagnostic codes verbatim from a re-run, separates the one derived number
   from the measured ones, and the reconstruction is a four-field edit to the
   versioned source (`cols`, `cellW`, `gapX`, plus the node), so a reader can
   re-derive every number in it.
2. **The record named the wrong diagnostic.** The surviving receipts say
   `delivery/provenance-hardlink-unsupported`; `requested-entry-hardlinked` was
   the reason inside `finalize/receipt-publication` on an earlier run.
3. **The folder's top-level receipt is a failure.**
   `papersmith-pi.finalize.json` records `ok: false` for the committed sha
   because that run stopped at `viewer/evidence-path-conflict`; only
   `review-4/papersmith-pi.finalize.json` carries the four green gates for those
   exact bytes. "The artifact finalizes green" is true of the newest run and was
   not true of the first receipt a reader would open.

Two consequences it surfaced, accepted rather than papered over:

- **The agent's `description` still carries only the arrival**, so an
  orchestrator choosing it by description gets no signal that the graph — or the
  `owed` report — is part of the stretch. That follows from decision 1: the
  arrival is held equal to `profile.ts` by
  `tests/proposal-deliberation-objective-flow.test.mjs`, and moving it would be a
  doctrine change, not this one.
- **The artifact-name convention had no test binding its two ends.** The
  extractor keys on `*.graph.html` and the skill instructs
  `--out proposals/<revision>.graph.html`, with nothing comparing them. Both
  ends now name the path (the agent says `proposals/<revision>.graph.html` when
  it reports), and `test_the_glob_matches_the_artifact_the_skill_names` fails if
  either side is renamed.

### Limitations of this evidence, the second of them since resolved

1. **Archify's strict-provenance checks could not run here.**
   `visual-check --require-provenance` and `check` on the repository copy both
   refuse, in the surviving receipts, as
   `delivery/provenance-hardlink-unsupported` with `links: 2`; an earlier run
   reported the same condition as `finalize/receipt-publication` with reason
   `requested-entry-hardlinked`. The gate requires exactly one link to prove
   every name was updated atomically, and the extra name is not findable:
   `find -inum` over the whole tree returns only the file itself, while a fresh
   file written by `cp`, by a shell redirect or by Python in the same directory
   reports one link. The cause was not identified, so this is an observed
   property of the environment, not a diagnosis — and it blocks the provenance
   chain, not the four gates, which ran on the `.archify` artifact where the
   count was one.
2. **The diagram's source was unversioned, and no longer is.** It lived in the
   parent directory, outside the repository and outside any git repository, so
   the regeneration above was not reproducible from a clone. That is now
   decision 5: the source is versioned in `docs/diagrams/` and reproduces both
   the archived candidate and the committed artifact byte for byte. What stays
   external is Archify itself — the pinned 3.0.1 binary is a documented
   prerequisite of the recipe, not something the repository carries.

## Next step

None: shipped. `feat/proposal-sky-flow` merged into `main` as `ff12fb0`,
`chore/release-0.11.0` as `4eb4606`, and annotated tag `v0.11.0` sits on
`4eb4606` with the GitHub release published. The audit over all thirteen tags
is consistent, `pip install "papersmith-ai @ git+…@v0.11.0"` in a throwaway
environment yields 0.11.0, and the merged branches are deleted.

The first real deliberation in a workspace is still the first execution of this
chain against real data, now with an agent that will report the missing overlay
instead of skipping it silently.

`docs/diagrams/README.md` carries the regeneration recipe; nothing else is owed
by this record.

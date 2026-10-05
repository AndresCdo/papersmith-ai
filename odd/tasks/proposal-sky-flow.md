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
5. **The diagram's own source is not versioned, and the record says so.**
   `.archify/…/build.mjs` is untracked and lives outside the repository. The
   regeneration is therefore not reproducible from a clone, which is a property
   of the existing setup, not something this feature introduces — noted here so
   the next person does not look for it.

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
- **S4** `11e0648`. The sixth-node attempt was measured, not guessed: the
  `proposals → sky` edge was first rejected for label room (`composition/label-gap`,
  26px clear against a 127px need), and with the label removed the gate named the
  real limit — a connection needs `gapX ≥ 24` and the widest label
  (`/experimental-implementation`, ~185px) needs `cellW ≥ 190`, which puts a
  six-column viewBox near 1370px against the 1240px budget that keeps 8px source
  text at or above the 6px floor. With the graph as the second artifact of the
  existing node the artifact finalizes green: `validate`, `deliver`, `check` and
  `browser-check` all pass for
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
- **Whole branch**: fast tier `--since 04f76fc` → 6 failed, 3160 passed, 3
  skipped, 1112 subtests in 5m12s. All six failures are pre-existing and
  environmental: five `GateInterpreterTests` that need a micromamba environment
  this checkout does not have, and one that asserts a case-sensitive filesystem,
  which macOS is not. `sync-repo-harness.py --check` clean (92 files).

### Two limitations of this evidence, stated rather than implied

1. **Archify's strict-provenance checks could not run here.**
   `visual-check --require-provenance` and `check` on the repository copy both
   refuse: the artifact and its delivery sidecar report `links: 2`, and the gate
   requires exactly one link to prove every name was updated atomically (the
   same condition produced two spurious `requested-entry-hardlinked` failures
   before the artifact finalized). The extra name is not findable: `find -inum`
   over the whole tree returns only the file itself, while a fresh file written
   by `cp`, by a shell redirect or by Python in the same directory reports one
   link. The cause was not identified, so this is an observed property of the
   environment, not a diagnosis — and it blocks the precedence chain, not the
   four gates, which ran on the `.archify` artifact where the count was one.
2. **The diagram's source is not versioned.** `.archify/…/build.mjs` lives in
   the parent directory, outside the repository and outside any git repository,
   so the regeneration above is not reproducible from a clone. Decision 5
   records this as a property of the existing setup that this feature neither
   introduced nor fixed.

## Next step

Merge `feat/proposal-sky-flow` into `main`, then release 0.11.0 following
`docs/releasing.md`: the release commit is where the README's pinned example
moves to `v0.11.0`, and the tag belongs on its merge commit.

The first real deliberation in a workspace is still the first execution of this
chain against real data, now with an agent that will report the missing overlay
instead of skipping it silently.

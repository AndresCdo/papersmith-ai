# Feature: the proposal's own sky (stage 3 artifact, SOTA-related)

## Objective
Stage 3 (proposal deliberation) ships a 3D graph artifact beside its published
revision: the SOTA sky rebuilt and overlaid with the proposal — its main idea,
the topics/items of the SOTA papers it touches, and 3–5 concepts that carry the
novelty and the issues it could resolve.

## What already exists (verified, not assumed)
- `skills/plausibility/scripts/render_atlas.py` (stdlib only) reads
  `sota-pool/atlas.json` and writes ONE self-contained HTML: the scene is
  computed in Python and written as a JSON data island, and the vendored
  three.js viewer (`skills/plausibility/assets/atlas3d.bundle.js`, 564 KB,
  rebuilt with `npm run build:atlas-viewer`) is inlined verbatim. No CDN, no
  network at view time, deterministic: same atlas, byte-identical sky.
- `skills/plausibility/scripts/check_atlas.py` is the contract: slot vocabulary,
  family membership, planet ceiling per system, dated evidence, and 2–5 families
  ("one family is no constellation, six is no constellation").
- The slot vocabulary ALREADY carries what this feature needs: `novelty`,
  `problem`, `topic_app`, `topic_ai`, `application`, `sun`, `family`. The
  relation vocabulary already carries `about`, `addresses`, `extends`,
  `contradicts`, `supports`, `yields`.
- `tests/test_sota_atlas.py` (272 lines) builds synthetic atlases and holds both
  the checker and the renderer, including "every planet has a point in three
  dimensions" and "the vendored viewer is inlined verbatim".

## Design decisions
1. **No second geometry engine.** The proposal graph is a *merged atlas*
   rendered by the existing renderer. The merge is data, not code: the SOTA
   systems stay exactly as they are, and the proposal enters as one more system
   with its own planets and links. This is what makes "the SOTA graph is updated
   and related to the proposal" literal rather than a second picture that can
   drift from the first.
2. **The merge emits a checker-valid atlas.** The output goes through the
   existing `check_atlas.py`, so the proposal's system must satisfy the same
   rules as a real SOTA system (dated evidence, ceiling, family membership).
   Reusing the checker as the contract is what keeps the overlay honest.
3. **The proposal's concepts are authored data, not parsed prose.** A sidecar
   JSON written during the deliberation — `proposals/research-concept-rNN.sky.json`
   — carries the proposal's planets and its links into SOTA ids. This mirrors how
   `atlas.json` is authored for the SOTA pool, and keeps the renderer
   deterministic and stdlib-only. Parsing headings out of the published Markdown
   was rejected: it would make the artifact's content depend on prose formatting.
4. **The artifact travels beside the revision**, as
   `proposals/research-concept-rNN.graph.html`, and the published revision links
   to it. The engine's publish transaction stays byte-exact over Markdown; the
   graph is a rendered sibling, not a second thing the transaction must hash.
5. `render_atlas.py` gains an optional `--title` so the artifact presents itself
   as the proposal's sky rather than as the SOTA constellation. The default
   stays byte-identical for the plausibility flow.

## Slices
- **S1** `--title` on `render_atlas.py` (+ the checker is untouched), behaviour
  preserved by default: prove byte-identical output on the existing fixtures.
- **S2** `skills/proposal-deliberation/scripts/merge_proposal_sky.py` (stdlib) —
  reads the SOTA atlas plus the proposal sidecar and writes a merged atlas.
  RED first: the merged output must pass `check_atlas.py` and must keep every
  SOTA system and link it was given.
- **S3** Contract and docs: `skills/proposal-deliberation/SKILL.md` gains the
  sidecar shape and when stage 3 renders the graph; `skills/plausibility/SKILL.md`
  gains the `--title` note; CHANGELOG.

## Checks

Runners: `.venv/bin/python -m pytest tests/test_sota_atlas.py tests/<new> -q`,
then the fast tier `.venv/bin/python scripts/fast_tests.py`, kit rebuild
(`python3 scripts/build-kit.py`, because `skills/` changed), and
`python scripts/sync-repo-harness.py --check`.

## Evidence

Backfilled on 2026-10-05, after the fact: the branch shipped in **0.8.0** and
this section was left as `(pending)` while the record was untracked, then
committed that way in `44a5107`. Each row cites the commit that carries the
claim; the counts are the ones the commits state, not re-measured when this
section was written.

| Slice | Commit | What it carries |
| --- | --- | --- |
| S1 — `--title` | `6baadf3` | `render_atlas.py` names the page in both the tab title and the heading, escaped; three tests, two of which fail against the previous renderer (it exits 2 on the unknown flag). Default output unchanged across a before/after render: `cf2fbdf1…` plain, `720f4f11…` with links |
| S2 — the merge | `6514389` | `merge_proposal_sky.py` plus the optional `contribution` slot (orbit 1, 0..5); twelve tests hold the chain end to end (merge, check, render) and the three refusals, and the two contract tests fail against a merger with the 3..5 range removed |
| S3 — contract and docs | `4854ee6` | the `contribution` row and the `--title` note in `plausibility/SKILL.md`, the overlay shape and the merge → check → render chain in `proposal-deliberation/SKILL.md`, plus the CHANGELOG entry. Independent verification read both files against the code and found three prose gaps, all fixed here: the relation set listed six of seven members, the overlay's planets omitted the `result` and `conclusion` nodes the checker requires of every system, and "stage 3" named a step neither skill defines. The forge-wide vocabulary guard also caught "ceiling" in the new script's prose as another repository's vocabulary, and the sentence now says "upper bound" |

Contract decision worth keeping: the merger refuses only merge incoherence (an
id already taken, a link with no planet to land on) and the overlay's own
contract; `check_atlas.py` stays the single authority on families, orbits and
evidence. That split is proven by the five-family pool that merges fine and is
then refused by the checker, named, in the same run.

The branch merged into `main` as `6236d61` and shipped in **0.8.0** (`e7fb53f`,
tag `v0.8.0`).

## Known gap (not a task)

The chain was never run against a real workspace: the two SKILL examples were
not executed over a real `sota-pool/atlas.json` and a real overlay, because the
overlay is authored by the deliberation itself. The first real deliberation in a
workspace is therefore the first execution of this path against real data, and
should be treated as such.

## Next step

None: shipped in 0.8.0. The gap above is a property of when the path gets its
first real input, not pending work in this record.

# The Pi flow diagram

`papersmith-pi-flow.html` is this repository's flow of record: the twelve
numbered tramos plus the transversal audit lane, drawn from the repository's own
files. The dashboard's *Pipeline* tab transcribes it — `PIPELINE_STAGES`,
`PIPELINE_CHAIN` and `GATE_SOURCES` in
`skills/_core/command_center/state_extractor.py` — and
`tests/test_command_center_state.py` holds the transcription, so the drawing and
the board cannot drift apart without a failing test.

| File | What it is |
| --- | --- |
| `papersmith-pi-flow.html` | The artifact: self-contained, offline, no network at view time |
| `papersmith-pi-flow.png` | The same drawing as an image, for readers who do not open HTML |
| `papersmith-pi-flow.build.mjs` | The source |
| `locales/es.json` | The translation table the rendered page embeds, vendored from Archify 3.0.1 (MIT) |

The source is here, and not only in the throwaway `.archify/` folder it was
authored in, because a diagram whose source lives outside the repository cannot
be regenerated from a clone — and one nobody can regenerate stops being evidence
and becomes an assertion. It was untracked until 0.11.0.

## Regenerating

Requirements: Node, and the Archify skill at the version the artifact was
rendered with (**3.0.1** — the bytes are the renderer's, so the version is part
of the recipe). The candidate records the repository revision it describes in
`meta.repository.revision`, and every node's `sources` names the path and line
range it was transcribed from, so the drawing is checkable against the code
rather than trusted.

```bash
SCRATCH=$(mktemp -d)
node docs/diagrams/papersmith-pi-flow.build.mjs "$SCRATCH/candidate.json"
node ~/.claude/skills/archify/bin/archify.mjs finalize architecture \
  "$SCRATCH/candidate.json" "$SCRATCH/papersmith-pi-flow.html" \
  --repo-root . --quality showcase --out-dir "$SCRATCH/evidence" --json
cp "$SCRATCH/papersmith-pi-flow.html" docs/diagrams/papersmith-pi-flow.html
```

`finalize` runs the four gates — showcase validation, delivery, strict
provenance check, and a real-browser check — and a passing receipt means all
four passed. A non-zero exit is never success.

`--out-dir` keeps each run's browser evidence apart from the last one: reusing a
directory whose artifact bytes have changed is refused, and that refusal is
about evidence ownership rather than about the drawing. Two gates have measured
teeth worth knowing before editing the layout: `layout/constraint` refuses a node
label wider than its cell or a connection shorter than 24px, and
`composition/desktop-readability` refuses a figure whose projected node text
falls under 6px at a 1440px viewport — which is what caps the viewBox at roughly
1240px.

## The PNG

The page draws at whatever width the viewport gives it, so the frame is a
capture decision rather than part of the artifact. The committed PNG is 1400px
wide at **device pixel ratio 1**, captured full-page with `?embed=1` (which is
what drops the viewer's own chrome). A browser driver needs those three
parameters; the ratio is the one that is easy to get wrong, because the default
capture comes out at 2× and a 2800px file is four times the bytes for a drawing
nobody reads at that size.

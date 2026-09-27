# Figure Raster Specification

## Purpose

`render` produces a compiled figure PDF and stops there; nothing today turns
that PDF into pixels, and nothing computes a geometric fact from it. This spec
pins the tenth skill, `figure-review`, that closes that gap: a deterministic
rasterizer fallback chain over an already-compiled `Figures/<id>.pdf`, the
geometric facts a raster can actually support, its own subprocess seam, its
presence as a command rather than a session judgement, and the test evidence
that proves all of it without ever touching `render`'s repair budget.

This spec does not decide which visual dimensions carry a verdict versus an
announced silence, or how a finding reaches `figure audit`'s report — that
taxonomy is `visual-finding-boundary`'s spec, and the schema join is
`diagram-obligation`'s.

## Requirements

### Requirement: Consumes an Already-Compiled PDF, Compiles Nothing

`figure-review`'s front door MUST accept the path to an already-compiled
`paper/Figures/<id>.pdf` and MUST NOT invoke `latexmk` or any other LaTeX
toolchain. It MUST NOT read from or write to `render`'s repair-budget ledger
(`REPAIR_BUDGET` and its per-id attempt count) under any code path, including
a failed rasterization.

#### Scenario: A full visual pass leaves the repair ledger untouched

- GIVEN a figure id with an existing repair ledger and a compiled `<id>.pdf`
- WHEN `figure-review` rasterizes and computes every geometric fact for that id
- THEN the ledger's bytes are identical before and after the pass, and its
  `attemptsUsed` count is unchanged

#### Scenario: A rasterization failure still spends no budget

- GIVEN a compiled `<id>.pdf` and a rasterizer chain that fails every link
- WHEN `figure-review` runs against that id
- THEN the repair ledger is unchanged, because failure to rasterize is not a
  compile failure and has no ledger to spend

### Requirement: Rasterizer Fallback Chain

`figure-review` MUST attempt rasterizer tools in this fixed order — `pdftoppm`,
`pdftocairo`, `gs`, `sips` — using the first tool it can locate on `PATH`, and
MUST NOT attempt a later link once an earlier one has successfully produced a
raster. Each attempted invocation MUST be independently provable: a test
holding only one link present on an injected `PATH` MUST exercise that exact
link and no other.

#### Scenario: The first link present is used

- GIVEN an injected `PATH` on which only `pdftoppm` resolves
- WHEN `figure-review` rasterizes a compiled PDF
- THEN `pdftoppm` is invoked and no other rasterizer tool is invoked

#### Scenario: A middle link is reached only when earlier links are absent

- GIVEN an injected `PATH` on which only `gs` resolves
- WHEN `figure-review` rasterizes a compiled PDF
- THEN `gs` is invoked, and neither `pdftoppm` nor `pdftocairo` was attempted
  as a successful producer

#### Scenario: The last link is reached only when every other link is absent

- GIVEN an injected `PATH` on which only `sips` resolves
- WHEN `figure-review` rasterizes a compiled PDF
- THEN `sips` is invoked and the raster it produces is accepted

### Requirement: Toolchain Absence Refuses By Name, Never Reports Unmeasured

When none of `pdftoppm`, `pdftocairo`, `gs`, or `sips` resolves on `PATH`,
`figure-review`'s front door MUST exit 2 with a named refusal code (for
example `RASTER_TOOLCHAIN_ABSENT`) naming every tool it probed and the exact
`PATH` it searched. This refusal MUST NOT be reported as `unmeasured`: an
absent tool is an unreadable invocation, not a visual dimension the pipeline
declined to judge.

#### Scenario: An emptied PATH refuses naming every probed tool

- GIVEN an injected `PATH` on which none of the four rasterizer tools resolves
- WHEN `figure-review`'s front door runs against a compiled PDF
- THEN it exits 2, and the refusal names `pdftoppm`, `pdftocairo`, `gs`, and
  `sips`, and the searched `PATH`

### Requirement: Out-of-Bounds Ink Is a Computed Verdict

`figure-review` MUST detect non-background ink inside the outermost pixel row
or column of a rasterized figure. When the compiled figure's source declares a
border (a `border` option on its `\documentclass[tikz,...]{standalone}`
header), `figure-review` MUST report `pass` or `fail` for that dimension,
naming the offending edge and the pixel count when it fails. The outermost
border band MUST be exactly one pixel wide; ink one pixel further inward MUST
NOT be counted. When the source declares no border, out-of-bounds ink cannot
be distinguished from a canvas that was fitted to its own ink, and the
dimension MUST instead be reported `unmeasured`, per the scenario below.

#### Scenario: Ink on the exact outermost pixel row fails

- GIVEN a raster with non-background ink placed on its outermost pixel row,
  compiled from a source that declares a border
- WHEN the out-of-bounds check runs
- THEN it reports `fail`, naming that edge and the ink's pixel count

#### Scenario: Ink one pixel inward from the border passes

- GIVEN a raster with non-background ink placed one pixel inward from every
  edge, and none on the outermost row or column, compiled from a source that
  declares a border
- WHEN the out-of-bounds check runs
- THEN it reports `pass`

#### Scenario: A border-less standalone source reports unmeasured, not fail

- GIVEN a compiled figure whose `\documentclass[tikz]{standalone}` declares
  no `border` option
- WHEN the out-of-bounds check runs
- THEN it reports `unmeasured` with reason `NO_DECLARED_BORDER` rather than
  `fail`, because a border-less standalone fits its own canvas to its ink by
  construction

### Requirement: Ink-Region Overlap Is a Computed Verdict, Reported Unnamed

`figure-review` MUST detect connected non-background ink regions and MUST
report `pass` or `fail` for whether any two regions' bounding boxes intersect.
A failing report MUST name the intersecting boxes in both pixel and point
coordinates. The check MUST use strict intersection: two regions whose
bounding boxes share only a boundary edge, with zero interior penetration,
MUST NOT be reported as overlapping. Overlap findings MUST refer to regions by
their coordinates only — never by a component name, since a raster carries no
component identity.

#### Scenario: Boxes sharing exactly one edge do not overlap

- GIVEN two ink regions whose bounding boxes share exactly one edge column and
  no interior pixels
- WHEN the overlap check runs
- THEN it reports `pass`

#### Scenario: One pixel of penetration overlaps

- GIVEN two ink regions whose bounding boxes share one column of interior
  overlap beyond their shared edge
- WHEN the overlap check runs
- THEN it reports `fail`, naming both boxes' pixel and point coordinates, with
  no component name attached to either

### Requirement: Canvas Occupancy Is Evidence, Never a Verdict

`figure-review` MUST report the non-background pixel fraction per band or
quadrant of the raster as a number. This dimension MUST NOT carry a `pass` or
`fail` value under any measured fraction — reporting how much of the canvas is
occupied is a fact; deciding whether that fraction is too much or too little
is a judgement about composition that this spec does not make.

#### Scenario: A large blank fraction is reported without failing

- GIVEN a raster whose lower half is entirely background
- WHEN canvas occupancy is computed
- THEN the lower band's near-zero non-background fraction is reported as a
  number, with no `pass`/`fail` field attached to it

### Requirement: Background Threshold, Resolving Tool, and DPI Are Recorded

Every geometric finding MUST record the non-background threshold used to
distinguish ink from background, which rasterizer link produced the raster,
and the DPI at which it was rasterized. A finding MUST NOT be presented as
comparable to a finding produced by a different rasterizer link or a
different DPI.

#### Scenario: A finding names its own provenance

- GIVEN a completed out-of-bounds or overlap check
- WHEN its result is reported
- THEN the report includes the background threshold, the resolving rasterizer
  tool's name, and the DPI used to produce the raster it measured

### Requirement: Figure-Review Declares Its Own Subprocess Seam

`figure-review` MUST declare its own subprocess-import allowlist, scoped to
`skills/figure-review/scripts/*.py` and pinned to exactly one named module
(the rasterizer invocation module). Its own AST scan MUST mirror all four
assertions that `paper-writing`'s `NoSubprocessScanTests` proves for its own
seam: the exception tuple has exactly one entry, that entry names the exact
rasterizer module, an unlisted script importing `subprocess` is caught, and
the scan covers every script in the skill's own `scripts/` directory.

#### Scenario: A planted subprocess import outside the exception is caught

- GIVEN a second script under `skills/figure-review/scripts/` that imports
  `subprocess` and is not the declared exception module
- WHEN `figure-review`'s own subprocess scan runs
- THEN it reports that script as a violation

#### Scenario: The exception tuple holds exactly one name

- GIVEN `figure-review`'s subprocess-exception tuple
- WHEN its length is inspected
- THEN it equals exactly `1`, and that one entry names the rasterizer
  invocation module

### Requirement: Presence Is a Command the Front Door Answers

`figure-review`'s front door MUST answer a `--help` (or equivalent) invocation
and MUST report which rasterizer link it resolved on the current `PATH`.
Whether the skill is usable MUST be measurable by running this command and
reading its exit and output, never by an agent's unverified claim that the
skill is "available in this session".

#### Scenario: The front door reports its resolved rasterizer

- GIVEN `figure-review` installed with at least one rasterizer tool on `PATH`
- WHEN its front door is invoked to report its resolved toolchain
- THEN it exits 0 and names the rasterizer link it would use

### Requirement: No-Skip Test Evidence Across Three Tiers

The suite MUST run three tiers unconditionally, on a machine with no
rasterizer installed: fixture-driven geometry assertions against committed
rasters, a stubbed rasterizer invocation on an injected `PATH` proving the
invocation shape of each fallback link, and an emptied `PATH` proving the
absence refusal. None of the three tiers MAY be skipped, and none MAY report
`pass` where it did not run.

#### Scenario: All three tiers execute on a machine without any rasterizer

- GIVEN a test machine with none of `pdftoppm`, `pdftocairo`, `gs`, or `sips`
  installed
- WHEN the `figure-review` suite runs
- THEN the fixture-driven, injected-PATH, and empty-PATH tiers all execute,
  and none is skipped

### Requirement: Raster Fixture Provenance

Committed raster (PNG) fixtures used by the fixture-driven test tier MUST be
raw bytes captured from a real rasterization run, never hand-drawn or
hand-edited to make a geometry assertion pass, and MUST record the invocation
that produced them.

#### Scenario: A committed fixture records its capture invocation

- GIVEN a committed PNG fixture under `figure-review`'s test tree
- WHEN its provenance is inspected
- THEN it records the real rasterizer invocation (tool, source PDF, DPI) that
  produced it

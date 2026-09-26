# Authored Diagram Specification

## Purpose

An authored diagram is a standalone TikZ source under `paper/Figures/<id>.tex`,
compiled with `latexmk` and reachable from `main.tex` through
`\includegraphics`. This spec pins the compile contract, the bounded repair
ledger, the toolchain/package refusals, the data-figure boundary, and the test
evidence a no-skip suite must produce. Component and caption checks against
contract obligations are `diagram-obligation`'s spec, not this one.

## Requirements

### Requirement: Source Layout

Each diagram id MUST resolve to `paper/Figures/<id>.tex`, a sibling
`<id>.diagram.json` manifest, and (once compiled) `<id>.pdf`; build scratch
lives under `paper/.paper-writing/figures/<id>/`. `main.tex` receives the
figure only through the existing `substitute` verb's `\includegraphics`; no
TikZ byte enters `main.tex`.

#### Scenario: Manifest without source refuses

- GIVEN `<id>.diagram.json` exists with no matching `<id>.tex`
- WHEN `render` runs for that id
- THEN it refuses `DIAGRAM_SOURCE_ABSENT` naming the id

### Requirement: Standalone Compile

`render` MUST invoke `latexmk -file-line-error -interaction=nonstopmode`
exactly once per call against the standalone `<id>.tex`, and MUST parse `!`
errors and `Overfull \hbox` warnings out of the log back to source lines.

#### Scenario: A clean compile produces the PDF

- GIVEN a syntactically valid `<id>.tex`
- WHEN `render` runs
- THEN exactly one `latexmk` invocation occurs and `<id>.pdf` is written

#### Scenario: An error is mapped to its source line

- GIVEN an `<id>.tex` with an undefined control sequence on a known line
- WHEN `render` runs and the compile fails
- THEN the refusal names that exact source line from the log

### Requirement: Toolchain Absence Refusal

`render` MUST refuse `LATEX_TOOLCHAIN_ABSENT`, naming the binary sought and
the searched `PATH`, when `latexmk` cannot be located. This MUST NOT degrade
to a skip or a silent pass.

#### Scenario: Empty PATH refuses by name

- GIVEN `PATH` contains no `latexmk`
- WHEN `render` runs
- THEN it refuses `LATEX_TOOLCHAIN_ABSENT` naming `latexmk` and the searched `PATH`

### Requirement: Package Absence Spends Nothing

A missing `.sty` reported by the log MUST refuse `LATEX_PACKAGE_ABSENT` naming
the package, and MUST NOT consume a repair-budget attempt — redrawing cannot
fix an absent package.

#### Scenario: Missing package refuses without spending budget

- GIVEN a log reporting a missing package and three attempts already spent
- WHEN `render` classifies the failure as package absence
- THEN it refuses `LATEX_PACKAGE_ABSENT` and the ledger's spent count is unchanged

### Requirement: Repair Budget Ledger

Each figure id MUST hold a repair ledger allowing four `latexmk` compiles;
editing the source between attempts MUST NOT reset the count. A fifth
attempt MUST refuse `REPAIR_BUDGET_SPENT`, naming every distinct diagnostic
and every source digest tried, cleared only by an explicit operator
acknowledgement.

#### Scenario: The budget survives edits between attempts

- GIVEN four failed compiles for one id, each preceded by a source edit
- WHEN a fifth compile is requested
- THEN it refuses `REPAIR_BUDGET_SPENT` naming all four diagnostics and digests

#### Scenario: Acknowledgement clears the ledger

- GIVEN a spent ledger for one id
- WHEN an operator issues the explicit acknowledgement
- THEN the id's ledger resets to zero and a new compile is accepted

### Requirement: Data-Figure Boundary

`render` MUST refuse `DIAGRAM_PLOTS_DATA` when the source loads a plotting
package, reads an external table, or embeds a coordinate series. Independently,
a compile MUST fail when no path from the source reaches any results tree.
Placing a measured figure MUST use a separate verb that compiles nothing and
requires provenance naming the run that produced it.

#### Scenario: A plotting package refuses before compiling

- GIVEN a diagram source that `\usepackage{pgfplots}`
- WHEN `render` runs
- THEN it refuses `DIAGRAM_PLOTS_DATA` naming the package, and no `latexmk` call occurs

#### Scenario: An unreachable results path fails independently

- GIVEN a source with no plotting package but a path construct pointing into a results tree
- WHEN `render` runs
- THEN the compile fails, distinct from `DIAGRAM_PLOTS_DATA`

### Requirement: No-Skip Test Evidence

The suite MUST run three tiers unconditionally: fixture-driven log parsing,
a stubbed `latexmk` on an injected `PATH` proving invocation shape, and an
emptied `PATH` proving the absence refusal. A genuine end-to-end compile MUST
report `unmeasured` where it did not run, never a pass.

#### Scenario: Every tier runs on a machine without TeX

- GIVEN a test machine with no `latexmk` installed
- WHEN the suite runs
- THEN all three tiers execute and none is skipped

#### Scenario: An unmeasured real compile never reads as a pass

- GIVEN no real `latexmk` distribution available in this environment
- WHEN the end-to-end scenario is evaluated
- THEN its result is `unmeasured`, not `ok`

### Requirement: Fixture Log Provenance

Committed `latexmk` log fixtures MUST be raw bytes captured from a real
compile, never hand-authored, so the parser cannot pass against a fixture
shaped by the same hand that wrote it.

#### Scenario: A fixture carries its capture provenance

- GIVEN a committed fixture log
- WHEN its provenance is inspected
- THEN it records the real `latexmk` invocation that produced it
### Requirement: Source Optimization

`figure optimize` MUST rewrite a diagram's TikZ source as a **candidate**, and
MUST commit it only after the two text guards and (by default) a compile have
accepted it. It MUST NOT remove a library it cannot prove unused, MUST NOT
delete a `% node:` marker under any flag, and MUST be idempotent: optimizing an
already-optimized source MUST produce byte-identical output.

#### Scenario: An unused library is pruned, a needed one is added

- GIVEN a source loading a library whose syntax does not appear, and using
  syntax that requires a library it does not load
- WHEN `figure optimize` runs
- THEN the first is removed, the second added, and both appear in `changes`

#### Scenario: A library the optimizer cannot recognize is kept

- GIVEN a source loading a library outside the detection map
- WHEN `figure optimize` runs
- THEN that library remains loaded

#### Scenario: Optimization is idempotent

- GIVEN any source
- WHEN `figure optimize` runs twice
- THEN the second run's text equals the first run's

#### Scenario: Markers survive every flag

- GIVEN a source carrying `% node: <label>` markers
- WHEN `figure optimize` runs, with and without `--strip-comments`
- THEN every marker is still present and the manifest cross-check still passes

#### Scenario: Repeated styles factor without moving anything

- GIVEN two sites with byte-identical option lists carrying no positional key
- WHEN `figure optimize` runs
- THEN one `\tikzset` style is introduced and both sites reference it

#### Scenario: A candidate that would fail stop A never reaches disk

- GIVEN a source whose candidate would declare a plotting construct
- WHEN `figure optimize` runs, including under `--no-compile`
- THEN it refuses `DIAGRAM_PLOTS_DATA` and the original is byte-identical

#### Scenario: A failing compile rolls back rather than refusing

- GIVEN a candidate that does not compile
- WHEN `figure optimize` runs
- THEN the call reports `verdict: "rolled_back"` with the diagnostics, exits 0,
  and the original is byte-identical

### Requirement: Honest Memory Guards

Static guards for runaway macro expansion MUST report as warnings in the
optimize report. No hard TeX memory limit may be claimed unless it has been
measured against the real toolchain; the guards MUST NOT imply one.

#### Scenario: A self-recursive macro is named

- GIVEN a source defining a macro that expands to itself
- WHEN `figure optimize` runs
- THEN the report names it as a warning

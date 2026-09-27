# Diagram Obligation Specification

## Purpose

What a diagram must contain is never known by this skill — it is read off the
per-block `figure:` declaration that `section-contract` carries, transcribed
from `sections/01`, `02`, and `05`. This spec pins the obligation vocabulary
and the three checks — components, separation, caption — plus the two-way
manifest crossing. No section id is ever named in code.

## Requirements

### Requirement: Obligations Read From Contract Front Matter

A block's diagram obligation MUST be read only from its `figure:` declaration
(`components_from` — optional — `ordered`, `excludes`, `caption_enumerates`,
`caption_decodes`, `mandatory`). No obligation MAY be hardcoded against a
section or block id.

#### Scenario: Deleting the declaration removes the obligation

- GIVEN a block whose `figure:` key is deleted from its contract
- WHEN obligation checks run for that block
- THEN no component, separation, or caption check runs for it, with zero code
  changed

### Requirement: Components Check

When `components_from` is declared, the diagram's declared component labels
MUST equal that fact's own currently-declared resolution — an ordered list of
strings, DERIVED at check time from `declare --fact <id> --value
'["a", "b"]'`'s own stored record, never supplied by the caller directly —
and, when `ordered: true`, the sequence MUST also match. A missing, extra, or
misordered component MUST refuse `COMPONENT_MISMATCH` naming the difference.
An undeclared or unresolved named fact MUST refuse `COMPONENTS_FACT_
UNRESOLVED`; a resolution that does not parse as a JSON array of strings MUST
refuse `COMPONENTS_FACT_NOT_A_LIST`. When `components_from` is absent, no
Components Check runs for that block at all — declared only for a block whose
diagram truly is one fact's own list by contract (`components_from`'s named
fact coincides with the FULL expected list only in that case; a block whose
diagram is a composite crossing over several categories of content, none of
which alone is the full list, declares no `components_from`, rather than
being wired to one fact's partial value and silently inverting the check).

#### Scenario: The methods diagram matches the contribution list

- GIVEN section 01's block declares `figure: {components_from: contributions,
  ordered: true}`, the `contributions` fact is declared as `["A", "B"]`, and
  the diagram's labels equal that list in order
- WHEN the components check runs
- THEN it passes with no refusal

#### Scenario: A dropped component refuses

- GIVEN the same block and declared fact, with one contribution's box removed
  from the diagram
- WHEN the components check runs
- THEN it refuses `COMPONENT_MISMATCH` naming the missing label

#### Scenario: An undeclared named fact refuses

- GIVEN a block declaring `figure: {components_from: contributions, ...}`
  whose `contributions` fact has never been declared
- WHEN the components check runs
- THEN it refuses `COMPONENTS_FACT_UNRESOLVED` naming the fact

#### Scenario: A block with no `components_from` runs no components check

- GIVEN section 02's `es-assessment` block, whose closing diagram is a
  composite crossing over several categories of content and whose contract
  declares no `components_from` at all
- WHEN obligation checks run for that block, against ANY manifest
- THEN no `COMPONENT_MISMATCH` can fire for it — the check simply does not
  run — while `check_excluded`/`check_caption`/`check_mandatory` and
  cross-diagram separation still do

### Requirement: Manifest Crossed With Source, Both Directions

Every label in `<id>.diagram.json` MUST exist as a node in `<id>.tex`, and
every node in `<id>.tex` MUST be declared in the manifest. A mismatch in
either direction MUST refuse `MANIFEST_SOURCE_MISMATCH` naming the label and
direction.

#### Scenario: An undeclared node refuses

- GIVEN a `.tex` node absent from the manifest
- WHEN the crossing check runs
- THEN it refuses `MANIFEST_SOURCE_MISMATCH` naming that node

### Requirement: Separation Check

Each diagram MUST exclude the element classes named in its own `excludes`,
and the component-label sets of any two diagrams MUST NOT intersect. Either
violation MUST refuse, naming the offending label and (for the second) both
diagram ids.

#### Scenario: A dataset in the methods diagram refuses

- GIVEN section 01's `figure.excludes` includes `dataset`, and the methods
  diagram carries a dataset box
- WHEN the separation check runs
- THEN it refuses `EXCLUDED_COMPONENT` naming `dataset`

#### Scenario: A label shared across two diagrams refuses

- GIVEN the same label appears in both the methods diagram and the
  experimental-setup diagram
- WHEN the cross-diagram separation check runs
- THEN it refuses `SHARED_COMPONENT` naming the label and both diagram ids

### Requirement: Caption Check

When `caption_enumerates: true`, every component MUST appear in the caption
in the diagram's order. When `caption_decodes: true`, every declared encoding
(for example, colour) MUST be decoded in the caption text. Either omission
MUST refuse `CAPTION_INCOMPLETE` naming what is missing.

#### Scenario: An undecoded encoding refuses

- GIVEN a diagram that encodes meaning by colour and a caption that never
  states what a colour means
- WHEN the caption check runs
- THEN it refuses `CAPTION_INCOMPLETE` naming the undecoded encoding

### Requirement: Mandatory Diagram Presence

When `mandatory: true` and the block carries no compiled diagram, the check
MUST refuse `MANDATORY_DIAGRAM_ABSENT` naming the block.

#### Scenario: A mandatory diagram missing refuses

- GIVEN section 01's closing block declares `mandatory: true` with no
  `<id>.pdf` produced
- WHEN obligation checks run
- THEN it refuses `MANDATORY_DIAGRAM_ABSENT` naming the block

### Requirement: Conditional Synthesis Artefact

When a block's contract states the synthesis artefact may be a diagram or a
table (section 05), no diagram obligation applies unless the operator's
declared artefact choice for that block is a diagram.

#### Scenario: A table choice carries no diagram obligation

- GIVEN section 05's block 5 declares the synthesis artefact as a table
- WHEN obligation checks run
- THEN no component, separation, or caption check runs for that block
### Requirement: Figure-Prose Semantic Audit

A diagram's manifest `components` MUST be checked against the prose of the
section that describes it, and the `components_from` fact's resolved list MUST
be checked against both the manifest and that prose. The audit's subject is the
**manifest**, never every `\node{}` string. Its verdict MUST be one of
`pass` | `fail` | `unmeasured`, and a warning MUST NOT change the verdict.

The returned report MUST also carry a `visual` key. `visual` MUST be supplied
by the caller as an already-computed plain-data argument — never resolved by
this function reading disk or spawning a process — the same way
`expected_components` is already supplied. `visual` MUST never be absent or
`null`; when no caller-supplied value is given, it MUST default to every
classified visual dimension present with `{"verdict": "unmeasured", "reason":
"<code>"}`. No value inside `visual` MAY change this requirement's own
semantic `verdict`.

(Previously: the returned report carried no `visual` key at all, and nothing
in `audit_semantics`'s signature or return shape accounted for a visual
finding.)

#### Scenario: A phantom component fails

- GIVEN a manifest component the section prose never names
- WHEN the audit runs
- THEN `verdict` is `fail` and the component is named in `unmatched_nodes`

#### Scenario: A missing pipeline stage fails

- GIVEN a `components_from` fact whose list names a step absent from both the
  manifest and the prose
- WHEN the audit runs
- THEN the step is named in `missing_pipeline_steps`

#### Scenario: A clean pair passes with every list empty

- GIVEN a figure, manifest, contract and prose that agree
- WHEN the audit runs
- THEN `verdict` is `pass` with empty `unmatched_nodes`,
  `missing_pipeline_steps` and `label_mismatches`

#### Scenario: Acronym drift warns rather than fails

- GIVEN a component whose only content is an acronym the prose spells out
- WHEN the audit runs
- THEN the token is named in `label_mismatches` and in `warnings`, and the
  verdict is not `fail`

#### Scenario: An uncheckable pair is unmeasured, never pass

- GIVEN a contract declaring no `components_from`, or a manifest declaring no
  components, or a components fact that does not resolve
- WHEN the audit runs
- THEN the verdict is `unmeasured` naming its reason, never `pass`

#### Scenario: One absent input does not unmeasure a comparison that ran

- GIVEN a call with no block bound, and a manifest and prose that CAN be
  compared to each other
- WHEN the audit runs
- THEN the pipeline-step half reports `CONTRACT_FIGURE_ABSENT` as its own
  reason, and the component comparison keeps the verdict it reached

The two halves are separated on purpose. `unmeasured` exists to stop a verdict
being claimed where nothing was measured; applying it to a comparison that DID
run, because a different comparison lacked an input, is that rule read
backwards — it would hide a real measurement behind another's gap. So each
half carries its own reason and neither poisons the other.

#### Scenario: A content finding is not a CLI refusal

- GIVEN a manifest naming a component the contract excludes
- WHEN `figure audit` runs
- THEN the call exits 0 with `status: ok` and `verdict: fail`, and the refusal
  code appears as a finding rather than as the process exit

#### Scenario: The report always carries a visual key

- GIVEN a call to `audit_semantics` with no `visual` argument supplied
- WHEN the report is assembled
- THEN it carries a `visual` key with every classified dimension present as
  `{"verdict": "unmeasured", "reason": "<code>"}`, never an absent key and
  never `null`

#### Scenario: A visual failure alongside a semantic pass leaves the top-level verdict at pass

- GIVEN a caller-supplied `visual` argument reporting `overlap` as `fail`, and
  a manifest, contract and prose that otherwise agree
- WHEN the audit runs
- THEN the top-level `verdict` is `pass`, and `visual.overlap.verdict`
  independently reads `fail` in the same report

### Requirement: The Audit Is Read Without Its Module

`verify`'s `figure-semantics` check MUST read only an already-computed report
dict on the evidence object. `paper_verify.py`'s import allowlist MUST NOT be
widened to admit the auditor or a JSON parser, and no `Path`-typed evidence
field may be read by a check.

This requirement extends unchanged to the report's `visual` key: `verify`'s
`figure-semantics` check MUST read any visual finding it surfaces from the
same already-computed dict, through the same evidence object, with no second
import path and no `Path`-typed field introduced to carry it.

(Previously: this requirement said nothing about the `visual` key, because the
report had none.)

#### Scenario: No figure declares nothing rather than passing

- GIVEN a paper with no diagram at all
- WHEN `verify` runs
- THEN `figure-semantics` reports `unmeasured`, reason `NO_FIGURE_DECLARED`

#### Scenario: A visual finding reaches verify through the existing dict, not a new import

- GIVEN a report dict whose `visual` key carries a computed `out-of-bounds`
  finding
- WHEN `verify`'s `figure-semantics` check reads that report
- THEN it reads `visual` from the same already-computed dict on the evidence
  object, and `paper_verify.py`'s import allowlist is unchanged

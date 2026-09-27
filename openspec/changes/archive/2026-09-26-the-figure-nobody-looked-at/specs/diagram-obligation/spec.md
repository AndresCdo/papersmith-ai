# Delta for Diagram Obligation

## MODIFIED Requirements

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

# implementation-product-shipped Specification

## Purpose

A `step` invocation already reports whether the paths it wrote lie inside or
outside the roots it declared under `produces` (`wrote.status` /
`wrote.inside` / `wrote.outside`). That reading answers "did this step write
where it says it writes", never "did any of that writing actually reach the
repository's history". A path can be inside a step's own declared root,
entirely legitimate by every check that runs today, and still be a path the
repository has been told, in `.gitignore`, never to ship. The declaration
reads satisfied, the run reports `outcome: "returned"`, and the artifact the
step was told to produce is absent from history — discoverable today only by
someone going looking for a file that was never committed.

This capability closes that gap: it cross-checks the paths a step's run
**actually wrote** inside its own declared roots against the repository's own
ignore rules, and reports the result on the same run, in the same durable
record that already carries `wrote`. It changes no refusal, no `status`
value, and no scope outside what a step already owns.

## Requirements

### Requirement: The Check Is Computed Over Actually-Written Paths, Never Over Declared Roots

The ignored-path check MUST be computed over the concrete paths a run
actually wrote or removed inside its declared roots (`wrote.inside`), never
over the bare declared root strings themselves. Checking a bare declared root
against a content-only ignore rule produces a false "not ignored" answer for
every real path underneath it, because a rule such as `Results/*` matches
files under `Results/own` without matching the literal string `Results/own`.

#### Scenario: A real written path under a content-only ignore rule is caught
- GIVEN a step declares root `Results/own`
- AND the repository's ignore rules exclude `Results/own/*` by content
  pattern, not by naming the bare root
- AND the run writes `Results/own/a.json`
- WHEN the ignored-path check runs
- THEN it reports `Results/own/a.json` as ignored
- AND a check that asked only about the bare declared root `Results/own`
  would have missed it

#### Scenario: Checking the bare declared root would be insufficient
- GIVEN the same step and the same content-only ignore rule
- WHEN the bare declared root string `Results/own` alone is evaluated against
  the ignore rules, instead of the actual written path
- THEN that evaluation reports "not ignored", even though every real file
  written under that root is ignored

### Requirement: The Path Base Passed To The Ignore Check Is Repository-Relative

The paths a run wrote are recorded product-relative (relative to the product
folder, e.g. `Results/own/a.json`), while the repository's ignore rules are
evaluated relative to the repository root. Before any written path is checked
against the ignore rules, the product name MUST be joined onto it so the
check evaluates the exact path the repository itself would evaluate (e.g.
`Method/Results/own/a.json` for a product named `Method`).

#### Scenario: A product-anchored ignore rule matches the joined path
- GIVEN a step named `Method` declares root `Results/own`
- AND the repository's ignore rules exclude `/Method/Results/own/` by a rule
  anchored to the product folder, not to the bare `Results/own/` shape
- AND the run writes `Results/own/a.json`
- WHEN the ignored-path check runs
- THEN it reports `Results/own/a.json` as ignored
- AND this scenario is only satisfiable if the product name was joined onto
  the path before the check ran — a check that evaluated the unjoined,
  product-relative path against the repository's ignore rules would report
  "not ignored" for a rule anchored this way

#### Scenario: A product-relative-only fixture cannot stand in for this scenario
- GIVEN an ignore rule written as the bare, unanchored shape `Results/own/`
- WHEN that rule is evaluated against both the joined path
  (`Method/Results/own/a.json`) and the unjoined path (`Results/own/a.json`)
- THEN both evaluations report "ignored", because an unanchored rule matches
  at any depth
- AND this pair — anchored rule required to distinguish the joined case from
  the unjoined case — is why an unanchored fixture rule MUST NOT be used to
  prove this requirement

### Requirement: A Clean, Tracked Write Reports An Empty Result And Never Raises

A non-zero exit from the underlying ignore-rule check that carries no output
MUST be read as "nothing is ignored", never as an error. A step whose written,
declared, and tracked product is queried against the repository's ignore
rules MUST report an empty ignored-paths result and MUST NOT raise.

#### Scenario: A tracked product reports empty and does not raise
- GIVEN a step declares root `Results/own`
- AND the run writes `Results/own/a.json`
- AND the repository does not ignore that path (it is tracked, or is
  trackable and not excluded by any rule)
- WHEN the ignored-path check runs
- THEN it completes without raising
- AND it reports an empty set of ignored paths

### Requirement: The Result Is A Parallel Field On `wrote`, Never A Fifth `status` Value

The ignored-path reading MUST be exposed as a field alongside the existing
`inside` and `outside` fields on the `wrote` result, never as a new value of
`wrote.status`. A run can be simultaneously `status: "own"` (every written
path lies under a declared root) and carry one or more ignored paths — these
are answers to two independent questions, and collapsing them into a single
enumerated value would make it impossible to express both facts about the
same run at once.

#### Scenario: An own run with an ignored path still reads `status: "own"`
- GIVEN a step declares root `Results/own`
- AND the run writes `Results/own/a.json` inside that root
- AND `Results/own/a.json` is ignored by the repository
- WHEN the run's `wrote` result is inspected
- THEN `wrote.status` still reads `"own"`
- AND the ignored-paths field lists `Results/own/a.json`

#### Scenario: An own run with no ignored paths reports the field empty, not absent
- GIVEN the same step declares root `Results/own`
- AND the run writes `Results/own/a.json`, which the repository tracks
- WHEN the run's `wrote` result is inspected
- THEN `wrote.status` reads `"own"`
- AND the ignored-paths field is present and empty

### Requirement: The Check Never Refuses, Regardless Of What It Finds

Finding one or more ignored paths among a step's own written, declared
product MUST NOT raise a refusal, halt the run, or alter `outcome`,
`exitStatus`, or `wrote.status`. The subprocess has already run and the
product is already on disk by the time this reading is computed; a refusal
at that point would discard the run's own verdict rather than add a fact to
it.

#### Scenario: A run with an ignored product still returns normally
- GIVEN a step declares root `Results/own`
- AND the run writes `Results/own/a.json`, which the repository ignores
- WHEN the step is invoked
- THEN it returns with the same `outcome` and `exitStatus` it would have
  returned had the path not been ignored
- AND no refusal is raised because of the ignored path

### Requirement: The Reading Is Durable — Written Into The Terminal Ledger Event, Not Only Returned

The ignored-paths field MUST appear in the same durable, append-only ledger
event that already carries the rest of `wrote` for that run (the terminal
`step` event), not only in the value returned to the immediate caller. A
reading that exists only in one process's return value or stdout is the same
gap this capability exists to close, one level removed.

#### Scenario: The ignored-paths field is present in the terminal ledger event
- GIVEN a step declares root `Results/own`
- AND the run writes `Results/own/a.json`, which the repository ignores
- WHEN the step's terminal ledger event is read back after the run
- THEN that event's `wrote` object carries the ignored-paths field
- AND it lists `Results/own/a.json`

### Requirement: Scope Is Limited To A Step's Own Declared-And-Written Paths (`inside`)

The ignored-path check MUST be computed only over `wrote.inside` — paths the
run wrote under its own declared roots. It MUST NOT be computed over
`wrote.outside` (paths a step wrote outside its declared roots). A foreign
write is already the strongest reading this skill gives for that half of the
result; this capability adds no further reading there.

#### Scenario: A foreign write is not evaluated for ignored status
- GIVEN a step declares root `Results/own`
- AND the run writes `Results/neighbour/b.json`, outside that declared root
- AND `Results/neighbour/b.json` is ignored by the repository
- WHEN the run's `wrote` result is inspected
- THEN `wrote.status` reads `"foreign"` and `wrote.outside` names
  `Results/neighbour/b.json`, exactly as before this capability
- AND the ignored-paths field does not evaluate or name any path from
  `wrote.outside`

### Requirement: Removed Paths Are Included, Not Only Added Or Modified Paths

A path a run removed under its declared roots MUST be included in the set of
paths checked against the repository's ignore rules, exactly as an added or
modified path is. The underlying ignore-rule check answers about path
patterns, not about whether a file currently exists on disk, so a removed
path still receives a real answer and MUST NOT be silently dropped by an
existence guard.

#### Scenario: A removed path under a declared root is still checked
- GIVEN a step declares root `Results/own`
- AND a prior run left `Results/own/old.json` in place
- AND a later run under the same declared root deletes `Results/own/old.json`
- AND `Results/own/old.json` is ignored by the repository
- WHEN the ignored-path check runs for the later run
- THEN it reports `Results/own/old.json` as ignored, even though the file no
  longer exists on disk

### Requirement: The Consequence Text Is A Single Named Constant, Asserted By Identity

The prose explaining what a reported ignored path means MUST be defined once,
as a single named constant, in the same location and style as the sibling
consequence constants this capability sits beside. Any test asserting this
requirement MUST assert identity against that constant, never merely that a
consequence-shaped string, or the ignored-paths field itself, is present.

#### Scenario: The consequence text is asserted by identity
- GIVEN a run with one or more ignored paths
- WHEN the run's `wrote` result (or its ledger event, before the `note` field
  is stripped for the ledger) is inspected for consequence text
- THEN the text is identical, by identity, to the single named constant that
  defines it
- AND replacing that constant's text with an empty string is detectable by
  the same assertion, not merely by checking that some field is non-empty

### Requirement: The Documented Sub-Key Enumeration Names The New Field

The published enumeration of `wrote`'s sub-keys (the documentation a reader
consults to learn what a `step` invocation's `wrote` result contains) MUST
name the new ignored-paths field alongside `status`, `declared`, `inside`,
and `outside`, in the same place that enumeration already lives.

#### Scenario: The documented enumeration lists the new field
- GIVEN the published enumeration of `wrote`'s sub-keys
- WHEN it is read after this capability ships
- THEN it names the ignored-paths field, its meaning, and that it is computed
  over `inside` only, alongside the existing sub-keys

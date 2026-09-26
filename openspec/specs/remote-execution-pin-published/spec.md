# Remote Execution — Pin-Published Refusal Specification

## Purpose

This capability governs what the `pin-published` pin condition tells the operator when it
refuses generation or submission because the declared `--repo-url` could not be confirmed to
hold the pinned commit. It does not change when the refusal fires, and it never pushes, fetches,
stages, commits, or otherwise mutates the operator's repository or the declared remote. Its only
job is to say, honestly and without inventing precision, how much unpushed work the recommended
push would carry — when that can be known from state already on disk, and nothing invented when
it cannot.

This is the first capability spec written for the `remote-execution` skill in this repository;
no prior `openspec/specs/` entry exists for it. This spec covers only the `pin-published`
condition's refusal wording and its local weight measurement. It does not cover the other four
pin conditions, the reachability probe's network behavior itself, or any other refusal in
`jobfolder.py`.

## Requirements

### Requirement: Weight measurement is attempted only from the catch-all refusal path

The system MUST attempt a local weight measurement only when the `pin-published` condition is
about to refuse through its catch-all branch (the branch already handling every failure other
than a probe timeout). The system MUST NOT attempt the weight measurement, and MUST NOT let it
influence, the branch that refuses because the reachability probe itself timed out.

#### Scenario: Catch-all refusal attempts the measurement

- GIVEN the declared remote answers the reachability probe with a confirmed refusal (for
  example, "not our ref") or the probe cannot be run at all for a reason other than a timeout
- WHEN the `pin-published` condition refuses generation or submission
- THEN the system attempts the local weight measurement before composing the refusal message

#### Scenario: Timeout refusal never attempts the measurement

- GIVEN the reachability probe expires its own timeout budget before finishing
- WHEN the `pin-published` condition refuses generation or submission
- THEN the refusal is produced exactly as before this change, with no weight measurement
  attempted and no remedy named

### Requirement: The weight reader makes no network call

The local weight measurement MUST NOT open a network connection, MUST NOT invoke `git fetch`,
`git ls-remote`, or any other operation that contacts a remote host, and MUST NOT transfer any
object bytes to or from a remote.

#### Scenario: Measurement transfers no bytes

- GIVEN a local repository with a remote-tracking ref that differs from the pinned commit
- WHEN the weight measurement runs as part of a `pin-published` refusal
- THEN no outbound network connection is opened and no object data is transferred, asserted
  directly rather than assumed from the absence of a crash

### Requirement: The refusal takes exactly one of two shapes, chosen only by measurability

When the `pin-published` condition refuses through its catch-all branch, the refusal MUST take
exactly one of two shapes. The choice between them MUST depend only on whether the local weight
measurement succeeded, and MUST NOT depend on the size of the measured weight, the type of the
underlying failure, or any other factor.

- **Measured**: the refusal states the measured weight, as an exact cache-relative count, and
  names the existing remedy (push the commit to the declared ref on the declared remote, then
  pin the commit the remote actually received).
- **Unmeasurable**: the refusal states what is known — the remote's own refusal or failure,
  carried forward as today — and prescribes no remedy.

#### Scenario: Measured weight still gets the remedy, regardless of magnitude

- GIVEN a local repository whose remote-tracking ref for the declared `--repo-url` is behind the
  pinned commit by a small number of commits/bytes
- WHEN the `pin-published` condition refuses
- THEN the refusal names the measured weight as an exact cache-relative count and names the
  push-and-pin remedy

#### Scenario: A large measured weight still gets the remedy, not a different message shape

- GIVEN a local repository whose remote-tracking ref for the declared `--repo-url` is behind the
  pinned commit by a large number of commits/bytes
- WHEN the `pin-published` condition refuses
- THEN the refusal names the measured weight as an exact cache-relative count and names the
  push-and-pin remedy, using the same message shape as the small-weight scenario above

#### Scenario: No matching local remote yields the unmeasurable shape

- GIVEN a local repository with no remote configuration that resolves to an anchor for the
  declared `--repo-url` (for example, a repository with no configured remote at all)
- WHEN the `pin-published` condition refuses
- THEN the refusal states what is known and prescribes no remedy, and never states a weight

### Requirement: A measured weight states an exact distance from the cache, and claims nothing about the remote now

When the weight is measurable, the refusal MUST state the exact commit count between the
cached anchor and the pinned commit. It MUST NOT phrase that count as a lower bound (for
example, "at least N commits") or as an upper bound (for example, "no more than N commits to
push"), and MUST NOT claim or imply anything about the remote's current state — only about the
distance from the state this clone's cache recorded for the declared remote.

#### Scenario: Exact cache-relative count, no floor or ceiling claim

- GIVEN a measurable weight of any magnitude
- WHEN the refusal states that weight
- THEN the stated sentence names the exact commit count between the cached anchor and the
  pinned commit, uses neither floor language ("at least") nor ceiling language ("no more
  than"), and makes no claim about the remote's state now

### Requirement: The anchor is selected by strict, exact string comparison against `--repo-url`

The system MUST anchor the local weight measurement on a local remote-tracking ref
(`refs/remotes/<name>/<branch>`) only when that ref's configured remote URL is an exact string
match of the declared `--repo-url`. Any non-exact match — a different scheme, a trailing
`.git`, an SSH form naming the same host and path as an HTTPS form, or any other spelling
difference — MUST be treated identically to no match at all, and MUST resolve to the
unmeasurable outcome. The system MUST NOT normalize, canonicalize, or fuzzy-match URLs when
selecting the anchor.

#### Scenario: Exact match resolves to a measured anchor

- GIVEN a local remote whose configured URL is byte-for-byte identical to the declared
  `--repo-url`, with a remote-tracking ref that differs from the pinned commit
- WHEN the `pin-published` condition attempts the weight measurement
- THEN the measurement succeeds and anchors on that remote-tracking ref

#### Scenario: A differently spelled remote is treated as no match

- GIVEN a local remote configured with a URL that is semantically equivalent to but not
  byte-identical with the declared `--repo-url` (for example, missing or carrying a `.git`
  suffix the declared URL lacks or has, or an SSH form where an HTTPS URL was declared)
- WHEN the `pin-published` condition attempts the weight measurement
- THEN the measurement resolves to unmeasurable, even though a local remote referring to what a
  human would call "the same repository" exists

#### Scenario: No configured remote at all

- GIVEN a local repository with no configured remotes
- WHEN the `pin-published` condition attempts the weight measurement
- THEN the measurement resolves to unmeasurable

### Requirement: The stated weight is documented as a cache, not the remote's current state

Wherever the measured weight is presented to the operator — in the refusal message and in
`SKILL.md`'s reachability-probe section — the wording MUST make clear that the anchor is a
local record of the remote's state as of the last fetch, and that the remote's actual current
state may differ. The wording MUST NOT imply a specific direction or magnitude of drift between
the cache and the remote's current state, and MUST NOT license any conclusion about how much
(if anything) remains to be pushed.

#### Scenario: SKILL.md states the cache caveat

- GIVEN the reachability-probe section of `SKILL.md`
- WHEN it documents the measured refusal shape
- THEN it states that the reported weight is an exact count derived from a local cache of the
  last fetch, not a live read of the remote, and makes no claim about the remote's state now

### Requirement: The weight reader fails silent

Any failure internal to the local weight measurement (a missing or unreadable local ref, a
git invocation failure, a repository in an unexpected state, or any other internal error) MUST
resolve to the unmeasurable outcome. It MUST NOT propagate as a `JobFolderError` distinguishable
from the one refusal shape the catch-all branch already raises, and MUST NOT introduce a new,
separate refusal path or exit condition.

#### Scenario: An internal measurement failure degrades to unmeasurable, not to a crash or a new refusal

- GIVEN a repository state in which every local primitive the weight reader depends on fails
- WHEN the `pin-published` condition refuses through its catch-all branch
- THEN the refusal produced is the careful, unmeasurable shape — not an unhandled exception and
  not a refusal with different wording, exit behavior, or condition identity than the existing
  `pin-published` refusal

### Requirement: The `GitTimeoutError` refusal remains unchanged

The refusal raised when the reachability probe itself expires its timeout budget MUST continue
to name no remedy at all, and MUST remain textually identical to its wording before this change.

#### Scenario: Timeout wording is byte-unchanged

- GIVEN the reachability probe times out before finishing
- WHEN the `pin-published` condition refuses
- THEN the refusal text is identical to the pre-change timeout refusal, naming no remedy and no
  weight

### Requirement: The existing refusal prefix is preserved verbatim; new material is appended only

Every refusal produced by the catch-all branch MUST continue to begin with the exact substring
`"could not be confirmed reachable"`. Any new weight or measurability language introduced by
this change MUST be appended after the existing message content and MUST NOT be spliced ahead
of it or interleaved within it.

#### Scenario: Prefix substring still present, unmodified, in both shapes

- GIVEN either the measured or the unmeasurable refusal shape
- WHEN the refusal message is composed
- THEN it contains the exact substring `"could not be confirmed reachable"` at the same position
  relative to the message start as before this change

### Requirement: The `pin-published` condition is identified only by its declared id

Any new prose this change introduces — in refusal messages, in `SKILL.md`, or in tests — that
refers to this condition MUST refer to it by its backtick id `` `pin-published` ``. It MUST NOT
refer to the condition by its position among the pin conditions, and MUST NOT state or imply how
many pin conditions exist in total.

#### Scenario: New prose names the condition by id

- GIVEN any new sentence introduced by this change that refers to the pin-published condition
- WHEN that sentence is read
- THEN it names the condition as `` `pin-published` `` and never by ordinal position or by a
  count of the total conditions

### Requirement: No new pin condition is introduced

This change MUST NOT add, remove, or reorder the set of pin conditions evaluated before
generation or submission. The conditions continue to run in their existing order, unchanged in
number.

#### Scenario: The condition set is unchanged

- GIVEN the pin conditions evaluated before generation or submission, before and after this
  change
- WHEN they are compared
- THEN the set, its membership, and its evaluation order are identical

### Requirement: The weight reader's timeout is its own distinct, measured budget

The local weight measurement MUST be bounded by a timeout value held in its own module
constant. That constant MUST be distinct from the constant bounding ordinary local git
operations and distinct from the constant bounding the network reachability probe. The comment
documenting the constant MUST state the measurement it was derived from. A timeout value not
backed by a stated measurement MUST NOT be introduced.

#### Scenario: A separate, documented constant exists

- GIVEN the module that implements the weight reader
- WHEN its timeout budget is inspected
- THEN it is a distinct constant from the ones bounding ordinary local git calls and the network
  reachability probe, and its comment states the measurement behind the chosen value

#### Scenario: Only the weight reader's call receives this budget

- GIVEN the module's git invocations
- WHEN the calls the weight reader makes are compared against every other local, purely-local
  git call in the module
- THEN only the weight reader's own call is bound by the new constant

### Requirement: `SKILL.md` documents both refusal shapes

The reachability-probe section of `SKILL.md` MUST describe both refusal shapes — measured and
unmeasurable — plainly enough that an operator reading it before running the tool understands
that a stated weight is an exact count derived from the local cache, with no claim about the
remote's state now, and that no weight is stated when it cannot be measured.

#### Scenario: Both shapes are documented

- GIVEN the reachability-probe section of `SKILL.md`
- WHEN an operator reads it before hitting a `pin-published` refusal
- THEN it describes both the measured (weight-plus-remedy) and unmeasurable (no-remedy) refusal
  shapes and states that the measured weight is an exact count derived from the local cache,
  with no claim about the remote's state now

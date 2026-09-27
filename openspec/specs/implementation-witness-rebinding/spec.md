# Implementation Witness Rebinding Specification

## Purpose

This capability governs `settle --attach --replace`: the instrument that lets an operator move
an agreement checklist line's `` `test_<id>` `` witness token onto a different test, without
touching the claim's tick and without touching anything else in the holder file
(`AGREED.md`). Re-pointing a proof is not retracting a claim — the agreement's truth did not
change, only the artifact that demonstrates it — and this capability exists because the only
path that reached the end state before it, `--reverse` followed by a fresh placement, achieves
that by de-ticking and un-witnessing a line that was already measured and closed.

This is the first spec for `settle`'s mode vocabulary; no prior `openspec/specs/` entry names
`cmd_settle`. This spec covers only the `--replace` modifier on `--attach`: what it writes, what
it records, what it refuses, and the two properties it must not touch (the mark, and the gating
surface). It does not cover `--attach`'s other refusals, `--remove`, `--reverse`, `--done`, or
plain `settle`'s placement path, except where `--replace` changes one of their outcomes.

## Out of Scope

- **What `close` or `gate` refuse on.** `AGREEMENT_DISAGREES` continues to fire in exactly the
  one place it fires today; the set of gating commands is untouched by this capability.
- **Un-ticking.** A checklist line's mark can be set by re-pointing (see below) but this
  capability never clears a mark; that stays deliberately absent.
- **Any edit a forge makes to a target's agreements on its own judgement.** This capability is an
  operator instrument; it never decides, on its own, that a witness should be re-pointed.
- **Witness measurement.** The system MUST NOT check whether the incoming witness names a test
  that exists in `tests/`, or whether it passes. `verify` reports on that; `close` gates on it;
  `settle` never has, and this capability does not change that.
- **Repairing any specific target's stale witness.** Applying this capability to a particular
  `AGREED.md` line is a use of the capability, performed by an operator, and belongs to that
  target's own work — not to this capability's scope.

## Requirements

### Requirement: Replacing an Existing Witness Leaves the Mark and the Rest of the Holder Untouched

When `--attach --replace` locates a checklist line that already carries a `` `test_<id>` ``
witness token, the system MUST splice only that token for the new one it was given. The line's
tick state (`[x]` or `[ ]`), the line's claim text, and every other byte of the holder file MUST
be identical before and after the write.

#### Scenario: A ticked, witnessed line is re-pointed

- GIVEN a checklist line marked `[x]` whose text carries witness token `test_a`
- WHEN the operator runs `settle --attach --witness test_b --replace --text <that exact line>`
- THEN the line's witness reads `test_b`
- AND the line remains marked `[x]`
- AND every other byte of the holder file is identical to before the call

#### Scenario: An unticked, witnessed line is re-pointed and stays unticked

- GIVEN a checklist line marked `[ ]` whose text carries witness token `test_a`
- WHEN the operator runs `settle --attach --witness test_b --replace --text <that exact line>`
- THEN the line's witness reads `test_b`
- AND the line remains marked `[ ]`
- AND every other byte of the holder file is identical to before the call

### Requirement: Re-Pointing Is Mark-Blind

The system MUST NOT condition `--replace`'s success on the located line's tick state.
`--attach` already binds a witness onto a line "ticked or not"; `--replace` inherits that rule
rather than restating or narrowing it. A witness bound before its claim comes true is a normal
state in a target's `AGREED.md`, and refusing to correct one on an open line would leave stale
witnesses exactly on the lines nobody is currently gating on — the ones whose staleness would
otherwise surface only later, as a surprise at `close`.

#### Scenario: Tick state is never inspected to decide the refusal

- GIVEN two otherwise-identical witnessed checklist lines, one `[x]` and one `[ ]`
- WHEN each is re-pointed with `settle --attach --witness <new> --replace --text <line>`
- THEN both calls succeed identically, and neither call's outcome differs because of the mark

### Requirement: `--replace` Is Only Valid Alongside `--attach`

The system MUST refuse `` `SETTLE_REPLACE_CONFLICT` `` when `--replace` is given without
`--attach`. This mirrors the existing `` `SETTLE_ATTACH_CONFLICT` ``, `` `SETTLE_REMOVE_CONFLICT` ``
and `` `POSITION_REPAIR_CONFLICT` `` shape: a modifier flag names the mode it belongs to when
given without it.

#### Scenario: `--replace` without `--attach` is refused

- GIVEN a `settle` invocation carrying `--replace` but not `--attach`
- WHEN the command is evaluated
- THEN it refuses `` `SETTLE_REPLACE_CONFLICT` ``, and no write is made to the holder file

### Requirement: `--replace` Requires an Existing Witness to Replace

The system MUST refuse `` `SETTLE_NOTHING_TO_REPLACE` `` when `--attach --replace` locates a
checklist line that carries no witness token at all. This MUST NOT silently degrade to a plain
`--attach` (create) on that line. The caller asked to replace a binding; if none exists, the call
believed something was true that was not, and treating that as success would hide the mismatch
rather than surface it. The refusal's detail MUST name the located line and state that plain
`--attach` (without `--replace`) is the create path for a line with no witness.

#### Scenario: `--replace` on an unwitnessed line is refused, not silently accepted

- GIVEN a checklist line whose text carries no `` `test_<id>` `` token
- WHEN the operator runs `settle --attach --witness test_b --replace --text <that exact line>`
- THEN the command refuses `` `SETTLE_NOTHING_TO_REPLACE` ``
- AND no witness is written to that line
- AND the refusal's detail names the located line and states that `--attach` alone (without
  `--replace`) is the path to bind a first witness

### Requirement: A No-Op Replacement Is Refused, Not Silently Written

The system MUST refuse `` `SETTLE_WITNESS_UNCHANGED` `` when the incoming `--witness` token is
identical to the token already on the located line. **This is a decision made for this spec, not
an inheritance from settled doctrine**: the proposal for this capability flagged this refusal as
recommended but not load-bearing, leaving it open whether a same-token call should refuse or
silently succeed as a no-op. This spec decides it refuses, for the same reason
`` `SETTLE_NOTHING_TO_REPLACE` `` refuses rather than degrades: the ledger event this capability
adds records `replacedWitness`, and a write that appends a `replacedWitness` event for a splice
that changed nothing would be the one `settle` write whose own ledger entry claims a change that
did not happen. Refusing keeps every `replacedWitness` event honest evidence of an actual change.

#### Scenario: Replacing a witness with itself is refused

- GIVEN a checklist line whose text carries witness token `test_a`
- WHEN the operator runs `settle --attach --witness test_a --replace --text <that exact line>`
- THEN the command refuses `` `SETTLE_WITNESS_UNCHANGED` ``
- AND no ledger event is appended, and the holder file is unchanged

### Requirement: `SETTLE_ALREADY_WITNESSED` Still Fires Without `--replace`, and Now Names Its Exit

Without `--replace`, `--attach` on an already-witnessed line MUST continue to refuse
`` `SETTLE_ALREADY_WITNESSED` `` exactly as before this capability — this is a regression
surface, and the refusal's firing condition MUST NOT change. What changes is only the refusal's
detail text: it MUST now name `--replace` as the exit available to the operator, closing the gap
where every other `settle` refusal names a next step and this one, until now, named none.

#### Scenario: The refusal still fires under the same condition

- GIVEN a checklist line that already carries a witness
- WHEN the operator runs `settle --attach --witness <new>` without `--replace`
- THEN the command refuses `` `SETTLE_ALREADY_WITNESSED` ``, identically to before this
  capability existed

#### Scenario: The refusal's detail names the exit

- GIVEN the same refusal as above
- WHEN its detail text is read
- THEN it names `--replace` as what the operator can add to proceed

### Requirement: The Previous Witness Is Recorded as Evidence

A successful replacement MUST record the displaced token, not only the new one. The `kind:
"settle"` ledger event MUST gain a `replace` boolean and, on a successful replacement, a
`replacedWitness` field naming the token that was there before the splice. The command's response
MUST mirror both fields. The previous witness is evidence — it names what someone previously
believed proved the claim — and a replacement that recorded only the incoming token would be the
only `settle` write whose own event cannot answer what was there before.

#### Scenario: The ledger event and the response both name the displaced token

- GIVEN a checklist line whose text carries witness token `test_a`
- WHEN the operator successfully runs
  `settle --attach --witness test_b --replace --text <that exact line>`
- THEN the appended `kind: "settle"` ledger event carries `replace: true` and
  `replacedWitness: "test_a"`
- AND the command's response also carries `replace: true` and `replacedWitness: "test_a"`

#### Scenario: `replace` is present on every settle response, mirroring the other mode flags

- GIVEN any `settle` invocation, regardless of mode
- WHEN its response is inspected
- THEN it carries a `replace` boolean, present the same way the existing `attach`, `remove`,
  `reverse` and `done` flags are always present

### Requirement: Re-Pointing Performs No Test-Suite Measurement

The system MUST NOT read `tests/`, parse test definitions, or otherwise check whether the
incoming or the displaced witness names a test that exists, when evaluating or executing
`--replace`. Gating on whether a witness is backed by a real test is `verify`'s and `close`'s job,
reached only through `agreements_state()`; `settle` writing a second, independent check of the
same fact would create a second gate, which is the doctrine this capability is written not to
disturb.

#### Scenario: Replacement succeeds even when the new witness names no real test

- GIVEN a checklist line witnessed by `test_a`
- WHEN the operator runs `settle --attach --witness test_does_not_exist --replace --text <line>`
- THEN the replacement succeeds, writing `test_does_not_exist` as the line's witness
- AND no read of `tests/` occurs as part of evaluating or executing this call

### Requirement: The Gating Surface Is Unchanged

`agreements_state()` MUST continue to be reached from exactly the same call sites it is reached
from today, and from nowhere new. This capability MUST NOT add a call site in `cmd_gate`,
`cmd_probe`, `cmd_offer`, or `cmd_step`. `close` remains the only command that refuses on the
witness axis.

#### Scenario: No new command gates on the witness axis

- GIVEN the full set of commands that call `agreements_state()` before and after this capability
  ships
- WHEN the two sets are compared
- THEN they are identical, and `cmd_gate`, `cmd_probe`, `cmd_offer` and `cmd_step` are absent from
  both

### Requirement: The Three New Refusals Classify as Invocation Defects

`` `SETTLE_REPLACE_CONFLICT` ``, `` `SETTLE_NOTHING_TO_REPLACE` `` and
`` `SETTLE_WITNESS_UNCHANGED` `` MUST each be classified `INVOCATION_DEFECT` in the same
classification table that already classifies `` `SETTLE_ALREADY_WITNESSED` `` there. Each is a
fact about the call's argv (a conflicting flag, a missing prerequisite, a redundant value), not
about the state of the work. Because a code's resolution-builder obligation applies only to codes
classified `WORK_STATE`, none of the three new codes requires a `resolve` builder entry, and the
existing set of work-state resolution builders MUST remain untouched by this capability.

#### Scenario: All three codes are classified, and the reachable-refusal check passes

- GIVEN the full classification table used to validate every reachable refusal code
- WHEN the three new codes are looked up
- THEN each is present and classified `INVOCATION_DEFECT`

#### Scenario: No resolution builder is added for the new codes

- GIVEN the set of resolution builders reserved for work-state refusal codes
- WHEN it is inspected after this capability ships
- THEN it contains no entry for `SETTLE_REPLACE_CONFLICT`, `SETTLE_NOTHING_TO_REPLACE`, or
  `SETTLE_WITNESS_UNCHANGED`, and its existing entries are unchanged

### Requirement: Existing `--attach` Refusals Still Take Precedence

Refusals that fire on a `settle --attach` invocation for reasons unrelated to `--replace` —
absent or ambiguous `--text`, missing or malformed `--witness`, or a conflicting `--under`/
`--supersedes` — MUST continue to fire before any of the three new `--replace`-specific
refusals are evaluated, in the same relative order as before this capability. `--replace` MUST
NOT change when those existing refusals fire.

#### Scenario: A missing `--text` still refuses before any replace-specific check runs

- GIVEN a `settle --attach --witness test_b --replace` invocation with no `--text` given
- WHEN the command is evaluated
- THEN it refuses on the existing missing-`--text` condition, and neither
  `SETTLE_NOTHING_TO_REPLACE` nor `SETTLE_WITNESS_UNCHANGED` is reached or reported

### Requirement: The Sealed Golden Delta Is a Declared Consequence, Not a Surprise

Because the `settle` response dict carries every mode flag on every call, adding the
always-present `replace` flag necessarily changes the stdout digest of the one existing sealed
`settle` case, independent of whether that case ever exercises `--replace`. This capability MUST
NOT attempt to avoid that move (for example, by making the `replace` flag conditionally absent);
the moved digest MUST be regenerated and individually read, per the seal capability's own
declared-delta discipline, as part of shipping this capability.

#### Scenario: The existing sealed `settle` case's digest is expected to move

- GIVEN the one sealed `settle` case that exists before this capability ships
- WHEN this capability's response-schema change (the added `replace` flag) is applied
- THEN that case's digest changes, and this change is treated as an expected, declared delta
  requiring regeneration and individual review — not as an unexplained seal failure

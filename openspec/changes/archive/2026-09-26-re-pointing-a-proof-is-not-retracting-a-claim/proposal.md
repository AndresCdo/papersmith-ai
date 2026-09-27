# Proposal: re-pointing-a-proof-is-not-retracting-a-claim

## Intent

An agreement's witness can go stale without the agreement going wrong, and the CLI has no way to
say so.

A target's `AGREED.md` holds one checklist line per agreement, and a line may carry a trailing
`` `test_<id>` `` token naming the test that proves it. `verify` reports
`agreements.witness.disagrees` for a ticked line whose witness is absent from a fully-parsed
`tests/`, and `close` refuses `AGREEMENT_DISAGREES`
(`skills/_core/implementation/engine/implementation_engine.py:16536-16546`). That much works, and
it works on purpose.

**What cannot be done is move the token.** `settle`'s five modes are place (the default),
`--attach`, `--remove`, `--reverse` and `--done`, and `--attach` refuses
`SETTLE_ALREADY_WITNESSED` — *"`--attach` never replaces one, only adds"* (engine:14965-14970,
restated in the `--witness` help at engine:20682-20684 and in
`skills/proposal-implementation/references/usage.md:1382-1383`). Nothing else offers a re-point
path: no other command and no `_core` helper. Four files name that code today.

**The workaround is honest, and it is still the wrong instrument.** `--reverse` does not corrupt
the record — the target itself proves it. `MIL-CREDA/AGREED.md:327` records a reversal of exactly
this class: a line whose witness measured a contribution panel that was later deleted, with the
surviving claim re-placed at `:144`. The record reads correctly. **The cost is elsewhere, and it is
the whole argument for this change:** `--reverse` deletes the settled line, and a fresh placement
starts `[ ]` and unwitnessed. Re-pointing through reversal therefore **de-ticks and un-witnesses**
an item that was measured and closed, forcing re-discussion and re-measurement to reach the state
it already had. `:144` sits open and unwitnessed today. That is the cost, visible, in the file.

**`--attach` already made this exact argument once.** `usage.md:1353-1357` says a witness could
previously be bound only by hand-editing `AGREED.md` (unsupported) or by re-`settle`ing the line,
*"which would write a fresh `[ ]` line and un-tick whatever was already reached"* — and `--attach`
exists to close that gap. Re-pointing is the same sentence one step further on: the same un-ticking
cost, paid for the same reason, closed by the same kind of flag. This proposal does not introduce a
principle; it finishes applying one.

## The doctrine this change must reckon with, and does not overturn

**Gating at close is settled and stays settled.** `agreements_state()` (engine:374) is reached from
`cmd_close` (engine:16536), from `cmd_verify`'s report (engine:17582), and from one
holder-resolution helper `settle` itself uses (engine:570) — and from nowhere else. Never
`cmd_gate`, never `cmd_probe`, never `cmd_offer`, never `cmd_step`. The engine states the rule in
its own comment at engine:16533-16535 — *"Reported by `verify`/`probe` and gated nowhere but here
(spec 'Gating stays at close')... this is the one and only place the CLI ever refuses on it"* —
restated at `usage.md:806` and `:2780`. This proposal preserves that doctrine verbatim and puts any
change to it explicitly out of scope. In particular, the new mode **must not** check whether the
incoming witness exists in `tests/`: a `settle` that measured tests would become a second gate, and
the second gate is the thing the doctrine forbids.

**The closed-class doctrine is where the real question sits.** `SKILL.md:2996-3004` declares
*"`settle`'s class is closed at five modes"*, and that closure rests on exactly two named
compositions: editing an agreement's text is `--reverse` + a fresh placement; moving one between
sections is `--remove` + a placement. **Re-pointing a witness is not among them** — not considered
and refused, simply not considered. Apply the doctrine's own criterion and it fails: the only
composition that would reach the end state is reverse, place, attach, done, and it is *not*
equivalent, because it destroys the tick and writes a `## Reversed` entry for something that was
never reversed. Neither of the two sanctioned compositions has either effect. Note also that the
same doctrine records un-ticking as *deliberately out of scope*
(`usage.md:1572-1579`) — which is precisely why the composition cannot be performed gently.

So this is not reopening a closed decision. It is supplying the case the closure argument never
examined, and amending the closure sentence to say so.

## Scope

### In Scope

- **A re-point capability on `settle`**, spelled as recommended below, that binds a new
  `` `test_<id>` `` token onto a line that already carries one.
- **The previous token recorded**, in both the `kind: "settle"` ledger event (engine:15167-15174)
  and the response (engine:15176-15183), which already carry every mode flag and the witness.
- **Three new refusals**, each classified in `GATING_REFUSALS` (engine:19039-19055) — the suite
  reddens on an unclassified reachable code (`tests/test_proposal_implementation.py:33581`).
- **`SETTLE_ALREADY_WITNESSED`'s detail gains the exit it currently lacks.** Today it states a fact
  and names nothing the operator can do. That silence *is* the gap, from where the operator stands.
- **The prose that goes false the moment the flag lands**: `cmd_settle`'s numbered docstring roster
  item 17 (engine:14719-14726, *"there is no separate flag that does"*), the `--witness` help
  (engine:20682-20684, *"`--attach` never replaces one"*), `SKILL.md`'s closed-class paragraph
  (`:2996-3004`) and its `settle` row, and `usage.md:1374-1389`.
- **Tests**, RED before GREEN, each proven reachable-red by inverting the production line.
- **One declared golden delta** in the CLI seal — see *The seal moves, and it is decisive*, below.

### Out of Scope — recorded with reasons

- **No change to what `close` or `gate` refuse on.** `AGREEMENT_DISAGREES` fires in exactly one
  place and keeps firing there. The set of gating commands is untouched.
- **No edit a forge makes to a target's agreements on its own judgement.** This change gives the
  operator an instrument; it never decides that a witness should be re-pointed. `MIL-CREDA/AGREED.md`
  is not edited by this change.
- **Un-ticking stays out.** It is deliberately absent (`usage.md:1572-1579`), it needs its own guard
  designed on its own terms, and this change makes it *less* needed, not more.
- **No witness measurement inside `settle`.** See the gating doctrine above. The new mode writes a
  token; `verify` reports on it and `close` gates it, exactly as today.
- **No sixth writer into `AGREED.md`'s checklist body.** `SKILL.md:3004` states that `settle` and
  `position` are the whole of it, and that stays true.

## Capabilities

### New Capabilities

- `implementation-witness-rebinding`: re-pointing an agreement's `` `test_<id>` `` witness — what it
  writes, what it records, what it refuses, and the two properties it must not touch (the mark, and
  the gating surface).

### Modified Capabilities

None. No existing capability owns `settle`'s mode vocabulary: `experimental-implementation-skill`
names `cmd_settle` only in a holder-obligation scenario (`spec.md:278`), and `implementation-cli-seal`
holds digests, not settle semantics. The seal's requirements already sanction a declared delta
(`implementation-cli-seal/spec.md:141` *F3 Declared-Delta Discipline*), so satisfying them is an
obligation of this change, not a requirement change.

---

## Decision block — the shape. Accept or change.

**The question: a sixth mode, or a modifier on `--attach`?**

**Recommendation: a modifier — `settle --attach --replace`.**

*Reasoning, in three parts.*

**One: the behavior already exists; only one refusal stands in front of it.** `--attach` locates by
`--text` exact match, requires `--witness`, refuses `SETTLE_ATTACH_CONFLICT` for `--under` and
`--supersedes`, and — this is the load-bearing part — already declares **"The mark is never
touched. A ticked item stays ticked, an open one stays open"** (`usage.md:1385-1387`). That is
exactly the property re-pointing requires, already written, already tested. A sixth mode would
restate it in a second place, and two copies of a property is how one of them goes stale.

**Two: this CLI has already chosen the modifier shape for this exact semantics.** `position` spells
deliberate over-writing as `--replace` on the existing install verb — `--sequence - --replace`
(`usage.md:1069`, `:1198`; `POSITION_BLOCK_EXISTS` unless `--replace` is given) — not as a second
install verb. The forge therefore accepted witness replacement once already, on the position
ladder, and `settle` was left asymmetric. Reusing that word rather than inventing a third vocabulary
is the point: an operator who knows `position --replace` knows what `--attach --replace` does before
reading anything.

**Three: it keeps the doctrine sentence literally true.** *"`settle`'s class is closed at five
modes"* survives as written; what is amended is its closure *argument*, which must now name the
modifier alongside the two compositions. A sixth mode forces the sentence to be rewritten, grows
every mode-conflict matrix by a row, and asks the reader to learn a verb that does what `--attach`
does minus one refusal.

**Alternative, if the operator prefers it:** a sixth mode, `--repoint`. Say so and every argument
below carries over unchanged — the recorded field, the untouched mark, the three refusals, the
gating boundary. Only the spelling and the doctrine sentence differ.

---

## Approach

### What is recorded, and why it is not optional

`settle` already appends one `kind: "settle"` event per write, carrying `attach`, `remove`,
`reverse`, `done`, `witness`, `holder` and the collision list (engine:15167-15174), and the response
mirrors it (engine:15176-15183). The replacement therefore needs no new store and no new file: the
event and the response each gain `replace` (the flag, as the four siblings already appear) and
**`replacedWitness` — the token that was there.**

That second field is the one that matters. The previous witness is evidence: it is what someone
believed proved this claim, and after the splice it exists nowhere. A replacement that recorded only
the incoming token would be the only `settle` write whose own event cannot answer *what was here
before* — and losing prior evidence silently is a failure class this forge keeps catching. Recording
it costs one string in a dict that already carries six.

### What refuses, and what each refusal must name

- `SETTLE_REPLACE_CONFLICT` — `--replace` given without `--attach`. The mirror of
  `SETTLE_ATTACH_CONFLICT`, `SETTLE_REMOVE_CONFLICT` and `POSITION_REPAIR_CONFLICT`; names the mode
  it belongs to.
- `SETTLE_NOTHING_TO_REPLACE` — `--replace` on a located line carrying no witness. **Not** a silent
  degrade to plain `--attach`: the caller believed a binding existed and it did not, and a call that
  thinks it changed something and did not is the defect shape this whole proposal is about. Names the
  line and says `--attach` alone is the create path.
- `SETTLE_WITNESS_UNCHANGED` — the incoming token equals the one already there. Refusing rather than
  writing keeps the ledger honest: a no-op splice that appends a `replacedWitness` event claims a
  change that did not happen. *Recommended, not load-bearing — say the word and it becomes a silent
  no-op instead.*
- `SETTLE_ALREADY_WITNESSED` — **survives, unchanged in code and changed in wording.** It fires when
  `--replace` is absent, and its detail names `--replace` as the exit. Every other refusal in this
  command tells the operator where to go; this one currently does not.
- Unchanged and still firing ahead of all of the above: `SETTLE_TEXT_ABSENT`,
  `SETTLE_TEXT_AMBIGUOUS`, `SETTLE_WITNESS_REQUIRED`, `SETTLE_WITNESS_MALFORMED`,
  `SETTLE_ATTACH_CONFLICT`.

**All three new codes are `INVOCATION_DEFECT`**, like `SETTLE_ALREADY_WITNESSED` itself
(engine:19047) — each is a fact about this call's argv, not about the state of the work.

**A measured narrowing of the cost surface.** `_publish_resolution` returns `None` unless
`GATING_REFUSALS[code] == WORK_STATE` (engine:20146-20152). Classified as invocation defects, the
three new codes owe **no `resolve` builder at all**, and `_WORK_STATE_RESOLUTIONS` is untouched. The
`resolve` obligation named in exploration applies to work-state codes only; read from disk, it does
not apply here.

### The mark, and the open line

**The mark is never touched**, and this is not a preference. Re-pointing a proof is not re-asserting
a claim: the agreement's truth did not change, only the artifact that demonstrates it. A ticked line
stays ticked and an open one stays open, which is `--attach`'s own rule inherited rather than
restated.

**An unticked line may be re-pointed.** `--attach` already binds onto a line "ticked or not"
(`usage.md:1354`), and the target holds a live instance of the shape: `MIL-CREDA/AGREED.md:146` is
`[ ]` and carries `test_every_sigma_consumer_receives_the_one_declared_constant`. A witness bound
before its claim comes true is a normal state here, and a mode that refused to correct one would
leave exactly the lines nobody is currently gating on — the ones whose staleness will surface later,
at close, as a surprise.

### The seal moves, and it is decisive

`tests/seal/cases.json:395` holds one `settle` case, the default place path, and it is not in
`unsealed.json`. The response dict always carries every mode flag, so a `"replace": false` key moves
that case's stdout digest **whatever else is decided** — which settles a question that would
otherwise have been argued: making `replacedWitness` conditional on the replace path buys nothing,
because the flag has already moved the golden. Keep the response shape uniform, regenerate the one
digest, and read it individually as
`implementation-cli-seal/spec.md:384` requires. One declared delta, F3 discipline.

## The instance, and its honest scale

`MIL-CREDA/AGREED.md:68` is ticked and names
`test_progress_prints_one_line_per_cell_and_names_that_cells_slowest_arm`, which does not exist. The
live test is `test_progress_prints_one_line_per_cell_and_names_no_timing`
(`implementations/Domain_Adaptation/tests/test_arm_objectives.py:804`), and its own docstring
(`:812-814`) says the slowest-arm and timing halves are gone along with `seconds`/`peakMiB`
themselves. The agreement's prose never claimed those halves — it claims one line per transfer and
nothing about timing — so the current test still proves the agreed claim. **Re-pointing is right
here and reversal is not.** The agreement was written 2026-08-31 (`2183ec2`); the test was renamed
2026-09-17 (`3bd7516`).

**Scale, stated honestly.** Exactly one `AGREED.md` exists in this repository. All 85 of its
witnesses were checked against every `def test_`, including class-scoped ones, and line 68 is the
**only** stale one. "Any paper will hit this" is a claim about the mechanism — a witness names a test
by string, tests get renamed, and nothing links the two — not an observed multi-instance fact. One
instance, and a mechanism that guarantees more.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `engine:14965-14970` | Modified | The ~6-line refusal becomes conditional on `--replace`; its detail names the exit |
| `engine:14334-15196` (`cmd_settle`, 863 lines) | Modified | The `--attach` branch grows the replace path; item 17 of the numbered docstring roster is amended |
| `engine:15167-15183` | Modified | Event and response gain `replace` and `replacedWitness` |
| `engine:19039-19055` (`GATING_REFUSALS`) | Modified | Three new `INVOCATION_DEFECT` entries |
| `engine:20607` / argparse for `settle` | Modified | The `--replace` flag and its help |
| `engine:20682-20684` (`--witness` help) | Modified | *"`--attach` never replaces one"* stops being true |
| `skills/proposal-implementation/SKILL.md:2996-3004` | Modified | The closure argument names the modifier |
| `skills/proposal-implementation/SKILL.md` `settle` row | Modified | New refusals listed |
| `skills/proposal-implementation/references/usage.md:1374-1389` | Modified | The `--attach` section gains the replace path |
| `tests/test_proposal_implementation.py` | Modified | New locks; 51 lines already mention attach |
| `tests/seal/digests.json` | Modified | One declared golden delta, read individually |
| `_WORK_STATE_RESOLUTIONS` (engine:20150) | **Untouched** | Measured: invocation defects owe no `resolve` |
| `agreements_state` call sites (engine:570, 16536, 17582) | **Untouched** | Gating stays at close |
| `implementations/Domain_Adaptation/MIL-CREDA/AGREED.md` | **Untouched** | The repair is the operator's call, run with the new flag |

## Test strategy

RED before GREEN, every unit; a lock that passes on its first run is proven reachable-red by
inverting the production line and watching it fail. This repository has two suites and running one
has hidden a regression before — `npm run test:all` (`openspec/config.yaml:18`), with
`python3 -m unittest tests.test_proposal_implementation` as the fast inner loop, under python3.12.

Locks the change owes:

- The happy path: a line with witness `test_a`, re-pointed to `test_b`, comes back with `test_b`
  and **the rest of the holder file byte-identical** — the mark assertion is a byte comparison, not
  a regex.
- The ledger event and the response both carry `replacedWitness: "test_a"`.
- Each of the three refusals, fired and named, and each present in `GATING_REFUSALS` — otherwise
  `reachable_refusal_codes()` (`tests:33435`, asserted at `:33581`) reddens the suite on its own.
- `SETTLE_ALREADY_WITNESSED` still fires without `--replace`, and its detail names `--replace`.
- An **unticked** witnessed line re-points, and stays unticked.
- `agreements_state` is still reached from exactly three sites, and `cmd_gate`/`cmd_probe`/
  `cmd_offer`/`cmd_step` still do not gate on it.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A new code ships unclassified and the whole suite reddens | **High if unattended** | `reachable_refusal_codes()` catches it by construction (`tests:33581`); classify all three in the same commit as the flag |
| Prose outlives its mechanism — four files say `--attach` never replaces | **High** | Four files name `SETTLE_ALREADY_WITNESSED` and two more state the claim in prose; all six are listed in *Affected Areas*, and a test asserts the sentence is gone |
| The mark is touched by an off-by-one splice | Med | The happy-path lock is a byte comparison of the whole holder file, not a field assertion |
| The new mode drifts into measuring the witness, becoming a second gate | Med | Out of scope, and a lock asserts the three `agreements_state` call sites are unchanged |
| The sealed `settle` digest is regenerated without being read | Med | `implementation-cli-seal/spec.md:384` requires each moved digest be individually read; the delta is declared in advance here |
| Someone reads this change as licence to un-tick | Low | Out of scope, stated with its reason; the change makes un-ticking less needed |
| The one measured instance reads as the whole justification | Low | The scale is stated honestly: one instance, and a mechanism that produces more |

## Rollback

One commit against `main`, reverting independently. Nothing persistent changes shape: the flag is
additive, `replacedWitness` appears only on events this change can write, and a reverted engine
simply refuses `SETTLE_ALREADY_WITNESSED` again on any line a replacement had reached — the holder
file is left exactly as the replacement wrote it, which is a valid `AGREED.md` under either version.
The one golden delta reverts with the commit. No `AGREED.md` in this repository is edited by the
change itself, so there is no target state to migrate back.

## Success criteria

- [x] A witnessed line, ticked or open, can be re-pointed in one call, with the rest of the holder
      file byte-identical. Observed: `SettleReplaceCommandTests` locks 1.1/1.2, whole-file byte
      comparison, mutation-proven against the rebuild-the-line mutation.
- [x] The replaced token is recorded in both the ledger event and the response.
- [x] Three new refusals exist, are classified, and each names what the operator should do.
- [x] `SETTLE_ALREADY_WITNESSED` names its exit; no file still claims `--attach` never replaces.
- [x] `agreements_state` is reached from the same three sites; `close` is the only command that
      gates on the witness axis. Locked by `test_agreements_state_call_sites_do_not_grow`,
      mutation-proven against a new call added inside `cmd_gate`.
- [x] `SKILL.md`'s closure argument names the new case rather than leaving it unconsidered.
- [ ] **Unmet, honestly — measured, not assumed.** The proposal's own Decision 6/spec's own
      requirement predicted the one sealed `settle` case's digest would move regardless of whether
      `--replace` is exercised. Measured during apply (Phase 4): that case already refuses
      `SETTLE_NOT_DISCUSSED` before reaching the success path where `replace`/`replacedWitness`
      would ever appear — a pre-existing condition unrelated to this change. Recapturing produced a
      byte-identical `tests/seal/digests.json` (confirmed via `git diff`, zero changed entries), so
      the declared delta never materialized. `ImplementationSealTests` stays green either way; this
      is recorded as a design assumption that did not hold, not as work left undone.
- [x] `npm run test:all` green, every new lock proven reachable-red. One additional, unplanned
      consequence surfaced during Phase 7 verification and was fixed in the same slice:
      `tests/test_implementation_domain_lock.py`'s `M5_PINNED_RESIDUE` word-occurrence pins moved
      for nine words (`after`, `before`, `check`, `claim`, `command`, `rather`, `recorded`,
      `value`, `write`) from this change's own engine prose alone — updated following that file's
      own established one-entry-per-change convention.

## Review budget forecast

Measured estimate: ~70-100 lines in the engine (flag, three refusals, roster entries, event and
response keys, two amended prose blocks), ~15 in `SKILL.md`, ~40-60 in `usage.md`, ~150-250 in
tests, plus one regenerated golden. Roughly **300-420 authored lines (additions + deletions)**.

`Decision needed before apply: No` · `Chained PRs recommended: No` · `400-line budget risk: Medium`

One slice is the intent. If the lock count grows past the budget, the natural cut is
**engine + refusals + roster + their locks** first, **documentation + the amended doctrine** second
— but they should not land far apart, because the doctrine amendment is what makes the flag
legitimate rather than merely present. The `ask-on-risk` strategy resolves this at task time.

---

## Already shipped, recorded here so the record has no hole

Recorded at the operator's explicit request. **This is documentation of a released change — not new
scope, not work to plan, not work to redo.**

Commit `d747e23`, `feat(remote-execution): hand the run's mode and units to the kernel`, released in
`v0.4.0`, shipped without a proposal. It added `FORGE_RUN_MODE` and `FORGE_RUN_UNITS` to what
`runner_invoke.py`'s `kernel_environment()` hands an executed notebook's kernel, composed by a
`submission_environment()` composition point applied by both the notebook and the callable branch
(`skills/remote-execution/assets/runner_invoke.py:123-124`, `:150-182`, `:184-207`, `:363`).

The defect it closed: `submit --unit` distributed the **ledger** and not the **work**. The packer
split units across workers and the adapter merged each worker's slice into its `run-config.json`,
but nothing on the worker read them — so every worker ran the identical whole job. The two variables
are the channel by which a worker learns which slice is its own.

This section exists so that the forge's record does not have a hole where a capability entered
without one. It asserts nothing about this proposal's scope.

## Open question for the operator

One, and only one: **the decision block above.** Accept the modifier (`settle --attach --replace`,
recommended, with its three reasons), or switch it to a sixth mode (`--repoint`). Everything else
here is either settled by what was read from disk or recommended with its reasoning exposed and
changeable on a word.

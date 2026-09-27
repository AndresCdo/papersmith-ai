# Design: re-pointing-a-proof-is-not-retracting-a-claim

## Technical Approach

`cmd_settle`'s `--attach` branch (`implementation_engine.py:14942-14973`) already does every part
of this except one: it locates the line by exact `--text`, it owns the located span, it hands that
span's raw bytes to the one renderer that knows how a witness token is spelled, and it feeds the
result to the one `impl_position.splice` call the whole command shares. Exactly one statement
stands between that machinery and re-pointing — the refusal at `:14965-14970`.

So the change is a **modifier inside that one branch**, and nothing else moves. There is no new
mode, no second located-line search (the four modes each duplicate that loop today — a fifth copy
would be the wrong lesson learned from a shape that is already duplicated four times), no second
`splice`, and no second construction of a witness token's bytes. The `--replace` path enters the
existing branch after the existing text search, evaluates three refusals against the located line,
and leaves through the existing renderer and the existing splice.

Two consequences follow from that placement and are load-bearing rather than incidental:

- **The mark is never touched, by inheritance rather than by a second rule.** `_render_settled_line`'s
  `raw_line` branch (`:14045-14050`) never parses and rebuilds a line; it takes the located bytes
  verbatim. `--replace` stays inside that branch, so "a ticked item stays ticked" is not restated
  anywhere — it is the same sentence, in the same function, holding for one more caller.
- **No test-suite measurement can leak in**, because the branch this lives in reads exactly one
  file: the resolved holder. Adding a witness check would mean adding a reader that is not there,
  which is visible in review as a new call rather than as a changed condition.

Spec coverage: `specs/implementation-witness-rebinding/spec.md`, all 12 requirements. Every line
cited below was read from disk during this phase; the places where the inputs disagree with disk
are recorded under *Disagreements with disk*, and one of them is a **four-item omission in the
proposal's file list that would have reddened the suite**.

## Architecture Decisions

### Decision 1: The `--replace` path lives inside the existing `--attach` branch, and adds no second splice

**Choice.** After `target_path, data, span = candidates[0]` (`:14961`) and the existing
`AGREEMENT_LINE` match (`:14963-14964`), the single refusal becomes a four-line ladder:

```python
        raw_line = data[span["start"]:span["end"]]
        located = AGREEMENT_LINE.match(raw_line.decode("utf-8").rstrip())
        existing = located.group("witness")
        if existing and not replace:
            raise Refused("SETTLE_ALREADY_WITNESSED", ...)      # detail now names --replace
        if replace:
            if not existing:
                raise Refused("SETTLE_NOTHING_TO_REPLACE", ...)
            if existing == witness:
                raise Refused("SETTLE_WITNESS_UNCHANGED", ...)
            replaced_witness = existing

        new_line = _render_settled_line(text, witness, raw_line=raw_line, replacing=replace)
        spliced = impl_position.splice(data, new_line, span)
```

`replaced_witness` is initialised `None` beside `heading`, `supersedes` and `collides`
(`:14938-14940`), because the ledger append at `:15167` and the response at `:15176` both sit
outside every branch and need the name in scope in all five modes.

**Alternatives considered:**

| Rejected | Why, from disk |
|---|---|
| A sixth mode `--repoint` with its own located-line loop | The loop at `:14943-14961` is copied verbatim into all four non-create modes already (`:14975-14993`, `:15007-15025`, `:15075-15093`). A fifth copy is not "following the pattern", it is paying its cost again for a mode that would then also have to restate `--attach`'s "the mark is never touched" rule — and two copies of a property is how one goes stale. Also rejected by the operator's accepted decision block. |
| A new renderer `_render_replaced_witness_line`, mirroring `_render_done_line` | `_render_done_line` (`:14056-14081`) is a legitimate sibling because it writes a **different field** — the mark. A witness-replacement writes the field `_render_settled_line` already owns, and its token grammar (`` f" `{witness}`" ``) is spelled in exactly one place today, `:14049`. A second function emitting that grammar is a second place it can drift. Secondary cost, measured: `AgreementWitnessSingleWritePathTests` (`tests:25906`) holds one `call_site_functions` assertion per renderer (`:25936`, `:25940`, `:25944`); a fourth renderer silently ships with no such assertion unless someone remembers to write one. |
| Compute the replaced line's bytes in `cmd_settle` and splice them directly | That is the "second place that decides how a line is written" this design exists to avoid, and it would break the three call-site locks above by making `cmd_settle` the author rather than the caller. |

**Rationale.** After this change `settle` still has exactly one splice per mode, one renderer that
owns the witness token, and one located-line search per mode — the same counts as before. The only
number that moves is the number of refusals guarding one branch.

### Decision 2: `_render_settled_line` gains a keyword-only `replacing`, and replaces at `span("witness")`

**Choice:**

```python
def _render_settled_line(text: str, witness: str | None, *,
                         raw_line: bytes | None = None,
                         replacing: bool = False) -> bytes:
```

Inside the existing `raw_line` branch, when `replacing` is true the body is re-matched and only the
witness group's own characters are substituted — the identical technique `_render_done_line` uses
for the mark (`:14078-14080`):

```python
    if raw_line is not None:
        has_newline = raw_line.endswith(b"\n")
        body = raw_line[:-1] if has_newline else raw_line
        if replacing:
            decoded = body.decode("utf-8")
            located = AGREEMENT_LINE.match(decoded)
            start, end = located.span("witness")
            body = (decoded[:start] + witness + decoded[end:]).encode("utf-8")
        elif witness:
            body += f" `{witness}`".encode("utf-8")
        return body + (b"\n" if has_newline else b"")
```

**Why the group's span and not "strip the tail and re-append".** Splicing at `span("witness")`
replaces the identifier and nothing else: the backticks, the space before them, any trailing
whitespace the line happened to carry, the bullet character, the mark, and the claim text are never
re-emitted. That is the strongest possible form of the spec's "every other byte of the holder file
MUST be identical", and it is free — the span is already computed by a regex the branch already
runs.

**Alternatives considered:**

- **No flag at all; replace whenever the located line carries a witness.** Genuinely tempting: the
  refusal ladder above already determines which case is reachable, so the flag carries no
  information the data does not. Rejected because it makes plain `--attach` silently overwrite the
  moment `SETTLE_ALREADY_WITNESSED` is ever weakened — the behaviour would be implicit in a guard
  one function away rather than in this function's own signature. This repository's failure
  catalogue is full of a call that thought it changed something; a renderer whose intent is
  inferred is the same shape one level down.
- **`replacing: str | None` carrying the displaced token, asserted against the located group.**
  Rejected as ceremony: the assertion could only fail if `_locate_settled_text` returned a span for
  a line that does not match `AGREEMENT_LINE`, which is impossible by that function's own
  construction (`:14145-14147`).

**The precondition, stated in the docstring rather than guarded.** When `replacing` is true the
witness group always participated, because `SETTLE_NOTHING_TO_REPLACE` refused otherwise. This is
the identical contract `_render_done_line` already keeps for `mark` — that function does not check
either, and its docstring says why. The difference worth writing down: an unmatched `mark` group is
impossible, whereas an unmatched `witness` group would make `span()` return `(-1, -1)` and corrupt
the line silently. The docstring names the refusal that makes it unreachable and the lock that
holds that refusal; the *lock*, not a defensive branch, is the mechanism.

### Decision 3: `SETTLE_REPLACE_CONFLICT` is checked immediately after `SETTLE_ATTACH_CONFLICT`, and the numbered roster does not renumber

**Choice.** The check lands at `:14791`, between the `SETTLE_ATTACH_CONFLICT` block
(`:14784-14789`) and the `witness = getattr(...)` resolution (`:14791-14792`):

```python
    replace = bool(getattr(args, "replace", False))
    if replace and not attach:
        raise Refused(
            "SETTLE_REPLACE_CONFLICT",
            "--replace modifies --attach: it re-points the witness on a "
            "line that already carries one, and names nothing on its own. "
            "Give it together with --attach, or omit it.")
```

with `replace` read alongside `attach`/`remove`/`reverse`/`done` at `:14779-14782`.

**Measured: this placement changes no existing refusal's firing.** Nothing between `:14784` and
`:14829` reads `replace` today, so no existing conflict code can fire on a `--replace`-carrying
call before this one does. The three combinations worth naming:

| Invocation | Today | After |
|---|---|---|
| `--attach --replace --under X` | `SETTLE_ATTACH_CONFLICT` | unchanged (attach given, checked first) |
| `--remove --replace` | no conflict fires | `SETTLE_REPLACE_CONFLICT` |
| `--done --replace` | no conflict fires | `SETTLE_REPLACE_CONFLICT` |

The last two are correct under the spec as written: both *are* "`--replace` without `--attach`",
and the detail names the exit. Their own mode-conflict codes do not need to learn about `--replace`
— `SETTLE_REMOVE_CONFLICT`, `SETTLE_REVERSE_CONFLICT` and `SETTLE_DONE_CONFLICT` stay byte-unchanged.

**Why this placement and not beside `--paragraph`'s guard.** The numbered docstring roster
(`:14583-14733`) claims to list the refusals *in check order*. Inserting a new conflict at the
`--paragraph` guard's position (`:14823`) would make it item 7 and renumber items 7 through 18 — an
eighty-line diff of pure renumbering, spending review budget on nothing. Placed at `:14791` it is
item 3's own neighbour, so item 3 grows a sentence and the roster's numbering is untouched.

**The uncomfortable precedent, named rather than hidden.** `--paragraph` given without `--reverse`
raises `SETTLE_REVERSE_CONFLICT` (`:14823-14828`) — the **mode's** code, not a code of its own. By
that precedent `--replace` without `--attach` should raise `SETTLE_ATTACH_CONFLICT`. Three reasons
the spec's ruling (a distinct code) is the right one, and the first is the strongest:

1. `SETTLE_ATTACH_CONFLICT` has only ever meant *"`--attach` was given together with something that
   does not apply"*. Reusing it for *"`--attach` was not given"* inverts it, so one name would carry
   two opposite conditions and a reader of the code would have to check which. `SETTLE_REVERSE_CONFLICT`
   survives its double duty because it is already raised in both directions today (`:14802` and
   `:14823`); `SETTLE_ATTACH_CONFLICT` is raised in one.
2. A distinct code is what `reachable_refusal_codes()` and the roster can see. A reused code adds a
   reachable condition that the classification table cannot distinguish.
3. The spec decided it, and it is not reopened here. Note for the record that the precedent the
   spec cites — `POSITION_REPAIR_CONFLICT` — is a *mode + forbidden flag* code (SKILL.md:3008),
   i.e. the same direction as `SETTLE_ATTACH_CONFLICT`, not the modifier-without-mode direction.
   It supports minting a code named for the flag; it does not settle the direction. Reason 1 does.

### Decision 4: `replace` and `replacedWitness` are both unconditional keys

**Choice.** The ledger event (`:15167-15174`) and the response (`:15176-15183`) each gain two keys,
placed so the mode-flag run stays contiguous:

```python
        {"kind": "settle", ..., "attach": attach, "remove": remove,
         "reverse": reverse, "done": done, "replace": replace,
         "replacedWitness": replaced_witness, "paragraph": paragraph, ...}
```

`replacedWitness` is `None` on every call that displaced nothing — which is every call but a
successful replacement.

**Alternatives considered:** emit `replacedWitness` only on the replace path. Rejected on the
proposal's own measurement, which is decisive rather than aesthetic: the always-present `replace`
flag has *already* moved the one sealed `settle` digest, so conditionality buys no golden stability
— it only buys a response whose key set varies by mode, which nothing else in this dict does
(`witness`, `under`, `paragraph`, `supersedes` and `about` are all always present and frequently
`None`). Keeping the shape uniform also means the field can never be read as "this key's absence
means no replacement happened", a reading a consumer would eventually take.

**Confirmed from disk:** no test pins `cmd_settle`'s returned key set — `returned_keys(ENGINE, ...)`
is used for `agreements_state` (`tests:3737`) and not for any `cmd_*`. The only golden that moves
is the seal digest (Decision 6).

### Decision 5: `SETTLE_ALREADY_WITNESSED`'s condition is byte-unchanged; only its sentence moves

**Choice.** The condition becomes `if existing and not replace:` — which, on every invocation that
does not carry `--replace`, evaluates exactly as `if located.group("witness"):` did. The detail
gains one clause:

> `'…' already carries witness 'test_a'; --attach adds a witness, it never replaces one. To
> re-point this line at a different test, add --replace.`

**Why the wording matters enough to be a decision.** Every other refusal in this command names a
next act — `SETTLE_NOT_WITNESSED` says *"bind one first with `settle --attach --witness test_<id>`"*
(`:15105-15109`), `SETTLE_ALREADY_REVERSED` says *"which plain --remove performs on its own"*
(`:15034-15035`), `SETTLE_COLLIDES_UNNAMED` prints a runnable `discuss` (`:15151-15153`). This one
stated a fact and stopped, and from the operator's side that silence *was* the gap this change
closes. Shipping the flag while leaving the sentence mute would close the capability and leave the
discoverability defect standing.

**Regression surface, stated as such.** The spec makes this a MUST-NOT-CHANGE condition. The
existing lock at `tests:24626-24639` asserts both the code and that the file is byte-unchanged
after the refusal; it is not edited, and it must stay green as written.

### Decision 6: One seal digest, regenerated by the declared capture, read as a one-entry diff

**The delta.** `tests/seal/cases.json:394-413` holds one `settle` case, the default create path
(`--about record --text "New settled text." --under "## Ladder"`). It is not in `unsealed.json`.
Two always-present keys join its stdout, so its digest moves — independent of `--replace` ever
being exercised.

**Measured: no other case moves.** `walk` (`cases.json:12-25`) is the only other case that could
carry a settle response, and `cmd_walk` contains no `"settle"` literal — the only `"settle"` strings
in the engine are the event kind (`:15169`), the response's own `command` (`:15177`),
`GATING_COMMANDS` (`:18951`), the dispatch table (`:20306`), a session-requiring set (`:20388`) and
the parser branch (`:20607`). No sealed case prints anything derived from `GATING_REFUSALS`.

**The regeneration step, declared so apply does not discover it.** `tests/seal_capture.py` is the
only writer of `tests/seal/digests.json`; it is deliberately not matched by `unittest discover`
(its own docstring, `:4-7`) and is run by hand:

```
.venv/bin/python tests/seal_capture.py
```

It rewrites the **whole** file (`:153-154`) after running every case twice in two independently
built corpora and refusing to write anything on an unexpected disagreement (`:132-146`). So the
declared-delta review is a read of the resulting diff, and the diff must show **exactly one changed
entry** — `settle` — with `__corpus_fingerprint__` unchanged, because `tests/seal/corpus.py` is not
edited by this change. Any second moved entry is an unexplained seal failure, not a bulk
regeneration to be accepted (`implementation-cli-seal/spec.md:384`), and stops apply.

The regenerated `digests.json` is a generated golden: excluded from the authored review-line count,
included in the commit.

### Decision 7: The gating-surface requirement is held by a call-site-set lock, and its docstring must not overclaim

**Choice.** A new lock reusing `AgreementWitnessSingleWritePathTests.call_site_functions`
(`tests:25918-25934`) — the house instrument for exactly this question:

```python
self.assertEqual(self.call_site_functions("agreements_state"),
                 {"holder_resolution", "cmd_close", "cmd_verify"})
```

**Measured from disk**, because the proposal states the three sites by line and not by name:
`agreements_state` is defined at `engine:374` and called at `:570` (inside `holder_resolution`,
defined `:533`), `:16536` (inside `cmd_close`, `:16415`) and `:17582` (inside `cmd_verify`,
`:17082`). Three sites, three distinct enclosing functions.

**The sentence the docstring must not write.** `cmd_settle` *does* reach `agreements_state` today —
through `holder_resolution` (`:14891`), in every one of its five modes, to find the holder by shape.
What it has never done is read the witness axis. A lock whose prose says "settle never reaches
`agreements_state`" would be false the day it is written; the true claim, and the one the spec
requires, is that **the set of call sites does not grow**, and that `cmd_gate`, `cmd_probe`,
`cmd_offer` and `cmd_step` are absent from it before and after.

`AGREEMENT_DISAGREES` keeps its one raise site at `:16539-16546`, under the comment at
`:16529-16535` that states the doctrine. Byte-unchanged.

### Decision 8: The doctrine sentence survives; the closure *argument* gains a third case

`SKILL.md:2996-3004` says *"`settle`'s class is closed at five modes"* and rests that closure on two
named compositions. The modifier keeps the sentence literally true, which is the whole payoff of
the accepted decision block — and it is measurably true in more places than the proposal counted:
`engine:14346` (*"All five modes go through this one command"*), `engine:14655` (*"all five
modes"*), `SKILL.md:2996`, and `skills/experimental-implementation/references/usage.md:36`
(*"`settle`'s five modes"*) all stay correct with no edit. Only `SKILL.md`'s closure *paragraph*
changes, to add the third case its criterion never examined:

> …and re-pointing a witness is neither: it is `--attach`'s own write with one refusal lifted, so
> it is spelled `--attach --replace` rather than as a sixth mode. The composition that would reach
> the same end state — reverse, place, attach, done — is not equivalent, because it destroys a tick
> the agreement never lost and writes a `## Reversed` entry for something that was never reversed.

`SettleFiveModesClassStatedOnceTests` (`tests:25829-25866`) reads that paragraph by substring
(`:25851-25852`); both anchors it asserts are in sentences this change does not touch.

## Data Flow

    settle --attach --witness test_b --replace --text "<claim text>"
      │
      ├─ argv tier (:14768-14863) — unchanged order
      │    SETTLE_STDIN_CONFLICT · SETTLE_EMPTY_TEXT
      │    SETTLE_ATTACH_CONFLICT (:14784)
      │    SETTLE_REPLACE_CONFLICT (:14791)   ← new, --replace without --attach
      │    SETTLE_REMOVE/REVERSE/DONE_CONFLICT · SETTLE_WITNESS_REQUIRED
      │    SETTLE_WITNESS_MALFORMED (:14857)
      │
      ├─ holder_resolution(:14891) ──→ agreements_state(:570)   (by shape; NOT the witness axis)
      │    SETTLE_HOLDER_ABSENT · HOLDER_UNDECLARED
      │
      └─ --attach branch (:14942)
           _locate_settled_text(data, text)  ── matches AGREEMENT_LINE's TEXT group (:14146)
             │                                   (the witness token is NOT part of --text)
             ├─ 0 hits → SETTLE_TEXT_ABSENT      1+ hits → SETTLE_TEXT_AMBIGUOUS
             │
             └─ one span → AGREEMENT_LINE.match(raw_line)
                  existing = group("witness")
                    existing and not replace → SETTLE_ALREADY_WITNESSED  (detail names --replace)
                    replace and not existing → SETTLE_NOTHING_TO_REPLACE
                    replace and existing == witness → SETTLE_WITNESS_UNCHANGED
                    otherwise → replaced_witness = existing
                  │
                  _render_settled_line(..., raw_line=, replacing=replace)   ← one renderer
                       replacing: substitute at span("witness")   — identifier bytes only
                       else:      append " `test_<id>`"           — unchanged behaviour
                  │
                  impl_position.splice(data, new_line, span)                ← one splice

    write_spliced(target_path, spliced, expect_digest=pre_digest)   (:15163-15164, unchanged;
                                                                     POSITION_HOLDER_MOVED as today)
      │
      ├─ append_event  kind:"settle"  … replace, replacedWitness   (:15167-15174)
      └─ response      … replace, replacedWitness                  (:15176-15183)
                                                                        │
                                                    tests/seal/cases.json:395 digest moves

Nothing reads `tests/` anywhere on this path. `verify` reports `agreements.witness.disagrees` on
the new token at the next `verify`, and `close` gates on it at `:16539` — exactly as before.

## File Changes

| File | Action | Description |
|---|---|---|
| `skills/_core/implementation/engine/implementation_engine.py:14014-14053` | Modify | `_render_settled_line` gains keyword-only `replacing`; the `raw_line` branch forks on it and splices at `span("witness")`. Docstring gains the third case and its precondition |
| `…engine…:14583-14733` (`cmd_settle` docstring roster) | Modify | Item 3 gains `SETTLE_REPLACE_CONFLICT`; item 17 rewritten (*"there is no separate flag that does"* is retired); a new item 18 covers `SETTLE_NOTHING_TO_REPLACE` and `SETTLE_WITNESS_UNCHANGED`, moving the current item 18 to 19. Items 1-17 keep their numbers |
| `…engine…:14335-14347` (`cmd_settle` docstring head) | Modify | One clause: `--attach` takes `--replace`, which re-points rather than adds. *"All five modes"* stays |
| `…engine…:14779-14782` | Modify | `replace` read beside the four mode flags |
| `…engine…:14791` | Create | `SETTLE_REPLACE_CONFLICT` |
| `…engine…:14938-14940` | Modify | `replaced_witness = None` initialised beside `heading`/`supersedes`/`collides` |
| `…engine…:14963-14973` | Modify | The refusal ladder above, and `replacing=replace` on the renderer call |
| `…engine…:19033-19058` | Modify | Three `INVOCATION_DEFECT` entries in the settle block of `GATING_REFUSALS` |
| `…engine…:20607` (settle parser) | Create | `--replace` (`action="store_true"`) and its help |
| `…engine…:20669-20718` | Modify | `--witness` help (`:20682-20684`, *"--attach never replaces one"*) and `--attach` help gain the replace path |
| `…engine…:14974-15112` (remove/reverse/done branches) | **Untouched** | No other mode learns about `--replace`; their conflict codes are byte-unchanged |
| `…engine…:15163-15164`, `impl_position.splice` | **Untouched** | One splice, one compare-and-swap, as today |
| `…engine…:374`, `:570`, `:16536`, `:17582`, `:16529-16546` | **Untouched** | Gating stays at close |
| `…engine…:19776` (`_WORK_STATE_RESOLUTIONS`) | **Untouched** | Measured: `refusal_resolution` returns `None` for a non-`WORK_STATE` code at `:20148-20149`, before the builder lookup at `:20150` |
| `skills/proposal-implementation/SKILL.md:2996-3004` | Modify | The closure argument names the third case |
| `…SKILL.md:3015` (settle row) | Modify | `--replace` in *What it writes*; three codes in *Refuses on*. One physical line, large |
| `…SKILL.md:3060` | Modify | **"One hundred and twenty-one distinct codes"** → twenty-four |
| `…SKILL.md:3078` | Modify | **"an *invocation* defect** (50 codes)"** → 53 |
| `…SKILL.md:3082` | **Untouched** | Work-state count stays 71 |
| `…references/usage.md:1351-1403` | Modify | The `### --attach` section gains the replace path: prose, a runnable example, a response block, the three refusals, and the mark rule restated as inherited. `:1383` (*"never replaces one, only adds"*) is retired |
| `…references/usage.md:1342-1349` | Modify | The single-write-path paragraph names the third route into the token |
| `…references/usage.md:2460` | Modify | **"Fifty codes, and nothing is published beside them"** → "Fifty-three codes" |
| `…references/usage.md:2465` | **Untouched** | "Seventy-one codes, including" stays |
| `skills/experimental-implementation/references/usage.md:36` | **Untouched** | *"`settle`'s five modes"* — read and confirmed still true |
| `tests/test_proposal_implementation.py` | Modify | New locks (see *Testing Strategy*); `test_the_derivation_finds_the_measured_one_hundred_and_twenty_one` renamed and its assertion moved to 124 |
| `tests/seal/digests.json` | Modify | One entry, regenerated by `tests/seal_capture.py`. Generated golden |
| `tests/seal/cases.json`, `tests/seal/corpus.py`, `tests/seal/unsealed.json` | **Untouched** | No new case; `__corpus_fingerprint__` must not move |
| `implementations/Domain_Adaptation/MIL-CREDA/AGREED.md` | **Untouched** | The one stale witness is the operator's to repair with the shipped flag |

## Interfaces / Contracts

```python
# implementation_engine.py

def _render_settled_line(text: str, witness: str | None, *,
                         raw_line: bytes | None = None,
                         replacing: bool = False) -> bytes:
    """...
    **Re-pointing an EXISTING witness** (`raw_line` given, `replacing=True`,
    `cmd_settle --attach --replace`): only the characters `AGREEMENT_LINE`'s
    own `witness` group matched are substituted -- the backticks, the space
    before them, the bullet, the mark, the claim text and any trailing
    whitespace are never re-emitted, so "every other byte identical" holds
    by construction rather than by care.

    The group always participated when `replacing` is true: `cmd_settle`
    refuses `SETTLE_NOTHING_TO_REPLACE` on a located line carrying no token,
    ahead of this call. Not re-checked here, the identical contract
    `_render_done_line` keeps for `mark` -- the guard is the refusal, and
    `SettleReplaceCommandTests` holds the refusal.
    """
```

New refusal codes, all `INVOCATION_DEFECT`:

| Code | Fires when | The detail names |
|---|---|---|
| `SETTLE_REPLACE_CONFLICT` | `--replace` without `--attach` | that `--replace` modifies `--attach`, and the two exits (add `--attach`, or drop `--replace`) |
| `SETTLE_NOTHING_TO_REPLACE` | `--attach --replace` on a located line with no witness | the located line, and that plain `--attach` is the create path |
| `SETTLE_WITNESS_UNCHANGED` | the incoming token equals the one already there | the token, and that nothing would change |

Event and response, both modes' shape unchanged except for two keys:

```jsonc
{ "kind": "settle", "attach": true, "remove": false, "reverse": false,
  "done": false, "replace": true, "replacedWitness": "test_a",
  "witness": "test_b", "paragraph": null, "supersedes": null, "collides": [] }
```

## Testing Strategy

RED before GREEN for every lock (`openspec/config.yaml:1`, `strict_tdd: true`). The mutation named
per row is chosen so that a **weaker** lock survives it — reverting the production line proves the
test can go red at all, and only these choices prove it goes red for the right reason. Fixtures and
helper reuse `SettleAttachCommandTests._box` / `_settle` (`tests:24574-24603`), whose argv builder
already emits a bare flag for a `True` value, so `--replace` needs no helper change.

| # | Lock | The mutation a weaker lock survives |
|---|---|---|
| 1 | A ticked, witnessed line re-points; the holder file is **byte-identical except the token** — a `read_bytes()` equality against the expected whole file, never a regex on the line | Rebuild the line as `f"- [x] {text} \`{witness}\`"` instead of splicing at `span("witness")`. A lock asserting "the new witness is present and the mark is still `[x]`" survives it; only a whole-file byte comparison, on a fixture whose line uses a `*` bullet and doubled internal spacing, fails |
| 2 | An **unticked** witnessed line re-points and stays `[ ]` | Add `if located.group("mark") != "x": raise` (a plausible "only re-point what is proven" guard). Lock 1 survives entirely; only the unticked fixture fails. This is the lock that pays for the spec's mark-blindness requirement |
| 3 | `SETTLE_NOTHING_TO_REPLACE` on an unwitnessed line, **and the file unchanged afterwards** | Delete the `if not existing` check so `--replace` degrades to a plain create. A lock asserting only "the command exits 2" survives nothing, but a lock asserting only the code survives a variant that refuses *after* writing; the byte comparison is what closes that |
| 4 | `SETTLE_WITNESS_UNCHANGED` on a same-token call, **and no ledger event appended** — `position.jsonl` line count before and after | Make it a silent no-op that returns `status: "written"`. A lock asserting exit 2 fails, so it is reachable-red; but a lock asserting only exit 2 survives a no-op that refuses *and still appends*. The ledger census is what the spec's own argument for this refusal actually requires |
| 5 | `SETTLE_REPLACE_CONFLICT` for `--replace` alone, and for `--remove --replace` | Move the check below `SETTLE_WITNESS_REQUIRED`. The `--replace`-alone case survives (no `--attach`, so `WITNESS_REQUIRED` cannot fire either); only the `--attach`-less-with-`--witness` case pins the position |
| 6 | All three codes present in `GATING_REFUSALS` and classified `INVOCATION_DEFECT` | Satisfied by construction via `reachable_refusal_codes()` (`tests:33581`) — but that check only proves *presence*. Classify one as `WORK_STATE` and `test_every_work_state_publishes_something_runnable` (`tests:33713`) goes red for a missing builder; assert the kind explicitly so the reason is readable rather than inferred from a builder failure |
| 7 | `SETTLE_ALREADY_WITNESSED` still fires without `--replace`, and its detail contains the literal `--replace` | Two separate mutations. (a) `if existing and not replace` → `if existing and replace`: the existing lock at `tests:24626` catches it. (b) Ship the flag and leave the old sentence: only a detail-substring assertion catches it, and *only* if it asserts the exit token, not merely that the detail is non-empty |
| 8 | The replacement succeeds when the new witness names **no real test** — no `tests/` read on this path | Add an existence check inside the branch. A lock asserting "the command succeeds" on a box whose `tests/` happens to contain the function survives; the fixture must write a `tests/` containing a *different* function, then assert exit 0 **and** that `agreements_state` immediately reports the line under `witness.disagrees` — proving the engine wrote a token it did not measure. Mirrors `tests:25770-25786` |
| 9 | `call_site_functions("agreements_state") == {"holder_resolution", "cmd_close", "cmd_verify"}` | Add `agreements_state(target, name)` inside `cmd_gate`. A lock asserting "`cmd_gate` is not in the set" survives a new call added to `cmd_probe`; only the full-set equality fails for any new site |
| 10 | The seal's one moved digest | Not a written lock: `ImplementationSealTests` already compares every case against `digests.json`. The discipline is procedural — recapture, then read the diff and assert by eye that exactly one entry moved and `__corpus_fingerprint__` did not |
| 11 | Documentation: the `### \`--attach\`` section names `--replace`, the three codes, and no longer says *"never replaces one"* | Mirrors `SettleRemoveReverseUsageDocumentedTests` (`tests:25789-25826`), reading the section body between headings. A lock asserting only "`--replace` appears in usage.md" survives leaving line 1383 standing; a negative assertion on the retired sentence is what makes the prose-outlives-mechanism risk enforceable |
| 12 | The settle row names the three codes | Extends `test_the_settle_row_documents_remove_and_reverse` (`tests:25854-25866`), which already reads that row's *Refuses on* cell by table parse |

**The four locks the change inherits rather than writes**, each of which goes red on the classification
commit unless its counterpart document moves in the same commit:

- `test_the_derivation_finds_the_measured_one_hundred_and_twenty_one` (`tests:33624-33676`) —
  `assertEqual(len(reachable_refusal_codes()), 121)` → `124`. **The test's own name carries the
  number**, so it is renamed to `…one_hundred_and_twenty_four` and its docstring gains one sentence
  recording that this change's delta is +3, measured here rather than predicted. Renaming, not
  adding a second method: two methods differing only in a number is how five tests once stopped
  running in this file.
- `test_the_doctrine_states_the_split_the_roster_actually_holds` (`tests:33740-33793`) — derived,
  not edited, but it reads four sentences off disk. Measured today: 50 `INVOCATION_DEFECT` + 71
  `WORK_STATE` = 121. After: 53 + 71 = 124. `SKILL.md:3060`, `SKILL.md:3078` and `usage.md:2460`
  must move; `SKILL.md:3082` and `usage.md:2465` must not.
- `test_the_roster_classifies_nothing_a_gating_command_cannot_raise` (`tests:33691`) — the reverse
  direction. Classifying a code whose raise site is never added goes red here.
- `AgreementWitnessSingleWritePathTests` (`tests:25936-25946`) — three assertions, unchanged,
  green only because this design adds no renderer.

**Commands.** `npm run test:all` (`openspec/config.yaml:18`), with
`python3.12 -m unittest tests.test_proposal_implementation` as the fast inner loop. This repository
has two suites and running one alone has hidden a thirteen-test regression before; the Node suite
is unaffected by this change but is not evidence until it has run.

**Non-vacuity.** Locks 1-5, 7 and 8 drive the real CLI as a subprocess against a real box. Each
must assert the fixture produced the state it claims — the located line present, carrying exactly
the token the test names — before asserting on the outcome, because a fixture that silently failed
to write the witness would make lock 3 pass for the wrong reason.

## Threat Matrix

**N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or
process-integration boundary.** This change adds one boolean flag, three refusals and two dict keys;
its only write is the existing `impl_position.write_spliced` call, guarded by the pre-image digest
it already carries (`:15163-15164`), into a markdown file under a path `resolve_target` and
`holder_resolution` already resolved. No subprocess is spawned, no path is classified, no command
is composed, no remote is contacted.

One residual, named rather than matrixed: the splice writes at a byte offset computed from a read
that happened earlier in the same call. That is not new — it is the exact hazard
`POSITION_HOLDER_MOVED` exists for, and `--replace` reaches it through the identical compare-and-swap
as the other four modes. Lock 1's whole-file byte comparison is what would catch an off-by-one in
the offset this change does introduce (`span("witness")`).

## Migration / Rollout

No migration required. Nothing persistent changes shape: `replacedWitness` appears only on events
this change can write, and a reverted engine reads an event carrying it exactly as it reads any
other `settle` event — the reader consults named keys, never a fixed schema. A holder file a
replacement already rewrote is a valid `AGREED.md` under either version: the token grammar is
unchanged, only which token is there.

One commit against `main` is the intent (see *Review budget* for the declared cut if it does not
fit). Rollback is `git revert`, including the regenerated golden, whose entry returns to the value
it holds today because nothing else in `corpus.py` or `cases.json` moved.

## Review budget

Estimated authored lines (additions + deletions, generated goldens excluded), per file:

| File | Est. | Note |
|---|---|---|
| `implementation_engine.py` — code | ~45 | flag read, conflict block, refusal ladder, renderer fork, two dict keys, three roster entries |
| `implementation_engine.py` — docstrings & argparse help | ~75 | roster items 3/17/18 (+ one renumber), head clause, renderer docstring, `--replace` help, two amended helps. This file's help strings run 15-25 lines each; that is its register, not padding |
| `SKILL.md` | ~18 | closure paragraph ~12, three count/row lines ~6 (one of them very long) |
| `references/usage.md` | ~55 | the `--attach` section's replace path with example and response block ~45, retired sentence ~4, count sentence ~2, single-write paragraph ~4 |
| `tests/test_proposal_implementation.py` | ~170 | twelve locks at this file's fixture-per-test density, plus the rename and its docstring sentence |
| **Total** | **~360** | |
| `tests/seal/digests.json` | (excluded) | generated golden |

**Verdict: one slice.** ~360 against a 400-line budget, with the two largest uncertainties both in
tests (lock count) and documentation (how long the worked example runs). The proposal forecast
300-420 and rated the risk Medium; this design's reading is the same number with a tighter engine
figure and a larger docstring figure, because the roster items and the argparse help in this file
are long by convention.

`Decision needed before apply: No` · `Chained PRs recommended: No` · `400-line budget risk: Medium`

**The cut, declared in advance so apply does not have to invent one.** If the measured count passes
400 before the documentation lands, cut here:

- **Slice 1 — the flag and everything the suite forces to move with it.** Engine code and its
  docstrings, the three `GATING_REFUSALS` entries, argparse, locks 1-9, the count test rename, the
  three count sentences (`SKILL.md:3060`, `SKILL.md:3078`, `usage.md:2460`), and the seal
  recapture. Stands alone: `npm run test:all` green, the flag works, the refusals name their exits.
  The count sentences are **not** deferrable — `test_the_doctrine_states_the_split_the_roster_actually_holds`
  reads them off disk, so they are engine work wearing a markdown file's clothes.
- **Slice 2 — the narrative.** `SKILL.md`'s closure paragraph, the settle row, `usage.md`'s worked
  replace path, and locks 11-12. Stands alone: documentation plus its own locks, no engine change.

They should not land far apart. Slice 1 ships a capability whose only written argument lives in a
docstring, and the closure amendment is what makes the flag legitimate rather than merely present.

## Open Questions

None blocking. Two rulings this design took that the inputs left open, recorded so they can be
overturned on a word rather than rediscovered:

- [x] **`replacedWitness` is always present, `None` when nothing was displaced** (Decision 4). The
      spec says "on a successful replacement"; read as *populated then*, not *present then*, on the
      proposal's own seal measurement.
- [x] **`SETTLE_REPLACE_CONFLICT` sits at `:14791`, not at the `--paragraph` guard** (Decision 3).
      Chosen to keep the numbered roster from renumbering twelve items; measured to change no
      existing refusal's firing.

## Disagreements with disk

1. **The proposal's file list omits four places the suite forces to move, and its risk row
   under-states the consequence.** The row *"A new code ships unclassified and the whole suite
   reddens"* names classification only. Classification is necessary and not sufficient:
   - `tests:33676` asserts `len(reachable_refusal_codes()) == 121`, and
     `test_the_derivation_finds_the_measured_one_hundred_and_twenty_one` carries the number **in
     its own method name**. Three new codes make it 124.
   - `test_the_doctrine_states_the_split_the_roster_actually_holds` (`tests:33740`) reads
     `SKILL.md:3060` (*"One hundred and twenty-one distinct codes are reachable from the ten gating
     commands"*), `SKILL.md:3078` (*"(50 codes)"*) and `usage.md:2460` (*"Fifty codes, and nothing
     is published beside them"*) against the live roster.
   - Measured from disk: 50 `INVOCATION_DEFECT` + 71 `WORK_STATE` = 121, which matches
     `len(GATING_REFUSALS)` exactly, as both roster locks require. After: 53 + 71 = 124.
     `SKILL.md:3082` and `usage.md:2465` (the work-state sentences) must **not** move — and that
     test's own docstring warns that a stale count on one side used to pass while the other was
     right. **Followed disk**: all four are in *File Changes* and in Slice 1.
2. **`_publish_resolution` does not exist.** The proposal cites *"`_publish_resolution` returns
   `None` unless `GATING_REFUSALS[code] == WORK_STATE` (engine:20146-20152)"*. The function on disk
   is `refusal_resolution` (`:20121`), and its two early `None` returns are at `:20146-20147`
   (non-gating command) and `:20148-20149` (not `WORK_STATE`), with the builder lookup at `:20150`.
   **Followed disk — and the proposal's conclusion is correct**: an `INVOCATION_DEFECT` returns
   before `_WORK_STATE_RESOLUTIONS` (`:19776`) is consulted, so the three new codes owe no builder
   and that dict is untouched. `test_no_invocation_defect_publishes_a_resolution` (`tests:33730`)
   holds it.
3. **`GATING_REFUSALS`' settle block is `19033-19058`, not `19039-19055`.** The proposal's range
   starts at `SETTLE_DONE_CONFLICT` and ends at `SETTLE_HEADING_ABSENT`, clipping five entries at
   each end. `SETTLE_ALREADY_WITNESSED` at `:19047` is cited correctly. **Followed disk.**
4. **`--text` is the claim text, not the whole line, and not the line including its token.** Both
   the spec's scenarios and the brief write `--text <that exact line>`.
   `_locate_settled_text` matches `AGREEMENT_LINE`'s `text` group (`:14146`), and that group stops
   before the trailing `` `test_<id>` `` (`:321-322`). So re-pointing
   `- [x] the claim \`test_a\`` is `--text "the claim"`, never `--text "the claim \`test_a\`"` —
   which would match zero lines and refuse `SETTLE_TEXT_ABSENT`. **Followed disk**; this is the one
   operator-facing surprise in the change, and `usage.md`'s worked example must show it explicitly.
5. **`cmd_settle` already reaches `agreements_state`.** Through `holder_resolution` (`:14891` →
   `:570`), in every mode, to find the holder by shape. The proposal's *Untouched* row is accurate
   about the call sites; the design records the fact so lock 9's docstring does not write a false
   sentence about which commands reach the function (Decision 7).
6. **A seventh place states the five-mode class**, beyond the six the proposal's risk row counts:
   `skills/experimental-implementation/references/usage.md:36`. Read and confirmed **still true**
   under the modifier decision — recorded so a later sweep does not "find" it and change a correct
   sentence.

Everything else the inputs asserted was re-read and confirmed at the cited line: the refusal
(`:14965-14970`), `cmd_settle`'s span (`:14334-15183`), the event and response (`:15167-15183`),
item 17 (`:14719-14726`), the `--witness` help (`:20682-20684`), `AGREEMENT_DISAGREES`' single raise
site and its doctrine comment (`:16529-16546`), `agreements_state`'s three call sites (`:570`,
`:16536`, `:17582`), `SKILL.md:2996-3004` and its settle row (`:3015`), `usage.md:1353-1357` and
`:1374-1389`, `position --replace`'s precedent (`usage.md:1069`, `:1198`), the sealed `settle` case
(`tests/seal/cases.json:394-413`) and its absence from `unsealed.json`, the seal's declared-delta
requirements (`implementation-cli-seal/spec.md:141`, `:384`), and
`reachable_refusal_codes()`'s derivation (`tests:33435-33507`), which reaches the engine through the
`cmd_*` closure — `CORE_IMPLEMENTATION.glob("*.py")` (`tests:33503`) is non-recursive and does not
see `engine/implementation_engine.py`, so the three new codes are derived because `settle` is in
`GATING_COMMANDS` (`:18950-18951`), not because the file is swept.

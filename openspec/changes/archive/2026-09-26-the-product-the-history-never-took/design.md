# Design: The Product the History Never Took

## Technical Approach

The capability adds one fact to a block that already exists. `_step_wrote`
(`implementation_engine.py:10698-10719`) already computes `wrote["inside"]` —
the concrete, product-relative paths this run wrote under the roots the step
declared. This change asks git which of those paths the repository has been
told not to ship, and publishes the answer as `wrote["ignored"]`, a parallel
field beside `inside`/`outside`, reaching both surfaces `wrote` already
reaches: the terminal ledger event (`:16821`) and `cmd_step`'s return
(`:16832`).

Three layers, each owning one thing:

| Layer | Location | Owns |
|---|---|---|
| The subprocess | `impl_gitops.repository_ignored` | asking git, and reading its exit codes honestly |
| The path base | engine `_step_wrote_ignored` | joining the product name on, and mapping the answer back |
| The wiring | `cmd_step`, between `:16809` and `:16811` | putting the field where both surfaces already read |

The proposal settled the product decisions; this document settles the four
internal ones it deferred, and one it did not anticipate (D4, the consequence
prose and the ledger). Every line number below was re-verified against disk on
2026-09-26; the two the proposal got wrong are named in **Citations
re-verified**.

## Architecture Decisions

### Decision D1: The computation happens at the `cmd_step` call site, not inside `_step_wrote`

**Choice**: option **(b)**. `_step_wrote` keeps its signature
`(declared, before, after)` and stays pure. A new module-level helper
`_step_wrote_ignored(target, name, inside)` sits beside it, and `cmd_step`
calls it at `:16809`, folding the result into the local `wrote` dict before
the ledger event is built.

**Alternatives considered**: option **(a)** — `_step_wrote` gains keyword-only
`target`/`name` parameters (with defaults) and computes the check itself.

**Rationale**, in the order the evidence decided it:

1. **`_step_wrote` is the only pure function on this path, and (a) ends that.**
   It reads two dicts and a list and returns a dict. Its two helpers are pure
   too: `changed_paths` (`:10649-10655`) and `_owns` (`:10658-10670`). Every
   process, filesystem and git boundary in `step` is owned one level up by
   `cmd_step` — `product_snapshot` (`:16765`, `:16809`), `impl_steps.run_step`
   (`:16790`), `suite_digest` (`:16815`), `impl_position.append_event`
   (`:16786`, `:16823`). (a) would put a `git check-ignore` subprocess inside
   the one function in this path that can currently be reasoned about, and
   exercised, without a repository on disk. (b) leaves the boundary where the
   boundaries already are.
2. **The test-ripple argument that usually decides this does not apply here,
   and that is a measured fact rather than an estimate.** `rg '_step_wrote'`
   over the whole repository returns exactly two source hits: the definition
   (`:10698`) and the single call (`:16808`). **No test calls `_step_wrote`
   directly** — `StepWriteScopeTests` drives the real CLI as a subprocess
   (`_run`, `tests/test_proposal_implementation.py:36291-36296`). The prior
   change's lesson (a new parameter is only call-site-free when it is
   keyword-only **with a default**, because roughly eighteen suite call sites
   passed positionally) therefore has nothing to bite on: there are no other
   call sites to keep untouched. This removes the cheapest argument **for**
   (a) as well as the argument against it, which is why the boundary argument
   above carries the ruling alone rather than being stacked on a ripple count
   that is zero.
3. **Both required surfaces are downstream of the call site.** The spec
   requires the field in the ledger event *and* in the return. The event dict
   (`:16811-16822`) and the return dict (`:16825-16834`) are both built from
   the local `wrote` after `:16808`, so one assignment reaches both. (a)
   reaches both too — this is neutral on correctness, but (b) reaches them
   with the join, the query and the answer-mapping visible inside the same
   twenty-five lines a reader is already reading to learn what `step` returns,
   instead of split across two functions six thousand lines apart.
4. **Under (a) the parameters would be dead on three of four branches.**
   `_step_wrote` returns early for `undeclared` (`:10706-10708`) and produces
   an empty `inside` for `nothing`; only the `own`/`foreign` path has anything
   to ask git about. A parameter used on one branch of four is a signature
   that lies about what the function needs.
5. **Rollback is contiguous under (b).** Deleting the helper, the constant, the
   two-line wiring block and one tuple entry removes the capability. Under (a)
   the revert also touches `_step_wrote`'s signature and its four return
   dicts — a larger blast radius for the same fact.

**What (b) costs, and how it is paid**: `_step_wrote`'s return value is no
longer the complete `wrote` block, so a reader of that function alone would not
learn that `ignored` exists. Paid with prose, the way this file pays for
everything: `_step_wrote`'s docstring gains a sentence naming `ignored`, saying
it is joined on by `cmd_step`, and saying why it is not computed here. That is
a task in `tasks.md`, not a test.

**If a second caller of `_step_wrote` ever appears**, promoting these two lines
into it is mechanical. Demoting a subprocess back out of a function many
callers treat as pure is not. The reversible direction is the one to take
first.

### Decision D2: The helper mirrors `forge_vocabulary.repository_ignored`'s shape, and `impl_gitops`'s argument order

**Choice**: `impl_gitops.repository_ignored(target: Path, paths: list[str]) -> set[str]`.

**Alternatives considered**: importing `tests/forge_vocabulary.repository_ignored`
(`:220-250`); extending `present_files` (`impl_gitops.py:23-50`); copying
`forge_vocabulary`'s `(paths, root)` argument order verbatim.

**Rationale**: the import is refused by the proposal and by direction —
`skills/_core/` must not depend on `tests/`. `present_files` globs the whole
tree itself and takes no path list (`:35-39`), so it cannot answer a targeted
question and is left alone. The argument order is the one deliberate
divergence from the mirrored shape: every function in `impl_gitops` takes the
repository first (`git(target, *args)` `:9`, `tracked_files(target)` `:18`,
`present_files(target)` `:23`, `text_files(target, paths)` `:53`,
`read_text(target, rel)` `:57`), and `text_files(target, paths)` is already
exactly this signature. Matching the module beats matching the file we are
mirroring from; a module with one function whose arguments run backwards is
how a caller comes to pass them backwards.

Returns `set[str]`, not `set[Path]`. `forge_vocabulary` returns `Path` objects
because its callers compare against `Path`s; ours compares against the POSIX
strings `product_snapshot` records (`snapshot[relative.as_posix()]`, `:10645`),
and converting to `Path` and back would reintroduce the separator question on
Windows that the `as_posix()` call already settled.

### Decision D3: Exit codes are not branched on — stdout is parsed unconditionally, and `check=False` is written explicitly

**Choice**: one `subprocess.run([...], check=False)` whose stdout is split on
NUL regardless of return code. No `returncode` comparison, no `try/except`
around a raising call, and never `impl_gitops.git()` — which raises
`Refused("GIT_FAILED")` on any non-zero exit (`:13-14`) and is therefore the
exact trap the proposal names.

**Alternatives considered**: an explicit `{0: ..., 1: ...}` dispatch, as
`accounts_cli.is_ignored` uses (`:175-177`); `check=True` with a
`CalledProcessError` handler.

**Rationale and the contract each code becomes**:

| Exit | Meaning | Becomes |
|---|---|---|
| `0` | at least one path matched an ignore rule | the matched paths, parsed from stdout |
| `1` | nothing matched | `set()` — a clean, empty answer, never an error |
| `128` | not inside a work tree | `set()` — same reading, for the same caller's question |
| `OSError` (no `git` on `PATH`) | git could not be asked | `set()` |

A non-zero exit carries no stdout, so parsing stdout unconditionally *is* the
contract — the same thing `present_files` already does (`:45-50`, which reads
the return code nowhere). `accounts_cli.is_ignored`'s three-way dispatch exists
because it answers a **boolean about one path** and must distinguish "not
ignored" from "git declined", to avoid writing a secret into a tracked file.
Our caller asks **which of these paths are excluded**, and both non-answers
mean the same thing to it: name nothing. That is
`forge_vocabulary.repository_ignored`'s own stated reasoning (`:232-238`),
which is why its shape is the one mirrored.

`check=False` is written **explicitly** rather than left to the default. It is
the default, so this changes no behaviour — it makes the mutation visible at
the call site, so the lock in row 2 of the test table has a literal to flip.

`OSError` is caught and returns `set()` for the same reason the whole reading
never refuses: by the time it runs the subprocess has already executed and the
product is on disk (`undeclared_produces_state:2425-2429`). A missing `git`
must not convert a returned run into a crash.

**`--no-index` is deliberately NOT passed.** The default consults the index, so
a path that is already tracked is reported as not-ignored even when a rule
matches it. That is precisely the semantics this capability wants: a tracked
path is already in the history, so it is not a product the history never took.
`present_files` and `forge_vocabulary.repository_ignored` both take the default
too. No lock in the test table depends on this nuance — no fixture creates a
path that is both tracked and rule-matched — so it is recorded as a stated
design intent rather than an assumption a test rests on. See **Open Questions**.

### Decision D4: The paths reported are product-relative; only the question asked of git is repository-relative

**Choice**: `_step_wrote_ignored` joins `f"{name}/{path}"` for each entry of
`inside`, asks the helper about those joined strings, and maps the answer back
to the original product-relative entries, preserving `inside`'s order.
`wrote["ignored"]` therefore lists `Results/own/a.json`, never
`Method/Results/own/a.json`.

**Alternatives considered**: reporting the joined repository-relative paths;
stripping the `name/` prefix off git's answer with string surgery.

**Rationale**: the spec's scenarios state the reported spelling directly
("THEN it reports `Results/own/a.json` as ignored"), and a field that reads in
a different base from `inside` and `outside` — the two fields it sits beside —
would need explaining every time it is read. Mapping back by membership
(`[p for p in inside if f"{name}/{p}" in answered]`) rather than by stripping
avoids a second place where the join could be written wrong, and inherits
`inside`'s order for free.

The join is `"/"`, spelled literally, never `Path(name) / path`. `inside` is
always POSIX because `product_snapshot` records `relative.as_posix()`
(`:10645`), and `Path(name) / path` would emit backslashes on Windows.

### Decision D5: The consequence is a fifth constant on a new `ignoredNote` key, and the ledger strips prose keys by a named tuple

**Choice**:
- `STEP_WROTE_IGNORED`, a module-level constant beside `STEP_WROTE_OWN`
  (`:10674`), `STEP_WROTE_NOTHING` (`:10682`) and `STEP_WROTE_FOREIGN`
  (`:10689`), carrying its doctrine in their register.
- `wrote["ignored"]` is present on **every** run — an empty list when nothing
  is excluded, which the spec requires explicitly ("present and empty, not
  absent").
- `wrote["ignoredNote"]` is present **only** when `ignored` is non-empty.
- `WROTE_PROSE_KEYS = ("note", "ignoredNote")`, and `:16821` becomes
  `if key not in WROTE_PROSE_KEYS` instead of `if key != "note"`.

**Alternatives considered**: appending the sentence to the existing `note`;
adding a fifth `status` value; nesting `{"paths": [...], "note": ...}` under
`ignored`; leaving `:16821` alone and letting the prose into the ledger.

**Rationale**: `note` is bound to `status` and asserted by identity at
`:36336`; appending to it would break that binding and make one string answer
two questions. A fifth `status` value is refused by the proposal and by the
existing `own` assertions (`:36303-36308`). A nested `note` would slip past
`:16821`'s top-level strip and land in the ledger, which is exactly what the
existing assertion at `:36350-36351` objects to — "a constant sentence repeated
into every ledger line". Leaving `:16821` alone has the same defect one step
more directly.

Splitting field-always / prose-when-it-fires follows both doctrines at once.
`_step_wrote`'s docstring says the reading is "Published on every run, in all
four states, so a reader learns what the check watches rather than meeting it
only when it has something to say" — that is about the **field**, and the field
is always published. Every `*_CONSEQUENCE` sibling in this file appears only
beside a finding (`PILOT_UNMEASURABLE_CONSEQUENCE` at `:11107`,
`PLACEMENT_UNDECLARED_CONSEQUENCE` at `:11408`) — that is about the **prose**,
and the prose fires with the fact.

`WROTE_PROSE_KEYS` is a named tuple rather than a suffix test
(`key.endswith("Note")`). A suffix test is a guard-shaped string comparison,
which is the thing `_owns`'s own docstring refuses (`:10659-10663`); the tuple
is a roster, and a key added to `wrote` without being classified is visible.

**Two constraints the constant's text must satisfy**, both derived from locks
already on disk:

1. **It must not contain the word "proposal", in any case.**
   `test_l1_residue_pin_equals_the_measured_s0_baseline_minus_its_one_recorded_shrink`
   (`tests/test_implementation_domain_lock.py:879-894`) pins
   `len(re.findall(r"\bproposal\b", source, re.IGNORECASE))` over
   `implementation_engine.py` at `L1_EXPECTED_COUNT` = 97 − 3 + 2 = **96**. One
   new occurrence, even in a docstring, reddens it. The pin measures
   `skills/_core/implementation/engine/**/*.py` (`_engine_files`, `:114-115`),
   so `impl_gitops.py` is outside it — the constraint is still applied to both
   files, because the word buys nothing there either.
2. **It must borrow no target vocabulary.** `leaks_in` derives its denylist
   from the target's own module basenames, so a plausible-sounding noun can
   redden the forge from a direction the author cannot see. Row 7 of the test
   table asserts it, following the measured precedent at `:36705-36717`.

Register, matching `STEP_WROTE_FOREIGN`: state the defect, state that it was
found only by hand, name both explanations, and say the reading never repairs
either. Draft (wording is `sdd-apply`'s to finish; identity is what the test
asserts):

> this run wrote paths under the roots this step declares that the
> repository's own ignore rules exclude, so they will not enter the history:
> the declaration reads satisfied, the run reports `outcome: "returned"`, and
> the product is absent from every clone but this one — found today only by
> somebody going looking for a file that was never committed. Either the
> ignore rule reaches further than it was written to, or this product belongs
> somewhere the repository keeps. Both are the target's to decide; this
> reports what is excluded and never repairs it.

### Decision D6: Deletions are carried through with no existence guard anywhere

**Choice**: neither the helper nor `_step_wrote_ignored` consults the
filesystem. No `Path.exists()`, no `is_file()`, no filtering of any kind
between `inside` and the question asked of git.

**Alternatives considered**: skipping paths that no longer exist, on the theory
that git cannot answer about an absent file.

**Rationale**: `changed_paths` counts removals by construction (`:10649-10653`,
"A removal counts: a step that deletes a neighbour's result has written into
that neighbour's tree exactly as surely as one that overwrites it"), so `inside`
already contains deleted paths. `check-ignore` matches path patterns and does
not stat the filesystem, so it answers for them. An existence guard would
silently drop the half of the input the incident is most likely to live in — a
step that removes a product it was told to produce. Row 5 of the test table is
the lock; nothing else in the table would survive its absence being noticed,
because nothing else deletes.

### Decision D7: Two documentation surfaces, not one

**Choice**: amend both `SKILL.md:3014`'s `step` row **and** the `wrote`
paragraph in `skills/proposal-implementation/references/usage.md:2275-2290`.

**Alternatives considered**: `SKILL.md:3014` alone, as the proposal's Affected
Areas table lists.

**Rationale**: this is a disk finding the proposal did not have.
`SKILL.md:3014` is the enumeration of sub-keys by name — "`status`
(`own`/`nothing`/`foreign`/`undeclared`), the `declared` roots, the `inside`
and `outside` paths, and a note" — and it is what the spec's last requirement
names. But `usage.md:2275-2290` carries the longer narrative of the same
reading, including "The same block, minus its constant note, is written into
the terminal ledger event", and a reader consulting it after this ships would
learn nothing about the new field. The correction that reaches `SKILL.md` and
stops is a shape this repository has already measured once. The `usage.md`
edit is roughly three lines and is listed as its own task.

**Neither edit is enforced by a derived guard, and that is stated rather than
assumed.** `returned_keys(ENGINE, "cmd_step")` reads only **top-level** keys of
the returned dict; this change adds no top-level key, so
`test_the_returned_response_dict_never_gains_suite_digest`
(`:30172-30173`) and the `returned_keys` shape it locks are untouched.
`VerifyStatusRosterTests.test_the_contract_names_every_status_verify_reports`
(`:16479-16487`) derives from `cmd_verify`, which this change does not touch at
all. There is no equivalent guard for `cmd_step`'s sub-keys. **Both
documentation edits are tasks, not tests.**

## Data Flow

```
cmd_step
  │
  ├─ before_product = product_snapshot(target, name)      :16765
  ├─ run_step(...)  ── subprocess ──► target's own venv   :16790
  │
  ├─ wrote = _step_wrote(produces, before, after)         :16808   [pure]
  │            └─► {"status", "declared", "inside", "outside", "note"}
  │
  ├─ ignored = _step_wrote_ignored(target, name,          :16809   [NEW]
  │                                wrote["inside"])
  │      │
  │      ├─ inside == []  ──────────────────────────────► []      (no subprocess)
  │      ├─ join:  "Results/own/a.json" → "Method/Results/own/a.json"
  │      ├─ impl_gitops.repository_ignored(target, joined)
  │      │        └─ git check-ignore --stdin -z  (cwd=target, check=False)
  │      │             exit 0 → stdout        exit 1/128/OSError → set()
  │      └─ map back, preserving `inside` order ────────► ["Results/own/a.json"]
  │
  ├─ wrote["ignored"]     = ignored                       :16809+  [NEW]
  ├─ wrote["ignoredNote"] = STEP_WROTE_IGNORED if ignored else absent
  │
  ├─ event["wrote"] = {k: v for k, v in wrote.items()
  │                    if k not in WROTE_PROSE_KEYS}      :16821   [MODIFIED]
  ├─ append_event(ledger_path, event)                     :16823
  └─ return {..., "wrote": wrote, ...}                    :16832
```

Both surfaces are fed by the one local dict. The ledger carries the **fact**
(`ignored`) and not the **prose** (`ignoredNote`); the return carries both.

## File Changes

| File | Action | Description |
|---|---|---|
| `skills/_core/implementation/impl_gitops.py` | Modify | New `repository_ignored(target, paths) -> set[str]` with its docstring, placed after `present_files` (`:23-50`) and before `text_files` (`:53`) |
| `skills/_core/implementation/engine/implementation_engine.py` | Modify | `STEP_WROTE_IGNORED` after `STEP_WROTE_FOREIGN` (`:10695`); `WROTE_PROSE_KEYS`; `_step_wrote_ignored` after `_step_wrote` (`:10719`); import `repository_ignored` at `:61`; wiring at `:16809`; strip change at `:16821`; `_step_wrote`'s docstring |
| `skills/proposal-implementation/SKILL.md` | Modify | The `step` row's `wrote` sub-key enumeration (`:3014`) names `ignored` and `ignoredNote`, says it is computed over `inside` only, and says the ledger carries the paths without the prose |
| `skills/proposal-implementation/references/usage.md` | Modify | The `wrote` paragraph (`:2275-2290`) gains the same fact in its own narrative register (D7) |
| `tests/test_proposal_implementation.py` | Modify | `StepWriteScopeTests` (`:36213`): `_box` gains a keyword-only `ignore=` with the current default; two step functions added to the embedded `steps.py`; six or seven new tests |
| `tests/forge_vocabulary.py` | **None** | Shape mirrored, never imported |
| `implementations/**` | **None** | Read-only |

## Interfaces / Contracts

```python
# skills/_core/implementation/impl_gitops.py
def repository_ignored(target: Path, paths: list[str]) -> set[str]:
    """Which of `paths` this repository declares it does not ship.

    `paths` are repository-relative, POSIX-spelled, and asked in ONE batch.
    Returns the subset git names, verbatim as supplied.

    Never raises, never refuses, and deliberately does not route through
    `git()` above: that helper raises `GIT_FAILED` on any non-zero exit, and
    `check-ignore` exits 1 when nothing matched and 128 outside a work tree.
    Both mean the same thing to a caller asking which paths to drop, so the
    return code is not read at all -- a non-zero exit carries no output and
    the parse below yields the empty set on its own. An empty `paths` spawns
    nothing.
    """
```

```python
# skills/_core/implementation/engine/implementation_engine.py
def _step_wrote_ignored(target: Path, name: str, inside: list[str]) -> list[str]:
    """Which of this run's own written products the repository will not take.

    `inside` is product-relative and the ignore rules are repository-relative,
    so the product name is joined on before the question is asked and the
    answer is mapped back -- the reported spelling stays `inside`'s, in
    `inside`'s order, because a field beside `inside` and `outside` that read
    in a different base would need explaining every time it is read.

    Computed over `inside` alone: `outside` is already the strongest reading
    this skill gives for the other half. No existence guard anywhere -- a
    removal counts as a write (`changed_paths`), and `check-ignore` matches
    patterns rather than the filesystem, so a deleted path still gets a real
    answer.
    """
```

Shape of the returned block:

```jsonc
"wrote": {
  "status": "own",                          // unchanged, never a fifth value
  "declared": ["Results/own"],
  "inside": ["Results/own/a.json"],
  "outside": [],
  "ignored": ["Results/own/a.json"],        // NEW: always present, [] when clean
  "note": "<STEP_WROTE_OWN>",               // stripped for the ledger
  "ignoredNote": "<STEP_WROTE_IGNORED>"     // NEW: only when `ignored` is non-empty;
}                                           //      stripped for the ledger
```

## Testing Strategy

The house rule: **choose the mutation a weaker lock would survive.** Every row
names its mutation and why the rest of the table survives it. All tests live in
`StepWriteScopeTests` (`tests/test_proposal_implementation.py:36213`) and reuse
`_box`/`_entry`/`_run`/`_wrote` (`:36235`/`:36285`/`:36291`/`:36298`) rather
than rebuilding a git fixture.

### The fixture change, and why it is the design decision in this section

`_box` hand-writes three **unanchored** rules (`__pycache__/`,
`.ipynb_checkpoints/`, `.implementation/`, `:36271-36273`) before `git add -A`
(`:36280`) — so an ignored product path is never tracked, which is the incident
exactly. `_box` gains one keyword-only parameter with a default:

```python
def _box(self, suffix, steps, *, ignore=("__pycache__/", ".ipynb_checkpoints/",
                                          ".implementation/")):
```

A default keeps the six existing calls byte-identical — the one place in this
change where the prior lesson about defaults genuinely applies.

**The rule the new fixtures pass must be product-anchored (`/Method/Results/own/`).**
An unanchored `Results/own/` matches at any depth, so it matches the
**product-relative** `Results/own/a.json` at the repository root just as well
as the correctly joined `Method/Results/own/a.json`. A fixture written that way
passes with the product-name join deleted, which is the single silent false
negative this change can ship. The leading slash anchors the rule to the
repository root, so only the joined path can match it.

### The locks

| # | Lock | The mutation a weaker test survives | What the test does |
|---|---|---|---|
| 1 | **The path base is repository-relative** | **Delete the `f"{name}/"` join** in `_step_wrote_ignored`. A fixture whose rule is the unanchored `Results/own/` still matches the unjoined product-relative path, so the mutation passes and the field still fills. | `_box(ignore=(..., "/Method/Results/own/"))`, step `write_own`. Assert `wrote["ignored"] == ["Results/own/a.json"]` **and** `wrote["status"] == "own"` (the parallel field, not a fifth status). Docstring states the anchored-rule reasoning so nobody "simplifies" the rule later. |
| 2 | **Non-zero exit means nothing ignored** | **Flip `check=False` to `check=True`**, or route through `impl_gitops.git()`. Row 1 never sees exit 1, so it survives. | Default `_box` ignore set, step `write_own` over the tracked `a.json`. Assert `proc.returncode == 0`, `wrote["ignored"] == []`, `wrote["status"] == "own"`, and `assertNotIn("ignoredNote", wrote)`. This is the only row that exercises exit 1. |
| 3 | **The check exists at all** | Delete the call. Row 2 alone survives (an empty field and an absent one are both falsy to a weak assertion). | Rows 1 and 2 together; neither alone is a lock. Row 2 asserts the key is **present** and equal to `[]`, never merely absent. |
| 4 | **The reading is durable** | **Compute it and add it to the return only**, after the event dict is built at `:16822`. Rows 1-2 read CLI stdout and survive. **Second mutation**: carry the prose into the ledger by leaving `:16821` at `key != "note"`. | Row 1's fixture; read `Method/.implementation/position.jsonl`, take the terminal event. Assert `terminal["wrote"]["ignored"] == ["Results/own/a.json"]` and `assertNotIn("ignoredNote", terminal["wrote"])`. Mirrors `:36338-36351`. |
| 5 | **The consequence prose is real** | **Replace the constant's text with `""`.** A test asserting `assertIn("ignoredNote", wrote)` survives. | Row 1's fixture; `assertEqual(wrote["ignoredNote"], impl.STEP_WROTE_IGNORED)`, by identity against the module constant, exactly as `:36336` does with `PRODUCES_UNDECLARED_CONSEQUENCE`. |
| 6 | **Removals are checked, not dropped** | **Add an existence guard** (`if (product / path).exists()`). Rows 1-5 all write files that exist afterwards, so every one of them survives. | New step function `delete_own` in the embedded `steps.py`; `_box(ignore=(..., "/Method/Results/own/"))` so the pre-created, mtime-zeroed `a.json` is ignored and untracked. Assert `wrote["ignored"] == ["Results/own/a.json"]` with the file gone from disk. |
| 7 | **Scope is `inside` only** | **Compute over `changed` instead of `inside`.** Every other row's step writes only inside its declared root, so all of them survive. | `_box(ignore=(..., "/Method/Results/neighbour/"))`, step `write_neighbour`. Assert `status == "foreign"`, `outside == ["Results/neighbour/b.json"]`, and `ignored == []`. |
| 8 | **The prose borrows no target vocabulary** (repo convention, not spec-derived) | Writing a target's word into forge prose. Nothing else in this table reads the constant's content. | `assertEqual(leaks_in(impl.STEP_WROTE_IGNORED), [])`, following the measured precedent at `:36705-36717`. Cheap; listed last because it locks a standing repository instruction rather than a spec requirement. |

### Layers

| Layer | What to Test | Approach |
|---|---|---|
| Unit | `leaks_in` over the constant (row 8); constant identity (row 5) | Direct attribute reads off `impl` |
| Integration | Every path reading (rows 1, 2, 6, 7) | Real CLI subprocess against a real git fixture — the class's existing shape |
| E2E / durability | The ledger event (row 4) | Read `position.jsonl` back off disk after the run |

### Execution discipline

- **RED before GREEN** (`strict_tdd: true`, `openspec/config.yaml:1`).
- `PYTHONDONTWRITEBYTECODE=1` and `__pycache__` purged before each RED run: a
  same-size mutation otherwise reuses a stale `.pyc` and the mutated source
  never runs.
- Both suites: `npm run test:all` (`test:node` then `test:py`), never one
  alone.
- `git diff --stat` does not prove a mutation landed — assert the anchor
  changed before reading the red.

## Threat Matrix

This design adds a subprocess and a git invocation, so the matrix applies.

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | `requirements.txt`, `CMakeLists.txt`, executable Markdown, `README.sh` | **N/A** — nothing here classifies, executes, or branches on a path's name or suffix. Every path in `inside` is treated identically; the only consumer is `check-ignore`, which reads patterns. | — | — |
| Git repository selection | `git -C`, relative paths, absolute paths | **Applicable** | The repository is selected by `cwd=target` on the `subprocess.run`, never by `-C`, never by a path composed into an argument, and never from the current working directory — `target` is the value `cmd_step` already resolved and already used for `product_snapshot` and `suite_digest`. Paths reach git only through `--stdin`, so no path can be read as an option. `128` (outside a work tree) degrades to "nothing ignored" rather than raising; `cmd_step` cannot reach it, because `DIRTY_WORKTREE` already refuses before anything spawns (`cmd_step`'s own docstring, `:16596-16598`), which presupposes a work tree. | Row 1 proves the answer comes from the box's rules, not the forge's, by using a rule that exists only in the box (a nested repository inside `FORGE/implementations/`, which the forge itself ignores). Row 2 proves exit 1 does not raise. |
| Commit state | staged, `commit -a`, empty index | **Applicable (read-only)** | Nothing stages, commits, or writes anything to git. `check-ignore` is a query. The default (index-consulting) behaviour is deliberate and stated in D3: a tracked path is already in the history and is correctly reported as not-ignored. | Row 2 runs against a **committed, tracked** product and must report empty; rows 1 and 6 run against an **untracked, ignored** product and must report it. The pair covers both index states the capability distinguishes. |
| Push state | tracking branch, first push, explicit refspec | **N/A** — nothing here reaches a remote, resolves a ref, or reads a tracking branch. | — | — |
| PR commands | explicit `--head`, environment prefix, composed commands | **N/A** — no PR automation, and the argument vector is a fixed four-token list with every variable path delivered on stdin. | — | — |

## Migration / Rollout

No migration. The field is computed per run and appended to an append-only
ledger, so events written before this lands simply lack the key — the same
shape a pre-change event already has, which `_step_verdicts` (`:10722`) already
tolerates. No target declaration changes and no new `__steps__` key, so no
target needs migrating; `STEP_KEYS` (`:11256-11257`) is untouched, which is
what keeps `KitDemandsEveryStepKeyTests` (`:37116-37144`, derived from
`STEP_KEYS`) out of this change entirely. A target that never runs a step after
this lands is byte-identical either way.

Rollback: remove `STEP_WROTE_IGNORED`, `_step_wrote_ignored`, the two wiring
lines, the `ignoredNote` entry from `WROTE_PROSE_KEYS`, the helper in
`impl_gitops.py`, and the two documentation edits. Nothing persists that a
rollback strands.

**Delivery**: one slice, ~150-250 authored changed lines, under the 400-line
budget. Do not plan a chain.

## Citations re-verified

Every location this design cites was read off disk on 2026-09-26. Two
statements in the inherited artefacts did not survive that reading:

1. **The launch brief's "~existing tests that call `_step_wrote` directly"** —
   the count from disk is **zero**. `rg '_step_wrote'` over the repository
   returns two source hits total: the definition (`:10698`) and the single call
   in `cmd_step` (`:16808`). Every test of this behaviour drives the CLI as a
   subprocess. This changed how D1 is argued (the ripple count decides nothing;
   the purity boundary decides everything) without changing its ruling.
2. **The proposal's Affected Areas table names `SKILL.md` as the only
   documentation surface** — `references/usage.md:2275-2290` carries a second,
   narrative enumeration of the same `wrote` reading, including the ledger
   sentence. D7 adds it. The proposal's row is incomplete rather than wrong.

Two further citations are imprecise but not wrong, and are recorded so nobody
re-derives them: `present_files`'s `check-ignore` call is at
`impl_gitops.py:45-48` (the launch brief says `:45-46`), and
`VerifyStatusRosterTests` opens at `tests/test_proposal_implementation.py:16436`
with the guard method at `:16479-16487` (the proposal cites the method range,
which is correct).

Everything else verified exactly as cited: `changed_paths:10649-10655`,
`_owns:10658-10670`, `STEP_WROTE_OWN:10674`, `STEP_WROTE_FOREIGN:10689-10695`,
`_step_wrote:10698-10719`, `PRODUCES_UNDECLARED_CONSEQUENCE:2396-2406`,
`undeclared_produces_state:2409` with its doctrine at `:2425-2429`,
`cmd_step`'s `_step_wrote` call at `:16808`, the ledger strip at `:16821`, the
return at `:16832`, `STEP_KEYS:11256-11257`, `SKILL.md:3014`,
`forge_vocabulary.repository_ignored:220-250`, `accounts_cli.is_ignored:160-177`,
`StepWriteScopeTests:36213` with `_box:36235`, the `own` assertions at
`:36303-36308`, the ledger test at `:36338-36351`, the identity assertion at
`:36336`, and `KitDemandsEveryStepKeyTests:37116`.

One lock the inherited artefacts did not name at all: the `\bproposal\b`
occurrence pin over the engine file
(`tests/test_implementation_domain_lock.py:833-894`, currently **96**). See D5,
constraint 1.

## Open Questions

- [ ] **None blocking.** The one question the proposal deferred (D1) is ruled
      above.
- [ ] Non-blocking, for `sdd-apply` to confirm cheaply while the fixture is in
      hand: that `check-ignore`'s default index-consulting behaviour reports a
      **tracked** path as not-ignored even when a rule matches it (D3). No lock
      in the test table depends on it — row 2's tracked product is matched by no
      rule, so it exercises exit 1 either way — but if the observed behaviour
      differs, D3's stated rationale for omitting `--no-index` should be
      corrected in place rather than left as an unverified claim.

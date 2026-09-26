# Proposal: The Product the History Never Took

## Intent

**Problem.** A `__steps__` entry declares what it writes under `produces`. That declaration is
validated for shape (`cmd_step`, `implementation_engine.py:16726-16742`), reported when absent
(`undeclared_produces_state`, `:2409`, surfaced as `verify`'s `undeclaredProduces`,
`SKILL.md:2799`), and compared against what the run actually wrote (`_step_wrote`, `:10698-10719`).
**Nothing compares any of it against `.gitignore`.**

So a step can declare `Results/own`, actually write `Results/own/a.json`, and have the repository
ignore it. `_step_wrote` reports `status: "own"` with `inside: ["Results/own/a.json"]` — the
strongest reading this skill can give — the run reports `outcome: "returned"`, the declaration
reads satisfied, and the artifact never enters history. Nobody finds out until someone goes
looking for a file that was never committed.

This is the same shape as the incident `STEP_WROTE_FOREIGN` already exists for, stated in that
constant's own words: a run "reported as `outcome: \"returned\"` and caught only by a digest
compared by hand" (`:10692-10693`). The difference is that `foreign` was closed and this was not.

**Why now.** The repository already applies this insight by hand, twice, in the one file whose
whole job is declaring what does not ship. `.gitignore:119-124` cross-references the `guidance/*/*`
rule by name:

> Listas de trabajo sobre el corpus: que papers quedan afuera y por que. Son
> decisiones de investigacion sobre UN paper, no doctrina de la forja, asi que
> siguen la regla de DEUDA-*.md. Por clase y no por nombre, la misma razon que
> `guidance/*/*` ya declara: una regla escrita nombrando lo que existia ese dia
> no alcanza a lo que nace despues, y la primera lista nueva se publicaria.

The author reasons this way and writes it out by hand. Nothing derives it, and nothing checks the
inverse direction: a rule written for what existed that day can also *over*reach, and swallow a
product a step was told to produce. The hand-applied insight has no machine partner.

**What success looks like.** A step whose declared, written product the repository has been told to
ignore says so, on the run that wrote it, in the same block that already says who owns it — and
says it durably, in the ledger, not once on stdout.

## Scope

### In Scope

- A new helper in `skills/_core/implementation/impl_gitops.py` that asks git which of a given set
  of paths the repository declares it does not ship. Batch `check-ignore --stdin -z`, explicit
  `paths` + `root` parameters, non-zero exit read as "nothing ignored".
- An `ignored` field on the `wrote` block, computed over `wrote["inside"]` — the paths the run
  **actually wrote** under its declared roots, not the declared roots themselves.
- One new consequence constant beside `STEP_WROTE_OWN` / `STEP_WROTE_FOREIGN` /
  `PRODUCES_UNDECLARED_CONSEQUENCE`, carrying the doctrine prose those siblings carry.
- The reading reaches both surfaces `wrote` already reaches: `cmd_step`'s return (`:16832`) and the
  terminal ledger event (`:16821`).
- The `step` row of the Output Contract table (`SKILL.md:3014`), which today enumerates `wrote`'s
  sub-keys as "`status` (`own`/`nothing`/`foreign`/`undeclared`), the `declared` roots, the
  `inside` and `outside` paths, and a note".
- Tests, RED before GREEN, each mutation chosen so a weaker lock would survive it (below).

### Out of Scope

- **Refusing.** This reading reports and never gates, and the reason is not a preference:
  `undeclared_produces_state`'s own docstring (`:2425-2429`) gives it. "Every fail-closed refusal in
  this skill guards an act the engine is about to take. This one grades an act already taken: the
  subprocess has run, the product is on disk, and the time is spent." That argument applies to this
  reading verbatim — it is computed at `:16808`, after `run_step` returned. A refusal here would
  discard the run's own verdict.
- **The `outside` paths.** A foreign write is already the strongest reading `_step_wrote` gives;
  adding "and also ignored" to a block that already fired changes no decision. The incident is
  about a step's OWN product, declared and produced and lost.
- **A new top-level `verify` status.** Checking declared roots statically is less faithful (a
  content-only rule like `Results/*` does not match the bare root `Results/own`, so a real
  incident reads clean), and it trips `VerifyStatusRosterTests.test_the_contract_names_every_status_verify_reports`
  (`tests/test_proposal_implementation.py:16479-16487`), which derives `returned_keys(ENGINE,
  "cmd_verify")` from source and demands a matching SKILL.md row per top-level key.
- **A new `__steps__` declaration key.** Reusing `produces` is what keeps
  `KitDemandsEveryStepKeyTests` (`:37116`, derived from `STEP_KEYS`) out of this change entirely.
- **Importing `tests/forge_vocabulary.repository_ignored`.** It is exactly the right shape
  (`:220-250`) and it is test-only; importing it into `skills/_core/` inverts the dependency
  direction. Mirror its shape, including its exit-code reasoning; do not import it.
- **`present_files`'s existing call** (`impl_gitops.py:45-46`). It globs the whole tree itself and
  takes no `paths` parameter, so it cannot answer a targeted question. Leave it alone.
- Anything under `implementations/`.

## Capabilities

### New Capabilities

- `implementation-product-shipped`: the cross-check between what a step declared, wrote and owns,
  and what the repository declares it does not ship — its report-never-refuse standing, the paths
  it is computed over, and the surfaces it reaches.

### Modified Capabilities

- None. No capability currently in `openspec/specs/` states behaviour this change alters.

## Approach

**The seam is `_step_wrote`, and the reason is the false negative.** It already holds
`before_product`/`after` snapshots and computes `wrote["inside"]`: the exact, real paths this run
wrote under its declared roots. Asking `check-ignore` about *those* cannot produce the false
negative that asking about a bare declared root would — a rule written `Results/*` matches
`Results/own/a.json` and does not match `Results/own`. Real paths, real answer. It needs no re-run,
and it trips neither guard named above.

**The path base is the trap, and it is not cosmetic.** `changed_paths` returns **product-relative**
paths (`:10649-10655`, and the fixture asserts `["Results/own/a.json"]`, not
`["Method/Results/own/a.json"]`). `check-ignore` answers about paths relative to the repository
root. So the helper must be given repo-relative paths — the product name joined on — and
`_step_wrote(declared, before, after)` currently has neither `target` nor `name` in scope. Either
it gains them or the computation happens at the `cmd_step` call site where both already are. That
is a design decision, not a product one; `sdd-design` picks the shape.

**A parallel field, never a fifth `status` value.** A run can be both `own` and ignored — those are
answers to different questions, and collapsing them into one enum would destroy the `own` reading
the existing tests assert exactly (`:36303-36308`). `ignored` sits beside `inside`/`outside`.

**The exit-code trap, named here so it is not discovered in review.** `git check-ignore` exits
**1 when nothing matched** and 128 outside a work tree. A naive `check=True`, or a `try/except`
around a raising call, reads "nothing is ignored" as a failure. Both existing correct call sites
say so in their own words — `forge_vocabulary.repository_ignored` at `:235-238` ("`check-ignore`
exits 1 when nothing matched and 128 outside a work tree, and both mean the same thing to a caller
asking which paths to drop") and `accounts_cli.is_ignored` at `:175-177` ("0 = ignored, 1 = not
ignored, anything else ... is git declining to answer, not evidence of exposure"). The new helper
must read non-zero-with-no-output as *nothing ignored*.

**A deletion is a change, and `check-ignore` still answers for it.** `changed_paths` counts
removals (`:10650-10653`). A deleted path no longer exists on disk; `check-ignore` matches path
patterns rather than inspecting the filesystem, so it answers anyway. Stated so nobody adds an
existence guard that silently drops half the input.

## Test strategy — the mutation each lock must not survive

The house rule is stronger than inverting a line: choose the mutation a **weaker** lock would
survive, and name it per lock.

| Lock | The mutation a weaker test survives | What the test must therefore do |
|---|---|---|
| The path base is repo-relative | **Drop the product-name join.** A fixture whose rule is written `Results/own/` STILL matches the product-relative `Results/own/a.json` at the repo root, so the mutation passes. | Anchor the fixture rule to the product folder (`/Method/Results/own/`) so a product-relative path cannot match it. This is the single most important test-design decision in the change. |
| Non-zero exit means nothing ignored | **Flip `check=False` to `check=True`.** A test that only ever exercises an ignored path never sees exit 1, so it survives. | Exercise the clean case explicitly — a written, declared, *tracked* product must report an empty `ignored` and not raise. |
| The check exists at all | Delete the call. A test that only exercises the clean case survives. | Both cases are required; neither alone is a lock. |
| The reading is durable | **Compute it and drop it from the ledger event.** A test reading only CLI stdout survives. | Assert it in `.implementation/position.jsonl`'s terminal event, mirroring `test_the_reading_is_written_into_the_terminal_ledger_event` (`:36338-36351`). |
| The consequence prose is real | **Replace the constant's text with `""`.** A test asserting `"ignored" in wrote` survives. | Assert identity against the module constant, as `test_a_step_declaring_no_roots_is_graded_against_nothing` does with `impl.PRODUCES_UNDECLARED_CONSEQUENCE` (`:36336`). |

**Reuse the fixture; do not rebuild it.** The `wrote`-scope class's `_box()` helper
(`:36271-36283`) already initialises a real git repository, hand-writes a `.gitignore`
(`__pycache__/`, `.ipynb_checkpoints/`, `.implementation/`) and commits it. `_entry()` (`:36285`),
`_run()` (`:36291`) and `_wrote()` (`:36298`) are directly reusable. Note that `_box` writes the
`.gitignore` *before* `git add -A`, so a newly ignored product path is simply never tracked — which
is the incident, exactly.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `skills/_core/implementation/impl_gitops.py` | Modified | New targeted ignore helper + docstring |
| `skills/_core/implementation/engine/implementation_engine.py` | Modified | `_step_wrote` gains `ignored`; new consequence constant; `cmd_step` wiring at `:16808`/`:16821`/`:16832` |
| `skills/proposal-implementation/SKILL.md` | Modified | The `step` row's `wrote` sub-key enumeration (`:3014`) |
| `tests/test_proposal_implementation.py` | Modified | 3-4 tests in the existing `wrote`-scope class |
| `tests/forge_vocabulary.py` | **None** | Shape mirrored, never imported |
| `implementations/**` | **None** | read-only |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| The product-relative/repo-relative confusion ships as a silent false negative | **High if unnamed** | Named above as the primary mutation; the fixture rule must be product-anchored so the mutation cannot pass |
| `check=True` reads "clean" as a crash | Medium | Both correct precedents quoted in the approach; the clean-case test is mandatory, not optional |
| Line numbers in this engine move between proposal and apply | High | Every citation here was re-verified against disk on 2026-09-26; `sdd-apply` must re-verify rather than trust them |
| `_step_wrote`'s signature change ripples to other callers | Low | `cmd_step:16808` is its only call site in the engine; confirm before editing |
| Doc row drifts from the returned keys | Medium | No derived guard binds `cmd_step`'s sub-keys to `SKILL.md:3014` (unlike `cmd_verify`'s). The row is a hand-kept claim; keeping it is a task, not a test |
| A target whose product folder is legitimately ignored now reports on every step | Low | Report-only by design; it names a real fact and gates nothing |

## Rollback Plan

Revert the `ignored` key from `_step_wrote`'s returned dict, the consequence constant, the helper in
`impl_gitops.py`, and the `SKILL.md` row text. Nothing persists that a rollback strands: the field
is computed per run and written into an append-only ledger, so older events simply lack the key —
the same shape a pre-change event already has, which `_step_verdicts` already tolerates. No target
declaration changes, so no target needs migrating. A target that never ran a step after this landed
is byte-identical either way.

## Dependencies

- None. No target-side declaration, no new `__steps__` key, and no prior slice.

## Open Product Decisions

**None.** Every fork this proposal met was decided by doctrine already written in the repository
rather than by preference, and each is recorded above with the text that decides it: report-versus-
refuse by `undeclared_produces_state:2425-2429`; parallel field versus fifth status by the existing
`own` assertions at `:36303-36308`; `inside`-only scope by `STEP_WROTE_FOREIGN` already firing on
the other half. The one genuinely open question — whether `_step_wrote` gains `target`/`name` or the
computation moves to the call site — is an internal shape for `sdd-design`, not something the
operator is owed a ruling on.

## Review Budget Forecast

~150-250 authored changed lines (additions + deletions), **one slice, under the 400-line budget**.
Breakdown: helper + docstring ~20-30; engine wiring + consequence constant ~25-40; tests ~60-90;
docstring and `SKILL.md` updates ~20-30. The figure is above a naive estimate because this
repository's convention is that every constant and function carries its doctrine prose — the
sibling constants `PRODUCES_UNDECLARED_CONSEQUENCE` (`:2396-2406`, 11 lines) and
`STEP_WROTE_FOREIGN` (`:10690-10695`) are the measured precedent.

## Success Criteria

- [ ] A step whose declared, written product the repository ignores reports that fact on the run
      that wrote it, with `status` still reading `own`.
- [ ] A step whose declared, written product is tracked reports an empty `ignored` and does not
      raise — the exit-1 case is exercised, not assumed.
- [ ] The reading appears in the terminal ledger event, not only on stdout.
- [ ] The path base is proven repo-relative by a fixture rule anchored to the product folder, so
      dropping the product-name join fails the suite.
- [ ] The consequence constant is asserted by identity, not by key presence.
- [ ] `SKILL.md:3014`'s `wrote` enumeration names the new sub-key.
- [ ] RED before GREEN (`strict_tdd: true`, `openspec/config.yaml:1`); `PYTHONDONTWRITEBYTECODE=1`
      and `__pycache__` purged, since a same-size mutation otherwise reuses a stale `.pyc`.
- [ ] `npm run test:all` green — **both** suites (`test:node` then `test:py`), never one alone.

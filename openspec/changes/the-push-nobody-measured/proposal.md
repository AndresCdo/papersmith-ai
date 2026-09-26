# Proposal: the-push-nobody-measured

## Intent

The `pin-published` refusal prescribes a push, and nothing anywhere has ever measured whether
that push is viable.

`_verify_commit_reachable()`'s catch-all branch —
`skills/remote-execution/scripts/jobfolder.py:2579-2596` — appends the same remedy to every
failure it sees:

> `— push it to {repo_ref!r} on {repo_url!r} and pin the commit the remote actually received`

It appends it unconditionally: the branch catches `(JobFolderError, OSError)`, so a remote that
answered `not our ref`, a DNS failure, a proxy refusal and a scratch `git init` that could not
write all arrive at one sentence that tells the operator to push. Confirmed absent from the whole
skill: `rev-list`, `pack-objects`, `count-objects`, `cat-file --batch-check` return **zero hits**
under `skills/remote-execution/` — no code in this skill has ever asked how much a push would
carry.

**The precedent for the fix sits in the same function, one branch above.**
`except GitTimeoutError` (`jobfolder.py:2559-2578`) names **no remedy at all**, and its comment
says why:

> a timeout means the question could not be finished asking, which is NOT the same as the remote
> saying no, and is not, by itself, evidence the commit is unpublished

That branch exists because sharing one message with the branch below once let a
slow-but-successful fetch be reported as a confirmed refusal — *a true measurement producing a
false conclusion*. One branch is careful about attribution. The other is not. This change extends
the careful branch's discipline to its neighbour.

**Weight demonstrably matters here.** `PIN_PUBLISHED_TIMEOUT_SECONDS = 240.0`
(`jobfolder.py:2212`) is a separate constant from `GIT_TIMEOUT_SECONDS = 120.0`
(`jobfolder.py:2175`) precisely because a 12.4 MiB transfer took 209s once and 27s on an identical
re-run (`jobfolder.py:2194-2211`, restated in `tests/test_remote_execution.py:20498-20505`). An
operator told to push has no idea whether that costs a second or a quarter of an hour on this
link. When we can tell them, we should; when we cannot, we must not pretend the push is free.

## Scope

### In Scope

- **A local, byte-free weight reader** in `jobfolder.py`: how much the pin holds that the declared
  remote's *cached* tip does not. No network, no transfer, no push.
- **Its own timeout constant**, small, carrying its measurement in a comment the way
  `PIN_PUBLISHED_TIMEOUT_SECONDS` does (`jobfolder.py:2194-2212` is the shape).
- **A two-shape refusal for the catch-all branch** (`jobfolder.py:2579-2596`): measured → state the
  weight **and** the remedy; unmeasurable → state what is known and prescribe nothing, the shape
  the timeout branch already uses.
- **Two signature edits** so the weight reader can reach the repository:
  `_refuse_unpublished_pin` (`jobfolder.py:2847-2878`) currently discards `target` into
  `**_unused`, and `_verify_commit_reachable` does not take it. No call site changes —
  `verify_pin_preconditions()` (`jobfolder.py:3074-3084`) already passes `target=resolved_target`
  to every condition callable uniformly.
- **`SKILL.md`'s reachability-probe section** (`skills/remote-execution/SKILL.md:798-829`) gains the
  two shapes and says plainly that the weight is a floor read from a cache.
- **Tests**, RED before GREEN, reusing the fixtures named under *Test strategy* below.

### Out of Scope — recorded with reasons

- **No new `PIN_CONDITIONS` member.** The tuple (`jobfolder.py:2607-2608`) is untouched, so
  `PinConditionDoctrineTests` (`tests:12779`) and `PinConditionOrdinalGuardTests` (`tests:12951`)
  are satisfied by construction — **provided** every new sentence names the condition by its
  backtick id `` `pin-published` ``, never by position and never by spelling out how many members
  the tuple has. That guard scans `SKILL.md`, `jobfolder.py`, `remote_cli.py` *and the test file
  itself* (`tests:12986-12991`), so this constraint binds the new tests too.
- **No network call in the weight reader.** `_published_equivalent()` (`jobfolder.py:2958-3009`) is
  the only primitive in this codebase that asks the remote what it holds, and it does so with
  `ls-remote` (`:2993`). It is excluded. The weight reader contacts nothing.
- **No push, ever.** The remedy is reported, never performed. `SKILL.md:792-796` already commits
  this skill to never committing, pushing, staging, stashing, resetting or fetching into the
  operator's repository, and that stands.
- **No change to when the refusal fires.** An unpublished pin still refuses, with the same exit and
  the same condition. This change governs only what the refusal **says**.
- **No change to the `GitTimeoutError` branch** (`jobfolder.py:2559-2578`). It already has the right
  shape; it is the model, not the patient.

## Capabilities

### New Capabilities
None. The `remote-execution` skill has no capability spec under `openspec/specs/`; its pin
conditions are held by the suite and by `SKILL.md`'s doctrine table, not by an openspec spec.

### Modified Capabilities
None. No spec-level requirement changes — this is refusal wording plus a local measurement.

## Approach

### The split is on "could I measure?", never on "is it big?"

Inside the existing catch-all branch, before composing the message: attempt the local weight read.

- **Measurement succeeded** → the refusal states the weight *and* the remedy, exactly as today
  plus a number.
- **Measurement failed, for any reason** → the refusal states what is known (the remote could not
  serve the pin, git's own message carried forward) and prescribes nothing.

There is no size threshold anywhere. A measured 4 KiB and a measured 400 MiB both get the remedy;
what differs is that the operator can now see which one they are about to pay for.

### Three mechanical constraints, each already load-bearing

1. **`GitTimeoutError` subclasses `JobFolderError`** (`jobfolder.py:136`). Any wrapper-style catch
   added around this region must exclude it explicitly, or it will re-decorate the timeout branch
   and regress the exact defect that branch exists to prevent. The weight read is reached from the
   catch-all branch **only**.
2. **The weight reader fails silent.** Its own errors resolve to "unmeasurable" and never escape as
   a refusal of a different shape. A measurement helper that can raise a second kind of refusal has
   become a guard, and this is not one.
3. **Whatever text is raised reaches the operator byte-for-byte.** Both decision points —
   `generate_job()` (`jobfolder.py:1947-1964`) and `remote_cli.py::_gate_job_folder_pin()`
   (`remote_cli.py:790`, called from `cmd_submit` at `:1189`) — let `JobFolderError` propagate
   unwrapped to one stderr printer. Nothing reformats, truncates or parses it. Enrichment is
   therefore additive and safe; it is also unreviewed by any intermediary, so the wording is the
   whole product.

### Reaching the repository costs two signatures

`verify_pin_preconditions()` hands `target=resolved_target` to every condition callable in one
uniform keyword shape (`jobfolder.py:3074-3084`). `_refuse_unpublished_pin` already receives it and
throws it away into `**_unused` (`:2854`). Threading it through to `_verify_commit_reachable` is two
signature edits and no call-site rewrite. Thread it explicitly, the way `repo_credential_path` is
threaded and for the same stated reason (`jobfolder.py:2866-2870`): a parameter riding the catch-all
is a parameter a future signature edit can drop without anything noticing.

---

## Decision block — the anchor. Accept or change.

**The question exploration could not settle.** To measure how much is unpushed you need an anchor:
what the remote already has. The only primitive in this codebase that answers that is `ls-remote`
inside `_published_equivalent()` (`jobfolder.py:2993`) — a network call, excluded by the
no-network constraint. What remains is the local cache `refs/remotes/<name>/<branch>`, which records
what the remote had at the last fetch. Finding which local remote corresponds to `--repo-url` means
comparing URL strings, and those are fuzzy: `https://host/repo.git`, `https://host/repo`, and an SSH
form can all name one remote.

**Recommendation: match STRICTLY. Report unmeasurable whenever the match is not exact.**

*Reasoning.* A weight anchored on the wrong remote is a number that **looks** measured and is not —
worse than no number, because the operator has no way to tell the two apart. The split above already
makes "unmeasurable" a normal, well-handled outcome rather than a failure, so strict matching costs
us a well-formed message, not a broken one. Loose matching buys more measurements at the price of
occasionally lying with one. This repository has refused that trade before, on the same grounds: a
guard that can only be *sometimes* right is worse than an honest absence.

*What this costs, stated plainly.* The measurement will often be unavailable — any operator whose
remote is configured with a different URL spelling than the one they passed to `--repo-url`, and
every generation run from a clone with no matching remote at all, falls back to the careful wording.
**That is the intended trade, not a gap**, and the fallback message is a first-class outcome, not a
degraded one.

*The anchor is a cache, and the wording must say so.* `refs/remotes/<name>/<branch>` reflects the
last fetch, not the remote now. Someone else may have pushed since. The weight is therefore a
**floor** — "at least N commits / at least N bytes" — never an exact figure, and the sentence must
not claim more precision than the anchor can carry. Claiming an exact number from a cached ref would
be the same defect in a new costume: a true measurement licensing a false conclusion.

**Alternative, if the operator prefers it:** normalize URLs before comparing (strip `.git`, unify
scheme/host forms, map SSH to HTTPS). More measurements, at the risk that one of them is anchored on
a remote the operator did not name. Say so and the strict rule becomes the normalizing rule; nothing
else in this proposal changes.

---

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `skills/remote-execution/scripts/jobfolder.py:2579-2596` | Modified | The catch-all branch grows two message shapes |
| `skills/remote-execution/scripts/jobfolder.py` (new helper) | New | Local, byte-free weight reader; fails silent |
| `skills/remote-execution/scripts/jobfolder.py` (new constant) | New | The weight read's own small budget, with its measurement in the comment |
| `skills/remote-execution/scripts/jobfolder.py:2847-2878` | Modified | `_refuse_unpublished_pin` stops discarding `target` |
| `skills/remote-execution/scripts/jobfolder.py` (`_verify_commit_reachable` signature) | Modified | Accepts `target` |
| `skills/remote-execution/SKILL.md:798-829` | Modified | The probe section documents both shapes and the floor |
| `tests/test_remote_execution.py` | Modified | New locks, each proven reachable-red |
| `skills/remote-execution/scripts/jobfolder.py:2559-2578` | **Untouched** | The precedent branch |
| `PIN_CONDITIONS` (`jobfolder.py:2607-2608`) | **Untouched** | No new member |

## Test strategy

RED before GREEN, every unit; the local idiom holds — a lock that passes on its first run is proven
reachable-red by inverting the production line and watching it fail.

**Fixtures that already exist and are reused rather than rebuilt:**

- `PublishedPinResolutionTests.published_target()` (`tests/test_remote_execution.py:19558`) and
  `.commit_local_only()` (`:19578`) — a real `origin` with a pushed tip plus an unpushed local
  commit. *Correction to the exploration note: these two live on `PublishedPinResolutionTests`
  (`tests:19535`), not on `CommitDefaultTests` (`tests:13055`). Read from disk; cite the class that
  actually holds them.*
- `CommitReachabilityTests._real_repositories()` (`tests:11720`) — repositories with no configured
  remote, i.e. the unmeasurable path by construction.
- `PinPublishedTimeoutBudgetTests` (`tests:20492`) is the shape for the new budget's test: assert it
  is a distinct module constant, and assert only the intended call receives it.

**Additive enrichment is safe.** Existing tests assert only substrings of the refusal. Two of them
key on the prefix `"could not be confirmed reachable"` — `tests:12124` and `tests:19626` — so that
prefix is preserved verbatim and the new material is appended, never spliced ahead of it.

**Commands:** `npm run test:all` (`openspec/config.yaml:18`), with
`python3 -m unittest tests.test_remote_execution` as the fast inner loop. This repository has two
suites and running one has hidden a regression before.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A new catch re-decorates the timeout branch | **Med** | `GitTimeoutError` subclasses `JobFolderError` (`:136`); the weight read is reached from the catch-all branch only, and a test asserts the timeout refusal still names no remedy |
| The weight reader raises and becomes a second guard | Med | It fails silent into "unmeasurable" by contract; a test drives it against a repository where every primitive fails and asserts the refusal is the careful shape, not an error |
| New prose names the condition by position or spells out the tuple size | Med | `PinConditionOrdinalGuardTests` (`tests:12951`) scans all four files including the test file and fails the suite; write `` `pin-published` `` everywhere |
| The strict anchor makes the measurement rarely available | **High, and accepted** | This is the decision above, not a defect. The fallback wording is a first-class outcome |
| The cached floor is read as an exact figure by an operator | Low | The sentence says "at least", and `SKILL.md` states the anchor is the last fetch, not the remote now |
| The new budget number is invented rather than measured | Low | The constant carries its measurement in its comment, as `:2194-2211` does; if the measurement is not taken, the constant is not written |

## Rollback

One commit against `main`, reverting independently. Nothing is written to disk by this change — no
job folder field, no config key, no artifact — so there is no data to migrate back. Reverting
restores the unconditional remedy sentence exactly as it stands at `jobfolder.py:2579-2596`, and the
refusal's firing conditions never changed, so no job folder generated under either version differs.

## Success criteria

- [x] When the weight is measurable, the `pin-published` refusal states it **and** names the
      remedy. Observed true, with one wording note: this line's own "as a floor" phrasing is
      superseded by the operator's post-design ruling (Phase 0 of `tasks.md`), which also amended
      `spec.md` and `design.md` — the actually-specified and actually-implemented behavior states
      an **exact cache-relative count**, never a floor. The underlying criterion (weight stated,
      remedy kept) holds; only this line's specific word does not.
- [x] When it is not, the refusal states what is known and prescribes nothing — asserted against a
      repository with no matching remote.
- [x] The `GitTimeoutError` refusal still names no remedy and is byte-unchanged.
- [x] The weight reader makes no network call and transfers no bytes — asserted, not assumed.
- [x] The weight read has its own module constant, distinct from both `GIT_TIMEOUT_SECONDS` and
      `PIN_PUBLISHED_TIMEOUT_SECONDS`, and its comment carries the measurement it came from.
- [x] `PIN_CONDITIONS` is unchanged and the doctrine and ordinal guards are green.
- [x] `tests:12124` and `tests:19626` are green without edits.
- [x] `npm run test:all` is green, with every new lock proven reachable-red.
- [x] `SKILL.md`'s probe section documents both shapes and says the anchor is a cache.

## Review budget forecast

Measured estimate: ~40-60 lines in `jobfolder.py`, ~10-20 in `SKILL.md`, ~120-200 in tests —
roughly **200-300 authored lines (additions + deletions), one slice**. Under the 400-line per-PR
guard; no chaining needed. `400-line budget risk: Low`.

## Open question for the operator

One, and only one: **the anchor decision block above.** Accept the strict rule (recommended, with
its stated cost), or switch it to URL normalization. Everything else in this proposal is settled by
decisions already taken and by what was read from disk.

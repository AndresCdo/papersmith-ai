# Design: the-push-nobody-measured

## Technical Approach

The `pin-published` refusal's catch-all branch (`jobfolder.py:2579-2596`) gains one call, made
before the message is composed, to a new module-private reader that answers a single question
from state already on disk: **how far is the pin beyond the last state this clone recorded for
the declared remote?** The answer is a value object whose `measured` flag — never a count, never
a truthiness test — selects between the two refusal shapes the spec mandates.

Nothing else moves. `PIN_CONDITIONS` (`:2607-2608`) is untouched, the `except GitTimeoutError`
branch (`:2559-2578`) is byte-unchanged, and the reader is reached from the catch-all branch
only, so `GitTimeoutError`'s membership in `JobFolderError` (`:136`) cannot drag the timeout
message into the new behaviour. The reader contacts nothing: its whole vocabulary is
`git config`, `git rev-parse` and `git rev-list --count`, all local, all through the module's
single git composition point `_run_git()` (`:2231`).

Spec coverage: `specs/remote-execution-pin-published/spec.md`, all 13 requirements. Every
decision below is grounded in a line read from disk during this phase, and the three places
where the inputs disagree with disk are recorded under *Disagreements with disk*.

## Architecture Decisions

### Decision 1: The weight is a commit count. No byte figure is reported.

**Choice**: one `git rev-list --count <anchor>..<pin> --` invocation. The refusal states commits
and never bytes.

**Alternatives considered**:

| Rejected primitive | Why it was rejected, from disk |
|---|---|
| `rev-list --objects` piped into `cat-file --batch-check`, summed | `cat-file --batch-check` reads object names **on stdin**. `_run_git()` hardcodes `stdin=subprocess.DEVNULL` (`:2289`) and exposes no stdin/`input` parameter. Using it means either widening the module's single git seam — whose `stdin=DEVNULL` discipline is load-bearing and argued at `:2262-2276` — or opening a second, parallel subprocess path, which is exactly what `_verify_commit_reachable`'s own docstring rejects at `:2404-2409`. A cosmetic second unit is not worth either. |
| `pack-objects --stdout --revs` | Same stdin problem (`--revs` reads revisions on stdin), **plus** `_run_git()` passes `text=True` (`:2291`): a packfile on stdout would be fed to a UTF-8 decoder and raise `UnicodeDecodeError`, which is not a `JobFolderError` and not an `OSError`. It is also the one candidate whose cost scales with the answer — it performs the real delta compression — so the budget bounding it would have to cover the very thing it measures. On the change's own "byte-free" constraint: it transfers no *network* bytes, but it materialises a full pack locally, so it is byte-free only in the narrow sense and unbounded in the expensive one. Both readings fail. |
| `rev-list --objects --disk-usage <range>` (the one stdin-free byte route) | Reports **on-disk** size. Freshly committed objects are loose and individually zlib-compressed; a push sends a thin, re-delta'd pack. The same unchanged range therefore reports a different number before and after a `gc`, and the disk figure routinely exceeds the wire cost several times over. A number that moves while its subject does not is the defect class this change exists to extend, not to import. Secondary: it needs git ≥ 2.31 and this skill declares no git floor anywhere. |

**Rationale**: a commit count is exact about what it counts, needs no stdin, produces four bytes
of ASCII, and costs a history walk bounded by the new constant. Every byte figure available to
this module is either unreachable through the one git seam or dishonest about what a push would
actually carry. The spec permits an exact cache-relative count in either unit ("N commits" or
"N bytes"); this design takes the one it can state truthfully.

### Decision 2: Anchor resolution — `git config --local --get-regexp`, exact string match, ambiguity is unmeasurable

**Choice**, in three steps, each failing into *unmeasurable*:

1. `git config --local --get-regexp '^remote\..*\.url$'` in the target. One line per key,
   `remote.<name>.url <value>`; the remote name is the text between the `remote.` prefix and
   the `.url` suffix, the URL is everything after the first space.
2. Keep every entry whose value is **byte-identical** to `repo_url` — `==`, no strip, no
   normalisation, no case folding. **Zero matches → unmeasurable. Two or more matches →
   unmeasurable.** Exactly one match yields the remote name.
3. The anchor ref is `refs/remotes/<name>/<branch>`, where `<branch>` is `repo_ref` with a
   leading `refs/heads/` removed; a `repo_ref` that still begins with `refs/` after that removal
   is unmeasurable (a tag or an exotic ref has no general remote-tracking mirror). The ref is
   read with `git rev-parse --verify --quiet <ref>^{commit}` — which both proves it exists and
   yields the cached sha the message names.

**Alternatives considered**:

- `git remote -v` — rejected. Its output is human formatting (`<name>\t<url> (fetch)`), so the
  URL has to be recovered from between a tab and a parenthetical suffix, and it folds in
  `pushurl`, a different config key. `--get-regexp` returns the exact key the spec names
  ("that ref's configured remote URL"), one key per line, and its `\.url$` anchor excludes
  `remote.<name>.pushurl` by construction (the character before `url` there is `h`, not `.`).
- URL normalisation (strip `.git`, map SSH to HTTPS) — rejected by the proposal's accepted
  decision block. Not reopened here.
- **Ambiguity: pick `origin`, or pick the first match** — rejected. Two remotes carrying the
  identical URL are two independent caches fetched at different times; they can hold different
  shas and therefore yield different numbers. Picking one is choosing an answer the operator
  cannot see the basis for, which is precisely the trade the strict rule was adopted to refuse.
- **Ambiguity: accept when all matching anchors resolve to the same commit** — rejected. More
  code and a second concept (anchor agreement) to rescue a configuration nobody in this
  repository has; the rule stops being one sentence long.

**Rationale**: the strict rule's whole value is that a stated number has exactly one possible
provenance. Ambiguity is the case where that stops being true, so it resolves the same way every
other non-exact case does. Note that `GIT_ENV_ALLOWLIST` (`:2161-2174`) admits no `HOME`, so git
cannot find a global config through `_run_git()` at all; `--local` states the intent rather than
relying on that.

### Decision 3: `_unpushed_weight_from_cache()` returns a frozen `_CachedWeight`, never `int | None`

**Choice**:

```python
@dataclass(frozen=True)
class _CachedWeight:
    """What the local cache says the pin holds beyond the declared remote.

    `measured` is the ONLY gate. A measured zero is a real answer — the
    cache already reaches the pin, so the probe most likely failed for a
    local reason rather than the remote refusing — and it is a different
    fact from a read that could not be taken.
    """
    measured: bool
    commits: int = 0
    anchor_ref: str = ""
    anchor_commit: str = ""
    reason: str = ""


def _unpushed_weight_from_cache(
    target: Path | None, commit: str, repo_url: str, repo_ref: str
) -> _CachedWeight: ...
```

Signature placement: defined immediately above `_verify_commit_reachable` (`:2332`), beside the
other helper that function owns (`_looks_like_ssh_remote`, `:2305`). Its body is one
`try: ... except (JobFolderError, OSError): return unmeasurable("anchor-unreadable")` — every
internal failure resolves inside the function and nothing escapes it.

**Alternatives considered**: `int | None` with `None` for unmeasurable — rejected, because
`if count:` reads a measured zero as unmeasurable and that is a one-character mistake a future
edit makes silently. A `(ok, value)` tuple — rejected, unpacking order is unlabelled. A sentinel
object — rejected, it still travels as an `int`-shaped value.

**Rationale**: the measured zero is reachable in production, not hypothetical — the catch-all
branch also catches a failed `TemporaryDirectory()` (asserted at `tests:11704-11716`), a DNS
failure and a proxy refusal, and in every one of those the pin may genuinely be published, so
the cache legitimately reports `0`. The module already owns this idiom: `JobFolder`
(`:2215-2228`) is a frozen dataclass whose docstring argues exactly this — "there is no
`is_stale()` a caller can forget" — by making the unsafe reading inexpressible rather than
discouraged.

`reason` carries one of four fixed codes, rendered as one sentence each in the unmeasurable
shape: `no-local-repository`, `no-exact-url-match`, `ambiguous-url-match`, `anchor-unreadable`.
Without it the ambiguity ruling in Decision 2 is invisible to the operator it affects.

### Decision 4: `target` is threaded explicitly, keyword-only, defaulted to `None`

**Choice**:

```python
def _verify_commit_reachable(
    commit: str, repo_url: str, repo_ref: str, *,
    decision: str = "generation",
    repo_credential_path: str | Path | None = None,
    target: str | Path | None = None,          # new
) -> None: ...

def _refuse_unpublished_pin(
    *, commit: str, repo_url: str, repo_ref: str, decision: str,
    repo_credential_path: str | Path | None = None,
    target: Path | None = None,                # stops riding `**_unused` (:2854)
    **_unused: object,
) -> None: ...
```

with `target=target` added to the inner call at `:2872-2878`.

**Alternatives considered**: leaving `target` inside `**_unused` and reaching it as
`_unused["target"]` — rejected for the reason already written into this function at
`:2866-2870` for `repo_credential_path`: a parameter riding the catch-all is a parameter a
future signature edit drops without anything noticing. A positional third parameter — rejected;
see below.

**Confirmed from disk**: no production call site changes. `verify_pin_preconditions()`
(`:3012`) passes `target=resolved_target` to every condition callable in one uniform keyword
block (`:3074-3084`), and `_refuse_unpublished_pin` is reached only through
`_PIN_CONDITION_CHECKS` (`:2881-2887`).

**One correction to the brief**: "no call site needs rewriting" holds for production, and holds
for the suite **only because the new parameter is keyword-only with a default**. There are ~18
direct `JOBFOLDER._verify_commit_reachable("c" * 40, url, "main")` calls in
`tests/test_remote_execution.py` (`:11575`, `:11612`, `:11633`, `:11662`, `:11688`, `:11710`,
`:11801`, `:11835`, `:12118`, `:12145`, `:20548`, `:20588`, `:20608`, `:23036`, `:23041`,
`:23084`, `:23093`, `:23121`, `:23137`, `:23148`, `:23168`), each passing three positional
arguments and no target. A required or positional `target` rewrites all of them. With
`target=None` they are untouched and take the `no-local-repository` path, which is correct: a
call with no repository has nothing to read. Their `_run_git` fakes have the signature
`(args, *, cwd, timeout=None)` and would tolerate the reader's calls anyway, but with the
default those calls never happen.

### Decision 5: The new budget is measured before it is written

**Choice**: `PIN_WEIGHT_TIMEOUT_SECONDS`, declared immediately below
`PIN_PUBLISHED_TIMEOUT_SECONDS` (`:2212`), carrying its measurement in its comment in the shape
`:2194-2211` established. Passed explicitly to each of the reader's three `_run_git()` calls;
no other call in the module receives it.

**The measurement procedure `sdd-apply` executes** (not invents):

1. Repository under measurement: this repository, plus — only if one is already on disk — the
   largest other git repository available, named with its commit count
   (`git rev-list --count HEAD`).
2. Timed, each five consecutive times, warm cache, on the apply machine (named: OS and
   hardware): (a) `git config --local --get-regexp '^remote\..*\.url$'`,
   (b) `git rev-parse --verify --quiet refs/remotes/origin/main^{commit}`,
   (c) `git rev-list --count refs/remotes/origin/main..HEAD --`.
3. Record min and max per call, and the max across all three. Raw numbers go into
   `apply-progress.md`; the comment quotes the max and the repository it came from.
4. The chosen value and its stated multiple. `PIN_PUBLISHED_TIMEOUT_SECONDS` took ~1.15x its
   worst case because that worst case was a 209s network transfer on the same link the constant
   governs. This constant governs a local walk whose cost is dominated by a variable the
   measurement cannot sample — history size on a machine that is not this one — so the comment
   must state a much larger multiple **and why**: the failure mode of too small a budget here is
   `unmeasurable`, a first-class outcome, not a wrong answer. Expected landing zone: a small
   round number, seconds not minutes, and unambiguously below `GIT_TIMEOUT_SECONDS` (120.0), so
   the constant reads as "this is the cheap local read" at a glance.
5. The budget is per `_run_git()` call (`timeout=` reaches `subprocess.run`, `:2292`), so the
   reader's wall-clock worst case is three times the constant. The comment says so.

**If the measurement cannot be taken** (no git on the apply machine, or the timing harness
cannot run): the constant is not written, the reader is not written, and `sdd-apply` stops at
that task and reports `blocked` with the reason. It does **not** ship an unmeasured number, and
it does not ship the reader bounded by a borrowed constant — the proposal's own risk row commits
to this, and `PIN_PUBLISHED_TIMEOUT_SECONDS` exists because a borrowed budget once produced a
false verdict.

**Alternatives considered**: reuse `GIT_TIMEOUT_SECONDS` — rejected by the spec (the constant
must be distinct) and by the precedent it would undo. Reuse
`PIN_PUBLISHED_TIMEOUT_SECONDS` — rejected; 240s is a network budget, and a local read that
hangs for four minutes inside a refusal path is a worse outcome than no number.

### Decision 6: Message composition — both shapes, as literal appends

The existing base string is unchanged and is extracted verbatim; `remedy` (`:2580-2583`) and
`unauthenticated` (`:2584-2590`) keep their current literals byte-for-byte.

```python
except (JobFolderError, OSError) as exc:
    remedy = (                       # unchanged literal, :2580-2583
        f" — push it to {repo_ref!r} on {repo_url!r} and pin the "
        "commit the remote actually received"
    )
    unauthenticated = (...)          # unchanged, :2584-2590
    base = (                         # unchanged text, extracted to a name
        f"{decision} refuses: commit {commit!r} could not be confirmed "
        f"reachable on the declared remote {repo_url!r} — a runner "
        "would attempt and fail this same fetch inside the kernel, "
        f"after quota is already spent{unauthenticated}: {exc}"
    )
    weight = _unpushed_weight_from_cache(target, commit, repo_url, repo_ref)
    if weight.measured:
        plural = "" if weight.commits == 1 else "s"
        raise JobFolderError(
            base + remedy +
            f". Measured locally, no bytes moved: the pin is "
            f"{weight.commits} commit{plural} beyond the last state this "
            f"clone recorded for that remote ({weight.anchor_ref} at "
            f"{weight.anchor_commit[:12]}, from the last fetch). That count is "
            "exact about this clone's cached record and makes no claim about "
            "the remote's state now."
        ) from exc
    raise JobFolderError(
        base +
        ". How much that push would carry could not be measured here: "
        f"{_WEIGHT_UNMEASURABLE_REASONS[weight.reason]}. Nothing is "
        "prescribed from a measurement that was not taken."
    ) from exc
```

`_WEIGHT_UNMEASURABLE_REASONS` is a module-level mapping, one clause per code:

| code | clause |
|---|---|
| `no-local-repository` | `no local repository was available to read it from` |
| `no-exact-url-match` | `no local remote is configured with exactly that URL` |
| `ambiguous-url-match` | `more than one local remote is configured with exactly that URL, and those records can disagree` |
| `anchor-unreadable` | `the local record of that remote's branch could not be read` |

Three composition rulings, each with its rejected alternative:

1. **The weight clause is appended after `remedy`, not between `{exc}` and `remedy`.** The spec
   forbids splicing ahead of *or interleaving within* existing content, and `remedy` is existing
   content. Rejected alternative: placing the number before the remedy, which reads slightly
   better and violates the letter of the requirement the suite will be held to.
2. **The unmeasurable shape drops `remedy` and appends its own clause.** Verified from disk that
   this breaks nothing: `rg` across the repository finds no test asserting `"push it to"` or
   `"actually received"` — only `jobfolder.py:2581-2582` itself and an archived verify report.
   The two live assertions key on `"could not be confirmed reachable"` (`tests:12124`,
   `tests:19626`), which sits in `base` and is untouched in both shapes.
3. **One template must read correctly at 0, 1 and N.** The spec forbids a third shape, so the
   zero case cannot get its own sentence. `"0 commits beyond the last state this clone
   recorded"` is clumsy but true and interpretable — with the anchor sha named beside it, the
   operator can see that the cache already reaches the pin. Rejected alternative: a separate
   zero sentence, which is a third shape.

**On the exact cache-relative count** — see *Disagreements with disk*, item 2 (CLOSED by
operator ruling). The clause states an exact count **over the subject it is literally true of**:
distance from the state this clone recorded, not distance from the remote as it is now. Both of
the spec's MUSTs are met (an exact commit count is stated; no floor or ceiling claim is made
about what remains unpublished) and the sentence is true regardless of which way the remote has
actually drifted since the last fetch.

## Data Flow

    verify_pin_preconditions(:3012)
      └─ target=resolved_target ──→ _refuse_unpublished_pin(:2847)
                                      └─ target= ──→ _verify_commit_reachable(:2332)
                                                       │
                                        scratch repo + fetch --dry-run (:2537-2558)
                                                       │
                              ┌────────────────────────┴────────────────────────┐
                    except GitTimeoutError(:2559)                    except (JobFolderError, OSError)(:2579)
                              │                                                  │
                     BYTE-UNCHANGED                              _unpushed_weight_from_cache(target, …)
                     no remedy, no weight                                        │
                                                          git config --local --get-regexp   (local)
                                                          git rev-parse --verify <anchor>   (local)
                                                          git rev-list --count A..pin --    (local)
                                                                                 │
                                                             _CachedWeight(measured=True|False)
                                                                                 │
                                                        measured ──→ base + remedy + weight clause
                                                    unmeasurable ──→ base + reason clause (no remedy)

Both refusals leave through one path to one stderr printer: `generate_job()` (`:1949-1961`) and
`remote_cli.py::_gate_job_folder_pin()` (`:790`, called from `cmd_submit` at `:1189`) let
`JobFolderError` propagate unwrapped. Nothing reformats, truncates or parses it.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `skills/remote-execution/scripts/jobfolder.py` (after `:2212`) | Create | `PIN_WEIGHT_TIMEOUT_SECONDS`, with its measurement in the comment |
| `skills/remote-execution/scripts/jobfolder.py` (before `:2332`) | Create | `_CachedWeight`, `_WEIGHT_UNMEASURABLE_REASONS`, `_unpushed_weight_from_cache()` |
| `skills/remote-execution/scripts/jobfolder.py:2332-2339` | Modify | `_verify_commit_reachable` gains keyword-only `target=None` |
| `skills/remote-execution/scripts/jobfolder.py:2579-2596` | Modify | Catch-all branch grows the two shapes |
| `skills/remote-execution/scripts/jobfolder.py:2847-2878` | Modify | `_refuse_unpublished_pin` stops discarding `target`; threads it |
| `skills/remote-execution/scripts/jobfolder.py:2559-2578` | **Untouched** | The precedent branch, byte-for-byte |
| `skills/remote-execution/scripts/jobfolder.py:2607-2608` | **Untouched** | `PIN_CONDITIONS` gains no member |
| `skills/remote-execution/SKILL.md` (after `:863`, before `:865`) | Modify | The probe section documents both shapes and the exact cache-relative count |
| `tests/test_remote_execution.py` | Modify | New locks, each proven reachable-red |

## Interfaces / Contracts

```python
PIN_WEIGHT_TIMEOUT_SECONDS: float      # measured; see Decision 5

@dataclass(frozen=True)
class _CachedWeight:
    measured: bool
    commits: int = 0
    anchor_ref: str = ""        # "refs/remotes/<name>/<branch>"
    anchor_commit: str = ""     # full sha of that ref, rendered to 12 chars
    reason: str = ""            # one of the four codes; "" when measured

def _unpushed_weight_from_cache(
    target: Path | None, commit: str, repo_url: str, repo_ref: str
) -> _CachedWeight:
    """Never raises. Never contacts a remote. Three local git calls, each
    bounded by PIN_WEIGHT_TIMEOUT_SECONDS."""
```

Contract, restated so a future edit cannot lose it: this helper **raises nothing**. A helper that
can raise a second kind of refusal has become a guard, and this is not one.

## Testing Strategy

RED before GREEN for every lock. The mutation named per row is chosen so that a *weaker* lock
survives it — inverting the production line proves reachability, and only this choice proves
strength.

| # | Layer | Lock | Fixture | The mutation a weaker lock survives |
|---|---|---|---|---|
| 1 | Unit | Measured shape names the count as an exact cache-relative distance and keeps the remedy | `PublishedPinResolutionTests.published_target()` (`tests:19558`) + `.commit_local_only()` (`:19578`), remote URL passed byte-identically | Emit the bare count without the cache-relative clause. A lock asserting only the number survives; only one asserting the exact cache-relative phrasing fails. |
| 2 | Unit | A **measured zero** still takes the measured shape | published target, pin = the published tip, probe forced to fail locally | `if weight.commits:` instead of `if weight.measured:`. Every nonzero test survives; only the zero case fails. This is the lock that pays for Decision 3. |
| 3 | Unit | No configured remote → unmeasurable, no remedy | `CommitReachabilityTests._real_repositories()` (`tests:11720`) | Fall back to `origin` when no URL matches. A lock asserting "refusal still happens" survives; only one asserting the absence of `"push it to"` fails. |
| 4 | Unit | A near-miss URL spelling is unmeasurable | published target with the remote configured as `<url>.git` while `--repo-url` lacks the suffix | Normalise by stripping `.git` before comparing. A no-remote-at-all lock survives; only a near-miss fixture fails. |
| 5 | Unit | Two remotes, one URL → unmeasurable, naming the ambiguity | published target with a second remote added at the identical URL | Take the first match. Locks 1–4 all survive; only this one fails. |
| 6 | Unit | Timeout refusal is **byte-identical** and the reader is never called | patched `_run_git` raising `GitTimeoutError`; `_unpushed_weight_from_cache` patched with a `Mock` and asserted `not_called` | Move the reader above both branches (or into a wrapper catching `JobFolderError`). A lock asserting only "no remedy in the timeout message" survives, because the weight clause is not the remedy; only a full-string equality plus `assert_not_called` fails. |
| 7 | Unit | The reader opens no network connection and moves no bytes | `_real_repositories()`, `_run_git` recorded | Have the reader call `ls-remote`. A lock asserting "no exception raised" survives; only an argv allowlist (`{config, rev-parse, rev-list}`) plus a before/after census of `.git/objects` and the absence of `FETCH_HEAD` fails. |
| 8 | Unit | `PIN_WEIGHT_TIMEOUT_SECONDS` is a distinct constant and only the reader's calls carry it | shape copied from `PinPublishedTimeoutBudgetTests` (`tests:20492`) | Pass it to the local `init` call too. A lock asserting only `!=` on the two existing constants survives; only the per-call census fails. |
| 9 | Unit | Fails silent: every local primitive failing yields the careful shape, not a crash and not a new refusal | `_run_git` patched to raise `OSError` for everything after `init` | Let the reader's `except` re-raise. A lock catching `JobFolderError` broadly survives; only one asserting the exact unmeasurable sentence fails. |
| 10 | Integration | End-to-end through `generate-job`, measured shape, real git, real subprocess | `PublishedPinResolutionTests.generate()` (`tests:19587`) | Compose the message anywhere other than the one raise site — an in-process unit lock survives a wrapper that reformats; only the CLI-level stderr assertion fails. |
| — | Doctrine | `PinConditionDoctrineTests` (`tests:12779`) and `PinConditionOrdinalGuardTests` (`tests:12951`) stay green | existing | Satisfied by construction provided every new sentence names the condition by its backtick id `` `pin-published` ``. The guard scans `SKILL.md`, `jobfolder.py`, `remote_cli.py` and the test module itself (`tests:12986-12991`); its patterns are `\bcondition(s)?\s*\(\s*[1-5]\s*\)` and `\b(two|three|four|five)\b(\s+\S+){0,2}\s+condition(s)?\b` (`tests:12876-12883`), so new prose must not write a count immediately before the word "conditions". |

**Commands**: `npm run test:all` (`openspec/config.yaml:18`), with
`python3 -m unittest tests.test_remote_execution` as the fast inner loop. This repository has two
suites and running one alone has hidden a regression before.

**Non-vacuity**: locks 1, 2, 4, 5 and 10 drive real `git` subprocesses, so each must assert the
fixture actually produced the state it claims (the remote URL recorded, the anchor ref present,
the pin distinct from the tip) before asserting on the message.

## Threat Matrix

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | `requirements.txt`, executable Markdown, `README.sh` | **N/A** — this change classifies no file and executes nothing off a path; its inputs are a URL string, a ref string and a validated hex pin | — | — |
| Git repository selection | `git -C`, relative paths, absolute paths | **Applicable** — the reader runs git in the operator's own repository, the first thing in this function's history to do so since `target` was removed from it | `cwd=target` only, where `target` is already `resolve_target()`d by `verify_pin_preconditions` (`:3069`); never `git -C` on a raw argument, matching `_run_git`'s documented rule (`:2243-2245`). `target=None` is unmeasurable, never a fallback to the process cwd | Lock 3 (no remote in that repo), lock 7 (the repository is read and not written), plus a lock asserting `cwd` equals the resolved target for every call the reader makes |
| Commit state | staged, `commit -a`, empty index | **Applicable** — the reader must not care about, or disturb, the index or worktree | Only `config`, `rev-parse` and `rev-list` — three read-only plumbing verbs. No `add`, `commit`, `stash`, `reset`, `checkout`, `fetch`, honouring `SKILL.md:792-796` | Lock 7's before/after census covers `.git/objects`; extend it to assert `.git/index` mtime and `git status --porcelain` are unchanged across the reader |
| Push state | tracking branch, first push, explicit refspec | **Applicable** — the anchor *is* a tracking-ref question, and "no tracking ref yet" is the first-push case | `refs/remotes/<name>/<branch>` derived from the declared `--repo-ref`, never from `branch.<x>.merge` or the checked-out branch's upstream; a missing ref is unmeasurable, which is exactly the honest answer on a first push | Lock 3 (no remote), plus a first-push lock: a configured exact-URL remote with **no** `refs/remotes/<name>/<branch>` yet → unmeasurable, `anchor-unreadable` |
| PR commands | explicit `--head`, environment prefix, composed commands | **N/A** — this change composes no PR or VCS-mutating command and spawns no shell; every invocation goes through `_run_git()`'s `shell=False` list argv (`:2278-2286`) | — | — |

The three applicable rows carry into `tasks.md` unchanged; their RED tests are written before the
production lines they hold.

## Migration / Rollout

No migration required. Nothing is written to disk by this change — no job folder field, no config
key, no artifact — and the refusal's firing conditions do not move, so no job folder generated
under either version differs. One commit against `main`, reverting independently.

## Open Questions

- [x] **CLOSED — the direction of "at least" (see *Disagreements with disk*, item 2).** The
      operator ruled after design.md was first written: the sentence states an exact count
      relative to the cache — "the pin is N commits beyond the last state this clone recorded
      for `<remote>`" — never "at least N" (a floor) and never "no more than N to push" (a
      ceiling). `count(anchor..pin)` is a ceiling on the real push in the ordinary drift
      direction, so both of the earlier framings over-claimed; the sentence must claim nothing
      about the remote's current state, which was never measured. Applied throughout this
      document and the spec.
- [x] **CLOSED — `PIN_WEIGHT_TIMEOUT_SECONDS`'s value**, per Decision 5's procedure, run during
      apply: five consecutive warm-cache timings of the reader's three calls, against this
      repository (1,131 commits) and the largest other repository already on the apply machine
      (AgentPt, 48 commits). Observed max across every call and both repositories: ~6.2ms
      (`git rev-parse --verify --quiet`, this repository). Chosen value: **5.0 seconds**, ~800x
      that observed worst case — deliberately far wider than `PIN_PUBLISHED_TIMEOUT_SECONDS`'s
      ~1.15x, because this budget cannot fully sample history size on a machine that is not this
      one, and undershooting only produces `unmeasurable`, never a wrong verdict. Raw timings
      recorded in `apply-progress.md` (mirrored to the Engram `apply-progress` observation).

## Disagreements with disk

1. **The proposal cites `SKILL.md:798-829` as the reachability-probe section.** On disk that
   section runs `798-871`: the numbered properties end at `:856`, the refusal paragraph at
   `:858-863`, and the timeout paragraph at `:865-871`. **Followed disk** — the documentation
   edit appends after `:863` and before `:865`, so the new material sits with the refusal it
   describes and leaves the timeout paragraph's adjacency intact.
2. **CLOSED by operator ruling. The spec's original floor direction was inconsistent with its
   own cache caveat.** Spec `:140` (pre-ruling text) stated the remote "may hold more than the
   cache shows"; if the remote holds *more*, the push carries *less*, so `count(anchor..pin)`
   over-states the push in the ordinary drift direction — it is a ceiling on the push, not a
   floor. It under-states only if the declared ref was rewound or deleted since the last fetch.
   Design and exploration flagged this as an open question rather than resolving it; the
   operator's post-design ruling settled it: the sentence states an **exact count relative to
   the cache** — "the pin is N commits beyond the last state this clone recorded for
   `<remote>`" — not "at least N" (a floor) and not "no more than N to push" (a ceiling),
   because the sentence must claim nothing about the remote's current state, which this change
   never measures. Phase 0 of `tasks.md` swept this wording into both `spec.md` and this
   document.
3. **"No call site needs rewriting" holds only with a defaulted keyword-only parameter.** ~18
   direct `_verify_commit_reachable` calls in the suite pass three positional arguments and no
   target; a required or positional `target` rewrites all of them. **Followed disk** — see
   Decision 4.

Everything else the inputs asserted was re-read and confirmed at the cited line:
`GitTimeoutError` (`:136`), the constants (`:2175`, `:2194-2212`), `_verify_commit_reachable`
(`:2332`), the two branches (`:2559-2578`, `:2579-2596`), `PIN_CONDITIONS` (`:2607-2608`),
`_refuse_unpublished_pin` and its `**_unused` (`:2847-2878`, `:2854`), the credential-threading
precedent (`:2866-2870`), `_published_equivalent` and its `ls-remote` (`:2958-3009`, `:2993`),
`verify_pin_preconditions` and its uniform keyword block (`:3012`, `:3074-3084`),
`generate_job`'s call (`:1949-1961`), `remote_cli.py:790` and `:1189`, and every cited test
anchor. `rev-list`, `pack-objects`, `count-objects`, `cat-file --batch-check`, `remote -v`,
`get-regexp`, `for-each-ref` and `refs/remotes` return **zero hits** across
`skills/remote-execution/` — re-run this phase, still zero. There is no house precedent for any
of the primitives chosen above; this design establishes one.

# Feature: papersmith verifies without the operator's personal context

Status: round 1 revision — Judgment Day re-judgment pending
Branch: `feat/engram-optional` (from `integration/command-center` @ `b8dd5fe`)
Created: 2026-05-18
Round 1 revision: 2026-05-18, from frozen ledger `sha256:60875fd340f68967bbb07d16768a9de1ffd704fce9ae8cd1959ca3383c663c19`

## Goal

A green gate must prove that papersmith works **without the operator's personal
agent context** — Engram above all, but also personal skill trees, personal MCP
servers and personal agent configuration. Today a green gate proves only that
the suite passed on a machine that happens to have all of that installed.

Concretely: the declared gate must produce the same result whether it runs under
the operator's real `HOME` or under an empty one. Engram stays in the operator's
own working session; it does not stay in the verification path.

## Operator decisions (recorded)

1. **Branch base.** `feat/engram-optional` from `integration/command-center`, so
   it rides the CI provisioning repair rather than a `main` whose CI is broken.
2. **Artifact store target.** Filesystem only. The canonical context stops
   naming a second store at all.
3. **Scope.** De-machining `openspec/project-context.md` (E2) is in scope.
4. **Judgment Day runs on the plan** before any source edit.
5. **(Round 1, operator-directed)** The goal is *test-time isolation*, not
   removing Engram from the operator's session: "i want engram to be disable for
   the testing ... the idea is to test without engram, so we can verify that
   papersmith works without my personal context."
6. **(Round 1, operator-directed)** Implement E1–E5, then the merge feature's
   T4–T5, then **one** Judgment Day on the combined tree — not two.

## Defects found while implementing, by the gate rather than by me

Recorded because both are the failure class this feature exists to close, and
both were mine:

1. **The guard fired on itself.** `MemoryProviderCallTests` failed because the
   guard's own inversion controls contain the literal `mem_save` and
   `engram_mem_search`. A scanner must contain the pattern it scans for, so the
   scan now excludes this file by identity — and a control asserts that it does,
   so the exclusion cannot silently widen.
2. **The signature reader under-observed.** A 21-minute run reported *three*
   failing tests where pytest counted *six*, because `SUBFAILED` lines do not
   match `^(FAILED|ERROR)`. Two runs differing only in a subfailure would have
   been called equal. This is precisely the under-observing control the judges
   caught in the first E4 design, reproduced one level down; it is fixed, with an
   inversion control for the subfailure reader, and the fixed reader was first
   verified against the logs the flawed run produced (6 entries, identical).

## Revision log (round 1)

Every correction below is recorded against the frozen row that caused it. No
frozen claim is altered silently; the original text is superseded, not erased.

| Row | What was wrong | What replaced it |
| --- | --- | --- |
| `JD-A-001` / `JD-B-001` (CRITICAL) | E4's mechanical control was a guaranteed green: it re-ran the static gate with `ENGRAM_BIN`/`ENGRAM_URL` unset, but **nothing tracked reads either variable** and the gate spawns no agent, so both runs were identical by construction | E4 is now a **differential control** over the declared gate: real `HOME` vs empty `HOME`, identical results required. It fails if any test reads personal context, and it has a measured baseline (F8) |
| `JD-A-002` (CRITICAL) / `JD-B-002` | E3's tool roster was a hand-written phrase list in disguise — it omitted `mem_session_summary`, `mem_doctor`, `mem_judge`, `mem_review`, `mem_compare`, `mem_capture_passive`, `mem_list_projects`, `mem_pin` and the `engram_mem_*` MCP rows — and, because the tree holds zero calls, it passed before *and* after E1, so it could never meet the fail-before/pass-after standard | E3 now declares a small **provider-free store set** and carries a **planted-call inversion control** (`kind=guard-never-fires`), so the guard is proven to fire. Its load-bearing half moved to the differential control, which can fail on its own |
| `JD-A-005` (inferential) | F1 claimed `Artifact store: both` *requires* Engram. The generator defines `both`/`hybrid` as "write file-backed artifacts and save the phase artifact to memory **when tools are available**", so the filesystem half is written regardless. The two losses F2 cited declared store `engram`, not `both` | F1 and F2 corrected below; the loss class is the **12 memory-only `engram` changes**, not hybrid mode |
| `JD-B-004` | The Goal claimed reach to "a user who initializes a workspace from it", but `papersmith init` ships no `openspec/` at all (`KIT_ENTRIES` has no such entry; `_create_topology` creates none; no `openspec` reference exists under `src/`) | The Goal now claims what this repository can actually enforce: the **verification path** of this repository, plus its tracked artifacts |
| `JD-B-005` | `openspec/specs/.gitkeep:2` declares "Directory created by sdd-init (hybrid)" — a second declaration in a different vocabulary that neither the Engram-token sweep nor E3's canonical-context-scoped check would catch | Added as F5b, and E3 now scans for the declaration *shape*, not one file |
| `JD-A-003` | E3 constrained only the artifact-store line, while E1 must also drop the `Engram mirrors:` line — a partial E1 would pass the guard | E3 covers both lines |
| `JD-A-004` / `JD-B-003` | The plan's own close-out steps ("mirror to Engram") falsified its Goal, and a user without the provider cannot execute them | Per operator decision 5, the **tracked** steps are filesystem-only; the operator's own session mirror is recorded as an operator-side step and marked optional, never a tracked requirement |
| `JD-B-006` | E1 claimed a note written *inside* generator output would survive a regeneration that supersedes the record wholesale | The in-file note is now a courtesy, not the mitigation. E3's guard plus E5 are named as the regeneration protection |
| `JD-B-007` | E5 restated the gate as a command string instead of naming the declared gate | E5 names `npm run test:all`, the command stated at three sites in `openspec/config.yaml` |

## Findings (measured, not assumed)

### F1 — CORRECTED. What the canonical context actually declares

`openspec/project-context.md` is the file every harness entrypoint routes to
(`CLAUDE.md`, `PI.md`, `OPENCODE.md`, `.antigravity/rules.md`).

- Line 5: ``- Artifact store: `both` (hybrid: `openspec/` files + Engram observations)``
- Line 45: `- Engram mirrors: sdd-init/papersmith-ai, sdd/papersmith-ai/testing-capabilities, skill-registry`

**Corrected reading.** `both` is not memory-only. The generator's own asset
(`~/.pi/agent/npm/node_modules/gentle-pi/assets/agents/sdd-spec.md:48`) defines
it as "write file-backed artifacts and save the phase artifact to memory when
tools are available", so the filesystem half is written regardless. The same
asset contradicts itself four lines earlier — `:34` calls that save "mandatory"
for `engram`/`both`. So the line 5 declaration is a **recorded preference with an
internal contradiction**, not a hard requirement; whether E1 removes a
requirement or rewrites a preference is therefore stated as *this*: it removes a
name, and it removes the contradiction's home. The durable protection is E3 and
E5, not the edit.

### F2 — CORRECTED. The loss class is memory-only `engram`, not hybrid

82 tracked files under `openspec/changes/archive/` mention Engram. The store each
change actually declared, counted across the archive:

```
35  Store: openspec
19  hybrid / both      (filesystem half always written)
12  Store: engram      (memory-only)
```

The two losses the previous revision cited declared **`engram`**:

- `openspec/changes/archive/2026-08-21-the-pin-the-runner-can-actually-fetch/archive-report.md:9`
  — "**Artifact store**: `engram` — **the Engram MCP backend was disconnected for
  the entire cycle**. Every artifact of this change is a file in a session
  scratchpad, not an Engram observation."
- `openspec/changes/archive/2026-08-20-the-flow-names-what-it-needs/apply-progress.md:3`
  — "Store: engram MCP disconnected — this file is the artifact."

So the measurable defect is: **12 changes ran with a memory-only store and left
artifacts in a scratchpad that does not survive the session.** Hybrid mode
produced no such loss in the archive.

### F3 — There is no code dependency

```
git grep -l -E "mem_(save|search|context|get_observation|session_start|update)\b" -- .
```

returns six files, **all** under `openspec/changes/archive/`. Nothing in `src/`,
`skills/`, `scripts/` or `tests/` calls a memory-provider tool. The non-archive
code references are provenance comments citing past observations:

- `skills/_core/implementation/engine/implementation_engine.py:12549,15783`
- `skills/remote-execution/scripts/ledger.py:530`

### F4 — The provider is a global harness package, which is why the gate is blind

`~/.pi/agent/settings.json` lists, under `packages`: `npm:gentle-pi`,
`npm:gentle-engram`, `npm:gentle-engram@0.1.16` (the same package twice),
`npm:pi-mcp-adapter`. Engram is not a papersmith dependency, so nothing in
`package.json`, `requirements.txt`, or the gate's derivation can see it.

### F5 — The same canonical file leaks the maintainer's machine

`openspec/project-context.md` states as project truth:
`Root: /home/carlos/Documents/projects/papersmith-ai`, `node v26.8.1`,
`.venv Python 3.14.7`, `pytest 9.1.0`. Same defect family, same file, same fix.

### F5b — ADDED (row `JD-B-005`). A second declaration in a different vocabulary

`openspec/specs/.gitkeep:2`: "Directory created by sdd-init (hybrid) on
2026-09-09". One declaration is not one declaration when the same claim is spelled
twice; E3 therefore scans for the shape, not for one file.

### F6 — The isolation doctrine already exists in this repository

- `tests/seal/harness.py:55,118,122` — pins the child environment and passes
  `PATH`/`HOME` through deliberately.
- `tests/test_remote_execution.py:12261-12279` — enumerates the names that would
  make a probe "someone rather than anyone": `HOME`, `XDG_CONFIG_HOME`, and a
  `~/.gitconfig` carrying `credential.helper`.
- `tests/test_mcp_errors.py:129,136` — `HOME: /home/tester`.
- `tests/test_mcp_no_mcp_json.py` — "no `.mcp.json` is generated, read, or
  overwritten": the behavioral shape E4 now follows.

The suite is not hostile to this feature. It has been doing it locally, in
pieces, without ever asserting the property end to end.

### F7 — Corrections found while checking

- `.atl/skill-registry.md` hardcodes `/home/carlos/...`, but `.atl/` is
  gitignored (`.gitignore:8`) and `git ls-files -- .atl/` is empty: a local
  artifact, **not** a clone leak. Out of scope.
- `openspec/changes/` holds no active changes.

### F8 — ADDED. The differential control, measured

The declared gate was run under an empty `HOME` (a fresh `mktemp -d` holding no
`.pi`, no `.agents`, no `.claude`, no `.engram`):

| Half | Empty `HOME` | Real `HOME` |
| --- | --- | --- |
| Node (`npm test`) | exit 0 | exit 0 |
| Python (`pytest`) | 5 failed, 5353 passed | the same 5 failed |

The five, re-run under the real `HOME`, fail identically — so they are
**context-independent**, not isolation defects:

| Failure | Cause |
| --- | --- |
| 3 × `ReportFirstSectionProseTests` subfailures (`health_inspector.py`, `state_extractor.py`, `index-Du6DExVG.js`) | T4's `kaggle` leak, pending on the integration branch |
| `tests/test_mcp_registry.py::test_registry_labels_match_the_real_cli_roster` | pre-existing on the branch |
| `tests/test_version_sources.py::ReleaseHygieneTests::test_shipped_changes_since_the_last_release_moved_the_version` | pre-existing on the branch |

**Differential today: zero.** That is the baseline E4 asserts against — and the
reason it can fail: a test that reads personal context would make the two columns
differ.

## Task list

- [x] E0 — Tracking and branch. This document, its mirror, and
  `feat/engram-optional` from `integration/command-center`.
  - Evidence: `075f8e9`. The session mirror is operator-side and optional
    (decision 5); it is not a tracked requirement of this feature.
- [x] E1 — Canonical context stops naming a provider store.
  - `openspec/config.yaml` gained `store: openspec` — the single
    repository-local source the guard derives its expectation from.
  - `openspec/project-context.md` now declares `openspec` and the
    `Engram mirrors:` line is gone (both lines — row `JD-A-003`).
  - `openspec/specs/.gitkeep` no longer declares `(hybrid)` — row `JD-B-005`.
  - **Token deviation from operator decision 2, reported rather than taken
    silently:** `files` was the label I offered, and it is not in the
    generator's vocabulary. gentle-pi's own preflight
    (`lib/sdd-preflight.ts:956`) accepts exactly `openspec|engram|hybrid|none`,
    and the file said `both` — a token that vocabulary rejects. `openspec` is
    the only file-backed-only mode, so it is what was written.
  - The reason is recorded in the file as a courtesy to the next reader; it is
    **not** the mitigation, because the file is generator output and a refresh
    supersedes it wholesale (row `JD-B-006`).
  - Evidence: `45ee097`.
- [x] E2 — De-machine the same file.
  - The absolute `Root:` is gone and the measured-runtime row is date-stamped as
    a measurement on the initializing machine, never a requirement.
  - Two further false facts corrected while in the file, since a canonical
    context that misinforms is the defect family this feature is about: the
    Python dependency row predated the command center's four dependencies, and
    the CI row still described `pip install -r requirements.txt` after CI moved
    to the micromamba environment the gate names.
  - Evidence: `45ee097`.
- [x] E3 — Guard: `tests/test_no_personal_context_dependency.py`.
  - **Rule A (store).** Every tracked declaration, found by anchored shape
    anywhere in the repository, must carry the mode declared in
    `openspec/config.yaml`. Anchoring matters: the plan document quotes `both`,
    `engram` and `hybrid` while discussing them, and an unanchored scanner would
    fire on its own documentation. History is excluded — completed changes are
    an audit trail that is never rewritten, so demanding they be edited would be
    demanding a lie.
  - **Rule B (calls).** One declared namespace (`mem_*`, `engram_mem_*`), never a
    roster of tool names, excluding this file by identity.
  - **RED first, kept in history:** `a79d972` fails 4 assertions on three real
    declarations. That is the fail-before evidence, not a claim.
  - Nine inversion controls prove every scanner fires on a planted input.
  - Evidence: `a79d972` (red) -> `45ee097` (green); 19 passed.
- [x] E4 — Differential context control, the load-bearing deliverable.
  - `scripts/clean_context_gate.py` runs the **declared gate**, read from
    `package.json`'s `test:all` rather than restated (row `JD-B-007`), under an
    empty `HOME` and under a **decoy** `HOME` carrying `.pi/agent/mcp.json`,
    `.agents/skills/`, `.claude/skills/`, `.config/opencode/`, `.engram/`, and
    fails naming any difference.
  - Synthetic homes, deliberately: comparing the operator's real home against an
    empty one would be trivially green on CI. A decoy is present on every
    machine, so the control fires on a runner exactly as on a laptop.
  - Its comparator, signature reader and decoy builder carry their own inversion
    controls in E3's guard.
  - `.github/workflows/test.yml` gained the stage (`e8f7ffe`), with the doubled
gate time recorded in the step's own comment.
- [x] E5 — Prove the flows.
  - `python3 scripts/clean_context_gate.py` (19m08s): Node `exit 0` under both
    homes; Python `exit 1` under both with **5 failing tests and an identical
    signature**. Verdict: identical, so the verification path does not read the
    operator's context.
  - The 5 are the context-independent ones F8 named: `test_mcp_registry`,
    `test_version_sources`, and the three `kaggle` subfailures that T4 removes.
  - Guard: 19 passed.
- [x] E6 — **One** Judgment Day, on the combined tree (operator decision 6),
  shared with the merge feature's T6 rather than run twice.
  - Outcome: **`JUDGMENT: APPROVED`**, recorded in full in
    `odd/tasks/merge-command-center.md`'s T6. Two rounds; no severe row survived.
  - The one row that reached this feature's own surface is `JD-A-002`
    (CRITICAL): the differential control's Node reader matched a shape `node
    --test` never emits, so the Node half compared exit codes alone and its
    inversion control proved a reader on a line no run produces. `verified`
    after `1227799`, which also closed the second hole — a gate that could not
    run reading as agreement. Both were the same under-observation class as the
    two holes found and fixed while building the control, which is four in one
    deliverable and worth remembering about it.
- [~] E7 — Close-out, **pending CI** (marker is permanent in the repo; see T7 in
  `odd/tasks/merge-command-center.md`). Commit identities and gate evidence are
  recorded in that document's Close-out. Cross-repo follow-up, not done here:
  `sdd-init`'s default artifact store should stop assuming Engram. Worktree
  removal is post-merge and operator-side.

## Non-goals

- **Removing Engram from the operator's own working session** (decision 5). The
  session mirror stays; it is operator-side and optional.
- Changing gentle-engram, or uninstalling any global Pi package.
- Deleting the provenance comments in F3. They cite history; they are not calls.
- Fixing the five context-independent failures in F8: the `kaggle` leak is T4's,
  and the other two are pre-existing on `integration/command-center`. This
  feature must not hide them by narrowing the gate.
- `.atl/` (F7: gitignored, not tracked, not a leak).

## Risks

- **A control that runs the suite twice.** E4 doubles gate time. Accepted: the
  property is the deliverable, and the alternative was a guaranteed green.
- **Rule A's provider-free set is declared, not derived.** It is three tokens
  with a planted negative control, not a roster that rots. The plan says so
  instead of claiming derivation it does not have.
- **Prose is out of the guard's reach.** A future document could require a
  provider in words no rule parses. The differential control is what catches the
  consequence; the rules only narrow the surface.
- **Generator overwrite.** E1 edits generator output. E3's Rule A and E5 are the
  protection; the in-file note is not.
- **The `mirror to Engram` wording in `odd/tasks/merge-command-center.md`** (T0
  and T7) now describes the mirror as optional and operator-side; corrected at
  T7 close-out (row `JD-A-004`).

## Judgment Day protocol

Round 1 fix batch authorized by the operator for the three frozen severe rows
(`JD-A-001`, `JD-A-002`, `JD-B-001`) plus a labeled diagnosis correction. Frozen
ledger: `.scratch/jd-engram-plan/ledger.jsonl`,
`sha256:60875fd340f68967bbb07d16768a9de1ffd704fce9ae8cd1959ca3383c663c19`.

- **Re-judgment** receives only those three frozen IDs, their exact hash-bound
  rows, and this revision's diff, and returns one
  `verified | corroborated | regression` per ID. It resolves only those IDs: no
  new findings, no changed frozen claims, no second fix request.
- **Informational rows** (`JD-A-003`, `JD-A-004`, `JD-A-005`, `JD-B-002`–`JD-B-007`)
  never schedule fixes; they are recorded here and answered in the revision log.
- At most one further round. Round-two survivors escalate.
- Then exactly one final verification on the implementation tree, and the
  terminal `JUDGMENT: APPROVED` or `JUDGMENT: ESCALATED`.

## Judgment Day outcome — plan review, CLOSED

- **Verdict: `JUDGMENT: APPROVED`.**
- **Bound revision:** `66ed57f`, artifact sha256
  `8ff5163625a618d3ed1086e8e9b24b74090c7194b438c8fd3ede3e5a76cb2a1f` — the
  revision the re-judges actually read. This block is post-verdict bookkeeping;
  it is not part of the reviewed artifact.
- **Frozen ledger:** `.scratch/jd-engram-plan/ledger.jsonl`,
  `sha256:60875fd340f68967bbb07d16768a9de1ffd704fce9ae8cd1959ca3383c663c19`,
  unchanged through the whole run.
- **Discovery:** two blind judges, identical criteria, one exhaustive read-only
  sweep each. 12 rows — 3 CRITICAL, 6 WARNING, 3 SUGGESTION.
- **Round 1:** one scoped fix batch on the three severe rows, plus the labeled
  diagnosis correction the operator authorized.
- **Re-judgment:** cross-assigned, so no judge resolved its own row.

  | Row | Raised by | Re-judged by | Outcome |
  | --- | --- | --- | --- |
  | `JD-B-001` | judge B | judge A | `verified` |
  | `JD-A-001` | judge A | judge B | `verified` |
  | `JD-A-002` | judge A | judge B | `verified` |

- **No round 2.** No severe row survived, so the single remaining round was
  never needed.
- **Independently reproduced.** Both re-judges re-ran the differential
  measurement themselves rather than accepting the plan's word: Node 653 pass,
  exit 0, under both `HOME`s; Python `5 failed, 5353 passed, 8 skipped` under
  both, with the same five names F8 lists.
- **Falsifiability demonstrated, not argued.** Judge B pointed `HOME` at
  `kaggle-inbox` and
  `test_recognises_what_came_from_the_inbox_and_what_did_not` flipped pass to
  fail — the replacement control genuinely fires. The control it replaced could
  not fire at all: nothing tracked read `ENGRAM_BIN` or `ENGRAM_URL`.
- **Roster coverage confirmed.** The provider exposes 19 tools, all matching
  `engram_mem_*` with short aliases matching `mem_*`, so the declared namespace
  covers every tool the frozen row listed as omitted.
- **Informational rows.** The six WARNING/SUGGESTION rows never scheduled fixes;
  each is answered in the revision log above.
- **The agent-session claim** is now an explicit operator-authorized non-goal
  (decision 5), not a hidden over-claim.

## Close-out

(to be completed at E7)

- Gate evidence:
- Differential control evidence:
- Commit identities:
- Cross-repo follow-up:

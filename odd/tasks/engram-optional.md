# Feature: papersmith works without an agent memory provider

Status: planned — Judgment Day on this plan is the next step
Branch: `feat/engram-optional` (from `integration/command-center` @ `b8dd5fe`)
Created: 2026-05-18

## Goal

Nothing this repository tracks may *require* an agent memory provider. A user who
clones papersmith, or who initializes a workspace from it, must be able to run
every workflow with no Engram and no memory MCP server present, and the
canonical context must describe an artifact store that exists on their machine.

The defect is not a crash. It is a flow that works where the operator happens to
have the provider installed and silently degrades where they do not, which is why
the suite has never caught it.

## Operator decisions (recorded)

1. **Branch base.** `feat/engram-optional` branches from
   `integration/command-center`, so it rides the CI provisioning repair rather
   than a `main` whose CI is still broken.
2. **Artifact store target.** Filesystem only. The canonical context stops
   naming a second store at all.
3. **Scope.** De-machining `openspec/project-context.md` (E2) is in scope: it is
   the same file and the same defect family.
4. **Judgment Day runs on this plan** before any source edit.

## Findings (measured, not assumed)

### F1 — The canonical project context requires Engram

`openspec/project-context.md` is the file every harness entrypoint routes to
(`CLAUDE.md`, `PI.md`, `OPENCODE.md`, `.antigravity/rules.md`).

- Line 5: ``- Artifact store: `both` (hybrid: `openspec/` files + Engram observations)``
- Line 45: `- Engram mirrors: sdd-init/papersmith-ai, sdd/papersmith-ai/testing-capabilities, skill-registry`

A user without Engram is instructed, by the project's own canonical context, to
persist half the artifact set to a store that does not exist on their machine.

### F2 — The degradation is documented by this repository's own history

82 tracked files under `openspec/changes/archive/` mention Engram, and several
record the failure mode rather than a success:

- `openspec/changes/archive/2026-08-21-the-pin-the-runner-can-actually-fetch/archive-report.md:9`
  — "**the Engram MCP backend was disconnected for the entire cycle**. Every
  artifact of this change is a file in a session scratchpad, not an Engram
  observation. There are no observation IDs to record."
- Same file, `:355` — "scratchpad that does not survive the session."
- `openspec/changes/archive/2026-08-20-the-flow-names-what-it-needs/apply-progress.md:3`
  — "Store: engram MCP disconnected — this file is the artifact."

This is the measured evidence that the flow's artifact store is provider-shaped:
where the provider exists the store works, and where it does not, the artifact
lands somewhere that does not survive.

### F3 — There is no code dependency

```
git grep -l -E "mem_(save|search|context|get_observation|session_start|update)\b" -- .
```

returns six files, **all** under `openspec/changes/archive/`. Nothing in `src/`,
`skills/`, `scripts/` or `tests/` calls a memory-provider tool. The only
non-archive code references are provenance comments citing past observations:

- `skills/_core/implementation/engine/implementation_engine.py:12549,15783`
- `skills/remote-execution/scripts/ledger.py:530`

Those are history, not a call. The fix is therefore a contract and guard fix,
not a code refactor.

### F4 — The provider is a global harness package, which is why the gate is blind

`~/.pi/agent/settings.json` lists, under `packages`: `npm:gentle-pi`,
`npm:gentle-engram`, `npm:gentle-engram@0.1.16` (the same package listed twice),
`npm:pi-mcp-adapter`. Engram is not a papersmith dependency, so nothing in
`package.json`, `requirements.txt`, or the gate's derivation could ever see the
coupling.

### F5 — The same canonical file leaks the maintainer's machine

`openspec/project-context.md` states, as project truth:
`Root: /home/carlos/Documents/projects/papersmith-ai`, `node v26.8.1`,
`.venv Python 3.14.7`, `pytest 9.1.0`. A clone on another machine carries those
as facts about the project. Same defect family, same file, same fix.

### F6 — "No external agent-side connector" is already a tested contract here

`tests/test_mcp_no_mcp_json.py` — "Success criterion #6: no `.mcp.json` is
generated, read, or overwritten." The new guard is that same shape applied to a
memory provider, so it has in-repo precedent rather than being an invention.

### F7 — Two corrections found while checking

- `.atl/skill-registry.md` hardcodes `/home/carlos/...` source paths, but
  `.atl/` is gitignored (`.gitignore:8`) and `git ls-files -- .atl/` is empty, so
  it is a local artifact and **not** a clone leak. It stays out of scope.
- `openspec/changes/` holds no active changes (only `archive/` and
  `_measurements/`), so this feature has no in-flight SDD change to coordinate
  with.

Tracked non-archive files mentioning Engram, in full:

```
git grep -l -i engram -- . ':!openspec/changes/archive'
odd/tasks/merge-command-center.md
openspec/project-context.md
skills/_core/implementation/engine/implementation_engine.py
skills/remote-execution/scripts/ledger.py
tests/test_experimental_implementation.py
tests/test_proposal_implementation.py
```

The last four are comments and test prose; `openspec/project-context.md` is the
one declaration; `odd/tasks/merge-command-center.md` is the ODD plan doc for the
merge work, which names an Engram mirror as an ODD convention.

## Task list

- [x] E0 — Tracking and branch. This document, its Engram mirror
  `odd/engram-optional/tasks`, and `feat/engram-optional` created from
  `integration/command-center`.
  - Evidence: this document's work-unit commit on the branch.
- [ ] E1 — Canonical context stops requiring Engram.
  - `openspec/project-context.md` moves to a filesystem-only artifact store and
    drops the `Engram mirrors:` line, with the reason stated in the file so a
    later `sdd-init` refresh does not silently restore it.
  - **Caveat that must not be hidden:** this file is generated by gentle-pi's
    `sdd-init`. A local edit fixes this repository's copy and does not fix the
    generator's default. The durable half is a change in that other repository,
    recorded at E7 as a follow-up rather than claimed as done here.
- [ ] E2 — De-machine the same file. Drop or explicitly date-stamp the `Root:`
  and runtime-version facts so a clone does not carry one machine as project
  truth.
- [ ] E3 — The guard: `tests/test_no_engram_dependency.py`. Derived, never a
  hand-written list:
  - no memory-provider tool call in tracked code (Python parsed with `ast`;
    `.ts`/`.mjs` by identifier);
  - the artifact-store declaration in the canonical context must name a store
    that exists inside the repository.
  - The lock must **fail before E1 and pass after it**, the same standard T3 was
    held to.
- [ ] E4 — Negative control, in two layers, with the limitation stated.
  - *Mechanical:* re-run the gate with the provider unreachable — `ENGRAM_BIN`
    pointed at a nonexistent path and `ENGRAM_URL` unset, which is the resolution
    path gentle-engram's own README documents — and require the same result as
    with it present.
  - *Procedural:* one end-to-end SDD/ODD flow run with the provider absent, whose
    artifacts must land under `openspec/` alone.
  - **Stated limitation:** no automated test in this repository can drive an
    agent session, so the procedural layer is recorded evidence, not a green
    check. Dressing it as a test would be a claim this repository cannot verify.
- [ ] E5 — Prove the flows. Full gate in the main checkout:
  `npm ci && npm test && .micromamba/envs/papersmith/bin/python -m pytest`, read
  for collection errors and not only for a pass count.
- [ ] E6 — Judgment Day on the frozen implementation tree.
- [ ] E7 — Close-out. Record commit identities and raw gate output here; record
  the cross-repo follow-up; mirror to Engram; remove worktrees.

## Non-goals

- Uninstalling, disabling, or reconfiguring the operator's global Pi packages,
  including gentle-engram.
- Changing gentle-engram itself.
- Deleting the provenance comments in F3. They cite history; they are not calls.
- Touching the pending T4–T5 merge work on `integration/command-center`.
- `.atl/` (F7: gitignored, not tracked, not a leak).

## Risks

- **Generated-file overwrite.** E1 edits a file `sdd-init` produces. Without the
  reason written into the file itself, the next refresh restores the defect.
- **The guard becoming a phrase blacklist.** The citation-versus-requirement
  distinction in prose is semantic and cannot be fully derived. The guard must
  enforce the derivable half — calls in code, and the store declaration — and
  this document says so rather than implying full coverage.
- **A negative control that cannot fail.** A run where the provider is present
  but unused proves nothing. Absence must be enforced, not assumed.
- **Prose is out of the guard's reach.** A future document could require Engram
  in words the guard cannot parse. The guard narrows that surface; it does not
  close it.

## Judgment Day protocol for this plan

- **Target:** this document, frozen at the commit that adds it, with the
  repository evidence it cites as the read-only scope. Judges verify F1–F7
  against the tree; they do not take the document's word for them.
- **Actors:** exactly two blind judges, identical criteria, zero refuters, one
  exhaustive read-only sweep each.
- **Criteria:** (1) is the diagnosis complete — are there mandatory-dependency
  surfaces in tracked artifacts this sweep missed? (2) does the fix actually
  remove the dependency for a user with no Engram, or only relabel it? (3) can
  the negative control fail, or could it never distinguish absence from
  never-needed? (4) does the guard avoid becoming a hardcoded exception list?
- The document's findings are **not** injected into the judge prompts.
  Independent rediscovery is corroboration; anything beyond them is the value.
- At most two scoped fix/re-judgment rounds; terminal `JUDGMENT: APPROVED` or
  `JUDGMENT: ESCALATED`.

## Close-out

(to be completed at E7)

- Gate evidence:
- Judgment Day verdict:
- Commit identities:
- Cross-repo follow-up:

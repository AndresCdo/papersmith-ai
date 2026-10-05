# Feature: `upgrade` migrates workspace artifacts, not just framework files

## Goal

`papersmith upgrade` carries an existing workspace to the installed release's
framework files and — new here — to that release's *artifact* expectations, so
the version a workspace records is a claim about its artifacts and not only
about its skills tree. Executed stages and research state survive the move; a
migration that fails leaves the recorded version where it was, so the workspace
never reports a shape it does not have.

## Why

`upgrade` already synchronizes the kit, re-renders harness projections,
preserves research state, refuses downgrades and clears retired paths
(`src/papersmith/core/upgrade.py`). It has one silent assumption: that workspace
artifacts are opaque and timeless. It preserves them by *not touching them*,
which holds only while their shape never changes.

Two consequences are already observable on `main`, before any release changes a
shape:

1. **The version can lie.** `upgrade` writes `.papersmith/version`
   (`upgrade.py:293`) after synchronizing framework files and without ever
   consulting an artifact. Nothing in `src/` migrates anything —
   `grep -rni "migrat" src --include="*.py"` returns one line, and it is a test
   name quoted in a docstring (`upgrade.py:91`).
2. **Graph artifacts are protected only by accident.** `sota-pool/` holds
   source-of-truth graph state — `candidates.json` from the `sota-scout` agent
   and `atlas.json` from `sota-grapher` — plus the derived `atlas.html`. That
   directory is in neither `KIT_ENTRIES` nor `PRESERVE_PATTERNS` nor
   `_create_topology`'s `directories`; `grep -rn "sota-pool" src/papersmith`
   returns nothing. The files survive today only because `upgrade` deletes just
   paths it previously baselined. Survival by accident is not a contract.

`sota-pool/atlas.html` makes the gap concrete: it is rendered from `atlas.json`
by `skills/plausibility/scripts/render_atlas.py`, which inlines
`skills/plausibility/assets/atlas3d.bundle.js` — both kit files. An upgrade that
ships a new viewer bundle leaves the rendered graph stale, with no mechanism
that notices.

## Design

### Two kinds of migration, one mechanism

Every migration declares an `id`, a `summary`, an optional `applies_from`
version, a `plan(workspace)` returning the human-readable actions it would take,
and an `apply(workspace)` performing them.

- **Version-gated** (`applies_from` set): a shape change between releases.
  Selected when `recorded < applies_from <= kit_version` and the `id` is not in
  the applied ledger. Runs once, then is recorded.
- **Convergence** (`applies_from is None`): makes the workspace match the
  installed release's expectations regardless of history. Evaluated on every
  upgrade; `plan()` is a probe, so an already-satisfied workspace yields no
  actions. Never recorded, because it is never finished.

### Ordering inside `upgrade`

Migrations run *after* the kit is synchronized — a migration may need the new
release's own scripts and assets — and *before* `.papersmith/version` is
written. The version marker advances only when no migration failed. That single
ordering is the invariant the whole feature exists for: the recorded version
never runs ahead of the artifacts. A failed run is re-runnable, because kit
copies are hash-skipped and convergence migrations are probe-guarded.

### Refusing to guess

A recorded version with no orderable number cannot place a version-gated
migration on either side of its gate. Such migrations are returned as
`undetermined` and never applied, the same refusal `_refuse_a_downgrade` already
makes for the same reason: writing files under a relationship nobody established
is the silence being removed. Convergence migrations are unaffected — they ask
the filesystem, not the version.

A damaged `.papersmith/migrations.json` is a hard refusal before any write,
matching `upgrade`'s existing behaviour for a corrupted manifest. Reading it as
empty would silently re-apply version-gated migrations.

### Not `--dry-run`

`--plan-migrations` reports the pending set and exits having written nothing.
It is deliberately not called `--dry-run`: a flag by that name on `upgrade`
would imply the kit copy, the projections and the orphan sweep were previewed
too, and they are not. One flag must not overstate its reach.

## Tasks

- [x] T0 Restore a green baseline: four version-coupled fixtures broken by the
      0.10.0 bump (pre-existing on `main`, not caused by this feature)
- [x] T1 Migration core: `core/migrations.py` — `Migration`, `REGISTRY`,
      selection, applied ledger, damaged-ledger refusal
- [x] T2 Wire into `upgrade()`: ordering, the version-advances-only-on-success
      invariant, `--no-migrate`, `--plan-migrations`, CLI reporting
- [x] T3 Fix the graph-pool contract at the source: `sota-pool` in
      `_create_topology` with a `.gitkeep`, and the missing entry in
      `gitignore.tpl`. **Reframed**: `sota-pool/**` is NOT added to
      `PRESERVE_PATTERNS` — proven dead code, see Decisions
- [x] T4 Convergence migration `sota-pool-scaffold`: scaffold the graph
      directory in workspaces that predate T3
- [x] T5 Convergence migration `atlas-render-refresh`: re-render a stale
      `sota-pool/atlas.html` from `atlas.json`, degrading honestly when the
      renderer, the viewer bundle or the input is unusable
- [x] T6 Surface migrations in `status`'s `framework` block
- [x] T7 Docs: `README.md` (Spanish, the project's convention) and
      `docs/releasing.md` gains "how to add a migration". **No CHANGELOG
      entry and no version bump** — see Open questions
- [ ] T8 Full verification

## Review workload

T1–T7 is roughly 600 lines with tests, past the 400-line review guidance. It
chains into three slices that each stand alone:

- **A** — T0, T1 (mechanism, no behaviour change to `upgrade`)
- **B** — T2, T6 (wiring and reporting; registry still empty of real entries)
- **C** — T3, T4, T5, T7 (the graph contract, the two migrations, docs)

## Evidence

- **T0** — RED observed first: `tests.test_papersmith_upgrade` → 20 ran, 4
  errors, each a `UserError` refusing the fixture's own setup upgrade
  (`records '0.10.0'`, `installed kit is '0.9.0'`). GREEN: 20 ran, OK.
  Characterized as pre-existing by stashing the edit and re-running: the two
  unrelated failures in `tests.test_papersmith_init`
  (`test_the_mcp_init_tool_skips_provisioning_unless_asked`,
  `test_checkout_with_pyproject_keeps_editable_install`) reproduce identically
  with and without this change, so they are environment-dependent and
  out of scope. Commit `fcc8391`.
- **T1** — RED observed: `ImportError: cannot import name 'migrations'`.
  GREEN: `tests.test_papersmith_migrations` → 15 ran, OK. Refactor: `upgrade.
  _version_order` deleted in favour of the shared `migrations.version_order`,
  one implementation for the downgrade guard and the migration gate;
  `tests.test_papersmith_migrations tests.test_papersmith_upgrade` → 35 ran, OK.

- **T2** — RED: 11 of 13 failing (`TypeError: unexpected keyword argument
  'migrate'`, `KeyError: 'migrations'`, and five assertion failures). GREEN:
  13 ran, OK. The early damaged-ledger refusal was then covered explicitly and
  its RED observed by removing the guard line: the stale framework file was
  synchronized before the failure, exactly the half-moved workspace the guard
  prevents. Restored: 14 ran, OK. Commit `5a36637`.
- **T3/T4** — RED: 6 of 7 failing. GREEN: 7 ran, OK. Commit `20fce7d`.
- **T5** — RED: all 7 new tests failing. GREEN: 14 ran, OK. Commit `994cca6`.
  Found while building the fixture and left alone as out of scope:
  `render_atlas._readable_shape` admits a system without an `id`, which
  `_scene` then requires, so such an atlas crashes with an untyped `KeyError`
  traceback instead of one of the renderer's typed codes.
- **T6** — RED: `KeyError: 'migrations'` on three tests plus the text report.
  GREEN: 18 ran, OK. Commit `66705b8`.
- **Regression check against `main`** — a throwaway detached worktree at `main`
  ran the same focused set (`test_papersmith_status`, `test_command_center_state`,
  `test_command_center_cli`, `test_command_center_history`, `test_cli_paper_e2e`):
  14 failures on `main`, the same 14 on this branch, empty regression diff.
- **Pre-existing failures, confirmed by stashing and by the base worktree**:
  `test_papersmith_init` (2: `test_the_mcp_init_tool_skips_provisioning_unless_asked`,
  `test_checkout_with_pyproject_keeps_editable_install`),
  `test_workspace_skills_e2e` (2), `test_workspace_commands_e2e` (1), and the
  `test_mcp_*` / `test_command_center_*` loader errors, which are a runner
  problem rather than a defect: those modules import sibling helpers
  (`workspace_series`, `domain_profile`) and need `tests` on `PYTHONPATH`.
  This worktree has no `.venv`, no `.micromamba` and no `node_modules`.

## Decisions

- Migration bookkeeping lives in `.papersmith/migrations.json`, not in
  `config.json`: `config.json` carries a validator (`schema.py:151`) and is
  rewritten by `upgrade` on every run, and applied-migration history is
  workspace state like `runs_ledger.jsonl`, not configuration.
- The first release ships convergence migrations only. No `applies_from` entry
  can target a version at or below 0.10.0, and the release bump is not this
  feature's to make (`docs/releasing.md`).
- `render_atlas.py` is invoked through `bridges/python.run_script`, the
  established idiom for skill entrypoints, rather than imported.
- **`sota-pool/**` is not added to `PRESERVE_PATTERNS`.** The original plan
  called it a preservation fix; it would have been dead code. All three
  `is_preserved` callers (`manifest.py:414`, `upgrade.py:119`, `upgrade.py:245`)
  iterate `kit_files(kit_root)` alone, and `walk_kit_files` walks only
  `KIT_ENTRIES`, which has no `sota-pool`. A kit can therefore never ship such a
  path, and `workspace_framework_files` never walks the workspace, so the pool
  can never enter the framework manifest either. The real defects were the
  unscaffolded directory and the missing `gitignore.tpl` entry, both fixed at
  the source.
- The MCP `upgrade` tool is left untouched. It already exposes a deliberate
  subset (`tools`, `force`) and never carried `--allow-downgrade`, so widening
  it is a separate reviewable decision; the default `migrate=True` is the right
  behaviour for an agent-driven upgrade.

## Open questions

**The version bump is not made here, and the release-hygiene test is red
because of it.** `test_shipped_changes_since_the_last_release_moved_the_version`
holds the documented rule: once a tag exists, a change under `src/`, `skills/`
or `scripts/` forces a version move. It is green on `main`
(`git diff v0.10.0..main -- src skills scripts` is empty) and red here, exactly
as intended.

It is not taken because the sibling session's branch `feat/proposal-sky-flow`
has already bumped `src/papersmith/__init__.py` to `0.11.0`. Both branches
claiming the same version would collide in four files (`__init__.py`,
`package.json`, `package-lock.json`, `CHANGELOG.md`), and the release is the
maintainer's decision, not this feature's. Whoever merges second bumps, adds
the `## X.Y.Z` changelog section, and that test goes green.

No migration in this release carries an `applies_from`, so nothing here depends
on which number is chosen.

## Constraints

- A sibling worktree `../papersmith-ai` on `feat/proposal-sky-flow` belongs to
  another session. This work stays inside this worktree and commits only to
  `feat/upgrade-migrations`.
- This worktree has no `.venv`, no `.micromamba` and no `node_modules`. Tests
  run as `PYTHONPATH=src python3 -m unittest ...`; `src/` is stdlib-only.

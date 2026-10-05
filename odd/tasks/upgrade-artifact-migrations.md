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
- [ ] T2 Wire into `upgrade()`: ordering, the version-advances-only-on-success
      invariant, `--no-migrate`, `--plan-migrations`, CLI reporting
- [ ] T3 Protect graph artifacts by contract: `sota-pool/**` in
      `PRESERVE_PATTERNS`, `sota-pool` in `_create_topology` with a `.gitkeep`
- [ ] T4 Convergence migration `sota-pool-topology`: scaffold the graph
      directory in workspaces that predate T3
- [ ] T5 Convergence migration `atlas-html-rerender`: re-render a stale
      `sota-pool/atlas.html` from `atlas.json`, degrading honestly when the
      renderer, the viewer bundle or the input is unusable
- [ ] T6 Surface migrations in `status`'s `framework` block
- [ ] T7 Docs: `docs/releasing.md` gains "how to add a migration"; CHANGELOG
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

## Constraints

- A sibling worktree `../papersmith-ai` on `feat/proposal-sky-flow` belongs to
  another session. This work stays inside this worktree and commits only to
  `feat/upgrade-migrations`.
- This worktree has no `.venv`, no `.micromamba` and no `node_modules`. Tests
  run as `PYTHONPATH=src python3 -m unittest ...`; `src/` is stdlib-only.

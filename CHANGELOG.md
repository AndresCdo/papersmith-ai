# Changelog

Notable changes to papersmith-ai, newest first.

This file starts at 0.2.0. `0.1.0` was set in the commit that created the
package and never moved again across more than a thousand commits, so there
is no honest way to reconstruct a release history for it — its record is the
git log, and pretending otherwise would put a fabricated summary where a
reader expects a kept one.

Versions follow [semantic versioning](https://semver.org): while the first
number is `0`, breaking changes can still arrive without a major bump.

## 0.14.0

### Fixed

- **An adopted finding reaches a terminal state instead of blocking the
  audit forever.** Once `proposal-deliberation` published a remedy and the
  target was re-bound to the successor revision, four readers disagreed about
  the finding: `verify`'s `remediesWithoutValidation` still demanded the
  `test_remedy_<id>` that `audit.migration` demands be retired, `admit
  --revision <successor>` ruled the finding inadmissible because the text the
  remedy replaces is gone (which is what adoption means), and the
  compatibility audit kept reporting `needs-deliberation` for the notation the
  remedy had introduced. The audit could only reach `ok` by deleting the
  finding. All of them now read one shared adoption state
  (`finding_adoption`): an adopted finding keeps its evidence
  (`test_finding_<id>` and its entry in `tests/findings.py`), owes no remedy
  validation, introduces no notation, and owes only the move `migration`
  checks. `admit` rules it admissible with an `adopted` verdict naming the
  revision and the expected form that confirmed it. `changed-unrecognized`
  (the replaced text gone, nothing expected in its place) is not adoption and
  stays inadmissible. Shared by `experimental-implementation`, which runs the
  same engine. The sealed CLI corpora already carried an adopted finding and
  had characterized the defect (ruled inadmissible, listed as unvalidated);
  their `verify` and `admit` goldens move accordingly.
- **Sibling implementation skills no longer collide on each other's
  checklist holder.** Once `proposal-implementation` had settled items into
  its declared `<Name>/AGREED.md`, `experimental-implementation` (declared
  holder `Experimental_AGREED.md`) refused every `position`/`settle` write on
  the same target with `HOLDER_UNDECLARED`, and both exits it offered —
  rename the sibling's file, or adopt its name — were destructive to the
  sibling. The same held in the other direction. `holder_resolution` now sets
  aside every holder filename a profile sharing the engine declares, derived
  from each `impl_profile.py` next to the loaded one (reading only
  `PROFILE["holder"]["filename"]`; a profile that cannot be read contributes
  nothing, so its file still refuses). A target holding only the sibling's
  holder resolves create-on-absent and the skill writes its own holder beside
  it. A checklist no skill declares still refuses, and the refusal and its
  question never name a sibling's holder as a file to rename. The read side
  follows the same rule: the agreements reader (`verify`, `close`)
  and the position reader (`verify`, `probe`, `gate`, `close`, `discuss`, `settle`, `offer`, `step`) no
  longer read the sibling's holder as this skill's, so its open items stop
  appearing as this skill's open agreements and its position block stops
  standing in for this skill's position.
- **`probe` no longer hides the pilot ladder when nothing is comparable.** A
  target whose comparison arms live inside its own package has no prior-work
  package under `src/`, so `probe` answered `nothing-to-compare` before any
  other rung, even with declared steps still short at pilot and, later, with
  every step finished at pilot and none placed. `pilot-first` and
  `pilot-decisions` never fired, so neither the rung question nor one
  per-step placement question was ever published. Comparability now answers
  the comparison only: with no baseline, `probe` returns `pilot-first` while a
  declared step is short and `pilot-decisions` (with its per-step questions)
  once the pilot is complete and a step is undecided, and
  `nothing-to-compare` only after both are settled. Shared by
  `experimental-implementation`.
- **A freshly scaffolded target no longer fails its own `verify`.**
  `materialize --stage scaffold` writes the kit's seal,
  `src/<Package>/report_digest.py`, which implements no claim and so declares
  no `__provenance__`; `verify` listed it under `missingProvenance` and read
  `fidelity: drift` on a target nobody had touched, under both implementation
  skills. The seal is now exempt only while it is still the kit's file: its
  path is a scaffold destination with a kit source (derived from the scaffold
  table, not a hand list), and its bytes equal today's kit source or the
  `writtenSha256` the scaffold receipt's `materialized` entry recorded (so a
  seal written by an earlier release still counts). An `adopted` or
  `authored` entry does not count, and a modified copy is reported as before.
- **`close` is reachable for a proposal-only target, and witness-less
  agreements have a recorded closing act.** `close` refused
  `POSITION_ABSENT` on every target without a position, and a position can
  only name execution witnesses (a step, notebook, record, rehearsed job or
  shard), so a target with no flow could pass only by installing an item
  pointing at a witness that does not exist. A position is now owed only
  when the target declares part of a flow (`__levels__`, `__steps__`,
  `__records__`, a shard root or a job folder); otherwise `close` checks the
  agreement and discussion axes, skips the refresh, and records the close
  over an empty sequence. Separately, an agreement no test could ever
  witness (a scoping decision, a premise, a deferral) could be ticked only
  by hand, so `agreements` stayed `open` unless someone edited the holder
  outside every command. `settle --done --unwitnessed --reason <text>` now
  ticks such a line and writes the operator's reason and the session to the
  ledger. It is never counted as witnessed: `agreements.witness` names it
  under `decided`. `--done` on a line that names a witness is unchanged, and
  `--unwitnessed` on such a line refuses `SETTLE_WITNESS_PRESENT`. Shared by
  `experimental-implementation`.
- **Deliberation gives one candidate the same verdict at v1 creation,
  preview and accept, and a code span is no longer a heading.** The three
  points ran three validation sets: `CREATE_INITIAL_REVISION` ran only the
  canonical-form rules, the `CREATE_SUCCESSOR` preview ran only the
  orchestrator's candidate validator, and only the accept turn ran the
  workspace's pre-publish set. The shared standalone-ATX check also read a
  backtick span such as `` `## Results` `` as a heading fused with prose. So
  a v1 carrying an inline-code `## ` published, every successor preview
  answered `awaiting_acceptance`, and every accept refused
  `atx-heading-standalone`: no successor could be published until unrelated
  text was reworded. The check now masks CommonMark code spans (a backtick
  run closed by a run of exactly the same length, on one line) before it
  looks for a fused marker; a marker outside code still refuses, and a span
  that crosses a line ending stays unmasked. The preview now runs the accept
  turn's own pre-publish validation (`successorCandidateRefusal`, the same
  function `derive_successor` runs before writing) and v1 runs the guarded
  first write's (`initialCandidateRefusal`). Both deliberation skills share
  the engine.
- **The two experimental skills agree on what an experiment heading is.**
  `experimental-deliberation` writes and validates an experiment as a heading
  carrying its `[exp:<id>]` declaration (cited as `[tests:<id>]` or `(Exp.
  <id>)`), while `experimental-implementation` located experiments only by a
  bare `## N` heading and counted only digit prose citations (`Exp. 3`). A
  document written the deliberation's way declared no experiment to the
  implementation skill, so every finding locus read as unknown and `compose`
  refused every replacement; documents had to carry both forms (`## N` wrapping a `###
  Experiment [exp:EN]` heading). The convention now lives in one file,
  `skills/_core/conventions/experiments.json` (identifier class, declaration
  and citation markers, prose form), read by both skills: the deliberation's
  `reference-experimental.ts`/`profile.ts` through `experiment-convention.ts`,
  and the implementation's `impl_profile.py`. The implementation skill now
  locates an experiment by a heading of any level carrying `[exp:<id>]`, its
  block running to the next heading of the same or a higher level, and counts
  `(Exp. <id>)` citations. `[claims:N]` crossings into the proposal are
  unchanged.
- **Each implementation skill binds its own document lineage.** On a target
  both `proposal-implementation` and `experimental-implementation` work on, the
  two read the same `src/<Package>/__init__.py`, and `__implementation__`'s
  `revision` held one name that each skill read as a revision of its own
  document. Bound to the proposal, the experimental skill's `verify` searched
  `experiments/` for a proposal family, discovered nothing and reported
  `fidelity: unknown` (and the reverse for the proposal skill); keeping one
  skill current meant re-binding away from the other. `revision` may now name
  one revision per document label, `{"proposal": "r03.md", "experiments":
  "experiments-<slug>-v02.md"}`; each skill reads only its own document 0's
  label. The scaffold template's comment named `proposals/` under both skills;
  it now names the loading skill's own document directory and label.

- **`init` and `upgrade` no longer copy unreleased framework code silently.**
  From an editable install the kit is the live checkout, and both commands
  copied it uncommitted edits included, with nothing recording which commit a
  workspace came from. Every `init` and every `upgrade` now writes
  `.papersmith/kit-source.json` (`version`, `commit`, `dirty`, `source`:
  `checkout`, `bundled` or `override`, `recordedAt`), and `papersmith status`
  reports it on a `Kit source:` line and under `framework.kit_source` in
  `--json`. A kit source tree with uncommitted or untracked changes under its
  shipped paths (`skills/`, `sections/`, `.claude/agents/`, the provisioning
  scripts, `requirements.txt`, `src/papersmith/`) refuses before anything is
  written, and so does one whose git state cannot be determined (unknown is
  treated as dirty). `--allow-dirty-kit` proceeds and records
  `allowedDirty: true`; the MCP `workspace_init` and `workspace_upgrade` tools
  forward it as `allow_dirty_kit`. `scripts/build-kit.py` now embeds the
  commit and dirty flag of the tree it copied into `kit-manifest.json`, so a
  wheel install records the commit it was built from; a bundled kit built
  dirty refuses too, and one built without provenance is admitted with the
  commit unknown. `upgrade --plan-migrations` writes nothing and does not
  refuse.

- **Scripts the CLI launches no longer write bytecode into the workspace.**
  `run_script` (every bridged skill script, from `audit` to `target check`)
  and `papersmith run`'s local job and Kaggle submission children inherited
  the parent environment unchanged, so a skill script importing a sibling
  module left `__pycache__/` inside the workspace's `skills/` kit copy. They
  now run with `PYTHONDONTWRITEBYTECODE=1` (one helper,
  `bridges.python.script_environment`; an explicit caller value still wins),
  the rule the MCP bridge and the dashboard child already followed.

- **One `upgrade` across a release now ends with `audit --check-drift`
  clean.** The routing docs (`CLAUDE.md`, `OPENCODE.md`,
  `.pi/APPEND_SYSTEM.md`, `.agents/AGENTS.md`) state the version the workspace
  records, and `upgrade` rendered them before it moved `.papersmith/version`.
  So every upgrade from an older release left them naming the old version,
  `audit --check-drift` reported them as generator drift, and only a second
  `upgrade` cleared it. They are now rendered again once the marker moves.
  Found by upgrading the populated 0.13.0 fixture below.

- **Deliberation engine state is ignored like the content it describes.**
  The workspace `.gitignore` keeps research content local (`proposals/*`,
  `experiments/*` and the rest), but `.proposal-deliberation/` and
  `.experimental-deliberation/`, where the two deliberation engines keep each
  revision's state, receipts and permanent locks, were neither tracked nor
  ignored. That state embeds and hashes the revisions the file already keeps
  local, so committing it published them, and it grows to megabytes. Both are
  now ignored, together with `backup/proposals/` and `backup/experiments/`,
  where the deliberation skills move revisions and their sidecars when
  reconciling a base. The set is checked against every `skills/*/profile.ts`
  the kit ships (its `artifact.sidecarRoot`, read through the engine) and by
  running the engine and asking git what it would track. The other skills'
  engine state already lives inside ignored folders (`paper/.paper-writing/`,
  `implementations/<target>/...`, `sota-pool/`).
- **`upgrade` no longer overwrites lines a workspace added to its
  `.gitignore`.** The file was re-rendered whole on every upgrade, so a user's
  own ignore lines were lost, and until then `status` and `audit
  --check-drift` reported the edit as drift. The framework's lines now sit in
  a delimited managed block: `upgrade` rewrites the block and keeps every line
  outside it, and drift is measured on the block alone. A file with no block
  yet (every workspace made before 0.14.0) is converted on its next upgrade:
  replaced whole when it is byte-identical to what the framework last wrote
  (the manifest's digest), and otherwise given the block with every line the
  block does not already carry kept below it, in order. Malformed markers
  are never guessed at: the file is left as it is, the run reports it as not
  written, and it stays drift until repaired.
- **The plausibility flow no longer starts a `paper/` tree.** `sota-scout`
  and `novelty-screener` confirm candidates through paper-writing's
  `resolve`, which cached every answer under `paper/.paper-writing/metadata/`
  by default, so exploring an idea wrote paper content before any paper
  existed. `resolve` gains `--cache-dir <dir>` (caches as
  `<dir>/<metadata_digest>.json`, refused outside the repository with
  `PAPER_OUTSIDE_REPOSITORY`, mutually exclusive with `--paper`), and both
  agents now pass `--cache-dir sota-pool/metadata`, keeping their caches in
  the pool. paper-writing's own calls pass nothing and keep caching under
  `paper/`, where `bib` and `full_text` read. The test reads the invocation out
  of each agent's definition and runs it against a workspace's shipped
  `paper_cli.py`.
- **`verify` reports per-section drift for the section labels revisions
  actually carry.** The implementation engine counted a heading as a section
  only when its first token was a bare number followed by a space
  (`## 3. Title`). Headings with an identifier label (`### O1. Objective`), a
  dotted label (`### 3.1`) or a label alone on the line (`## 3`, the legacy
  experiments form) produced no sections. `changedSections` stayed empty and
  `__provenance__["sections"]` was never compared with what moved, so only
  the file-level revision drift worked. The label grammar now lives once, in
  `skills/_core/conventions/sections.json`, and both implementation profiles
  pass it to the engine as `documents[0].section_heading`.
  `experimental-implementation` adds the experiment heading's `[exp:<id>]` as
  a marker, so its drift is reported per experiment id. A labelled heading
  nested under another is its own section and still part of its parent, and
  the parent covers the same lines it did before. `proposal-deliberation`
  documents the labels to use for sections that should be tracked.
- **`settle` places items in the order they were settled, never inside the
  position block, and `--reverse` opens its own heading.** The create path
  inserted each new item at the section's first checklist line, so a
  section read newest first. On the holder `position` creates, that first
  line is the position block's own item, so the documented
  `settle --under "## Ladder"` wrote into the block and `verify` then refused
  `POSITION_ITEM_MALFORMED`. A new item is now appended after the section's
  last checklist item, skipping the block's lines. If the section's only
  items are the block's, the new item goes right after `<!-- /position -->`.
  `settle --reverse` refused `SETTLE_HEADING_ABSENT` until someone added
  `## Reversed` by hand; now the first reversal adds that heading at the end
  of the file, in the same write as the deletion. A tick still cannot be
  undone. The correction path, now documented, is `settle --reverse` on the
  ticked line (the explanation and the ledger event stay) followed by a new
  `settle --under`.
- **`position.attainedLevel` no longer claims a rung nothing ran.** A
  sequence with no leveled (`:level`) witness reported the ladder's top
  rung, so an all-two-state position aimed at `pilot` read `attainedLevel:
  full` with no full-scale run behind it. With nothing leveled, attainment is
  now the rung the position aims at (`targetLevel`), and `null` when the aim
  is not on the ladder. Sequences with leveled witnesses read as before.
- **`verify`'s `prose` check no longer reports the engine's own writes.**
  After re-binding to a successor revision, `prose.staleRevisions` named the
  position block header in `<Name>/AGREED.md`, which records the revision it
  was derived from, and `prose.unresolvedSymbols` named the
  `` `test_<id>` `` witness token that `settle --attach` had written. In a
  checklist holder (this skill's declared filename or a sibling skill's), the
  check now skips the position block's opener and closer lines, the witness
  token at the end of an agreement line, and the append-only `## Reversed`
  section. The rest of the holder is still checked, including an
  agreement's own text, and the same lines in any other document are still
  reported.
- **An implementation skill no longer runs under the other skill's profile
  inherited from the environment.** Each launcher `setdefault`s its own
  `IMPLEMENTATION_DOMAIN_PROFILE`, so an explicit value wins. A shell, or an
  earlier process that ran the other skill, could leave the other skill's
  `impl_profile.py` exported, and this skill then read the other skill's
  documents and holder (for example `AGREED.md` from
  `experimental-implementation`) without saying so. Both launchers now refuse
  `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING` (exit `2`, before the engine loads)
  when the inherited value resolves to another skill's own profile, naming
  both profiles. Any other explicit value, such as a test fixture profile,
  still wins. The test that leaked this skill's profile into later tests of
  the same process now restores the environment.
- **The engine's ambiguous-family mutation test no longer rewrites the
  shipped engine.** `tests/test_implementation_pair.py` wrote its mutation
  into `skills/_core/implementation/engine/implementation_engine.py` and
  restored it on cleanup, so a parallel worker could run the mutated engine
  and a crash could leave `MUTATED` in the tree. It now mutates a scratch
  copy of the engine tree and runs a copy of the launcher against it; the
  shipped file is asserted unchanged. Test-only: nothing a workspace runs
  changes.
- **Executing a kit-placed notebook is no longer structure drift.** Running
  `verification.ipynb` or `probe.ipynb` in place rewrites its outputs,
  execution counts and kernel metadata, and `verify` reported the notebook in
  `structure.scaffoldDrift`/`harnessDrift` until `materialize --authored`
  re-sealed it. A notebook destination's seal now also reads its source
  content (each cell's type and source, in order): the materialize stages,
  `--authored` and `--adopt` record it as `writtenSourceSha256`, and a match
  on either the full bytes or the source content is sealed. A changed cell
  source or cell type still drifts, and a notebook that is not readable JSON
  is compared on its full bytes only. Receipts written by 0.13.0 keep
  reading: an engine-written entry's source content is rebuilt from the kit
  and trusted only when it hashes to the entry's `writtenSha256`.
- **An unmeasured `@step` mark now says why, and what the step digest
  covers.** A step's verdict counts only while `suite_digest` (every `.py`
  under `src/` and `tests/`, plus the environment manifests) still matches,
  so a test-only edit turned every earlier step mark unmeasured with nothing
  saying so. The scope is kept: a step's callable may run the suite, read a
  file under `tests/` or spawn a subprocess, and the engine cannot see which,
  so a narrower digest could leave a mark satisfied over code the step runs.
  Each unmeasured `@step` item in a position state's `unmeasured` list now
  carries `reason` (no verdict yet, or the last run no longer counts, with
  the exact `step` command that clears it) and `digestScope`. Documented in
  `SKILL.md` and `references/usage.md`, with the advice to commit code and
  tests before the first pilot step.
- **A cost forecast says what parallelism its duration was taken at.**
  `probe`'s `search.costForecast` and the benchmark's `projectedCost` scale
  one recorded duration, and read it as if runs never competed: a pilot on
  eight workers took 2.42 times the projection, one arm about five times.
  Both now carry `parallelism`, `contention` and `basis`. A record whose
  `reduction` names `parallelism` (a positive integer) is projected from
  that run's own duration, `contention: "included"`, holding at that
  parallelism only. Otherwise the forecast is labelled single-process with
  `contention: "unmeasured"`, and no contention factor is supplied. A
  malformed `parallelism` is echoed as `parallelismMalformed` and never read.

- **A successor locus is matched by its heading's own words, and an outer
  section can be named.** `RESOLVE_TARGET` (and `CREATE_SUCCESSOR`'s
  `selectedEntryId`/`selectedEntryIds`, which share its resolver) tested each
  query word as a substring of the heading line, so `O1` also matched
  `O10` and blocked; two headings carrying the same words tied even when
  one of them was exactly the query; and nested matches collapsed to the
  innermost one, so once `### Synthetic data` existed `## Data` could not be
  targeted at all and a label line directly under it could not be edited.
  A query word now matches a whole heading token (a dotted identifier such
  as `3.1` stays one token; the parts of a hyphenated word still count); a
  heading whose words are exactly the query's, ignoring its section label
  (read from `_core/conventions/sections.json`) and stopwords, outranks one
  that merely contains them; and a query opening with level marks (`## Data`)
  considers only headings of that level. Nested matches are no longer
  collapsed: the gate decides on the scores. A blocked result lists every
  candidate with its level marks and its real heading path
  (`### Methods › Setup`), and `RESOLVE_TARGET` returns them as
  `candidates`.

- **A successor that inherits a link to the previous revision's companion
  artifacts says so.** Nothing in the engine writes the companion-picture
  line: the deliberation links `proposals/<revision>.graph.html` (rendered
  from `<revision>.sky.json`) from the revision's own text. A successor copies
  every byte outside its locus, so r02 kept pointing at r01's picture and
  nothing flagged it. `CREATE_SUCCESSOR` now reports every reference in the
  successor to a file named after another managed revision with a suffix
  other than `.md`, as `staleCompanionReferences` (`reference`, `revision`,
  `inherited`), on the preview, on the published result and in the receipt.
  The engine never rewrites the line or renders the picture; a replacement of
  the line inside the successor, deliberated and validated like any other
  edit, clears the flag.

- **A successor can delete the document's first section.** A managed
  revision opens with the artifact marker line and one newline, so removing
  the first section left the marker and the next heading one line break
  apart, and `derive_successor`'s removal-join check refused it as
  `successor-markdown-block-safety` (since A6 already at the preview, as
  `CANDIDATE_VALIDATION_FAILED`). The marker is an HTML comment line no block
  can fuse into, so a removal whose left side is exactly the marker is now a
  clean join; every other single-newline join is still refused.

- **`experimental-deliberation`'s usage guide names the heading v1 really
  writes.** It said source fragments are pasted under `## Paper Guide
  Reference`; the renderer writes this profile's `sourceReferenceHeading`,
  `## Reference Sources`, as `SKILL.md` already said. The usage-doc drift test
  now holds every heading the guide and `SKILL.md` say the engine writes
  ("under a `## X` heading", "the `## X` block") against the v1 the worked
  example actually renders and the profile's change header.

- **`verify` reports a notebook that is not a notebook instead of crashing.**
  A file under `<Name>/Notebooks/` whose bytes were not UTF-8, were not JSON,
  or were JSON whose top level is not an object made `verify` (and `probe`)
  exit with a traceback: the seal check and the prose check read it without
  the guard the execution check already had, and the execution check itself
  crashed on a JSON array or string. Every notebook reader now shares one
  read (`read_notebook_document`). The file is reported as `unreadable`,
  `sealed: false`, `sourcesMatch: null`, listed under `unsealed`, and the
  notebooks verdict reads `drift`, so it never passes for a sealed report.

- **`papersmith status` reads a proposal's stage from the engine's own
  state.** It probed only the legacy `proposals/deliberated/` and
  `proposals/accepted/` folders, which nothing writes any more, so every
  current proposal printed as `(draft)`. The latest managed revision's stage
  now comes from its publication receipt
  (`.proposal-deliberation/receipts/<file>.json`): `published` when the
  receipt is committed and its `documentShaAfter` is the document's current
  digest, `edited-after-publication` when the bytes changed since, `draft`
  when no committed receipt exists. The legacy folders are still read first,
  so an old workspace keeps its stage.

- **A fresh target walks `env` -> `plan` -> `apply` -> `materialize` without
  a hand commit in between.** `env` built `.venv/` before anything ignored
  it, so the `plan` that follows refused `DIRTY_WORKTREE` on a `git init`
  target, and the `pip install -e .` that `env` prints left an untracked
  `src/<dist>.egg-info/` that refused the next clean-requiring step again.
  `env` now appends `.venv/` and `*.egg-info/` to the clone's own
  `.git/info/exclude` before it builds anything (reported as `excluded`), so
  no tracked file changes and anything else untracked still refuses. The
  `.gitignore` block `apply` and `materialize --stage scaffold` author also
  carries `*.egg-info/` (not a scaffold gap on its own). The plan approved
  before `apply` stays `PLAN_STALE` for `materialize` (apply carried out its
  `createDirs`); the refusal now says so and the lifecycle (re-plan once
  `apply` has run) is documented in `proposal-implementation`'s usage guide.
  Shared by `experimental-implementation`.

- **The array backend is declared, not inferred from a helper's imports.**
  The kit's `tests/conftest.py` and `tests/sweep.py` imported numpy for a
  seeded generator, so a target whose modules compute in torch read as
  `mixed` and `probe` routed it to `convert` with no way out. Both kit files
  are now backend-neutral (`random.Random`, `SEED`, `configuration_seed`),
  the scaffold `pyproject.toml` (template and default) lists no array
  backend, and a target may state `__backend__ = "torch"` (or `"numpy"`,
  `"jax"`, `"tensorflow"`) in `src/<Package>/__init__.py`: `probe`'s
  `backend` then follows it (`declared-unmet` when no package file imports
  it; any other value is `unrecognized-backend`, never trainable). With
  nothing stated, import inference is unchanged. `env --torch cpu|gpu
  [--torch-version X]` adds the torch build to `nextCommand`: CPU uses the
  PyTorch CPU index and an exact `torch==X+cpu` pin (refusing
  `TORCH_VERSION_REQUIRED` without an exact release), GPU the default
  index's build. Shared by `experimental-implementation`.

- **The default `smoke_and_invariants` profile runs the target's own
  interpreter against the target.** It substituted the workspace folder name
  for `{paper_slug}` (`implementations/<workspace>/tests/...`, a directory
  no target is named after) and ran `pytest` from PATH. `papersmith run`
  now resolves two new placeholders, `{target}` (`implementations/<name>`,
  the only directory there or the one `--implementation <name>` picks) and
  `{target_python}` (that target's `.venv` interpreter), and the
  `papersmith init` template uses them (`{target_python} -m pytest
  {target}/tests/test_invariants.py`; the remote profiles name `{target}`).
  An unresolvable target (none, several without `--implementation`, an
  unknown name, or no `.venv` when `{target_python}` is named) refuses before
  anything is dispatched or recorded; `--dry-run` reports it under
  `target_resolution` instead. Profiles naming neither placeholder run as
  written.

- **A sibling's profile from another skills tree no longer passes the
  launcher.** The `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING` guard compared
  skills roots only, so an inherited `impl_profile.py` of the other
  implementation skill from a second checkout or workspace was accepted and,
  for example, `experimental-implementation` read `AGREED.md`. Both
  launchers now read the skill a profile declares (the skill directory of
  its `PROFILE["cli"]["path"]`) and refuse any other skill's profile
  wherever it lives; this skill's own profile, and a fixture profile naming
  this launcher, still run. A sibling in the same tree is still refused by
  path even when it cannot be loaded.
- **A first revision's title and section heading no longer end in a full
  stop.** `CREATE_INITIAL_REVISION` takes the title from the idea's first
  sentence and the section heading from its second, and kept each sentence's
  terminal punctuation, so v1 opened with `# My idea.`. Both headings now drop
  their terminal `.`, `!` or `?` run (punctuation inside the sentence is kept);
  the slug is unchanged. Taking the heading from the second sentence and
  repeating the idea verbatim as the section body stay as they were and are now
  documented as intended: the headings are labels capped at 200 characters, the
  body is the only place the whole idea survives. Both deliberation skills'
  `SKILL.md` and `references/usage.md` state the derivation; the proposal
  usage example, a single sentence that `INITIAL_IDEA_SINGLE_SENTENCE` refused,
  now has two.
- **The 65,536-character instruction cap is enforced on the CLI, documented,
  and reported.** `proposal_deliberation_execute` declared `instruction` as
  `maxLength: 65536`, but the CLI host calls the tool directly and nothing on
  that path read the schema, so the cap a Pi session met did not exist for
  `cli.mjs` and no document stated it. One exported constant
  (`MAX_INSTRUCTION_CHARACTERS`) now feeds the schema and a check at the top of
  the tool's `execute`: a longer instruction is refused on every operation and
  host with `INSTRUCTION_TOO_LONG` (`nextAction: "shorten_instruction"`),
  nothing written. The `CREATE_SUCCESSOR` preview and the
  `CREATE_INITIAL_REVISION` result carry
  `instructionBudget: { limit, used, remaining }`. Both deliberation skills'
  `SKILL.md` and `references/usage.md` state the cap.
- **The first revision's source window is reported, warns when it cuts, and
  can be widened.** `CREATE_INITIAL_REVISION` reads at most 4000 bytes across
  every declared source, in declaration order (for the experiments domain the
  data paper first), and cut the crossing document mid-text and skipped every
  later one in silence: a data paper over 4000 bytes left the managed proposal
  out of v1 with nothing saying so. Every result that composed a document now
  carries `sourceWindow` (`limitBytes`, `loadedBytes`, one
  `{path, bytes, loadedBytes, status}` per document) and a
  `SOURCE_WINDOW_TRUNCATED` warning naming what was cut or left out;
  `sourceWindowBytes` (1 to 262144) widens the window for one creation
  (`SOURCE_WINDOW_INVALID` outside that range, `SOURCE_WINDOW_UNSUPPORTED` on
  another operation). The experimental `SKILL.md` no longer claims that only
  `<source>/<folder>/<folder>.md` is loaded and that `proposals/` contributes
  presence only (flat files have been read since the flat pass); both rules,
  the order and the window are documented in both skills.
- **An experiments plan can state its fixed settings in a table.**
  `report-table-fabricated-value` refused any digit in a body cell past column
  one of every table but a baselines table, so `| learning rate | 3e-4 |`
  blocked `CREATE_INITIAL_REVISION` and every successor as a "fabricated
  result". A table whose first header cell is, whole and case-insensitively,
  `Parameter`, `Parameters`, `Hyperparameter` or `Hyperparameters` is now a
  parameters table: a declaration of settings the plan fixes, exempt from the
  rule and from the baseline rules. Every other table keeps the rule, including
  one whose first header cell merely contains the word (`Parameter count`) or
  carries it in another column. Documented in `experimental-deliberation`'s
  `SKILL.md` and its usage example.
- **A remedy test's control is recognized however it calls the
  implementation.** `audit.remediesWithoutControl` accepted a
  `test_remedy_<id>` only when it called a name imported with `from <Package>
  import <name>` directly by that bare name, so `kernel.f(...)`,
  `import <Package>.kernel as k; k.f(...)`, `<Package>.kernel.f(...)` and a
  same-file helper doing any of those were reported as having no control,
  holding the audit at `incomplete`. The detection now follows attribute calls
  to the name they start from and same-file helpers to a fixed point. It still
  requires a call into the target's own package: importing without calling,
  passing a function along uncalled, and calling an unrelated import remain no
  control. Shared by `experimental-implementation`. Documented in
  `proposal-implementation`'s `references/usage.md`.
- **The objects stage follows the approved object map instead of a fixed
  file name.** `materialize --stage objects` always wrote
  `src/<Package>/module.py`, and `verify`'s `structure.objectGaps` reported it
  missing on any target without it, even one whose map had been written as
  modules of their own names, so the structure could not read `ok` without a
  file nobody asked for. `--module <name>` now names the module the stage
  writes (`src/<Package>/<name>.py`, from the same template, sealed and
  releasable with `--authored` like `module.py`), refusing
  `MODULE_NAME_INVALID` and `MODULE_STAGE_MISMATCH` for a name that cannot be
  a module file or a mode other than `--stage objects`. Without the flag the
  module destination is owed, and written, only while the package holds no
  module of its own. Targets that already carry `module.py` verify unchanged.
  Documented in `proposal-implementation`'s `SKILL.md` step 9 and
  `references/usage.md`.
- **Kit placeholders are filled when their value is known, and fail clearly
  when not.** `materialize` substituted only `{{PKG}}` and `{{SEED}}`, leaving
  values the engine already held to be filled by hand: the product name, the
  bound revision (`tests/test_smoke.py`, `tests/admissibility.py`, the
  verification notebook) and the module name. Unfilled, they failed as
  `'r01.md' != '{{REVISION}}'`, a remedy refused "against revision
  '{{REVISION}}'", or a collection `SyntaxError` for `def {{FUNCTION_NAME}}`.
  The scaffold stage now fills `{{NAME}}`, and `{{REVISION}}` when the target
  declares one or the approved plan was taken with `plan --revision`. The
  objects stage fills `{{REVISION}}`, `{{NAME}}` and `{{MODULE}}` in what it
  writes, and fills the same tokens into every scaffold file still
  byte-identical to its receipt, re-sealing each entry (listed under an
  additive `filled` key); a file somebody edited is never touched. Whatever is
  still unanswered fails naming the step that answers it: `admissibility.py`
  and `test_smoke.py` say the revision or the module is not known yet, and the
  kit's `conftest.py` collects a test file whose placeholders keep it from
  parsing as one failing item naming them. Receipts record each entry's
  substitutions. Documented in `proposal-implementation`'s `SKILL.md` steps 5
  and 9 and `references/usage.md`.

- **`status` and `audit --check-drift` no longer print projection warnings
  on every call.** Both re-render the runtime projections to compare them,
  and rendering the Pi agents emitted a multi-line `UserWarning` (`agent
  '<name>': tool 'WebSearch' has no Pi tool; not granted`) each time, so a
  healthy workspace read as faulty in a read-only command. The two commands
  now collect those notes: `status --json` carries them under
  `framework.generator_notes`, and `status --verbose` / `audit --check-drift
  --verbose` print them to stderr as `note: ...`. `init` and `upgrade`, which
  write the projections, still emit them as before. Documented in the
  manual's `status` and `audit` reference.

- **`proposal-implementation`'s docs name the checklist holder it declares.**
  `SKILL.md` (the checklist doctrine, the `agreements` status row and the
  `close` refusal row) and `references/usage.md` still called the holder
  `AGREEMENTS.md`, a name from one early commit; the profile declares
  `AGREED.md`, which is the file `settle` writes. A new drift test checks that
  every `*AGREE*.md` a skill's docs spell is a holder some implementation
  profile declares.

- **`materialize --authored`/`--adopt` say which paths they accept.** Naming
  any other path refused `NOT_A_KIT_DESTINATION` with "is not one of this
  stage's kit destinations" and nothing else, and no doc listed the set. The
  refusal detail now lists every accepted path (for `--authored`, including a
  file the objects stage recorded under a `--module` name), and
  `proposal-implementation`'s `references/usage.md` lists the set under "The
  sealed set", kept equal to the engine's `all_kit_destinations` by a test.

- **`papersmith implement` says what it bridges and what it does not.** The
  bridge runs nine of the engine's commands (`env`, `name`, `plan`, `apply`,
  `admit`, `handoff`, `compose`, `probe`, `verify`), and its `--action
  materialize` was an undocumented alias of `apply` — the layout migration —
  while the engine's own `materialize --stage/--authored/--adopt` was
  unreachable through it. The alias keeps working and now prints a note on
  stderr saying which command it runs and how to reach the engine's
  `materialize`; an unsupported action is refused naming the bridged commands
  and the direct `implementation_cli.py` route; `--action`'s help lists both.
  The manual's `papersmith implement` section lists the direct-only commands
  (a test keeps it equal to the engine's `COMMANDS` minus the bridge).
- **Direct engine use documents its two inputs.** `proposal-implementation`'s
  `SKILL.md` and `references/usage.md`, `experimental-implementation`'s
  `SKILL.md` and the manual now state that a hand-set
  `IMPLEMENTATION_DOMAIN_PROFILE` must be absolute
  (`IMPLEMENTATION_DOMAIN_PROFILE_NOT_ABSOLUTE`), and define the `--session`
  id the ledger-writing commands require: chosen by the caller, one per
  working session, one shell-safe token, stamped verbatim as attribution and
  never validated.

- **The `sota-grapher` agent runs the atlas checker with the pool.** Its
  repair loop ran `check_atlas.py sota-pool/atlas.json` without `--pool`, so
  the quote-fidelity guard added to the checker never ran inside the stretch
  that draws the quotes. The agent now runs
  `check_atlas.py sota-pool/atlas.json --pool sota-pool/candidates.json`; the
  OpenCode, Pi and `.agents` projections are regenerated from it, and a test
  reads every agent definition that runs the checker on the atlas.

### Added

- **A populated 0.13.0 workspace fixture, and a test that upgrades it.**
  `tests/fixtures/workspace_v0_13_0/` holds a workspace produced by the
  0.13.0 release itself (`scripts/build-v0_13_0-fixture.py` drives that
  tree's own CLI and engines): two managed proposal revisions and one
  experiments revision with their receipts, state and locks, and an
  implementation target with its scaffold receipt and seal file, both
  implementation skills' holders with settled items, and their position
  ledger. `tests/test_upgrade_v0_13_0_workspace.py` upgrades it with the
  current CLI and asserts that nothing it holds changes except the listed
  `.papersmith/` records, that every registered migration applies or is
  already satisfied, that `audit --check-drift` is clean, and that the
  deliberation consistency audit and both implementation `verify` runs still
  read what 0.13.0 wrote. `tests/fixtures/README.md` documents how it is built
  and stored.
- **`CREATE_INITIAL_REVISION --dry-run`: see the first revision before it
  exists.** A successful creation leaves
  `<sidecarRoot>/locks/initial-revision.lock` in place for good (the
  slug-independent single-winner guard), so the only way to see v1's filename,
  derived headings and canonical-form verdict was to create it, after which
  every further attempt is refused. `cli.mjs --dry-run` (or `"dryRun": true`
  in the request) runs every check and the composition and returns
  `status: "preview"` with the would-be `targetFilename`, `canonicalMetadata`
  and composed `markdown`, without taking the lock or writing anything. A
  present lock is reported as the `MANAGED_PROPOSAL_ALREADY_EXISTS` the real
  call would meet and is never touched. `dryRun` on any other operation is
  refused `DRY_RUN_UNSUPPORTED` rather than ignored. Existing locks are neither
  removed nor reinterpreted. Documented in both deliberation skills' `SKILL.md`
  and `references/usage.md`.
- **A successor receipt can record why the change was made and who decided
  it.** Receipts kept only an `instructionHash`, so a published revision could
  not say why it existed or whether a person or an agent took the call.
  `CREATE_SUCCESSOR` accepts two optional fields, `rationale` (at most 2000
  characters) and `decider` (`agent` or `human`), and the successor's receipt
  records them verbatim beside the hash. Malformed values are refused
  `DECISION_RECORD_INVALID` at the preview, and either field on another
  operation `DECISION_RECORD_UNSUPPORTED`. Documented in both deliberation
  skills' `SKILL.md` and `references/usage.md`.
- **`ADOPT_INITIAL_REVISION`: adopting an existing document as v1 gets the
  same state, receipt and validation as creating one.** Both deliberation
  skills offered "adopt it as v1" and the only way was by hand (prepend the
  marker, rename the file), which left no committed state and no receipt
  (`runConsistencyAudit` reported `MISSING_MANIFEST`) and skipped the
  canonical-form gate and pre-publish validation, so a document breaking the
  domain's rules entered the lineage unexamined. The new operation, with
  `sourceFilename` naming an unmanaged `.md` in the managed directory, runs
  that gate and publishes the file's bytes through the creation path itself
  (lock, exclusive write, state, receipt with `operation:
  "CREATE_INITIAL_REVISION"` and an additive `adoptedFrom`), named after its
  first `# ` title; the source is left in place for the agent to back up. With
  `sourceFilename` naming an old hand-adopted v1 it is the explicit repair
  path: after the same gate it writes that revision's state and receipt,
  bytes untouched, and refuses one that already has a receipt
  (`ADOPTION_ALREADY_RECORDED`). Accepts `--dry-run`. Documented in both
  deliberation skills' decision trees, operation tables and usage.
- **An audit that found nothing can be ruled on.** `admit` refused
  `NO_FINDINGS` whenever `tests/findings.py` declared an empty list, so a
  target whose audit found no defect could never record it and `verify` stayed
  at `audit: none`, the answer a never-audited target gets. `admit
  --no-findings` now records an empty ruling (`"findings": {}`,
  `"noFindings": true`) bound to the revision's bytes; `verify` reads it as
  `audit: ok` with an additive `noFindings` key, and as `incomplete` once the
  revision moves. Plain `admit` on an empty list still refuses `NO_FINDINGS`
  (its detail now names the flag), and the flag with findings declared refuses
  `FINDINGS_DECLARED`. Shared by `experimental-implementation`, which runs the
  same engine. Documented in `proposal-implementation`'s `SKILL.md` step 11
  and `references/usage.md`.
- **A defect that lives in the prose can be declared as a finding.** A
  finding's correction was only expressible as one numbered equation rewritten
  in place: the kit's `test_audit.py` required a non-empty `remedy_equations`,
  `compose` substitutes at the equation's own `\tag{n}`, and `verify` kept
  asking for a `remedy_block` that nobody can write for a sentence with no tag.
  A finding may now declare `"remedy_in_prose": True` with its remedy locus
  list empty and no `remedy_block`: it is admitted on the same notation and
  adoption checks, never listed under `localRemediesNotWritten` (so no
  `toDiscuss` entry), and `handoff` defers it as `prose-remedy` to a
  deliberation session of its own. Declaring it beside remedy loci, or with a
  value other than `True`, is ruled inadmissible; without the flag an empty
  locus list reads exactly as before. The kit's `findings.py` documents the
  field and `test_audit.py` accepts it. Shared by `experimental-implementation`.
  Documented in both implementation skills' `SKILL.md` and
  `proposal-implementation`'s `references/usage.md`.
- **An experiments document can declare a proposal claim out of scope.**
  `agree` reported every declared claim no experiment cites as
  `untested:<id>`, and the only way past one was `--acknowledge
  untested:<id>`, request-scoped by design and so retyped on every call, with
  nothing in either document recording the decision. The shared experiment
  convention (`skills/_core/conventions/experiments.json`) now registers an
  `outOfScope` marker, `[out-of-scope:<id>]`; the experimental profile's
  crossing reads it (an optional `cross_citation.out_of_scope` pattern, held to
  the one-group rule), and `agree` subtracts a declared, uncited claim marked
  that way from `untested` and echoes it under `outOfScope`. The marker clears
  nothing else: a citation to an undeclared claim stays `absent`, a marker
  naming an undeclared claim subtracts nothing, and a document without one
  reads exactly as before. Documented in `experimental-deliberation`'s
  `SKILL.md` (where the document is written) and `experimental-implementation`'s
  `SKILL.md` and `references/usage.md`.

- **`paper-ingestion` can OCR every page instead of trusting a poor text
  layer.** Marker rebuilds digital tables from the PDF's own text layer
  (`tables_pdftext`) in both `fast` and `balanced` mode, so a text layer that
  is present but poor produced confidently garbled tables and switching
  `--mode` could not avoid it. `extract_pdf.py --force-ocr` (or
  `force_ocr: true` under `paper_ingestion:` in `papersmith.yaml`) hands
  Marker its `force_ocr` option: no text layer is extracted and every page,
  tables included, is rebuilt by OCR. Off by default; a non-boolean
  `force_ocr` is a configuration error reported before any model loads.
  Documented in the skill's `SKILL.md` ("Tables from a poor text layer") and
  the manual.

- **`walk` commits under a subject the target's convention accepts.** The
  walker commits what each step produced (`step` refuses on a dirty tree), and
  the subject was fixed at `walk: <step>`, so a target enforcing Conventional
  Commits through a hook or a lint refused the walk's commits or carried
  history its own policy rejects. `walk --commit-template '<subject>'` now
  shapes it, with `{step}` as the one placeholder (`chore(walk): {step}`).
  The default stays `walk: {step}`. A template with no `{step}`, any other
  brace, or more than one line is refused `WALK_COMMIT_TEMPLATE_MALFORMED`
  before anything runs. Shared by both implementation skills; documented in
  `proposal-implementation`'s `SKILL.md` and `references/usage.md`, and in
  `experimental-implementation`'s `SKILL.md`.

- **The plausibility checker can hold every quote to its abstract.**
  `check_atlas.py` certified shape only, so a paraphrase or an invented
  sentence dressed as a quote ran green. `check_atlas.py <atlas> --pool
  sota-pool/candidates.json` now requires each planet's `evidence.origin` to
  name a pool candidate (`identifier`, `source_url` or `url`;
  `EVIDENCE_ORIGIN_NOT_IN_POOL`), that candidate to hold an abstract
  (`EVIDENCE_ABSTRACT_MISSING`), and the quote to be a verbatim substring of
  it (`EVIDENCE_QUOTE_NOT_IN_ABSTRACT`); whitespace runs compare collapsed,
  nothing else is normalized. An unreadable or malformed pool exits 2. The
  plausibility `SKILL.md` documents the invocation and, measured from
  `paper_resolve.py`, what each resolver cannot give the pool: Crossref never
  returns an abstract (and reports no year), arXiv reports `year: null` and
  `venue: "arXiv"`.

### Changed

- **Workspace support policy: a live workspace is upgraded, never
  re-initialized.** This supersedes the 0.8.0 note "existing workspaces are
  not migrated; re-run `papersmith init` in a fresh workspace", which would
  discard a paper's ledgers, receipts, seals and managed revisions. From
  0.14.0 on, every release that changes the shape of something a workspace
  already holds ships, in the same release, a migration in `upgrade`'s
  registry or a compatibility read that keeps the old shape reading, and says
  which under Behaviour changes. Workspaces recorded at 0.12.0 or later (the
  first release with artifact migrations) are supported; older ones still
  upgrade, but pre-0.12.0 shape changes have no migration (0.8.0's
  `.antigravity/` files are not removed). Documented in `docs/releasing.md`
  ("Workspace support policy"), the `upgrade-project` skill and the manual.

### Behaviour changes

- `admit` returns a new `adopted` map (present only when some finding is
  adopted), and `tests/admissibility.json` carries
  an optional `adopted` key on each adopted finding's verdict. Both are
  additive: rulings written by 0.13.0 carry no such key and keep reading
  unchanged, so no migration is needed.
- `verify`'s `audit` gains an `adopted` map, present only when some finding is
  adopted. A target whose only blocker was
  an adopted finding now reads `audit: ok` instead of `incomplete` or
  `needs-deliberation`.
- Under a profile declaring more than one document, adoption is read from the
  document(s) a finding names, the same text `admit` already checked the
  marker against, instead of always from document 0.
- A target holding the other implementation skill's declared holder (and no
  holder of this skill's own) no longer refuses `HOLDER_UNDECLARED` on
  `position --sequence`, `position --reconcile` or `settle`: the write creates
  this skill's declared holder with its scaffold and leaves the sibling's file
  byte-identical. Workspaces that already created their own holder by hand
  keep resolving it as declared; no migration is needed.
- `verify`'s `agreements` (and the same reader in `close`) no
  longer counts the other implementation skill's declared holder: a target
  whose only checklist is the sibling's now reads `agreements: absent` instead
  of the sibling's items, and a new `siblingHolders` list names the skipped
  file. The key is present only when such a file exists, so other targets read
  byte-identically. The position section likewise reads `absent` until this
  skill installs its own block, instead of the sibling's.
- `probe` on a target with no prior-work package under `src/` and a declared
  `__steps__` flow now answers `pilot-first` or `pilot-decisions` where it
  used to answer `nothing-to-compare`, and publishes those rungs' questions
  in `resolve` and `toDiscuss`. Targets that declare no flow, or whose pilot
  is complete and every step decided, still read `nothing-to-compare`. No
  stored artefact changes shape; no migration is needed.
- `verify`'s `fidelity.missingProvenance` no longer names
  `src/<Package>/report_digest.py` while it is unmodified, so a target whose
  only provenance gap was the seal now reads a non-`drift` fidelity status.
  Existing 0.13.0 targets benefit without any action: the exemption also
  accepts the bytes their own scaffold receipt recorded. The receipt shape is
  unchanged; no migration is needed.
- `close` on a target declaring no flow now records the close (status
  `closed`, `positionOwed: false`) where it used to refuse `POSITION_ABSENT`.
  A target declaring any part of a flow still refuses, and the detail now
  names what it declares. `positionOwed` is absent whenever a position was
  owed.
- `verify`'s `agreements.witness` gains `decided` (lines closed by `settle
  --done --unwitnessed`, with reason, session and time) and `handTicked`
  (ticked witness-less lines with no such record), each present only when
  non-empty. Lines ticked by hand in a 0.13.0 holder keep counting as
  settled and stay under `unwitnessed`; they are now also named under
  `handTicked`. The `settle` ledger event and response carry `unwitnessed`
  and `reason` only on the new act. Additive; no migration is needed.
- `SETTLE_NOT_WITNESSED`'s detail and question now name `--unwitnessed` for a
  line no test could witness. Three new refusals: `SETTLE_UNWITNESSED_CONFLICT`,
  `SETTLE_REASON_REQUIRED` (a work state whose question asks the operator
  why) and `SETTLE_WITNESS_PRESENT`.
- `proposal-deliberation` and `experimental-deliberation`: a successor
  preview whose candidate the accept turn would refuse now answers `blocked`
  / `CANDIDATE_VALIDATION_FAILED` instead of `awaiting_acceptance`; the
  validation carries the accept turn's refusal under `candidateValidation`,
  `results.prePublish` and `prePublishApplicable`. Such a token could never
  be spent, so no publishable flow changes.
- `CREATE_INITIAL_REVISION` refuses a composed v1 that fails the structural
  pre-publish validation (oversized or reserved bytes, malformed display
  blocks, a heading fused into prose outside code) with
  `INITIAL_REVISION_CANDIDATE_VALIDATION_FAILED` and `nextAction:
  repair_candidate_markdown`, where it used to publish a v1 that blocked
  every successor. A heading marker inside a code span now passes at all
  three points. Existing managed revisions, receipts and ledgers are not
  re-validated and keep reading; a 0.13.0 v1 that carries an inline-code
  `## ` becomes able to publish successors. No migration is needed.
- `experimental-implementation` reads experiments documents in three forms:
  the canonical heading carrying `[exp:<id>]`, and both legacy forms (a bare
  `## N`, and `## N` wrapping an `[exp:<id>]` heading). Managed revisions are
  never rewritten: a 0.13.0 experiments document keeps every id it declared
  (`N`), and a legacy dual block also declares its nested `<id>`, so findings,
  `__provenance__` claims and `admissibility.json` rulings that cite `N` keep
  reading, and new ones may cite `<id>`. Inside one legacy block both ids name
  the same experiment: `compose` accepts a replacement carrying both (a new,
  optional `block_locator.block_aliases` profile leaf, off unless declared;
  `proposal-implementation` does not declare it and is unchanged). The
  migration is a compatibility read; no workspace artefact changes shape and
  no `upgrade` migration is needed.
- `__implementation__["revision"]` accepts a mapping keyed by document label.
  A bare string keeps its meaning (the reading skill's own document) and reads
  exactly as before under both skills; nothing rewrites existing declarations,
  and the engine still writes `"revision": ""` into new scaffolds (only the
  comment above it changed). A mapping without the reading skill's label
  leaves that skill's revision unanswered (never another lineage's name): with
  empty `premises` the declaration reads `undeclared` with a detail naming the
  label, otherwise `materialize --stage objects` refuses
  `OBJECT_MAP_NOT_APPROVED` naming `revision`. A non-string value under the
  label reads `undeclared`. The reader's contract carries the full mapping as
  `revisionByDocument`. Declarations live in target repositories under
  `implementations/`, not in the workspace kit, so no `upgrade` migration
  applies.
- `papersmith init` and `papersmith upgrade` refuse (exit 1) when the kit
  they resolve is a checkout or `PAPERSMITH_KIT_ROOT` tree with uncommitted
  changes under its shipped paths, or whose git state cannot be read. Users of
  an editable install with local edits will meet this; commit the edits, or
  pass `--allow-dirty-kit` (`PAPERSMITH_ALLOW_DIRTY_KIT=1` is the same
  override, used by the test suite). Wheel installs are unaffected unless the
  wheel was built from a dirty tree.
- A workspace created by 0.13.0 or earlier has no kit-source record:
  `status` reports `Kit source: unknown (recorded before 0.14.0)` until the
  next `upgrade`, which writes it. Nothing else changes shape and no migration
  is needed; the record is not a framework-managed file, so `audit
  --check-drift` and `status`'s drift list do not report it.
- `papersmith run` on a `local` target now runs the profile's command with
  `PYTHONDONTWRITEBYTECODE=1`, so the job writes no `.pyc` files (into the
  workspace or the target it imports); imports are recompiled on each run.
  No stored artefact changes; no migration is needed.
- After an `upgrade` that moves the version marker, the routing docs name the
  new version in the same run. No stored artefact changes; no migration is
  needed.
- The workspace `.gitignore` changes shape on the next `upgrade`: the
  framework's lines move into a block between two marker lines, and lines the
  workspace added stay below it. It now ignores `.proposal-deliberation/`,
  `.experimental-deliberation/`, `backup/proposals/` and
  `backup/experiments/`. No registry migration is needed: `upgrade` re-renders
  `.gitignore` on every run, and that render now merges into the existing file
  (converting a 0.13.0 file as described under Fixed) instead of replacing it,
  which `tests/test_workspace_gitignore.py` checks against the 0.13.0
  fixture. Ignoring a path does not untrack it: a workspace that already
  committed engine state keeps it in git until `git rm -r --cached
  .proposal-deliberation .experimental-deliberation` is run, which is the
  user's call.
- The plausibility agents' `resolve` calls cache under `sota-pool/metadata/`
  instead of `paper/.paper-writing/metadata/`. Caches an earlier run already
  left under `paper/` are valid paper-writing caches (same record, same key)
  and keep reading; nothing moves them and no migration is needed. A
  workspace that wants them gone can delete
  `paper/.paper-writing/metadata/` while no paper has been started.
- `verify`'s `fidelity.drift[].changedSections`/`touchedSections` and
  `fidelity.benchmark.changedSections`/`armsReached` now list identifier,
  dotted and label-only sections. A change inside `3.1` reports both `3` and
  `3.1`. A drift entry whose sections now resolve reads
  `sections it declares have changed` where it used to read `bound to an older
  revision, but none of its sections moved`. A numbered parent's digest covers
  the same lines as before, so existing numbered `__provenance__` references
  keep matching what they matched. Under `experimental-implementation`,
  sections are experiment ids (`E1`) and legacy `## N` numbers. The
  implementation profile gains an optional `documents[N].section_heading`
  leaf (refused as `IMPLEMENTATION_DOMAIN_PROFILE_INVALID_SECTION_HEADING`
  when malformed; a profile that does not declare it reads no sections). This
  is reader-side only: no stored artefact changes and no migration is needed.
- `settle --under` appends after the section's last item instead of placing
  the item first. In a holder that 0.13.0 wrote newest first, the existing
  lines stay where they are and new items follow them, so the section reads
  as the old newest-first run followed by an oldest-first run. Nothing is
  reordered or rewritten. A section whose only items are the position
  block's receives the item right after the block. `settle --reverse` with no
  `## Reversed` heading now adds one at the end of the file instead of
  refusing `SETTLE_HEADING_ABSENT`, a code that path no longer raises. More
  than one heading still refuses `SETTLE_HEADING_AMBIGUOUS`. Holders and
  ledgers keep their shape, so no migration is needed.
- `verify`'s `position.attainedLevel` for a sequence with no leveled witness
  is the header's `targetLevel` instead of the ladder's top rung. `gate` and
  the launch menu read the same value. On a ladder of three or more rungs, a
  launch from such a position now needs the position to aim at the launch
  rung (`levels[-2]` or above). One aimed at a lower rung refuses
  `RUNG_NOT_ATTAINED` where it used to pass, and re-sealing with
  `position --target-level <rung>` is the exit, which the rung-skip rule
  allows for such a sequence. Sealing is otherwise unchanged. Nothing stored
  changes shape and no migration is needed.
- `verify`'s `prose.staleRevisions` and `prose.unresolvedSymbols` list fewer
  entries for targets whose holders carry a position block, witness tokens or
  a `## Reversed` section. Both keys were report-only and never moved a
  status. This changes the reading only: no migration is needed.
- Running either implementation launcher with `IMPLEMENTATION_DOMAIN_PROFILE`
  set to the other implementation skill's `impl_profile.py` now refuses
  `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING` instead of running under that
  profile. Unset the variable. Nothing stored changes and no migration is
  needed.
- `verify` no longer lists an executed kit notebook under
  `structure.scaffoldDrift` or `structure.harnessDrift`, and new receipt
  entries for notebook destinations carry an extra `writtenSourceSha256` key.
  The key is additive: receipts without it keep reading (full bytes, or the
  source content rebuilt from the kit for an engine-written entry), so no
  migration is needed. A legacy `authored` or `adopted` notebook entry still
  drifts on execution until its next `materialize --authored`.
- Unmeasured `@step` entries in a position state's `unmeasured` list carry
  two new keys, `reason` and `digestScope`; the `sequence` entries and every
  verdict are unchanged. Step events keep their digest, so marks recorded by
  0.13.0 read exactly as before. No migration is needed.
- `search.costForecast` and `projectedCost` gain `parallelism`,
  `contention` and `basis` (and `parallelismMalformed` when that key is
  unreadable) wherever they carry a projection; `projectedSeconds` is
  unchanged. Search records are read, never rewritten, so no migration is
  needed.

- Locus queries resolve differently only where they were wrong: a word that
  matched part of a heading word no longer matches (`O1` vs `O10`); a query
  naming an outer heading exactly (`Data`) now resolves to it instead of a
  nested heading sharing the word; a query whose candidates nest within the
  gate's margin blocks and lists both instead of silently picking the
  innermost; and a query opening with `#` level marks only considers headings
  of that level. Entry ids, labels and tags (the non-successor resolver) are
  untouched. A blocked `RESOLVE_TARGET` result gains a `candidates` array;
  managed revisions, receipts and locks are not read differently, so no
  migration is needed.

- A `CREATE_SUCCESSOR` preview, its published result and the successor's
  receipt gain an optional `staleCompanionReferences` array, present only
  when the successor names another revision's companion artifact. Receipts
  written by 0.13.0 carry no such key and keep validating on read; no
  existing revision is rewritten and no migration is needed.

- A file under `<Name>/Notebooks/` that is not a JSON notebook object now
  yields a `verify`/`probe` payload (the notebook `unreadable`, listed under
  `unsealed`, notebooks verdict `drift`) where 0.13.0 exited 1 with a
  traceback. Nothing on disk is read differently; no migration is needed.

- `papersmith status` prints `published` (or `edited-after-publication`)
  where it printed `draft` for a revision the engine published, and its JSON
  `proposal` object gains a `receipt` key (`null`, or `operation` and
  `document_matches`). Nothing on disk is read differently or rewritten; no
  migration is needed.

- `env` appends `.venv/` and `*.egg-info/` to the target clone's
  `.git/info/exclude` (once; its JSON gains `excluded`), and a `.gitignore`
  block authored by `apply` or `materialize --stage scaffold` gains
  `*.egg-info/`. Existing `.gitignore` files are not rewritten, the scaffold
  gap list is unchanged (so `verify` reads an existing target exactly as
  before), and no receipt or ledger changes; no migration is needed.

- `probe`'s `backend` gains `declared` and `source`, and two states
  (`declared-unmet`, `unrecognized-backend`) that only a target stating
  `__backend__` can reach; an existing target states nothing and reads
  exactly as before. `env` gains `--torch`/`--torch-version` and a `torch`
  key (`{"variant": null, "args": []}` without the flag). A newly
  scaffolded target gets the backend-neutral `conftest.py`/`sweep.py` and a
  `pyproject.toml` with `dependencies = []`; files already in a target are
  never rewritten and their receipts are untouched, so no migration is
  needed.

- `papersmith.yaml` is the user's and `upgrade` never rewrites it, so a
  workspace initialized before 0.14.0 keeps its `smoke_and_invariants`
  profile. Where that profile's `implementations/{paper_slug}` names a
  directory that does not exist, `papersmith run` now refuses before
  dispatch and names the edit (`{target}`, `{target_python} -m pytest`);
  where it exists, the profile runs exactly as before. A `--dry-run` of such
  a profile, and every run of a profile naming the new placeholders, records
  a `target_resolution` key in its ledger row. No migration (user-owned file).

- An `IMPLEMENTATION_DOMAIN_PROFILE` naming the other implementation skill's
  profile from a different skills tree now exits `2` with
  `IMPLEMENTATION_DOMAIN_PROFILE_SIBLING` where 0.13.0 ran against it.
  Nothing on disk is read differently; no migration is needed.

- A v1 created by `CREATE_INITIAL_REVISION` from now on carries headings
  without terminal punctuation (`# Title`, not `# Title.`). Existing managed
  revisions are never rewritten and keep their headings; an idea whose two
  sentences differ only in their terminal punctuation is now refused with
  `INITIAL_IDEA_SINGLE_SENTENCE`. No migration is needed.

- Through `cli.mjs`, an `instruction` longer than 65,536 characters (an idea,
  for `CREATE_INITIAL_REVISION`) is now refused with `INSTRUCTION_TOO_LONG`
  where 0.13.0 accepted it. The successor preview and the first revision's
  result gain an additive `instructionBudget` key. Nothing on disk changes; no
  migration is needed.

- A deliberation request carrying `dryRun` on an operation other than
  `CREATE_INITIAL_REVISION` is now refused with `DRY_RUN_UNSUPPORTED` (nothing
  runs); 0.13.0 ignored the unknown field and executed the operation. Existing
  creation locks are untouched; no migration is needed.

- `CREATE_INITIAL_REVISION` results gain additive `sourceWindow` and, when a
  source was cut or left out, `warnings` keys; the default window (4000 bytes)
  and what v1 contains for a given set of sources are unchanged. A request
  carrying `sourceWindowBytes` outside 1..262144, or on another operation, is
  refused. No migration is needed.

- `experimental-deliberation` now accepts digits in the body of a table whose
  first header cell is `Parameter(s)` or `Hyperparameter(s)`; such a document
  was refused by 0.13.0. Every other table is judged exactly as before, and
  published revisions are unaffected. No migration is needed.

- Successor receipts may carry two new optional keys, `rationale` and
  `decider`, only when the request supplied them. The change is additive:
  receipts written by 0.13.0 carry neither and keep validating and reading
  unchanged, so no migration is needed.

- A first revision adopted by hand in 0.13.0 (no state, no receipt) keeps
  reading unchanged and is never rewritten by `upgrade`; the consistency audit
  still reports `MISSING_MANIFEST` for it until `ADOPT_INITIAL_REVISION` is run
  on it explicitly, which writes the state and a receipt carrying
  `adoptedFrom`. `ADOPT_INITIAL_REVISION` joins the CLI's accepted operations.
  No migration is needed.

- `admit` accepts `--no-findings`, and `tests/admissibility.json` may carry an
  additive `noFindings` key; `verify`'s `audit` reports `ok` (with
  `"noFindings": true`) for an empty audit ruled that way. Without the flag an
  empty findings list still refuses `NO_FINDINGS` and still reads
  `audit: none`; existing rulings carry no such key and read unchanged, so no
  migration is needed.

- `handoff` can return a new `deferredBecause` value, `prose-remedy`, only for
  a finding that declares `"remedy_in_prose": True`; findings without the key
  are sized, admitted and reported exactly as before. A target scaffolded
  before 0.14.0 keeps its own `tests/test_audit.py`, which still requires a
  non-empty `remedy_equations`; to declare a prose finding there, apply the
  kit's two-line change to that file and re-seal it with `materialize
  --authored tests/test_audit.py`. No migration is needed.

- `verify`'s `audit.remediesWithoutControl` may list fewer tests than 0.13.0
  did: a remedy test that calls the package through a module attribute or a
  same-file helper is no longer listed, so such a target can move from
  `audit: incomplete` to its next state. Nothing on disk changes; no migration
  is needed.

- An experiments document carrying `[out-of-scope:<id>]` markers now gets
  those claims subtracted from `agree`'s `untested` list, and an agreed `agree`
  payload gains an `outOfScope` key when any is marked. Published experiments
  revisions without the marker read and agree exactly as before, and
  `--acknowledge` is unchanged. The convention file gains one additive key; no
  migration is needed.

- `verify`'s `structure.objectGaps` no longer names `src/<Package>/module.py`
  on a target whose package already holds modules of its own, so such a target
  can now read `structure: ok`; `materialize --stage objects` then writes only
  the two test files. `materialize` accepts `--module`. Targets carrying
  `module.py` and every existing receipt read exactly as before; no migration
  is needed.

- `materialize --stage scaffold` now writes `{{NAME}}` (and `{{REVISION}}`
  when known) already filled, and `materialize --stage objects` now rewrites
  scaffold destinations that still carry `{{REVISION}}`/`{{NAME}}`/`{{MODULE}}`
  and are byte-identical to their receipt, updating those receipt entries'
  `writtenSha256` and `substitutions`; its result gains an additive `filled`
  key. Scaffold files of an existing target that were edited, adopted or
  declared authored are left untouched, and receipts written by 0.13.0 keep
  verifying unchanged (an executed notebook sealed before 0.14.0 is still read
  through the same legacy reconstruction). Kit files already on disk are not
  replaced; the clearer failure messages reach a target scaffolded from this
  release on. No migration is needed.

- `paper-ingestion`'s `extract_pdf.py` accepts a fifth flag, `--force-ocr`,
  and `papersmith.yaml` an optional `paper_ingestion.force_ocr` boolean.
  Existing configurations carry no such key and convert exactly as before;
  the skill-audit roster for `paper-ingestion` moves from 4 to 5 accepted
  flags. No migration is needed.

- `walk` accepts `--commit-template`; without it the walked commits keep the
  exact `walk: <step>` subject and body as before. No receipt or ledger
  records the message, so nothing on disk changes. No migration is needed.

- `papersmith status` and `papersmith audit --check-drift` are quiet about
  projection notes by default; pass `--verbose` to see them. `status --json`
  gains an additive `framework.generator_notes` list. Nothing on disk changes;
  no migration is needed.

- `check_atlas.py` without `--pool` behaves exactly as before; an existing
  `atlas.json` checked with `--pool` may now fail where a quote was
  paraphrased or cites an origin outside the pool. `_failures(atlas)` keeps
  its one-argument form for the command center. No migration is needed.

- `papersmith implement --action materialize` still runs `apply`, and now
  prints a one-line note on stderr pointing at `--action apply`. Its stdout
  and exit code are unchanged.

- `papersmith upgrade` rewrites `.claude/agents/sota-grapher.md` and its
  OpenCode/Pi/`.agents` projections, so the grapher's checker run now
  refuses an atlas whose quotes are not verbatim in the pool's abstracts
  (verified on a scratch workspace initialized from the previous commit).


## 0.13.0

### Added

- **`/upgrade-project` brings the upgrade inside the workspace.**
  `papersmith upgrade` has existed since 0.12.0 and was reachable only from a
  terminal, so an agent working inside a workspace could see that the workspace
  was running an older release and could do nothing about it. The twelfth skill
  closes that: `skills/upgrade-project/SKILL.md`, projected as a slash command
  to `.claude/commands/`, `.opencode/commands/` and `.pi/prompts/`.
  It delegates every write to `papersmith upgrade` and reimplements nothing ---
  the upgrade is a kit copy, a symlink repair, a re-derivation of every
  projection, an orphan sweep and an ordered migration run, with the version
  marker written last, and a second implementation of that is a second answer
  that can disagree with the first. What the skill adds is the two preflight
  refusals that fail better before a write than during one (this is not a
  workspace; the CLI is unreachable), the flag semantics including why
  `--plan-migrations` must not be described as a dry run, and how to read a
  non-zero exit instead of summarizing it as done.

### Changed

- **The Paper Command Center speaks the architecture diagram's visual
  language, in two themes.** A reader moving from
  `docs/diagrams/papersmith-pi-flow.html` to `papersmith ui` crossed a visual
  seam that carried no information: different type, different elevation,
  different palette, for the same stages and the same gates. Light stays
  `:root`, dark arrives as `[data-theme='dark']`, and the choice persists ---
  the system preference decides the first visit, an explicit choice wins after
  that, and `light` is the floor when storage cannot be read at all.
  Archify publishes no stylesheet, so the signature is transcribed rather than
  imported: elevation as glow instead of drop shadow, radius by opposition
  (pills at 999px against structure at 1px), and tracking by opposition (tight
  on headings, wide on uppercase micro-labels). Archify's infrastructure-role
  hues are deliberately not adopted --- its frontend/backend/database taxonomy
  says nothing about a paper pipeline, so stage, gate and section keep their
  meaning and only their hues move. On the canvas a node's role is now a full
  stroke over a translucent fill of the same hue, the way the diagram states
  it, instead of an accent bar on one edge.

### Added

- **The style contract understands two themes, and still refuses literal
  colour.** `ui/src/styles.test.ts` was generalized from a single `:root` to a
  theme map: it reads both blocks, excises both from the text its
  literal-colour rule inspects, resolves dark tokens through a light fallback
  the way the cascade does, and runs every WCAG AA contrast assertion once per
  theme. The contract was extended, never weakened; both themes pass on every
  surface, badge fill, node, edge label and terminal.
- **Browser checks for behaviour and layout.** 255 jsdom tests could not see a
  clipped label or an overlapping control, because jsdom computes no layout.
  Playwright now runs `ui`-local as `npm run test:e2e` against the real FastAPI
  server serving the committed bundle --- not `vite preview`, which resolves
  assets differently and skips the `Host` validation that has broken the
  dashboard before. It waits on `body[data-ready]`, the signal `App.tsx`
  already published. Functional: tab activation and singularity, deep links
  surviving a reload, node selection opening an addressable detail panel, and
  the theme switch actually repainting --- asserted through computed
  `backgroundColor`, because an attribute that changes while the paint does not
  is the failure worth catching. Layout: text clipped by its own box,
  horizontal spill past the viewport, pairwise control overlap, a 24px minimum
  hit target, and the element panel's geometry on both sides of the 900px
  breakpoint.
  It earned its place on the first run: the new uppercase tabs spilled past an
  820px viewport. Bisecting against the pre-restyle stylesheet proved it was a
  regression introduced by this work rather than a pre-existing defect, and the
  tab strip now wraps. Horizontal scroll was rejected for hiding the last tabs
  behind a gesture nobody announces.
  It is deliberately not in `npm run test:all`, which does not run the vitest
  suite either; wiring a browser suite into a gate that skips the unit suite
  would be backwards.

## 0.12.0

### Added

- **`upgrade` migrates workspace artifacts, not only framework files.** The
  recorded `.papersmith/version` is now a claim about a workspace's artifacts
  rather than about which skills tree it holds, and a release that changes an
  artifact's shape can carry an older workspace to it. Migrations run in one
  place — after the kit is copied, because a migration may need the scripts and
  assets of the release that just arrived, and before the version marker is
  written. The mechanism is `src/papersmith/core/migrations.py`.
- **Two classes of migration, and only one of them is recorded.** A
  version-bound migration runs once, when the workspace sits below its gate and
  the installed kit at or above it, and lands in `.papersmith/migrations.json`
  so it cannot run twice. A convergence migration has no gate: it asks the
  filesystem through a read-only probe and is evaluated on every run, because
  the next release can change what it converges toward.
- **`sota-pool/` is a declared directory instead of a survivor.** It holds
  `candidates.json` and `atlas.json` from the scouting agents plus the derived
  `atlas.html`, and it survived upgrades only because `upgrade` deletes nothing
  it did not baseline first. This release ships two convergence migrations:
  `sota-pool-scaffold` creates the pool's `.gitkeep` in older workspaces, and
  `atlas-render-refresh` re-renders `sota-pool/atlas.html` when its atlas, its
  renderer or the vendored viewer bundle it inlines has changed — decided by
  hashes stored in `sota-pool/.atlas-render.json` and never by modification
  times, because `upgrade` rewrites files for reasons that have nothing to do
  with the page.
- **`status` reports pending migrations**, and `upgrade` gained
  `--plan-migrations`, which reports the pending set and writes nothing. It is
  deliberately not named `--dry-run`: that name would imply the kit copy, the
  harness projections and the orphan sweep were previewed as well, and they are
  not.

### Changed

- **The version marker advances only when that version's migrations are done.**
  A failed migration leaves `.papersmith/version` where it was, exits non-zero,
  and the next run retries. `--no-migrate` does not advance it either — doing so
  would record a release the workspace never reached and let `status`'s
  `version_match` report that as agreement. The manifest is the opposite case
  and is always written: it describes files, and the files did move.
- **A version that cannot be ordered refuses rather than guesses.** With the
  marker missing or unreadable, a version-bound migration is reported
  `undetermined` and never applied: migrating artifacts under a relation nobody
  established is the silence the downgrade guard already removed on the file
  side. Convergence migrations are unaffected, because they ask the disk.
- **The downgrade guard and the migration gate share one ordering
  implementation** (`migrations.version_order`), replacing `upgrade`'s own
  `_version_order`.

### Fixed

- **Four `test_papersmith_upgrade` fixtures derive a version newer than the
  kit's instead of pinning `0.9.0`.** A fresh workspace records the
  *distribution* version, so once the package moved past `0.9.0` those fixtures
  turned their own setup upgrade into a downgrade that the guard correctly
  refused: the guard doing its job while the tests asserted the opposite. They
  had been failing the CI gate since `0.10.0`.

## 0.11.0

### Changed

- **The proposal tramo reports its two artifacts separately.** It was lit only
  by `proposals/*.md`, so a published revision and a published revision with
  its graph read the same to the board. It now counts the revisions and the sky
  graphs (`proposals/*.graph.html`), names both in its detail, and reports
  their ratio as its progress -- a revision without its graph is exactly the
  half-done state worth showing.
- **The Pi flow diagram names both artifacts** on `proposals/` and draws a
  dashed `atlas.json` edge from `sota-grapher` to `deliberation-publish`. A
  sixth node in that carril did not survive the diagram's own gates. With a cell
  narrow enough to leave the figure readable, validation reports
  `layout/constraint`: `/experimental-implementation` is ~185px of label in a
  176px cell, and connections shortened with it fall under their 24px floor.
  With cells and gaps wide enough for both, the six-column viewBox reaches
  1370px, where `composition/desktop-readability` projects 8px source text at
  5.43px against its 6px floor. The graph therefore travels as the second
  artifact of the tramo's existing node, which is how the extractor counts it.

### Added

- **The proposal's sky graph is a step of the flow.** Stage 3's graph -- the
  SOTA constellation with the proposal inside it -- was documented, tested and
  run by nobody: the architecture diagram had no node for it, the *Pipeline*
  tab could not see it, and no agent produced it. Three surfaces now carry it.
  `deliberation-publish` now requires the overlay — reporting it as `owed`
  rather than inventing a relation to have something to draw — runs the skill's
  three commands in order (merge, check, render), and reports the rendered path,
  `proposals/<revision>.graph.html`, with the checker's verdict and whether the
  published revision names it. The deliberation's own skill now pins *when* the
  overlay is authored -- before the change is accepted, because the successor's
  text is what names the picture -- and the publish stretch has no `Write`, so
  an overlay it cannot find is reported rather than manufactured.

## 0.10.0

### Changed

- **The dashboard's flow is the architecture diagram's flow.** The Paper Command
  Center's *Pipeline* tab drew six stages invented inside the extractor --
  `ingestion`, `deliberation`, `experiments`, `drafting`, `auditing`,
  `publishing` -- while `docs/diagrams/papersmith-pi-flow.html` drew the same
  project as twelve numbered tramos plus a transversal audit lane, and nothing
  compared the two. The board now draws those twelve tramos in the diagram's
  order, with the diagram's main chain as the edges, and each tramo lights up
  from its own artifact on disk: `sota-pool/`, `guidance/`, `proposals/`,
  `implementations/`, `.experimental-deliberation/`, `experiments/`, the
  accounts store, the inbox, `paper/Figures/`, `sections/`. A tramo with no
  artifact reports what is missing instead of an invented progress. The chain
  travels in the payload (`pipeline_chain`, `gate_links`), so the drawing cannot
  disagree with the stage list it is drawn from -- which is how it disagreed
  before.

### Added

- **The writing flow, section by section.** A new *Writing* tab draws the
  paper's ten sections in rendering order, each with its live status, its word
  count and its blocks, as a flow of its own.
- **`npm run build:ui` and `npm run dev:ui`.** Rebuilding or serving the
  dashboard meant knowing to run `npm install` and `vite build` inside `ui/`,
  and the repository offered no script for either half.

## 0.9.0

### Added

- **`papersmith init` reports its own progress.** A bar with an estimate of the
  time left, plus the streamed log of the two child processes it runs —
  `npm install` and the workspace's environment provisioning — which until now
  ran with their output captured: minutes of silence, and on a cold cache up to
  the whole provisioning timeout. The estimate starts from declared priors and
  is recalibrated with the pace the run measures, so a step that overruns its
  share moves the number instead of contradicting it. `--progress` forces a
  plain log for CI, `--no-progress` silences the bar, and a pipe stays silent by
  default — which is what keeps the MCP server's child invocation readable.

## 0.8.0

### Changed

- **The Pi entrypoint is the file Pi reads.** The `pi` runtime's generated
  entrypoint moves from `PI.md` at the workspace root to
  `.pi/APPEND_SYSTEM.md`. Pi never read `PI.md`: its project context candidates
  are `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md` and
  `CLAUDE.MD`, while a trusted project `.pi/APPEND_SYSTEM.md` is appended to the
  system prompt and takes precedence over the operator's own agent-level append
  instead of combining with it. `upgrade` retires a baselined `PI.md` — nothing
  else could, since a static entrypoint is deliberately outside the orphan rule
  — and `audit` names a leftover one, in any workspace, as surplus. A `PI.md`
  this tool never wrote is the operator's file and is never removed.
- **The SOTA atlas is a 3D sky.** `/plausibility`'s `sota-pool/atlas.html`
  now draws the constellation with three.js instead of an inline SVG plane:
  family neighborhoods at their own heights, one tilted orbital plane per
  system, arcs between systems, orbit/zoom/fly-to controls. It is still one
  self-contained file that opens offline and renders byte-identically from the
  same atlas: `render_atlas.py` (stdlib-only) precomputes the scene and inlines
  the vendored viewer `skills/plausibility/assets/atlas3d.bundle.js`, rebuilt
  with `npm run build:atlas-viewer` (pinned `three` and `esbuild`
  devDependencies). The planet popup now builds its text with `textContent`.

### Fixed

- **Skill descriptions fit the ceiling the harness enforces.** Pi caps a
  skill's `description` at 1024 UTF-16 code units
  (`MAX_DESCRIPTION_LENGTH`), and `paper-writing` sat at 1680 while
  `remote-execution` sat at 1814; Pi warned and loaded both anyway, so nothing
  ever failed. They now measure 1015 and 923, and
  `tests/test_skill_descriptions.py` holds the budget — in UTF-16 code units,
  because that is the unit JS `length` counts and therefore the unit the
  ceiling is written in. No claim was dropped on the way: `remote-execution`'s
  provenance date for the pinned `kagglesdk` (`since 2025-07-11`) moved into
  the body beside the pin, where it had never been written down.
- **Pi agents no longer list unsourced `mcp`/`mcpScript` tools.** The
  `.pi/agents` projection skips `WebSearch`/`WebFetch` with a note instead of
  mapping them to names Pi does not document. The Antigravity
  `commandExecutionPolicy` values are documented as having undocumented
  semantics; its output is unchanged.
- **Workspace `.gitignore` covers the skills links.** A new workspace now
  ignores `.claude/skills`, `.opencode/skills`, `.pi/skills` and
  `.agents/skills` (the generated symlinks to `skills/`), so `git add .` no
  longer commits them.

### Added

Interactive Paper Command Center: a light theme, a clickable diagram and a
session history.

- **The proposal travels with its own sky.** Stage 3 ships a 3D graph beside the
  published revision — the SOTA constellation with the proposal inside it, drawn
  by the same vendored viewer. `merge_proposal_sky.py` merges the pool
  (`sota-pool/atlas.json`) with the proposal's overlay
  (`proposals/<revision>.sky.json`) into one atlas, and the existing
  `render_atlas.py` draws it, so the proposal's main idea, the topics it takes
  from the SOTA papers, its one novelty claim, the issue it could resolve and
  its three to five contribution concepts are nodes with real edges into the
  papers they touch — the relationship is drawn rather than asserted. The atlas
  gains one optional slot, `contribution` (orbit 1, zero to five planets), which
  a paper leaves empty; the three-to-five range belongs to the merger, because
  it is the overlay's contract and not the constellation's, and the pool's own
  checker stays the single authority on families, orbits and evidence.
  `render_atlas.py` also gains `--title`, so one viewer can name another
  domain's sky instead of borrowing a title that would be false for it.
- **Read-only paper preview routes in the command center.**
  `GET /api/paper/preview` returns sections (extractor order and ids) with
  plain-text block bodies from `paper/main.tex`, citation keys, `written`,
  truncation/duplicate flags, PDF/figure info (with an `mtime` in ms used as
  a `?v=` cache-buster) and `sections_dir` (`ok`/`absent`/`unsafe`, `truncated`
  past 100 non-canonical sections); `GET /api/paper/file?name=`
  serves only `main.pdf` and `figures/<id>.pdf|png` (real directory
  `paper/Figures/`; id is one `[A-Za-z0-9._-]` segment, no leading dot, at most
  100 characters). Reads are size-capped before reading (`main.tex` 2 MiB,
  sections 256 KiB, 200 KiB of text per response, 25 MiB per file with 413),
  resolved and contained in the workspace, regular files only. Responses carry
  `nosniff`, `X-Frame-Options: SAMEORIGIN` and `no-store`; there is no CSP
  sandbox and no `Range` support. The `Host` allow-list (421) covers them only on
  loopback binds; non-loopback binds do no `Host` filtering.
- **Preview tab.** `#preview` shows the written block text (escaped plain text,
  citation keys as chips, placeholders for unwritten blocks, truncation and
  `main.tex` status notices) beside the compiled `paper/main.pdf` in an
  `<iframe>` (with a stale badge) and a list of `paper/Figures` files. It is
  fetched when the tab opens and refetched when the workspace revision changes,
  with an inline error and Retry. The visual checker covers the tab.
- **Atlas tab.** `#atlas` shows a native summary of `sota-pool/atlas.json`
  (systems, planets, families, link and relation counts, a capped evidence list,
  a validation chip) beside `atlas.html` in an
  `<iframe sandbox="allow-scripts">` without `allow-same-origin`. Every text is
  escaped; absent, too-large, unsafe, unreadable, invalid, missing-HTML,
  missing-JSON and STALE states are explained. The atlas is not watched, so it is
  fetched when the tab opens and on a Refresh button, with an inline error and
  Retry. The visual checker covers the tab and waits for the frame fetch.
- **Decisions tab.** `#decisions` renders `/api/decisions` as a read-only
  timeline: dated events newest first, then an "Undated" group for edit receipts; each
  row shows a UTC timestamp, a source chip, the kind, the summary and the `ref`
  as plain text, an "unverified" label for lifecycle records read without hash
  checks, and muted notes. Per-source status chips (ok, absent, unreadable,
  too_large, counts, detail, truncated), a client-side source filter and a
  "Showing N of total" notice. Fetched when the tab opens and on Refresh, with an
  inline error and Retry; all text is escaped. No Sections link (not cleanly
  derivable). The visual checker covers the tab.
- **Read-only decisions timeline route in the command center.**
  `GET /api/decisions` merges, on request, normalized events
  `{ts, source, kind, summary, ref}` from the declarations region of
  `paper/main.tex` (only the current state is stored, so earlier values are not
  recoverable), the `.proposal-deliberation/` and `.experimental-deliberation/`
  receipts and lifecycle transitions, and the remote-execution ledgers at
  `implementations/<repo>/<Name>/.remote-execution/ledger.jsonl` (exactly two
  levels, no recursion; `kaggle-inbox/` is never read). Edit receipts have no
  timestamp, so their events carry `ts: null` and sort after dated events (file
  mtime is never used); the initial-revision receipt carries `createdAt`, which is
  its `ts` ("Created initial revision r01"); deliberation events are plain-JSON reads without the
  lifecycle hash checks and carry `verified: false` (to be shown as
  "unverified"). Newest first with a stable tie-break; each source reports
  `status` (`ok`, `absent`, `unreadable`, `too_large`) so one broken source never
  fails the response. Caps: 500 events per source, 1000 total (`truncated`),
  `main.tex` 2 MiB, 256 KiB per receipt or transition, 500 files per sidecar
  directory, 20 ledgers of 2 MiB and 2000 lines each (the newest 2000 lines are kept; `detail`
  counts the oldest ones ignored). Optional `source=` (422 on
  an unknown name) and `limit=` (1 to 1000). Nothing is written. The `Host`
  allow-list (421) covers it only on loopback binds.
- **Read-only SOTA atlas routes in the command center.** `GET /api/atlas`
  reports the state of `sota-pool/atlas.json` and `atlas.html` (ok, absent,
  too_large, unsafe, unreadable, invalid), staleness (json newer than html),
  the workspace checker's verdict (`ok`, `failed` with up to 50 errors,
  `unavailable`) and a summary (systems, families, links, relations, evidence).
  Each file entry carries an `mtime` (ms) the UI uses as `?v=` on the iframe;
  `GET /api/atlas/view` serves `atlas.html` (404 absent/unsafe, 413 over 2 MiB)
  under `Content-Security-Policy: sandbox allow-scripts; default-src 'none';
  script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:`,
  `nosniff`, `no-store`, `X-Frame-Options: SAMEORIGIN` and
  `Referrer-Policy: no-referrer`. Reads are size-capped (2 MiB), resolved and
  contained in the workspace, regular files only; nothing is written or
  regenerated. Validation loads the workspace's own
  `skills/plausibility/scripts/check_atlas.py` from that one fixed path and runs
  it inside the server process (workspace Python execution: only serve trusted
  workspaces); a missing or failing script yields `unavailable`. The `Host`
  allow-list (421) covers both routes only on loopback binds.
- **Light theme.** The dashboard uses one light theme built on colour tokens;
  Vitest guards reject colour literals outside `:root` and check WCAG AA
  contrast for the token pairs. The state and health payloads now load
  independently, so a slow health measurement no longer keeps the page on
  "Loading".
- **Clickable pipeline diagram with deep links.** Every stage, gate, section
  and edge can be selected with the mouse or the keyboard and opens a detail
  panel (fields, connections, history). The selection lives in the URL hash
  (`#pipeline?el=<id>`), so links open the element directly.
- **In-memory history.** A History tab and `GET /api/history` (cursor paging
  with `boot_id`, `after_seq`, `has_more`, `reset` and `gap`) record section,
  gate, stage, health and smoke changes since the server started, and
  `history_append` streams new entries over SSE. Nothing is written to disk.
- **Host allow-list.** On loopback binds the server answers 421 to a `Host`
  header it does not recognise; `papersmith ui --allowed-host HOST:PORT`
  (repeatable) adds one, for example `--allowed-host localhost:5173` when
  running `npm run dev`. Stage history entries now say what changed.
- **Visual checker and UI tests.** `scripts/command-center-visual-check.mjs`
  screenshots every tab in Chromium (`--full-page`, `--click-check`,
  `--drag-check`); the Node CI job now also runs `npm ci --prefix ui` and the
  Vitest suite (`npm test --prefix ui`).

Harness parity: skills, commands, agents and guards in each harness, wired by
`init` and `upgrade`, with an honest report of what is not.

- **Per-harness wiring summary.** `init` and `upgrade` print one line per active
  harness (`skills`, `commands`, `agents`, `plugins` as `wired`, `unsupported`,
  `failed` or `blocked`) and add a `wiring` key to their results. The support
  matrix lives in `generators.HARNESS_CAPABILITIES`, derived from the constants
  `render_files` writes through; exit codes and existing keys are unchanged.
  The health inspector's structural fallback also checks agents and the
  plugin/extension. The README table of what each harness wires is tested
  against that matrix.
- **README support matrix and Antigravity note.** The README now carries the
  sourced per-harness support matrix (with source URLs and the 2026-10-02 date)
  and states why Antigravity gets no command files (workflows are deprecated in
  favour of skills); its commands cell reads "unsupported — vía skills". Nothing
  generated changes.
- **Link-failure warnings.** Skill-link failures (an `OSError`, or a real
  directory at a link path) are reported by `init` and `upgrade` instead of
  being skipped silently.
- **OpenCode agents.** `init` and `upgrade` project each `.claude/agents/*.md`
  definition into `.opencode/agents/<name>.md` with `mode: subagent` and a
  least-privilege `permission` block mapped from the Claude `tools:` list
  (unknown tools are never granted and are reported). `upgrade` removes agents
  whose source disappeared.
- **Antigravity agents.** `init` and `upgrade` generate `.agents/agents/<name>.md`
  from the `.claude/agents/` sources (explicit `tools` allow-list mapped to
  Antigravity tool names, `commandExecutionPolicy` `off` unless the agent has a
  shell tool). Stale ones are removed on upgrade. Sourced from
  https://antigravity.google/docs/subagents and /docs/hooks.
- **Pi prompt templates.** `init` and `upgrade` project one prompt template per
  skill under `.pi/prompts/<name>.md` (the same body as the Claude Code and
  OpenCode commands, with `$ARGUMENTS`), and `upgrade` removes the ones whose
  skill disappeared.
- **Pi off-path push guard.** `init` and `upgrade` generate
  `.pi/extensions/refuse-offpath-push.js` for workspaces that declare `pi`: a
  `tool_call` extension that shells out to the same Python guard as the OpenCode
  plugin (a tripwire, not a gate) and fails open when the guard, python, or the
  event is unusable. `docs/guard-hooks.md` documents an opt-in Claude Code hook
  snippet (never written to `.claude/settings.json`) and records that an
  Antigravity guard is unsupported until its hook input schema is verified.
- **Antigravity `.agents/skills` link.** `init`, `upgrade` and
  `scripts/setup-harnesses.sh` link `.agents/skills` to `skills/`, so skills can
  be invoked as `/name`. Antigravity still gets no command files.
- **Docs.** `docs/harness-support-matrix.md` (sourced per-harness support) and
  `docs/guard-hooks.md`; the README now states per harness what is wired,
  unsupported or opt-in.

### Changed

- **The health check is per enabled tool.** It requires each harness link and
  commands directory only for the tools the workspace enables, instead of
  reporting drift for every known harness.
- **Antigravity uses only documented locations.** Skills at `.agents/skills`,
  agents at `.agents/agents/` and the rules entrypoint at `.agents/AGENTS.md`.
  `.antigravity/rules.md` and `.antigravity/skills` are no longer generated.
  Pre-1.0 breaking change: existing workspaces are not migrated; re-run
  `papersmith init` in a fresh workspace.
- `upgrade` also removes stale `.pi/agents` files whose source disappeared.
- Pi agents need the third-party `pi-subagents` package; Pi core has no
  sub-agents.
- Unverified before release: that real Antigravity lists `.agents/skills/<name>`
  as `/name`, and whether Pi shows a trust prompt for project `.pi/prompts`. If
  the Antigravity premise fails, ship the Pi part alone.

## 0.7.1

### Fixed

- **The clean-context gate fails when the gate itself fails.** `scripts/clean_context_gate.py`
  only compared the empty-HOME run with the decoy-HOME run, so a suite that
  failed the same way under both exited 0. The empty home is the machine with
  no personal context, so its own failure now fails the step. Its temporary
  homes are also removed on SIGTERM (a cancelled CI job) and when a read-only
  file is left under HOME, and a leftover is reported instead of ignored.

### Changed

- **CI runs the suite once per job, not twice.** The plain `pytest` step is
  gone: the gate already runs the declared suite under an empty HOME, and
  with the fix above it fails on that run's own failure. About eleven minutes
  less per Python job.
- **The README installs the latest `main`**, never a pinned tag, and its
  counts (CLI commands, skills, agents, MCP tools), flag tables, badges and CI
  description now match the code.

## 0.7.0

### Added

- **Pi receives the agent roster.** The nineteen agent definitions existed
  only under `.claude/agents/`, while Pi discovers agents at
  `<cwd>/.pi/agents/*.md` -- so in that harness a delegated stretch had no agent
  to land on, and a flow could stall asking the operator about routing that did
  not exist. The kit renderer now projects each definition onto Pi's shape:
  front matter travels verbatim except `tools:`, mapped onto Pi's tool names
  (`WebSearch`/`WebFetch` onto the MCP gateway the agent bodies already
  prefer), and the body's `.claude/skills/` references become the
  harness-neutral `skills/` link every workspace already carries. It is a
  rendered path, so `init`, `upgrade`, `status` and the drift check pick it up
  from the one path authority -- and nothing is forked: the projection derives
  from `.claude/agents/` on every run. A malformed definition, an absent or
  unsafe name, or an unreadable file is skipped with a warning, never raised
  on.
- **A fresh workspace ships the `paper_writing` connector roles.** Without
  them, `paper_cli.py resolve` refused `RESOLVER_ROLE_EMPTY` before any
  literature work could start -- and that front door is what the scout and the
  screener both depend on. The seeded block mirrors this repository's own:
  OpenAlex/Crossref/arXiv for resolution, and full-text only for the two
  connectors whose own resolved metadata names a fetchable PDF. `contact` is
  seeded empty on purpose; it is the operator's courtesy address for OpenAlex's
  polite pool, never a shared credential.

### Fixed

- **`init` no longer aborts a workspace's provisioning on the editable
  install.** The provisioner ran `pip install -e <root>` unconditionally and
  with `check=True`, and a workspace is not a Python project -- no
  `pyproject.toml`, no `setup.py`, only `requirements.txt`. Pip refused with
  "does not appear to be a Python project", the step aborted before
  `marker-pdf`, and the workspace reported `OCR Engine Missing` while its conda
  environment was otherwise fine: `fastapi` imported and `papersmith ui` ran.
  The editable install now runs only where there is a Python project to
  install, which is the framework checkout, and says so when it skips.
- **`resolve` accepts the identifier a user actually pastes.**
  `arXiv:1512.03385` was sent to the arXiv API with its prefix, and that feed
  answers entry-less -- measured: 706 bytes with no `<entry>`, against 2814 for
  the bare id -- so the command died on a traceback instead of returning
  metadata. One case-insensitive `arXiv:` prefix and surrounding whitespace are
  stripped before the query, and a feed that names no work now refuses as
  `IDENTIFIER_UNRESOLVED`, the code the contract already documented.
- **Both offline smoke wrappers are hermetic again.** They called `init` with
  `--no-npm` and no `--no-env`, so the wrapper provisioned a real
  multi-gigabyte environment: the wiring smoke built one inside its own 180s
  test timeout and failed there, while its header promises "no npm, no
  network". Neither line had changed since it was written -- `init` gained the
  provisioning step two days later -- and the guard written to catch exactly
  this swept `tests/` only, so it stayed green over both callers. The wrappers
  pass `--no-env` now, and the guard sweeps `scripts/` and `.github/` too.

### Internal

- `.gitignore` covers the `.venv` symlink CI creates. The directory form
  (`.venv/`) does not match a symlink, so `git status` reported the workflow's
  own artifact as untracked.

## 0.6.0

### Added

- **`papersmith ui`: the Paper Command Center.** A local dashboard and
  health/wiring control plane for an initialized workspace, reachable through
  one command. It serves the workspace's own state -- paper metadata, the ten
  section contracts, the four quality gates, the pipeline stages, and the
  evidence ledgers -- over `/api/state`, reports harness, skill, agent and
  environment wiring over `/api/health/wiring`, and streams changes over SSE
  within about a second of a section edit. The backend ships in the kit
  (`skills/_core/command_center/`), so a workspace can run
  `python -m skills._core.command_center.server` standalone with no Node/npm
  dependency in the paper directory; the React/Vite dashboard is committed as a
  built bundle beside it, and `--export-static` writes a copy anywhere. The
  server is read-only: it observes a paper and never edits one.

### Changed

- **`init` reports a wired harness `skills` link like every other kit file,
  and `upgrade` repairs one.** Each harness (`claude`, `opencode`, `pi`,
  `antigravity`) reaches the kit through a relative `skills` symlink. A
  filesystem that could not create one used to read as a silent success; it now
  surfaces as a gap. The link never overwrites real, non-symlinked content at the
  same path, and `upgrade` re-links a stale one. A hermetic smoke script,
  `scripts/cli-paper-wiring-smoke.sh`, asserts the four links, agent and
  slash-command parity across the harnesses, and live repair.
- **`init` provisions the workspace environment, and `papersmith ui` resolves
  the interpreter that provisioning creates.** `init` runs the workspace's own
  `scripts/setup_env.py install` (fail-soft, skipped with `--no-env`), so the
  dashboard works straight after `init` instead of exiting on a raw
  `ModuleNotFoundError`. `ui` looks for `.micromamba/envs/papersmith` first, then
  a `.venv`, and refuses with the one command that provisions the environment
  when neither can import the backend.

### Fixed

- **`scripts/setup_env.py` installs the command center's dependencies.**
  `fastapi`, `uvicorn`, `watchfiles` and `pydantic` were declared in the kit's
  `requirements.txt` but never installed, so the environment the gate names could
  not load the server's tests. They are installed from the same list now.

## 0.5.1

### Added

- **`settle --attach --replace`: re-pointing a proof is not retracting a
  claim.** A checklist line's `` `test_<id>` `` witness could be attached
  once and never moved -- `--attach` refused `SETTLE_ALREADY_WITNESSED` on a
  line that already carried one, and the only path that reached a re-point
  was `--reverse` followed by a fresh placement, which de-ticks and
  un-witnesses a line that was already measured and closed. `--replace`
  closes that gap as a modifier on `--attach`'s own write, not a sixth mode:
  the mark is never touched (mark-blind between a ticked and an open line),
  and every other byte of the holder file is identical before and after the
  call. Three new refusals guard it, all `INVOCATION_DEFECT`:
  `SETTLE_REPLACE_CONFLICT` (`--replace` without `--attach`),
  `SETTLE_NOTHING_TO_REPLACE` (the located line carries no witness at all --
  plain `--attach` is the create path), and `SETTLE_WITNESS_UNCHANGED` (the
  incoming token equals the one already there). Performs no read of
  `tests/`: gating on whether a witness names a real test stays exactly
  where it already was, at `verify`/`close`. The previous token is recorded
  as `replacedWitness` in both the `settle` ledger event and the command's
  response, beside an always-present `replace` boolean that mirrors the
  other four mode flags on every `settle` call.

### Changed

- The one sealed `settle` case's declared golden delta did not materialize:
  that case already refuses `SETTLE_NOT_DISCUSSED` before reaching the
  success path where `replace`/`replacedWitness` would appear, a
  pre-existing condition unrelated to this change. `tests/seal/digests.json`
  is therefore unchanged -- recaptured and confirmed byte-identical, not
  regenerated.

## 0.5.0

### Added

- **`figure-review`, the tenth skill: the eye that looks at the rendered
  diagram.** `render` compiled a figure to PDF and `figure audit` judged it
  against the prose, and nothing ever looked at the picture. Overlapping boxes,
  text running off the canvas and bad connections were all reported
  `unmeasured` -- honestly, but unmeasured, and the socket for the skill that
  would measure them had been written and left empty.

  The skill rasterizes the already-compiled `Figures/<id>.pdf` through the
  first of `pdftoppm`, `pdftocairo`, `gs`, `sips` that resolves, decodes the
  PNG with a stdlib `zlib` reader, and computes what a raster can actually
  support. It calls `latexmk` never, so it spends nothing against `render`'s
  repair budget, and it imports nothing into `paper-writing` -- the join is
  `--visual-report <path>`, a report already on disk read as plain data. A
  test now holds that import edge absent rather than leaving it true by
  accident.

  What it reports is graded by what can be known, and the grading is the
  point:

  - **A verdict** for `out-of-bounds` and `overlap` -- computed, numeric,
    with intersecting boxes in pixel and point coordinates, and reported as
    unnamed regions. The raster found the collision; the source names the
    nodes, and nothing here joins them.
  - **A number with no verdict** for `canvas-occupancy`. "Too much whitespace"
    is a judgement about composition, so the fraction is reported and nothing
    fails on it.
  - **An announced silence** for legibility, style, connection correctness and
    which component an overlap belongs to, each with a named reason.
  - **An assisted reading** for what the agent itself sees. It is labelled,
    never appears in a verdict field, and may never upgrade an `unmeasured`
    dimension to `pass`.

  `out-of-bounds` is itself `unmeasured` when the source declares no border: a
  standalone TikZ canvas is fitted to its own ink, so without one there is no
  way to tell ink that ran off from a canvas that was drawn to fit.

- **`figure audit`'s report carries a `visual` key**, always present, never
  null, supplied by the caller and unable to change the semantic verdict. A
  visual `fail` beside a semantic `pass` leaves the top-level verdict at
  `pass`, and a test holds that in both places it could regress.

### Fixed

- **`figure-auditor`'s precondition is a command instead of a belief.** It read
  "when that skill is available in this session" with nothing measuring it; it
  now runs the skill's front door and quotes the exit.
- **`legibility`'s reason for being unmeasured was false.** It named a missing
  image tool. Glyph metrics come from the PDF's text layer, not an image, so
  the tool was never the obstacle -- legibility is a threshold judgement, and
  the reason code now says so. Deferring behind an honest reason is a note;
  deferring behind a false one is the defect this release exists to remove.

### Internal

- Five sequential work units, each mutation-proved: every lock was broken on
  purpose with the mutation a weaker lock would have survived, and watched to
  go red. One lock did survive its mutation and was rewritten -- it had been
  comparing literals rather than calling the function it claimed to guard.
- A file this repository tracked inside the target's own repository, under a
  path its own `.gitignore` declares it does not carry, is tracked no longer.

## 0.4.0

### Added

- **A step now reports the product the repository was told to ignore.** A
  `__steps__` step declares what it writes, `step` already compares those
  declared roots against what the run actually wrote, and nothing asked whether
  those written files were ones `.gitignore` excludes. So a step could declare a
  product, produce it, and have git skip it silently: the declaration read
  satisfied, the run read clean, and the artifact never entered history. Nobody
  finds out until someone looks for a file that was never committed.

  `wrote` now carries `ignored` -- always present, `[]` when clean -- the subset
  of the run's own written paths the repository's ignore rules exclude, plus an
  `ignoredNote` when it is non-empty. Both readings reach the terminal ledger
  event, so the finding is durable rather than printed once.

  It reports and never refuses, for the reason `undeclaredProduces` already
  gives: it grades an act already taken. The step has run and the files are on
  disk; refusing now undoes nothing and hides the finding behind an error.

  The check runs over the paths actually written, never over the bare declared
  roots. A declared root checked against a content-only rule (`Results/*`)
  answers "not ignored" truthfully and uselessly, because every file under it
  is. That distinction is what the test fixture proves: its rule is anchored to
  the product folder, because an unanchored rule matches the product-relative
  path at the repository root just as well and would pass with the path join
  deleted.

### Internal

- This repository's own `.gitignore` already stated the insight behind the above
  by hand, in the one file whose whole job is declaring what does not ship: *"una
  regla escrita nombrando lo que existia ese dia no alcanza a lo que nace
  despues"*. It was applied to two subtrees one at a time and derived nowhere.

## 0.3.1

### Fixed

- **The `pin-published` refusal no longer prescribes a push nobody measured.**
  It appended the same remedy -- push it and re-pin -- to every failure it
  caught, so a remote answering `not our ref`, a DNS failure, a proxy refusal
  and a scratch `git init` that could not write all arrived at one sentence
  telling the operator to push. Nothing in the skill had ever asked how much
  that push would carry. The refusal now takes one of two shapes, chosen only
  by whether the weight could be read and never by how large it is: measured
  states the count and keeps the remedy; unmeasurable states what is known and
  prescribes nothing. That second shape is not new to this codebase -- the
  `GitTimeoutError` branch one block above has always named no remedy, because
  a question that could not be finished being asked is not the remote saying
  no. That branch is untouched here; it was the model, not the patient.

  The reader is local and transfers nothing. It matches a configured remote to
  `--repo-url` by exact string comparison, resolves the cached
  `refs/remotes/<name>/<branch>`, and counts commits. Two remotes sharing one
  URL resolve to unmeasurable rather than picking one: they are independent
  caches fetched at different moments, so a choice between them is an answer
  the operator cannot audit. The measurement is therefore often unavailable,
  and that is the intended trade -- a weight anchored on the wrong remote is a
  number that looks measured and is not.

  The clause states an exact distance from the cache and claims nothing about
  the remote now. An earlier draft called that number a floor. It is a ceiling
  on the real push: a remote that moved forward since the last fetch needs
  fewer objects, not more. Both framings over-claim, and over-claiming from a
  true measurement is the defect this change exists to close.

## 0.3.0

### Fixed

- **A campaign submitted with `--unit` now distributes the work.** Both
  per-submission facts already reached the worker — the packer splits the unit
  list across workers and writes each worker's own slice, `--smoke` sets the
  mode the same way, and the adapter merges both into the job folder's
  `run-config.json`. Nothing read them. Every worker received its slice in a
  file nobody opened and ran the identical whole job, so a distributed
  campaign distributed the ledger and not the work. `submission_environment()`
  is now the one place either name is decided, applied by both the notebook
  and callable branches and kept separate from `kernel_environment()`, which
  the callable branch has no clone or `PYTHONPATH` to compose for. An absent
  mode or absent units leave the environment as it was rather than
  substituting an empty string for a value nobody declared; a DECLARED empty
  list still sets the variable, because only a present key can say that zero
  units was the answer.
- **`lfs` names the large files that are real content.** It reported the
  pointers by path and the materialized side by tally, so a reader needing one
  specific checkpoint could not tell whether it had arrived — while the
  skill's own table promises to report which files are which.

### Internal

- The D2 grounding tripwire counts recorded runs before judging, instead of
  failing permanently. Below ten it announces the silence; at or above it, it
  applies the falsifier and either names what fired or asks for the discharge.
  A permanently red test is not a signal, and this repository has already paid
  for that lesson once.
- `init`'s tests derive the recorded version from the kit instead of restating
  `0.1.0`, a literal that passed for a thousand commits and broke on the first
  real bump.

## 0.2.0

The first release where the version means anything: `0.1.0` had been frozen
since the package skeleton, so nothing downstream could tell two builds
apart.

### Fixed

- **The provisioned environment can now run the suites.** `setup_env.py`
  built an environment missing `nbformat`, `nbclient`, an editable install of
  this project, and `ipykernel`. Running the configured gate under it failed
  31 tests. `nbclient` pulls in `jupyter_client`, which knows how to talk to
  a kernel, and never `ipykernel`, which runs the cells — so that last gap
  surfaced as a child process exiting non-zero rather than as a missing
  module.
- **`npm run setup` runs.** It invoked bare `python`, which does not exist on
  a machine that has only `python3`, while the script it calls documented
  `python3` in its own usage. Same for `setup:env`, `clean:env` and two
  README instructions.
- **The test gate names the environment this project provisions.** It named
  bare `pytest`, resolved by the caller's `PATH` — measured resolving to a
  Python 3.9 install that cannot import this project at all.
- **`upgrade` refuses to move a workspace backwards.** It read the kit's
  version and wrote it in three places while comparing only for equality, so
  installing an older kit rolled a workspace back in silence and reported the
  older version as the new truth. A deliberate rollback now needs
  `--allow-downgrade`, which is its own flag: `--force` already means "write
  even when the bytes match" and must not double as permission to change
  version.
- **Ingesting a paper no longer deletes its appendix.** `strip_references`
  cut from the references heading to the end of the document. Measured on a
  116-document corpus: five papers place supplementary material after their
  references, and the cut removed 52% to 74% of each file — a generalization
  bound, a derivation, dataset details, an algorithm's specification. Every
  references section is now cut, and only up to the next heading, which also
  makes the operation idempotent.
- **A failed remote run reports why.** The Colab executor records its reason
  in `status.json`, bounded on purpose; `poll` reported the exit code alone
  and dropped it. Separately, the "session not found" test matched that
  phrase anywhere in a helper's output, including the run's own recorded
  error — so a run whose error contained those words was reported as a
  vanished session, which means *evidence missing* rather than *this failed*.

### Added

- **Each `write` run records its grounding counts** to
  `paper/.paper-writing/grounding-runs.jsonl`, one line per completed run.
  A ruling that shipped without a numeric threshold named ten recorded runs
  as its falsifier, and nothing recorded them.
- **A `--allow-downgrade` flag** on `papersmith upgrade`.

### Changed

- **`upgrade` now refuses where it used to proceed.** Installing an older kit
  over a newer workspace was accepted silently; it now raises unless
  `--allow-downgrade` is given. For anyone driving `upgrade` from a script
  this is a breaking change, and under strict conventional commits its commit
  deserved a `!` it did not carry. Recording it here because a reader looking
  for what broke looks in this file, not in a commit subject.

  Worth naming the reason it was missed: across the 817 commits between
  `0.1.0` and this release, not one carried `!` or `BREAKING CHANGE`. The
  marker has never been used in this repository, so a version derived from
  commit types cannot answer whether a major bump is owed -- the input for
  that question was never written down.
- **Pin conditions are named by id, never by position.** Two conditions had
  been inserted into the middle of the list; the doctrine table renumbered
  itself and 55 prose references across four files did not, leaving two
  different functions documented under the same ordinal.

### Internal

Guards added for defects that were previously invisible: the two version
sources are held to each other, the gate's interpreter is probed against
every import the suites and their assets actually require plus a notebook
kernel, scratch fixtures are held to resolving their paths (a macOS symlink
had four tests failing over correct code), and the end-to-end suite's line
budget now counts code rather than taxing the explanations beside it.

# Proposal: The Figure Nobody Looked At

## Intent

`render` compiles a standalone TikZ figure to a PDF and writes it to
`paper/Figures/<id>.pdf` (`skills/paper-writing/scripts/paper_figure.py:275-282`,
path resolved at `:99`). `figure audit` then judges that figure against the prose
that describes it (`paper_figure_audit.py:179-291`). Between the two, **nothing
ever looks at the picture.**

Every visual dimension — overlapping boxes, illegible text, labels running off
the canvas — is reported `unmeasured` today. That is honest and it is deliberate:
`.claude/agents/figure-auditor.md:63-67` forbids inferring a visual verdict from
the source, because "source that *should* render cleanly is not the rendered
figure." But an honest `unmeasured` is still nothing measured, and the whole
figure pipeline therefore ends one step short of the only question a reader of
the paper will actually ask: does the diagram read?

**The capability holds and it was measured this session, not asserted.**
`pdftoppm -png -r 150 paper/Figures/mm-proposal-summary.pdf` produced a
1481x702 PNG, and reading that PNG surfaced three facts invisible in the `.tex`:
the *global discrepancy* arc sweeps through the empty lower half of the canvas,
the main flow occupies a thin band at the top with roughly a third of the image
blank below, and the *local discrepancy* label nearly touches the box to its
left. An agent can genuinely see a rasterized diagram. That is the load-bearing
capability, and it is now a measurement rather than a hope.

What is missing is the machinery, and the line. The pipeline produces PDF and no
PNG — re-verified this session: zero hits for
`png|rasteri|pdftoppm|pdftocairo|magick|sips|ghostscript` across every file in
`skills/paper-writing/scripts/`. And `audit_semantics`'s returned dict
(`paper_figure_audit.py:273-291`) has no `visual` key, so there is no slot today
for a visual finding to land in even if one were produced.

Success looks like this: for a compiled figure, `figure-review` returns numbers
somebody else can re-measure for the dimensions a raster can actually support,
and an announced silence with a named reason for the dimensions it cannot. A
`pass` on "style" would be strictly worse than today's honest `unmeasured`, and
this change must not buy coverage at that price.

## Scope

### In Scope

1. A tenth skill, `skills/figure-review/`, with its own `SKILL.md`, its own
   `scripts/` front door, and its own subprocess seam — rasterizing the
   already-compiled `Figures/<id>.pdf` and computing geometric facts from the
   raster.
2. A rasterizer fallback chain over the four tools measured present on this
   machine (`pdftoppm`, `pdftocairo`, `gs`, `sips`), and a refusal naming every
   tool it probed when none is.
3. Two computed, re-measurable verdicts: **out-of-bounds ink** and
   **ink-region overlap**, reported in pixel and point coordinates.
4. One computed number with no verdict attached: **canvas occupancy** per band.
5. A `visual` key on the `figure audit` report schema, populated by the caller
   the same way `expected_components` already is, defaulting every dimension to
   `unmeasured` with a named reason, and structurally unable to change the
   semantic verdict.
6. `figure-auditor`'s precondition rewritten from a session-level judgement
   ("when it is available in this session") to a command whose exit it quotes.
7. The roster and count updates a tenth skill forces — four test assertions
   across three files, and six hand-written prose counts no test enforces.

### Out of Scope, and why

- **A new agent.** Operator ruling, and it matches the contract already on disk:
  `.claude/agents/figure-auditor.md:58-67` and
  `skills/paper-writing/SKILL.md:1397-1403` both already bound the visual half to
  `figure-review`, loaded by `figure-auditor` itself. The exploration left this
  open; the disk had already closed it.
- **Repairing anything.** The eye reports; `diagram-author` decides what to
  change and redraws. `figure-auditor.md:3` ("Never repairs the figure") and
  `:20-24` are the existing doctrine, and this repository has already recorded
  the lesson that a verifier which edits what it certifies stops being one.
- **Any `latexmk` call, and any contact with the repair-budget ledger.** The
  visual pass consumes a PDF that already exists. `REPAIR_BUDGET`
  (`paper_figure.py:44`) and its ledger (`:256-263`, `:293-298`) are untouched;
  the operator's bound on compiles is not this change's to spend.
- **Legibility, arrow correctness, legend quality, style, aesthetics.** These
  stay `unmeasured` with named reasons. See "The honesty line" below; this is
  the deliberate centre of the change, not an omission.
- **Naming which declared component an overlap belongs to.** A raster yields ink
  regions, not names. The finding reports coordinates; the author maps them to
  its own source. Joining raster geometry to manifest component names would need
  per-node boxes from LaTeX, which needs a compile, which is out of scope above.
- **Rasterizing during `verify` or during the aggregate paper run.** `verify`'s
  `figure-semantics` check reads an already-computed dict and MUST keep doing so
  (`openspec/specs/diagram-obligation/spec.md:211-216`).
- **`magick`, `convert`, `mutool`.** Measured absent on this machine. Design may
  add them as optional extra links in the chain, but no refusal, test, or
  documented expectation may depend on them.
- **Changing any harness projection code.** Measured: `manifest.KIT_ENTRIES`
  (`src/papersmith/core/manifest.py:48-55`), `generators.collect_commands`
  (`src/papersmith/generators.py:180-215`) and `scripts/setup-harnesses.sh`
  (whole-tree symlink, `:41-60`) all walk generically. Zero code change.

## Capabilities

### New Capabilities

- `figure-raster`: rasterizing an already-compiled figure PDF deterministically —
  the fallback chain and its named absence refusal, the three unconditional test
  tiers, fixture provenance, the front door that makes the skill's presence a
  command rather than a judgement, and the obligation that the visual pass spends
  nothing against `render`'s repair budget.
- `visual-finding-boundary`: which visual dimensions carry a verdict and which
  are an announced silence — the taxonomy, its reason codes, the isolation of the
  visual verdict from the semantic one, and the rule that an agent's reading of a
  raster is labelled as a reading and can never upgrade an `unmeasured`
  dimension to `pass`.

### Modified Capabilities

- `diagram-obligation`: `Requirement: Figure-Prose Semantic Audit` (`:148-154`)
  gains the `visual` key on the returned report and a scenario pinning that a
  visual finding never changes the semantic `verdict`; `Requirement: The Audit Is
  Read Without Its Module` (`:211-216`) is re-proven against the wider schema —
  no import-allowlist widening, and no `Path`-typed field for a check to read.

`authored-diagram` is deliberately **not** modified. The budget-isolation
obligation belongs to the new capability that must honour it, not to the spec
that owns the ledger; adding a "spends nothing" scenario to `authored-diagram`
would make an existing capability's spec carry a promise about a skill it does
not know exists.

## Approach

### Decision 1 — rasterization lives in `figure-review`'s own `scripts/`

Confirmed, with the exploration's reasoning strengthened by two guards measured
this session and one cost the exploration did not price.

The new skill's front door consumes `paper/Figures/<id>.pdf` — the file
`render` already leaves on disk (`paper_figure.py:275-282`) — writes its raster
into the scratch directory `figure_paths()` already resolves
(`paper_figure.py:95`), which `_cmd_figure_audit` already writes
`figure_audit.json` into (`paper_cli.py:2952-2956`). It calls `latexmk` never.

**Rejected: put the rasterizer in `skills/paper-writing/scripts/`.** Two
measured costs:

- `ModuleCompletenessTests.test_every_script_on_disk_is_imported_at_module_level_by_paper_cli`
  (`tests/test_paper_writing.py:6170-6173`) asserts `{stems of scripts/*.py}`
  equals `paper_cli.py`'s module-level import set. A new module there must be
  imported by `paper_cli` or the suite goes red.
- The rasterizer needs `subprocess`, and
  `NoSubprocessScanTests.test_exception_list_has_exactly_one_entry`
  (`tests/test_paper_writing.py:6138-6140`) pins
  `SUBPROCESS_EXCEPTIONS == ("paper_latex.py",)` at `len == 1`, deliberately so
  "a SECOND name requires hand-editing that literal in a diff someone reads"
  (`:6099-6101`). Widening paper-writing's Ruling-1 seam for a capability that
  belongs to another skill spends the exact guard that comment exists to protect.

**Rejected: make `render` rasterize as a side effect.** It would put a second
subprocess inside the compile path and couple the eye to the repair budget — a
failed rasterization would then have to decide whether it spends an attempt.
`render`'s refusal roster (`paper_figure.py:229-237`) is closed and deliberate,
and this would reopen it for a reason unrelated to compiling.

**The cost this choice actually carries, paid rather than pocketed.** A new
skill's scripts sit entirely outside paper-writing's subprocess scan: that scan
is scoped to `SKILL_SCRIPTS = skills/paper-writing/scripts`
(`tests/test_paper_writing.py:33`, `:6121-6133`). Moving the capability out
therefore buys budget isolation by losing a guard. So `figure-review` declares
**its own** subprocess seam: its own exception tuple pinned to exactly one named
module, its own AST scan over `skills/figure-review/scripts/*.py`, mirroring
`scan_forbidden_process_imports`'s shape and all four of
`NoSubprocessScanTests`' assertions (`:6138-6158`). Without this the change trades
one honest property for another silently.

**The fallback chain, ordered by what was measured.** `pdftoppm` →
`pdftocairo` → `gs` → `sips`.

| Link | Why here | Evidence |
|---|---|---|
| `pdftoppm` | The one actually measured producing a correct 1481x702 raster at 150 dpi | measured this session |
| `pdftocairo` | Same poppler suite, different renderer; the natural second opinion | on PATH (`/opt/homebrew/bin`) |
| `gs` | Renders at a chosen resolution; third because its device names and argument shape vary most | on PATH |
| `sips` | macOS-only; last, and its presence must never read as portability | on PATH (`/usr/bin`) |

When no link resolves, the verb **refuses by exit 2 with a new named code**
(e.g. `RASTER_TOOLCHAIN_ABSENT`) quoting every tool it probed and the PATH it
probed them on — the shape `authored-diagram`'s `Requirement: Toolchain Absence
Refusal` and its `Scenario: Empty PATH refuses by name` (`spec.md:46-57`) already
established. It does **not** return `unmeasured`: an absent tool is an unreadable
invocation, not a dimension we declined to judge. The agent then reports the
visual dimensions `unmeasured` **quoting that refusal as the reason** — which is
the existing division of labour, since `figure-auditor.md:105-110` already
requires `stoppedAt` to carry the exact refusal code and `state` to carry any
`unmeasured` dimension and why.

### Decision 2 — yes, the schema gains a `visual` key

Ruled, not deferred, because a measured constraint decides it.

`openspec/specs/diagram-obligation/spec.md:211-216` requires that `verify`'s
`figure-semantics` check read **only an already-computed report dict**, that
`paper_verify.py`'s import allowlist **not** be widened, and that **no
`Path`-typed evidence field** be read by a check. A schema slot on that
already-computed dict is therefore the only shape in which a visual finding can
ever reach `verify` without breaking a requirement already in the source of
truth. Free prose in an agent's report cannot reach `verify` at all, and would
weaken the "return facts that can be measured again" doctrine
(`figure-auditor.md:96-100`) at the same time.

Four constraints on the slot, each load-bearing:

1. **`audit_semantics` does not rasterize.** It reads no disk and spawns nothing,
   and says so about itself: `expected_components` is "supplied by the caller
   because resolving a fact is a disk read and this function performs none"
   (`paper_figure_audit.py:188-191`). The `visual` report arrives the same way —
   an optional already-computed argument. Chosen over a top-level key assembled
   only in `_cmd_figure_audit` because it reuses a precedent the function already
   documents for itself, giving one signature the same shape twice.
2. **Plain data only.** String paths, integers, lists — never a `Path` object, so
   the `no Path-typed field` rule holds for whatever check reads it later.
3. **Never absent, never `null`.** The default is every dimension present with
   `{"verdict": "unmeasured", "reason": "<code>"}`. An absent key is how "nothing
   was looked at" quietly becomes "nothing was wrong".
4. **Structurally unable to change the semantic verdict.** The semantic
   `verdict`'s domain is pinned at `spec.md:153-154`; `visual` carries its own
   three-valued verdict. Letting an overlap flip a semantic `pass` to `fail` is
   the same error the spec already warns against for the pipeline-step half at
   `:198-202` — one half's gap poisoning a verdict the other half genuinely
   reached.

**Rejected: defer to design.** The `Audit Is Read Without Its Module`
requirement makes this a spec-level question, not an implementation detail, and
leaving it open would let slice 3 pick a shape that contradicts a merged spec.

**Rejected: free prose in the agent report.** It cannot reach `verify`, cannot be
re-measured, and is precisely the conclusion-shaped output
`figure-auditor.md:96-100` forbids.

### Decision 3 — presence becomes a command; only context-loading stays a judgement

Nothing in code measures the skill's presence today. Re-verified: the only three
occurrences of `figure-review` or `figure_review` in the whole repository are
`.claude/agents/figure-auditor.md:3`, `:61`, and
`skills/paper-writing/SKILL.md:1400` — all prose, none executable. The current
wording, "when it is **available in this session**"
(`figure-auditor.md:61-62`), is a session-level judgement, and a judgement is
what this repository distrusts most.

Two things become measured facts:

- **The skill ships.** Adding `figure-review` to the three roster tuples makes
  this test-enforced (see decision 4). `test_every_repository_skill_ships_in_the_workspace`
  (`tests/test_workspace_skills_e2e.py:69-73`) already proves a workspace carries
  whatever the repository carries, dynamically.
- **The verb answers.** `figure-review`'s front door answers `--help` and reports
  which rasterizer it resolved. The agent's precondition becomes "run it, quote
  what it returned" — a command and an exit, exactly the shape `did` already
  demands (`figure-auditor.md:104`). So `figure-auditor.md:58-67` is rewritten
  from "available in this session" to "when the verb answers".

**What stays a judgement, recorded explicitly**: whether a harness session
actually loaded the checklist into its context window. Nothing in this
repository can measure another agent's context, and the repository already
carries this class of limit as declared debt (`skill-audit` cannot spawn agents;
its stages 2-4 are the operator's). This is acceptable **only because** the
second fact above removes the load-bearing part: the agent no longer decides
whether the skill is available, it runs a command and reports what happened. A
judgement that nothing depends on is a note; a judgement a verdict rests on is a
defect.

**Rejected: leave it entirely a session judgement.** It leaves the whole visual
half gated on an agent's self-report, which is the false-green shape the third
verdict value exists to prevent.

**Rejected: a registry or manifest flag paper-writing reads.** It would make
paper-writing's code know a sibling skill's name — the coupling ruling 2 exists
to avoid, and `collect_commands` (`generators.py:198-205`) is generic precisely
so no skill is named in code.

### Decision 4 — four slices, re-cut, because slice 1 cannot wire nothing

The exploration proposed a first slice that "wires nothing". Measured, that is
not available: the moment `skills/figure-review/` exists on disk with a valid
`SKILL.md`, **four assertions across three files go red**, because
`collect_commands` derives one command per skill generically and three tests pin
the result against hand-written literals.

| Assertion | Location | Why it fires |
|---|---|---|
| `test_every_skill_becomes_exactly_one_slash_command` | `tests/test_workspace_skills_e2e.py:90-95` vs `SKILL_NAMES` `:31-41` | equality against a 9-tuple |
| `test_generators_are_clean_after_init` | `tests/test_papersmith_generators.py:79-98` vs `COMMAND_NAMES` `:37-47` | equality against a 9-tuple, twice |
| `test_command_derivation_is_scoped_to_the_command_tools` | `tests/test_papersmith_generators.py:105,108` | `== 9` literals, per harness |
| `test_init_projects_nine_commands_per_command_harness` | `tests/test_workspace_commands_e2e.py:200-205` vs `COMMAND_NAMES` `:188-198` | equality against a 9-tuple |

This corrects the exploration's "exactly one guard fires on a tenth skill": it is
four, in three files. `test_every_skill_declares_itself`
(`test_workspace_skills_e2e.py:75-83`) does **not** fail — it iterates
`SKILL_NAMES` and would silently skip the new skill, which the same tuple edit
fixes. `test_every_repository_skill_ships_in_the_workspace` (`:69-73`) is
dynamic-vs-dynamic and unaffected, as the exploration said.

Note the sorted insertion point: `collect_commands` sorts by name
(`generators.py:214`), so `figure-review` lands between
`experimental-implementation` and `kaggle-accounts` in every tuple.

| Slice | Content | Forecast | Ends green |
|---|---|---|---|
| **1 — the tenth skill exists, and the roster says so** | `skills/figure-review/SKILL.md`; `scripts/` front door, rasterizer, geometry; figure-review's own subprocess seam and its four scan tests; the three-tier no-skip suite; the four roster/count assertions above; `.claude/commands/figure-review.md` and `.opencode/commands/figure-review.md` regenerated via `python scripts/sync-repo-harness.py` with `--check` clean | ~500 | yes — wires nothing into paper-writing |
| **2 — the schema gains its slot** | `audit_semantics` accepts an optional already-computed `visual` argument and always returns a `visual` key defaulting to `unmeasured` per dimension; `_cmd_figure_audit` supplies `None`, so behaviour is identical and only the schema widens; `diagram-obligation` delta scenarios; `The Audit Is Read Without Its Module` re-proven | ~300 | yes — no behaviour change |
| **3 — the CLI fills the slot** | the join between `figure-review`'s output and `figure audit`'s report; the verdict-isolation lock; end-to-end over a real rasterized fixture | ~350 | yes |
| **4 — the agent stops judging** | `.claude/agents/figure-auditor.md` (precondition rewrite, `state` gains the `visual` block and the `assistedReading` label); `skills/paper-writing/SKILL.md:1397-1403`; the six unenforced prose counts | ~250 | yes |

Each slice is a **sequential commit on `main`** — never a branch, never a PR,
never a stacked chain. Operator ruling; branches are forbidden outright.

**Slice 3's one design constraint, stated now so design cannot contradict it**:
`paper-writing` must not import `figure-review`'s scripts. Cross-skill imports
would couple two independently shipped skills and put a `subprocess`-importing
module on paper-writing's import graph, defeating decision 1 entirely. The join
is a JSON file in the shared scratch directory or a CLI flag carrying a path —
never an import. Which of the two is design's to choose.

**Rejected: a single commit.** ~1400 authored lines in one commit is
unreviewable and unrevertible at the granularity the work actually has.

**Rejected: the exploration's cut, with the roster edits in a later slice.**
Measured above: slice 1 would land red. A slice that does not end green is not a
slice.

## The honesty line

This is the heart of the change. Three tiers, and the boundary between them is
the deliverable.

**Tier 1 — carries a verdict. Computed, numeric, re-measurable, no eye required.**

- `out-of-bounds`: non-background ink inside the outermost border band of the
  raster. A raster answers this exactly and needs no naming. `pass` / `fail`
  with the offending edge and the pixel count.
- `overlap`: connected ink regions whose bounding boxes intersect. `pass` /
  `fail` with the intersecting boxes in pixel **and** point coordinates. Reported
  as **unnamed regions** — "ink at these coordinates collides", never "the
  local-discrepancy node overlaps the kernel node". The raster cannot name a
  component; the author reads the coordinates against its own source.

**A number with no verdict:**

- `canvas-occupancy`: the non-background fraction per band or quadrant. Reported
  as evidence with **no pass/fail**, because "too much whitespace" is a
  judgement about composition. This is deliberate and slightly
  counter-intuitive: the most striking fact in the measured example — roughly a
  third of the canvas blank below the flow — is worth reporting and is *not* a
  failing condition.

**Tier 2 — announced silence: `unmeasured` with a named reason.**

| Dimension | Why it cannot carry a verdict |
|---|---|
| `legibility` / text size | No measured tool here extracts glyph metrics; `magick`, `convert`, `mutool` are absent and no OCR is present. A reason code such as `NO_GLYPH_METRICS`. |
| arrow / connection correctness | A judgement about meaning, not a property of pixels. |
| style, aesthetics, legend quality | Judgements. A `pass` here would be strictly worse than today's honest `unmeasured`. |
| which component an overlap belongs to | The raster found the collision, the source names the nodes, and nothing in this change joins them. A reason code such as `UNATTRIBUTED_INK`. |

**Tier 3 — the agent's assisted reading. Labelled, and never a verdict.**

The agent *can* read the PNG; that was measured, and it surfaced real findings.
That reading is valuable and it is **not** a measurement. It belongs in the
agent's report under an explicit `assistedReading` label, it never appears in
`visual.verdict`, and it may never upgrade an `unmeasured` dimension to `pass`.
The exact reason-code vocabulary for assisted readings is spec's to fix; the rule
that they are separate from verdicts is settled here.

## Test strategy: the mutation a weaker lock would survive

House rule. For each lock, the mutation is named, and it is chosen as one a
lazier test would pass.

| # | Lock | The mutation a weaker lock survives | What the test must therefore use |
|---|---|---|---|
| 1 | out-of-bounds | band width 1px → 0px, or `>=` → `>`, so ink exactly on the last row stops counting. A fixture with ink deep inside and ink far outside survives it. | ink on **exactly** the outermost pixel row |
| 2 | overlap | strict intersection → "intersect **or** touch" (`<` → `<=`). Two grossly overlapping boxes survive it. | two boxes sharing exactly one edge column: abutting is NOT overlap, 1px penetration IS |
| 3 | `unmeasured` default | delete the default-population line so `visual` is absent or `None` when nothing was measured. A test that reads the key only on the measured path survives it. | assert every dimension present with a reason on the **unmeasured** path; `KeyError` is the RED |
| 4 | verdict isolation | let `visual.verdict == "fail"` set the top-level `verdict`. A clean figure survives it. | semantic `pass` **plus** visual `fail`: top-level stays `pass`, `visual.verdict` is `fail` |
| 5 | budget isolation | a single `_write_ledger` or `paper_latex.compile` call inside the visual path. A test that only checks the PNG exists survives it. | ledger bytes byte-identical before and after a full visual pass, and `attemptsUsed` unchanged |
| 6 | figure-review's subprocess seam | empty exception tuple, or a scan returning `{}` unconditionally. | plant `import subprocess` in a second script in a temp dir and assert it is caught, **and** pin `len(...) == 1` with the exact name — the shape `tests/test_paper_writing.py:6138-6158` already proved strong |
| 7 | rasterizer fallback chain | collapse the chain to its first link. On this machine `pdftoppm` is present, so every mutation survives a naive test. | four injected-PATH cases holding only link 2, only 3, only 4, and none — the last asserting the refusal names every probed tool |
| 8 | roster (inherited, not authored) | none: the four assertions in decision 4 already fire on a tenth skill. | state explicitly that this lock is inherited, so nobody claims credit for authoring it |

**Two repo-native obligations carried over verbatim.**

- **No skips.** `authored-diagram`'s `Requirement: No-Skip Test Evidence`
  (`spec.md:110-127`) requires three unconditional tiers and that a real
  end-to-end run report `unmeasured` where it did not run, never a pass. The
  visual suite obeys the same rule: fixture-driven geometry, a stubbed
  rasterizer on an injected PATH proving invocation shape, and an emptied PATH
  proving the absence refusal — all three running on a machine with no
  rasterizer at all, none skipped.
- **Fixture provenance.** `Requirement: Fixture Log Provenance`
  (`spec.md:129-139`): committed fixtures MUST be raw bytes from a real run,
  never hand-authored, "so the parser cannot pass against a fixture shaped by the
  same hand that wrote it." Committed PNG fixtures must therefore be rasterized
  from a real compile and record the invocation that produced them — never drawn
  by hand to make a geometry assertion pass.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `skills/figure-review/SKILL.md` | New | The checklist `figure-auditor` loads; the tenth skill's declaration |
| `skills/figure-review/scripts/` | New | Front door, rasterizer (the only module allowed `subprocess`), geometry |
| `skills/paper-writing/scripts/paper_figure_audit.py` | Modified | `audit_semantics` gains an optional `visual` argument and always returns a `visual` key (`:179-182`, `:273-291`) |
| `skills/paper-writing/scripts/paper_cli.py` | Modified | `_cmd_figure_audit` supplies the visual report (`:2866-2957`); the `figure` subparser gains its flag (`:3537-3557`) |
| `skills/paper-writing/SKILL.md` | Modified | `:1397-1403` — the visual half is now measured, and the precondition is a command |
| `.claude/agents/figure-auditor.md` | Modified | `:3`, `:58-67`, `:102-113` — precondition rewrite; `state` gains `visual` and `assistedReading` |
| `tests/test_workspace_skills_e2e.py` | Modified | `SKILL_NAMES` `:31-41` |
| `tests/test_papersmith_generators.py` | Modified | `COMMAND_NAMES` `:37-47`; the `== 9` literals `:105`, `:108` |
| `tests/test_workspace_commands_e2e.py` | Modified | `COMMAND_NAMES` `:188-198`; docstring `:186` |
| `tests/` (new suite) | New | figure-review's own tests: geometry, seam, chain, no-skip tiers |
| `.claude/commands/figure-review.md`, `.opencode/commands/figure-review.md` | New (derived) | Regenerated by `python scripts/sync-repo-harness.py`; `--check` must be clean |
| `openspec/specs/diagram-obligation/spec.md` | Modified at archive | Delta from this change's `specs/` |
| `openspec/project-context.md:30`, `README.md:10`, `README.md:298`, `README.es.md:6`, `CLAUDE.md:20`, `OPENCODE.md:20` | Modified | Hand-written skill counts ("nine"/"nueve") no test enforces — tasks, never tests |
| `src/papersmith/core/manifest.py`, `src/papersmith/generators.py`, `scripts/setup-harnesses.sh` | **Unchanged** | Measured generic; recorded here so nobody goes looking |

Note: `README.md` and `README.es.md` are Spanish. Their count lines stay
Spanish — an edit follows its target context's language; only new artifacts
default to English.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Unnamed overlap coordinates are hard for `diagram-author` to act on | Med | Report both pixel and point coordinates (the dpi is ours and the MediaBox is readable), so the author can map back to its canvas arithmetically |
| A rasterizer renders differently than the measured `pdftoppm`, shifting geometry between links | Med | The verb records **which** link produced the raster and at what dpi, in the report; a finding is only comparable against another finding from the same link |
| Anti-aliasing makes "non-background" ambiguous, so overlap/out-of-bounds become threshold-sensitive | Med | Fix and record the background threshold in the report; test the boundary cases in lock 1 and 2 at that exact threshold |
| `figure-review` becomes an unguarded subprocess surface outside paper-writing's scan | Med | Its own seam, pinned to one name, with all four of `NoSubprocessScanTests`' assertions mirrored (decision 1) |
| Tier-2 dimensions quietly drift into Tier 1 later, dressing a judgement as a measurement | Med | Each Tier-2 dimension carries a named reason code in the schema; promoting one requires deleting its reason in a diff someone reads |
| Slice 1 at ~500 authored lines exceeds this repository's 400-line review guard | High | Operator authorized ~1400 total above the guard, with sequential commits on `main`. `sdd-tasks` must still emit the exact guard lines; if slice 1 forecasts materially over ~500, split the geometry module from the front door rather than widening the slice |
| A PNG committed as a fixture is hand-shaped to make an assertion pass | Low | `Requirement: Fixture Log Provenance`'s rule applied to rasters: real capture, recorded invocation |

## Rollback Plan

Each slice is one commit on `main`, so rollback is `git revert <sha>` per slice,
newest first. Slice-specific notes:

- **Slice 4** reverts to prose only: the agent returns to reporting the visual
  dimensions `unmeasured`. Nothing breaks.
- **Slice 3** reverts the join. Slice 2's `visual` key remains, defaulting to
  `unmeasured` per dimension — which is exactly today's honest answer, expressed
  in the schema. Safe to leave reverted indefinitely.
- **Slice 2** reverts the schema. Any consumer reading `report["visual"]` must be
  gone first, which is why slice 3 is reverted before it.
- **Slice 1** reverts the whole skill **and** the roster edits together; they
  must be in the same revert or the four assertions in decision 4 fail in the
  opposite direction (a 10-tuple against nine skills on disk). After the revert,
  run `python scripts/sync-repo-harness.py --check` to confirm the derived
  command files are gone and clean.

No migration is needed at any point: nothing persists state, rasters live in the
already-transient scratch directory, and no ledger is touched.

## Dependencies

- A PDF rasterizer on PATH at **run** time: `pdftoppm`, `pdftocairo`, `gs` or
  `sips`. All four measured present on this machine
  (`/opt/homebrew/bin`, `/usr/bin`). None is required at **test** time — the
  no-skip suite runs its three tiers on a machine with none.
- `render` must already have produced `Figures/<id>.pdf`. The visual pass does
  not compile and does not ask for the budget.
- No new Python or Node dependency. No addition to `requirements.txt`.

## Success Criteria

- [ ] `figure-review` ships as the tenth skill and the four roster assertions in
      decision 4 pass against a 10-tuple; `python scripts/sync-repo-harness.py --check`
      is clean.
- [ ] `figure audit`'s report always carries a `visual` key; every dimension is
      either a computed verdict with its numbers or `unmeasured` with a named
      reason. No dimension is ever absent, `null`, or silently `pass`.
- [ ] A visual `fail` alongside a semantic `pass` leaves the top-level `verdict`
      at `pass`, proven by the lock-4 test.
- [ ] A full visual pass leaves `render`'s ledger byte-identical and
      `attemptsUsed` unchanged, proven by the lock-5 test.
- [ ] With an emptied PATH, the verb refuses by name quoting every tool it
      probed, and the agent reports the visual dimensions `unmeasured` quoting
      that refusal.
- [ ] Each of the eight locks is proven RED by its named mutation before it is
      proven GREEN, and the mutation is recorded with the lock.
- [ ] The three test tiers run unconditionally on a machine with no rasterizer;
      nothing is skipped, and no tier reports `pass` where it did not run.
- [ ] `figure-auditor` no longer judges availability: its precondition is a
      command it runs and an exit it quotes.
- [ ] `npm run test:all` passes on every one of the four commits.
- [ ] The six hand-written counts say ten (`diez`), and no test was invented to
      enforce a prose claim.

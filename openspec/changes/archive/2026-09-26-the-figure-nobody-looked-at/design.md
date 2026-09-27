# Design: The Figure Nobody Looked At

## Technical Approach

`figure-review` ships as a tenth skill with a three-verb front door
(`probe`, `raster`, `measure`), a four-link rasterizer chain isolated in one
module, a stdlib PNG decoder, and a pure-Python connected-component pass. It
writes a PNG plus a provenance record into the scratch directory
`paper_figure.figure_paths` already resolves (`paper_figure.py:95`) and emits a
plain-data `visual` dict. `figure audit` reads that dict through a new
`--visual-report <path>` operand — never an import — and `audit_semantics`
accepts it as a caller-supplied argument exactly as `expected_components`
already is (`paper_figure_audit.py:188-191`).

Three layers, three owners:

| Layer | Owner | Never does |
|---|---|---|
| Rasterize | `skills/figure-review/scripts/raster.py` | compute geometry; read the ledger |
| Measure | `png_read.py`, `geometry.py`, `findings.py` | spawn a process |
| Consume | `paper_figure_audit.py`, `paper_cli.py` | import `figure-review`; read disk in `audit_semantics` |

The dimension roster and reason-code vocabulary are declared **once**, in a
shared `skills/_core/figure/` shelf both sides import, so the producer's
capability and the consumer's default cannot drift.

Specs implemented: `figure-raster` (11 requirements), `visual-finding-boundary`
(5), `diagram-obligation` (2 MODIFIED).

---

## Disk verification log

Every load-bearing citation in this document was re-read this phase. Results,
including the three that contradicted an input premise:

| Claim | Verified | Result |
|---|---|---|
| `paper/.paper-writing/` is gitignored | `.gitignore:106-112` (`paper/*`, `!paper/.gitkeep`) | **Confirmed.** No `.paper-writing/` line exists; the comment at `:110-111` states `paper/*` covers it deliberately |
| `SUBPROCESS_EXCEPTIONS` pinned at one | `tests/test_paper_writing.py:6101`, `:6138-6140` | Confirmed |
| Scan scoped to paper-writing only | `tests/test_paper_writing.py:33`, `:6121-6133` | Confirmed; `glob("*.py")`, non-recursive |
| Four roster assertions fire | `test_workspace_skills_e2e.py:31-41`,`:90-95`; `test_papersmith_generators.py:37-47`,`:79-98`,`:105`,`:108`; `test_workspace_commands_e2e.py:188-198`,`:200-205` | Confirmed, all four, line-exact |
| `test_every_skill_declares_itself` silently skips | `test_workspace_skills_e2e.py:75-83` | Confirmed — iterates `SKILL_NAMES` |
| Sorted insertion point | `generators.py:214` (`commands.sort(key=name)`) | Confirmed: between `experimental-implementation` and `kaggle-accounts` |
| `expected_components` caller-supplied precedent | `paper_figure_audit.py:179-191` | Confirmed, keyword-only, `= None` |
| `audit_semantics` return shape has no `visual` | `paper_figure_audit.py:273-291` | Confirmed |
| `scratch_dir` receives `figure_audit.json` | `paper_cli.py:2952-2956` | Confirmed |
| `REPAIR_BUDGET = 4` | `paper_figure.py:44` | Confirmed |
| `figure-auditor` precondition is a judgement | `.claude/agents/figure-auditor.md:58-67` | Confirmed, verbatim "when it is **available in this session**" |
| No image library available | `pyproject.toml:10` (`dependencies = []`) | **Contradicted.** `requirements.txt:12` declares `numpy>=1.26` and `:20` `PyMuPDF>=1.23`; `scripts/setup_env.py:51` installs `pymupdf`; `requirements.txt` is in `KIT_ENTRIES` (`manifest.py:54`), so both travel to every workspace. See Decisions 1 and 7 |
| Skills are stdlib-only by doctrine | `tests/test_forge_gate.py:57`, `:279-306` | **Partly contradicted.** No guard forbids a third-party import in `skills/*/scripts/*.py`; the guard only requires every unguarded one to resolve under the gate's interpreter (`:683-720`). Stdlib-only is therefore a convention this design keeps by choice, not a test-enforced rule |
| PGM is the better geometry intermediate | tool capability | **Contradicted.** `pdftocairo` emits only png/jpeg/tiff and `sips` emits no PGM, so PGM cannot be the uniform intermediate. See Decision 1 |
| Only four assertions fire on a tenth skill | `test_agents.py:415-432`; `test_proposal_implementation.py:9252-9280`; `test_workspace_skills_e2e.py:98-146` | **Incomplete.** Three further guards engage — two dynamically (no edit, but new constraints) and one requiring an addition. See "The roster, re-measured" |

---

## Architecture Decisions

### Decision 1 — the geometry intermediate is PNG, decoded by a stdlib module; PGM is rejected

**Choice.** Every chain link emits **PNG** (with `-gray` where the tool supports
it). `scripts/png_read.py` decodes it with stdlib `zlib` into a
`(width, height, bytearray)` grayscale raster, restricted to **bit depth 8,
non-interlaced, colour types 0 / 2 / 4 / 6**, and refusing anything else by name
(`RASTER_FORMAT_UNSUPPORTED`). Colour types 2/6 are reduced to luminance with
integer ITU-R BT.601 (`(299R + 587G + 114B) // 1000`), and the colour model is
recorded in the provenance.

**Alternatives considered.**

- *PGM/PPM as the geometry intermediate, PNG as the agent artifact.* Rejected on
  a measured capability gap: `pdftoppm` (`-gray` → PGM) and `gs`
  (`-sDEVICE=pgmraw`) can emit it, but **`pdftocairo`'s raster devices are
  png/jpeg/tiff only, and `sips` has no PGM output format at all.** PGM would
  therefore be the intermediate for links 1 and 3 and absent for links 2 and 4 —
  so the parser would need a PNG path anyway, and the chain would silently have
  two different measurement pipelines depending on which link resolved. That is
  the opposite of the comparability `figure-raster`'s
  `Requirement: Background Threshold, Resolving Tool, and DPI Are Recorded`
  exists to protect.
- *PIL / Pillow.* Not declared in `requirements.txt` and not installed by
  `scripts/setup_env.py`. Adding it would grow the set
  `required_third_party_imports()` derives (`test_forge_gate.py:279-306`) and
  therefore every workspace's install, for a decoder this design writes in ~130
  lines.
- *numpy for the pixel buffer.* Available (`requirements.txt:12`), and rejected
  anyway: the expensive step is **connected-component labelling**, which numpy
  does not provide — `scipy.ndimage.label` does, and scipy is neither declared
  nor installed. numpy would accelerate thresholding only, while adding a
  third-party edge to a skill that has no other. A `bytearray` and run-length
  row union-find is bounded and exact.
- *PyMuPDF (`fitz`) as the rasterizer, replacing the chain entirely.* This is the
  strongest rejected alternative and it deserves its reasoning stated plainly:
  `fitz` is declared (`requirements.txt:20`), installed
  (`scripts/setup_env.py:51`), travels in `KIT_ENTRIES`, and
  `page.get_pixmap(dpi=150)` would delete `raster.py`, the four-link chain, the
  subprocess seam, and `RASTER_TOOLCHAIN_ABSENT` in one stroke. Rejected for
  three reasons. (1) It contradicts an approved spec: `figure-raster` pins the
  chain, the seam, and the absence refusal as MUST requirements across four of
  its eleven entries. (2) `pdftoppm` is what was actually **measured** producing
  a correct 1481x702 raster this session; PyMuPDF rasterization has been
  measured here zero times, and this change's whole premise is measurement over
  plausibility. (3) PyMuPDF is currently imported by **nothing** in the
  repository — a declared dependency with no reader (`README.md:680` records the
  ingestion script explicitly not importing it). Making a new skill the first
  consumer of a stranded dependency couples this change to an unrelated open
  question about whether that dependency should exist at all.

**Rationale.** One decoder, one format, one measurement pipeline across all four
links. The refusal on an unsupported flavour converts "a tool emitted 16-bit or
palette PNG" from a wrong number into a named exit — the distinction this whole
change is about.

**Cost carried, not pocketed.** The decoder is new correctness-critical code
handling five PNG filter types. It is the reason slice 2 exists separately, and
it is fixture-locked in both directions (a valid raster decodes to known pixel
values; a 16-bit raster refuses by name).

---

### Decision 2 — the chain, its per-link invocation, and its refusal

**Choice.** `scripts/raster.py` is the **only** module in the skill permitted
`subprocess`. It probes `shutil.which` in the fixed spec order and invokes the
first link that resolves:

| # | Link | Invocation (argv list, `shell=False`) | dpi control | `dpiSource` |
|---|---|---|---|---|
| 1 | `pdftoppm` | `pdftoppm -png -gray -r 150 -f 1 -l 1 <abs.pdf> <abs-prefix>` | `-r` | `flag` |
| 2 | `pdftocairo` | `pdftocairo -png -gray -r 150 -f 1 -l 1 <abs.pdf> <abs-prefix>` | `-r` | `flag` |
| 3 | `gs` | `gs -q -dSAFER -dBATCH -dNOPAUSE -dFirstPage=1 -dLastPage=1 -sDEVICE=pnggray -r150 -sOutputFile=<abs.png> <abs.pdf>` | `-r` | `flag` |
| 4 | `sips` | `sips -s format png --out <abs.png> <abs.pdf>` | **none** | `derived` |

**What `sips` actually is, from its capabilities rather than its presence.**
`sips` has no resolution operand for PDF rasterization — `-s dpiWidth/dpiHeight`
write image metadata, they do not resample a PDF page, and `-Z` bounds the pixel
box rather than choosing a density. So `sips` renders at the page's nominal
density and the dpi is **not ours to choose**. It is therefore last for two
independent reasons, not one: it is macOS-only (its presence must never read as
portability), and it is the only link whose dpi we discover rather than request.
Under link 4 the effective dpi is **derived**: `sips -g pixelWidth -g pixelHeight
<abs.pdf>` reports the page box in points (PDF's nominal unit is 1/72 in), and
`effective_dpi = raster_px_width * 72 / page_pt_width`. Every finding records
`dpi` **and** `dpiSource`, so a `derived` number is never silently read as a
requested one.

**Per-link timeout, never a shared budget.** Each invocation gets its own
`subprocess.run(..., timeout=RASTER_TIMEOUT_S)` with `RASTER_TIMEOUT_S = 60`. A
timeout is a **link failure** and falls through to the next link; it is not a
global refusal. One shared deadline across probe-plus-transfer is a defect this
repository has already paid for twice, and the fix was per-operation bounds.

**The refusal.** When no link resolves, the front door exits 2 with
`RASTER_TOOLCHAIN_ABSENT`, naming all four probed tools **and** the exact `PATH`
searched. It is raised as `impl_refusals.Refused` — the shared primitive
`paper_figure.py:34-35` already reaches through
`parents[2] / "_core" / "implementation"`, which is the same depth from
`skills/figure-review/scripts/`. No new refusal class.

`RASTER_TOOLCHAIN_ABSENT` is **not** `unmeasured`. An absent tool is an
unreadable invocation; the agent then reports the visual dimensions `unmeasured`
quoting that code, which is the division of labour
`.claude/agents/figure-auditor.md:105-110` already requires.

**Alternatives considered.** *One shared timeout for the whole chain* — rejected:
a slow link 1 would consume the budget three later links needed, and the refusal
would then name a toolchain absence that was really a deadline. *Treating a
timeout as `RASTER_TOOLCHAIN_ABSENT`* — rejected: the tool was present and
answered slowly; naming that "absent" is a false reason code. *Probing by
running each tool* — rejected: `shutil.which` answers presence without spending a
process, and the empty-`PATH` tier needs exactly that cheap answer.

**Argv safety.** Always a list, never a composed string, never `shell=True`. The
PDF operand is resolved to an **absolute** path before it reaches argv, which
also closes the leading-`-` injection (an absolute POSIX path always begins
`/`), so no tool can read the operand as a flag regardless of whether it honours
`--`.

---

### Decision 3 — `figure-review` declares its own subprocess seam, mirroring all four assertions plus one

**Choice.** `tests/test_figure_review.py` declares its own seam, mirroring
`scan_forbidden_process_imports`'s shape (`tests/test_paper_writing.py:6104-6133`):

```python
REVIEW_SCRIPTS = FORGE_ROOT / "skills" / "figure-review" / "scripts"
REVIEW_SUBPROCESS_EXCEPTIONS: tuple = ("raster.py",)
```

The four assertions of `NoSubprocessScanTests` (`:6138-6158`), named exactly as
the class proves them, and mirrored one-for-one:

| # | paper-writing's assertion | line | figure-review's mirror |
|---|---|---|---|
| 1 | `test_exception_list_has_exactly_one_entry` | `:6138-6140` | `len(...) == 1` **and** `== ("raster.py",)` |
| 2 | `test_no_shipped_script_imports_a_forbidden_process_primitive` | `:6142-6143` | `scan(REVIEW_SCRIPTS) == {}` |
| 3 | `test_a_planted_subprocess_import_is_caught` | `:6145-6151` | plant `evil.py` in a tempdir, assert caught |
| 4 | `test_the_exception_named_file_is_tolerated_when_present` | `:6153-6158` | plant `raster.py` in a tempdir, assert `{}` |

**Plus one the precedent lacks.** Assertion 2 passes **vacuously** if
`REVIEW_SCRIPTS` ever resolves to an empty or wrong directory — an empty scan and
a clean scan are the same `{}`. So a fifth assertion pins non-vacuity: the
scanner's own file set equals the tracked `*.py` set on disk, and is non-empty.
This is an additive strengthening; paper-writing's own seam keeps its four and is
not touched by this change.

**Recursive glob, deliberately.** The mirror uses `rglob("*.py")` where the
precedent uses `glob("*.py")` (`:6127`). Both trees are flat today so the two
scans are identical, and the recursive form means a future
`scripts/<subdir>/tool.py` is covered rather than silently unscanned. A
non-recursive glob over a directory that later grows a subdirectory is a
blind spot that reads exactly like a clean scan.

**Forbidden set, carried unchanged:** `import subprocess|multiprocessing`,
`from subprocess|multiprocessing import ...`, `os.system`, `os.popen`,
`os.exec*`.

**Alternatives considered.** *Reuse paper-writing's scan by widening
`SUBPROCESS_EXCEPTIONS` to two names* — rejected by the proposal's Decision 1 and
re-confirmed here: the literal is pinned at one precisely so a second name costs
a hand edit in a read diff (`:6099-6101`), and the scan's scope constant
(`:33`) points at paper-writing's directory, so widening would not even reach the
new tree. *Extract one shared scanner into `_core`* — rejected: the two seams
must be able to disagree about their exception names, and a shared scanner whose
exception tuple is a parameter loses the "pinned literal in a diff someone
reads" property that is the whole guard.

---

### Decision 4 — the `visual` argument: shape, name, default, and structural isolation

**Signature.** One new keyword-only argument on `audit_semantics`
(`paper_figure_audit.py:179-182`), placed after `expected_components` so the
existing call at `paper_cli.py:2943-2949` stays valid unchanged:

```python
def audit_semantics(
    *, tex: str, manifest: dict, section_text: str,
    contract_figure: dict | None, expected_components: list | None = None,
    visual: dict | None = None,
) -> dict:
```

**Shape.** Plain data only — `str`, `int`, `float`, `bool`, `list`, `dict`.
Never a `Path`, so `The Audit Is Read Without Its Module` holds for whatever
check reads it later.

```json
{
  "verdict": "fail",
  "provenance": {
    "tool": "pdftoppm", "dpi": 150, "dpiSource": "flag",
    "colorModel": "gray", "inkMaxLevel": 200, "connectivity": 8,
    "pixelWidth": 1481, "pixelHeight": 702, "ptPerPx": 0.48,
    "declaredBorderPt": 2.0
  },
  "dimensions": {
    "out-of-bounds":        {"verdict": "pass", "reason": null, "edges": {}},
    "overlap":              {"verdict": "fail", "reason": null,
                             "collisions": [{"pixel": [[10,20],[40,60]],
                                             "point": [[4.8,9.6],[19.2,28.8]]}]},
    "canvas-occupancy":     {"verdict": null, "reason": null,
                             "bands": [0.31, 0.02, 0.00, 0.00]},
    "legibility":           {"verdict": "unmeasured", "reason": "<code>"},
    "connection-correctness": {"verdict": "unmeasured", "reason": "VISUAL_MEANING_NOT_A_PIXEL_PROPERTY"},
    "style-quality":        {"verdict": "unmeasured", "reason": "VISUAL_JUDGEMENT_NOT_MEASURED"},
    "overlap-ownership":    {"verdict": "unmeasured", "reason": "UNATTRIBUTED_INK"}
  }
}
```

`canvas-occupancy` carries `"verdict": null` **and the key is present** — the
dimension exists in the roster, and its verdict slot is explicitly empty rather
than absent, so "this dimension has no verdict by design" is readable and
`Requirement: Canvas Occupancy Is Evidence, Never a Verdict` is satisfied
without the key vanishing.

**The default, and where it lives.** When `visual is None`, the returned report
carries the full roster with every dimension `{"verdict": "unmeasured",
"reason": <code>}` and `"provenance": null`. The roster cannot be built by
importing `figure-review` — the proposal forbids it. So the roster, its tier
classification, and the reason-code vocabulary are declared **once** in a new
shared shelf:

```
skills/_core/figure/figure_dimensions.py
```

imported by both `paper_figure_audit.py` (consumer default) and
`skills/figure-review/scripts/findings.py` (producer), via the same
`sys.path.insert(parents[2] / "_core" / ...)` pattern `paper_figure.py:34-35`
already uses for `impl_refusals`.

**Alternatives considered.** *Declare the roster twice and add an equality test.*
Rejected, and the repository argues the case itself: a drift test proves drift
*happened*, whereas one definition makes it impossible — the exact reasoning at
`tests/test_proposal_implementation.py:8950-8953` ("the floor is written down
somewhere other than `DEFINITION`, so the two can drift apart"). *Put the roster
in `paper_figure_audit.py` and have `figure-review` import paper-writing.*
Rejected: it makes a new skill depend on the skill this change deliberately kept
it out of, in the reverse direction, and puts paper-writing's whole import graph
behind a raster measurement. *A `_core/figure/` shelf adds no command* —
confirmed: `collect_commands` skips `_`-prefixed directories
(`generators.py:199`), and `test_every_repository_skill_ships_in_the_workspace`
(`test_workspace_skills_e2e.py:69-73`) compares `_core` dynamically on both
sides.

**Known gap in that shelf, closed by construction.** `_core/figure/` is outside
`IMPORT_SCOPE_PATHSPECS` (`test_forge_gate.py:57` covers
`skills/*/scripts/*.py`), so the third-party import guard never scans it.
Mitigation: the module is a roster of string constants, and a test asserts its
AST contains **zero** `Import`/`ImportFrom` nodes — which makes the scan
unnecessary rather than merely absent.

**Isolation, enforced rather than intended.** Three mechanisms, none of which is
a comment:

1. **Structural.** `visual` is read in exactly one place —
   `report["visual"] = visual if visual is not None else default_visual()` —
   placed **after** the verdict computation at `paper_figure_audit.py:263-269`.
   The verdict is already bound to a local `str` before `visual` is touched, so
   there is no code path from a visual value to the semantic verdict.
2. **Namespace.** Visual verdicts live under `report["visual"]["dimensions"]
   [<dim>]["verdict"]`. Nothing writes to `report["verdict"]` outside
   `:263-269`.
3. **Test.** Lock 4: a caller-supplied `visual` with `overlap` = `fail`
   alongside a manifest/contract/prose that agree leaves top-level `verdict` at
   `pass`.

---

### Decision 5 — the join is a `--visual-report <path>` flag, not a derived scratch location

**Choice.** `figure audit` gains `--visual-report <path>`, resolved through the
existing `_resolve_repo_path` (`paper_cli.py:2112-2125`), parsed as JSON, and
passed to `audit_semantics(visual=...)`. `figure-review measure` writes that
JSON; the operator or agent names it on the call. No import, in either
direction.

**Alternatives considered.**

- *A derived scratch file at `figure_paths(...)["scratch"] / "visual.json"`,
  read implicitly.* Rejected on three measured grounds. (1) **It does not exist
  for half the verb's invocations**: `scratch_dir` is `None` whenever
  `--file`/`--manifest` is used instead of `--figure-id`
  (`paper_cli.py:2879-2888`), so the join would silently be unavailable on that
  path — a capability that is present or absent depending on which mutually
  exclusive operand the caller chose, with nothing saying so. (2) An implicit
  location **silently re-consumes a stale report**: the scratch directory
  persists between runs, so a visual report from a previous, differently-rendered
  figure would be read as this run's measurement with nothing naming it. (3) The
  explicit-path operand is the precedent already set — `_resolve_repo_path`
  exists for `--draft`/`--audit`/`--transcript` (`:2113`) and reuses
  `PAPER_OUTSIDE_REPOSITORY` rather than inventing a code.
- *A new refusal code for an unreadable visual report.* Rejected: reuse. An
  out-of-tree path is `PAPER_OUTSIDE_REPOSITORY` (already classified
  `INVOCATION_DEFECT` at `paper_cli.py:189`); an absent or unparseable file is
  `DIAGRAM_SOURCE_ABSENT`, which `_cmd_figure_audit` already uses twice for
  "this call cannot audit from these sources" (`:2890-2894`, `:2895-2908`).

**Where the PNG goes, and why that was worth confirming.** The raster and its
provenance are written to `figure_paths(...)["scratch"]` =
`paper/.paper-writing/figures/<id>/` (`paper_figure.py:95`). `.gitignore:111`
ignores `paper/*` with only `!paper/.gitkeep` escaping it, and the comment at
`:106-112` states that this **deliberately** covers `paper/.paper-writing/` with
no separate line needed. So the raster is transient by design and no product is
silently dropped from history — because nothing there is intended to be history.

**The corollary that matters more.** Committed **fixtures** must therefore
**never** live under `paper/`, or they would be written, appear to exist locally,
and never reach the repository. They go to `tests/fixtures/figure-review/`,
beside the existing `tests/fixtures/paper-figure/*/provenance.json` precedent.

---

### Decision 6 — one threshold, 8-connectivity, and both recorded in every finding

**Choice.** `INK_MAX_LEVEL = 200` on an 8-bit 0–255 grayscale scale: a pixel is
ink **iff** `level <= 200`. Connected components use **8-connectivity**. Both
constants, plus the resolving tool, dpi, `dpiSource`, colour model and
`ptPerPx`, are recorded in `visual.provenance` on every finding.

**Why 200, measured against the two populations it must separate.**

- Anti-aliasing halo at the outer edge of a black stroke at 150 dpi lands in the
  ~230–254 band. At 200 it falls **outside** ink, so a halo neither inflates a
  bounding box by a pixel nor manufactures border ink.
- A deliberate light TikZ fill does land inside: `fill=black!25` renders at level
  ≈ 191, `black!22` ≈ 199.
- 200 sits in the gap between those two populations rather than at a round
  number nobody measured.

**The cost, named rather than discovered later.** A fill lighter than ≈ 22%
black (level > 200) is invisible to this pass. That is a real blind spot, it is
recorded as `inkMaxLevel` in every report, and it is preferable to the
alternative: a threshold high enough to see a 10% fill also sees every
anti-aliasing halo, which would make every stroke's bounding box one pixel too
large in each direction and turn abutting boxes into false overlaps — breaking
lock 2 at exactly the boundary lock 2 exists to protect.

**Why 8-connectivity.** Under 4-connectivity an anti-aliased diagonal stroke
fragments into many components, each with its own bounding box, and those boxes
overlap each other — producing `overlap: fail` on a single clean arrow. 8
keeps a diagonal stroke one region. Recorded as `connectivity` because it changes
what counts as one region and therefore what counts as a collision.

**Comparability, stated plainly.** A finding is **not comparable** to a finding
produced by a different rasterizer link, a different dpi, a different
`dpiSource`, a different colour model, or a different threshold. The report
carries all five so the reader can tell; nothing in the code compares two
findings, and nothing should.

**Alternatives considered.** *Two thresholds — a sensitive one for out-of-bounds
and a conservative one for overlap.* Rejected: `Requirement: Background
Threshold, Resolving Tool, and DPI Are Recorded` asks for **the** threshold, and
two thresholds make two dimensions of one report incomparable with each other,
which is worse than either being imperfect. *Otsu or another derived threshold.*
Rejected: a per-image threshold means two runs of the same figure can disagree,
and the constant is the thing that makes lock 1 and lock 2's boundary fixtures
meaningful at all.

---

### Decision 7 — a measured glyph route exists; text height is the measurement, legibility is not

The proposal places `legibility` in Tier 2 with reason `NO_GLYPH_METRICS`. That
reason is **contradicted by disk**, and the contradiction is reported rather than
absorbed.

**What was found.**

| Route | Yields | Status here |
|---|---|---|
| `pdffonts` | font names, embedding, type | **No sizes.** Not a legibility route |
| LaTeX `.log` | warnings, box diagnostics | **No glyph sizes.** Not a route |
| `pdftotext -bbox` | per-word bounding boxes in points | A real route; poppler, same suite as the measured `pdftoppm` |
| PyMuPDF `page.get_text("dict")` | per-span `size` in points + bbox | A real route; declared `requirements.txt:20`, installed `setup_env.py:51`, travels in `KIT_ENTRIES` |

So `NO_GLYPH_METRICS` — "no measured tool here extracts glyph metrics" — is
false as written. `magick`/`convert`/`mutool` being absent was the wrong
question; glyph metrics come from the PDF's text layer, not from an image tool.

**The ruling.** The thing that is measurable is **text height in points**. The
thing that is not measurable is **legibility**, because "is 6pt too small" is a
threshold judgement about a reader, exactly as "is a third of the canvas blank
too much" is a judgement about composition. So:

1. `legibility` **stays Tier 2** — correctly, but for a different reason than the
   spec gives. Its reason code becomes
   `LEGIBILITY_IS_A_THRESHOLD_JUDGEMENT`.
2. A future `text-height` dimension belongs in the **evidence-only** class
   alongside `canvas-occupancy`: minimum and median span height in points,
   reported as numbers with `"verdict": null`. That is the same pattern the spec
   already blesses.

**Priced, so it is claimed rather than left silently unclaimed.**

| Route | Authored lines | Added coupling |
|---|---|---|
| `pdftotext -bbox` + stdlib `xml.etree` parse + dimension + fixtures + locks | ≈ 150 | a fifth probed tool; no new dependency |
| PyMuPDF span dict + dimension + fixtures + locks | ≈ 70 | first import of a stranded dependency |

**Recommendation: defer the measurement, correct the reason now.** The
measurement is out of this change's approved scope and would push an already
over-forecast delivery further; the false reason code is not, because shipping a
reason that names a tool absence as the cause when the cause is a judgement is
the precise defect this change exists to remove. Deferring is safe **only
because** the correct reason code is shipped with it — a deferral behind an
honest reason is a note, a deferral behind a false one is a defect.

**Spec amendment required (1 of 2).** `visual-finding-boundary`,
`Scenario: Legibility with no glyph-metric tool is an announced silence`
(`specs/visual-finding-boundary/spec.md:38-44`) names `NO_GLYPH_METRICS` and
premises it on `magick`/`convert`/`mutool` absence. It needs the reason code and
the premise replaced. `sdd-tasks` must carry this as a task.

---

### Decision 8 — out-of-bounds is answerable only when the source declares a border

**The finding.** `\documentclass{standalone}` fits the page to the content's
bounding box. With no `border`, ink **is** on the outermost pixel row by
construction, so out-of-bounds would report `fail` on every correctly-drawn
figure — a verdict that always fails, which is as useless as a guard that can
never fire.

Measured, this repository is mostly protected and not entirely:
`paper_tikz.py:60` authors `\documentclass[tikz,border=2pt]{standalone}`, so the
skill's own default leaves ≈ 4.2 px of margin at 150 dpi and row 0 is
background. But `paper_tikz.py:270-273` **deliberately leaves a border-less
`standalone` as authored** ("attach a border deliberately, not as a side effect
of optimization"), so a figure authored `\documentclass[tikz]{standalone}` has a
tight box and the raster cannot distinguish "ink ran off the canvas" from "the
canvas was fitted to the ink."

**Choice.** `figure-review` reads `<id>.tex` beside `<id>.pdf` with its own
minimal `\documentclass[...]` regex and derives `declaredBorderPt`:

- `declaredBorderPt > 0` → `out-of-bounds` carries `pass` / `fail`.
- no border declared, or the header is unparseable → `out-of-bounds` is
  `unmeasured`, reason `NO_DECLARED_BORDER`, and `declaredBorderPt` is recorded
  as `null`.

**Alternatives considered.** *Report `fail` regardless.* Rejected: a correct
border-less figure would read as a defect, and a dimension that fails on
everything stops carrying information. *Import `paper_tikz` to reuse
`_DOCUMENTCLASS_RE` and `STANDALONE_HEADER`.* Rejected: it makes `figure-review`
depend on paper-writing and pulls paper-writing's import graph behind a raster
measurement; the duplicated regex is ~3 lines and the constant it needs
(`border` present in the option list) is a LaTeX fact, not a paper-writing one.
*Take the border as a caller-supplied operand like `expected_components`.*
Rejected: `figure-review` already reads disk (it reads the PDF), so the argument
that justifies `expected_components` being caller-supplied — "this function
performs no disk read" — simply does not apply here.

**Spec amendment required (2 of 2).** `figure-raster`,
`Requirement: Out-of-Bounds Ink Is a Computed Verdict`
(`specs/figure-raster/spec.md:86-105`) says MUST report `pass` or `fail`; both
its scenarios presuppose a raster with a margin. It needs a third scenario for
the border-less case. This narrows the requirement rather than contradicting
either existing scenario, and it is consistent with
`visual-finding-boundary`'s `Every Dimension Is Always Present` (`:55-68`).

---

## Data Flow

```
  render (unchanged)                    figure-review (new)
  ─────────────────                     ───────────────────
  paper/Figures/<id>.tex                     probe ──→ resolved link + PATH
        │ latexmk ×≤4                           │           (exit 0, or exit 2
        ▼ (REPAIR_BUDGET, untouched)            │            RASTER_TOOLCHAIN_ABSENT)
  paper/Figures/<id>.pdf ───────────────→ raster.py
        │                                       │ subprocess (the ONE seam)
  paper/Figures/<id>.tex ──┐                    ▼
   (border only) ──────────┼──→ paper/.paper-writing/figures/<id>/
                           │        <id>.png  +  raster-provenance.json
                           │              │ (gitignored: .gitignore:111)
                           │              ▼
                           └────→ png_read.py ──→ geometry.py ──→ findings.py
                                  (zlib, gray)    (8-conn, ≤200)      │
                                                                      ▼
                                                            visual-report.json
                                                          (plain data, no Path)
                                                                      │
  paper-writing (modified)                                            │
  ────────────────────────                    --visual-report <path> ─┘
  figure audit ─→ _resolve_repo_path ─→ json.loads ─→ audit_semantics(visual=…)
        │                                                     │
        │                          verdict computed FIRST (:263-269)
        │                          then report["visual"] = visual or default
        ▼
  scratch/figure_audit.json  ──→  verify's figure-semantics check
                                  (already-computed dict; no new import,
                                   no Path-typed field)

  skills/_core/figure/figure_dimensions.py
        ├──→ paper_figure_audit.py   (the default roster)
        └──→ figure-review/findings.py (the produced roster)
        one definition, so the two cannot drift
```

**Never an edge:** `paper-writing ──X──> figure-review`, and
`figure-review ──X──> paper-writing`. Both sides reach `_core` only.

---

## File Changes

| File | Action | Description |
|---|---|---|
| `skills/figure-review/SKILL.md` | Create | The checklist `figure-auditor` loads; `name: figure-review` frontmatter + description |
| `skills/figure-review/scripts/review_cli.py` | Create | Front door: `probe`, `raster`, `measure`. No `subprocess` |
| `skills/figure-review/scripts/raster.py` | Create | The chain, per-link argv, per-link timeout, the refusal. **The only module allowed `subprocess`** |
| `skills/figure-review/scripts/png_read.py` | Create | stdlib `zlib` PNG decoder → grayscale `bytearray`; refuses unsupported flavours |
| `skills/figure-review/scripts/geometry.py` | Create | Run-length union-find components, bounding boxes, out-of-bounds, overlap, occupancy |
| `skills/figure-review/scripts/findings.py` | Create | Assembles the `visual` dict from the roster; populates every dimension |
| `skills/_core/figure/figure_dimensions.py` | Create | The dimension roster, tier classification, reason codes — one definition, zero imports |
| `skills/paper-writing/scripts/paper_figure_audit.py` | Modify | `audit_semantics` gains `visual: dict \| None = None` (`:179-182`); return gains `"visual"` (`:273-291`) |
| `skills/paper-writing/scripts/paper_cli.py` | Modify | `--visual-report` on the `figure audit` subparser (`:3537-3561`); read + pass in `_cmd_figure_audit` (`:2943-2949`) |
| `skills/paper-writing/SKILL.md` | Modify | `:1397-1403` — the visual half is measured; the precondition is a command |
| `.claude/agents/figure-auditor.md` | Modify | `:3`, `:58-67` precondition rewrite; `:102-113` `state` gains `visual` + `assistedReading` |
| `tests/test_figure_review.py` | Create | The three tiers, the seam (4+1), geometry locks, chain locks, roster locks |
| `tests/fixtures/figure-review/*.png` + `provenance.json` | Create | Real captured rasters, mirroring `tests/fixtures/paper-figure/*/provenance.json`'s shape |
| `tests/test_workspace_skills_e2e.py` | Modify | `SKILL_NAMES` `:31-41` → 10-tuple; **add** `test_figure_review_front_door_lists_its_commands` to `SkillFrontDoorTests` (`:98`) |
| `tests/test_papersmith_generators.py` | Modify | `COMMAND_NAMES` `:37-47` → 10-tuple; `== 9` → `== 10` at `:105` and `:108` |
| `tests/test_workspace_commands_e2e.py` | Modify | `COMMAND_NAMES` `:188-198` → 10-tuple; docstring `:186`; test name `:200` (`nine` → `ten`) |
| `.claude/commands/figure-review.md`, `.opencode/commands/figure-review.md` | Create (derived) | `python scripts/sync-repo-harness.py`; `--check` clean |
| `openspec/changes/.../specs/figure-raster/spec.md` | Modify | Amendment 2: border-less out-of-bounds scenario |
| `openspec/changes/.../specs/visual-finding-boundary/spec.md` | Modify | Amendment 1: the legibility reason code and its premise |
| `README.md:10`, `:298`; `README.es.md:6`; `CLAUDE.md:20`; `OPENCODE.md:20`; `openspec/project-context.md:30` | Modify | Hand-written counts nine → ten (`nueve` → `diez`; both READMEs' lines stay Spanish) |
| `src/papersmith/core/manifest.py`, `src/papersmith/generators.py`, `scripts/setup-harnesses.sh` | **Unchanged** | Re-measured generic. `KIT_ENTRIES` carries `skills` wholesale (`manifest.py:48-55`); `collect_commands` derives and sorts (`generators.py:198-214`) |

---

## The roster, re-measured — the proposal's four, plus three it did not count

The four assertions are confirmed line-exact. Three further guards engage, and
two of them are new constraints rather than new edits:

| # | Guard | Location | Fires? | Consequence |
|---|---|---|---|---|
| 5 | `test_every_delegated_stretch_names_what_to_measure_first` | `tests/test_agents.py:415-432` | Only if triggered | Any skill whose `SKILL.md` contains the literal ``delegates to the `​`` MUST also contain `Measure this before delegating`. **Constraint:** `figure-review/SKILL.md` either avoids that phrase or carries the precondition heading |
| 6 | Target-vocabulary leak scan, roster read off the directory | `tests/test_proposal_implementation.py:9252-9259`, `:9261-9280` | **Dynamically, no edit** | `skills/figure-review/**` and `_core/figure/**` are automatically inside `guarded_documents()`. **Constraint below** |
| 7 | `SkillFrontDoorTests` | `tests/test_workspace_skills_e2e.py:98-146` | No — hand-written per skill | So `figure-review` would have **no** front-door test. `Requirement: Presence Is a Command` demands one, so slice 1 **adds** a tenth method |

**Guard 6's constraint, concretely.** The fixed floor is
`("kaggle", "t4", "ceiling", "ramp", "transfer", "latent", "creda", "milcreda")`
(`tests/forge_vocabulary.py:55`, `:79`, `:94`, `:105`), and Rule B adds a
denylist **derived from the operator's `implementations/` tree at test time** —
which is gitignored and therefore not knowable from this checkout. Two concrete
consequences:

1. **`transfer` and `ceiling` are on the fixed floor and are natural words in
   rasterization prose** ("transfer the raster", "the ceiling of the band").
   Shipped `figure-review` files must not use them. Substitutes: "write", "the
   band's upper edge".
2. **The proposal's own motivating example must not reach a shipped file.** It
   names *global discrepancy*, *local discrepancy* and the kernel node
   (`proposal.md:22-24`, `:339`) and the figure id `mm-proposal-summary`. Those
   are the target's science words. `discrepancy` is not on the fixed floor
   today, but Rule B derives from the target's own module basenames, so it
   cannot be cleared from here. Shipped prose, fixture names and figure ids use
   neutral placeholders (`example-figure`, "two boxes", "an arrow").

Guard 6 is the reason this section exists: it will not need an edit, and it will
turn red at apply time if the SKILL.md is written from the proposal's example
prose.

**Two more environment facts that change where files go:**

- `pyproject.toml:37-44` sets `norecursedirs` including `skills`, so a suite
  under `skills/figure-review/tests/` would **never run**. The suite must be
  `tests/test_figure_review.py`.
- `.claude/agents/figure-auditor.md`'s slice-5 rewrite must preserve the literal
  strings `never conclusions` and `measured again`
  (`tests/test_agents.py:405-413`) and the four fields `did` / `stoppedAt` /
  `state` / `owed` (`:393-403`). A rewrite that drops either literal reddens the
  agent suite.

---

## Interfaces / Contracts

```python
# skills/_core/figure/figure_dimensions.py — one definition, zero imports
VERDICT_DIMENSIONS  = ("out-of-bounds", "overlap")
EVIDENCE_DIMENSIONS = ("canvas-occupancy",)
SILENT_DIMENSIONS   = ("legibility", "connection-correctness",
                       "style-quality", "overlap-ownership")
DEFAULT_REASONS = {
    "out-of-bounds":           "RASTER_NOT_MEASURED",
    "overlap":                 "RASTER_NOT_MEASURED",
    "canvas-occupancy":        "RASTER_NOT_MEASURED",
    "legibility":              "LEGIBILITY_IS_A_THRESHOLD_JUDGEMENT",
    "connection-correctness":  "VISUAL_MEANING_NOT_A_PIXEL_PROPERTY",
    "style-quality":           "VISUAL_JUDGEMENT_NOT_MEASURED",
    "overlap-ownership":       "UNATTRIBUTED_INK",
}
def default_visual() -> dict: ...   # every dimension present, unmeasured

# skills/figure-review/scripts/raster.py — the only subprocess module
CHAIN = ("pdftoppm", "pdftocairo", "gs", "sips")
RASTER_TIMEOUT_S = 60
DEFAULT_DPI = 150
def resolve_link(path: str | None = None) -> str | None: ...
def rasterize(pdf: Path, out_dir: Path, *, dpi: int = DEFAULT_DPI,
              path: str | None = None) -> dict: ...
# → {"tool","argv","dpi","dpiSource","png","pixelWidth","pixelHeight","colorModel"}
# raises Refused("RASTER_TOOLCHAIN_ABSENT", <four tools + the PATH searched>)

# skills/figure-review/scripts/png_read.py — no subprocess
def read_gray(png: Path) -> tuple[int, int, bytearray]: ...
# raises Refused("RASTER_FORMAT_UNSUPPORTED", <bit depth / colour type / interlace>)

# skills/figure-review/scripts/geometry.py — no subprocess
INK_MAX_LEVEL = 200
CONNECTIVITY = 8
def ink_regions(w: int, h: int, gray: bytearray) -> list[tuple[int,int,int,int]]: ...
def out_of_bounds(w, h, gray) -> dict: ...      # 1-px band, per-edge counts
def overlaps(boxes) -> list[dict]: ...          # STRICT intersection
def occupancy(w, h, gray, *, bands: int = 4) -> list[float]: ...
```

`out-of-bounds` band, stated precisely: rows `y == 0` and `y == h - 1`, columns
`x == 0` and `x == w - 1`. Exactly one pixel. Ink at `y == 1` is not counted.

`overlaps` strictness, stated precisely: boxes as half-open `[x0, x1)` × `[y0,
y1)`; overlap iff `x0_a < x1_b and x0_b < x1_a and y0_a < y1_b and y0_b < y1_a`.
Sharing one edge column yields zero interior penetration and is **not** overlap.

---

## Testing Strategy

`strict_tdd: true` (`openspec/config.yaml:1`). RED before GREEN for every lock,
and the mutation is chosen as one a **weaker** lock would survive.

| Layer | What to test | Approach |
|---|---|---|
| Unit | PNG decode, components, boxes, thresholds, roster | Fixture-driven, no rasterizer required |
| Integration | chain link selection, refusal, the seam, the `visual` default | Injected `PATH` with stub executables; tempdir AST scans |
| E2E | `figure audit --visual-report` end-to-end; ledger byte-identity | `run_workspace_script` over a real captured raster fixture |

### The lock table — twelve locks, each with the mutation it must survive

| # | Lock | Mutation a weaker lock survives | What the test must therefore use |
|---|---|---|---|
| 1 | out-of-bounds band | band `1px → 0px`, or `>=` → `>`, so ink on the last row stops counting | ink on **exactly** the outermost row; and a second fixture with ink on row 1 only, asserting `pass` |
| 2 | overlap strictness | strict → "intersect **or** touch" (`<` → `<=`) | two boxes sharing **exactly one edge column** → `pass`; **one column** of penetration → `fail` |
| 3 | `unmeasured` default | delete the default-population line so `visual` is absent or `None` | read **every** dimension by key on the unmeasured path; `KeyError` is the RED |
| 4 | verdict isolation | let `visual.dimensions.overlap.verdict == "fail"` set top-level `verdict` | semantic `pass` **plus** visual `fail` → top-level stays `pass` |
| 5 | budget isolation | one `_write_ledger` / `paper_latex.compile` call in the visual path | ledger bytes **byte-identical** before/after a full pass, `attemptsUsed` unchanged; and the same over a chain that fails every link |
| 6 | the seam | empty exception tuple, or a scan returning `{}` unconditionally | plant `import subprocess` in a second tempdir script; **and** `len(...) == 1` with the exact name; **and** non-vacuity (scanned set == on-disk set, non-empty) |
| 7 | chain fallback | collapse the chain to link 1 — every naive test survives it, because `pdftoppm` is present here | four injected-`PATH` cases holding only link 2, only 3, only 4, and **none**; the last asserts the refusal names all four tools **and** the searched `PATH` |
| 8 | roster (**inherited**) | none — the four assertions already fire on a tenth skill | stated explicitly so nobody claims credit for authoring this lock |
| 9 | the threshold boundary | `<=` → `<` at `INK_MAX_LEVEL`, or the constant nudged by one | fixture pixels at **exactly level 200** (ink) and **exactly 201** (background); a fixture using only pure black and pure white survives every threshold mutation |
| 10 | the border precondition | delete the border read, so out-of-bounds always carries a verdict | a **border-less** `standalone` source whose ink **is** on row 0 → `unmeasured` / `NO_DECLARED_BORDER`, **not** `fail`. A bordered clean fixture survives the mutation |
| 11 | one roster, not two | re-declare the roster in `paper_figure_audit.py` and let it drift | `paper_figure_audit`'s default keys **==** `figure_dimensions`' roster, read from the module, and `figure-review`'s produced keys likewise |
| 12 | `_core/figure/` stays import-free | add a third-party import to the shelf that the forge gate never scans | AST of `figure_dimensions.py` contains **zero** `Import`/`ImportFrom` nodes |
| 13 | PNG flavour refusal | accept a 16-bit or palette PNG and mis-read its stride | a 16-bit-depth fixture and an interlaced fixture each refuse `RASTER_FORMAT_UNSUPPORTED`; a decoder that ignores the header passes on 8-bit fixtures alone |

### The three unconditional tiers

Per `figure-raster`'s `Requirement: No-Skip Test Evidence Across Three Tiers`,
all three run on a machine with **no** rasterizer, and none is skipped:

1. **Fixture-driven geometry** — committed PNGs under
   `tests/fixtures/figure-review/`, decoded and measured in-process.
2. **Injected `PATH`** — a tempdir holding a stub executable named for exactly
   one link, which writes a committed fixture's bytes to the expected output
   path and records its own argv. Proves invocation shape per link without any
   real rasterizer.
3. **Emptied `PATH`** — `PATH=""`, asserting exit 2 and the refusal naming all
   four tools and the searched `PATH`.

No `skipTest`, no `@unittest.skipUnless`, in any of the three.

### Fixture provenance

`Requirement: Raster Fixture Provenance` and `tests/fixtures/paper-figure/
*/provenance.json`'s shape, applied to rasters. Every committed PNG carries a
sibling `provenance.json`:

```json
{"tool": "pdftoppm", "toolVersion": "pdftoppm version 25.x",
 "argv": ["pdftoppm","-png","-gray","-r","150","-f","1","-l","1","<src>.pdf","<prefix>"],
 "sourcePdf": "<relative path>", "dpi": 150, "dpiSource": "flag",
 "colorModel": "gray", "pixelWidth": 1481, "pixelHeight": 702,
 "capturedAt": "<ISO 8601>", "os": "Darwin 25.5.0"}
```

The threshold-boundary fixtures for lock 9 are the one place where a **captured**
raster cannot supply an exact level-200 pixel on demand. Rule: capture a real
raster, then record in `provenance.json` the byte-level post-processing applied
and why — never a hand-drawn image passed off as a capture. The provenance's job
is that nobody can mistake one for the other.

---

## Threat Matrix

This change adds subprocesses and shell-tool invocation, so the matrix applies.
The template's five rows first, then the rows this boundary actually has.

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | `requirements.txt`, `CMakeLists.txt`, executable Markdown, `README.sh` | **N/A** — `figure-review` classifies no file as executable and executes nothing it reads. It consumes a `.pdf` and writes a `.png` | — | — |
| Git repository selection | `git -C`, relative, absolute | **N/A** — no git invocation on any code path. The `git ls-files` calls are pre-existing test helpers | — | — |
| Commit state | staged, `commit -a`, empty index | **N/A** — no VCS automation | — | — |
| Push state | tracking branch, first push, refspec | **N/A** — no VCS automation; delivery is four commits on `main` by hand | — | — |
| PR commands | `--head`, env prefix, composed | **N/A** — branches and PRs are forbidden for this change by operator ruling | — | — |
| **Subprocess argument composition** | operand beginning `-`; spaces; `;`/`\|`; non-ASCII; `--` unsupported by a link | **Applicable** | argv **list** only, `shell=False`, never a composed string. The PDF operand is resolved **absolute** before argv, so it always begins `/` and cannot be read as a flag on any of the four tools | A figure path containing a space, a `;`, and one beginning `-` each rasterize via a stubbed link with argv asserted element-by-element |
| **PATH resolution / tool discovery** | empty `PATH`; a link present but not executable; a same-named non-rasterizer earlier on `PATH`; relative `PATH` entries | **Applicable** | `shutil.which` only; the resolved absolute path is recorded in `argv[0]` and in the provenance. A link that resolves but exits non-zero is a **link failure** → fall through, never a global refusal | Empty `PATH` → exit 2 naming four tools; a stub that exits 1 → next link used; the resolving link named in the report matches the stub actually invoked |
| **Subprocess timeout and resource bound** | a link that hangs; a link that hangs on the *last* position | **Applicable** | Per-link `timeout=RASTER_TIMEOUT_S` (60 s), **never one shared chain budget**; timeout → kill → next link. A timeout on the last link yields the absence refusal naming the timeout, not a false "absent" | A stub that sleeps past the bound → the next link is used; a chain of four sleeping stubs → refusal naming timeout per link |
| **Path containment of the caller-supplied operand** | `../../etc/passwd`; a symlink out of tree; an absolute path outside the repo | **Applicable** | `--visual-report` goes through the existing `_resolve_repo_path` (`paper_cli.py:2112-2125`) and its `PAPER_OUTSIDE_REPOSITORY` refusal. `figure-review`'s own PDF operand resolves and is checked against the repo root the same way | `--visual-report ../../tmp/x.json` → `PAPER_OUTSIDE_REPOSITORY`; a symlink escaping the tree → same code |
| **Untrusted output parsing** | a truncated PNG; 16-bit; palette; interlaced; a zlib bomb; zero-byte output; a link that exits 0 writing nothing | **Applicable** | `png_read` validates signature, IHDR, bit depth, colour type and interlace **before** inflating, and refuses `RASTER_FORMAT_UNSUPPORTED` by name. Decompressed size is bounded by `width*height*channels + height` from IHDR, so a bomb refuses rather than allocating. A zero-byte or missing output is a **link failure** → next link | Truncated, 16-bit, palette, interlaced, zero-byte, and oversized-inflate fixtures each refuse by name; a stub exiting 0 with no output file → next link used |
| **Scratch write collision** | two concurrent passes on one id; a stale raster from a previous run; a read-only scratch dir | **Applicable** | Output written to a per-call `tempfile.mkdtemp()` inside the id's scratch dir, then atomically `os.replace`d to `<id>.png`; provenance written in the same move. A stale raster is overwritten, never read as this run's | A pre-existing `<id>.png` with different bytes is replaced, and the provenance's `capturedAt` is the new run's |
| **Repair-budget isolation** | any write to the ledger; a failing chain deciding it spent an attempt | **Applicable** | `figure-review` never imports `paper_latex` or `paper_figure` and never opens `ledger.json`. Enforced by the AST scan (no such import) **and** by lock 5's byte-identity assertion | Lock 5, in both directions: a full successful pass and a fully failing chain |

Every **Applicable** row's cases carry into `tasks.md` unchanged as RED tests.
No task is created for an `N/A` row.

---

## Migration / Rollout

No migration. Nothing persists state, rasters live in the already-transient and
already-ignored `paper/.paper-writing/` tree, and no ledger is touched.

### Slices — re-cut to five, because slice 1 cannot be staged and cannot fit

**Two measured constraints force the re-cut.**

1. **The skill directory cannot exist without a valid `SKILL.md`.**
   `collect_commands` skips a skill whose `SKILL.md` is missing or malformed and
   records a warning (`generators.py:199-205`), and
   `test_every_skill_becomes_exactly_one_slash_command` asserts
   `sink == []` — "a healthy workspace skips no skill"
   (`test_workspace_skills_e2e.py:95`). So `skills/figure-review/` plus a
   `SKILL.md` plus the four roster edits are **inseparable**: they are the first
   commit or nothing is.
2. **Slice 1 as proposed forecasts far past ~500.** With the PNG decoder,
   geometry, chain, front door, seam, three tiers and fixtures, it is ≈ 900. The
   operator's ruling authorises exactly this remedy: *split the geometry module
   from the front door.*

The split is available **because** the change's own doctrine supplies it: slice 1
ships the skill claiming **no dimension at all** — `probe` and `raster` only,
emitting a PNG and its provenance. No dimension is reported, so no false reason
code and no premature `pass` ships, and the commit is genuinely green.

| Slice | Content | Forecast | Ends green |
|---|---|---|---|
| **1 — the tenth skill exists, rasterizes, and the roster says so** | `SKILL.md`; `review_cli.py` (`probe`, `raster`); `raster.py` + chain + timeout + `RASTER_TOOLCHAIN_ABSENT`; the seam and its 4+1 assertions; chain tiers (4 injected-`PATH` + empty-`PATH`); the front-door test added to `SkillFrontDoorTests`; the four roster edits; derived command files via `python scripts/sync-repo-harness.py` with `--check` clean | ~480 | yes — claims no dimension, wires nothing into paper-writing |
| **2 — the pixels become numbers** | `png_read.py`; `geometry.py`; `findings.py`; `_core/figure/figure_dimensions.py`; `review_cli.py measure`; fixtures + provenance; locks 1, 2, 9, 10, 11, 12, 13; the border precondition; both spec amendments | ~440 | yes — figure-review measures; paper-writing still untouched |
| **3 — the schema gains its slot** | `audit_semantics(visual=…)` + the always-present `visual` key; `_cmd_figure_audit` supplies `None` so behaviour is identical; `diagram-obligation` deltas; `The Audit Is Read Without Its Module` re-proven; lock 3 | ~300 | yes — no behaviour change |
| **4 — the CLI fills the slot** | `--visual-report` + `_resolve_repo_path`; the join; locks 4 and 5; end-to-end over a real captured raster | ~320 | yes |
| **5 — the agent stops judging** | `.claude/agents/figure-auditor.md` (precondition rewrite, `state` gains `visual` and `assistedReading`, the four fields and both literals preserved); `paper-writing/SKILL.md:1397-1403`; the six unenforced prose counts | ~250 | yes |

Each slice is a **sequential commit on `main`** — never a branch, never a PR,
never a stacked chain. `npm run test:all` (`.micromamba/envs/papersmith/bin/pytest`
plus `node --test`) green on every one of the five.

**The forecast overrun, reported rather than pocketed.** ~1790 authored lines
against the operator's authorised ~1400. The ≈ 390 delta is attributable, not
diffuse:

| Added scope | Why the proposal did not price it | Lines |
|---|---|---|
| `png_read.py` + its flavour-refusal fixtures (lock 13) | The proposal assumed an image library or a PGM intermediate; neither is available uniformly | ~220 |
| The border precondition + lock 10 | `paper_tikz.py:270-273` leaves a border-less source as authored, which the proposal did not read | ~100 |
| Threshold-boundary fixtures (lock 9) | The proposal fixed a threshold but did not lock its boundary | ~50 |
| One-roster shelf + locks 11, 12 | The proposal did not notice the roster would be declared twice | ~50 |

This needs an operator decision before slice 2, not before `sdd-tasks`: the
options are accept ~1790, or defer the `canvas-occupancy` dimension and the
`sips` derived-dpi path to a sixth slice.

### Rollback

`git revert <sha>` per slice, newest first.

- **5** → the agent returns to reporting the visual dimensions `unmeasured`.
  Nothing breaks.
- **4** → reverts the join. Slice 3's `visual` key remains, defaulting to
  `unmeasured` per dimension — today's honest answer, in the schema. Safe
  indefinitely.
- **3** → reverts the schema. Any consumer of `report["visual"]` must be gone
  first, which is why 4 reverts before it.
- **2** → reverts the measurement. Slice 1's skill remains and still rasterizes.
  `_core/figure/figure_dimensions.py` goes with it, so slice 3 must not already
  be applied.
- **1** → reverts the skill **and** the roster edits **together**, or the four
  assertions fail in the opposite direction (a 10-tuple against nine skills on
  disk). Then run `python scripts/sync-repo-harness.py --check` to confirm the
  derived command files are gone and clean.

---

## Open Questions

- [ ] **Amendment 1 — the legibility reason code.** `NO_GLYPH_METRICS` is
      contradicted by disk (`pdftotext -bbox` and PyMuPDF both yield glyph
      metrics). Recommended: `LEGIBILITY_IS_A_THRESHOLD_JUDGEMENT`, with the
      measurement deferred and priced (Decision 7). Needs an operator ruling
      before slice 2 ships the roster. Default if unanswered: ship the corrected
      code, since shipping a false reason is the defect this change exists to
      remove.
- [ ] **Amendment 2 — the border-less out-of-bounds scenario.** `figure-raster`
      `:86-105` needs a third scenario (Decision 8). Additive; no existing
      scenario changes. Default if unanswered: add it.
- [ ] **The ~390-line overrun** (see above). Accept ~1790, or defer
      `canvas-occupancy` and the `sips` derived-dpi path to a sixth slice.
- [ ] **A stranded dependency, out of scope and worth recording.** `PyMuPDF` is
      declared (`requirements.txt:20`), installed (`setup_env.py:51`), travels
      in `KIT_ENTRIES`, and is imported by **nothing**. Not this change's to
      resolve — Decision 1 deliberately does not become its first consumer — but
      it is a real finding and the next change that wants glyph metrics should
      decide it rather than inherit it.

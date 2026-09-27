# Tasks: The Figure Nobody Looked At

## Delivery Authorization — recorded, do not re-raise

The design forecast **~1790 authored lines** against an operator-authorized
budget of **~1400**. The operator explicitly ruled **Option A: accept ~1790
and close everything in this batch** — nothing deferred, `canvas-occupancy`
and the `sips` derived-dpi path are in scope. Five slices, each a
**sequential commit directly on `main`** — never a branch, never a stacked
or standalone pull request. This authorization was given directly by the
operator in the session that produced this task file; a later reader must
not re-ask it, and `sdd-apply` must not re-open it as a pending decision.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1790 (authorized; see above) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes — as five sequential direct commits on `main`, not GitHub PRs |
| Suggested split | Commit 1 → Commit 2 → Commit 3 → Commit 4 → Commit 5 (see work units below) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main (closest match: each slice integrates into `main` in order; the operator's specific instantiation skips PR ceremony entirely and commits directly — recorded here, not a deviation from this file) |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

**Why "Decision needed before apply" is No despite `ask-on-risk`.** The chain
strategy and the total-budget overrun are not open questions carried into
`sdd-apply` — the operator already decided both, explicitly, in the same
session that produced this file (see "Delivery Authorization" above).
`sdd-apply` MUST proceed with the five-commit plan below without asking
again. If a *future* session reopens this change and the operator's ruling
is no longer available in context, `sdd-apply` should treat this table as
the recorded decision, not re-derive it from the `ask-on-risk` default.

### Suggested Work Units

| Unit | Goal | Likely delivery | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | `figure-review` ships as the tenth skill; rasterizes to PNG + provenance; claims no visual dimension yet; roster/count tests updated | Commit 1 (direct to `main`) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_workspace_skills_e2e.py tests/test_papersmith_generators.py tests/test_workspace_commands_e2e.py tests/test_figure_review.py` | `python scripts/sync-repo-harness.py --check` (derived command files) | Revert skill dir + roster edits together (§ Rollback below); `sync-repo-harness.py --check` clean after |
| 2 | Pixels become numbers: decoder, geometry, findings, shared roster shelf, fixtures | Commit 2 (direct to `main`) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_figure_review.py` | N/A — pure computation over committed fixtures, no live rasterizer needed | Revert commit 2; commit 1's raster-only skill remains functional |
| 3 | `audit_semantics` gains the always-present `visual` key, behaviour unchanged | Commit 3 (direct to `main`) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_paper_figure_audit.py tests/test_figure_review.py` | N/A — schema widening only, no CLI wiring yet | Revert commit 3; consumers of `report["visual"]` must not exist yet (they don't until commit 4) |
| 4 | CLI join: `--visual-report <path>`, verdict isolation, ledger byte-identity | Commit 4 (direct to `main`) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_paper_figure_audit.py tests/test_paper_writing.py -k "figure_audit or visual or ledger"` | `pytest tests/test_cli_paper_e2e.py` (hermetic CLI paper journey, exercises `figure audit`) | Revert commit 4; commit 3's default `visual` key remains, reads as today's honest `unmeasured` |
| 5 | Agent precondition rewrite; `SKILL.md` cross-reference; six prose counts | Commit 5 (direct to `main`) | `.micromamba/envs/papersmith/bin/python -m pytest tests/test_agents.py -k figure_auditor` | `pytest tests/test_workspace_agents_e2e.py` | Revert commit 5; agent returns to reporting visual dimensions `unmeasured` in prose, nothing breaks |

Full-suite gate on every commit: `npm run test:all` (both `node --test` and
pytest — running only one has hidden a regression in this repository
before). Baseline at `HEAD` (tag `v0.4.0`): node 653 passed / 0 failed,
pytest 5188 passed / 4 skipped / 0 failed. Each commit's task closes only
when `npm run test:all` is green against that baseline (plus this change's
new tests).

---

## Phase 0: Spec Amendments (land before any test asserts on them)

Both additive; neither changes an existing scenario. These MUST land before
Phase 1's tests reference the corrected reason code or the border-less
scenario, so no test is ever written against a spec text that is about to
change underneath it.

- [x] 0.1 Amend `openspec/changes/the-figure-nobody-looked-at/specs/visual-finding-boundary/spec.md:38-44` (Scenario: Legibility with no glyph-metric tool is an announced silence). Replace the reason code `NO_GLYPH_METRICS` and its premise (absence of `magick`/`convert`/`mutool`) with `LEGIBILITY_IS_A_THRESHOLD_JUDGEMENT`, and correct the given/when/then text: glyph metrics ARE measurable via the PDF text layer (`pdftotext -bbox`, PyMuPDF `get_text("dict")`), but legibility is a threshold judgement about a reader, not a pixel property. Preserve Tier 2 classification of `legibility` — only the reason changes, not the tier.
- [x] 0.2 Amend `openspec/changes/the-figure-nobody-looked-at/specs/figure-raster/spec.md:86-105` (Requirement: Out-of-Bounds Ink Is a Computed Verdict). Add a third scenario: **"A border-less standalone source reports unmeasured, not fail"** — GIVEN a compiled figure whose `\documentclass[tikz]{standalone}` declares no `border` option, WHEN the out-of-bounds check runs, THEN it reports `unmeasured` with reason `NO_DECLARED_BORDER` rather than `fail`, because a border-less standalone fits its own canvas to its ink by construction. Do not alter the two existing scenarios.
- [x] 0.3 Re-read both amended files to confirm the edits are additive/corrective only — no existing scenario's given/when/then text was altered, no requirement was removed.

---

## Phase 1: Commit 1 — the tenth skill exists, rasterizes, and the roster says so (~480 lines)

Claims no visual dimension. Wires nothing into `paper-writing`. Ends green.

### 1.1 — Front door and rasterizer chain (production, guarded by RED tests below)

- [x] 1.1 Create `skills/figure-review/SKILL.md` — the checklist `figure-auditor` loads. Use neutral placeholder vocabulary throughout (e.g. "example-figure", "two boxes", "an arrow band") — never the words `transfer` or `ceiling` (both on the fixed vocabulary floor, `tests/forge_vocabulary.py:79`), and never the target's own science vocabulary ("global discrepancy", "local discrepancy", "kernel node", the figure id `mm-proposal-summary`) per Guard 6 in `design.md` ("The roster, re-measured"). If the phrase `` delegates to the ` `` appears anywhere in the file, also include the exact literal `Measure this before delegating` (Guard 5, `tests/test_agents.py:415-432`); otherwise omit the phrase entirely and skip the literal.
- [x] 1.2 Create `skills/figure-review/scripts/review_cli.py` — front door with `probe` and `raster` verbs (no `measure` yet). `probe` reports the resolved rasterizer link (or the `RASTER_TOOLCHAIN_ABSENT` refusal) and answers `--help`/equivalent per `figure-raster`'s `Requirement: Presence Is a Command the Front Door Answers`. Contains no `subprocess` import.
- [x] 1.3 Create `skills/figure-review/scripts/raster.py` — the only module in the skill permitted `subprocess`. Implement `CHAIN = ("pdftoppm", "pdftocairo", "gs", "sips")`, `RASTER_TIMEOUT_S = 60`, `DEFAULT_DPI = 150`, `resolve_link(path=None)`, `rasterize(pdf, out_dir, *, dpi=150, path=None)` per the exact argv table in `design.md` Decision 2 (list argv, `shell=False`, absolute PDF path resolved before argv construction). Per-link independent `subprocess.run(..., timeout=RASTER_TIMEOUT_S)` — never one shared chain-wide deadline. Raise `impl_refusals.Refused("RASTER_TOOLCHAIN_ABSENT", ...)` (reusing the shared primitive at the depth `paper_figure.py:34-35` already reaches) naming all four probed tools and the exact searched `PATH` when no link resolves. `sips`'s dpi is derived (`dpiSource: "derived"`), computed from `sips -g pixelWidth -g pixelHeight` and the PDF's page-box points; every other link's dpi is `dpiSource: "flag"`. Output is written to a per-call `tempfile.mkdtemp()` inside the id's scratch dir, then atomically `os.replace`d to `<id>.png`, with provenance written in the same move (Threat Matrix row: Scratch write collision).
- [x] 1.4 Wire `review_cli.py probe`/`raster` to call `raster.py`'s functions; write `<id>.png` plus `raster-provenance.json` into `figure_paths(...)["scratch"]` (the same scratch directory `paper_figure.py:95` already resolves).

### 1.2 — Figure-review's own subprocess seam (mirrors `NoSubprocessScanTests`, plus one)

- [x] 1.5 **RED**: In `tests/test_figure_review.py`, add `REVIEW_SCRIPTS = FORGE_ROOT / "skills" / "figure-review" / "scripts"` and `REVIEW_SUBPROCESS_EXCEPTIONS: tuple = ("raster.py",)`, then write the five seam assertions before `raster.py`'s exception is honored by the scanner: (a) `len(REVIEW_SUBPROCESS_EXCEPTIONS) == 1` and equals `("raster.py",)`; (b) a clean scan over `REVIEW_SCRIPTS` returns `{}`; (c) planting a second script `evil.py` importing `subprocess` under a tempdir copy is caught as a violation; (d) planting `raster.py` itself (importing `subprocess`) is tolerated, returning `{}`; (e) **non-vacuity** — the scanner's own scanned-file set equals the on-disk `*.py` set under `REVIEW_SCRIPTS`, and that set is non-empty (guards against assertion (b) passing vacuously on an empty/misconfigured directory). Confirm (b)–(e) fail RED before `raster.py` exists or before the scanner is written.
- [x] 1.6 Write the scanner used by 1.5's assertions, mirroring `scan_forbidden_process_imports`'s shape (`tests/test_paper_writing.py:6104-6133`) but using `rglob("*.py")` (recursive, deliberately, unlike the non-recursive precedent at `:6127`) over `REVIEW_SCRIPTS`. Forbidden set carried unchanged: `import subprocess|multiprocessing`, `from subprocess|multiprocessing import ...`, `os.system`, `os.popen`, `os.exec*`. **GREEN**: confirm all five assertions from 1.5 pass.
- [x] 1.7 **RED then GREEN** — Repair-budget isolation, raster-only half (full end-to-end half is task 4.5): assert by AST that `raster.py` and `review_cli.py` import neither `paper_latex` nor `paper_figure`, and that no file under `skills/figure-review/scripts/` opens or writes `ledger.json`. Mutation to survive: temporarily add a `_write_ledger`-shaped call inside `raster.py` and confirm the test catches it before removing the mutation.

### 1.3 — Chain fallback and PATH/timeout locks (lock 7, and the Applicable Threat Matrix rows scoped to `raster.py`)

- [x] 1.8 **RED**: In `tests/test_figure_review.py`, add four injected-`PATH` cases, each holding only one of: `pdftoppm`, `pdftocairo`, `gs`, `sips`, using a tempdir of stub executables that write a committed fixture's bytes to the expected output path and record their own argv. For "only `gs`" and "only `sips`", additionally assert neither earlier link was invoked as a successful producer. Confirm each fails RED before the corresponding chain step exists.
- [x] 1.9 **RED**: Add the empty-`PATH` case (`PATH=""`): assert exit 2, refusal code `RASTER_TOOLCHAIN_ABSENT`, and the message names all four tools (`pdftoppm`, `pdftocairo`, `gs`, `sips`) and the exact searched `PATH`.
- [x] 1.10 **RED**: Threat Matrix — PATH resolution / tool discovery: a stub that exits non-zero on the first link falls through to the next link (link failure, not a global refusal); the report's recorded resolving-link name matches the stub actually invoked.
- [x] 1.11 **RED**: Threat Matrix — subprocess timeout and resource bound: a stub that sleeps past `RASTER_TIMEOUT_S` on link 1 causes fallthrough to link 2; a chain of four sleeping stubs yields the absence refusal, and the refusal names a timeout (not a false "toolchain absent" for a tool that was actually present and slow).
- [x] 1.12 **RED**: Threat Matrix — untrusted output parsing, chain-fallback half: a stub that exits 0 but writes no output file is treated as a link failure and the chain falls through to the next link (the decoder-half of this row — truncated/16-bit/palette/interlaced/zero-byte fixtures — is Phase 2, task 2.9, since it needs `png_read.py`).
- [x] 1.13 **RED**: Threat Matrix — subprocess argument composition: a figure path containing a space, a `;`, and a path beginning with `-` each rasterize successfully via a stubbed link, with the stub's recorded argv asserted element-by-element (never a composed shell string, `shell=False` throughout, absolute path always resolved first so a leading `-` is never read as a flag).
- [x] 1.14 **GREEN**: Implement the fallback/timeout/argv behavior in `raster.py` so tasks 1.8–1.13 pass. Confirm the naive "collapse to link 1" mutation (lock 7's named mutation) is caught by 1.8/1.9 — on this machine `pdftoppm` is present, so a naive single-link implementation would otherwise pass every test that does not inject `PATH`.
- [x] 1.15 Clear `__pycache__` after any RED/GREEN cycle that reintroduces a same-size mutation for verification (`find . -name __pycache__ -type d -exec rm -rf {} +`), so a stale `.pyc` never masks a mutated source file.

### 1.4 — Roster and count updates (inherited lock 8 — the four assertions already fire on a tenth skill)

- [x] 1.16 Update `tests/test_workspace_skills_e2e.py:31-41` — add `"figure-review"` to `SKILL_NAMES`, sorted, landing between `"experimental-implementation"` and `"kaggle-accounts"` (10-tuple).
- [x] 1.17 Update `tests/test_papersmith_generators.py:37-47` — add `"figure-review"` to `COMMAND_NAMES` at the same sorted position (10-tuple); update the `== 9` literals at `:105` and `:108` to `== 10`.
- [x] 1.18 Update `tests/test_workspace_commands_e2e.py:188-198` — add `"figure-review"` to `COMMAND_NAMES` at the same sorted position (10-tuple); update the docstring at `:186` and the test name at `:200` from "nine" to "ten".
- [x] 1.19 **Add** `test_figure_review_front_door_lists_its_commands` to `SkillFrontDoorTests` in `tests/test_workspace_skills_e2e.py:98-146` — this class is hand-written per skill and does NOT fail on a tenth skill by itself; without this addition `figure-review` would ship with no front-door test at all. Assert the front door answers `--help`/equivalent and names `probe`/`raster` (mirrors `Requirement: Presence Is a Command the Front Door Answers`).
- [x] 1.20 Confirm `test_every_skill_declares_itself` (`tests/test_workspace_skills_e2e.py:75-83`) and `test_every_repository_skill_ships_in_the_workspace` (`:69-73`) pass without further edits — the former is fixed by the `SKILL_NAMES` tuple edit in 1.16, the latter is dynamic-vs-dynamic and unaffected.
- [x] 1.21 Run `python scripts/sync-repo-harness.py` to regenerate `.claude/commands/figure-review.md` and `.opencode/commands/figure-review.md`; confirm `python scripts/sync-repo-harness.py --check` reports clean.

### 1.5 — Vocabulary leak-scan verification for this commit's prose

- [x] 1.22 Run the target-vocabulary leak scan (`tests/test_proposal_implementation.py`, the section around `:9252-9280` that derives `guarded_documents()` dynamically off the skills directory) against everything written in this phase (`skills/figure-review/SKILL.md`, `scripts/review_cli.py`, `scripts/raster.py`, fixture names used in `tests/test_figure_review.py`). Confirm zero hits for the fixed floor (`kaggle`, `t4`, `ceiling`, `ramp`, `transfer`, `latent`, `creda`, `milcreda`) and zero hits for the operator's `implementations/`-derived denylist (not knowable from this checkout, but a real scan run — not skipped).

### 1.6 — Commit 1 close-out

- [x] 1.23 Run the focused command: `.micromamba/envs/papersmith/bin/python -m pytest tests/test_workspace_skills_e2e.py tests/test_papersmith_generators.py tests/test_workspace_commands_e2e.py tests/test_figure_review.py`. All green.
- [ ] 1.24 Run `npm run test:all` in full. Confirm no regression against the `v0.4.0` baseline (node 653/0, pytest 5188 passed/4 skipped/0 failed) plus this commit's new tests. **Deferred by explicit orchestrator instruction**: this apply session was told not to run the full `npm run test:all` (a concurrent session shares this working tree and collides on fixed-name scratch fixtures); the orchestrator runs the full gate once, after all five commits. The focused command (task 1.23) and the leak scan (task 1.22) were run directly by this session and are green.
- [x] 1.25 Commit directly on `main` (no branch). Conventional Commit message, e.g. `feat(figure-review): ship the tenth skill and its rasterizer chain`. **Committed as `e0dc535`.**

---

## Phase 2: Commit 2 — the pixels become numbers (~440 lines)

`figure-review` measures; `paper-writing` remains untouched. Depends on Commit 1's `raster.py` and scratch-directory writes.

### 2.1 — Shared roster shelf (one definition, read by both sides)

- [x] 2.1 **RED**: Write a test asserting `skills/_core/figure/figure_dimensions.py`'s AST contains **zero** `Import`/`ImportFrom` nodes (lock 12) — confirm it fails before the file exists, then confirm it survives a mutation that adds a throwaway `import os` to the file.
- [x] 2.2 Create `skills/_core/figure/figure_dimensions.py`: `VERDICT_DIMENSIONS = ("out-of-bounds", "overlap")`, `EVIDENCE_DIMENSIONS = ("canvas-occupancy",)`, `SILENT_DIMENSIONS = ("legibility", "connection-correctness", "style-quality", "overlap-ownership")`, `DEFAULT_REASONS` mapping per `design.md` Decision 4/7 (`legibility` → `LEGIBILITY_IS_A_THRESHOLD_JUDGEMENT`, matching Phase 0's spec amendment 0.1), and `default_visual() -> dict` populating every dimension `{"verdict": "unmeasured"/None, "reason": <code>}`. Zero imports, string constants only. Confirm task 2.1's test passes.

### 2.2 — PNG decoder (new correctness-critical code)

- [x] 2.3 **RED**: In `tests/test_figure_review.py`, assert a valid, committed 8-bit non-interlaced PNG fixture decodes to known pixel values (exact byte-for-byte expected grayscale buffer for a small fixture). Confirm it fails before `png_read.py` exists.
- [x] 2.4 **RED**: lock 13 — assert a 16-bit-depth PNG fixture, a palette (colour type 3) PNG fixture, and an interlaced PNG fixture each refuse with `RASTER_FORMAT_UNSUPPORTED` naming the offending property (bit depth / colour type / interlace flag). Confirm a decoder stub that ignores the header and passes only on 8-bit fixtures does NOT accidentally pass these three cases — i.e. write the assertions against the refusal, not against "did not crash".
- [x] 2.5 **RED**: Threat Matrix — untrusted output parsing, decoder half: truncated PNG, zero-byte PNG, and an oversized-inflate ("zlib bomb") fixture each refuse `RASTER_FORMAT_UNSUPPORTED` (or a decompressed-size-bound refusal) rather than allocating unboundedly. Bound decompressed size by `width*height*channels + height` read from IHDR before inflating.
- [x] 2.6 Create `skills/figure-review/scripts/png_read.py`: `read_gray(png: Path) -> tuple[int, int, bytearray]`, stdlib `zlib` decode, restricted to bit depth 8, non-interlaced, colour types 0/2/4/6; colour types 2/6 reduced to luminance via integer ITU-R BT.601 (`(299R + 587G + 114B) // 1000`); colour model recorded for provenance. Validate PNG signature, IHDR, bit depth, colour type, and interlace flag **before** inflating. Confirm tasks 2.3–2.5 pass.

### 2.3 — Geometry (connected components, boxes, out-of-bounds, overlap, occupancy)

- [x] 2.7 **RED**: lock 1 — a fixture with non-background ink on exactly the outermost pixel row (or column) reports `fail` naming that edge and the ink pixel count; a second fixture with ink on row/column 1 only (one pixel inward, nowhere on the outermost row/column) reports `pass`. Confirm the `1px → 0px` band-width mutation and the `>=`→`>` mutation are each caught by these two fixtures together.
- [x] 2.8 **RED**: lock 2 — two ink regions whose bounding boxes share exactly one edge column with zero interior penetration report `pass` (abutting is not overlap); two regions sharing one column of interior overlap beyond their shared edge report `fail`, naming both boxes in pixel **and** point coordinates, with no component name attached. Confirm the `<`→`<=` strict-intersection mutation is caught.
- [x] 2.9 **RED**: lock 9 — fixture pixels at exactly grayscale level 200 (ink, per `INK_MAX_LEVEL = 200`) and exactly level 201 (background) each classify correctly; a fixture using only pure black and pure white must NOT be the only boundary evidence (it survives every threshold mutation). Confirm an `<=`→`<` mutation at `INK_MAX_LEVEL` is caught by the level-200/level-201 fixture pair specifically.
- [x] 2.10 **RED**: canvas-occupancy — a raster whose lower half is entirely background reports that band's near-zero non-background fraction as a number with **no** `pass`/`fail` field attached (the key is present, `verdict` is explicitly `None`/`null`, never absent).
- [x] 2.11 Create `skills/figure-review/scripts/geometry.py`: `INK_MAX_LEVEL = 200`, `CONNECTIVITY = 8` (8-connectivity — record the reasoning that 4-connectivity fragments an anti-aliased diagonal stroke into overlapping sub-regions), `ink_regions(w, h, gray)` via run-length row union-find (no numpy/scipy), `out_of_bounds(w, h, gray)` (exactly one pixel band: rows `y==0`/`y==h-1`, columns `x==0`/`x==w-1`), `overlaps(boxes)` (strict half-open interval intersection: `x0_a < x1_b and x0_b < x1_a and y0_a < y1_b and y0_b < y1_a`), `occupancy(w, h, gray, *, bands=4)`. Confirm tasks 2.7–2.10 pass.
- [x] 2.12 **RED**: lock 8 (inherited, documented not authored) — no new test needed; add a one-line note in `tests/test_figure_review.py`'s module docstring or a comment stating this lock is proven by the four roster assertions from Phase 1 (tasks 1.16–1.18), not by anything in Phase 2.

### 2.4 — Border precondition (Decision 8, depends on Phase 0 task 0.2)

- [x] 2.13 **RED**: lock 10 — a border-less `\documentclass[tikz]{standalone}` source fixture whose ink IS on row 0 (by construction, since a border-less standalone fits its own canvas to its ink) reports `out-of-bounds` as `unmeasured` with reason `NO_DECLARED_BORDER`, **not** `fail`. Confirm a bordered clean fixture (e.g. `border=2pt`, ink with margin) survives this same mutation — i.e. write both fixtures so the border-only-fixture test alone would falsely pass a "delete the border read" mutation, and the border-less fixture is what actually catches it.
- [x] 2.14 Implement the border-read in `skills/figure-review/scripts/findings.py` (or a small helper it calls): read `<id>.tex` beside `<id>.pdf` with a minimal, locally-owned `\documentclass[...]` regex (do NOT import `paper_tikz` — that would couple `figure-review` to `paper-writing`'s import graph); derive `declaredBorderPt`. When `declaredBorderPt > 0`, `out-of-bounds` carries `pass`/`fail`; when no border is declared or the header is unparseable, `out-of-bounds` is `unmeasured` / `NO_DECLARED_BORDER` and `declaredBorderPt` is recorded as `null`. Confirm task 2.13 passes.

### 2.5 — Findings assembly and the `measure` verb

- [x] 2.15 Create `skills/figure-review/scripts/findings.py`: assembles the full `visual` dict from `skills/_core/figure/figure_dimensions.py`'s roster, populating every dimension (Tier 1 computed verdicts, Tier 1 evidence-only, Tier 2 announced silence) exactly once, plus `provenance` (`tool`, `dpi`, `dpiSource`, `colorModel`, `inkMaxLevel`, `connectivity`, `pixelWidth`, `pixelHeight`, `ptPerPx`, `declaredBorderPt`).
- [x] 2.16 **RED**: lock 11 — assert `paper_figure_audit.py`'s default visual-dimension keys equal `figure_dimensions`'s roster (read from the shared module, not re-typed), and `figure-review`'s produced keys (from `findings.py`) likewise equal that roster. This test cannot pass until Phase 3 wires `paper_figure_audit.py` to the shared shelf — write it now as RED, note it stays RED until task 3.2, and confirm it in task 3.3. **Split into two test classes**: `RosterDriftLockFigureReviewHalf` (figure-review's own half, GREEN now) and `RosterDriftLockCrossModuleHalfStaysRedUntilCommit3` (the cross-module half, confirmed RED for the documented reason: `audit_semantics` carries no `visual` key yet).
- [x] 2.17 Add the `measure` verb to `skills/figure-review/scripts/review_cli.py`: consumes the PNG + provenance from `raster`, calls `png_read` → `geometry` → `findings`, and writes a plain-data `visual-report.json` (no `Path` objects — string paths, ints, floats, lists, dicts only) into the scratch directory.
- [x] 2.18 **RED then GREEN** — Threat Matrix, untrusted output parsing (chain half, extended to `measure`): a fully failing rasterization (all four links absent) still causes zero writes to any ledger file; confirm this alongside the AST-level check from task 1.7, now that `measure` exists as a second entry point.

### 2.6 — Fixture provenance (raw captures, never hand-drawn)

- [x] 2.19 Capture a real rasterization run against an existing compiled figure PDF (or a minimal fixture-only TikZ figure compiled once for this purpose) at 150 dpi via `pdftoppm`. Commit the resulting PNG(s) under `tests/fixtures/figure-review/`, each with a sibling `provenance.json` recording `tool`, `toolVersion`, `argv`, `sourcePdf`, `dpi`, `dpiSource`, `colorModel`, `pixelWidth`, `pixelHeight`, `capturedAt`, `os` — mirroring `tests/fixtures/paper-figure/*/provenance.json`'s shape. **Delivered as per-fixture subdirectories** (`tests/fixtures/figure-review/<name>/{<name>.png, provenance.json}`), matching the precedent's `*/provenance.json` shape exactly.
- [x] 2.20 For the lock-1, lock-2, and lock-9 boundary fixtures (exact outermost-row ink, exact-one-column overlap penetration, exact level-200/201 pixels) that a captured raster cannot reliably supply on demand: capture a real raster, then record in that fixture's `provenance.json` the exact byte-level post-processing applied and why (never a hand-drawn image passed off as a capture). State explicitly in the provenance which pixels were adjusted and to what value.
- [x] 2.21 Ensure no fixture file uses target-vocabulary words (leak-scan constraint, same as task 1.22) — fixture and figure ids stay neutral (e.g. `example-figure`, not any target science term).

### 2.7 — Commit 2 close-out

- [x] 2.22 Run the focused command: `.micromamba/envs/papersmith/bin/python -m pytest tests/test_figure_review.py`. **56 passed, 1 documented expected failure** (the cross-module half of lock 11, task 2.16 — confirmed GREEN in task 3.3, not here). Every other test, including all 13 locks' RED/GREEN/mutation evidence, is green.
- [x] 2.23 Run the vocabulary leak scan (as task 1.22) against everything added in this phase. `pytest tests/test_proposal_implementation.py -k "leak or guarded"`: 9 passed. Manual `rg` cross-check against every new production/test/fixture file: zero hits.
- [ ] 2.24 Run `npm run test:all` in full. Confirm no regression. **Deferred by explicit orchestrator instruction** (same as task 1.24): a concurrent session shares this working tree; the orchestrator runs the full gate once, after all five commits.
- [x] 2.25 Commit directly on `main`. Conventional Commit message, e.g. `feat(figure-review): compute out-of-bounds, overlap, and occupancy from the raster`. **Committed as `2015efa`.**

---

## Phase 3: Commit 3 — the schema gains its slot (~300 lines)

No behaviour change to any existing caller. Depends on Commit 2's `skills/_core/figure/figure_dimensions.py`.

- [x] 3.1 **RED**: In a suitable location in `tests/test_paper_figure_audit.py`, assert that calling `audit_semantics(...)` with no `visual` argument returns a report whose `report["visual"]` key is present and contains every classified dimension, each carrying `{"verdict": "unmeasured"/None, "reason": <code>}` — reading any dimension by key MUST NOT raise `KeyError` (lock 3). Confirm this fails before `audit_semantics`'s signature changes. Also assert the delete-the-default-population mutation (removing the default-visual line) is caught — i.e. write the test against reading every dimension by key on the unmeasured path, not just checking the top-level key exists. **Confirmed RED** (`TypeError: audit_semantics() got an unexpected keyword argument 'visual'` — 20 tests failed, including every pre-existing `_audit`-based test, before the signature changed).
- [x] 3.2 Modify `skills/paper-writing/scripts/paper_figure_audit.py:179-182` — add one new keyword-only argument to `audit_semantics`: `visual: dict | None = None`, placed **after** `expected_components` so the existing call at `paper_cli.py:2943-2949` stays valid unchanged. Import `skills/_core/figure/figure_dimensions.py` via the same `sys.path.insert(parents[2] / "_core" / ...)` pattern `paper_figure.py:34-35` already uses for `impl_refusals`.
- [x] 3.3 Modify `skills/paper-writing/scripts/paper_figure_audit.py:273-291` — the returned report gains `report["visual"] = visual if visual is not None else default_visual()`, placed **structurally after** the semantic `verdict` is already bound to a local `str` (`:263-269`), so there is no code path from a visual value to the semantic verdict. Confirm task 3.1 passes, and confirm task 2.16 (lock 11) now passes since `paper_figure_audit.py` reads the shared roster rather than re-declaring it. **`RosterDriftLockCrossModuleHalfStaysRedUntilCommit3` is now GREEN**, unmodified, by wiring alone.
- [x] 3.4 **RED then GREEN** — lock 4, first half (schema-level isolation, full CLI-level isolation is task 4.3): assert that a caller-supplied `visual` dict with `overlap.verdict == "fail"`, alongside a manifest/contract/prose combination that otherwise agrees, leaves `report["verdict"]` at `pass` while `report["visual"]["dimensions"]["overlap"]["verdict"]` independently reads `fail`. Confirm the "let `visual.verdict` set the top-level verdict" mutation is caught. **Confirmed**: mutation (`if report["visual"]["dimensions"].get("overlap", {}).get("verdict") == "fail": report["verdict"] = "fail"`) flipped the assertion (`'fail' != 'pass'`), then was removed.
- [x] 3.5 Add the "report always carries a visual key" scenario from `openspec/changes/the-figure-nobody-looked-at/specs/diagram-obligation/spec.md` (Scenario: The report always carries a visual key) and "A visual failure alongside a semantic pass leaves the top-level verdict at pass" as executable tests in `tests/test_paper_figure_audit.py`, tracing them explicitly to those spec scenarios in a comment or docstring. **Done** — `VisualKeyDefaultTests` and `VisualVerdictIsolationTests`.
- [x] 3.6 Re-prove `Requirement: The Audit Is Read Without Its Module` (`openspec/changes/the-figure-nobody-looked-at/specs/diagram-obligation/spec.md:97-107`) against the widened schema: confirm `paper_verify.py`'s import allowlist is unmodified (no new import added), and that no `Path`-typed field was introduced anywhere in the `visual` dict (all values are `str`/`int`/`float`/`bool`/`list`/`dict`/`None`). Add or extend a test asserting this if the existing suite does not already cover it structurally. **Done** — `VisualIsNeverPathTypedTests` (recursive no-`Path` walk over `report["visual"]`, plus a local confirmation that `paper_verify.py`'s AST-enforced allowlist stays exactly `{"re"}` / `{"__future__"}`); `paper_verify.py` itself was not touched this phase.
- [x] 3.7 Confirm `_cmd_figure_audit` in `paper_cli.py` is untouched in this phase — it continues to call `audit_semantics` without a `visual` argument, so its behaviour is provably identical before and after this commit (no CLI flag exists yet; that is Phase 4). **Confirmed**: `paper_cli.py` was not edited this phase (`git diff --stat` shows no change to it).

### Commit 3 close-out

- [x] 3.8 Run the focused command: `.micromamba/envs/papersmith/bin/python -m pytest tests/test_paper_figure_audit.py tests/test_figure_review.py`. All green. **89 passed, 13 subtests passed.**
- [ ] 3.9 Run `npm run test:all` in full. Confirm no regression, and specifically confirm every existing `test_paper_figure_audit.py` test that predates this change still passes unchanged (proving "no behaviour change"). **Deferred by explicit orchestrator instruction** (same as tasks 1.24/2.24): a concurrent session shares this working tree; the orchestrator runs the full gate once, after all five commits. Run instead, all green: `tests/test_paper_writing.py` full (672 passed, 1 skipped, 57 subtests), `tests/test_paper_decisions.py` full (289 passed — confirms the shared `paper_mutation.py` harness fix below didn't regress its own mutation suite), `tests/test_forge_gate.py` full (10 passed), and the leak scan `tests/test_proposal_implementation.py -k "leak or guarded"` (9 passed).
- [x] 3.10 Commit directly on `main`. Conventional Commit message: `feat(paper-writing): widen figure-audit's report schema with an always-present visual key`. **Committed as `b171819`.**

---

## Phase 4: Commit 4 — the CLI fills the slot (~320 lines)

Depends on Commit 3's `visual` argument and Commit 2's `figure-review measure` output shape.

### 4.1 — The `--visual-report` flag and its containment

- [x] 4.1 Modify `skills/paper-writing/scripts/paper_cli.py:3537-3561` — add `--visual-report <path>` to the `figure audit` subparser, following the `--draft`/`--audit`/`--transcript` precedent (`:2112-2125`). **Done**: inserted after `--block` in `p_figure_audit`.
- [x] 4.2 Modify `skills/paper-writing/scripts/paper_cli.py:2943-2949` (`_cmd_figure_audit`) — when `--visual-report` is supplied, resolve it through the existing `_resolve_repo_path` (reusing `PAPER_OUTSIDE_REPOSITORY`, already classified `INVOCATION_DEFECT` at `:189`), `json.loads` it, and pass the parsed dict to `audit_semantics(visual=...)`. An absent or unparseable file reuses the existing `DIAGRAM_SOURCE_ABSENT` code (already used twice at `:2890-2894`, `:2895-2908` for "this call cannot audit from these sources") — no new refusal code is introduced. **Done**, exactly as specified.
- [x] 4.3 **RED then GREEN** — Threat Matrix, path containment of the caller-supplied operand: `--visual-report ../../tmp/x.json` refuses `PAPER_OUTSIDE_REPOSITORY`; a symlink escaping the repository tree refuses the same code. **Done** — `FigureAuditVisualReportJoinTests.test_a_visual_report_outside_the_repository_refuses` and `.test_a_symlink_escaping_the_repository_tree_refuses` in `tests/test_paper_writing.py`. Confirmed RED (flag did not exist) before the parser edit landed.
- [x] 4.4 **RED then GREEN** — lock 4, CLI-level (end-to-end confirmation of task 3.4's isolation): run `figure audit --visual-report <path>` end-to-end over a real captured raster fixture whose `visual-report.json` reports `overlap: fail`, against a manifest/contract/prose combination that otherwise agrees; confirm the CLI's own top-level `verdict` in the emitted `figure_audit.json` is `pass`. **Done** — `FigureAuditVisualReportJoinTests.test_a_visual_failure_alongside_a_semantic_pass_leaves_the_cli_verdict_at_pass` (custom `.scratch/`-rooted sections corpus so the semantic half reaches a real `pass`, not an `unmeasured` that would make the isolation claim vacuous); the persisted-`figure_audit.json` half is additionally confirmed in `VisualPassRepairBudgetLedgerIsolationTests`'s success-direction test (`--figure-id` mode). Mutation `if report["visual"]["dimensions"].get("overlap", {}).get("verdict") == "fail": report["verdict"] = "fail"` planted in `paper_figure_audit.py`, confirmed caught (`'fail' != 'pass'`), reverted.

### 4.2 — Repair-budget isolation, full end-to-end (lock 5)

- [x] 4.5 **RED then GREEN** — lock 5, both directions: (a) a full successful visual pass (`raster` → `measure` → `figure audit --visual-report`) over a figure id with an existing repair ledger leaves the ledger's bytes byte-identical before and after, and `attemptsUsed` unchanged; (b) a rasterizer chain that fails every link, run against the same id, likewise leaves the ledger unchanged (failure to rasterize spends no budget, because there is no ledger call on that path at all). Confirm the "single `_write_ledger` call inside the visual path" mutation is caught by both directions, not just the successful-pass direction. **Done** — `VisualPassRepairBudgetLedgerIsolationTests` in `tests/test_paper_writing.py`. Direction (a) plants inside `_cmd_figure_audit`'s visual-report branch (a bogus `paper_figure._write_ledger` call), caught, reverted. Direction (b) plants inside `raster.rasterize`'s `RASTER_TOOLCHAIN_ABSENT` branch, targeting `out_dir / "ledger.json"` with `out_dir` set to the SAME id's real scratch dir so the write lands on the exact ledger this test reads; caught, reverted. Both mutations confirmed independent (a plant in one location does not make the other direction's test fail, and vice versa) — each direction proves its own half of the "single call anywhere on the visual path" claim.

### 4.3 — End-to-end over a real fixture

- [x] 4.6 Add or extend an end-to-end test (in `tests/test_figure_review.py` or `tests/test_cli_paper_e2e.py`, following the `run_workspace_script` precedent) that runs `figure-review probe` → `raster` → `measure` against a real captured raster fixture from task 2.19, then `figure audit --visual-report <path>` against it, and asserts the combined report shape end-to-end. **Done** — `VisualReportEndToEndAuditTests` in `tests/test_figure_review.py`, using the real `example-figure` fixture (`border=2pt`) with an injected-`PATH` stub that reproduces the real captured PNG bytes (never a fresh/hand-drawn raster). Placed in `tests/test_figure_review.py` rather than `tests/test_cli_paper_e2e.py`: the latter's Unit-1 scope (init/status only, unrelated top-level `papersmith.cli`) never exercises `figure audit`, and adding a real generated-workspace fixture there for this join alone would be disproportionate to this phase's scope; `paper_cli.py` is imported directly instead, the same way `figure-review`'s own test files already cross into `paper-writing` for integration proof (never in production code, confirmed separately).

### Commit 4 close-out

- [x] 4.7 Run the focused command: `.micromamba/envs/papersmith/bin/python -m pytest tests/test_paper_figure_audit.py tests/test_paper_writing.py -k "figure_audit or visual or ledger"` plus `pytest tests/test_cli_paper_e2e.py`. **Both green**: first command 51 passed; second command 32 passed. Additionally ran the full `tests/test_paper_writing.py`+`tests/test_figure_review.py`+`tests/test_paper_figure_audit.py` (771 passed, 1 skipped), `tests/test_paper_decisions.py` (289 passed), and the leak scan `tests/test_proposal_implementation.py -k "leak or guarded"` (9 passed).
- [ ] 4.8 Run `npm run test:all` in full. Confirm no regression. **Deferred by explicit orchestrator instruction** (same as tasks 1.24/2.24/3.9): a concurrent session shares this working tree; the orchestrator runs the full gate once, after all five commits.
- [x] 4.9 Commit directly on `main`. Conventional Commit message, e.g. `feat(paper-writing): join figure-review's visual report into figure audit via --visual-report`.

---

## Phase 5: Commit 5 — the agent stops judging (~250 lines)

### 5.1 — Agent precondition rewrite

- [ ] 5.1 Modify `.claude/agents/figure-auditor.md:3`, `:58-67` — rewrite the precondition from a session-level judgement ("when it is available in this session") to a command whose exit it quotes ("run `figure-review probe` (or equivalent) and quote its exit and resolved rasterizer link"). Preserve every other doctrine sentence unchanged (e.g. "Never repairs the figure" at `:3`, `:20-24`).
- [ ] 5.2 Modify `.claude/agents/figure-auditor.md:102-113` — `state` gains a `visual` block (mirroring the `visual` schema from Commit 3) and an `assistedReading` label, separate from every `visual.<dimension>.verdict` field, per `visual-finding-boundary`'s `Requirement: An Agent's Assisted Reading Is Labelled, Never a Verdict`. Explicitly state that content under `assistedReading` MUST NOT be written into any `verdict` field and MUST NEVER upgrade an `unmeasured` dimension to `pass`.
- [ ] 5.3 **RED then GREEN**: Confirm `tests/test_agents.py:405-413`'s literal-preservation assertions (`never conclusions`, `measured again`) and `:393-403`'s four-field assertions (`did` / `stoppedAt` / `state` / `owed`) still pass after the rewrite — these are pre-existing guards, not new ones, but the rewrite must not accidentally drop either literal or field.
- [ ] 5.4 Add the "an agent quotes the refusal as the unmeasured reason" behavior from `visual-finding-boundary`'s `Requirement: A Toolchain Refusal Is Not an Unmeasured Visual Finding` to `figure-auditor.md`'s worked example or state-shape documentation: when `figure-review` returns `RASTER_TOOLCHAIN_ABSENT`, every visual dimension is reported `unmeasured` quoting that exact refusal code as the reason.

### 5.2 — SKILL.md cross-reference

- [ ] 5.5 Modify `skills/paper-writing/SKILL.md:1397-1403` — the visual half is now measured; update the precondition language to match the command-based check from task 5.1, and confirm the loaded checklist correctly names `figure-review` as the skill that answers it.

### 5.3 — Six unenforced prose counts (hand-kept, never test assertions)

- [ ] 5.6 Update `README.md:10` and `:298` — "nine" → "ten" (English; count of skills).
- [ ] 5.7 Update `README.es.md:6` — "nueve" → "diez" (Spanish stays Spanish per this file's target-context language).
- [ ] 5.8 Update `CLAUDE.md:20` — "nine" → "ten".
- [ ] 5.9 Update `OPENCODE.md:20` — "nine" → "ten".
- [ ] 5.10 Update `openspec/project-context.md:30` — "nine" → "ten".
- [ ] 5.11 Manually read back all six edits against the actual on-disk skill count (10 directories under `skills/`, excluding `_core`) — no test enforces these, so this is a checklist read-back, not an automated check.

### 5.4 — Final vocabulary leak scan (comprehensive, after every slice's prose has landed)

- [ ] 5.12 Run the target-vocabulary leak scan (`tests/test_proposal_implementation.py`'s `guarded_documents()`-derived scan) one final time across the entire change: `skills/figure-review/**`, `skills/_core/figure/**`, `.claude/agents/figure-auditor.md`, `skills/paper-writing/SKILL.md`, and all fixtures under `tests/fixtures/figure-review/`. Confirm zero hits against the fixed vocabulary floor and honestly report that the operator's `implementations/`-derived denylist portion is not fully knowable from this checkout, but that neutral placeholders were used by construction throughout.

### Commit 5 close-out

- [ ] 5.13 Run the focused command: `.micromamba/envs/papersmith/bin/python -m pytest tests/test_agents.py -k figure_auditor` plus `pytest tests/test_workspace_agents_e2e.py`.
- [ ] 5.14 Run `npm run test:all` in full — this is the fifth and final commit; confirm the suite is green with node 653+ passed / 0 failed and pytest 5188+ passed / 0 failed (allowing for the net-new tests added across all five commits) against the `v0.4.0` baseline recorded above.
- [ ] 5.15 Commit directly on `main`. Conventional Commit message, e.g. `docs(figure-review): retire the session-judged precondition for a command figure-auditor can quote`.

---

## Full-Change Success Criteria (traced to `proposal.md`'s own checklist)

- [ ] `figure-review` ships as the tenth skill; the four roster assertions pass against a 10-tuple; `python scripts/sync-repo-harness.py --check` is clean. (Phase 1)
- [ ] `figure audit`'s report always carries a `visual` key; every dimension is either a computed verdict with numbers or `unmeasured` with a named reason; never absent, `null`, or silently `pass`. (Phases 2–3)
- [ ] A visual `fail` alongside a semantic `pass` leaves the top-level `verdict` at `pass` (lock 4). (Phases 3–4)
- [ ] A full visual pass leaves `render`'s ledger byte-identical and `attemptsUsed` unchanged, in both the successful and the fully-failing-chain direction (lock 5). (Phase 4)
- [ ] With an emptied `PATH`, the verb refuses by name quoting every tool it probed, and the agent reports the visual dimensions `unmeasured` quoting that refusal. (Phases 1, 5)
- [ ] Each of the thirteen locks (design's lock table) is proven RED by its named mutation before it is proven GREEN, and the mutation is recorded with the lock in `tests/test_figure_review.py` or the relevant test file's comments.
- [ ] The three test tiers (fixture-driven, injected-PATH, empty-PATH) run unconditionally on a machine with no rasterizer; nothing is skipped, and no tier reports `pass` where it did not run. (Phase 1)
- [ ] `figure-auditor` no longer judges availability: its precondition is a command it runs and an exit it quotes. (Phase 5)
- [ ] `npm run test:all` passes on every one of the five commits. (All phases)
- [ ] The six hand-written counts say ten (`diez`), and no test was invented to enforce a prose claim. (Phase 5)

## Rollback Plan (per commit, newest first)

- [ ] Commit 5 revert → the agent returns to reporting the visual dimensions `unmeasured` in prose. Nothing breaks.
- [ ] Commit 4 revert → reverts the join. Commit 3's `visual` key remains, defaulting to `unmeasured` per dimension — today's honest answer, in the schema. Safe indefinitely.
- [ ] Commit 3 revert → reverts the schema. Any consumer of `report["visual"]` must already be gone, which is why Commit 4 is reverted before Commit 3.
- [ ] Commit 2 revert → reverts the measurement. Commit 1's skill remains and still rasterizes. `skills/_core/figure/figure_dimensions.py` goes with it, so Commit 3 must not still be applied when reverting Commit 2 alone.
- [ ] Commit 1 revert → reverts the skill **and** the roster edits together, in the same revert, or the four roster assertions fail in the opposite direction (a 10-tuple asserted against nine skills on disk). After reverting, run `python scripts/sync-repo-harness.py --check` to confirm the derived command files are gone and clean.

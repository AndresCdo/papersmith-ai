# The paper's prose pass, and the language it is written in

Objective: `paper-writing` states the language its output is written in, and gains an
explicit, opt-in prose pass whose contract is that citations, statistics, methodology and
technical terms are untouchable.

## What was asked for, and what is being built

The operator pointed at a marketplace "academic text humanizer" and asked for it to be
wired into the flow. Reading the artifact's real contract changed the answer:

- The listing attributes it to `brycewang-stanford`, who is only the **curator** of a
  collection of 6 562 vendored files. The author is `HosungYou`, project Diverga:
  `skills/25-HosungYou-Diverga/skills/humanize/SKILL.md`.
- Its purpose is **detection evasion**, not prose editing. It measures an
  `ai_probability_score` 0-100 against a `target_score` defaulting to 30%, reports its
  modes in percentage points of that score, and two of its lines settle it:
  `perturbation_naturalization` "Make edit patterns look human (~74% sub, ~18% del, ~8%
  ins)" and `DT2: Digression injection (authentic tangents)`.
- It needs two MCP servers the operator does not have (Diverga and Humanizer), spawns
  Claude-Code-only subagents (`diverga:g5|g6|f5`), ships no `LICENSE`, and is written in
  Korean at every checkpoint.

Asked to choose, the operator chose **the prose pass with the F5 contract only**.

**What is genuinely valuable and portable is the F5 verifier**: a check whose whole job is
that `citations, statistics, methodology, technical_terms` come out identical, with any
alteration counted as a **FAIL**. That is the forge's own invariant — every claim tied to
its evidence — restated as a contract, so it belongs here on its own merits.

## Verified before writing

- `skills/paper-writing/SKILL.md` contains **no** occurrence of `humaniz`, `language` or
  `idioma`. The language of the paper is currently implicit; the operator decided it is
  English even when the conversation is Spanish.
- The project's `.mcp.json` is a deliberate empty scaffold: *"a starter scaffold naming the
  role, not a working credential: an operator wires a real academic-search MCP server
  here."* A third-party connector is the operator's to wire. `init` writes no MCP config at
  all.
- `skills/proposal-implementation/SKILL.md:201-203` already declares the split the operator
  wants — *"Every artifact stays English ... The conversation does not."* — but only that
  one skill states it.

## Why this forces a version

`skills/` is a shipped root. The repository's rule (`docs/releasing.md`) is that once a tag
exists, any change under `src/`, `skills/` or `scripts/` forces a version move, and
`tests/test_version_sources.py::test_shipped_changes_since_the_last_release_moved_the_version`
enforces it. So this change carries **0.14.0** and its changelog section.

## Decisions

**No new MCP dependency.** The pass must work with nothing installed. When the operator has
wired a humanizer, the pass uses it; when not, it runs a prescribed checklist. A skill that
silently requires a third-party server is a skill that fails in someone else's workspace.

**The contract is the feature.** What makes the pass safe is not the tool it calls but the
list it may not touch, and the rule that any change there is a failure rather than a
warning.

**Nothing is ported from the Diverga skill.** No score, no target, no percentage points, no
edit-pattern mimicry, no digressions. Those are its purpose, and they are not this one's.

## Tasks

- [x] T1 — Branch `feat/paper-writing-prose-pass` off `main`
- [x] T2 — The language rule: the paper is written in English
- [x] T3 — The prose pass: opt-in, with the untouchable list and failure semantics
- [x] T4 — Bump to 0.14.0 and write its changelog section
- [x] T5 — Guards
- [x] T6 — Commit

## Evidence

Two `##` sections added to `skills/paper-writing/SKILL.md`, 62 lines, placed immediately
before `## The writer may assert only what it was given: \`write\``:

```
1040: ## The paper is written in English, whatever language the session is in
1066: ## The prose pass: what it may not touch
1102: ## The writer may assert only what it was given: `write`      (was 1040)
```

The frontmatter `description` is byte-identical — it sits at 1015 of the 1024 bytes
`tests/test_skill_descriptions.py` allows, so growing it was never an option.

Version bumped in all four literals:

```
src/papersmith/__init__.py   __version__ = "0.14.0"
package.json                 "version": "0.14.0"
package-lock.json            2 occurrences
CHANGELOG.md                 ## 0.14.0 section, above ## 0.13.0
```

Guards that can see this change:

```
test_version_sources + test_skill_descriptions + test_harness_parity
+ test_pypi_publishing + test_mcp_docs
→ 36 passed, 4 skipped, 29 subtests passed
```

**Checked before editing, not after**: `tests/test_workspace_commands_e2e.py:112` is the
only test that names `skills/paper-writing/SKILL.md`, and all it asserts is that the file
**exists** in a generated workspace. No test asserts its content, so 62 lines are safe to
add.

## Not done, on purpose

Nothing was ported from the Diverga skill: no detection score, no target percentage, no
edit-pattern mimicry, no digression injection, no Korean checkpoint vocabulary, and no new
MCP dependency. The reasoning is in the changelog entry, where a reader of the release will
find it rather than only here.

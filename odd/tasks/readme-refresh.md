# README refresh: the twelfth skill, the published package and a real mascot

Objective: bring the manual in line with the 0.13.0 tree, replace the hotlinked
mascot with an asset the repository owns, and let the install section lead with
the index now that there is one.

Authorized scope: `README.md`, a new `docs/assets/` entry, `odd/tasks/readme-refresh.md`.
No change under `src/`, `skills/` or `scripts/`.

## What was measured

Counts taken from the tree, not from any document — the manual's own rule at
`README.md:2705`:

| Thing | Command | Result |
| --- | --- | --- |
| Version | `src/papersmith/__init__.py` | 0.13.0 |
| Skills | `ls -d skills/*/` minus `_core` | 12 |
| CLI commands | `papersmith --help` | 12 |
| Agents | `.claude/agents/*.md` | 19 |

## What is stale

- `README.md:14`, `:62`, `:395`, `:678` and `:3567` say "once skills". There are
  twelve since `/upgrade-project` shipped in 0.13.0.
- The skills table at `:71`-`:80` lists eleven rows and never mentions
  `/upgrade-project` at all. The manual documents the framework and omits one of
  its skills.
- `README.md:10` hotlinks the mascot from `https://i.redd.it/jtiaurw1gknf1.gif`.
  That is an external image this repository does not control, on a host that
  promises nothing about hotlinking. It breaks silently the day reddit decides
  otherwise, and the failure is an empty box in the manual.
- The install block at `:152`-`:171` leads with git URLs; `pipx install
  papersmith-ai` appears only in a paragraph underneath. That was right while
  there was no index. 0.13.0 was published to PyPI today.

## What is NOT stale, checked and left alone

- `README.md:2701` contains "el número «once»", and it is a **quotation of a
  fossilized commit message** inside a lesson about never citing a count out of a
  commit message. Editing it would break the lesson it belongs to.
- "los doce comandos del CLI" and "los diecinueve agentes" are correct.
- The warning about the neighbouring `papersmith` on PyPI is still true, and stays.

## Decisions

**The mascot becomes a committed asset.** A manual whose first image is a
third-party hotlink has a dependency it cannot see and cannot pin. The generated
image lands in the repository, and the render stops depending on reddit.

**The anime version replaces the GIF; it does not sit beside it.** Two mascots is
one too many. The base is recorded here for provenance:
`https://i.redd.it/jtiaurw1gknf1.gif`, 320x240, GIF89a, 60 779 bytes, fetched
2026-10-11 during this cycle.

**Only the install section's lead changes.** The git URLs stay, because the tip of
`main` is still the right thing for someone developing the framework. What moves
is which one is offered first.

## Tasks

- [x] T1 — Branch `docs/readme-refresh-and-mascot`
- [x] T2 — Generate the anime mascot with the nanobanana MCP from the base GIF
- [x] T3 — The manual renders the committed asset
- [x] T4 — The five counts become twelve, and the table gains its twelfth row
- [x] T5 — The install block leads with the index
- [x] T6 — Guards green
- [x] T7 — Commit, merge `--no-ff`, push

## Evidence

The mascot, generated from the base GIF with `mcp__nanobanana__generate_image`:

```
✅ Edited 1 image(s) — Gemini 3.1 Flash Image, NB2 tier, 2k, grounding on
📁 docs/assets/agent-smith-anime.jpg — 1195x896, 705.3 KB
```

**16:9 was requested and the model returned 4:3**, which is the base's own
framing, so the result was kept rather than re-rolled. And the file arrived
named `.png` while its bytes are JPEG; `file` says so, and it was renamed to
`.jpg` rather than left lying about its format. The thumbnail the tool also
writes was moved out of the repository to `/tmp`, not deleted.

The counts, measured in the tree at the moment of the change:

```
skills                   12   (ls -d skills/*/ minus _core)
CLI commands             12   (papersmith --help)
agents                   19   (.claude/agents/*.md)
```

The guards that could see this change:

```
test_version_sources + test_pypi_publishing + test_mcp_docs
+ test_paper_evidence + test_harness_parity
→ 109 passed, 4 skipped, 29 subtests passed
```

No test was anchored to the hotlink or to the counts — checked before editing,
not after — so the four commits move documentation and nothing else.

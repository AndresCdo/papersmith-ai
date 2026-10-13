# The manual and the artifacts speak English

Objective: the repository's presentation, flows, generated artifacts and prose are
English, while the conversation with the operator may be Spanish and the skills and
commands stay invocable in Spanish.

Operator decisions, taken explicitly:
- "flujo 1 y 2" means steps 1 and 2 of the numbered flow in the manual
  (`/paper-ingestion`, `/plausibility`). The gates they asked for are a **separate
  cycle**, after this one.
- The paper's **content** is written in English even when the conversation is in
  Spanish. This is a product decision, not a formatting one: it means a paper cannot be
  produced in Spanish. The operator accepted that consequence knowingly.
- Order: language first, gates second.

## Why this is a cycle and not a commit

`src/`, `skills/` and `scripts/` are shipped roots. The repository's own rule (see
`docs/releasing.md`) is that once a tag exists, any change under them forces a version
move. So this work has two halves with different consequences:

| Half | Touches | Forces a version move? |
| --- | --- | --- |
| The manual | `README.md`, `README.es.md` | **No** — documentation is not a shipped root |
| The artifacts | `src/papersmith/templates/`, `skills/*/SKILL.md`, diagram locales | **Yes** — 0.14.0 and a release |

**This cycle does the manual first**, which needs no version move, and then the artifacts.

## Translation brief

Every unit is translated by a separate pass and committed on its own, so the diff stays
readable and `git blame` keeps its granularity.

### Glossary

Use the vocabulary the repository already writes in English — `CHANGELOG.md`,
`docs/releasing.md` and the skills are the authority, not this table.

| Spanish | English |
| --- | --- |
| forja | forge |
| el kit, la copia del kit | the kit, the kit copy |
| andamiaje, andamio | scaffolding, scaffold |
| compuerta | gate |
| deriva | drift |
| proyección (de skills) | projection |
| revisión gestionada | managed revision |
| constelación | constellation |
| huérfano (barrido) | orphan (sweep) |
| migración de artefactos | artifact migration |
| plantilla | template |
| marcador | marker |
| caminata (agente `*-walk`) | the walk |
| ingestión | ingestion |
| deliberación | deliberation |
| propuesta | proposal |
| figura | figure |
| almacén (`store/`) | store |

**Never translate:** paths, directory names (`guidance/`, `sota-pool/`, `proposals/`,
`paper/`, `sections/`, `implementations/`, `experiments/`, `store/`), command names,
CLI flags, file names, agent names (`sota-scout`, `redactor`, `insumos-observer`), code,
command output, or the `<!-- harness-capabilities:start -->` markers and their table.

### Rules

1. **Same content, same arguments, same caveats.** Translate the voice, not the shape:
   no claim added, removed, softened or sharpened. Where the Spanish is opinionated
   ("no es un descuido: es una decisión"), the English stays opinionated.
2. **Keep the em-dash density and the explanatory parentheses.** The manual's register is
   deliberate and must survive.
3. **Every question ends with `?`.** The Spanish used `¿…?`; English uses only `?`. A
   question broken across two lines must still close.
4. **Shell comments are prose and get translated.** The commands themselves never do.
5. **Tables keep their columns.** Translate the cell prose, not the structure.
6. **Mermaid blocks:** translate node and edge *labels*; never the node IDs.
7. **Relative links and the image `src` stay byte-identical.**
8. **Placeholders become English.** The original mixes `<dir>`, `<repo>`, `<id>`, `<slug>`,
   `<path>` and `<token>` with `<nombre>`, `<puerto>`, `<destino>`, `<trabajo>`,
   `<servicio>` and `<carpeta>`. In an English manual the second group becomes `<name>`,
   `<port>`, `<destination>`, `<job>`, `<service>` and `<folder>`. This applies only where
   the token stands for something the user types — never to a real path, directory or
   file name. A tree example that shows a workspace called `mi-paper/` keeps that name
   until the unit that owns it is translated, and then it moves with it.
9. **Neutral register. This rule supersedes "same register" in rule 1.** The operator
   asked for a neutral tone across the whole manual, and that is a deliberate change of
   voice, not a mistranslation to avoid. The Spanish original is opinionated — em-dash
   asides, emphatic negations, second-person address, rhetorical questions — and the
   English must not be. Concretely:
   - State what is true. Do not editorialize about it: no "the interesting part is",
     no "worth knowing before the first run", no "that is the point".
   - Drop the asides and the stage directions. A paragraph that tells the reader how to
     feel about the next paragraph loses that sentence.
   - Keep every claim, every number, every caveat and every refusal code. Neutral is a
     register, never a reduction: cutting a caveat, a limitation or a warning is a
     defect, and so is softening a refusal into a preference.
   - Prefer the plain declarative over the emphatic construction, and the impersonal
     over the direct address, without turning the text into passive bureaucracy.
   - The existing opinionated translations of U0-U8 are revised under this rule, one
     unit per commit, in the same order they were translated.

## Units

Line ranges are from the Spanish original at `0d128f9`. Each unit is one commit.

| # | Unit | Lines |
| --- | --- | --- |
| U0 | Front matter — title, badges, mascot, intro | 1-16 |
| U1 | Índice → Contents | 17-34 |
| U2 | Si es tu primera vez → If this is your first time | 35-59 |
| U3 | Flujo de uso — el camino corto → Use flow — the short path | 60-118 |
| U4 | Puesta en marcha → Getting started | 119-277 |
| U5 | Cómo funciona — el orden → How it works — the order | 278-383 |
| U6 | El workspace por dentro → Inside the workspace | 384-495 |
| U7 | Harnesses y proyección de skills → Harnesses and skill projection | 496-610 |
| U8 | Los agentes → The agents | 611-657 |
| U9 | Anatomía de cada skill → Anatomy of each skill | 658-2922 |
| U10 | Los comandos del CLI → The CLI commands | 2923-3452 |
| U11 | Cómputo remoto, con cuidado → Remote compute, carefully | 3453-3483 |
| U12 | Arquitectura → Architecture | 3484-3521 |
| U13 | Desarrollo y pruebas → Development and testing | 3522-3597 |
| U14 | Solución de problemas → Troubleshooting | 3598-3637 |
| U15 | Documentación relacionada → Related documentation | 3638-3654 |
| U16 | Licencia → License | 3655-3657 |

**U9 is 2,264 lines — 62% of the manual.** It is one `##` section but it holds one
`###` block per skill, so it is committed one skill at a time rather than as a single
unreviewable slab.

## Measured before starting

```
total            3.657 líneas
  prosa          2.210  (60%)
  tablas/marcas    364
  código           477
  bloques          45
preguntas sin cerrar: 0
```

The `?` check is a real check, not an assumption: it walks each `¿` forward across line
breaks to its `?`. Two questions wrap (lines 1410, 1773); both close.

## Tasks

- [x] T1 — Branch `docs/readme-english`
- [x] T2 — Pilot: U0-U3, reviewed for voice before scaling
- [x] T3 — U4-U8
- [x] T4 — The flow reordered: plausibility before ingestion
- [x] T5 — U9, one commit per skill, in neutral register
- [x] T6 — U10-U16, in neutral register. Eight commits, one per unit except the
      last three, which landed together; the deviation is declared in the commit
      that carries it. The manual is English end to end and `scripts/check_manual.py`
      reports 0 errors over it.
- [x] T7 — The neutral-register revision of U0-U8, one commit per unit. Eight
      commits, one per unit that needed one: `bfae53c` U0 · `7e12cf8` U2 ·
      `2fe02ef` U3 · `e18cd1b` U4 · `2bb2304` U5 · `a9f4b0d` U6 · `7818557` U7 ·
      `07df58e` U8. U1, the Contents, needed none and got no empty commit. The
      pass covers **running prose**: headings and table cells were frozen, and
      the second person left inside them is named in L10.
- [x] T8 — `README.es.md` stops claiming the manual is Spanish. It stays Spanish
      (L12); what changed is the claim and one stale count.
- [x] T9 — Guards, then merge. The merge landed earlier than the task: the
      branch went into `main` at `94512a4`, and the units after it were committed
      on `main` directly. The guards were run at the end of the pass (L13).
- [x] T10 — The artifacts half. **Measured, not assumed, on 2026-10-12 and already
      satisfied:** the twelve `skills/*/SKILL.md` (9,603 lines) and the thirteen
      `src/papersmith/templates/*.tpl` (786 lines) are English on the tree; the
      only Spanish left under a shipped root is `docs/diagrams/locales/es.json`,
      which is the Spanish locale and is Spanish on purpose. `0.14.0` is already
      in `CHANGELOG.md` and in `src/papersmith/__init__.py`, so this half forces
      no further version move and no release. The manual is documentation and
      never forced one either.
- [ ] T11 — Blocked on a decision, not on work. The citations are re-pointed and
      `meta.repository.revision` advanced (`3978f19`), and the artifact was **not**
      regenerated: the six-column layout cannot pass two independent gates (L14).
      What the drawing is supposed to show is the open question.
- [x] T12 — Reconcile this record with the tree (2026-10-12): T5 closed, T10
      re-measured, `## Log` opened
- [x] T13 — The manual's mechanical rules become a checkable script,
      `scripts/check_manual.py`, instead of a reading done by hand at every unit.
      It is wired into the fast tier's `GUARDS`, so the anchors and the translated
      lines are re-checked on every fast pass, not only when someone remembers.

## Measured on 2026-10-12, mid-cycle

The three numbers the remaining work is now planned against. They come from the
file, not from an estimate:

```
README.md                        3.852 líneas
  English, U0-U9                 3.117  (81%)
  Spanish, U10-U16                 735  (573 prosa, 73 tabla, 55 código)
  `###` blocks left to translate   13
U0-U8 to revise for register       679 lines of already-English text
SKILL.md + templates in Spanish      0 lines (both halves already English)
```

And the guard's own output on the state U10 started from, re-measured after two
corrections to the rule (L7). `python3 scripts/check_manual.py --lines A-B`
reports that range alone, so one unit's progress is one number:

```
.venv/bin/python scripts/check_manual.py
  13 errors    9 untranslated-heading, 3 spanish-placeholder, 1 inverted-punctuation
 270 warnings  untranslated-line
   0 findings anywhere in lines 1-3117, the part that is already English
```

The zero is the load-bearing number. A check that also fires on the translated
half is a check whose output has to be read, which is the cost it was written to
remove.

## Log

- **L1** — The operator's request that opened the reconciling unit, verbatim:
  *"revisa en que quedamos en este proyecto, analiza el todo, mira si podemos
  optimizar, nos estamos demorando mucho en estos cambios"*.
- **L2** — Operator decision, verbatim in its effect: reconcile this record and
  write the manual's guard **first**, then continue with T6 and T7. Chosen over
  translating straight through and guarding at the end.
- **L3** — Evidence found while reconciling, 2026-10-12: T5 was finished by
  `cb92ded` but still unchecked here, so the plan could not be trusted; T10 was
  planned as "the artifacts half, forcing 0.14.0" when the artifacts are already
  English and 0.14.0 is already released. T12 and T13 close both gaps.
- **L4** — The remaining serial cost was measured at ~22 minutes per unit across
  ten commits on 2026-10-12, which is what L1 was reacting to. The guard exists
  to remove the hand-reading from every one of the units left.
- **L5** — T13 lands with the rule that makes it safe to fail a build on: nothing
  Spanish is detected by a word list, which is how a check starts missing, but by
  *identity against `0d128f9`*. A heading or a prose line the manual still shares
  byte for byte with the text it came from was not translated. Measured before
  wiring it in: 21 headings, and nothing at all in the 3,117 lines that are
  already English. Two rules carry a stated limitation in the script's own
  docstring -- a Spanish question quoted as an example is reported, and a line
  carrying a markdown link is exempt from the identity check -- and the rule a
  machine cannot apply, the neutral register, is left where it was: with the
  reader.
- **L6** — The guard gains a rule before U10 is touched, because the first unit
  is where it would have bitten. The manual's Contents points at the sections by
  anchor, and those anchors are Spanish (`#los-comandos-del-cli`, and
  `#cómputo-remoto-con-cuidado` further down). Renaming a heading without its
  links leaves a reader at a dead anchor, and no other rule here notices: file
  targets are compared against the original, but a `#fragment` is the document
  talking to itself. There are nine of them. Every `](#fragment)` now has to
  land on a heading whose GitHub slug matches it, and the check is document-wide
  on purpose -- a heading and the links pointing at it have to move in the same
  commit, whatever lines they sit on.
- **L7** — Two of the guard's rules reported things nobody had to change, both
  found while translating U10 rather than by design. The document's `#` title is
  the project's name. And ten of the "untranslated" headings were only command
  names in backticks -- `` ### `papersmith init <dir>` `` -- which the brief
  never translates, so they were permanent errors no unit could ever clear. Two
  classes, one cause: identity proves nothing about text a translator was never
  meant to rewrite. The corrected baseline is 13 errors, not the 25 first
  written here, and the 12 difference is exactly those headings. Recorded
  because the first number is the one that would have been planned against.
- **L8** — T6 closes on 2026-10-12 with the manual English from the title to the
  license and the guard reporting 0 errors over the whole file. Two things are
  worth keeping from it. The `untranslated-line` warning earned its place: it is
  what caught three paragraphs of U11 that a commit message had already declared
  translated. And the two warnings left standing are a `Content-Security-Policy`
  value split across two lines, which the identity check cannot recognize as code;
  that limitation now sits in the script rather than waiting to be rediscovered.
- **L9** — T7 was run as a pilot first, the way the translation was. U0 to U3
  landed as three commits, and the operator confirmed the level of intervention
  before the pass scaled to the remaining 559 lines. The answer was to keep it,
  over the two alternatives offered: a lighter pass, which would have left the
  direct address where it was, and a deeper one, which would also have rewritten
  procedure steps and table cells.
- **L10** — T7 closes with a boundary stated rather than implied, because it is
  the part of this rule a reviewer is most likely to disagree with: **the pass
  covers running prose.** Headings cannot be renamed -- the Contents and the
  cross-references point at them -- and table cells were frozen, so the address
  that lives inside them survives. The writers named four of them: the five
  imperative `### Step N` headings, `### papersmith.yaml — the configuration you
  will actually touch`, the flow table's `You invoke` column, and three cells of
  the agent table. A second pass over headings and tables is a decision, not an
  oversight.
- **L11** — One finding the pass surfaced and deliberately did not fix, following
  the rule this cycle already set for U9: a correction needs its own commit with
  its own evidence. U8 says a workspace ships **nineteen** subagents and that the
  routing docs "list all nineteen"; `.claude/agents/` does hold 19 files, and the
  table standing right beside that sentence lists **18**:
  `section-grounding-auditor` is the one it does not have. Both the count and the
  table were frozen by this pass, so neither moved.
- **L12** — T8 rests on the repo's own precedent, which is explicit: a previous
  count fix records that "Spanish stays Spanish per this file's target-context
  language", and `README.es.md` exists only so that old links resolve. So the
  file stays Spanish and what changes is its false claim: the manual no longer
  lives there "en español", it lives in `README.md` in English, and the notice
  now says which date that happened. Its `once skills` was one behind the tree
  and became `doce`; the twelve CLI commands and the nineteen agents it already
  stated were re-measured against the tree and hold.
- **L13** — T9's guards, on 2026-10-12 at the end of the pass, over `README.md`
  (3,838 lines): `scripts/check_manual.py` reports 0 errors and the same 2 known
  warnings, and `tests/test_check_manual.py`, `tests/test_harness_parity.py` and
  `tests/test_version_sources.py` report 47 passed with 32 subtests. The merge
  this task names had already happened in `94512a4`, and what is left of the
  cycle is T11: the diagram was blocked on the manual moving, which is exactly
  what this pass finished doing.
- **L14** — T11's citations are done and its artifact is not, and the reason is a
  measurement rather than an obstacle: **the six-column layout cannot pass the
  gate battery.** Two independent failures, both reproduced:
  - *The 24px minimum connection length.* The source ships `gapX: 21`, and every
    one of the 38 `layout/constraint` reports says 21px. Raising it to 24 clears
    all 38.
  - *The 1240px readability cap.* The cap is arithmetic, not taste: the rendered
    edge labels are 8px and the desktop budget is 930px, so the projected text is
    `8 * 930 / width` and it has to reach 6px, which puts the ceiling at exactly
    1240. At a 24px gap and the node width the longest command label needs
    (186px), six columns floor at `30 + 6*186 + 5*24 + 70 = 1312`, and each term
    has its own floor: the gap cannot go under 24, the node width cannot go under
    the 186px that `/experimental-implementation` measures, and the left padding
    cannot go under the 30px the boundary rectangles need to stay inside the
    canvas. Shrinking the node to 168 was tried and refused by name.
  - The 70px on the right is where a legend sits; moving it does not close the
    72px gap on its own, and 5 columns close it with room to spare (1106px).
  - With five columns, dropping the `plausGate` node and expressing the gate as a
    `security`-variant edge `screener -> pool` **validates clean, 0 diagnostics**.
    The same edge refuses any label at a 24px gap: `gate` needs 46px and `human
    acceptance` needs 103px, so a labeled gate needs the gap widened, which five
    columns can afford (up to 57px) and six cannot.
  - Left open on purpose, because it changes what the drawing shows rather than
    where a box sits: whether the gate stays a node, becomes a labeled edge, or
    the pool node is the one that goes.

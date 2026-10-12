# Experimental Implementation — holder obligations

See [SKILL.md](../SKILL.md) for the full contract. This file documents only
this skill's own checklist-holder obligations — the declared filename, what
happens when it is absent, and what happens when a checklist already exists
under a different name. It does not mirror the sibling's full
`references/usage.md`: this skill ships no `assets/kit/`, so the kit-asset
sections there (`materialize --stage scaffold`/`objects`/`harness`, the
placeholder token table, adoption) do not apply here (see SKILL.md's "Which
commands are not available yet, and why").

## The declared holder: `Experimental_AGREED.md`

This skill declares its own checklist holder in
`impl_profile.py`'s `PROFILE["holder"]`:

```python
"holder": {
    "filename": "Experimental_AGREED.md",
    "headings": ("# Agreed", "## Ladder"),
    "scaffold": "# Agreed\n\n## Ladder\n",
},
```

`Experimental_AGREED.md` is a deliberately distinct name from the sibling's
own `AGREED.md` — the two skills share the same engine and the same
per-product-folder shape, so a fixed shared name would let one skill's write
land inside the other's checklist. Nothing else about a file makes it the
holder: not its item count, not whether it carries a position block, not its
size. A file is this skill's declared holder iff its name is exactly
`Experimental_AGREED.md` and it is a regular file under `<Name>/`.

Reading is unaffected by this declaration: `verify` still finds a checklist
by shape (any `*.md` under `<Name>/` holding checklist items), except a
sibling skill's own declared holder, which is never this skill's (see below). Only a WRITE — `position`'s fresh install/reconcile, or any of
`settle`'s five modes — resolves through the declared name first.

## Create-on-absent

When `Experimental_AGREED.md` does not exist and no other markdown file
under `<Name>/` holds checklist items yet (a sibling skill's own declared
holder does not count, see below), a write (`position --sequence`,
`position --reconcile`, or `settle`'s create path) writes the declared
scaffold to `<Name>/Experimental_AGREED.md` **before** anything else runs:

```
# Agreed

## Ladder
```

That is `HOLDER_SCAFFOLD`, written verbatim — no name interpolation, no
title composed from `--name`, zero checklist items. The file is created only
when `<Name>/` already exists as a directory; this skill never runs
`mkdir()` to bring the product folder itself into existence. If `<Name>/`
does not exist at all, the write instead refuses `POSITION_HOLDER_ABSENT`
(`position`) or `SETTLE_HOLDER_ABSENT` (`settle`) — "no product folder to
create a holder in," never a filename problem.

Once created, the file carries both declared headings
(`# Agreed`, `## Ladder`), so the very next `settle --under "## Ladder"`
places its line without also having to fix a missing heading.

## The sibling's holder is set aside, never refused

A target the sibling `proposal-implementation` already worked on usually holds
its declared `<Name>/AGREED.md`, with settled items in it. That file is the
sibling's, exactly as `Experimental_AGREED.md` is this skill's, so it is never
a candidate here: every holder filename a profile sharing this engine declares
(each `impl_profile.py` beside this skill's own, read for
`PROFILE["holder"]["filename"]` alone) is set aside before the candidate count.
With `Experimental_AGREED.md` absent and only the sibling's holder present, a
write resolves create-on-absent and the sibling's bytes are never touched.
The same rule runs in the other direction: the sibling sets this skill's
`Experimental_AGREED.md` aside.

The set is derived, never a hand-kept list, and fails closed: a sibling profile
that cannot be read contributes nothing, so its holder stays an ordinary
candidate and the refusal below still fires. A workspace that already created
`Experimental_AGREED.md` by hand beside the sibling's holder keeps resolving
it as this skill's declared holder.

The same rule holds for every read that picks this skill's holder: the
`agreements` count (`verify`, `close`) and the position section
(`verify`, `probe`, `gate`, `close`, `discuss`, `settle`, `offer`, `step`) never read the sibling's file,
so its open items are not this skill's open agreements and its position block
is not this skill's position. `agreements` lists the skipped file under
`siblingHolders`, present only when one exists. The collision search `settle`
and `discuss` run (`_agreement_collides`) still inventories every checklist
under `<Name>/`, the sibling's included, because it reports overlap rather than
choosing a holder.

## Write-refusal into an undeclared holder: `HOLDER_UNDECLARED`

When some other markdown file under `<Name>/` — one no skill sharing this
engine declares — already holds checklist items, and `Experimental_AGREED.md`
itself does not exist, a WRITE refuses `HOLDER_UNDECLARED` rather than
silently adopting that file or silently creating a second one beside it:

```json
{
  "status": "refused",
  "code": "HOLDER_UNDECLARED",
  "detail": "Method/TASKS.md holds checklist items under Method/, but this skill declares its own holder as Experimental_AGREED.md and no skill sharing this engine declares 'TASKS.md'; rename Method/TASKS.md to Experimental_AGREED.md in the target repository, or declare 'TASKS.md' in this skill's own PROFILE[\"holder\"][\"filename\"] if that name should become this skill's convention for every target. Sibling skills' own declared holders are recognized and left alone: Method/AGREED.md."
}
```

That detail is the one a target holding both `Method/TASKS.md` and the
sibling's `Method/AGREED.md` produces; the last sentence appears only when a
sibling's holder sits beside the candidate. The sibling's file is never one
of the exits.

Both exits are named in the refusal and neither is chosen for you:

1. rename the found file to `Experimental_AGREED.md` in the target
   repository, or
2. declare the found file's own name in this skill's own
   `PROFILE["holder"]["filename"]`.

Exit 2 is a decision that reaches every target this skill is ever run
against, not only this one — it changes the skill's own convention, not
this target's file. Take it only when the found name really should become
that convention; otherwise rename the file in the target repository
instead. `verify` continues to read the found file by shape either way —
`HOLDER_UNDECLARED` blocks writes, never reads.

When more than one candidate markdown file exists and neither is the
declared name, the write instead refuses the unchanged
`POSITION_HOLDER_AMBIGUOUS` — a human, not a flag, has to choose which file
receives the section.

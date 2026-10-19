# Proposal: A Revision Is Its Bytes

## Intent

Issue LIAUNAL/papersmith-ai#84. `revisionSha256` — in the `AGREED.md` position
header, in `tests/admissibility.json`, in the ledger's `authorization`, `gate`
and `close` events — says which revision a record is bound to, and the skill
documents it as bytes: "`revisionSha256` says which bytes" (`usage.md`), "a
revision whose bytes no longer match" (`SKILL.md`, and the `POSITION_STALE`
refusal itself).

Every binding site hashed something else: the text `revision_source` decoded,
UTF-8 with `errors="replace"` and universal newlines. Two files that decode to
one text — LF against CRLF against a lone CR, or two different undecodable
bytes — shared one identity. A position bound to one read `current` against
the other, a ruling admitted over one read `present`, and a launch token
minted over one gated a launch against the other. The identity claimed bytes
and checked a lossy projection of them.

The same reader hid a second, smaller hole: `_bound_to` read an empty text as
`unknown`, so a revision truncated to zero bytes after binding hid its own
staleness (`position` kept reading `open`).

## Scope

### In Scope

| File | Change |
|---|---|
| `skills/_core/implementation/engine/implementation_engine.py` | `revision_source` returns a `RevisionText`, the decoded text carrying the SHA-256 of the bytes it came from; all nine identity sites hash through `revision_identity`; `position_state` adds `textOnlyMatch` only when some document needs it; `admissibility_record`, `gate` and `close` say when a stored digest names the decoded text; `_bound_to` resolves a zero-byte revision |
| `skills/proposal-implementation/SKILL.md`, `references/usage.md` | the identity rule, the `textOnlyMatch` cause and its recovery |
| `tests/test_implementation_revision_identity.py` (new), `tests/test_proposal_implementation.py`, `tests/test_implementation_pair.py` | acceptance tests at the CLI boundary, under both hosts and at both of the experimental host's document positions |
| `tests/test_implementation_domain_lock.py` | one pin grows deliberately (`before`), with a changelog line |

### Out of Scope

- Admission's pre-existing double read of an extra document: two carriers,
  each consistent with itself; unchanged.
- Checkout policy (`core.autocrlf`, `.gitattributes`): documented, never
  enforced.
- `_extra_document_fidelity_status`: it checks readability, not identity.
- Any edit to a committed record or a historical ledger event.

## Capabilities

### New Capabilities

- None. One requirement is added under an existing capability.

### Modified Capabilities

- `implementation-document-binding`: *Every Scalar Revision Binding Is
  Byte-Identical Under One Document* says this capability introduces "no
  sanctioned delta". This change sanctions exactly two — the identity is the
  bytes, and zero bytes is an identity — keeps every sealed digest, keeps
  every wire shape but one additive key (`textOnlyMatch`, present only on a
  binding the first delta turns `stale`), and adds *A Revision's Identity Is
  The SHA-256 Of Its Bytes*.

## Approach

One read, two readings. The reader takes the file's bytes once, hashes them,
and decodes them through the same pipeline `Path.read_text(encoding="utf-8",
errors="replace")` runs, so every parser reads exactly the text it read before.
The identity travels on the text it belongs to, so `position_state` stays free
of I/O and keeps its signature. For a revision of LF lines in valid UTF-8 —
what the publisher writes, and every sealed fixture — the byte digest equals
the old text digest, so those records, tokens and goldens do not move.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| shared implementation engine | Modified | identity sites, one diagnostic key, three refusal texts |
| proposal-implementation docs | Modified | identity rule and recovery |
| experimental host | Unchanged code | served by the same engine; tested at both document positions |
| `openspec/specs/implementation-document-binding/spec.md` | Modified at archive | delta spec in this change |

## Rollback

Revert the commit. Bindings taken under this change for LF lines in valid
UTF-8 carry the same digest either way. Bindings taken for any other file read
`stale` under the reverted code and are re-bound by the same `position`,
`admit` and `offer` — the recovery, run in the other direction.

## Success Criteria

- [ ] The three acceptance tests the issue names pass at the CLI boundary.
- [ ] Both seal comparators pass without recapturing a golden.
- [ ] The single-document token re-derivation test passes unchanged.
- [ ] A text-only binding refuses with its cause named, never silently.

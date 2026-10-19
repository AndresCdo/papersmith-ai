# Design: A Revision Is Its Bytes

## Technical Approach

`RevisionText.read(path)` reads the file's bytes once, decodes them with
`io.TextIOWrapper(io.BytesIO(data), encoding="utf-8", errors="replace")` — the
pipeline `Path.read_text` runs, universal newlines included — and returns a
`str` subclass carrying `hashlib.sha256(data)`. `revision_source` returns it.
The 26 parse callers see the text they always saw; the nine identity sites call
`revision_identity(source)`, which returns the carried digest.

```
revision file ──read_bytes──▶ data ──sha256──────────────────▶ RevisionText.sha256
                                 │                                  │
                                 │                                  ▼
                                 │            revisionSha256: position header,
                                 │            admissibility.json, authorization /
                                 │            gate / close events
                                 └──decode (utf-8, replace, universal newlines)──▶
                                    str(RevisionText) ──▶ every parser, unchanged
```

## Architecture Decisions

### D1 — The identity is the working-tree bytes

**Choice:** SHA-256 of the file's bytes as read from disk.

**Alternatives:** (a) keep the text digest and document it — rejected: the
docs, the refusal texts and the issue all say bytes, and the text digest
provably collides; (b) the git blob digest — rejected: a revision directory
need not be a checkout, and under `core.autocrlf` blob and working tree
disagree while every reader reads the working tree; (c) a digest over
normalized bytes — rejected: that is the defect with another normalization.

**Tradeoff:** a checkout that rewrites line endings rewrites the identity, so
such a clone re-binds once. That is the honest reading — a lone CR or a
replaced byte can change what a parser sees — and `usage.md` says so.

### D2 — A carrier, not a second read or a new return type

**Choice:** `RevisionText(str)` with a `sha256` property.

**Alternatives:** (a) return `(text, digest)` — rejected: 26 parse callers
change for an identity nine sites need; (b) re-read the file at each identity
site — rejected: two reads can see two files, and `position_state` must stay
free of I/O; (c) return bytes and decode per parser — rejected: the churn of
(a), plus decodes that can drift apart.

**Tradeoff:** any `str` operation returns a plain `str` and drops the digest;
`revision_identity` then hashes the UTF-8 encoding — the convention for an
in-memory text with no file behind it, which direct callers of
`position_state` hand in. That is a provenance escape hatch: the CLI-boundary
tests pin the carrier on every identity path, and no copy or pickle machinery
is added without a consumer.

### D3 — The freshness vocabulary stays closed

**Choice:** `boundTo` keeps `current | stale | unknown`. A stored digest equal
to the decoded text's digest but not the bytes' reads `stale`, and
`position_state` adds `textOnlyMatch: [labels]` only when the list is not
empty. `admissibility_record`'s `stale` detail, gate's `POSITION_STALE` and
close's `POSITION_STALE` name the cause instead of claiming the bytes moved.

**Alternatives:** (a) a new `legacy` state — rejected: every consumer of
`boundTo` (the position fold, refusal classification, `WORK_STATE`) would need
a branch, and the state cannot be proven: a byte-bound LF file later rewritten
as CRLF yields the same digest relation; (b) read a text-only digest as
`current` for a grace period — rejected: that keeps the defect alive.

**Tradeoff:** an old binding over CRLF bytes refuses where it used to pass. It
fails closed, names its cause and names one command to recover. The key is
called legacy-compatible, never proven legacy, and its wording says "or".

### D4 — No scheme version, no migration

**Choice:** the header grammar and `_AUTHORIZATION_BINDING_KEYS` stay frozen;
nothing is stamped with a scheme version and nothing committed is rewritten.

**Why it holds:** for LF lines in valid UTF-8 the byte digest equals the text
digest, so those records hold unchanged. Records over other bytes read `stale`
with the cause named: `position` and `admit` re-bind, a token minted over the
text refuses `GATE_AUTHORIZATION_STALE`, and `offer` mints a fresh one.

**Alternative:** a `scheme=` header field — rejected: the header's strict
grammar refuses unknown fields (`POSITION_BLOCK_MALFORMED`), so every existing
reader would break to carry a fact the digest comparison already settles.

### D5 — Zero bytes is an identity

`_bound_to` reads `unknown` only for an unnamed revision or an absent file
(`source is None`). A revision truncated after binding reads `stale`; a
binding to an empty file reads `current`.

### D6 — The spec exception lives in this change

The canonical requirement says "no sanctioned delta". The delta spec here
sanctions exactly D1 and D5, keeps every sealed digest, and keeps every wire
shape but D3's one additive key, `textOnlyMatch`; the canonical file moves
only when this change is archived.

## Testing Strategy

| Layer | What | Where |
|---|---|---|
| CLI boundary | distinct bytes, persisted bytes, legacy compatibility, zero bytes | `tests/test_implementation_revision_identity.py` |
| Reader | text equals `read_text` across chunk boundaries, BOM, lone CR, invalid bytes; identity equals `sha256(bytes)` | same file, `RevisionTextTests` |
| Both document positions | experimental host, `experiments` (index 0) and `proposal` (index 1) | same file, `ExperimentalHostIdentityTests` |
| Gate | full refusal envelope, old token refuses, fresh token gates | `tests/test_proposal_implementation.py` |
| Close | both refusal branches (the text-only cause reached by line endings and by an undecodable byte), `position` as the resolution, then a close that closes | same file, `CloseCommandTests` |
| Second-document ruling | stored digest, text-only detail | `tests/test_implementation_pair.py` |
| Regression | both seal comparators, token re-derivation, domain lock | existing suites, no golden recaptured |

## Risks

- `textOnlyMatch` names a cause it cannot prove: a binding taken over text, or
  a file whose bytes changed since in a way its decoded text does not show
  (line endings, or a byte that does not decode where the file held a literal
  U+FFFD). Both need the same re-binding, so the diagnostics name both.
- A future refactor that strips or slices before hashing silently falls back
  to the text digest; the boundary tests are the guard.

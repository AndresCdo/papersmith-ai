# Delta for implementation-document-binding

## MODIFIED Requirements

### Requirement: Every Scalar Revision Binding Is Byte-Identical Under One Document

Every site presently reading or writing a scalar `revision`/`revisionSha256`
(the `revisionSha256` sites, the `revision_source(args.revision)` call
sites, `module["stale"]`, `admissibility_record`, `position_state`'s
`boundTo`) MUST produce output byte-identical to its pre-cut behavior when
`len(documents) == 1`, with exactly two sanctioned deltas, both from
*A Revision's Identity Is The SHA-256 Of Its Bytes*: the digest a
`revisionSha256` site computes is the SHA-256 of the revision file's bytes,
and a revision file of zero bytes has an identity, so `boundTo` resolves it
instead of reading `unknown`. No wire shape changes — header grammar, record
keys, ledger event fields, `_AUTHORIZATION_BINDING_KEYS` — but one additive
key: where the first delta turns a binding `stale` because its stored digest
names the decoded text, `position_state` adds `textOnlyMatch` naming those
documents, and the key is absent everywhere else. For a
revision of LF lines in valid UTF-8 the byte digest equals the pre-cut digest,
so every such output stays byte-identical, sealed corpus included.
(Previously: this capability introduced no sanctioned delta at any of these
sites.)

#### Scenario: The existing sealed corpus is unaffected
- GIVEN the existing sealed single-document corpus
- WHEN the seal is re-captured after this capability lands
- THEN every digest is byte-identical to its pre-cut golden

#### Scenario: A committed single-document token keeps its golden digest
- GIVEN the committed single-document binding fixture and its golden digest
- WHEN the gate authorization token is re-derived after this change lands
- THEN the recomputed digest equals the golden, byte-identical

## ADDED Requirements

### Requirement: A Revision's Identity Is The SHA-256 Of Its Bytes

Every `revisionSha256` the engine writes or compares — the position header,
`admissibility.json` at every document index, and the `authorization`, `gate`
and `close` ledger events — MUST be the SHA-256 of the revision file's bytes
as read from the working tree, taken from the same read that yields the text
the parsers see. That text MUST stay exactly what
`Path.read_text(encoding="utf-8", errors="replace")` yields. A stored digest
that equals the digest of the decoded text but not of the bytes MUST read
`stale`, and the reader MUST name that cause: `position_state` lists the
documents in `textOnlyMatch` (present only when not empty), and
`admissibility_record`'s detail and the gate's and close's `POSITION_STALE`
refusals say the digest names the decoded text, not the bytes. No committed
record is edited, re-digested or migrated: a stale binding is re-bound only by
the operator running `position`, `admit` or `offer`.

#### Scenario: Distinct bytes get distinct identities
- GIVEN revision files that decode to one text — LF, CRLF and lone-CR line
  endings, or two different undecodable bytes
- WHEN `position`, `admit` and `admit --no-findings` bind each one
- THEN each stored identity equals the SHA-256 of that file's bytes, and no
  two files share one

#### Scenario: A binding is checked against the persisted bytes
- GIVEN a position and a ruling bound to a published revision with CRLF lines
- WHEN the file is rewritten with LF lines and the same decoded text
- THEN `verify` reads the position `stale` and the ruling `stale`

#### Scenario: A pre-existing LF record holds unchanged
- GIVEN a position header and a ruling storing the digest of the decoded text
  of a revision with LF lines in valid UTF-8
- WHEN `verify` reads them after this change lands
- THEN the position's `boundTo` is `current`, the ruling `present`, and no
  `textOnlyMatch` key appears

#### Scenario: A text-only record refuses and names its cause
- GIVEN a position header and a ruling storing the digest of the decoded text
  of a revision with CRLF lines
- WHEN `verify` reads them
- THEN the position is `stale` with `textOnlyMatch` naming the document, and
  the ruling is `stale` with a detail naming the decoded text and `admit`
- AND after `position` and `admit` run again, both hold

#### Scenario: A launch token minted over the text needs a fresh offer
- GIVEN a launch authorization minted while the revision's bytes equal its
  text's encoding, and the revision then rewritten with CRLF lines
- WHEN `gate` runs with that token
- THEN it refuses `POSITION_STALE` naming the cause, `position` and `offer`,
  with a `position` command as its structured resolution
- AND after `position`, the old token refuses `GATE_AUTHORIZATION_STALE`
  while a token freshly minted by `offer` gates

#### Scenario: Close names why its position is stale
- GIVEN a position bound while the revision's bytes equal its text's
  encoding, and the revision then rewritten as other bytes of the same text:
  CRLF lines, or an undecodable byte where it held a literal U+FFFD
- WHEN `close` runs
- THEN it refuses `POSITION_STALE` naming the decoded-text cause, with a
  `position` command as its structured resolution
- AND a position bound to bytes that then changed keeps the moved-bytes
  sentence
- AND after `position` runs again, the same `close` closes

#### Scenario: Zero bytes is an identity
- GIVEN a position bound to a revision that is then truncated to zero bytes
- WHEN `verify` reads it
- THEN the position is `stale`
- AND a position bound to the empty file reads `current`

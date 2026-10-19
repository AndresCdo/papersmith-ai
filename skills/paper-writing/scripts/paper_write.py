"""paper_write: the `write` pipeline — readiness, gate, draft, evidence-
audit, contract-audit, `substitute --contract` — with exactly one bounded
re-draft, enforced through an on-disk attempt ledger rather than counted
in-process (`writing-orchestration` spec; `design.md`, Decision D7).

The CLI is a judge, never an invoker (`design.md`, Decision D2): `draft` and
`audit_account` below are JSON envelopes an agent already produced and
handed back through `--draft`/`--audit`. This module never drafts, never
audits, never spawns anything — it reconciles what it is given against
`main.tex` and either writes or refuses.

Public surface:

    BlockContract                    -> the pipeline's one immutable input shape
    read_envelope(path) -> dict      (raises EnvelopeUnreadable; the CLI names the code)
    write_block(paper_dir, contract, draft, audit_account) -> dict
        (raises DRAFT_UNREADABLE, AUDIT_ACCOUNT_UNREADABLE, GROUNDING_ACCOUNT_UNREADABLE,
         MODE_ABSENT, EVIDENCE_SET_REQUIRED, AUDIT_EXHAUSTED, AUDIT_FINDING_UNVERIFIED,
         plus every code `paper_bindings`/`paper_audit` themselves raise)
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_audit  # noqa: E402
import paper_bindings  # noqa: E402
import paper_block  # noqa: E402
import paper_evidence  # noqa: E402
import paper_vocabulary  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_core" / "implementation"))
from impl_refusals import Refused  # noqa: E402


@dataclass(frozen=True)
class BlockContract:
    """One block's real inputs, already resolved from `sections/*.md` and
    `paper/.paper-writing/evidence/`. Never touches disk itself — every
    field is a plain value a caller (the CLI, or a test fixture) hands in."""

    block_id: str
    contract_prose: str
    contract_source: str
    citations_regime: str
    mode: str | None
    requires_facts: tuple
    evidence_set: tuple = ()
    style_set: tuple = ()
    #: `transposition-fidelity` spec's own prerequisite plumbing (design.md
    #: Decision E). One entry per bound source section
    #: (`paper_source_span.resolve_bound_sections`'s own return shape:
    #: `{"fact", "lineage", "title", "path", "byte_start", "byte_end",
    #: "text"}`), already resolved from disk by the CLI -- this dataclass
    #: never touches disk itself. Defaulted, the same `produces_facts`/
    #: `source_bindings` precedent, so every construction site that
    #: predates this field stays green unchanged.
    source_sections: tuple = ()


#: Bytes one envelope file may hold. A drafted block and its accounts run to
#: kilobytes, so only a runaway answer reaches this (#71).
ENVELOPE_MAX_BYTES = 4 * 1024 * 1024
#: The verdict words `paper_audit.reconcile_verdicts` and
#: `paper_grounding.reconcile_support` decide on. Any other word would pass
#: as neither a finding nor a clearance, so the envelope check refuses it.
AUDIT_VERDICTS = ("fires", "clear", "undecidable")
GROUNDING_VERDICTS = ("supported", "unsupported", "undecidable")


def _json_type(value) -> str:
    """The JSON name of `value`'s type, for a refusal's detail."""
    if value is None:
        return "null"
    if isinstance(value, bool):  # before int: a Python bool is an int too
        return "a boolean"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "an array"
    if isinstance(value, dict):
        return "an object"
    return type(value).__name__


class EnvelopeUnreadable(Exception):
    """Why an envelope file holds no JSON object. The caller turns it into
    the refusal code of the envelope it was reading."""


def read_envelope(path: Path) -> dict:
    """The JSON object `path` holds, as an agent handed it back (#71).

    Bounded to `ENVELOPE_MAX_BYTES` and strict UTF-8. A Markdown code fence
    around the JSON is refused rather than stripped, so what `write` judges
    is exactly what was written: the agent is told to write the bare object.
    """
    try:
        with path.open("rb") as handle:
            raw = handle.read(ENVELOPE_MAX_BYTES + 1)
    except OSError as exc:
        raise EnvelopeUnreadable(f"{path}: {exc.strerror or exc}") from None
    if len(raw) > ENVELOPE_MAX_BYTES:
        raise EnvelopeUnreadable(f"{path}: more than {ENVELOPE_MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnvelopeUnreadable(f"{path}: not UTF-8 (byte {exc.start})") from None
    if text.lstrip().startswith("```"):
        raise EnvelopeUnreadable(
            f"{path}: a Markdown code fence wraps the JSON; write the bare object"
        )
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnvelopeUnreadable(
            f"{path}: invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from None
    except ValueError as exc:  # e.g. an integer past Python's digit limit
        raise EnvelopeUnreadable(f"{path}: invalid JSON: {exc}") from None
    except RecursionError:
        raise EnvelopeUnreadable(f"{path}: JSON nested too deeply") from None
    if not isinstance(value, dict):
        raise EnvelopeUnreadable(f"{path}: must be a JSON object, not {_json_type(value)}")
    return value


def _entries_problem(
    envelope: dict,
    key: str,
    required: tuple,
    optional: tuple = (),
    *,
    subject: str,
    verdicts: tuple = (),
) -> str | None:
    """Why `envelope[key]` is not an array of objects whose `required` fields
    are strings and whose `optional` fields, where present, are strings or
    null; None when it is.

    Each entry judges one `subject` (a sentence, a bullet), and the pipeline
    keeps the last entry per subject, so two entries for one subject that
    disagree would silently drop the first; that is refused, while an exact
    repeat changes nothing and is not. With `verdicts`, an entry's `verdict`
    must be one of them.
    """
    entries = envelope[key]
    if not isinstance(entries, list):
        return f"{key!r} must be an array, not {_json_type(entries)}"
    first_for: dict[str, int] = {}
    for index, entry in enumerate(entries):
        where = f"{key}[{index}]"
        if not isinstance(entry, dict):
            return f"{where} must be an object, not {_json_type(entry)}"
        for field in required:
            if field not in entry:
                return f"{where} has no {field!r}"
            if not isinstance(entry[field], str):
                return f"{where}[{field!r}] must be a string, not {_json_type(entry[field])}"
        for field in optional:
            value = entry.get(field)
            if value is not None and not isinstance(value, str):
                return f"{where}[{field!r}] must be a string or null, not {_json_type(value)}"
        if verdicts and entry["verdict"] not in verdicts:
            return f"{where}['verdict'] is {entry['verdict']!r}, not one of {', '.join(verdicts)}"
        earlier = first_for.setdefault(entry[subject], index)
        if entries[earlier] != entry:
            return f"{key}[{earlier}] and {where} disagree about one {subject}: {entry[subject]!r}"
    return None


def draft_problem(draft) -> str | None:
    """Why `draft` is not `{"latex": str, "bindings": [{"sentence": str,
    "binding": str}, ...]}`, the redactor's envelope, with one binding per
    sentence, each `evidence:<id>`, `fact:<id>` or `structural`; None when
    it is. Other keys are ignored."""
    if not isinstance(draft, dict):
        return f"the draft must be a JSON object, not {_json_type(draft)}"
    if "latex" not in draft:
        return "the draft has no 'latex'"
    if not isinstance(draft["latex"], str):
        return f"'latex' must be a string, not {_json_type(draft['latex'])}"
    if "bindings" not in draft:
        return "the draft has no 'bindings'"
    problem = _entries_problem(draft, "bindings", ("sentence", "binding"), subject="sentence")
    if problem:
        return problem
    for index, entry in enumerate(draft["bindings"]):
        try:
            paper_bindings.parse_binding(entry["binding"])
        except ValueError as exc:
            return f"bindings[{index}]['binding']: {exc}"
    return None


def audit_account_problem(account) -> str | None:
    """Why `account` is not `{"verdicts": [{"bullet": str, "verdict": str,
    "span": str | null}, ...]}`, the contract-auditor's envelope, with one
    verdict per bullet from `AUDIT_VERDICTS`; None when it is. `span` may be
    absent."""
    if not isinstance(account, dict):
        return f"the audit account must be a JSON object, not {_json_type(account)}"
    if "verdicts" not in account:
        return "the audit account has no 'verdicts'"
    return _entries_problem(
        account,
        "verdicts",
        ("bullet", "verdict"),
        ("span",),
        subject="bullet",
        verdicts=AUDIT_VERDICTS,
    )


def grounding_account_problem(account) -> str | None:
    """Why `account` is not `{"support": [{"sentence": str, "verdict": str,
    "fact": str | null, "span": str | null}, ...]}`, the section-grounding
    auditor's envelope, with one judgment per sentence from
    `GROUNDING_VERDICTS`; None when it is. An absent `support` still reads
    as no entries at all, as `paper_grounding` has always read it."""
    if not isinstance(account, dict):
        return f"the grounding account must be a JSON object, not {_json_type(account)}"
    if "support" not in account:
        return None
    return _entries_problem(
        account,
        "support",
        ("sentence", "verdict"),
        ("fact", "span"),
        subject="sentence",
        verdicts=GROUNDING_VERDICTS,
    )


def _attempt_key(contract: BlockContract) -> str:
    payload = json.dumps(
        {
            "contract": contract.contract_prose,
            "evidence": [dict(entry) for entry in contract.evidence_set],
            "mode": contract.mode,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ledger_path(paper_dir: Path, block_id: str) -> Path:
    return paper_dir / ".paper-writing" / "attempts" / f"{block_id}.json"


def _read_ledger(paper_dir: Path, block_id: str) -> dict | None:
    path = _ledger_path(paper_dir, block_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_ledger(paper_dir: Path, block_id: str, entry: dict) -> None:
    path = _ledger_path(paper_dir, block_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry), encoding="utf-8")


def _stage_readiness(contract: BlockContract) -> None:
    """`readiness`/`gate`, combined: the pipeline's own preconditions before
    any draft is even read. Refuses `MODE_ABSENT` (`section-contract` spec,
    `Requirement: Headers Written Before mode Existed`) when no mode
    resolved at either level — `write` never assumes a default. Refuses
    `EVIDENCE_SET_REQUIRED` (Ruling 3: a block whose `citations` regime is
    not `none` and carries no evidence set is refused, never reported
    `unvalidated` — every claim it would make is unbound, not merely
    unchecked) when `citations_regime != "none"` and `evidence_set` is
    empty. The pre-existing facts/declarations writability gate
    (`paper_readiness.compute_block_readiness`) is a separately-wired
    capability this pipeline does not duplicate; a caller (the CLI) is
    expected to have already confirmed the block is writable before
    invoking `write_block` at all.
    """
    if contract.mode is None:
        raise Refused(
            "MODE_ABSENT",
            f"{contract.block_id}: no mode resolves at section or block level; "
            "write refuses rather than assuming one",
        )
    paper_vocabulary.validate_mode(contract.mode)
    if contract.citations_regime != "none" and not contract.evidence_set:
        raise Refused(
            "EVIDENCE_SET_REQUIRED",
            f"{contract.block_id}: citations={contract.citations_regime!r} requires "
            "a non-empty evidence set; every claim this block would make is unbound",
        )


def _stage_evidence_audit(contract: BlockContract, draft: dict) -> list:
    bindings = paper_bindings.reconcile(draft["latex"], draft["bindings"])
    evidence_ids = {entry["id"] for entry in contract.evidence_set}
    facts = set(contract.requires_facts)
    paper_bindings.resolve_bindings(bindings, evidence_ids, facts)
    paper_bindings.type_structural(bindings, contract.contract_prose)
    evidence_by_id = {entry["id"]: entry for entry in contract.evidence_set}
    paper_bindings.check_mode_admissibility(bindings, contract.mode, evidence_by_id)
    return bindings


def _stage_contract_audit(contract: BlockContract, draft: dict, audit_account: dict) -> dict:
    return paper_audit.audit(
        contract.contract_prose, draft["latex"], audit_account["verdicts"],
        source_name=contract.contract_source,
    )


def write_block(
    paper_dir: Path, contract: BlockContract, draft: dict, audit_account: dict,
    *, grounding_account: dict | None = None,
) -> dict:
    """One `write` invocation for one block (`writing-orchestration` spec,
    `Requirement: Pipeline Stage Order`). Stages run in order: readiness,
    gate (both `_stage_readiness` above), draft (`draft`/`audit_account`
    already handed in), evidence-audit, contract-audit, `substitute
    --contract`. A stage never starts until every earlier one clears —
    `_stage_evidence_audit` running before `_stage_contract_audit` is what
    makes "a failing evidence-audit stops the pipeline before contract-audit
    runs" true by construction, not by a check somewhere else.

    Contract-audit firing does not itself refuse: it records the attempt in
    the on-disk ledger and reports the fired bullets as feedback for exactly
    one re-draft (`Requirement: One Bounded Re-Draft`). A second consecutive
    attempt under the same `(contract, evidence, mode)` key that still fires
    refuses `AUDIT_EXHAUSTED` naming every bullet that fired on that attempt
    (`Requirement: Exhaustion Leaves The Block Unwritten`) — `substitute` is
    never reached on that path, so `main.tex` stays byte-identical to its
    pre-`write` state.

    A `fires` claim reconciliation could not check (no span, or one not
    byte-present in the draft) neither passes nor spends the re-draft
    (#72): with nothing verified firing, `write` refuses
    `AUDIT_FINDING_UNVERIFIED` naming it, before `substitute` and without
    touching the ledger, so the same draft can be audited again.

    The envelopes are checked before any stage reads them (#71): a draft or
    account that is not the shape its agent is told to return refuses
    `DRAFT_UNREADABLE`, `AUDIT_ACCOUNT_UNREADABLE` or
    `GROUNDING_ACCOUNT_UNREADABLE` saying what is wrong, never a traceback,
    and spends no re-draft.
    """
    problem = draft_problem(draft)
    if problem:
        raise Refused("DRAFT_UNREADABLE", f"{contract.block_id}: {problem}")
    problem = audit_account_problem(audit_account)
    if problem:
        raise Refused("AUDIT_ACCOUNT_UNREADABLE", f"{contract.block_id}: {problem}")
    if grounding_account is not None:
        problem = grounding_account_problem(grounding_account)
        if problem:
            raise Refused("GROUNDING_ACCOUNT_UNREADABLE", f"{contract.block_id}: {problem}")
    _stage_readiness(contract)
    bindings = _stage_evidence_audit(contract, draft)

    key = _attempt_key(contract)
    ledger = _read_ledger(paper_dir, contract.block_id)
    attempt = 1
    if ledger is not None and ledger.get("key") == key:
        attempt = ledger.get("attempts", 0) + 1

    audit_result = _stage_contract_audit(contract, draft, audit_account)

    if audit_result["blocks"]:
        fired = [{"bullet": entry["bullet"], "span": entry["span"]} for entry in audit_result["fired"]]
        if attempt >= 2:
            raise Refused(
                "AUDIT_EXHAUSTED",
                f"{contract.block_id}: contract-audit still fires on attempt {attempt}: "
                f"{[entry['bullet'] for entry in fired]}",
            )
        _write_ledger(paper_dir, contract.block_id, {"key": key, "attempts": attempt, "fired": fired})
        return {
            "status": "audit-fired",
            "block": contract.block_id,
            "attempt": attempt,
            "fired": fired,
            "verdicts": audit_result["verdicts"],
        }

    if audit_result["unverified"]:
        raise Refused(
            "AUDIT_FINDING_UNVERIFIED",
            f"{contract.block_id}: contract-audit says "
            f"{[entry['bullet'] for entry in audit_result['unverified']]} fire, but "
            "quotes no span found byte for byte in this draft; audit the same draft "
            "again rather than write past a finding nobody can check",
        )

    if contract.style_set:
        # Local import, not module-level: `paper_write.py` is a Work Unit 1
        # file and must stay importable (and `write_block` callable with an
        # empty style set, the only value WU1 itself ever populates) even
        # when `paper_leak.py` is absent -- WU2's own rollback boundary
        # ("Unit 1 stands alone with an empty style channel"). Only a
        # non-empty `style_set` -- which only the WU2-wired CLI path
        # (`cmd_write`'s `--style`) ever produces -- reaches this branch.
        # `design.md`'s own Data Flow: "paper_leak.tripwire (styled only)
        # -> paper_write ledger" runs here, after contract-audit clears and
        # before `substitute`, independent of the A/B/S register/overlap
        # proof (`paper_leak.register_distance_holds`/
        # `relative_overlap_holds`), which is a Unit-level proof of the
        # mechanism itself (`design.md`, Testing Strategy table), not a
        # per-write runtime check -- the same role `_run_against_mutant`
        # plays for the byte-identity guards, exercised by
        # `StyleLeakDetectionTests`, never by a real `write` call.
        import paper_leak  # noqa: PLC0415
        paper_leak.check_tripwire(draft["latex"], contract.style_set)

    # Ruling 2's real caller: every real `write` that reaches this point
    # (contract-audit cleared) reports the style channel's own status in
    # the returned envelope, never only through a standalone unit test.
    # `register_result`/`overlap_result` stay `None` here -- that pair is
    # the proof harness's own measurement over recorded A/B/S transcripts
    # (`design.md`, Decision D6; `StyleLeakDetectionTests`), never computed
    # for a single real `write` call, which only ever runs the tripwire
    # above. An empty `style_set` still reaches this call, which is what
    # makes "unmeasured" a real reported status rather than an omitted key.
    style_report = style_channel_report(contract.style_set, None, None)

    # `transposition-fidelity` spec, `Requirement: The Guard Fires Inside
    # write, Before Substitution, Never Only From A Read-Only Verb` +
    # `Requirement: Only A Transposition-Mode Block Is Checked, Mode
    # Derived From The Contract On Disk, Never Listed` (design.md, Decisions
    # C/D; WU2). Runs AFTER the style tripwire above and BEFORE
    # `substitute`, so a draft failing both checks always names
    # `STYLE_OVERLAP` deterministically (design.md, Data Flow). Guarded on
    # `contract.mode == MODE_TRANSPOSITION`, the SAME derivation
    # `MODE_ABSENT` rests on -- no block id, no section title, no list.
    # Lazily imported, exactly as the style tripwire above, so
    # `paper_write.py` stays importable without `paper_leak.py` present.
    # `block_id` is passed straight through rather than caught and
    # re-raised here: a caller-side `except Refused as exc: raise
    # Refused(exc.code, ...)` would replace the refusal's own literal CODE
    # argument with a runtime value, which is exactly the shape this
    # repository's roster derivation (`reachable_paper_refusal_codes`) reads
    # statically and refuses to silently widen past -- measured directly
    # against this stage during apply.
    source_sections_report = None
    if contract.mode == paper_vocabulary.MODE_TRANSPOSITION and contract.source_sections:
        import paper_leak  # noqa: PLC0415
        source_sections_report = paper_leak.check_source_section_verbatim(
            draft["latex"], contract.contract_prose, contract.source_sections,
            block_id=contract.block_id,
        )

    # `transposition-fidelity` spec, `Requirement: A Block With No Measured
    # Bound Section Reports Unmeasured, Never Refused` (design.md Decision
    # E). `source_fidelity_report` adds no comparison and no refusal of its
    # own -- that is `check_source_section_verbatim`'s job, above -- this
    # call only shapes the envelope, mirroring `style_channel_report`'s
    # shipped shape rather than inventing a second reporting convention.
    source_fidelity = source_fidelity_report(contract.source_sections, source_sections_report)

    # `transposition-grounding` spec, `Requirement: The Subject Set Is An
    # Intersection...` + `Requirement: The Account Is Reconciled...` +
    # `Requirement: The Guard Fires After The Verbatim Check And Before
    # Substitution` (design.md D1/D3/D6/D8). Same `contract.mode ==
    # MODE_TRANSPOSITION` derivation `MODE_ABSENT` and the verbatim check
    # above both already rest on -- no block id, no list. Lazily imported,
    # exactly as `paper_leak` above, so `paper_write.py` stays importable
    # without `paper_grounding.py` present. Runs AFTER
    # `check_source_section_verbatim` clears and BEFORE `substitute`, so a
    # draft failing both checks always names `SOURCE_SECTION_VERBATIM`
    # first -- copying is decided before meaning (D6). An `argument`-mode
    # block, or a block with no `source_sections` at all, reports the
    # interim `unmeasured`/0 envelope WITHOUT ever importing
    # `paper_grounding` (`Scenario: An argument-mode block has no
    # subjects").
    source_grounding = {"status": "unmeasured", "subjects": 0}
    if contract.source_sections and contract.mode == paper_vocabulary.MODE_TRANSPOSITION:
        import paper_grounding  # noqa: PLC0415
        subjects = paper_grounding.subjects_for(bindings, contract.source_sections)
        reconciled = paper_grounding.reconcile_support(
            subjects, grounding_account, contract.source_sections, block_id=contract.block_id,
        )
        source_grounding = paper_grounding.source_grounding_report(subjects, reconciled)

    result = paper_block.substitute(paper_dir, contract.block_id, new_body=draft["latex"].encode("utf-8"))

    # `the-block-asserts-only-what-its-section-carries` skill's own
    # falsifier ("over ten or more recorded real `write` runs...") needs a
    # place to accumulate real runs against. Two constraints, both load-
    # bearing:
    #
    # 1. AFTER substitute, never before. The falsifier counts blocks that
    #    REACHED `written`. Appending before this point and then having
    #    `substitute` raise would record a run that never happened.
    # 2. Every `written` run, not only a measured one. This call sits here
    #    -- after every grounding branch above, unconditionally -- rather
    #    than inside the `contract.mode == MODE_TRANSPOSITION` branch,
    #    because an `argument`-mode block (or one with no `source_sections`)
    #    still leaves `source_grounding` at the interim `{"status":
    #    "unmeasured", "subjects": 0}` envelope and is still a real write
    #    run that belongs in the "ten or more" denominator the falsifier
    #    counts against.
    paper_evidence.append_grounding_run(paper_dir, contract.block_id, source_grounding)

    return {
        "status": "written",
        "block": contract.block_id,
        "verdicts": audit_result["verdicts"],
        "styleChannel": style_report,
        "sourceFidelity": source_fidelity,
        "sourceGrounding": source_grounding,
        **result,
    }


def source_fidelity_report(source_sections: tuple, measured: dict | None = None) -> dict:
    """`transposition-fidelity` spec, `Requirement: A Block With No
    Measured Bound Section Reports Unmeasured, Never Refused` (design.md
    Decision E) + `Requirement: The Floor And Threshold Are Reported, Never
    Inferred Silently` (Decision C). Mirrors `style_channel_report`'s own
    shape: no bound section resolved for this block -> `unmeasured`, never
    a silent pass and never inferred only from the absence of a refusal.

    `measured` is `check_source_section_verbatim`'s own return value
    (`{"sections": [...]}`) when the caller ran that check -- `None` when
    `source_sections` is empty (nothing to check) or when the caller never
    ran the check at all (WU1's own rollback boundary: a caller construct
    predating WU2 that still passes only `source_sections`). This function
    adds no comparison and no refusal of its own, only the envelope shape.
    """
    if not source_sections:
        return {"status": "unmeasured"}
    return {"status": "measured", "sections": measured["sections"] if measured is not None else []}


def style_channel_report(recorded_samples: list, register_result: dict | None, overlap_result: dict | None) -> dict:
    """Ruling 2 (orchestrator, this change): an empty `R` — every
    style-reference resolved `noEquivalent` — means register distance
    measures nothing and overlap is vacuously satisfied, so the style
    channel reports `unmeasured` rather than a silent pass. Joins
    `unprovenanced`/`unclassified`/`ambiguous` in this skill's own
    uncertainty vocabulary (`design.md`, Decision D8's sibling for the style
    channel)."""
    if not recorded_samples:
        return {"status": "unmeasured"}
    return {"status": "measured", "register": register_result, "overlap": overlap_result}

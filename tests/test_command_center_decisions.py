"""The read-only decisions timeline: bounded readers, normalisation and merge.

Readers are called directly; routes are covered in the second half of this
module. Fixture workspaces mirror the real on-disk layouts:

* declarations region in ``paper/main.tex`` (``paper_region`` grammar),
* ``.proposal-deliberation|.experimental-deliberation/receipts/<file>.json`` and
  ``.../lifecycle/v1/transitions/<id>.json``,
* ``implementations/<repo>/<Name>/.remote-execution/ledger.jsonl``
  (``implementation_engine.py`` builds ``target / name / '.remote-execution'``).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from skills._core.command_center import decisions

LEDGER_REL = "implementations/repo/Impl/.remote-execution/ledger.jsonl"


def _region(body: dict, kind: str = "declarations") -> str:
    lines = json.dumps(body, indent=2, sort_keys=True).splitlines()
    prefixed = "\n".join("%% " + line for line in lines)
    return (f"%% paper-writing {kind} begin sha256={'0' * 64}\n{prefixed}\n"
            f"%% paper-writing {kind} end\n")


def _decl_body(*records: dict) -> dict:
    return {"generation": len(records), "records": list(records)}


def _declaration(id_: str, value: str, recorded: str = "2026-03-01T10:00:00Z") -> dict:
    return {"kind": "declaration", "id": id_, "value": value, "fixed": True,
            "recorded": recorded, "generation": 1}


def _fact(id_: str, resolution: str, recorded: str = "2026-03-02T10:00:00Z") -> dict:
    return {"kind": "fact", "id": id_, "resolution": resolution, "fixed": True,
            "recorded": recorded, "generation": 2}


def _declined(id_: str, reason: str, recorded: str = "2026-03-03T10:00:00Z") -> dict:
    return {"kind": "fact", "id": id_, "reason": reason, "fixed": True, "declined": True,
            "condition": {"path": "x"}, "recorded": recorded, "generation": 3}


class _Workspace(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    @staticmethod
    def write(root: Path, rel: str, data: str | bytes) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return path

    def write_main(self, root: Path, body: dict | None, extra: str = "") -> None:
        text = "\\documentclass{article}\n" + extra
        if body is not None:
            text += _region(body)
        self.write(root, "paper/main.tex", text)

    def write_json(self, root: Path, rel: str, value: object) -> None:
        self.write(root, rel, json.dumps(value))

    def write_ledger(self, root: Path, events: list[dict], rel: str = LEDGER_REL) -> None:
        self.write(root, rel, "\n".join(json.dumps(e) for e in events) + "\n")

    @staticmethod
    def snapshot(root: Path) -> dict:
        out = {}
        for path in sorted(root.rglob("*")):
            info = path.lstat()
            out[str(path.relative_to(root))] = (info.st_size, info.st_mtime_ns)
        return out


class DeclarationsTests(_Workspace):
    def read(self, root: Path) -> dict:
        return decisions.read_declarations(root)

    def test_absent_without_main_tex(self) -> None:
        result = self.read(self.new_workspace())

        assert result["status"] == "absent" and result["events"] == []

    def test_absent_without_region(self) -> None:
        root = self.new_workspace()
        self.write_main(root, None)

        assert self.read(root)["status"] == "absent"

    def test_declaration_fact_and_declined_events(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(
            _declaration("dataset", "ImageNet"),
            _fact("seeds", "5 seeds"),
            _declined("novelty", "no baseline exists"),
        ))
        result = self.read(root)
        by_ref = {e["ref"]: e for e in result["events"]}

        assert result["status"] == "ok" and len(result["events"]) == 3
        decl = by_ref["paper/main.tex#dataset"]
        assert decl["summary"] == "Declared dataset" and decl["kind"] == "declaration"
        assert decl["ts"] == "2026-03-01T10:00:00Z" and decl["source"] == "declarations"
        assert by_ref["paper/main.tex#seeds"]["summary"] == "Resolved fact seeds"
        declined = by_ref["paper/main.tex#novelty"]
        assert declined["summary"] == "Declined fact novelty: no baseline exists"
        assert declined["kind"] == "fact_declined"

    def test_every_event_notes_that_only_the_current_state_is_stored(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(_declaration("a", "v")))
        note = self.read(root)["events"][0]["note"]

        assert "current" in note and "not recoverable" in note

    def test_unknown_record_kind_and_non_dict_records_are_tolerated(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(
            {"kind": "binding", "id": "b1", "recorded": "2026-03-01T00:00:00Z"}, "junk", 3))
        events = self.read(root)["events"]

        assert [e["summary"] for e in events] == ["Recorded binding b1"]

    def test_digest_is_not_verified(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(_declaration("a", "v")))

        assert self.read(root)["status"] == "ok"  # sha256 is all zeros in the fixture

    def test_corrupt_region_is_unreadable_not_an_exception(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/main.tex",
                   f"%% paper-writing declarations begin sha256={'0' * 64}\n%% {{not json\n"
                   "%% paper-writing declarations end\n")
        result = self.read(root)

        assert result["status"] == "unreadable" and result["events"] == []
        assert result["detail"]

    def test_unterminated_region_is_unreadable(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/main.tex",
                   f"%% paper-writing declarations begin sha256={'0' * 64}\n%% {{}}\n")

        assert self.read(root)["status"] == "unreadable"

    def test_over_the_cap_is_too_large_and_never_read(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/main.tex", b"x" * (decisions.MAIN_TEX_MAX_BYTES + 1))
        with mock.patch.object(decisions, "_read_bytes", side_effect=AssertionError("read")):
            result = self.read(root)

        assert result["status"] == "too_large"

    def test_symlink_escaping_the_workspace_is_unreadable(self) -> None:
        root = self.new_workspace()
        outside = self.new_workspace()
        self.write_main(outside, _decl_body(_declaration("secret", "leak")))
        (root / "paper").mkdir()
        (root / "paper" / "main.tex").symlink_to(outside / "paper" / "main.tex")
        result = self.read(root)

        assert result["status"] == "unreadable" and result["events"] == []

    def test_directory_named_main_tex_is_unreadable(self) -> None:
        root = self.new_workspace()
        (root / "paper" / "main.tex").mkdir(parents=True)

        assert self.read(root)["status"] == "unreadable"

    def test_provenance_region_is_ignored(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/main.tex", _region({"x": 1}, "provenance"))

        assert self.read(root)["status"] == "absent"


def _receipt(source: str = "r1", target: str = "r2", intent: str = "EDIT", patches: int = 2) -> dict:
    return {"sourceRevision": source, "targetRevision": target, "sourceFilename": "a.md",
            "targetFilename": "b.md", "intent": intent, "operation": intent,
            "documentShaBefore": "a" * 64, "documentShaAfter": "b" * 64,
            "resolvedEntryIds": ["e1"], "patchIds": ["p1", "p2"], "patchCount": patches}


def _transition(seq: int, operation: str, outcome: str, committed_at: str | None) -> dict:
    data = {"schemaVersion": "lifecycle-v1", "transitionId": f"t{seq}", "sequence": seq,
            "operation": operation, "outcome": outcome, "requestId": f"q{seq}"}
    if committed_at is not None:
        data["committedAt"] = committed_at
    return data


SIDE = ".proposal-deliberation"
TRANSITIONS = "lifecycle/v1/transitions"


class DeliberationTests(_Workspace):
    def read(self, root: Path, side: str = SIDE) -> dict:
        return decisions.read_deliberation(root, side)

    def test_absent_sidecar(self) -> None:
        result = self.read(self.new_workspace())

        assert result["status"] == "absent" and result["events"] == []

    def test_receipt_has_no_timestamp_and_is_unverified(self) -> None:
        root = self.new_workspace()
        self.write_json(root, f"{SIDE}/receipts/b.md.json", _receipt())
        result = self.read(root)
        event = result["events"][0]

        assert result["status"] == "ok"
        assert event["ts"] is None and event["verified"] is False
        assert event["source"] == "proposal"
        assert event["kind"] == "revision_receipt"
        assert event["summary"] == "Revision r1 -> r2 (EDIT), 2 patches"
        assert event["ref"] == f"{SIDE}/receipts/b.md.json"

    def test_receipt_never_uses_file_mtime(self) -> None:
        root = self.new_workspace()
        path = self.write(root, f"{SIDE}/receipts/b.md.json", json.dumps(_receipt()))
        os.utime(path, (1_700_000_000, 1_700_000_000))

        assert self.read(root)["events"][0]["ts"] is None

    def test_transition_uses_committed_at(self) -> None:
        root = self.new_workspace()
        self.write_json(root, f"{SIDE}/{TRANSITIONS}/t1.json",
                        _transition(1, "CREATE_SUCCESSOR", "COMMITTED", "2026-04-01T09:00:00Z"))
        event = self.read(root)["events"][0]

        assert event["ts"] == "2026-04-01T09:00:00Z" and event["verified"] is False
        assert event["kind"] == "lifecycle_transition"
        assert event["summary"] == "Committed create successor"

    def test_every_outcome_has_a_summary(self) -> None:
        expected = {
            "COMMITTED": "Committed register base",
            "ALREADY_COMMITTED": "Already committed register base",
            "REJECTED": "Rejected register base",
            "INCONSISTENT": "Inconsistent state after register base",
            "RECOVERY_REQUIRED": "Recovery required after register base",
        }
        root = self.new_workspace()
        for index, outcome in enumerate(expected, 1):
            self.write_json(root, f"{SIDE}/{TRANSITIONS}/t{index}.json",
                            _transition(index, "REGISTER_BASE", outcome, f"2026-04-0{index}T00:00:00Z"))
        summaries = {e["summary"] for e in self.read(root)["events"]}

        assert summaries == set(expected.values())
        assert set(expected) == set(decisions.OUTCOME_SUMMARIES)

    def test_unknown_outcome_and_operation_fall_back(self) -> None:
        root = self.new_workspace()
        self.write_json(root, f"{SIDE}/{TRANSITIONS}/t1.json",
                        _transition(1, "", "SOMETHING_NEW", "2026-04-01T00:00:00Z"))
        self.write_json(root, f"{SIDE}/{TRANSITIONS}/t2.json", {"sequence": 2})

        summaries = sorted(e["summary"] for e in self.read(root)["events"])
        assert summaries == ["Transition 1: unknown outcome (SOMETHING_NEW)",
                             "Transition 2: unknown outcome"]

    def test_experiment_sidecar_has_its_own_source_name(self) -> None:
        root = self.new_workspace()
        self.write_json(root, ".experimental-deliberation/receipts/x.json", _receipt())
        event = self.read(root, ".experimental-deliberation")["events"][0]

        assert event["source"] == "experiment"

    def test_transition_without_committed_at_has_null_ts(self) -> None:
        root = self.new_workspace()
        self.write_json(root, f"{SIDE}/{TRANSITIONS}/t1.json", _transition(1, "X", "REJECTED", None))

        assert self.read(root)["events"][0]["ts"] is None

    def test_corrupt_files_are_skipped_and_counted(self) -> None:
        root = self.new_workspace()
        self.write_json(root, f"{SIDE}/receipts/ok.json", _receipt())
        self.write(root, f"{SIDE}/receipts/bad.json", "{nope")
        self.write(root, f"{SIDE}/receipts/list.json", "[1, 2]")
        result = self.read(root)

        assert result["status"] == "ok" and len(result["events"]) == 1
        assert "2 unreadable" in result["detail"]

    def test_all_corrupt_is_unreadable(self) -> None:
        root = self.new_workspace()
        self.write(root, f"{SIDE}/receipts/bad.json", "{nope")
        result = self.read(root)

        assert result["status"] == "unreadable" and result["events"] == []

    def test_oversized_file_is_skipped_unread(self) -> None:
        root = self.new_workspace()
        self.write(root, f"{SIDE}/receipts/big.json", b"x" * (decisions.ITEM_MAX_BYTES + 1))
        self.write_json(root, f"{SIDE}/receipts/ok.json", _receipt())
        result = self.read(root)

        assert len(result["events"]) == 1 and "1 too large" in result["detail"]

    def test_only_oversized_files_is_too_large(self) -> None:
        root = self.new_workspace()
        self.write(root, f"{SIDE}/receipts/big.json", b"x" * (decisions.ITEM_MAX_BYTES + 1))

        assert self.read(root)["status"] == "too_large"

    def test_file_count_cap(self) -> None:
        root = self.new_workspace()
        for index in range(decisions.MAX_ITEM_FILES + 5):
            self.write_json(root, f"{SIDE}/receipts/r{index:04d}.json", _receipt(f"a{index}"))
        result = self.read(root)

        assert result["status"] == "too_large"
        assert len(result["events"]) == decisions.MAX_ITEM_FILES
        assert "500" in result["detail"]

    def test_non_json_names_and_subdirectories_are_ignored(self) -> None:
        root = self.new_workspace()
        self.write(root, f"{SIDE}/receipts/notes.txt", "hi")
        (root / SIDE / "receipts" / "dir.json").mkdir()
        self.write_json(root, f"{SIDE}/receipts/ok.json", _receipt())

        assert len(self.read(root)["events"]) == 1

    def test_symlinked_file_escaping_the_workspace_is_skipped(self) -> None:
        root = self.new_workspace()
        outside = self.new_workspace()
        target = self.write(outside, "r.json", json.dumps(_receipt()))
        (root / SIDE / "receipts").mkdir(parents=True)
        (root / SIDE / "receipts" / "r.json").symlink_to(target)
        result = self.read(root)

        assert result["events"] == [] and result["status"] == "unreadable"

    def test_symlinked_sidecar_escaping_the_workspace_is_unreadable(self) -> None:
        root = self.new_workspace()
        outside = self.new_workspace()
        self.write_json(outside, "receipts/r.json", _receipt())
        (root / SIDE).symlink_to(outside)
        result = self.read(root)

        assert result["status"] == "unreadable" and result["events"] == []

    def test_sidecar_that_is_a_file_is_unreadable(self) -> None:
        root = self.new_workspace()
        self.write(root, SIDE, "not a directory")

        assert self.read(root)["status"] == "unreadable"


def _submitted(ts: str, entrypoint: str = "run.py", worker: str = "w1", sid: str = "s1") -> dict:
    return {"kind": "submitted", "ts": ts, "entrypoint": entrypoint, "worker": worker,
            "submissionId": sid, "sourceDigest": "d", "requestedCapacity": 1, "grantedCapacity": 1}


def _returned(ts: str, sid: str = "s1") -> dict:
    return {"kind": "returned", "ts": ts, "submissionId": sid, "artifactPath": "a",
            "observedConcurrency": 1}


def _errored(ts: str, reason: str = "boom", sid: str = "s1") -> dict:
    return {"kind": "errored", "ts": ts, "submissionId": sid, "reason": reason}


class LedgerTests(_Workspace):
    def read(self, root: Path) -> dict:
        return decisions.read_ledgers(root)

    def test_absent_without_implementations(self) -> None:
        result = self.read(self.new_workspace())

        assert result["status"] == "absent" and result["events"] == []

    def test_events_and_summaries(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [_submitted("2026-05-01T00:00:00Z"),
                                 _returned("2026-05-01T01:00:00Z"),
                                 _errored("2026-05-01T02:00:00Z", "out of memory", "s2")])
        events = {e["kind"]: e for e in self.read(root)["events"]}

        assert events["submitted"]["summary"] == "Submitted run.py to w1"
        assert events["returned"]["summary"] == "Returned s1"
        assert events["errored"]["summary"] == "Errored: out of memory"
        assert events["submitted"]["ts"] == "2026-05-01T00:00:00Z"
        assert events["submitted"]["source"] == "remote-execution"
        assert events["submitted"]["ref"] == f"{LEDGER_REL}#1"
        assert events["errored"]["ref"] == f"{LEDGER_REL}#3"

    def test_discovers_only_the_two_level_layout(self) -> None:
        root = self.new_workspace()
        good = _submitted("2026-05-01T00:00:00Z", sid="good")
        self.write_ledger(root, [good])
        self.write_ledger(root, [_submitted("2026-05-02T00:00:00Z", sid="shallow")],
                          "implementations/repo/.remote-execution/ledger.jsonl")
        self.write_ledger(root, [_submitted("2026-05-03T00:00:00Z", sid="deep")],
                          "implementations/repo/Impl/sub/.remote-execution/ledger.jsonl")
        self.write_ledger(root, [_submitted("2026-05-04T00:00:00Z", sid="exp")],
                          "experiments/repo/Impl/.remote-execution/ledger.jsonl")
        self.write_ledger(root, [_submitted("2026-05-05T00:00:00Z", sid="top")],
                          ".remote-execution/ledger.jsonl")
        result = self.read(root)

        assert [e["ref"].split("#")[0] for e in result["events"]] == [LEDGER_REL]
        assert len(result["events"]) == 1

    def test_malformed_lines_are_skipped_and_counted(self) -> None:
        root = self.new_workspace()
        lines = [json.dumps(_submitted("2026-05-01T00:00:00Z")), "{broken", "[1]",
                 json.dumps({"kind": "weird", "ts": "2026-05-01T00:00:00Z"}), "",
                 json.dumps(_returned("2026-05-01T01:00:00Z"))]
        self.write(root, LEDGER_REL, "\n".join(lines) + "\n")
        result = self.read(root)

        assert result["status"] == "ok" and len(result["events"]) == 2
        assert "3 malformed" in result["detail"]

    def test_line_cap(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [_returned("2026-05-01T00:00:00Z", f"s{i}")
                                 for i in range(decisions.MAX_LEDGER_LINES + 10)])
        result = self.read(root)

        assert len(result["events"]) == decisions.MAX_LEDGER_LINES
        assert "2000" in result["detail"]

    def test_file_cap(self) -> None:
        root = self.new_workspace()
        for index in range(decisions.MAX_LEDGER_FILES + 3):
            self.write_ledger(root, [_returned("2026-05-01T00:00:00Z", f"s{index}")],
                              f"implementations/repo/N{index:03d}/.remote-execution/ledger.jsonl")
        result = self.read(root)

        assert len(result["events"]) == decisions.MAX_LEDGER_FILES
        assert "20" in result["detail"]

    def test_oversized_ledger_is_skipped_unread(self) -> None:
        root = self.new_workspace()
        self.write(root, LEDGER_REL, b"x" * (decisions.LEDGER_MAX_BYTES + 1))
        result = self.read(root)

        assert result["status"] == "too_large" and result["events"] == []

    def test_corrupt_only_ledger_is_unreadable(self) -> None:
        root = self.new_workspace()
        self.write(root, LEDGER_REL, "{{{\n")
        result = self.read(root)

        assert result["status"] == "unreadable"

    def test_missing_ts_is_null(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [{"kind": "returned", "submissionId": "s"}])

        assert self.read(root)["events"][0]["ts"] is None

    def test_symlinked_ledger_escaping_the_workspace_is_skipped(self) -> None:
        root = self.new_workspace()
        outside = self.new_workspace()
        target = outside / "ledger.jsonl"
        target.write_text(json.dumps(_returned("2026-05-01T00:00:00Z")) + "\n")
        (root / "implementations/repo/Impl/.remote-execution").mkdir(parents=True)
        (root / LEDGER_REL).symlink_to(target)

        assert self.read(root)["events"] == []

    def test_symlinked_implementations_dir_escaping_is_not_followed(self) -> None:
        root = self.new_workspace()
        outside = self.new_workspace()
        self.write_ledger(outside, [_returned("2026-05-01T00:00:00Z")], "repo/Impl/.remote-execution/ledger.jsonl")
        (root / "implementations").symlink_to(outside)

        assert self.read(root)["events"] == []

    def test_kaggle_inbox_is_never_opened(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [_submitted("2026-05-01T00:00:00Z")])
        trap = self.write(root, "kaggle-inbox/token.json", "SECRET")
        self.write_main(root, _decl_body(_declaration("a", "v")))
        self.write_json(root, f"{SIDE}/receipts/r.json", _receipt())
        seen: list[str] = []
        real_open, real_scandir = open, os.scandir

        def spy_open(file, *args, **kwargs):
            seen.append(os.fspath(file))
            return real_open(file, *args, **kwargs)

        def spy_scandir(path="."):
            seen.append(os.fspath(path))
            return real_scandir(path)

        with mock.patch("builtins.open", spy_open), mock.patch("os.scandir", spy_scandir):
            decisions.build_decisions(root)

        assert seen, "the spy saw no file access at all"
        assert not [p for p in seen if "kaggle-inbox" in p]
        assert trap.read_text() == "SECRET"


class MergeTests(_Workspace):
    def event(self, source: str, ts: str | None, summary: str) -> dict:
        return {"ts": ts, "source": source, "kind": "k", "summary": summary, "ref": summary}

    def test_dated_descending_then_null_in_stable_order(self) -> None:
        merged = decisions.merge([
            self.event("declarations", "2026-01-01T00:00:00Z", "old"),
            self.event("proposal", None, "n1"),
            self.event("remote-execution", "2026-03-01T00:00:00Z", "new"),
            self.event("proposal", None, "n2"),
            self.event("declarations", "2026-02-01T00:00:00Z", "mid"),
        ])

        assert [e["summary"] for e in merged] == ["new", "mid", "old", "n1", "n2"]

    def test_equal_ts_tie_break_is_source_order_then_input_order(self) -> None:
        ts = "2026-01-01T00:00:00Z"
        events = [self.event("remote-execution", ts, "r"), self.event("proposal", ts, "p1"),
                  self.event("declarations", ts, "d"), self.event("proposal", ts, "p2")]
        expected = ["d", "p1", "p2", "r"]

        assert [e["summary"] for e in decisions.merge(events)] == expected
        assert [e["summary"] for e in decisions.merge(list(events))] == expected

    def test_timezones_and_formats_compare_as_instants(self) -> None:
        merged = decisions.merge([
            self.event("declarations", "2026-01-01T02:00:00+02:00", "a"),  # 00:00Z
            self.event("declarations", "2026-01-01T00:30:00Z", "b"),
            self.event("declarations", "2026-01-01T00:10:00", "c"),  # naive: UTC
        ])

        assert [e["summary"] for e in merged] == ["b", "c", "a"]

    def test_unparseable_ts_becomes_null_and_sorts_last(self) -> None:
        merged = decisions.merge([self.event("declarations", "yesterday", "bad"),
                                  self.event("declarations", "2026-01-01T00:00:00Z", "good")])

        assert [e["summary"] for e in merged] == ["good", "bad"]
        assert merged[1]["ts"] is None


class BuildTests(_Workspace):
    def test_empty_workspace_has_four_absent_sources(self) -> None:
        data = decisions.build_decisions(self.new_workspace())

        assert data["events"] == [] and data["truncated"] is False
        assert set(data["sources"]) == {"declarations", "proposal", "experiment", "remote-execution"}
        assert {s["status"] for s in data["sources"].values()} == {"absent"}
        assert all(s["count"] == 0 for s in data["sources"].values())

    def test_one_broken_source_never_fails_the_others(self) -> None:
        root = self.new_workspace()
        self.write(root, "paper/main.tex",
                   f"%% paper-writing declarations begin sha256={'0' * 64}\n%% {{x\n"
                   "%% paper-writing declarations end\n")
        self.write_ledger(root, [_submitted("2026-05-01T00:00:00Z")])
        data = decisions.build_decisions(root)

        assert data["sources"]["declarations"]["status"] == "unreadable"
        assert data["sources"]["remote-execution"]["status"] == "ok"
        assert len(data["events"]) == 1

    def test_a_reader_that_raises_is_reported_unreadable(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [_submitted("2026-05-01T00:00:00Z")])
        with mock.patch.object(decisions, "read_declarations", side_effect=RuntimeError("kaput")):
            data = decisions.build_decisions(root)

        assert data["sources"]["declarations"]["status"] == "unreadable"
        assert len(data["events"]) == 1

    def test_merged_order_across_sources(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(_declaration("d", "v", "2026-03-01T00:00:00Z")))
        self.write_json(root, f"{SIDE}/receipts/r.json", _receipt())
        self.write_json(root, f"{SIDE}/{TRANSITIONS}/t.json",
                        _transition(1, "X", "COMMITTED", "2026-06-01T00:00:00Z"))
        self.write_ledger(root, [_returned("2026-04-01T00:00:00Z")])
        data = decisions.build_decisions(root)

        assert [e["source"] for e in data["events"]] == [
            "proposal", "remote-execution", "declarations", "proposal"]
        assert data["events"][-1]["ts"] is None

    def test_per_source_cap_and_truncated_flag(self) -> None:
        root = self.new_workspace()
        self.write_ledger(root, [_returned(f"2026-05-01T00:{i // 60:02d}:{i % 60:02d}Z", f"s{i}")
                                 for i in range(decisions.MAX_LEDGER_LINES)])
        with mock.patch.object(decisions, "MAX_SOURCE_EVENTS", 50):
            data = decisions.build_decisions(root)

        assert len(data["events"]) == 50 and data["truncated"] is True
        assert data["sources"]["remote-execution"]["count"] == 50
        assert data["sources"]["remote-execution"]["truncated"] is True
        # the newest events survive
        assert data["events"][0]["ref"].endswith(f"#{decisions.MAX_LEDGER_LINES}")

    def test_total_cap_and_limit(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(*[_declaration(f"d{i}", "v") for i in range(30)]))
        self.write_ledger(root, [_returned("2026-05-01T00:00:00Z", f"s{i}") for i in range(30)])
        full = decisions.build_decisions(root)
        limited = decisions.build_decisions(root, limit=10)

        assert len(full["events"]) == 60 and full["truncated"] is False
        assert len(limited["events"]) == 10 and limited["truncated"] is True
        assert limited["total"] == 60
        assert decisions.build_decisions(root, limit=0)["events"].__len__() == 1
        assert len(decisions.build_decisions(root, limit=10**9)["events"]) == 60

    def test_total_cap_constant(self) -> None:
        assert decisions.MAX_TOTAL_EVENTS == 1000 and decisions.MAX_SOURCE_EVENTS == 500

    def test_source_filter_reads_only_the_chosen_sources(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(_declaration("d", "v")))
        self.write_ledger(root, [_returned("2026-05-01T00:00:00Z")])
        with mock.patch.object(decisions, "read_declarations", side_effect=AssertionError("read")):
            data = decisions.build_decisions(root, sources=["remote-execution"])

        assert set(data["sources"]) == {"remote-execution"}
        assert [e["source"] for e in data["events"]] == ["remote-execution"]

    def test_unknown_source_raises(self) -> None:
        with self.assertRaises(decisions.DecisionsQueryError):
            decisions.build_decisions(self.new_workspace(), sources=["nope"])

    def test_read_only_invariant(self) -> None:
        root = self.new_workspace()
        self.write_main(root, _decl_body(_declaration("d", "v")))
        self.write_json(root, f"{SIDE}/receipts/r.json", _receipt())
        self.write_ledger(root, [_returned("2026-05-01T00:00:00Z")])
        before = self.snapshot(root)
        decisions.build_decisions(root)

        assert self.snapshot(root) == before
        assert not list(root.rglob("__pycache__"))


if __name__ == "__main__":
    unittest.main()

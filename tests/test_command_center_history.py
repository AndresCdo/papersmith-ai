"""History core: state/health diffs and the in-memory ring with paging."""

from __future__ import annotations

import copy
import threading
import unittest

from skills._core.command_center import history


def _state(**over) -> dict:
    state = {
        "generated_at": "2026-01-01T00:00:00Z",
        "sections": [
            {"id": "01-intro", "status": "CONTRACTED", "blocks_written": 0,
             "word_count": 0, "file": "sections/01-intro.md", "volatile": 1},
        ],
        "gates": [{"id": "writing-readiness", "state": "BLOCKED",
                   "reasons": ["no contract"], "parts": {"n": 1}}],
        "pipeline_stages": [{"id": "drafting", "active": False, "progress": 0.0,
                             "detail": "0/4 blocks written"}],
    }
    state.update(over)
    return state


def _health(overall="HEALTHY", harness="IN_SYNC") -> dict:
    return {
        "generated_at": "t",
        "summary": {"state": overall, "components_total": 3},
        "harness_sync": {"state": harness, "harnesses": [
            {"tool": "claude", "state": harness, "detail": "x"},
            {"tool": "pi", "state": "IN_SYNC", "detail": "y"},
        ]},
    }


class DiffStatesTests(unittest.TestCase):
    def test_identical_states_with_other_timestamp_produce_no_changes(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        curr["generated_at"] = "2027-01-01T00:00:00Z"
        curr["sections"][0]["volatile"] = 99
        curr["gates"][0]["parts"] = {"n": 2}
        curr["pipeline_stages"][0]["detail"] = "changed prose"

        assert history.diff_states(prev, curr) == []

    def test_section_status_blocks_and_words_are_reported_on_the_section_element(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        section = curr["sections"][0]
        section.update(status="DRAFTED", blocks_written=2, word_count=130)

        changes = {c.kind: c for c in history.diff_states(prev, curr)}

        assert set(changes) == {"section_status", "section_blocks", "section_words"}
        assert changes["section_status"].element_id == "section:01-intro"
        assert changes["section_status"].before == "CONTRACTED"
        assert changes["section_status"].after == "DRAFTED"
        assert changes["section_blocks"].after == 2
        assert changes["section_words"].before == 0
        assert changes["section_words"].after == 130
        assert "01-intro" in changes["section_words"].summary

    def test_gate_state_and_reasons_are_one_change_on_the_gate_element(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        curr["gates"][0].update(state="PASSED", reasons=[])

        (change,) = history.diff_states(prev, curr)

        assert change.kind == "gate"
        assert change.element_id == "gate:writing-readiness"
        assert change.before == {"state": "BLOCKED", "reasons": ["no contract"]}
        assert change.after == {"state": "PASSED", "reasons": []}

    def test_a_reason_only_change_is_still_a_gate_change(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        curr["gates"][0]["reasons"] = ["other reason"]

        (change,) = history.diff_states(prev, curr)

        assert change.kind == "gate"

    def test_stage_active_and_progress_are_one_change(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        curr["pipeline_stages"][0].update(active=True, progress=0.5)

        (change,) = history.diff_states(prev, curr)

        assert change.kind == "stage"
        assert change.element_id == "stage:drafting"
        assert change.before == {"active": False, "progress": 0.0}
        assert change.after == {"active": True, "progress": 0.5}

    def test_element_ids_keep_the_raw_id_with_spaces_and_unicode(self) -> None:
        prev = _state()
        curr = copy.deepcopy(prev)
        prev["sections"] = [{"id": "ñ ü 1", "status": "A", "blocks_written": 0, "word_count": 0}]
        curr["sections"] = [{"id": "ñ ü 1", "status": "B", "blocks_written": 0, "word_count": 0}]

        (change,) = history.diff_states(prev, curr)

        assert change.element_id == "section:ñ ü 1"

    def test_added_and_removed_sections_report_a_status_change_from_and_to_none(self) -> None:
        prev = _state()
        added = copy.deepcopy(prev)
        added["sections"].append({"id": "02-new", "status": "EMPTY",
                                  "blocks_written": 0, "word_count": 0})

        (appeared,) = history.diff_states(prev, added)
        (gone,) = history.diff_states(added, prev)

        assert (appeared.kind, appeared.before, appeared.after) == ("section_status", None, "EMPTY")
        assert (gone.kind, gone.before, gone.after) == ("section_status", "EMPTY", None)

    def test_missing_keys_do_not_raise(self) -> None:
        assert history.diff_states({}, {}) == []
        assert history.diff_states({"sections": [{"id": "a"}]}, {"sections": [{"id": "a"}]}) == []


class DiffHealthTests(unittest.TestCase):
    def test_only_overall_and_per_harness_status_count(self) -> None:
        prev = _health()
        curr = _health()
        curr["generated_at"] = "later"
        curr["summary"]["components_total"] = 9
        curr["harness_sync"]["harnesses"][0]["detail"] = "other"

        assert history.diff_health(prev, curr) == []

    def test_overall_and_harness_changes_are_health_entries_without_element(self) -> None:
        changes = history.diff_health(_health(), _health("DEGRADED", "DRIFT"))
        by_summary = {c.summary: c for c in changes}

        assert all(c.kind == "health" and c.element_id is None for c in changes)
        overall = [c for c in changes if c.before == "HEALTHY" and c.after == "DEGRADED"]
        harness = [c for c in changes if c.before == "IN_SYNC" and c.after == "DRIFT"]
        assert len(overall) == 1 and len(harness) == 1
        assert any("claude" in summary for summary in by_summary)


class HistoryStoreTests(unittest.TestCase):
    def new_store(self, capacity: int = 1000) -> history.HistoryStore:
        return history.HistoryStore(capacity=capacity)

    def fill(self, store, count: int, **kw) -> None:
        for index in range(count):
            store.add(kw.get("kind", "section_words"), kw.get("element_id", "section:a"),
                      f"change {index}", index, index + 1)

    def test_entries_have_boot_scoped_ids_and_a_monotonic_seq(self) -> None:
        store = self.new_store()
        first = store.add("health", None, "x", "A", "B")
        second = store.add("health", None, "y", "B", "C")

        assert first.seq == 1 and second.seq == 2
        assert first.boot_id == store.boot_id == second.boot_id
        assert first.id == f"{store.boot_id}-1"
        assert first.element_id is None
        assert first.to_dict()["id"] == first.id

    def test_entries_are_immutable(self) -> None:
        store = self.new_store()
        entry = store.add("gate", "gate:g", "s", {"state": "A"}, {"state": "B"})

        with self.assertRaises(Exception):
            entry.summary = "changed"  # type: ignore[misc]
        payload = entry.to_dict()
        payload["after"]["state"] = "mutated"
        assert store.page()["entries"][0]["after"] == {"state": "B"}

    def test_ring_keeps_only_the_newest_thousand(self) -> None:
        store = self.new_store()
        self.fill(store, 1005)

        page = store.page(limit=500)
        assert store.page(after_seq=0, limit=500)["entries"][0]["seq"] == 6
        assert page["gap"] is True

    def test_page_returns_oldest_first_with_has_more_and_default_limit(self) -> None:
        store = self.new_store()
        self.fill(store, 250)

        first = store.page()
        assert [e["seq"] for e in first["entries"]] == list(range(1, 201))
        assert first["has_more"] is True and first["reset"] is False and first["gap"] is False
        assert first["boot_id"] == store.boot_id

        second = store.page(after_seq=200)
        assert [e["seq"] for e in second["entries"]] == list(range(201, 251))
        assert second["has_more"] is False

    def test_limit_is_clamped_to_1_and_500(self) -> None:
        store = self.new_store()
        self.fill(store, 600)

        assert len(store.page(limit=0)["entries"]) == 1
        assert len(store.page(limit=-5)["entries"]) == 1
        assert len(store.page(limit=10_000)["entries"]) == 500

    def test_a_different_boot_id_resets_and_pages_from_the_start(self) -> None:
        store = self.new_store()
        self.fill(store, 3)

        page = store.page(boot_id="not-this-boot", after_seq=2)

        assert page["reset"] is True
        assert [e["seq"] for e in page["entries"]] == [1, 2, 3]
        assert store.page(boot_id=store.boot_id, after_seq=2)["reset"] is False

    def test_gap_is_true_only_when_requested_entries_were_evicted(self) -> None:
        store = self.new_store(capacity=10)
        self.fill(store, 15)  # retained seq 6..15

        assert store.page(after_seq=2)["gap"] is True
        assert store.page(after_seq=5)["gap"] is False
        assert store.page(after_seq=15)["gap"] is False

    def test_element_and_kind_filters(self) -> None:
        store = self.new_store()
        store.add("gate", "gate:g", "a", 1, 2)
        store.add("section_words", "section:s", "b", 1, 2)
        store.add("health", None, "c", "A", "B")

        assert [e["summary"] for e in store.page(element="gate:g")["entries"]] == ["a"]
        assert [e["summary"] for e in store.page(kind="health")["entries"]] == ["c"]
        assert store.page(element="gate:g", kind="health")["entries"] == []

    def test_filtered_pages_report_has_more_for_matching_entries_only(self) -> None:
        store = self.new_store()
        for _ in range(5):
            store.add("gate", "gate:g", "a", 1, 2)
            store.add("health", None, "c", "A", "B")

        page = store.page(kind="gate", limit=3)
        assert len(page["entries"]) == 3 and page["has_more"] is True
        assert store.page(kind="gate", after_seq=page["entries"][-1]["seq"])["has_more"] is False

    def test_element_with_spaces_and_unicode_is_valid(self) -> None:
        store = self.new_store()
        store.add("section_words", "section:ñ ü 1", "u", 0, 1)

        assert len(store.page(element="section:ñ ü 1")["entries"]) == 1

    def test_invalid_element_and_kind_raise_a_query_error(self) -> None:
        store = self.new_store()
        for bad in ("", "nokind", "edge:a", "stage:", "stage:" + "x" * 201,
                    "stage:a\nb", "stage:a\x00", "stage:a\x7f"):
            with self.subTest(element=bad), self.assertRaises(history.HistoryQueryError):
                store.page(element=bad)
        with self.assertRaises(history.HistoryQueryError):
            store.page(kind="bogus")
        assert store.page(element="stage:" + "x" * 200)["entries"] == []

    def test_concurrent_adds_keep_seq_unique_and_gapless(self) -> None:
        store = self.new_store()

        def worker() -> None:
            for _ in range(100):
                store.add("health", None, "s", 1, 2)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        seqs = [e["seq"] for e in store.page(limit=500)["entries"]]
        assert seqs == list(range(1, 501))


if __name__ == "__main__":
    unittest.main()

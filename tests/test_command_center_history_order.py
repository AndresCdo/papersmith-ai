"""``history_append`` frames must reach the bus in sequence order.

``record()`` is reachable from the watcher flush thread, health measurement
and the wiring-smoke path. The store assigns ``seq`` under its own lock, so the
publish that follows must be serialised with the add or two threads can emit
their frames out of order.
"""

from __future__ import annotations

import itertools
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from skills._core.command_center import history, server

THREADS = 8
FLUSHES_PER_THREAD = 50


class HistoryPublishOrderTests(unittest.TestCase):
    def test_concurrent_flushes_publish_history_in_seq_order(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sections").mkdir()

        counter = itertools.count(1)
        counter_lock = threading.Lock()

        def next_state(_root: Path) -> dict:
            # A unique word count per read makes every flush produce one entry.
            with counter_lock:
                words = next(counter)
            return {"generated_at": "t", "gates": [], "pipeline_stages": [],
                    "sections": [{"id": "01-intro", "status": "CONTRACTED",
                                  "blocks_written": 0, "word_count": words}]}

        store = history.HistoryStore()
        real_add = store.add

        def slow_add(*args, **kwargs):
            entry = real_add(*args, **kwargs)
            # Widen the add -> publish window so an unserialised publish
            # interleaves deterministically instead of by luck.
            time.sleep(0.0005)
            return entry

        store.add = slow_add  # type: ignore[method-assign]

        with mock.patch.object(server, "get_workspace_state", side_effect=next_state):
            app = server.create_app(root, history_store=store)
            published: list[dict] = []
            published_lock = threading.Lock()

            def publish(event: str, payload: dict) -> None:
                if event == "history_append":
                    with published_lock:
                        published.append(payload)

            app.state.bus.publish = publish  # type: ignore[method-assign]
            barrier = threading.Barrier(THREADS)

            def worker() -> None:
                barrier.wait()
                for _ in range(FLUSHES_PER_THREAD):
                    app.state.watcher.on_flush([root / "sections" / "01-intro.md"])

            threads = [threading.Thread(target=worker) for _ in range(THREADS)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        seqs = [frame["seq"] for frame in published]
        assert len(seqs) > 0
        assert seqs == sorted(seqs), "history_append frames were published out of order"
        assert seqs == list(range(1, len(seqs) + 1)), "seq has gaps or duplicates"
        assert {frame["boot_id"] for frame in published} == {store.boot_id}


if __name__ == "__main__":
    unittest.main()

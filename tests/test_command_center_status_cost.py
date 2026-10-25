"""/api/status is polled every few seconds: work whose input file did not
change is reused, and a changed file is read again on the next call."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from skills._core.command_center import server, state_extractor


_SAVES = iter(range(1, 10_000))


def bump(path: Path, text: str) -> None:
    """Rewrite a file as a save made a while ago would leave it: each save
    gets its own mtime, old enough for the memo to trust it."""
    path.write_text(text, encoding="utf-8")
    stamp = (time.time_ns() - 600_000_000_000) + next(_SAVES) * 1_000_000_000
    os.utime(path, ns=(stamp, stamp))


class ParsedFilesAreReusedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        state_extractor.clear_file_memo()

    def test_module_constants_are_parsed_once_until_the_script_changes(self) -> None:
        script = self.tmp / "tool.py"
        bump(script, 'INBOX_NAME = "inbox"\n')
        real_parse = state_extractor.ast.parse
        with mock.patch.object(state_extractor.ast, "parse", side_effect=real_parse) as parse:
            first = state_extractor._module_string_constants(script, ("INBOX_NAME",))
            second = state_extractor._module_string_constants(script, ("INBOX_NAME",))
            self.assertEqual(parse.call_count, 1)
            bump(script, 'INBOX_NAME = "drop"\n')
            third = state_extractor._module_string_constants(script, ("INBOX_NAME",))
            self.assertEqual(parse.call_count, 2)
        self.assertEqual(first, {"INBOX_NAME": "inbox"})
        self.assertEqual(second, first)
        self.assertEqual(third, {"INBOX_NAME": "drop"})

    def test_yaml_is_read_again_only_after_it_changes(self) -> None:
        config = self.tmp / "papersmith.yaml"
        bump(config, "title: First\n")
        first = state_extractor._load_yaml(config)
        first["title"] = "mutated by a caller"
        self.assertEqual(state_extractor._load_yaml(config), {"title": "First"})
        bump(config, "title: Second\n")
        self.assertEqual(state_extractor._load_yaml(config), {"title": "Second"})

    def test_a_file_saved_moments_ago_is_parsed_again(self) -> None:
        # Two saves inside one timestamp tick can share mtime and size; a file
        # that changed this recently is never trusted from the memo.
        config = self.tmp / "papersmith.yaml"
        config.write_text("phase: 3\n", encoding="utf-8")
        self.assertEqual(state_extractor._load_yaml(config), {"phase": 3})
        stat = config.stat()
        config.write_text("phase: 4\n", encoding="utf-8")
        os.utime(config, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(state_extractor._load_yaml(config), {"phase": 4})

    def test_a_permission_change_is_noticed(self) -> None:
        config = self.tmp / "papersmith.yaml"
        bump(config, "title: Open\n")
        self.assertEqual(state_extractor._load_yaml(config), {"title": "Open"})
        stat = config.stat()
        config.chmod(0o000)
        self.addCleanup(config.chmod, 0o644)
        os.utime(config, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        if os.access(config, os.R_OK):
            self.skipTest("running with privileges that ignore file modes")
        self.assertEqual(state_extractor._load_yaml(config), {})

    def test_a_missing_file_is_not_remembered(self) -> None:
        config = self.tmp / "papersmith.yaml"
        self.assertEqual(state_extractor._load_yaml(config), {})
        bump(config, "title: Late\n")
        self.assertEqual(state_extractor._load_yaml(config), {"title": "Late"})


class PdfPageCountTests(unittest.TestCase):
    def test_pdfinfo_runs_once_per_version_of_the_pdf(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "paper").mkdir()
        pdf = root / "paper" / "main.pdf"
        bump(pdf, "%PDF-1.4\n/Count 3\n")
        state_extractor.clear_file_memo()
        done = mock.Mock(stdout="Pages:          7\n")
        with mock.patch.object(server.subprocess, "run", return_value=done) as run:
            app = server.create_app(root)
            status = next(r.endpoint for r in app.routes if getattr(r, "path", "") == "/api/status")
            pages = [json.loads(status().body)["totals"] for _ in range(3)]
            calls = [c for c in run.call_args_list if c.args and c.args[0][0] == "pdfinfo"]
            self.assertEqual(len(calls), 1)
            bump(pdf, "%PDF-1.4\n/Count 4\n")
            status()
            calls = [c for c in run.call_args_list if c.args and c.args[0][0] == "pdfinfo"]
            self.assertEqual(len(calls), 2)
        self.assertEqual([p["pdf_pages"] for p in pages], [7, 7, 7])


if __name__ == "__main__":
    unittest.main()

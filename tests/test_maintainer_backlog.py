"""The backlog steward's checks: issue references, the root map, staleness.

`maintainer/backlog.py` is repository-only tooling. These tests drive its pure
functions with in-memory snapshots, and its CLI as a process, so no test talks
to GitHub.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "maintainer" / "backlog.py"

_spec = importlib.util.spec_from_file_location("maintainer_backlog", SCRIPT)
backlog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backlog)


def _issue(number, body="", title=None):
    return {"number": number, "title": title or f"issue {number}", "body": body}


def _pr(number, body):
    return {"number": number, "title": f"pr {number}", "body": body}


def _roots(*roots):
    return {"roots": [dict({"tier": 2, "fix": "f", "state": "open"}, **r) for r in roots]}


class IssueReferenceTests(unittest.TestCase):
    def test_closing_keywords_and_refs_are_read(self):
        body = "Fixes #12.\n\nCloses: #3, also resolves #40 and Refs #7"
        self.assertEqual(backlog.issue_refs(body), [3, 7, 12, 40])

    def test_a_reference_inside_an_html_comment_does_not_count(self):
        body = "<!-- Closes #12 -->\nNo link here."
        self.assertEqual(backlog.issue_refs(body), [])

    def test_a_cross_repository_reference_does_not_count(self):
        self.assertEqual(backlog.issue_refs("Closes other/repo#12"), [])

    def test_a_bare_mention_is_not_a_link(self):
        self.assertEqual(backlog.issue_refs("see #12 for context"), [])


class RootMapTests(unittest.TestCase):
    def test_a_complete_map_has_no_problems(self):
        roots = _roots({"key": "a", "issues": [1, 2]}, {"key": "b", "issues": [3]})
        issues = [_issue(1), _issue(2), _issue(3)]
        prs = [_pr(9, "Closes #1\nRefs #2")]
        self.assertEqual(backlog.check_roots(roots, issues, prs), [])

    def test_an_open_issue_outside_every_root_is_reported(self):
        problems = backlog.check_roots(_roots({"key": "a", "issues": [1]}), [_issue(1), _issue(2)], [])
        self.assertEqual(problems, ["#2 is open but sits in no root"])

    def test_an_issue_in_two_roots_is_reported(self):
        roots = _roots({"key": "a", "issues": [1]}, {"key": "b", "issues": [1]})
        problems = backlog.check_roots(roots, [_issue(1)], [])
        self.assertEqual(problems, ["#1 sits in more than one root: a, b"])

    def test_a_listed_issue_that_is_no_longer_open_is_reported(self):
        problems = backlog.check_roots(_roots({"key": "a", "issues": [1, 5]}), [_issue(1)], [])
        self.assertEqual(problems, ["#5 is listed in root a but is not open"])

    def test_a_pr_without_an_issue_link_is_reported(self):
        problems = backlog.check_roots(_roots({"key": "a", "issues": [1]}), [_issue(1)], [_pr(9, "no link")])
        self.assertEqual(problems, ["PR #9 links no issue (Closes/Fixes/Resolves/Refs #N)"])

    def test_a_pr_spanning_two_roots_is_reported(self):
        roots = _roots({"key": "a", "issues": [1]}, {"key": "b", "issues": [2]})
        problems = backlog.check_roots(roots, [_issue(1), _issue(2)], [_pr(9, "Closes #1\nCloses #2")])
        self.assertEqual(problems, ["PR #9 spans more than one root: a, b"])

    def test_a_root_without_required_fields_is_reported(self):
        problems = backlog.check_roots({"roots": [{"key": "a", "issues": [1]}]}, [_issue(1)], [])
        self.assertEqual(problems, ["root a lacks fix, state, tier"])


class StaleReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "pkg").mkdir()
        (self.root / "pkg" / "mod.py").write_text("a = 1\nb = 2\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_present_paths_and_lines_are_not_stale(self):
        body = "see `pkg/mod.py:2` and `mod.py`"
        self.assertEqual(backlog.stale_refs(body, self.root), [])

    def test_a_missing_path_is_stale(self):
        self.assertEqual(backlog.stale_refs("in `pkg/gone.py`", self.root), ["pkg/gone.py (no such file)"])

    def test_a_line_past_the_end_is_stale(self):
        self.assertEqual(backlog.stale_refs("`pkg/mod.py:40`", self.root), ["pkg/mod.py:40 (file has 2 lines)"])

    def test_a_line_range_checks_its_last_line(self):
        self.assertEqual(backlog.stale_refs("`mod.py:1-9`", self.root), ["mod.py:1-9 (file has 2 lines)"])


class RenderTests(unittest.TestCase):
    def test_the_tracker_lists_each_root_with_issue_titles(self):
        roots = _roots({"key": "ci", "title": "CI is red", "issues": [1], "tier": 1, "proof": "test_x"})
        text = backlog.render(roots, [_issue(1, title="CI fails")], [_pr(9, "Closes #1")])
        self.assertIn("### Tier 1", text)
        self.assertIn("**ci** — CI is red", text)
        self.assertIn("- [ ] #1 CI fails", text)
        self.assertIn("PRs: #9", text)
        self.assertIn("Proof: test_x", text)


class CliTests(unittest.TestCase):
    def _run(self, *args, env_body=None):
        env = None
        if env_body is not None:
            import os

            env = dict(os.environ, PR_BODY=env_body)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env
        )

    def test_pr_link_accepts_a_linked_body(self):
        result = self._run("pr-link", "--body-env", "PR_BODY", env_body="Closes #4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("#4", result.stdout)

    def test_pr_link_refuses_an_unlinked_body(self):
        result = self._run("pr-link", "--body-env", "PR_BODY", env_body="<!-- Closes #4 -->")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Closes #N", result.stderr)

    def test_check_reads_a_snapshot_and_exits_non_zero_on_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "snap.json"
            roots = Path(tmp) / "roots.json"
            snap.write_text(json.dumps({"issues": [_issue(1), _issue(2)], "prs": []}))
            roots.write_text(json.dumps(_roots({"key": "a", "issues": [1]})))
            result = self._run("check", "--snapshot", str(snap), "--roots", str(roots))
        self.assertEqual(result.returncode, 1)
        self.assertIn("#2 is open but sits in no root", result.stdout)


class ShippingTests(unittest.TestCase):
    def test_the_maintainer_kit_never_ships_to_workspaces(self):
        sys.path.insert(0, str(REPO / "src"))
        try:
            from papersmith.core.manifest import KIT_ENTRIES
        finally:
            sys.path.pop(0)
        self.assertFalse([e for e in KIT_ENTRIES if e.split("/")[0] == "maintainer"])


if __name__ == "__main__":
    unittest.main()

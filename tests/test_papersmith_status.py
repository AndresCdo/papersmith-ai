"""Status snapshots remain useful before optional runtimes are installed."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from papersmith.cli import main
from papersmith.core import init as init_module
from papersmith.core import status as status_module


class StatusTests(unittest.TestCase):
    def new_tmp(self) -> Path:
        """Scratch directory, resolved -- see BridgesTests.new_tmp for why."""
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def test_status_json_reports_versions_and_workspace_inventory(self) -> None:
        tmp_path = self.new_tmp()
        workspace = tmp_path / "status-paper"
        init_module.initialize(workspace, run_npm=False, run_env=False)
        (workspace / "implementations" / "toy" / "tests").mkdir(parents=True)
        (workspace / "implementations" / "toy" / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (workspace / "implementations" / "toy" / "tests" / "test_one.py").write_text("", encoding="utf-8")
        (workspace / "kaggle-inbox" / "job-1").mkdir()
        (workspace / "kaggle-inbox" / "job-1" / "metrics.json").write_text("{}", encoding="utf-8")

        snapshot = status_module.status(workspace)

        assert snapshot["project_name"] == "status-paper"
        assert snapshot["framework"]["version_match"] is True
        assert snapshot["framework"]["drifted_files"] == []
        assert snapshot["proposal"]["revision_id"] is None
        assert snapshot["implementations"] == [{
            "name": "toy",
            "path": "implementations/toy",
            "has_pyproject": True,
            "has_src": False,
            "test_files": 1,
        }]
        assert snapshot["inbox"] == {"files": 1, "job_directories": 1}

    def test_status_cli_json_is_machine_readable(self) -> None:
        tmp_path = self.new_tmp()
        workspace = tmp_path / "status-paper"
        init_module.initialize(workspace, run_npm=False, run_env=False)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert main(["status", str(workspace), "--json"]) == 0
        output = json.loads(buffer.getvalue())
        assert output["project_name"] == "status-paper"


class ProposalStageFromEngineStateTests(unittest.TestCase):
    """B2: the stage of the latest revision is read from the engine's own state.

    The deliberation engine publishes a revision as three artifacts: the
    document under `proposals/`, its derived state and its publication receipt
    under `.proposal-deliberation/`. The legacy `proposals/deliberated/` and
    `proposals/accepted/` folders are no longer written by anything, so a
    reader that only probes them calls every published revision a draft.
    """

    LATEST = "research-concept-topic-r02.md"

    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "proposals").mkdir()
        return root

    def write_revision(self, root: Path, body: bytes, *, receipt_sha: str | None = "match",
                       status: str = "COMMITTED") -> None:
        import hashlib
        (root / "proposals" / self.LATEST).write_bytes(body)
        if receipt_sha is None:
            return
        sha = hashlib.sha256(body).hexdigest() if receipt_sha == "match" else receipt_sha
        receipts = root / ".proposal-deliberation" / "receipts"
        receipts.mkdir(parents=True)
        (receipts / f"{self.LATEST}.json").write_text(json.dumps({
            "operation": "CREATE_SUCCESSOR", "targetRevision": "r02",
            "targetFilename": self.LATEST, "documentShaAfter": sha,
            "derivedStateStatus": status,
        }), encoding="utf-8")

    def stage(self, root: Path) -> dict:
        from unittest import mock
        response = {"status": "ok", "operation": "STATUS", "latest": self.LATEST,
                    "managedRevisions": [], "multipleActive": False, "nonManagedFiles": []}
        with mock.patch.object(status_module, "ensure_node_engine", return_value=("node", root)), \
                mock.patch.object(status_module, "call_engine", return_value=[response]):
            return status_module._proposal_status(root)

    def test_a_revision_with_its_publication_receipt_is_published(self) -> None:
        root = self.new_workspace()
        self.write_revision(root, b"<!-- marker -->\n# Proposal\n")
        report = self.stage(root)
        assert report["lifecycle_stage"] == "published", report
        assert report["receipt"] == {"operation": "CREATE_SUCCESSOR", "document_matches": True}

    def test_a_revision_edited_after_publication_says_so(self) -> None:
        root = self.new_workspace()
        self.write_revision(root, b"edited by hand\n", receipt_sha="0" * 64)
        report = self.stage(root)
        assert report["lifecycle_stage"] == "edited-after-publication", report
        assert report["receipt"]["document_matches"] is False

    def test_an_uncommitted_receipt_is_not_a_publication(self) -> None:
        root = self.new_workspace()
        self.write_revision(root, b"body\n", status="PENDING")
        assert self.stage(root)["lifecycle_stage"] == "draft"

    def test_a_revision_without_a_receipt_stays_a_draft(self) -> None:
        root = self.new_workspace()
        self.write_revision(root, b"body\n", receipt_sha=None)
        report = self.stage(root)
        assert report["lifecycle_stage"] == "draft"
        assert report["receipt"] is None

    def test_a_damaged_receipt_is_a_draft_not_a_crash(self) -> None:
        root = self.new_workspace()
        self.write_revision(root, b"body\n", receipt_sha=None)
        receipts = root / ".proposal-deliberation" / "receipts"
        receipts.mkdir(parents=True)
        (receipts / f"{self.LATEST}.json").write_text("{not json", encoding="utf-8")
        assert self.stage(root)["lifecycle_stage"] == "draft"

    def test_the_legacy_folders_still_read_for_an_old_workspace(self) -> None:
        for folder in ("deliberated", "accepted"):
            with self.subTest(folder=folder):
                root = self.new_workspace()
                (root / "proposals" / folder).mkdir()
                (root / "proposals" / folder / self.LATEST).write_text("x", encoding="utf-8")
                assert self.stage(root)["lifecycle_stage"] == folder

    def test_the_sidecar_and_directory_names_are_the_profiles(self) -> None:
        profile = (Path(__file__).resolve().parents[1] / "skills" / "proposal-deliberation"
                   / "profile.ts").read_text(encoding="utf-8")
        assert f'sidecarRoot: "{status_module.PROPOSAL_SIDECAR_ROOT}"' in profile
        assert f'directory: "{status_module.PROPOSAL_DIRECTORY}"' in profile

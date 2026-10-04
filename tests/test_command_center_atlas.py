"""The read-only SOTA atlas backend: bounded reads, summary, validation, view.

Route functions are called directly (like ``test_command_center_paper_preview``);
the Host allow-list goes through the raw-ASGI harness. The checker is loaded by
the server from the WORKSPACE's ``skills/plausibility/scripts/check_atlas.py``,
so fixture workspaces copy the real script from this repository.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import atlas

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "skills" / "plausibility" / "scripts" / "check_atlas.py"

def _planet(pid: str, slot: str, orbit: int, label: str | None = None) -> dict:
    return {"id": pid, "slot": slot, "orbit": orbit, "label": label or pid,
            "detail": f"detail of {pid}", "provenance": "stated",
            "evidence": {"origin": f"origin-{pid}", "quote": "q", "retrieved": "2026-01-02"}}


def _system(sid: str, family: str) -> dict:
    planets = [_planet("sun", "sun", 0), _planet("app", "topic_app", 1),
               _planet("ai", "topic_ai", 1), _planet("prob", "problem", 1),
               _planet("appl", "application", 1), _planet("fam", "family", 2, family),
               _planet("nov", "novelty", 1), _planet("res", "result", 3),
               _planet("con", "conclusion", 3)]
    return {"id": sid, "title": f"Title {sid}", "planets": planets}


def valid_atlas() -> dict:
    return {
        "systems": [_system("s1", "Alpha"), _system("s2", "Beta"), _system("s3", "Gamma")],
        "links": [
            {"from_system": "s1", "from": "res", "to_system": "s2", "to": "res", "rel": "supports"},
            {"from_system": "s1", "from": "fam", "to_system": "s2", "to": "fam",
             "rel": "shares-family-with"},
            {"from_system": "s2", "from": "res", "to_system": "s3", "to": "res", "rel": "supports"},
        ],
    }


class _Workspace(unittest.TestCase):
    def new_workspace(self, with_checker: bool = True) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sota-pool").mkdir()
        if with_checker:
            target = root / "skills" / "plausibility" / "scripts"
            target.mkdir(parents=True)
            shutil.copy(CHECKER, target / "check_atlas.py")
        return root

    def write(self, root: Path, rel: str, data: str | bytes) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_bytes(data)
        return path

    def write_atlas(self, root: Path, data: dict | None = None, html: str | None = "<html>atlas</html>") -> None:
        self.write(root, "sota-pool/atlas.json", json.dumps(data if data is not None else valid_atlas()))
        if html is not None:
            self.write(root, "sota-pool/atlas.html", html)

    def summary(self, root: Path) -> dict:
        return atlas.build_atlas(root)

    @staticmethod
    def snapshot(root: Path) -> dict:
        out = {}
        for path in sorted(root.rglob("*")):
            st = path.lstat()
            out[str(path.relative_to(root))] = (st.st_size, st.st_mtime_ns)
        return out

    @staticmethod
    def set_mtime(path: Path, when: float) -> None:
        os.utime(path, (when, when))


class AbsentStateTests(_Workspace):
    def test_no_sota_pool_directory(self) -> None:
        root = self.new_workspace()
        shutil.rmtree(root / "sota-pool")
        data = self.summary(root)

        assert data["json"] == {"status": "absent"}
        assert data["html"] == {"status": "absent"}
        assert data["stale"] is None
        assert data["summary"] is None
        assert data["validation"]["status"] == "unavailable"

    def test_empty_sota_pool(self) -> None:
        data = self.summary(self.new_workspace())

        assert data["json"]["status"] == "absent" and data["html"]["status"] == "absent"
        assert data["stale"] is None and data["summary"] is None


class SummaryTests(_Workspace):
    def test_valid_atlas_summary_counts(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root)
        data = self.summary(root)

        assert data["json"]["status"] == "ok" and data["json"]["size"] > 0
        assert data["html"] == {"status": "ok", "size": len("<html>atlas</html>")}
        assert data["validation"]["status"] == "ok" and data["validation"]["errors"] == []
        s = data["summary"]
        assert [x["id"] for x in s["systems"]] == ["s1", "s2", "s3"]
        assert s["systems"][0] == {"id": "s1", "title": "Title s1", "planets": 9, "families": ["Alpha"]}
        assert s["links"] == 3
        assert s["rels"] == {"supports": 2, "shares-family-with": 1}
        assert len(s["evidence"]) == 27
        assert s["evidence"][0] == {"system": "s1", "planet": "sun", "origin": "origin-sun",
                                    "retrieved": "2026-01-02"}

    def test_evidence_and_systems_are_capped(self) -> None:
        root = self.new_workspace()
        big = valid_atlas()
        big["systems"] = [_system(f"s{i}", f"F{i % 4}") for i in range(30)]
        self.write_atlas(root, big)
        s = self.summary(root)["summary"]

        assert len(s["evidence"]) == atlas.MAX_EVIDENCE
        assert s["evidence_total"] == 270
        assert len(s["systems"]) == 30

    def test_structurally_odd_json_gives_no_summary_but_no_error(self) -> None:
        root = self.new_workspace()
        self.write(root, "sota-pool/atlas.json", json.dumps([1, 2]))
        data = self.summary(root)

        assert data["json"]["status"] == "ok"
        assert data["summary"] is None
        assert data["validation"]["status"] == "failed"
        assert data["validation"]["errors"] == ["ATLAS_NOT_AN_OBJECT"]


class StalenessTests(_Workspace):
    def test_json_newer_than_html_is_stale(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root)
        self.set_mtime(root / "sota-pool/atlas.html", 1_700_000_000)
        self.set_mtime(root / "sota-pool/atlas.json", 1_700_000_100)

        assert self.summary(root)["stale"] is True

    def test_html_newer_than_json_is_fresh(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root)
        self.set_mtime(root / "sota-pool/atlas.json", 1_700_000_000)
        self.set_mtime(root / "sota-pool/atlas.html", 1_700_000_100)

        assert self.summary(root)["stale"] is False

    def test_json_present_html_missing(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, html=None)
        data = self.summary(root)

        assert data["json"]["status"] == "ok" and data["html"] == {"status": "absent"}
        assert data["stale"] is None
        assert data["summary"] is not None

    def test_html_present_json_missing(self) -> None:
        root = self.new_workspace()
        self.write(root, "sota-pool/atlas.html", "<html/>")
        data = self.summary(root)

        assert data["json"] == {"status": "absent"} and data["html"]["status"] == "ok"
        assert data["stale"] is None and data["summary"] is None


class InvalidAndCapTests(_Workspace):
    def test_invalid_json_is_reported_not_raised(self) -> None:
        root = self.new_workspace()
        self.write(root, "sota-pool/atlas.json", "{not json")
        data = self.summary(root)

        assert data["json"]["status"] == "invalid"
        assert data["validation"]["status"] == "failed"
        assert data["validation"]["errors"] and data["validation"]["errors"][0].startswith("ATLAS_NOT_JSON")
        assert data["summary"] is None

    def test_json_over_the_cap_is_not_read(self) -> None:
        root = self.new_workspace()
        self.write(root, "sota-pool/atlas.json", b"x" * (atlas.JSON_MAX_BYTES + 1))
        data = self.summary(root)

        assert data["json"] == {"status": "too_large", "size": atlas.JSON_MAX_BYTES + 1}
        assert data["summary"] is None
        assert data["validation"]["status"] == "unavailable"

    def test_html_over_the_cap_is_reported(self) -> None:
        root = self.new_workspace()
        self.write_atlas(root, html=None)
        self.write(root, "sota-pool/atlas.html", b"x" * (atlas.HTML_MAX_BYTES + 1))
        data = self.summary(root)

        assert data["html"] == {"status": "too_large", "size": atlas.HTML_MAX_BYTES + 1}
        assert data["stale"] is None or isinstance(data["stale"], bool)
        assert data["json"]["status"] == "ok"


class ContainmentTests(_Workspace):
    def test_symlinked_json_escaping_the_workspace_is_unsafe(self) -> None:
        root = self.new_workspace()
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        secret = Path(outside.name) / "atlas.json"
        secret.write_text(json.dumps(valid_atlas()))
        (root / "sota-pool" / "atlas.json").symlink_to(secret)
        data = self.summary(root)

        assert data["json"] == {"status": "unsafe"}
        assert data["summary"] is None

    def test_symlinked_html_escaping_the_workspace_is_unsafe(self) -> None:
        root = self.new_workspace()
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        secret = Path(outside.name) / "atlas.html"
        secret.write_text("secret")
        (root / "sota-pool" / "atlas.html").symlink_to(secret)

        assert self.summary(root)["html"] == {"status": "unsafe"}

    def test_sota_pool_directory_symlinked_outside_is_unsafe(self) -> None:
        root = self.new_workspace()
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        Path(outside.name, "atlas.json").write_text(json.dumps(valid_atlas()))
        shutil.rmtree(root / "sota-pool")
        (root / "sota-pool").symlink_to(outside.name)
        data = self.summary(root)

        assert data["json"]["status"] == "unsafe" and data["summary"] is None

    def test_in_workspace_symlink_is_followed(self) -> None:
        root = self.new_workspace()
        self.write(root, "elsewhere/a.json", json.dumps(valid_atlas()))
        (root / "sota-pool" / "atlas.json").symlink_to(root / "elsewhere" / "a.json")

        assert self.summary(root)["json"]["status"] == "ok"

    def test_directories_are_not_regular_files(self) -> None:
        root = self.new_workspace()
        (root / "sota-pool" / "atlas.json").mkdir()
        (root / "sota-pool" / "atlas.html").mkdir()
        data = self.summary(root)

        assert data["json"] == {"status": "unreadable"}
        assert data["html"] == {"status": "unsafe"}


class ValidationTests(_Workspace):
    def test_failures_are_mapped_and_capped(self) -> None:
        root = self.new_workspace()
        bad = valid_atlas()
        bad["systems"] = [_system(f"s{i}", f"F{i % 4}") for i in range(10)]
        bad["links"] = []
        for system in bad["systems"]:
            for planet in system["planets"]:
                planet["provenance"] = "bogus"
        self.write_atlas(root, bad)
        v = self.summary(root)["validation"]

        assert v["status"] == "failed"
        assert len(v["errors"]) == atlas.MAX_ERRORS
        assert v["error_count"] == 90
        assert all(isinstance(e, str) and "PROVENANCE_UNLABELED" in e for e in v["errors"])

    def test_few_failures_are_listed_in_full(self) -> None:
        root = self.new_workspace()
        bad = valid_atlas()
        bad["links"][0]["rel"] = "bogus"
        self.write_atlas(root, bad)
        v = self.summary(root)["validation"]

        assert v["status"] == "failed" and v["error_count"] == 1
        assert "REL_OUTSIDE_CLOSED_SET" in v["errors"][0]

    def test_checker_missing_is_unavailable_not_an_error(self) -> None:
        root = self.new_workspace(with_checker=False)
        self.write_atlas(root)
        data = self.summary(root)

        assert data["validation"]["status"] == "unavailable"
        assert data["validation"]["errors"] == [] and data["validation"]["detail"]
        assert data["summary"] is not None

    def test_checker_that_fails_to_import_is_unavailable(self) -> None:
        root = self.new_workspace()
        self.write(root, "skills/plausibility/scripts/check_atlas.py", "raise RuntimeError('boom')\n")
        self.write_atlas(root)
        v = self.summary(root)["validation"]

        assert v["status"] == "unavailable" and "RuntimeError" in v["detail"]

    def test_checker_without_a_validator_is_unavailable(self) -> None:
        root = self.new_workspace()
        self.write(root, "skills/plausibility/scripts/check_atlas.py", "X = 1\n")
        self.write_atlas(root)

        assert self.summary(root)["validation"]["status"] == "unavailable"

    def test_checker_that_returns_garbage_is_unavailable(self) -> None:
        root = self.new_workspace()
        self.write(root, "skills/plausibility/scripts/check_atlas.py",
                   "def _failures(a):\n    return 7\n")
        self.write_atlas(root)

        assert self.summary(root)["validation"]["status"] == "unavailable"

    def test_checker_that_raises_is_unavailable(self) -> None:
        root = self.new_workspace()
        self.write(root, "skills/plausibility/scripts/check_atlas.py",
                   "def _failures(a):\n    raise ValueError('nope')\n")
        self.write_atlas(root)
        v = self.summary(root)["validation"]

        assert v["status"] == "unavailable" and "ValueError" in v["detail"]

    def test_symlinked_checker_escaping_the_workspace_is_not_executed(self) -> None:
        root = self.new_workspace(with_checker=False)
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        marker = Path(outside.name) / "ran"
        script = Path(outside.name) / "check_atlas.py"
        script.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('x')\n"
                          "def _failures(a):\n    return []\n")
        target = root / "skills" / "plausibility" / "scripts"
        target.mkdir(parents=True)
        (target / "check_atlas.py").symlink_to(script)
        self.write_atlas(root)
        v = self.summary(root)["validation"]

        assert v["status"] == "unavailable"
        assert not marker.exists()


if __name__ == "__main__":
    unittest.main()

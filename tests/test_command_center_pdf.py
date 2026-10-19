"""The live PDF preview: vendored pdf.js, a revalidatable /api/pdf and the
change token the dashboard polls to reload the open preview."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import server

STATIC = Path(server.__file__).resolve().parent / "static"


class _Request:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}


def _route(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path and "GET" in (getattr(route, "methods", None) or ()):
            return route.endpoint
    raise AssertionError(f"no GET {path}")


class PdfRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name).resolve()
        (self.root / "paper").mkdir()
        self.pdf = self.root / "paper" / "main.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 first")
        os.utime(self.pdf, (1_700_000_000, 1_700_000_000))
        self.app = server.create_app(self.root, history_store=None)

    def get(self, headers: dict[str, str] | None = None):
        return _route(self.app, "/api/pdf")(_Request(headers))

    def test_the_pdf_carries_an_etag_and_revalidates(self) -> None:
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(bytes(response.body), b"%PDF-1.4 first")
        etag = response.headers["etag"]
        self.assertTrue(etag.startswith('"') and etag.endswith('"'))
        self.assertEqual(response.headers["cache-control"], "no-cache")
        self.assertEqual(response.headers["content-type"], "application/pdf")

    def test_a_matching_etag_answers_304_without_a_body(self) -> None:
        etag = self.get().headers["etag"]
        response = self.get({"If-None-Match": etag})
        self.assertEqual(response.status_code, 304)
        self.assertEqual(bytes(response.body), b"")
        self.assertEqual(response.headers["etag"], etag)

    def test_a_recompiled_pdf_gets_a_new_etag(self) -> None:
        old = self.get().headers["etag"]
        self.pdf.write_bytes(b"%PDF-1.4 second build")
        os.utime(self.pdf, (1_700_000_100, 1_700_000_100))
        response = self.get({"If-None-Match": old})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.headers["etag"], old)
        self.assertEqual(bytes(response.body), b"%PDF-1.4 second build")

    def test_a_missing_pdf_is_still_404(self) -> None:
        self.pdf.unlink()
        response = self.get()
        self.assertEqual(response.status_code, 404)

    def test_status_reports_the_pdf_change_token(self) -> None:
        status = json.loads(bytes(_route(self.app, "/api/status")().body))
        details = status["run_details"]
        self.assertTrue(details["pdf_ready"])
        self.assertEqual(details["pdf_mtime"], 1_700_000_000_000)
        self.pdf.unlink()
        status = json.loads(bytes(_route(self.app, "/api/status")().body))
        self.assertFalse(status["run_details"]["pdf_ready"])
        self.assertEqual(status["run_details"]["pdf_mtime"], 0)


class VendoredViewerTests(unittest.TestCase):
    def test_pdfjs_ships_with_the_dashboard(self) -> None:
        vendor = STATIC / "vendor"
        for name in ("pdf.min.js", "pdf.worker.min.js", "pdf_viewer.css", "pdfjs-LICENSE"):
            self.assertTrue((vendor / name).is_file(), name)
        self.assertTrue(any((vendor / "cmaps").glob("*.bcmap")))
        self.assertIn('"3.11.174"', (vendor / "pdf.min.js").read_text(encoding="utf-8"))

    def test_the_page_references_only_shipped_vendor_files(self) -> None:
        page = (STATIC / "index.html").read_text(encoding="utf-8")
        import re
        for ref in set(re.findall(r"\./vendor/([A-Za-z0-9_.\-]+)", page)):
            self.assertTrue((STATIC / "vendor" / ref).exists(), ref)


    def test_the_open_preview_follows_the_status_token(self) -> None:
        page = (STATIC / "index.html").read_text(encoding="utf-8")
        self.assertIn("syncPdfPreview((data.run_details || {}).pdf_mtime || 0)", page)
        self.assertIn("scrollToPdfPage(Math.min(page, pdfTotalPages || 1))", page)
        # The editorial execute path still forces its own reload.
        self.assertIn("await initPdfViewer(true);\n        loadExecutionHistory();", page)


if __name__ == "__main__":
    unittest.main()

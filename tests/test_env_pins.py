"""The provisioned environment installs what `requirements.txt` pins (#108).

`scripts/setup_env.py` keeps its own package list and never reads
`requirements.txt`. A bare `kagglesdk` there let a new environment pick up
conda-forge's newest build while the doctrine pin test expects the pinned one,
so CI went red on every run the day upstream published 0.1.38. And Marker,
opt-in since 5d63d3b6, still had one unguarded import, which the forge gate
counts as a hard requirement.
"""

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_parallel_tier import REPO, _conda_base_packages

EXTRACTOR_PATH = REPO / "skills" / "paper-ingestion" / "scripts" / "extract_pdf.py"


def _requirement_pins():
    pins = {}
    for line in (REPO / "requirements.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s#;]+)", line.strip())
        if match:
            pins[match.group(1).lower()] = match.group(2)
    return pins


def _conda_spec(spec):
    match = re.match(r"^([A-Za-z0-9_.-]+)\s*(?:==?\s*([^\s]+))?$", spec)
    return match.group(1).lower(), match.group(2)


class ProvisionedPinTests(unittest.TestCase):
    def test_every_package_requirements_pins_is_installed_at_that_version(self):
        pins = _requirement_pins()
        drift = []
        for spec in _conda_base_packages():
            name, version = _conda_spec(spec)
            if name in pins and version != pins[name]:
                drift.append(f"{spec!r} (requirements.txt pins {name}=={pins[name]})")
        self.assertEqual(drift, [], "setup_env.py installs these unpinned or at another version")

    def test_the_kaggle_sdk_is_among_the_checked_packages(self):
        names = {_conda_spec(s)[0] for s in _conda_base_packages()}
        self.assertIn("kagglesdk", names)
        self.assertIn("kagglesdk", _requirement_pins())


class OptionalMarkerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("extract_pdf_for_pins", EXTRACTOR_PATH)
        self.extractor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.extractor)

    def test_rendering_with_marker_absent_refuses_with_the_setup_hint(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            sys.modules, {"marker": None, "marker.output": None}
        ):
            with self.assertRaises(self.extractor.EngineError) as caught:
                self.extractor.render_paper(lambda _path: None, Path(tmp) / "x.pdf", False, Path(tmp))
        self.assertIn("Marker engine is not available", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

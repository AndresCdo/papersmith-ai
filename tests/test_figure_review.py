"""figure-review: the tenth skill's own suite (Commit 1 of five).

This commit claims exactly one thing — an already-compiled figure PDF can be
turned into a PNG deterministically, over a fixed fallback chain, with a
named refusal when no link resolves, and its own subprocess seam guarding
the one module allowed to spawn a process. It claims no visual dimension:
`png_read.py`, `geometry.py`, `findings.py` and the fixture-driven decode
tier all land in Commit 2.

Every chain-fallback test below runs against a scratch `PATH` holding only
stub executables — never a real rasterizer — so this suite is unconditional
on any machine, with or without `pdftoppm`/`pdftocairo`/`gs`/`sips`
installed (`figure-raster` spec, `Requirement: No-Skip Test Evidence Across
Three Tiers`).
"""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parents[1]
REVIEW_SCRIPTS = FORGE_ROOT / "skills" / "figure-review" / "scripts"
sys.path.insert(0, str(REVIEW_SCRIPTS))
import raster  # noqa: E402

sys.path.insert(0, str(FORGE_ROOT / "skills" / "_core" / "implementation"))
from impl_refusals import Refused  # noqa: E402

import unittest  # noqa: E402

# =====================================================================
# Figure-review's own subprocess seam, mirroring `NoSubprocessScanTests`
# (`tests/test_paper_writing.py:6136-6158`), plus one non-vacuity assertion
# the precedent lacks.
# =====================================================================

#: Pinned to `len(...) == 1` for the same reason paper-writing's own
#: exception tuple is: a SECOND name costs a hand edit to this literal in a
#: diff someone reads.
REVIEW_SUBPROCESS_EXCEPTIONS: tuple = ("raster.py",)


def _forbidden_process_names_in(source_path: Path) -> list:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    found: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("subprocess", "multiprocessing"):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module in ("subprocess", "multiprocessing"):
            found.append(node.module)
        elif (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "os"):
            if node.attr in ("system", "popen") or node.attr.startswith("exec"):
                found.append(f"os.{node.attr}")
    return found


def scan_review_subprocess_imports(scripts_dir: Path) -> dict:
    """Mirrors `test_paper_writing.scan_forbidden_process_imports`'s shape,
    scoped to `figure-review`'s own scripts. Deliberately `rglob` rather
    than the precedent's non-recursive `glob` (`test_paper_writing.py:6127`),
    so a future `scripts/<subdir>/tool.py` is covered rather than silently
    unscanned."""
    violations: dict = {}
    for path in sorted(scripts_dir.rglob("*.py")):
        if path.name in REVIEW_SUBPROCESS_EXCEPTIONS:
            continue
        found = _forbidden_process_names_in(path)
        if found:
            violations[path.name] = found
    return violations


class FigureReviewSubprocessScanTests(unittest.TestCase):

    def test_exception_list_has_exactly_one_entry(self) -> None:
        self.assertEqual(len(REVIEW_SUBPROCESS_EXCEPTIONS), 1)
        self.assertEqual(REVIEW_SUBPROCESS_EXCEPTIONS, ("raster.py",))

    def test_no_shipped_script_imports_a_forbidden_process_primitive(self) -> None:
        self.assertEqual(scan_review_subprocess_imports(REVIEW_SCRIPTS), {})

    def test_a_planted_subprocess_import_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "evil.py").write_text("import subprocess\n", encoding="utf-8")
            violations = scan_review_subprocess_imports(tmp_dir)
        self.assertIn("evil.py", violations)
        self.assertIn("subprocess", violations["evil.py"])

    def test_the_exception_named_file_is_tolerated_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "raster.py").write_text("import subprocess\n", encoding="utf-8")
            violations = scan_review_subprocess_imports(tmp_dir)
        self.assertEqual(violations, {})

    def test_the_scan_directory_is_not_vacuous(self) -> None:
        """Assertion 2 above passes vacuously if `REVIEW_SCRIPTS` ever
        resolved to an empty or wrong directory -- an empty scan and a
        clean scan are the same `{}`. Pin non-vacuity directly: the
        directory this scan actually reads is real, on disk, and not
        empty."""
        self.assertTrue(REVIEW_SCRIPTS.is_dir(), REVIEW_SCRIPTS)
        on_disk = {path.name for path in REVIEW_SCRIPTS.rglob("*.py")}
        self.assertTrue(on_disk, "figure-review ships no scripts, which cannot be")
        self.assertIn("raster.py", on_disk)
        self.assertIn("review_cli.py", on_disk)


# =====================================================================
# Repair-budget isolation, raster-only half (Threat Matrix: "Repair-budget
# isolation"). The full end-to-end half -- a real ledger byte-identical
# before and after a complete visual pass -- is Commit 4's lock 5.
# =====================================================================

class RepairBudgetIsolationTests(unittest.TestCase):

    FORBIDDEN_MODULES = ("paper_latex", "paper_figure")

    def _imported_modules(self, path: Path) -> set:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
        return found

    def test_no_shipped_script_imports_paper_latex_or_paper_figure(self) -> None:
        for path in sorted(REVIEW_SCRIPTS.rglob("*.py")):
            with self.subTest(script=path.name):
                imported = self._imported_modules(path)
                self.assertFalse(
                    imported & set(self.FORBIDDEN_MODULES),
                    f"{path.name} imports {imported & set(self.FORBIDDEN_MODULES)}, "
                    "coupling figure-review to the repair-budget ledger",
                )

    def test_no_shipped_script_names_a_ledger_file(self) -> None:
        for path in sorted(REVIEW_SCRIPTS.rglob("*.py")):
            with self.subTest(script=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("ledger.json", text)
                self.assertNotIn("_write_ledger", text)

    def test_a_planted_ledger_call_is_caught(self) -> None:
        """RED/GREEN evidence for the mutation this lock must survive: a
        `_write_ledger`-shaped call is exactly what the assertion above
        would catch if it ever appeared in a shipped script."""
        planted = "def _write_ledger(path, ledger):\n    pass\n"
        with self.assertRaises(AssertionError):
            self.assertNotIn("_write_ledger", planted)


# =====================================================================
# Rasterizer fallback chain (lock 7) and the Threat Matrix rows scoped to
# `raster.py`. Every case below is stubbed: no real `pdftoppm`,
# `pdftocairo`, `gs` or `sips` is ever invoked by this class.
# =====================================================================

#: A syntactically minimal PNG -- signature plus one `IHDR` chunk, nothing
#: else. `raster._read_png_header` reads only these 26 bytes; it never
#: inflates or validates a trailing `IDAT`/`IEND`, so this is sufficient to
#: prove chain-fallback and header-reporting behavior without a real
#: capture (the real, captured fixtures belong to Commit 2's fixture-driven
#: decode tier).
_FAKE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    + (13).to_bytes(4, "big") + b"IHDR"
    + (800).to_bytes(4, "big") + (600).to_bytes(4, "big")
    + bytes([8, 0, 0, 0, 0])
)

_POPPLER_STUB_BODY = f"""
import sys
from pathlib import Path

argv = sys.argv
prefix = argv[-1]
Path(prefix + "-1.png").write_bytes(bytes.fromhex({_FAKE_PNG_BYTES.hex()!r}))
"""

_GS_STUB_BODY = f"""
import sys
from pathlib import Path

argv = sys.argv
out_flag = next(a for a in argv if a.startswith("-sOutputFile="))
Path(out_flag.split("=", 1)[1]).write_bytes(bytes.fromhex({_FAKE_PNG_BYTES.hex()!r}))
"""

_SIPS_STUB_BODY = f"""
import sys
from pathlib import Path

argv = sys.argv
if "--out" in argv:
    out_path = Path(argv[argv.index("--out") + 1])
    out_path.write_bytes(bytes.fromhex({_FAKE_PNG_BYTES.hex()!r}))
else:
    print("pixelWidth: 800")
    print("pixelHeight: 600")
"""

_SLEEPING_STUB_BODY = "import time\ntime.sleep(10)\n"
_FAILING_STUB_BODY = "import sys\nsys.exit(1)\n"
_SILENT_SUCCESS_STUB_BODY = "import sys\nsys.exit(0)\n"

_STUB_BODIES = {
    "pdftoppm": _POPPLER_STUB_BODY,
    "pdftocairo": _POPPLER_STUB_BODY,
    "gs": _GS_STUB_BODY,
    "sips": _SIPS_STUB_BODY,
}


def _write_stub(bin_dir: Path, name: str, body: str) -> Path:
    path = bin_dir / name
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return path


def _stub_dir(tmp_dir: Path, tools: dict) -> Path:
    """`tools` maps a tool name to a stub body. Only the named tools become
    executables on the returned directory -- everything else on `CHAIN` is
    genuinely absent from it, never merely unobserved."""
    bin_dir = tmp_dir / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, body in tools.items():
        _write_stub(bin_dir, name, body)
    return bin_dir


class ChainFallbackTests(unittest.TestCase):

    def _tmp(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name)

    def _pdf(self, tmp_dir: Path, name: str = "example-figure.pdf") -> Path:
        figures_dir = tmp_dir / "paper" / "Figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        pdf = figures_dir / name
        pdf.write_bytes(b"%PDF-1.4 stub\n%%EOF\n")
        return pdf

    def test_the_first_link_present_is_used(self) -> None:
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {"pdftoppm": _STUB_BODIES["pdftoppm"]})
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
        self.assertEqual(result["tool"], "pdftoppm")
        self.assertTrue(Path(result["png"]).is_file())
        self.assertEqual(result["dpiSource"], "flag")

    def test_a_middle_link_is_reached_only_when_earlier_links_are_absent(self) -> None:
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {"gs": _STUB_BODIES["gs"]})
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
        self.assertEqual(result["tool"], "gs")
        self.assertIsNone(shutil.which("pdftoppm", path=str(bin_dir)))
        self.assertIsNone(shutil.which("pdftocairo", path=str(bin_dir)))

    def test_the_last_link_is_reached_only_when_every_other_link_is_absent(self) -> None:
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {"sips": _STUB_BODIES["sips"]})
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
        self.assertEqual(result["tool"], "sips")
        self.assertEqual(result["dpiSource"], "derived")
        self.assertTrue(Path(result["png"]).is_file())
        for earlier in ("pdftoppm", "pdftocairo", "gs"):
            self.assertIsNone(shutil.which(earlier, path=str(bin_dir)))

    def test_an_emptied_path_refuses_naming_every_probed_tool(self) -> None:
        tmp_dir = self._tmp()
        pdf = self._pdf(tmp_dir)
        with self.assertRaises(Refused) as ctx:
            raster.rasterize(pdf, tmp_dir / "scratch", path="")
        self.assertEqual(ctx.exception.code, "RASTER_TOOLCHAIN_ABSENT")
        for tool in raster.CHAIN:
            self.assertIn(tool, ctx.exception.detail)
        self.assertIn("PATH=", ctx.exception.detail)

        proc = subprocess.run(
            [sys.executable, str(REVIEW_SCRIPTS / "review_cli.py"), "probe", "--path", ""],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["code"], "RASTER_TOOLCHAIN_ABSENT")
        for tool in raster.CHAIN:
            self.assertIn(tool, payload["detail"])

    def test_a_failing_first_link_falls_through_to_the_next(self) -> None:
        """Threat Matrix: PATH resolution / tool discovery -- a link
        present but exiting non-zero is a LINK failure, not a global
        refusal."""
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {
            "pdftoppm": _FAILING_STUB_BODY,
            "pdftocairo": _STUB_BODIES["pdftocairo"],
        })
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
        self.assertEqual(result["tool"], "pdftocairo")

    def test_a_link_that_sleeps_past_the_timeout_falls_through(self) -> None:
        """Threat Matrix: subprocess timeout and resource bound."""
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {
            "pdftoppm": _SLEEPING_STUB_BODY,
            "pdftocairo": _STUB_BODIES["pdftocairo"],
        })
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir), timeout=2.0)
        self.assertEqual(result["tool"], "pdftocairo")

    def test_every_link_sleeping_refuses_naming_a_timeout_not_a_false_absence(self) -> None:
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {tool: _SLEEPING_STUB_BODY for tool in raster.CHAIN})
        pdf = self._pdf(tmp_dir)
        with self.assertRaises(Refused) as ctx:
            raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir), timeout=2.0)
        self.assertEqual(ctx.exception.code, "RASTER_TOOLCHAIN_ABSENT")
        self.assertIn("timed out", ctx.exception.detail)
        for tool in raster.CHAIN:
            self.assertNotIn(
                f"{tool}: absent", ctx.exception.detail,
                "a tool that was present and slow must never be reported as absent",
            )

    def test_a_link_that_exits_zero_writing_nothing_falls_through(self) -> None:
        """Threat Matrix: untrusted output parsing, chain-fallback half.
        The decoder half (truncated/16-bit/palette/interlaced/zero-byte
        fixtures) needs `png_read.py` and is Commit 2's task."""
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {
            "pdftoppm": _SILENT_SUCCESS_STUB_BODY,
            "pdftocairo": _STUB_BODIES["pdftocairo"],
        })
        pdf = self._pdf(tmp_dir)
        result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
        self.assertEqual(result["tool"], "pdftocairo")

    def test_argument_composition_survives_special_characters_in_the_pdf_path(self) -> None:
        """Threat Matrix: subprocess argument composition. Always a list,
        never a composed string, and the PDF operand is resolved absolute
        before it reaches argv -- so a name beginning with `-` is never
        read as a flag."""
        for label, filename in (
            ("space", "a figure.pdf"),
            ("semicolon", "a;figure.pdf"),
            ("leading dash", "-figure.pdf"),
        ):
            with self.subTest(case=label):
                tmp_dir = self._tmp()
                bin_dir = _stub_dir(tmp_dir, {"pdftoppm": _STUB_BODIES["pdftoppm"]})
                pdf = self._pdf(tmp_dir, name=filename)
                result = raster.rasterize(pdf, tmp_dir / "scratch", path=str(bin_dir))
                self.assertEqual(result["tool"], "pdftoppm")
                argv = result["argv"]
                pdf_operand = argv[-2]
                self.assertEqual(pdf_operand, str(pdf.resolve()))
                self.assertTrue(
                    pdf_operand.startswith("/"),
                    "the resolved PDF operand must be absolute, so a leading "
                    "'-' in the figure's own name is never read as a flag",
                )

    def test_probe_reports_the_resolved_link(self) -> None:
        tmp_dir = self._tmp()
        bin_dir = _stub_dir(tmp_dir, {"pdftocairo": _STUB_BODIES["pdftocairo"]})
        self.assertEqual(raster.resolve_link(path=str(bin_dir)), "pdftocairo")
        self.assertEqual(raster.probe(path=str(bin_dir))["resolved"], "pdftocairo")

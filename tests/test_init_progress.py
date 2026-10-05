"""`init` reports its own progress, without breaking its silent callers.

Three things are held here, and each exists because getting it wrong is
invisible until it hurts. The bar and the estimate are rendered from an
injected clock, so the arithmetic is asserted rather than watched. The child's
output is streamed AND kept, because the failure messages downstream read the
tail. And the default mode writes nothing at all, because the MCP server spawns
`papersmith init` as a child and reads its stdout.

Stdlib only.
"""

import io
import subprocess
import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from papersmith.core import progress  # noqa: E402


class FakeClock:
    """A clock the test advances by hand: no sleeping, no flakes."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds: float):
        self.now += seconds


STEPS = (
    progress.Step("prepare", "preparing", 1.0),
    progress.Step("kit", "copying the kit", 2.0),
    progress.Step("environment", "provisioning the environment", 300.0),
    progress.Step("manifest", "writing the baseline", 1.0),
)


class ReporterModeTests(unittest.TestCase):
    def test_the_default_reporter_writes_nothing(self):
        """The machine-readable path: a caller that says nothing gets no bytes."""
        stream = io.StringIO()
        report = progress.Reporter(stream)
        report.plan(STEPS)
        report.start("prepare")
        report.log("noise from a child")
        report.done("prepare")
        report.finish()
        self.assertEqual(stream.getvalue(), "")
        self.assertEqual(report.mode, progress.SILENT)

    def test_a_stream_that_is_not_a_terminal_is_silent_unless_asked(self):
        self.assertEqual(progress.Reporter.for_stream(io.StringIO()).mode, progress.SILENT)
        self.assertEqual(
            progress.Reporter.for_stream(io.StringIO(), requested=True).mode,
            progress.PLAIN)

    def test_a_terminal_gets_the_bar(self):
        class Tty(io.StringIO):
            def isatty(self):
                return True

        self.assertEqual(progress.Reporter.for_stream(Tty()).mode, progress.BAR)

    def test_plain_mode_names_every_step_once_and_never_carries_a_return(self):
        stream = io.StringIO()
        report = progress.Reporter(stream, mode=progress.PLAIN)
        report.plan(STEPS)
        for step in STEPS:
            report.start(step.key)
            report.done(step.key)
        report.finish()
        out = stream.getvalue()
        self.assertNotIn("\r", out)
        for step in STEPS:
            self.assertEqual(out.count(step.label), 1, step.key)
        self.assertIn("4/4", out)


class EstimateTests(unittest.TestCase):
    def test_the_first_estimate_is_the_declared_priors(self):
        report = progress.Reporter(io.StringIO(), mode=progress.BAR)
        report.plan(STEPS)
        self.assertAlmostEqual(report.remaining(), 304.0)

    def test_a_finished_step_scales_what_is_left_by_the_measured_pace(self):
        """A step that takes twice its prior makes the rest look twice as long:
        the estimate follows the run, it does not defend its first guess."""
        clock = FakeClock()
        report = progress.Reporter(io.StringIO(), mode=progress.BAR, clock=clock)
        report.plan(STEPS)
        report.start("prepare")
        clock.advance(2.0)          # prior was 1.0 -> pace 2.0
        report.done("prepare")
        # the remaining priors are 2 + 300 + 1 = 303, at pace 2.0
        self.assertAlmostEqual(report.remaining(), 606.0)

    def test_a_running_step_that_overruns_grows_the_estimate(self):
        clock = FakeClock()
        report = progress.Reporter(io.StringIO(), mode=progress.BAR, clock=clock)
        report.plan(STEPS)
        report.start("prepare")
        clock.advance(1.0)
        report.done("prepare")
        before = report.remaining()
        report.start("kit")          # prior 2.0 at pace 1.0
        clock.advance(5.0)           # 3 seconds past its own share
        self.assertAlmostEqual(report.remaining(), before + 3.0)

    def test_the_estimate_never_goes_negative(self):
        clock = FakeClock()
        report = progress.Reporter(io.StringIO(), mode=progress.BAR, clock=clock)
        report.plan(STEPS)
        for step in STEPS:
            report.start(step.key)
            clock.advance(0.001)
            report.done(step.key)
        self.assertGreaterEqual(report.remaining(), 0.0)


class RenderingTests(unittest.TestCase):
    def test_the_bar_counts_finished_steps_and_names_the_running_one(self):
        stream = io.StringIO()
        report = progress.Reporter(stream, mode=progress.BAR,
                                   clock=FakeClock())
        report.plan(STEPS)
        report.start("prepare")
        report.done("prepare")
        report.start("kit")
        out = stream.getvalue()
        self.assertIn("1/4", out)
        self.assertIn("copying the kit", out)
        self.assertIn("\r", out)

    def test_a_child_line_reaches_the_log_and_the_bar_comes_back(self):
        stream = io.StringIO()
        report = progress.Reporter(stream, mode=progress.BAR, clock=FakeClock())
        report.plan(STEPS)
        report.start("environment")
        report.log("Downloading micromamba")
        out = stream.getvalue()
        self.assertIn("Downloading micromamba", out)
        self.assertGreaterEqual(out.count("\r["), 2,
                                "the bar must be redrawn after a log line")

    def test_an_edit_free_finish_leaves_one_summary_line(self):
        stream = io.StringIO()
        report = progress.Reporter(stream, mode=progress.BAR, clock=FakeClock())
        report.plan(STEPS)
        for step in STEPS:
            report.start(step.key)
            report.done(step.key)
        report.finish()
        out = stream.getvalue()
        self.assertTrue(out.endswith("\n"))
        self.assertIn("4/4", out.splitlines()[-1])


class StreamingRunnerTests(unittest.TestCase):
    def test_lines_are_forwarded_to_the_reporter_and_returned_too(self):
        stream = io.StringIO()
        report = progress.Reporter(stream, mode=progress.PLAIN)
        report.plan((progress.Step("child", "running a child", 1.0),))
        report.start("child")
        code, tail = progress.run_streaming(
            [sys.executable, "-c",
             "import sys; [print(f'line {i}') for i in range(3)]; sys.stderr.write('boom\\n')"],
            report=report, timeout=30)
        self.assertEqual(code, 0)
        for i in range(3):
            self.assertIn(f"line {i}", stream.getvalue())
        self.assertIn("boom", tail)

    def test_a_non_zero_exit_still_returns_the_tail(self):
        report = progress.Reporter(io.StringIO(), mode=progress.SILENT)
        code, tail = progress.run_streaming(
            [sys.executable, "-c", "import sys; print('out'); sys.exit(3)"],
            report=report, timeout=30)
        self.assertEqual(code, 3)
        self.assertIn("out", tail)

    def test_a_timeout_is_reported_as_a_timeout_not_as_a_crash(self):
        report = progress.Reporter(io.StringIO(), mode=progress.SILENT)
        with self.assertRaises(progress.ChildTimedOut):
            progress.run_streaming(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                report=report, timeout=0.2)

    def test_a_missing_binary_raises_the_oserror_the_caller_already_handles(self):
        report = progress.Reporter(io.StringIO(), mode=progress.SILENT)
        with self.assertRaises(OSError):
            progress.run_streaming(["/nonexistent/binary"], report=report, timeout=5)


if __name__ == "__main__":
    unittest.main()

"""A step plan rendered while it runs: a bar, the child's log, an estimate.

``papersmith init`` spends most of its life inside two child processes — an
``npm install`` and the workspace's own environment provisioning — and until
this module existed it ran them with the output captured, so the operator
watched nothing for minutes and, on a cold cache, for the better part of an
hour. That is the state this file removes: the plan is declared up front, each
step is measured as it finishes, and the child's own lines are streamed instead
of swallowed.

**Three modes, and silence is the default.** ``Reporter()`` writes nothing:
every programmatic caller — the MCP server, which spawns ``papersmith init`` and
reads its stdout, and the test suite — keeps the bytes it always got. A caller
that wants reporting asks for it (``mode=BAR``/``mode=PLAIN``), or goes through
:meth:`Reporter.for_stream`, which chooses the bar for a terminal, the plain log
for an explicit request, and silence for a pipe.

**The estimate is calibrated, and it is an estimate.** Before anything finishes
it is the sum of the declared priors. After a step finishes, its measured time
replaces its prior and the remaining priors are scaled by the pace the run has
shown. A running step that exceeds its own share grows the estimate live rather
than leaving a number that cannot come true. The priors are priors: the
environment step is a download, and nobody knows in advance how long it will
take.

Stdlib only, like the rest of the CLI. No colour, no dependency.
"""

from __future__ import annotations

import contextlib
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Sequence

SILENT = "silent"
PLAIN = "plain"
BAR = "bar"

#: Cells in the drawn bar. Wide enough to read, narrow enough to leave room for
#: the label on an 80-column terminal.
BAR_WIDTH = 20

#: Lines of a child's output kept for the caller's failure message. The messages
#: downstream read only the last line, but a timeout is worth more context.
TAIL_LINES = 40


class ChildTimedOut(RuntimeError):
    """The child outlived its timeout. Its own output is in the message."""


@dataclass(frozen=True)
class Step:
    """One unit of work: a stable key, a label to read, and a prior in seconds."""

    key: str
    label: str
    seconds: float


def human(seconds: float) -> str:
    """A duration a human reads at a glance: ``7s``, ``3m05s``, ``1h12m``."""
    total = int(round(max(0.0, seconds)))
    if total < 60:
        return f"{total}s"
    minutes, rest = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m{rest:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


class Reporter:
    """The plan, its progress, and the child output that belongs to it."""

    def __init__(self, stream=None, *, mode: str = SILENT,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.stream = stream
        self.mode = mode
        self._clock = clock
        self._steps: list[Step] = []
        self._started: dict[str, float] = {}
        self._durations: dict[str, float] = {}
        self._running: str | None = None
        self._finished = 0
        self._began = clock()

    @classmethod
    def for_stream(cls, stream, *, requested: bool = False,
                   suppressed: bool = False,
                   clock: Callable[[], float] = time.monotonic) -> "Reporter":
        """Pick the mode from the stream itself.

        An explicit request wins in both directions, because the operator who
        typed the flag knows their terminal better than ``isatty`` does. A pipe
        gets silence: that is the MCP child's stdout and every test capture.
        """
        if suppressed:
            return cls(stream, mode=SILENT, clock=clock)
        if requested:
            return cls(stream, mode=PLAIN, clock=clock)
        if getattr(stream, "isatty", None) and stream.isatty():
            return cls(stream, mode=BAR, clock=clock)
        return cls(stream, mode=SILENT, clock=clock)

    # -- the plan ---------------------------------------------------------
    def plan(self, steps: Sequence[Step]) -> None:
        self._steps = list(steps)
        self._began = self._clock()

    def has_steps(self) -> bool:
        return bool(self._steps)

    @contextlib.contextmanager
    def step(self, key: str) -> Iterator[None]:
        """Run one step and mark it finished whatever happens.

        A step that raises still counts as finished: the failure is the
        caller's to report, and a bar stuck on the step that blew up is a worse
        answer than a bar that moved past it.
        """
        self.start(key)
        try:
            yield
        finally:
            self.done(key)

    def start(self, key: str) -> None:
        self._running = key
        self._started[key] = self._clock()
        self._render()

    def done(self, key: str) -> None:
        if key in self._started:
            self._durations[key] = self._clock() - self._started[key]
        self._finished += 1
        if self._running == key:
            self._running = None
        if self.mode == PLAIN:
            self._write(f"[{self._finished}/{len(self._steps)}] {self._label(key)}"
                        f" ({human(self._durations.get(key, 0.0))})\n")
        else:
            self._render()

    def log(self, text: str) -> None:
        """One line of a child's own output."""
        if self.mode == SILENT:
            return
        if self.mode == PLAIN:
            self._write(f"    {text}\n")
            return
        self._clear()
        self._write(f"    {text}\n")
        self._render()

    def finish(self) -> None:
        if self.mode == SILENT or not self._steps:
            return
        elapsed = human(self._clock() - self._began)
        if self.mode == PLAIN:
            self._write(f"[{len(self._steps)}/{len(self._steps)}] done in {elapsed}\n")
            return
        self._render(final=True)

    # -- the estimate -----------------------------------------------------
    def remaining(self) -> float:
        """Seconds left: the remaining priors at the pace this run has shown.

        Before a step finishes there is no pace to speak of, so the priors stand
        as declared. Afterwards the measured time of each finished step replaces
        its prior and scales what is left. A running step that has already spent
        more than its scaled share adds the difference, so a slow download moves
        the number instead of contradicting it.
        """
        finished_actual = 0.0
        finished_prior = 0.0
        pending = 0.0
        for step in self._steps:
            if step.key in self._durations:
                finished_actual += self._durations[step.key]
                finished_prior += step.seconds
            else:
                pending += step.seconds
        pace = finished_actual / finished_prior if finished_prior > 0 else 1.0
        estimate = pending * pace
        if self._running is not None:
            prior = self._prior(self._running)
            overrun = (self._clock() - self._started[self._running]) - prior * pace
            if overrun > 0:
                estimate += overrun
        return max(0.0, estimate)

    # -- rendering --------------------------------------------------------
    def _prior(self, key: str) -> float:
        for step in self._steps:
            if step.key == key:
                return step.seconds
        return 0.0

    def _label(self, key: str) -> str:
        for step in self._steps:
            if step.key == key:
                return step.label
        return key

    def _write(self, text: str) -> None:
        if self.stream is None:
            return
        self.stream.write(text)
        flush = getattr(self.stream, "flush", None)
        if flush is not None:
            flush()

    def _clear(self) -> None:
        self._write("\r" + " " * 78 + "\r")

    def _render(self, *, final: bool = False) -> None:
        if self.mode != BAR:
            return
        total = len(self._steps)
        filled = int(BAR_WIDTH * self._finished / total) if total else 0
        bar = "#" * filled + "." * (BAR_WIDTH - filled)
        if final:
            elapsed = human(self._clock() - self._began)
            self._write(f"\r[{bar}] {self._finished}/{total} done in {elapsed}\n")
            return
        current = self._label(self._running) if self._running else "working"
        self._write(f"\r[{bar}] {self._finished}/{total} {current}"
                    f"  left {human(self.remaining())}")


def run_streaming(argv: Sequence[str], *, report: "Reporter",
                  timeout: float, cwd=None) -> tuple[int, str]:
    """Run a child, stream its output to ``report``, and return its tail.

    The tail comes back because the callers' failure messages read it: the
    existing "npm install failed: …" and "environment provisioning failed: …"
    strings keep the last line the child wrote, exactly as they did when the
    output was captured whole.

    A timeout kills the child and raises :class:`ChildTimedOut` with the output
    it managed to write, so a provisioning step that stalls is a named state
    rather than a hang. A binary that cannot be started raises the ``OSError``
    the callers already handle.
    """
    process = subprocess.Popen(                       # noqa: S603 - argv is built by the caller
        list(argv), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1)

    lines: list[str] = []
    pipe: "queue.Queue[str | None]" = queue.Queue()

    def pump() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            pipe.put(line.rstrip("\n"))
        pipe.put(None)

    threading.Thread(target=pump, daemon=True).start()
    deadline = time.monotonic() + timeout
    timed_out = False
    while True:
        left = deadline - time.monotonic()
        if left <= 0:
            timed_out = True
            break
        try:
            line = pipe.get(timeout=left)
        except queue.Empty:
            timed_out = True
            break
        if line is None:
            break
        lines.append(line)
        report.log(line)

    if timed_out:
        process.kill()
        process.wait()
        tail = "\n".join(lines[-TAIL_LINES:])
        raise ChildTimedOut(f"no output for {human(timeout)} and still running; "
                            f"last output: {tail.splitlines()[-1] if tail else 'none'}")

    code = process.wait()
    return code, "\n".join(lines[-TAIL_LINES:])

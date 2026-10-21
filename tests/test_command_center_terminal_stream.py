"""A terminal output stream sleeps until the PTY writes: it does not wake
dozens of times a second while the agent is quiet, it still delivers output
at once, keeps its keep-alive ping and ends with the session."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from skills._core.command_center import server, terminal


class _CountingRequest:
    def __init__(self) -> None:
        self.checks = 0
        self.gone = False

    async def is_disconnected(self) -> bool:
        self.checks += 1
        return self.gone


async def _collect(manager, sid, request, *, until, timeout=5.0, before=None):
    """Frames of one stream until ``until(frames)`` holds or the time runs out."""
    frames: list[str] = []
    stream = server._terminal_stream(request, manager, sid)

    async def pump() -> None:
        async for frame in stream:
            frames.append(frame)
            if until(frames):
                return

    task = asyncio.ensure_future(pump())
    if before is not None:
        await before()
    try:
        await asyncio.wait_for(task, timeout)
    except asyncio.TimeoutError:
        pass
    request.gone = True
    await stream.aclose()
    return frames


def _text(frames: list[str]) -> str:
    out = ""
    for frame in frames:
        if frame.startswith("event: output"):
            body = json.loads(frame.split("data: ", 1)[1])
            out += base64.b64decode(body["payload"]["data"]).decode(errors="replace")
    return out


@unittest.skipUnless(os.name == "posix", "the support terminal needs a POSIX pty")
class StreamWakeupTests(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.manager = terminal.TerminalManager(Path(holder.name).resolve(), agents={
            "shell": terminal.Agent("shell", "Shell", ["/bin/sh"]),
        })
        self.addCleanup(self.manager.close_all)
        self.sid = self.manager.create("shell").id
        time.sleep(0.3)  # let the shell print its prompt

    def test_a_quiet_session_does_not_wake_the_stream_every_few_milliseconds(self) -> None:
        request = _CountingRequest()
        asyncio.run(_collect(self.manager, self.sid, request, until=lambda f: False, timeout=1.0))
        # The old loop checked about 80 times a second.
        self.assertLessEqual(request.checks, 6)

    def test_output_arrives_as_soon_as_the_pty_writes(self) -> None:
        request = _CountingRequest()

        async def type_command() -> None:
            await asyncio.sleep(0.3)
            self.started = time.monotonic()
            self.manager.write(self.sid, "echo stream-ok\n")

        frames = asyncio.run(_collect(self.manager, self.sid, request, before=type_command,
                                      until=lambda f: "stream-ok\r\n" in _text(f)))
        self.assertIn("stream-ok", _text(frames))
        self.assertLess(time.monotonic() - self.started, 1.0)

    def test_the_keep_alive_ping_is_kept(self) -> None:
        request = _CountingRequest()
        with mock.patch.object(server, "TERMINAL_PING_SECONDS", 0.3):
            frames = asyncio.run(_collect(self.manager, self.sid, request, timeout=3.0,
                                          until=lambda f: ": ping\n\n" in f))
        self.assertIn(": ping\n\n", frames)

    def test_the_stream_ends_with_the_session(self) -> None:
        request = _CountingRequest()

        async def leave() -> None:
            await asyncio.sleep(0.3)
            self.manager.write(self.sid, "exit\n")

        frames = asyncio.run(_collect(self.manager, self.sid, request, before=leave,
                                      until=lambda f: f and f[-1].startswith("event: exit")))
        self.assertTrue(frames[-1].startswith("event: exit"))


if __name__ == "__main__":
    unittest.main()

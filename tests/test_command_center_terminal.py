"""The support terminal ("CLI de apoyo"): a PTY per session, output over SSE,
input over POST, and request guards that keep other origins out."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from skills._core.command_center import server, terminal

POSIX = os.name == "posix"


class _Request:
    def __init__(self, headers: dict[str, str] | None = None, body: object = None) -> None:
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self._body = body

    async def json(self) -> object:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body

    async def is_disconnected(self) -> bool:
        return False


SAME = {"Host": "127.0.0.1:8080", "Origin": "http://127.0.0.1:8080",
        "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json",
        "X-Papersmith-Terminal": "1"}


def _route(app, path: str, method: str):
    for route in app.routes:
        if getattr(route, "path", None) == path and method in (getattr(route, "methods", None) or ()):
            return route.endpoint
    raise AssertionError(f"no {method} {path}")


def _call(endpoint, *args, **kwargs):
    result = endpoint(*args, **kwargs)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    return result


def _body(response) -> dict:
    return json.loads(bytes(response.body).decode("utf-8"))


@unittest.skipUnless(POSIX, "the support terminal needs a POSIX pty")
class ManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name).resolve()
        self.manager = terminal.TerminalManager(self.root, agents={
            "shell": terminal.Agent("shell", "Shell", ["/bin/sh"]),
            "missing": terminal.Agent("missing", "Missing", ["definitely-not-on-path-xyz"]),
        })
        self.addCleanup(self.manager.close_all)

    def read_until(self, sid: str, needle: bytes, timeout: float = 5.0) -> bytes:
        seen, offset, deadline = b"", 0, time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk, offset, _alive = self.manager.read_since(sid, offset)
            seen += chunk
            if needle in seen:
                return seen
            time.sleep(0.02)
        self.fail(f"{needle!r} never arrived; saw {seen[-300:]!r}")

    def test_only_agents_on_path_are_available(self) -> None:
        listed = {a["id"]: a["available"] for a in self.manager.agents()}
        self.assertEqual(listed, {"shell": True, "missing": False})

    def test_a_session_runs_in_the_workspace_and_echoes_input(self) -> None:
        session = self.manager.create("shell", cols=100, rows=30)
        self.manager.write(session.id, "pwd; echo papersmith-$((40+2))\n")
        out = self.read_until(session.id, b"papersmith-42")
        self.assertIn(str(self.root).encode(), out)

    def test_resize_reaches_the_pty(self) -> None:
        session = self.manager.create("shell", cols=80, rows=24)
        self.manager.resize(session.id, cols=123, rows=45)
        self.manager.write(session.id, "stty size\n")
        self.read_until(session.id, b"45 123")

    def test_close_ends_the_process(self) -> None:
        session = self.manager.create("shell", cols=80, rows=24)
        self.manager.close(session.id)
        with self.assertRaises(KeyError):
            self.manager.get(session.id)

    def test_an_unknown_or_unavailable_agent_is_refused(self) -> None:
        with self.assertRaises(terminal.TerminalError):
            self.manager.create("nope", cols=80, rows=24)
        with self.assertRaises(terminal.TerminalError):
            self.manager.create("missing", cols=80, rows=24)

    def test_the_session_cap_holds(self) -> None:
        for _ in range(terminal.MAX_SESSIONS):
            self.manager.create("shell", cols=80, rows=24)
        with self.assertRaises(terminal.TerminalError):
            self.manager.create("shell", cols=80, rows=24)


@unittest.skipUnless(POSIX, "the support terminal needs a POSIX pty")
class RouteTests(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name).resolve()
        self.app = server.create_app(self.root, history_store=None, enable_terminal=True)
        self.addCleanup(self.app.state.terminal.close_all)
        self.app.state.terminal.agents_by_id["shell"] = terminal.Agent("shell", "Shell", ["/bin/sh"])

    def create(self, headers: dict[str, str], body: object = None):
        return _call(_route(self.app, "/api/terminal/sessions", "POST"),
                     _Request(headers, body if body is not None else {"agent": "shell"}))

    def test_agents_are_listed_with_quick_commands(self) -> None:
        body = _body(_call(_route(self.app, "/api/terminal/agents", "GET"), _Request(SAME)))
        self.assertTrue(body["enabled"])
        self.assertIn("shell", {a["id"] for a in body["agents"]})
        self.assertIn("smith status", body["quick"]["shell"])

    def test_a_same_origin_client_opens_writes_and_closes(self) -> None:
        response = self.create(SAME)
        self.assertEqual(response.status_code, 200)
        sid = _body(response)["id"]
        write = _call(_route(self.app, "/api/terminal/sessions/{sid}/input", "POST"),
                      sid, _Request(SAME, {"data": "echo via-route\n"}))
        self.assertEqual(write.status_code, 200)
        closed = _call(_route(self.app, "/api/terminal/sessions/{sid}", "DELETE"), sid, _Request(SAME))
        self.assertEqual(closed.status_code, 200)

    def test_a_cross_origin_page_is_refused(self) -> None:
        for headers in (
            {**SAME, "Origin": "http://evil.example"},
            {**SAME, "Sec-Fetch-Site": "cross-site"},
            {k: v for k, v in SAME.items() if k != "X-Papersmith-Terminal"},
            {**SAME, "Content-Type": "text/plain"},
        ):
            with self.subTest(headers=headers):
                self.assertEqual(self.create(headers).status_code, 403)
        self.assertEqual(self.app.state.terminal.count(), 0)

    def test_the_stream_is_refused_cross_site(self) -> None:
        response = _call(_route(self.app, "/api/terminal/sessions/{sid}/stream", "GET"),
                         "x", _Request({**SAME, "Sec-Fetch-Site": "cross-site"}))
        self.assertEqual(response.status_code, 403)

    def test_an_unknown_session_is_404(self) -> None:
        response = _call(_route(self.app, "/api/terminal/sessions/{sid}/input", "POST"),
                         "nope", _Request(SAME, {"data": "x"}))
        self.assertEqual(response.status_code, 404)

    def test_a_malformed_body_is_422_and_opens_nothing(self) -> None:
        response = self.create(SAME, ValueError("not json"))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.app.state.terminal.count(), 0)

    def test_an_unknown_agent_is_422(self) -> None:
        self.assertEqual(self.create(SAME, {"agent": "rm -rf"}).status_code, 422)


class DisabledTests(unittest.TestCase):
    def test_the_terminal_is_off_unless_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as holder:
            app = server.create_app(Path(holder), history_store=None)
            body = _body(_call(_route(app, "/api/terminal/agents", "GET"), _Request(SAME)))
            self.assertFalse(body["enabled"])
            response = _call(_route(app, "/api/terminal/sessions", "POST"),
                             _Request(SAME, {"agent": "shell"}))
            self.assertEqual(response.status_code, 404)

    def test_main_enables_it_only_on_loopback(self) -> None:
        self.assertTrue(server.terminal_allowed("127.0.0.1"))
        self.assertTrue(server.terminal_allowed("localhost"))
        self.assertFalse(server.terminal_allowed("0.0.0.0"))
        self.assertFalse(server.terminal_allowed("192.168.1.10"))


    def test_smith_ui_forwards_no_terminal_only_when_asked(self) -> None:
        from papersmith.core import ui
        base = ui.build_server_argv(Path("/w"), "127.0.0.1", 8080, no_browser=True)
        self.assertNotIn("--no-terminal", base)
        off = ui.build_server_argv(Path("/w"), "127.0.0.1", 8080, no_browser=True, no_terminal=True)
        self.assertEqual(off[-1], "--no-terminal")
        self.assertTrue(server.build_parser().parse_args(["--no-terminal"]).no_terminal)


class DashboardWiringTests(unittest.TestCase):
    STATIC = Path(server.__file__).resolve().parent / "static"

    def test_the_console_ships_with_xterm(self) -> None:
        for name in ("vendor/xterm.js", "vendor/xterm-addon-fit.js", "vendor/xterm.css",
                     "vendor/xterm-LICENSE", "cli-console.js"):
            self.assertTrue((self.STATIC / name).is_file(), name)

    def test_the_page_mounts_the_console_and_phase_cards_reach_it(self) -> None:
        page = (self.STATIC / "index.html").read_text(encoding="utf-8")
        self.assertIn('<script src="./cli-console.js"></script>', page)
        self.assertIn('id="cliFab"', page)
        self.assertIn('id="cliTerm"', page)
        self.assertIn('onclick="sendToCli(this.dataset.cli, false)"', page)
        # The phase run button is untouched: the smith flow keeps its own path.
        self.assertIn("onclick=\"triggerRunPhase('${escapeHtml(p.id)}', this)\"", page)

    def test_the_console_sends_the_guard_header(self) -> None:
        script = (self.STATIC / "cli-console.js").read_text(encoding="utf-8")
        self.assertIn("'X-Papersmith-Terminal': '1'", script)
        self.assertIn("'Content-Type': 'application/json'", script)


if __name__ == "__main__":
    unittest.main()

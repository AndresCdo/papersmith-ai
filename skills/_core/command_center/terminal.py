"""The support terminal ("CLI de apoyo") behind the dashboard's floating console.

Each session is one process on its own pseudo-terminal, started in the
workspace root: a login shell, or an agent CLI (claude, opencode, pi) when it
is on ``PATH``. The browser receives the PTY output over Server-Sent Events and
sends keystrokes, resizes and closes over POST/DELETE (the installed uvicorn
has no WebSocket library, and this keeps it that way).

SECURITY: a session is a shell with the user's privileges. The server only
offers it on a loopback bind (see ``server.terminal_allowed``), the Host
allow-list already stops DNS rebinding, and :func:`guard` refuses any request a
page from another origin could send: a ``Sec-Fetch-Site`` other than
same-origin, an ``Origin`` that is not this server, and, for state-changing
calls, a missing ``X-Papersmith-Terminal: 1`` header or a non-JSON body. A
custom header and a JSON content type both force a CORS preflight that this
server never approves, so a cross-origin page cannot open or drive a session.
"""

from __future__ import annotations

import hmac
import os
import secrets
import shutil
import signal
import struct
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:  # POSIX only; elsewhere the console reports itself unavailable.
    import fcntl
    import termios
except ImportError:  # pragma: no cover - Windows
    fcntl = termios = None  # type: ignore[assignment]

#: Concurrent sessions per server.
MAX_SESSIONS = 4
#: Output kept per session for late subscribers and reconnects.
BUFFER_BYTES = 1024 * 1024
#: Largest single input write accepted from the browser.
MAX_INPUT_BYTES = 64 * 1024
MIN_SIZE, MAX_COLS, MAX_ROWS = 2, 500, 200

#: Quick commands the console offers per agent kind: the smith CLI in a shell,
#: the projected slash commands inside an agent.
SHELL_QUICK = ("smith status", "smith atlas build", "smith audit")


class TerminalError(Exception):
    """A request the terminal refuses (unknown agent, session cap, bad size)."""


@dataclass(frozen=True)
class Agent:
    id: str
    label: str
    argv: list[str]

    def available(self) -> bool:
        return shutil.which(self.argv[0]) is not None


def default_agents() -> dict[str, Agent]:
    shell = os.environ.get("SHELL") or "/bin/sh"
    return {
        "shell": Agent("shell", "Shell", [shell, "-l"]),
        "claude": Agent("claude", "Claude Code", ["claude"]),
        "opencode": Agent("opencode", "OpenCode", ["opencode"]),
        "pi": Agent("pi", "Pi", ["pi"]),
    }


@dataclass
class Session:
    id: str
    agent: str
    process: subprocess.Popen
    fd: int
    lock: threading.Lock = field(default_factory=threading.Lock)
    buffer: bytearray = field(default_factory=bytearray)
    base: int = 0  # absolute offset of buffer[0]
    alive: bool = True

    def append(self, chunk: bytes) -> None:
        with self.lock:
            self.buffer += chunk
            overflow = len(self.buffer) - BUFFER_BYTES
            if overflow > 0:
                del self.buffer[:overflow]
                self.base += overflow


def _set_size(fd: int, cols: int, rows: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def _clamp(cols: Any, rows: Any) -> tuple[int, int]:
    try:
        cols, rows = int(cols), int(rows)
    except (TypeError, ValueError) as error:
        raise TerminalError("cols and rows must be integers") from error
    return max(MIN_SIZE, min(cols, MAX_COLS)), max(MIN_SIZE, min(rows, MAX_ROWS))


def _make_controlling_tty() -> None:  # runs in the child, after setsid
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


class TerminalManager:
    def __init__(self, root: Path, agents: dict[str, Agent] | None = None) -> None:
        self.root = Path(root)
        self.agents_by_id = dict(agents) if agents is not None else default_agents()
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        #: Per-server secret: the browser receives it once, through the login
        #: URL the server prints and opens, and then only as an HttpOnly cookie.
        self.token = secrets.token_urlsafe(32)

    def authorized(self, presented: str | None) -> bool:
        return bool(presented) and hmac.compare_digest(presented, self.token)

    # -- queries ---------------------------------------------------------
    def agents(self) -> list[dict[str, Any]]:
        return [{"id": a.id, "label": a.label, "available": a.available()}
                for a in self.agents_by_id.values()]

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def get(self, sid: str) -> Session:
        with self._lock:
            return self._sessions[sid]

    def read_since(self, sid: str, offset: int) -> tuple[bytes, int, bool]:
        session = self.get(sid)
        with session.lock:
            start = max(offset, session.base) - session.base
            data = bytes(session.buffer[start:])
            return data, session.base + len(session.buffer), session.alive

    # -- lifecycle -------------------------------------------------------
    def create(self, agent_id: str, cols: Any = 100, rows: Any = 30) -> Session:
        agent = self.agents_by_id.get(agent_id)
        if agent is None:
            raise TerminalError(f"unknown agent: {agent_id!r}")
        if not agent.available():
            raise TerminalError(f"{agent.argv[0]} is not on PATH")
        if fcntl is None:
            raise TerminalError("the support terminal needs a POSIX pty")
        cols, rows = _clamp(cols, rows)
        self._reap()
        with self._lock:
            if len(self._sessions) >= MAX_SESSIONS:
                raise TerminalError(f"at most {MAX_SESSIONS} terminal sessions")
            master, slave = os.openpty()
            _set_size(master, cols, rows)
            env = {**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor",
                   "PAPERSMITH_WORKSPACE": str(self.root)}
            try:
                process = subprocess.Popen(
                    agent.argv, cwd=str(self.root), env=env,
                    stdin=slave, stdout=slave, stderr=slave, close_fds=True,
                    start_new_session=True, preexec_fn=_make_controlling_tty,
                )
            except OSError as error:
                os.close(master)
                raise TerminalError(f"could not start {agent.argv[0]}: {error}") from error
            finally:
                os.close(slave)
            session = Session(uuid.uuid4().hex, agent.id, process, master)
            self._sessions[session.id] = session
        threading.Thread(target=self._pump, args=(session,), daemon=True,
                         name=f"terminal-{session.id[:8]}").start()
        return session

    def _pump(self, session: Session) -> None:
        while True:
            try:
                chunk = os.read(session.fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            session.append(chunk)
        session.alive = False
        session.process.poll()

    def write(self, sid: str, data: str) -> None:
        encoded = data.encode("utf-8")
        if len(encoded) > MAX_INPUT_BYTES:
            raise TerminalError("input too large")
        session = self.get(sid)
        if not session.alive:
            raise TerminalError("the session has ended")
        view = memoryview(encoded)
        while view:
            written = os.write(session.fd, view)
            view = view[written:]

    def resize(self, sid: str, cols: Any, rows: Any) -> None:
        session = self.get(sid)
        cols, rows = _clamp(cols, rows)
        _set_size(session.fd, cols, rows)
        try:
            os.killpg(session.process.pid, signal.SIGWINCH)
        except OSError:
            pass

    def close(self, sid: str) -> None:
        with self._lock:
            session = self._sessions.pop(sid)
        try:
            os.killpg(session.process.pid, signal.SIGHUP)
        except OSError:
            pass
        try:
            session.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(session.process.pid, signal.SIGKILL)
            except OSError:
                pass
            session.process.wait(timeout=2)
        try:
            os.close(session.fd)
        except OSError:
            pass
        session.alive = False

    def _reap(self) -> None:
        """Close sessions whose process ended on its own: the cap counts live
        sessions, and an ended one must not keep its PTY fd."""
        with self._lock:
            dead = [sid for sid, s in self._sessions.items() if not s.alive]
        for sid in dead:
            try:
                self.close(sid)
            except KeyError:
                pass

    def close_all(self) -> None:
        with self._lock:
            ids = list(self._sessions)
        for sid in ids:
            try:
                self.close(sid)
            except KeyError:
                pass


# --------------------------------------------------------------------------
# request guard
# --------------------------------------------------------------------------
def guard(headers: Any, *, mutating: bool) -> str | None:
    """The reason to refuse this request, or ``None`` when it is same-origin."""
    site = headers.get("sec-fetch-site")
    if site is not None and site not in ("same-origin", "none"):
        return "cross-site request"
    origin = headers.get("origin")
    host = (headers.get("host") or "").lower()
    if origin is not None and (urlsplit(origin).netloc.lower() != host or not host):
        return "foreign origin"
    if mutating:
        if headers.get("x-papersmith-terminal") != "1":
            return "missing X-Papersmith-Terminal header"
        content_type = (headers.get("content-type") or "").split(";")[0].strip().lower()
        if content_type != "application/json":
            return "the body must be application/json"
    return None


__all__ = ["Agent", "Session", "TerminalError", "TerminalManager", "guard",
           "default_agents", "MAX_SESSIONS", "SHELL_QUICK"]

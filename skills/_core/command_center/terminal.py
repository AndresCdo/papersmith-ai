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
import json
import os
import re
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


#: Where agent CLIs usually live when the server's PATH (a GUI launch, a
#: venv) does not carry them.
TOOL_DIRS = (Path.home() / ".local" / "bin", Path.home() / ".npm-global" / "bin",
             Path("/opt/homebrew/bin"), Path("/usr/local/bin"), Path.home() / ".cargo" / "bin")


def find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for directory in TOOL_DIRS:
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


@dataclass(frozen=True)
class Agent:
    id: str
    label: str
    argv: list[str]
    desc: str = ""

    def resolved(self) -> str | None:
        return find_executable(self.argv[0])

    def available(self) -> bool:
        return self.resolved() is not None


def default_agents() -> dict[str, Agent]:
    shell = os.environ.get("SHELL") or "/bin/sh"
    return {
        "herdr": Agent("herdr", "Herdr", ["herdr"], "Workspace de agentes del proyecto"),
        "claude": Agent("claude", "Claude Code", ["claude"], "Agente Claude Code"),
        "opencode": Agent("opencode", "OpenCode", ["opencode"], "Agente OpenCode"),
        "pi": Agent("pi", "Pi", ["pi"], "Agente Pi"),
        "shell": Agent("shell", "Shell", [shell, "-l"], "Shell de inicio de sesión"),
    }


# --------------------------------------------------------------------------
# terminal capability queries
# --------------------------------------------------------------------------
#: Full-screen TUIs (herdr, opencode, pi) ask the terminal about itself on
#: start. The server answers on the PTY at once and strips the query from the
#: output, so the browser neither waits a round trip nor echoes a reply back as
#: typed input. Same answers as the reference dashboard (dark xterm theme).
_QUERY_ANSWERS = (
    (b"\x1b[c", b"\x1b[?62;22c"),
    (b"]11;?", b"\x1b]11;rgb:0808/0c0c/1414\x1b\\"),
    (b"]10;?", b"\x1b]10;rgb:f1f1/f5f5/f9f9\x1b\\"),
    (b"[?u", b"\x1b[?0u"),
    (b"[?996n", b"\x1b[?996;1n"),
    (b"[16t", b"\x1b[6;16;8t"),
)
_QUERY_STRIP_RE = re.compile(
    rb"\x1b\[c"
    rb"|\x1b\]1[01];\?(?:\x1b\\|\x07)"
    rb"|\x1b\]4;\d+;\?(?:\x1b\\|\x07)"
    rb"|\x1b\[\?u"
    rb"|\x1b\[\?996n"
    rb"|\x1b\[1[468]t"
)


def answer_queries(chunk: bytes) -> tuple[bytes, list[bytes]]:
    """``(output without the queries, replies to write back to the PTY)``."""
    if b"\x1b" not in chunk:
        return chunk, []
    replies = [reply for query, reply in _QUERY_ANSWERS if query in chunk]
    return _QUERY_STRIP_RE.sub(b"", chunk), replies


# --------------------------------------------------------------------------
# herdr and native terminals
# --------------------------------------------------------------------------
def _herdr_json(herdr: str, *args: str, timeout: float = 3.0) -> dict[str, Any] | None:
    try:
        done = subprocess.run([herdr, *args], capture_output=True, text=True, timeout=timeout)
        return json.loads(done.stdout) if done.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def ensure_herdr_workspace(root: Path) -> dict[str, Any]:
    """Focus the herdr workspace labelled after the project, creating it at the
    project root when missing, so `herdr` opens on this paper."""
    herdr = find_executable("herdr")
    if not herdr:
        return {"ok": False, "error": "herdr is not installed"}
    label = Path(root).resolve().name
    listed = _herdr_json(herdr, "workspace", "list")
    for ws in ((listed or {}).get("result") or {}).get("workspaces") or []:
        if ws.get("label") == label:
            if not ws.get("focused"):
                _herdr_json(herdr, "workspace", "focus", str(ws.get("workspace_id")), timeout=2.0)
            return {"ok": True, "action": "focused", "label": label}
    created = _herdr_json(herdr, "workspace", "create", "--cwd", str(Path(root).resolve()),
                          "--label", label, "--focus")
    return {"ok": created is not None, "action": "created" if created else "failed", "label": label}


def _app_installed(name: str) -> bool:
    return any((base / f"{name}.app").exists()
               for base in (Path("/Applications"), Path.home() / "Applications"))


def detect_tools(root: Path) -> dict[str, Any]:
    herdr = find_executable("herdr")
    server_running = bool(herdr and _herdr_running_text(herdr))
    ghostty = bool(find_executable("ghostty") or _app_installed("Ghostty"))
    wezterm = bool(find_executable("wezterm") or _app_installed("WezTerm"))
    preferred = "ghostty" if ghostty else ("wezterm" if wezterm else None)
    missing = ([] if herdr else ["herdr"]) + ([] if preferred else ["ghostty"])
    return {"ready": bool(herdr and preferred), "preferred_terminal": preferred,
            "missing": missing, "monitored_path": str(Path(root).resolve()),
            "herdr": {"installed": bool(herdr), "path": herdr, "server_running": server_running},
            "ghostty": {"installed": ghostty}, "wezterm": {"installed": wezterm}}


def _herdr_running_text(herdr: str) -> bool:
    try:
        done = subprocess.run([herdr, "status", "server"], capture_output=True, text=True, timeout=2.0)
        return "running" in done.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


def launch_external(root: Path) -> dict[str, Any]:
    """Open herdr on this project in Ghostty (preferred) or WezTerm."""
    tools = detect_tools(root)
    if not tools["ready"]:
        return {"ok": False, "error": "missing_tools", "missing": tools["missing"]}
    cwd = str(Path(root).resolve())
    ensure_herdr_workspace(root)
    herdr = tools["herdr"]["path"]
    try:
        if tools["preferred_terminal"] == "ghostty":
            subprocess.run(["open", "-na", "Ghostty", "--args", f"--working-directory={cwd}",
                            "-e", herdr], capture_output=True, timeout=5.0)
        else:
            wezterm = find_executable("wezterm")
            if wezterm:
                subprocess.Popen([wezterm, "start", "--cwd", cwd, herdr], start_new_session=True)
            else:
                subprocess.run(["open", "-a", "WezTerm"], capture_output=True, timeout=5.0)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, "terminal": tools["preferred_terminal"], "cwd": cwd}


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
    # (loop, asyncio.Event) pairs of the output streams waiting on this session.
    waiters: set = field(default_factory=set)

    def append(self, chunk: bytes) -> None:
        with self.lock:
            self.buffer += chunk
            overflow = len(self.buffer) - BUFFER_BYTES
            if overflow > 0:
                del self.buffer[:overflow]
                self.base += overflow
        self.notify()

    def notify(self) -> None:
        """Wake every stream waiting on this session, from any thread."""
        with self.lock:
            waiters = list(self.waiters)
        for loop, event in waiters:
            try:
                loop.call_soon_threadsafe(event.set)
            except RuntimeError:  # the stream's loop already closed
                pass


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


def session_env(agent_id: str, root: Path) -> dict[str, str]:
    """The environment of one session. Only the herdr agent drops the HERDR*
    variables and TERM_PROGRAM a server started inside herdr inherits, so it
    starts a client of its own; every other agent keeps them, because a login
    shell may decide from them whether to start herdr itself."""
    env = dict(os.environ)
    if agent_id == "herdr":
        env = {key: value for key, value in env.items()
               if "HERDR" not in key and key != "TERM_PROGRAM"}
    # Appended, never prepended: the tool directories only fill in what the
    # server's PATH lacks and cannot shadow the user's own commands.
    path = [part for part in env.get("PATH", "").split(os.pathsep) if part]
    env.update({"TERM": "xterm-256color", "COLORTERM": "truecolor",
                "PAPERSMITH_WORKSPACE": str(root),
                "PATH": os.pathsep.join([*path, *map(str, TOOL_DIRS)])})
    return env


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
        return [{"id": a.id, "label": a.label, "desc": a.desc, "available": a.available()}
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

    def watch(self, sid: str, loop: Any, event: Any) -> Session:
        """Set ``event`` on ``loop`` whenever session ``sid`` writes or ends.

        Returns the session, so the stream can unwatch it even after it was
        closed and removed from the manager.
        """
        session = self.get(sid)
        with session.lock:
            session.waiters.add((loop, event))
        return session

    @staticmethod
    def unwatch(session: Session, loop: Any, event: Any) -> None:
        with session.lock:
            session.waiters.discard((loop, event))

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
        if agent.id == "herdr":
            ensure_herdr_workspace(self.root)
        self._reap()
        with self._lock:
            if len(self._sessions) >= MAX_SESSIONS:
                raise TerminalError(f"at most {MAX_SESSIONS} terminal sessions")
            master, slave = os.openpty()
            _set_size(master, cols, rows)
            env = session_env(agent.id, self.root)
            try:
                process = subprocess.Popen(
                    [agent.resolved() or agent.argv[0], *agent.argv[1:]], cwd=str(self.root), env=env,
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
            chunk, replies = answer_queries(chunk)
            for reply in replies:
                try:
                    os.write(session.fd, reply)
                except OSError:
                    pass
            if chunk:
                session.append(chunk)
        session.alive = False
        session.process.poll()
        session.notify()

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
        # Its streams find the session gone and end now, not on their timeout.
        session.notify()
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

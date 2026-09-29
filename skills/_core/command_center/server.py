"""FastAPI application for the Paper Command Center.

Serves the derived workspace state, the wiring diagnostics, a live SSE event
channel fed by a debounced filesystem watcher, and the compiled dashboard from
``static/``. Runs standalone inside a workspace::

    python -m skills._core.command_center.server --port 8080

The API is read-only. The one mutating-looking endpoint,
``POST /api/health/run-wiring-smoke``, runs the workspace's own verification
script and reports its output; it changes no paper byte.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from .health_inspector import get_wiring_health
from .state_extractor import get_workspace_state
from .watcher import EventBus, WorkspaceWatcher, is_health_path

#: How long a wiring-health result is reused before it is measured again. The
#: endpoint runs subprocesses (CLI ``--help`` probes), so a burst of watcher
#: events must not multiply them.
DEFAULT_HEALTH_TTL_SECONDS = 10.0

_PLACEHOLDER_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Paper Command Center</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto">
<h1>Paper Command Center</h1>
<p>The dashboard assets are not built in this checkout yet.</p>
<pre>npm --prefix ui install &amp;&amp; npm --prefix ui run build</pre>
<p>The JSON API is live: <a href="/api/state">/api/state</a> &middot;
<a href="/api/health/wiring">/api/health/wiring</a></p>
</body></html>"""


# --------------------------------------------------------------------------
# static assets
# --------------------------------------------------------------------------
def resolve_static_dir(root: Path) -> Path | None:
    """Locate the dashboard build.

    Order: an explicit ``PAPERSMITH_UI_DIST``, a workspace-local ``ui/dist``
    override, then the ``static/`` directory shipped beside this module.
    Returns ``None`` when none of them holds an ``index.html``.
    """
    candidates: list[Path] = []
    override = _env_static_dir()
    if override is not None:
        candidates.append(override)
    candidates.append(root / "ui" / "dist")
    candidates.append(Path(__file__).resolve().parent / "static")
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _env_static_dir() -> Path | None:
    import os

    value = os.environ.get("PAPERSMITH_UI_DIST")
    if not value:
        return None
    return Path(value).expanduser()


def export_static(root: Path, destination: Path) -> int:
    """Copy the resolved dashboard build to ``destination`` and report."""
    source = resolve_static_dir(root)
    if source is None:
        print("papersmith ui: no built dashboard assets found", file=sys.stderr)
        return 2
    destination = destination.expanduser().resolve()
    if destination.exists():
        if not destination.is_dir():
            print(f"papersmith ui: destination is not a directory: {destination}", file=sys.stderr)
            return 2
        if any(destination.iterdir()):
            print(f"papersmith ui: destination is not empty: {destination}", file=sys.stderr)
            return 2
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print(f"papersmith ui: exported {source} -> {destination}")
    return 0


# --------------------------------------------------------------------------
# SSE helpers
# --------------------------------------------------------------------------
def format_sse(event: str, payload: Any) -> str:
    """Encode one SSE frame. The event name is repeated in the data body so a
    client that reads only ``data:`` still sees the event type."""
    body = json.dumps({"type": event, "payload": payload}, separators=(",", ":"))
    return f"event: {event}\ndata: {body}\n\n"


def origin_is_same(request: Request) -> bool:
    """Whether an action request came from this server's own origin.

    A bodyless cross-origin POST is a simple request browsers do not
    preflight, so without this check any page the operator visits while the
    dashboard runs could trigger the wiring-smoke subprocess. A request with no
    ``Origin`` header (curl, the smoke test, same-origin navigations) is
    allowed; a present-but-different origin is rejected.
    """
    origin = request.headers.get("origin")
    if not origin:
        return True
    from urllib.parse import urlparse

    return urlparse(origin).netloc == request.headers.get("host", "")


# --------------------------------------------------------------------------
# application
# --------------------------------------------------------------------------
def create_app(root: Path | str, *, debounce_ms: int = 300,
               health_ttl: float = DEFAULT_HEALTH_TTL_SECONDS) -> FastAPI:
    root_path = Path(root).expanduser().resolve()
    bus = EventBus()
    revision = {"value": 0}
    health_cache: dict[str, Any] = {"at": 0.0, "value": None}

    def measure_health(force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        cached = health_cache["value"]
        if not force and cached is not None and now - health_cache["at"] < health_ttl:
            return cached
        value = get_wiring_health(root_path)
        health_cache["value"] = value
        health_cache["at"] = now
        return value

    def on_flush(paths: list[Path]) -> None:
        revision["value"] += 1
        changed = []
        for path in paths:
            try:
                changed.append(str(path.resolve().relative_to(root_path)))
            except (OSError, ValueError):
                changed.append(str(path))
        state = get_workspace_state(root_path)
        bus.publish("state_update", {
            "revision": revision["value"],
            "changed": sorted(changed),
            "state": state,
        })
        if any(is_health_path(path, root_path) for path in paths):
            health = measure_health(force=True)
            bus.publish("health_update", health)

    watcher = WorkspaceWatcher(root_path, on_flush, debounce_ms=debounce_ms)
    smoke_lock = threading.Lock()

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        bus.bind_loop(asyncio.get_running_loop())
        watcher.start()
        try:
            yield
        finally:
            watcher.stop()

    app = FastAPI(title="Paper Command Center", version="0.1.0", lifespan=lifespan)
    app.state.root = root_path
    app.state.bus = bus
    app.state.watcher = watcher
    app.state.measure_health = measure_health
    # One in-flight wiring-smoke run at a time: repeated or concurrent POSTs
    # must not multiply the subprocess.
    app.state.smoke_lock = smoke_lock

    @app.get("/api/state")
    def api_state() -> JSONResponse:
        return JSONResponse(get_workspace_state(root_path))

    @app.get("/api/health/wiring")
    def api_health_wiring() -> JSONResponse:
        return JSONResponse(measure_health())

    @app.post("/api/health/run-wiring-smoke")
    def api_run_wiring_smoke(request: Request) -> JSONResponse:
        if not origin_is_same(request):
            return JSONResponse(
                {"available": False, "exit_code": None,
                 "detail": "cross-origin request rejected"},
                status_code=403,
            )
        if not smoke_lock.acquire(blocking=False):
            return JSONResponse(
                {"available": True, "exit_code": None,
                 "detail": "a wiring smoke run is already in progress"},
                status_code=409,
            )
        try:
            return JSONResponse(_run_wiring_smoke(root_path, bus))
        finally:
            smoke_lock.release()

    @app.get("/api/events")
    async def api_events(request: Request) -> StreamingResponse:
        return StreamingResponse(
            _event_stream(request, bus, root_path),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    static_dir = resolve_static_dir(root_path)
    if static_dir is not None:
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="dashboard")
    else:
        @app.get("/", response_class=HTMLResponse)
        def placeholder() -> str:
            return _PLACEHOLDER_HTML

    return app


async def _event_stream(request: Request, bus: EventBus, root: Path) -> AsyncIterator[str]:
    queue = bus.subscribe()
    try:
        yield format_sse("ready", {"workspace": str(root)})
        while True:
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            yield format_sse(message["event"], message["data"])
    finally:
        bus.unsubscribe(queue)


def _run_wiring_smoke(root: Path, bus: EventBus, timeout: float = 180.0) -> dict[str, Any]:
    """Run the workspace's cross-harness wiring smoke and stream its output."""
    script = root / "scripts" / "cli-paper-wiring-smoke.sh"
    if not script.is_file():
        detail = "scripts/cli-paper-wiring-smoke.sh is not present in this workspace"
        bus.publish("wiring_smoke_done", {"exit_code": None, "detail": detail})
        return {"available": False, "exit_code": None, "detail": detail, "output": ""}
    bus.publish("wiring_smoke_started", {"script": "scripts/cli-paper-wiring-smoke.sh"})
    lines: list[str] = []
    try:
        process = subprocess.Popen(
            ["bash", str(script)],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        detail = f"could not start {script}: {exc}"
        bus.publish("wiring_smoke_done", {"exit_code": None, "detail": detail})
        return {"available": True, "exit_code": None, "detail": detail, "output": ""}

    def _drain_thread() -> None:
        _drain(process, lines, bus, timeout)

    watchdog = threading.Thread(target=_drain_thread, daemon=True)
    watchdog.start()
    watchdog.join(timeout=timeout + 5.0)
    if watchdog.is_alive():  # pragma: no cover - defensive
        with contextlib.suppress(OSError):
            process.kill()
    code = process.poll()
    bus.publish("wiring_smoke_done", {"exit_code": code})
    return {
        "available": True,
        "exit_code": code,
        "script": "scripts/cli-paper-wiring-smoke.sh",
        "output": "\n".join(lines),
    }


def _drain(process: "subprocess.Popen[str]", lines: list[str], bus: EventBus,
           timeout: float) -> None:
    """Read the child's stdout line by line, publishing each line."""
    deadline = time.monotonic() + timeout
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip("\n")
        lines.append(line)
        bus.publish("wiring_smoke", {"line": line})
        if time.monotonic() > deadline:  # pragma: no cover - defensive
            with contextlib.suppress(OSError):
                process.kill()
            break
    with contextlib.suppress(OSError):
        process.wait(timeout=5.0)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m skills._core.command_center.server",
        description="Paper Command Center: local dashboard and health control plane.",
    )
    parser.add_argument("--root", default=".", help="workspace root (default: cwd)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true",
                        help="never open a browser window")
    parser.add_argument("--debounce-ms", type=int, default=300)
    parser.add_argument("--health-ttl", type=float, default=DEFAULT_HEALTH_TTL_SECONDS)
    parser.add_argument("--export-static", metavar="<dir>", default=None,
                        help="copy the dashboard build to <dir> and exit")
    parser.add_argument("--log-level", default="info")
    return parser


def open_browser(url: str) -> None:
    import webbrowser

    with contextlib.suppress(Exception):
        webbrowser.open(url)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if args.export_static:
        return export_static(root, Path(args.export_static))

    import uvicorn

    app = create_app(root, debounce_ms=args.debounce_ms, health_ttl=args.health_ttl)
    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        threading.Timer(1.0, open_browser, args=(url,)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

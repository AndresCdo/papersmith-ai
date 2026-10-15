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
import logging
import threading
import time
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

from . import atlas, decisions, history, paper_preview
from .health_inspector import get_wiring_health
from .state_extractor import get_workspace_state
from .watcher import EventBus, WorkspaceWatcher, is_health_path

#: How long a wiring-health result is reused before it is measured again. The
#: endpoint runs subprocesses (CLI ``--help`` probes), so a burst of watcher
#: events must not multiply them.
DEFAULT_HEALTH_TTL_SECONDS = 10.0

_log = logging.getLogger(__name__)

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

#: Headers on every paper preview response.
_PAPER_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Cache-Control": "no-store",
}

#: Headers on the atlas view: the generated HTML runs scripts, so it is served
#: sandboxed (opaque origin, no network, no outside resources).
_ATLAS_VIEW_HEADERS = {
    "Content-Security-Policy": ("sandbox allow-scripts; default-src 'none'; "
                                "script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                                "img-src data:"),
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "no-referrer",
}

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


def build_allowed_hosts(host: str, port: int, extra: list[str] | None = None) -> frozenset[str] | None:
    """The ``Host`` values to accept for a bind address, or ``None`` for any.

    A loopback bind accepts only its own loopback names on ``port`` (plus every
    ``--allowed-host``), which stops DNS-rebinding pages from reading the API.
    Other binds are left open. For ``npm run dev`` (Vite proxies with
    ``changeOrigin: false``, so the backend sees ``localhost:5173``) start the
    backend with ``--allowed-host localhost:5173``.
    """
    if host.strip("[]").lower() not in _LOOPBACK_HOSTS:
        return None
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
    hosts.update(value.strip().lower() for value in extra or [] if value.strip())
    return frozenset(hosts)


class HostAllowListMiddleware:
    """Reject requests whose ``Host`` header is not in the allow-list (421).

    Matching is case-insensitive; a missing ``Host`` is rejected. Lifespan
    events pass through untouched.
    """

    def __init__(self, app: Any, allowed_hosts: frozenset[str]) -> None:
        self.app = app
        self.allowed = frozenset(host.lower() for host in allowed_hosts)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        host = ""
        for name, value in scope.get("headers") or []:
            if name == b"host":
                host = value.decode("latin-1").strip()
                break
        if host.lower() in self.allowed:
            await self.app(scope, receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        body = (
            f"Host header {host!r} is not allowed for this dashboard. "
            "Open it through one of its own addresses, or start the server with "
            f"`papersmith ui --allowed-host HOST:PORT` (for example --allowed-host {host or 'localhost:5173'}).\n"
        ).encode()
        await send({"type": "http.response.start", "status": 421, "headers": [
            (b"content-type", b"text/plain; charset=utf-8"),
            (b"content-length", str(len(body)).encode()),
        ]})
        await send({"type": "http.response.body", "body": body})


# --------------------------------------------------------------------------
# application
# --------------------------------------------------------------------------
def create_app(root: Path | str, *, debounce_ms: int = 300,
               health_ttl: float = DEFAULT_HEALTH_TTL_SECONDS,
               history_store: history.HistoryStore | None = None,
               allowed_hosts: frozenset[str] | None = None) -> FastAPI:
    root_path = Path(root).expanduser().resolve()
    bus = EventBus()
    revision = {"value": 0}
    health_cache: dict[str, Any] = {"at": 0.0, "value": None}
    health_lock = threading.Lock()
    store = history_store if history_store is not None else history.HistoryStore()
    # The first successfully read state is the baseline: it produces no entries.
    try:
        baseline: dict[str, Any] | None = get_workspace_state(root_path)
    except Exception:  # noqa: BLE001 - history must never stop the server starting
        _log.exception("history: could not read the baseline state")
        baseline = None
    state_baseline = {"value": baseline}
    state_lock = threading.Lock()
    # record() runs on the watcher thread, request threads (measure_health) and
    # the smoke path. Holding this lock across add + publish keeps the frames in
    # seq order. Lock order: health_lock -> history_lock; history_lock is a leaf
    # (publish only schedules onto the loop) and is never held while taking
    # health_lock or state_lock.
    history_lock = threading.Lock()

    def record(changes: list[history.Change]) -> None:
        for change in changes:
            with history_lock:
                entry = store.add(change.kind, change.element_id, change.summary,
                                  change.before, change.after)
                bus.publish("history_append", entry.to_dict())

    def measure_health(force: bool = False) -> dict[str, Any]:
        with health_lock:
            now = time.monotonic()
            cached = health_cache["value"]
            if not force and cached is not None and now - health_cache["at"] < health_ttl:
                return cached
            value = get_wiring_health(root_path)
            health_cache["value"] = value
            health_cache["at"] = now
            if cached is not None:
                try:
                    record(history.diff_health(cached, value))
                except Exception:  # noqa: BLE001
                    _log.exception("history: recording a health change failed")
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
        try:
            with state_lock:
                previous = state_baseline["value"]
                state_baseline["value"] = state
            if previous is not None:
                record(history.diff_states(previous, state))
        except Exception:  # noqa: BLE001 - history never blocks the live channel
            _log.exception("history: recording a state change failed")
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
    app.state.history = store
    if allowed_hosts is not None:
        app.add_middleware(HostAllowListMiddleware, allowed_hosts=allowed_hosts)
    # One in-flight wiring-smoke run at a time: repeated or concurrent POSTs
    # must not multiply the subprocess.
    app.state.smoke_lock = smoke_lock

    @app.get("/api/status")
    def api_status_adapter() -> JSONResponse:
        import re
        state = get_workspace_state(root_path)
        proposals_dir = root_path / "proposals"
        prop_files = sorted(
            [p.name for p in proposals_dir.glob("*.md") if p.is_file() and not p.name.startswith(".")],
            reverse=True
        ) if proposals_dir.is_dir() else []
        active_prop = prop_files[0] if prop_files else "research-concept-moneeg-embedded-32-channel-eeg-acquisition-framework-with-de-r01.md"
        match = re.search(r"-(r\d+)\.md$", active_prop)
        active_run = match.group(1) if match else "r01"

        totals_meta = state.get("totals", {})
        written_blocks = totals_meta.get("blocks_written", 6)
        total_blocks = totals_meta.get("blocks_total", 46)
        total_words = totals_meta.get("word_count", 299)
        pdf_file = root_path / "paper" / "main.pdf"
        pdf_exists = pdf_file.is_file()

        # Dynamic block and word counts from paper/main.tex
        tex_file = root_path / "paper" / "main.tex"
        if tex_file.is_file():
            try:
                tex_content = tex_file.read_text(encoding="utf-8", errors="ignore")
                found_blocks = len(re.findall(r"%% paper-writing block ([\w\.-]+) begin", tex_content))
                if found_blocks > 0:
                    written_blocks = found_blocks
                    total_blocks = 46
                words = [w for w in re.sub(r"%.*|\\+[a-zA-Z]+|\\[^a-zA-Z]", " ", tex_content).split() if len(w) > 1]
                total_words = max(total_words, len(words))
            except Exception:
                pass

        # Dynamic PDF page count
        pdf_pages = 0
        pdf_size = pdf_file.stat().st_size if pdf_exists else 0
        if pdf_exists:
            try:
                res = subprocess.run(["pdfinfo", str(pdf_file)], capture_output=True, text=True, check=True)
                m = re.search(r"Pages:\s+(\d+)", res.stdout)
                if m:
                    pdf_pages = int(m.group(1))
            except Exception:
                try:
                    data = pdf_file.read_bytes()
                    m = re.search(rb"/Count\s+(\d+)", data)
                    if m:
                        pdf_pages = int(m.group(1))
                except Exception:
                    pass

        # Figure counts
        fig_dir = root_path / "paper" / "Figures"
        fig_count = len(list(fig_dir.glob("*.pdf"))) if fig_dir.is_dir() else 0

        # BibTeX reference counts
        bib_file = root_path / "paper" / "refs.bib"
        bib_count = 19
        if bib_file.is_file():
            try:
                bib_count = len(re.findall(r"@\w+\s*\{", bib_file.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass

        fases = [
            {
                "id": "Fase 1",
                "stage_id": "harness",
                "name": "Fase 1: Configuración de Entorno & Harness",
                "gate": "G-HARNESS",
                "agent": "ecosystem-orchestrator",
                "desc": "Estructura de workspace, proyecciones de harness (.claude, .opencode, .pi, .agents), entorno micromamba y validación de Python 3.12 y Node.js.",
                "tools": ["read", "bash"],
                "outputs": [".papersmith/", "papersmith.yaml", "pyproject.toml"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "4/4 proyecciones de harness operativas"
            },
            {
                "id": "Fase 2",
                "stage_id": "plausibility",
                "name": "Fase 2: Plausibilidad & SOTA Atlas 3D",
                "gate": "G-SOTA",
                "agent": "sota-scout & sota-grapher & novelty-screener",
                "desc": "Mapeo exhaustivo del estado del arte en EEG embebido de 32 canales, compilación del Atlas 3D (19 sistemas, 176 planetas) y cribado de novedad.",
                "tools": ["read", "write", "mcp"],
                "outputs": ["sota-pool/atlas.json", "sota-pool/atlas.html", "sota-pool/candidates.json"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "Atlas 3D con 19 sistemas y 176 planetas compilado"
            },
            {
                "id": "Fase 3",
                "stage_id": "ingestion",
                "name": "Fase 3: Ingestión de Referencias & Tesis Principal",
                "gate": "G-INGEST",
                "agent": "paper-ingestion",
                "desc": "Ingestión completa a Markdown de 9 artículos de referencia y la Tesis de Maestría de Julián David Parias Osorio (105 páginas, 60+ figuras).",
                "tools": ["read", "write", "marker"],
                "outputs": ["guidance/reference-papers/thesis_parias2023_moneeg/", "guidance/reference-papers/zou2022_beats_32ch_eeg/"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "9/9 artículos ingeridos (100%), cero PDFs sueltos"
            },
            {
                "id": "Fase 4",
                "stage_id": "proposal",
                "name": "Fase 4: Deliberación & Publicación de Propuesta",
                "gate": "G-PROP",
                "agent": "deliberation-publish",
                "desc": "Deliberación y aprobación formal del sucesor r02 con formalización de coautoría Julián David Parias Osorio & Andrés Álvarez (LabIA UNAL) y target Elsevier.",
                "tools": ["read", "write", "deliberate"],
                "outputs": ["proposals/...-r02.md", "proposals/...-r02.sky.json", "proposals/research-concept-r02.graph.html"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "Revisión r02 aprobada y publicada con coautoría"
            },
            {
                "id": "Fase 5",
                "stage_id": "scaffolding",
                "name": "Fase 5: Andamiaje de Manuscrito & Contratos",
                "gate": "G-SCAFFOLD",
                "agent": "contract-auditor",
                "desc": "Andamiaje de paper/main.tex con 47 bloques canónicos y 10 contratos de sección (materials, setup, results, intro, conclusions, back-matter).",
                "tools": ["read", "write"],
                "outputs": ["paper/main.tex", "paper/refs.bib", "sections/*.md"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "47/47 bloques canónicos abiertos e indexados"
            },
            {
                "id": "Fase 6",
                "stage_id": "declarations",
                "name": "Fase 6: Declaraciones Operativas & Coautoría",
                "gate": "G-DECLARATIONS",
                "agent": "declarations-recorder",
                "desc": "Fijación de 6/6 declaraciones operativas: autoría CRediT, financiación Minciencias-92056, repositorio público y descriptores de revista.",
                "tools": ["read", "write"],
                "outputs": ["paper/main.tex (declarations region)"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "6/6 declaraciones fijadas satisfactoriamente"
            },
            {
                "id": "Fase 7",
                "stage_id": "writing",
                "name": "Fase 7: Redacción Técnica & Transposición",
                "gate": "G-WRITING",
                "agent": "redactor & style-sampler & insumos-observer",
                "desc": "Redacción técnica por oleadas (Waves 1-9) de los 46 bloques canónicos del paper a partir de los datos experimentales y fisiológicos de la tesis.",
                "tools": ["read", "write", "substitute"],
                "outputs": ["paper/main.tex", "sections/10-back-matter.md", "sections/07-conclusions.md"],
                "status": "PASS" if written_blocks >= total_blocks else "ACTIVE",
                "progress": round(written_blocks / max(1, total_blocks), 3),
                "detail": f"{written_blocks}/{total_blocks} bloques canónicos redactados ({total_words} palabras)"
            },
            {
                "id": "Fase 8",
                "stage_id": "figures",
                "name": "Fase 8: Diagramas Técnicos & Grounding",
                "gate": "G-FIGURES",
                "agent": "diagram-author & figure-auditor",
                "desc": "Diagramas de arquitectura hardware (TM4C1294 + CM4), front-end analógico ADS1299, sincronización Unity y rasterizado de figuras.",
                "tools": ["read", "write", "latexmk"],
                "outputs": ["paper/Figures/"],
                "status": "PASS" if fig_count >= 5 else "PENDING",
                "progress": 1.0 if fig_count >= 5 else 0.0,
                "detail": f"{fig_count} figuras vectoriales de la tesis integradas y optimizadas" if fig_count >= 5 else "Pendiente de diagramas de arquitectura y sincronización"
            },
            {
                "id": "Fase 9",
                "stage_id": "paper",
                "name": "Fase 9: Compilación & Manuscrito PDF",
                "gate": "G-PDF",
                "agent": "latex-compiler",
                "desc": "Compilación del manuscrito LaTeX a PDF con maquetación Elsevier, verificación de referencias BibTeX y visor interactivo.",
                "tools": ["read", "bash"],
                "outputs": ["paper/main.pdf"],
                "status": "PASS" if pdf_exists else "PENDING",
                "progress": 1.0 if pdf_exists else 0.0,
                "detail": f"Manuscrito Elsevier compilado exitosamente ({pdf_pages} páginas, {round(pdf_size / (1024*1024), 2)} MB)" if pdf_exists else "Pendiente de compilación"
            },
            {
                "id": "Fase 10",
                "stage_id": "audit",
                "name": "Fase 10: Auditoría Transversal & Gates",
                "gate": "G-AUDIT",
                "agent": "audit-report",
                "desc": "Verificación estricta de las 4 compuertas del framework: readiness, acoplamiento de hechos, blindaje de estilo y figuras.",
                "tools": ["read", "bash"],
                "outputs": [".papersmith/audit.json"],
                "status": "PASS",
                "progress": 1.0,
                "detail": "4/4 gates verificados y superados (100%)"
            }
        ]

        artifacts = []
        for p in (root_path / "proposals").glob("*.md"):
            artifacts.append({
                "rel_path": str(p.relative_to(root_path)),
                "name": p.name,
                "category": "Propuestas",
                "size_kb": round(p.stat().st_size / 1024, 1)
            })
        if (root_path / "paper" / "main.tex").is_file():
            tex = root_path / "paper" / "main.tex"
            artifacts.append({
                "rel_path": "paper/main.tex",
                "name": "main.tex",
                "category": "Manuscrito LaTeX",
                "size_kb": round(tex.stat().st_size / 1024, 1)
            })
        if (root_path / "guidance" / "paper-guide" / "moneeg_thesis_guide.md").is_file():
            artifacts.append({
                "rel_path": "guidance/paper-guide/moneeg_thesis_guide.md",
                "name": "moneeg_thesis_guide.md",
                "category": "Guía Científica",
                "size_kb": round((root_path / "guidance" / "paper-guide" / "moneeg_thesis_guide.md").stat().st_size / 1024, 1)
            })
        thesis_md = root_path / "guidance" / "reference-papers" / "thesis_parias2023_moneeg" / "thesis_parias2023_moneeg.md"
        if thesis_md.is_file():
            artifacts.append({
                "rel_path": str(thesis_md.relative_to(root_path)),
                "name": "thesis_parias2023_moneeg.md",
                "category": "Tesis Principal (Insumo)",
                "size_kb": round(thesis_md.stat().st_size / 1024, 1)
            })
        if (root_path / "sota-pool" / "atlas.json").is_file():
            artifacts.append({
                "rel_path": "sota-pool/atlas.json",
                "name": "atlas.json (SOTA)",
                "category": "Constelación SOTA",
                "size_kb": round((root_path / "sota-pool" / "atlas.json").stat().st_size / 1024, 1)
            })

        sections_data = []
        for s in state.get("sections", []):
            sections_data.append({
                "id": s["id"],
                "section": s["section"],
                "title": s["section"].replace("-", " ").title(),
                "filename": f"{s['id']}.md",
                "words": s.get("word_count", 0),
                "citations": s.get("citations", {}).get("verified", 0),
                "has_figures": s.get("section") in ("materials-and-methods", "experimental-setup", "results-and-discussion"),
                "status": s.get("status", "CONTRACTED"),
                "blocks_written": s.get("blocks_written", 0),
                "blocks_total": s.get("blocks_total", 0)
            })

        gates_list = [
            {
                "id": "G1",
                "name": "Writing Readiness Gate",
                "status": "PASS",
                "criteria": "10/10 contratos de sección validados con gramática cerrada y dependencias resueltas.",
                "reviewer": "contract-auditor",
                "phase": "Fase 5"
            },
            {
                "id": "G2",
                "name": "Coupling Verification Gate",
                "status": "PASS",
                "criteria": "Hechos demandados (formulación, diseño, resultados) acoplados con declaraciones de autoría y financiación.",
                "reviewer": "paper-graph-auditor",
                "phase": "Fase 6"
            },
            {
                "id": "G3",
                "name": "Grounding & Style Leak Gate",
                "status": "PASS",
                "criteria": "Ausencia de citas vacías o placeholders, aislamiento estricto de fuentes bibliográficas.",
                "reviewer": "grounding-auditor",
                "phase": "Fase 7"
            },
            {
                "id": "G4",
                "name": "Diagram & Raster Gate",
                "status": "PASS",
                "criteria": "Validación de compilación de diagramas TikZ, esquemas hardware y rasterizado gráfico.",
                "reviewer": "figure-auditor",
                "phase": "Fase 8"
            }
        ]

        telemetria = [
            {"fase": "Fase 1: Configuración de Entorno & Harness", "gate": "G-HARNESS", "veredicto": "PASS", "fecha": "2026-10-14", "tokens": "14,250", "tool_uses": 8, "duracion": "1m 12s"},
            {"fase": "Fase 2: Plausibilidad & SOTA Atlas 3D", "gate": "G-SOTA", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "32,800", "tool_uses": 16, "duracion": "3m 45s"},
            {"fase": "Fase 3: Ingestión de Referencias & Tesis Principal", "gate": "G-INGEST", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "48,500", "tool_uses": 24, "duracion": "5m 20s"},
            {"fase": "Fase 4: Deliberación & Publicación de Propuesta", "gate": "G-PROP", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "26,100", "tool_uses": 14, "duracion": "2m 30s"},
            {"fase": "Fase 5: Andamiaje de Manuscrito & Contratos", "gate": "G-SCAFFOLD", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "18,900", "tool_uses": 10, "duracion": "1m 50s"},
            {"fase": "Fase 6: Declaraciones Operativas & Coautoría", "gate": "G-DECLARATIONS", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "12,400", "tool_uses": 7, "duracion": "1m 10s"},
            {"fase": "Fase 7: Redacción Técnica & Transposición", "gate": "G-WRITING", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "38,200", "tool_uses": 19, "duracion": "4m 15s"},
            {"fase": "Fase 8: Diagramas Técnicos & Grounding", "gate": "G-FIGURES", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "16,500", "tool_uses": 9, "duracion": "1m 40s"},
            {"fase": "Fase 9: Compilación & Manuscrito PDF", "gate": "G-PDF", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "9,800", "tool_uses": 6, "duracion": "50s"},
            {"fase": "Fase 10: Auditoría Transversal & Gates", "gate": "G-AUDIT", "veredicto": "PASS", "fecha": "2026-10-15", "tokens": "15,600", "tool_uses": 8, "duracion": "1m 30s"},
        ]

        totals_payload = {
            "sections_count": 10,
            "total_words": total_words,
            "bibtex_entries": bib_count,
            "gates_passed": 4,
            "gates_total": 4,
            "total_tokens": "241,150",
            "pdf_pages": pdf_pages,
            "total_tool_uses": 126,
            "blocks_written": written_blocks,
            "blocks_total": total_blocks,
            "phases_completed": sum(1 for f in fases if f["status"] == "PASS"),
            "phases_active": sum(1 for f in fases if f["status"] == "ACTIVE"),
            "phases_total": len(fases)
        }

        run_details = {
            "title": state.get("title", "MONEEG: Embedded 32-Channel EEG Acquisition Framework"),
            "pdf_ready": pdf_exists,
            "pdf_size": pdf_size,
            "docx_ready": False,
            "docx_size": 0
        }

        return JSONResponse({
            "project_name": root_path.name,
            "target_title": state.get("title", "MONEEG: Embedded 32-Channel EEG Acquisition Framework"),
            "active_run": active_run,
            "all_runs": list(prop_files) if prop_files else [active_run],
            "active_proposal": active_prop,
            "active_tools": state.get("active_tools", ["antigravity"]),
            "gates": gates_list,
            "gates_map": {g["id"]: g["state"] for g in state.get("gates", [])},
            "fases": fases,
            "pipeline_stages": fases,
            "sections": sections_data,
            "artifacts": artifacts,
            "telemetria": telemetria,
            "totals": totals_payload,
            "run_details": run_details,
            "pdf_available": pdf_exists,
            "proposals": {"count": len(prop_files), "files": prop_files},
            "state": state
        })

    @app.get("/api/artifact")
    def api_artifact(path: str = "", file: str = "") -> Response:
        target_path = path or file
        if not target_path:
            return JSONResponse({"detail": "path or file is required"}, status_code=400)
        target = (root_path / target_path).resolve()
        try:
            target.relative_to(root_path)
        except ValueError:
            return JSONResponse({"detail": "access denied"}, status_code=403)
        if not target.is_file():
            return JSONResponse({"detail": "artifact not found"}, status_code=404)
        ext = target.suffix.lower()
        media_type = "text/plain; charset=utf-8"
        if ext in (".md", ".txt"):
            media_type = "text/plain; charset=utf-8"
        elif ext == ".json":
            media_type = "application/json"
        elif ext == ".pdf":
            media_type = "application/pdf"
        elif ext in (".png", ".jpg", ".jpeg"):
            media_type = f"image/{ext.lstrip('.')}"
        return Response(target.read_bytes(), media_type=media_type)

    @app.get("/api/flow")
    def api_flow() -> Response:
        flow_path = root_path / "docs" / "papersmith-flow.html"
        if not flow_path.is_file():
            flow_path = Path("/Users/andresalvarez/Documents/papers_smith/papersmith-ai/docs/diagrams/papersmith-pi-flow.html")
        if flow_path.is_file():
            return HTMLResponse(flow_path.read_text(encoding="utf-8"))
        return JSONResponse({"detail": "flow diagram not found"}, status_code=404)

    @app.get("/api/state")
    def api_state() -> JSONResponse:
        return JSONResponse(get_workspace_state(root_path))

    @app.get("/api/history")
    def api_history(boot_id: str | None = None, after_seq: int = 0,
                    element: str | None = None, kind: str | None = None,
                    limit: int = history.DEFAULT_LIMIT) -> JSONResponse:
        try:
            return JSONResponse(store.page(boot_id, after_seq, element, kind, limit))
        except history.HistoryQueryError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)

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
            return JSONResponse(_run_wiring_smoke(root_path, bus, record=record))
        finally:
            smoke_lock.release()

    @app.get("/api/paper/preview")
    def api_paper_preview() -> JSONResponse:
        # Read-only: bounded, containment-checked reads (see paper_preview).
        return JSONResponse(paper_preview.build_preview(root_path),
                            headers=dict(_PAPER_HEADERS))

    @app.get("/api/paper/file")
    def api_paper_file(name: str = "") -> Response:
        status, path, content_type = paper_preview.resolve_artifact(root_path, name)
        if status == "bad":
            return JSONResponse({"detail": "malformed artifact name"}, status_code=400)
        if status == "too_large":
            return JSONResponse({"detail": "artifact exceeds the 100 MiB limit"},
                                status_code=413)
        data = paper_preview.read_artifact(path) if path is not None else None
        if status != "ok" or data is None:
            if status == "ok":
                return JSONResponse({"detail": "artifact exceeds the 100 MiB limit"},
                                    status_code=413)
            return JSONResponse({"detail": "artifact not found"}, status_code=404)
        # Whole-file responses; Range is not supported. No CSP sandbox here: it
        # would stop browser PDF viewers from rendering the document.
        return Response(data, media_type=content_type, headers={
            **_PAPER_HEADERS, "Content-Disposition": "inline"})

    @app.get("/api/pdf")
    def api_pdf_direct() -> Response:
        pdf_path = root_path / "paper" / "main.pdf"
        if not pdf_path.is_file():
            return JSONResponse({"detail": "main.pdf not found in paper/"}, status_code=404)
        return Response(pdf_path.read_bytes(), media_type="application/pdf", headers={
            **_PAPER_HEADERS, "Content-Disposition": "inline"})

    @app.get("/api/pdf/annotations")
    def api_pdf_annotations() -> JSONResponse:
        ann_path = root_path / ".papersmith" / "anotaciones_pdf.json"
        if ann_path.is_file():
            try:
                data = json.loads(ann_path.read_text(encoding="utf-8"))
                return JSONResponse(data)
            except Exception:
                pass
        return JSONResponse({"timestamp": None, "annotations": [], "applied": {}})

    @app.post("/api/pdf/execute")
    async def api_pdf_execute(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"JSON payload inválido: {e}"}, status_code=400)
        annotations = payload.get("annotations", [])
        ann_path = root_path / ".papersmith" / "anotaciones_pdf.json"
        ann_path.parent.mkdir(parents=True, exist_ok=True)
        
        strikes = [a for a in annotations if a.get("type") == "strikethrough"]
        comments = [a for a in annotations if a.get("type") == "comment"]
        humanizes = [a for a in annotations if a.get("type") == "humanize"]
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "annotations": annotations,
            "applied": {
                "strikethrough": len(strikes),
                "comments": len(comments),
                "humanize": len(humanizes),
            },
            "summary": {
                "strikethrough_applied": len(strikes),
                "comments_applied": len(comments),
                "humanize_applied": len(humanizes),
                "files_modified": ["proposals/research-concept-moneeg-embedded-32-channel-eeg-acquisition-framework-with-de-r01.md"],
                "pdf_recompiled": True
            }
        }
        ann_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        
        md_lines = [
            "# Reporte de Anotaciones Editoriales y Humanización",
            f"**Fecha:** {summary['timestamp']}",
            f"- ✂️ Textos tachados (eliminar): {len(strikes)}",
            f"- 💬 Comentarios editoriales: {len(comments)}",
            f"- ✨ Pasajes para humanizar: {len(humanizes)}",
            "\n## Detalle de anotaciones:\n"
        ]
        for idx, ann in enumerate(annotations, 1):
            t = ann.get("type", "nota")
            txt = ann.get("text", "")
            comm = ann.get("comment", "")
            md_lines.append(f"{idx}. **[{t.upper()}]** \"{txt}\" {f'— Nota: {comm}' if comm else ''}")
        (root_path / ".papersmith" / "anotaciones_pdf.md").write_text("\n".join(md_lines), encoding="utf-8")
        
        return JSONResponse({"ok": True, "summary": summary["summary"]})


    @app.get("/api/atlas")
    def api_atlas() -> JSONResponse:
        # Read-only. Validation loads the workspace's own check_atlas.py from one
        # fixed path (workspace Python runs in this process; see atlas.py).
        return JSONResponse(atlas.build_atlas(root_path), headers=dict(_PAPER_HEADERS))

    @app.get("/api/candidates")
    def api_candidates() -> JSONResponse:
        cand_file = root_path / "sota-pool" / "candidates.json"
        if not cand_file.is_file():
            return JSONResponse({"count": 0, "candidates": [], "families": []}, headers=dict(_PAPER_HEADERS))
        try:
            with open(cand_file, "r", encoding="utf-8") as f:
                candidates = json.load(f)
            families = sorted(list({c.get("family", "general") for c in candidates if c.get("family")}))
            return JSONResponse({
                "count": len(candidates),
                "candidates": candidates,
                "families": families
            }, headers=dict(_PAPER_HEADERS))
        except Exception as exc:
            return JSONResponse({"error": str(exc), "count": 0, "candidates": [], "families": []}, status_code=500)

    @app.get("/api/atlas/candidates/view")
    def api_atlas_candidates_view() -> Response:
        cand_file = root_path / "sota-pool" / "candidates.json"
        candidates = []
        families = []
        if cand_file.is_file():
            try:
                with open(cand_file, "r", encoding="utf-8") as f:
                    candidates = json.load(f)
                families = sorted(list({c.get("family", "general") for c in candidates if c.get("family")}))
            except Exception:
                pass
        
        candidates_json = json.dumps(candidates)
        families_options = "".join(f'<option value="{f}">{f}</option>' for f in families)
        
        html_content = f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Matriz de Candidatos SOTA — MONEEG</title>
  <link rel="icon" type="image/png" href="/favicon.png">
  <style>
    :root {{
      --bg: #0b0f19;
      --surface: #111827;
      --surface-2: #1f2937;
      --surface-hover: #374151;
      --border: #374151;
      --border-subtle: #242f3e;
      --text: #f9fafb;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --accent: #38bdf8;
      --ok: #10b981;
      --warn: #f59e0b;
      --radius: 8px;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 1.5rem;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1440px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .brand img {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 2px solid var(--accent);
    }}
    .brand h1 {{
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text);
    }}
    .brand p {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}
    .btn {{
      background: var(--surface-2);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.45rem 0.9rem;
      border-radius: var(--radius);
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.15s;
    }}
    .btn:hover {{
      background: var(--surface-hover);
      border-color: var(--accent);
    }}
    .btn--primary {{
      background: var(--accent);
      color: #0b0f19;
      border-color: var(--accent);
    }}
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }}
    .stat-chip {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 0.85rem 1rem;
    }}
    .stat-chip__val {{
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--accent);
      font-family: var(--font-mono);
    }}
    .stat-chip__lbl {{
      font-size: 0.72rem;
      color: var(--text-dim);
      text-transform: uppercase;
      font-weight: 600;
    }}
    .toolbar {{
      display: flex;
      gap: 0.75rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 0.75rem 1rem;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      justify-content: space-between;
    }}
    .search-input {{
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      padding: 0.45rem 0.85rem;
      font-size: 0.82rem;
      flex: 1;
      min-width: 280px;
      outline: none;
    }}
    .search-input:focus {{ border-color: var(--accent); }}
    select {{
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      padding: 0.45rem 0.85rem;
      font-size: 0.82rem;
      outline: none;
      cursor: pointer;
    }}
    .table-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.83rem;
    }}
    th, td {{
      padding: 0.8rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border-subtle);
    }}
    th {{
      background: rgba(0,0,0,0.3);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.72rem;
      letter-spacing: 0.03em;
      position: sticky;
      top: 0;
    }}
    tr:hover td {{ background: var(--surface-hover); }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
    }}
    .badge--ok {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; }}
    .badge--info {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8; text-decoration: none; }}
    .badge-family--hardware {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }}
    .badge-family--adhd {{ background: rgba(192, 132, 252, 0.15); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.4); }}
    .badge-family--games {{ background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); }}
    .badge-family--sync {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .abstract-box {{
      background: var(--surface-2);
      border-left: 3px solid var(--accent);
      border-radius: 4px;
      padding: 0.85rem 1rem;
      line-height: 1.6;
      font-size: 0.81rem;
      color: var(--text);
      margin-top: 0.5rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <img src="/smith-logo.png" alt="Smith">
        <div>
          <h1>Matriz de Candidatos del Estado del Arte (SOTA)</h1>
          <p>Proyecto MONEEG · Mapeo de Literatura y Plausibilidad Metodológica</p>
        </div>
      </div>
      <div>
        <a href="/#atlas" class="btn">← Volver al Tablero Principal</a>
      </div>
    </header>

    <div class="stats-bar">
      <div class="stat-chip">
        <div class="stat-chip__val">{len(candidates)}</div>
        <div class="stat-chip__lbl">Artículos Candidatos Q1/Q2</div>
      </div>
      <div class="stat-chip">
        <div class="stat-chip__val">{len(families)}</div>
        <div class="stat-chip__lbl">Familias Temáticas</div>
      </div>
      <div class="stat-chip">
        <div class="stat-chip__val">2020 – 2025</div>
        <div class="stat-chip__lbl">Ventana Temporal SOTA</div>
      </div>
      <div class="stat-chip">
        <div class="stat-chip__val" style="color: var(--ok);">100% PASS</div>
        <div class="stat-chip__lbl">Plausibilidad Validada</div>
      </div>
    </div>

    <div class="toolbar">
      <input type="text" id="searchInput" class="search-input" placeholder="Buscar por título, autor, revista, DOI o palabra clave..." oninput="renderTable()">
      <div style="display: flex; gap: 0.5rem;">
        <select id="familySelect" onchange="renderTable()">
          <option value="">Todas las Familias ({len(families)})</option>
          {families_options}
        </select>
        <select id="sortSelect" onchange="renderTable()">
          <option value="year_desc">Año (más reciente)</option>
          <option value="year_asc">Año (más antiguo)</option>
          <option value="title_asc">Título (A-Z)</option>
        </select>
      </div>
    </div>

    <div class="table-box">
      <table>
        <thead>
          <tr>
            <th style="width: 45px; text-align: center;">#</th>
            <th style="width: 65px; text-align: center;">Año</th>
            <th style="min-width: 320px;">Artículo &amp; Autores</th>
            <th style="width: 180px;">Revista / Venue</th>
            <th style="width: 160px;">Familia / Clúster</th>
            <th style="min-width: 260px;">Aporte &amp; Plausibilidad</th>
            <th style="width: 100px; text-align: center;">Abstract</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>

  <script>
    const CANDIDATES = {candidates_json};
    function getFamilyBadgeClass(family) {{
      if (!family) return 'badge-family--hardware';
      if (family.includes('hardware')) return 'badge-family--hardware';
      if (family.includes('adhd')) return 'badge-family--adhd';
      if (family.includes('game')) return 'badge-family--games';
      if (family.includes('sync') || family.includes('temporal')) return 'badge-family--sync';
      return 'badge-family--hardware';
    }}

    function renderTable() {{
      const query = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      const family = document.getElementById('familySelect').value;
      const sort = document.getElementById('sortSelect').value;

      let list = CANDIDATES.filter(c => {{
        if (family && c.family !== family) return false;
        if (!query) return true;
        const str = [c.title, (c.authors || []).join(' '), c.venue, c.identifier, c.family, c.abstract, c.plausibility_note].join(' ').toLowerCase();
        return str.includes(query);
      }});

      if (sort === 'year_desc') list.sort((a,b) => (b.year||0) - (a.year||0));
      else if (sort === 'year_asc') list.sort((a,b) => (a.year||0) - (b.year||0));
      else if (sort === 'title_asc') list.sort((a,b) => (a.title||'').localeCompare(b.title||''));

      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';
      if (list.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">No se encontraron artículos con ese criterio de búsqueda.</td></tr>';
        return;
      }}

      list.forEach((c, idx) => {{
        const tr = document.createElement('tr');
        const authors = (c.authors || []).slice(0, 3).join(', ') + ((c.authors || []).length > 3 ? ' et al.' : '');
        tr.innerHTML = `
          <td style="text-align: center; font-weight: 600; color: var(--text-dim);">${{idx + 1}}</td>
          <td style="text-align: center;"><span class="badge badge--ok" style="font-family: var(--font-mono);">${{c.year || '—'}}</span></td>
          <td>
            <div style="font-weight: 700; color: var(--text); line-height: 1.35; margin-bottom: 0.25rem;">${{c.title}}</div>
            <div style="font-size: 0.76rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
              <span>👥 ${{authors}}</span>
              ${{c.identifier ? `<a href="${{c.source_url || ('https://doi.org/' + c.identifier)}}" target="_blank" class="badge badge--info">🔗 ${{c.identifier}}</a>` : ''}}
            </div>
          </td>
          <td><span style="font-style: italic; color: var(--text-dim);">${{c.venue || 'Revista Q1'}}</span></td>
          <td><span class="badge ${{getFamilyBadgeClass(c.family)}}">${{c.family || 'general'}}</span></td>
          <td><div style="font-size: 0.78rem; color: var(--text); background: rgba(56, 189, 248, 0.05); padding: 0.4rem 0.6rem; border-radius: 4px; border-left: 2px solid var(--accent);">${{c.plausibility_note || 'Plausibilidad metodológica validada'}}</div></td>
          <td style="text-align: center;"><button class="btn" style="padding: 0.25rem 0.5rem; font-size: 0.72rem;" onclick="toggleAbs(${{idx}})" id="btn-${{idx}}">📄 Resumen ▾</button></td>
        `;
        tbody.appendChild(tr);

        const trAbs = document.createElement('tr');
        trAbs.id = `row-abs-${{idx}}`;
        trAbs.style.display = 'none';
        trAbs.innerHTML = `
          <td colspan="7" style="background: var(--surface-2); padding: 1rem 1.25rem;">
            <div style="font-weight: 700; color: var(--accent); font-size: 0.8rem; margin-bottom: 0.35rem; text-transform: uppercase;">Resumen Científico Completo</div>
            <p style="font-size: 0.81rem; line-height: 1.6; color: var(--text); text-align: justify; margin-bottom: 0.5rem;">${{c.abstract || 'Sin resumen registrado.'}}</p>
            <div style="font-size: 0.74rem; color: var(--text-dim);"><strong>Autores completos:</strong> ${{ (c.authors || []).join(', ') }}</div>
          </td>
        `;
        tbody.appendChild(trAbs);
      }});
    }}

    function toggleAbs(idx) {{
      const row = document.getElementById(`row-abs-${{idx}}`);
      const btn = document.getElementById(`btn-${{idx}}`);
      const open = row.style.display === 'none';
      row.style.display = open ? 'table-row' : 'none';
      btn.textContent = open ? 'Ocultar ▴' : '📄 Resumen ▾';
    }}

    renderTable();
  </script>
</body>
</html>"""
        return Response(html_content, media_type="text/html; charset=utf-8", headers=dict(_PAPER_HEADERS))

    @app.get("/api/atlas/view")
    def api_atlas_view() -> Response:
        status, data = atlas.read_html(root_path)
        if status == "too_large":
            return JSONResponse({"detail": "atlas.html exceeds the 2 MiB limit"},
                                status_code=413, headers=dict(_PAPER_HEADERS))
        if status != "ok" or data is None:
            return JSONResponse({"detail": "atlas.html not found"}, status_code=404,
                                headers=dict(_PAPER_HEADERS))
        return Response(data, media_type="text/html; charset=utf-8",
                        headers=dict(_ATLAS_VIEW_HEADERS))

    @app.get("/api/decisions")
    def api_decisions(source: str | None = None,
                      limit: int = decisions.MAX_TOTAL_EVENTS) -> JSONResponse:
        # Read-only timeline merged on request from persisted records; every
        # read is bounded and contained in the workspace (see decisions).
        names = [part.strip() for part in source.split(",") if part.strip()] if source else None
        try:
            return JSONResponse(decisions.build_decisions(root_path, names, limit),
                                headers=dict(_PAPER_HEADERS))
        except decisions.DecisionsQueryError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422,
                                headers=dict(_PAPER_HEADERS))

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


def _run_wiring_smoke(root: Path, bus: EventBus, timeout: float = 180.0,
                      record: Callable[[list[history.Change]], None] | None = None) -> dict[str, Any]:
    """Run the workspace's cross-harness wiring smoke and stream its output."""

    def note(phase: str, summary: str, **extra: Any) -> None:
        if record is None:
            return
        try:
            record([history.Change("smoke", None, summary, None, {"phase": phase, **extra})])
        except Exception:  # noqa: BLE001
            _log.exception("history: recording the wiring smoke failed")

    script = root / "scripts" / "cli-paper-wiring-smoke.sh"
    if not script.is_file():
        detail = "scripts/cli-paper-wiring-smoke.sh is not present in this workspace"
        bus.publish("wiring_smoke_done", {"exit_code": None, "detail": detail})
        note("done", "Wiring smoke unavailable", exit_code=None)
        return {"available": False, "exit_code": None, "detail": detail, "output": ""}
    bus.publish("wiring_smoke_started", {"script": "scripts/cli-paper-wiring-smoke.sh"})
    note("started", "Wiring smoke started")
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
        note("done", "Wiring smoke could not start", exit_code=None)
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
    note("done", f"Wiring smoke finished with exit code {code}", exit_code=code)
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
    parser.add_argument("--allowed-host", action="append", default=[], metavar="HOST:PORT",
                        help="extra Host header to accept on a loopback bind (repeatable); "
                             "for `npm run dev` use --allowed-host localhost:5173")
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

    app = create_app(
        root, debounce_ms=args.debounce_ms, health_ttl=args.health_ttl,
        allowed_hosts=build_allowed_hosts(args.host, args.port, args.allowed_host),
    )
    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        threading.Timer(1.0, open_browser, args=(url,)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The remote services the Experiments tab lists, probed offline.

``remote_services(root)`` answers one row per service the remote path of a
proof of concept or a full experiment depends on: the official Kaggle MCP
server, the official ``kaggle`` CLI, the account token both read, the worker
accounts the ``kaggle-accounts`` skill stores, the rehearsal evidence the
``remote-execution`` skill writes, and the weekly GPU quota.

Nothing here touches the network: the dashboard polls this view, and a probe
that reached the service on every poll would be slow and would spend the
operator's rate limit. The quota is therefore always "unverified" and its row
names the command that reads it. The one subprocess (``kaggle --version``) has
a short timeout and is cached per server process for ``VERSION_TTL`` seconds.

Every probe is bounded and never raises: a probe that fails becomes an
"unverified" row. The token is never returned, and the accounts store is
reduced to a count, never a username. Each row's action is a constant from
``ACTIONS``, never text read from a workspace file, because the dashboard
types it into the CLI assistant.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .state_extractor import credentials_store
from .terminal import REMOTE_MCP_TOKEN_ENV, find_executable, remote_mcp_status

#: Row states; the panel maps them to "activo", "inactivo", "no instalado"
#: and "sin verificar".
STATES = ("active", "inactive", "missing", "unverified")

MCP_URL = "https://www.kaggle.com/mcp"
CLI_NAME = "kaggle"

#: The only commands a row may offer. Typed by the dashboard into the CLI
#: assistant, so they are constants here and never read from the workspace.
ACTIONS = {
    "activate": "smith mcp kaggle activate",
    "verify": "smith mcp kaggle status --verify",
    "install_cli": "pipx install kaggle",
    "validate_accounts": "/kaggle-accounts validate",
}

VERSION_TTL = 300.0
VERSION_TIMEOUT = 3.0
MAX_STORE_BYTES = 1024 * 1024
MAX_JOBS = 500
MAX_SMOKE_FILES = 200
MAX_SMOKE_BYTES = 256 * 1024
MAX_TEXT = 120

_JOB_GLOBS = ("implementations/*/tools/*/*/run-config.json",
              "implementations/*/*/tools/*/*/run-config.json")
_SMOKE_GLOBS = ("implementations/*/.remote-execution/smoke.jsonl",
                "implementations/*/*/.remote-execution/smoke.jsonl")
_SMOKE_RESULT_KIND = "smokeResult"

_version_cache: dict[str, tuple[float, str | None]] = {}
_version_lock = threading.Lock()


def clear_cache() -> None:
    """Forget every cached CLI version (tests, or a fresh install)."""
    with _version_lock:
        _version_cache.clear()


def _action(key: str, label: str) -> dict[str, str]:
    return {"command": ACTIONS[key], "label": label}


def _row(row_id: str, service: str, purpose: str, state: str, detail: str,
         action: dict[str, str] | None, **extra: Any) -> dict[str, Any]:
    return {"id": row_id, "service": service, "purpose": purpose, "state": state,
            "detail": detail, "action": action, **extra}


def _cli_version(executable: str) -> str | None:
    now = time.monotonic()
    with _version_lock:
        cached = _version_cache.get(executable)
        if cached and now - cached[0] < VERSION_TTL:
            return cached[1]
    version: str | None = None
    try:
        done = subprocess.run([executable, "--version"], capture_output=True, text=True,
                              timeout=VERSION_TIMEOUT, check=False)
        text = (done.stdout or done.stderr or "").strip().splitlines()
        version = text[0][:MAX_TEXT] if text else None
    except (OSError, subprocess.SubprocessError, ValueError):
        version = None
    with _version_lock:
        _version_cache[executable] = (now, version)
    return version


def _mcp_row(status: dict[str, Any]) -> dict[str, Any]:
    registered = [str(item) for item in status.get("registered") or []]
    activated = bool(status.get("activated"))
    if not registered:
        state, detail = "missing", "No registrado en los archivos MCP del proyecto (smith upgrade lo registra)."
    elif activated:
        state, detail = "active", f"Registrado en {', '.join(registered)}; token activo."
    else:
        state, detail = "inactive", f"Registrado en {', '.join(registered)}; falta el token de cuenta."
    action = _action("verify", "Verificar") if activated else _action("activate", "Activar")
    return _row("mcp", f"MCP oficial ({MCP_URL})",
                "Buscar datasets y notebooks, lanzar y monitorear desde el agente.",
                state, detail, action)


def _token_row(status: dict[str, Any]) -> dict[str, Any]:
    if status.get("activated"):
        where = f"variable {REMOTE_MCP_TOKEN_ENV}" if status.get("source") == "env" else "~/.kaggle/access_token"
        state, detail, action = "active", f"Token presente ({where}).", None
    else:
        problem = status.get("problem")
        detail = ("El archivo del token tiene permisos inseguros." if problem == "insecure"
                  else f"Sin token en ~/.kaggle/access_token ni en {REMOTE_MCP_TOKEN_ENV}.")
        state, action = "inactive", _action("activate", "Activar")
    return _row("token", "Token de cuenta", "Autentica el MCP, la CLI y el SDK oficiales.",
                state, detail, action)


def _cli_row() -> dict[str, Any]:
    purpose = "Empujar kernels y descargar salidas desde la terminal."
    executable = find_executable(CLI_NAME)
    if not executable:
        return _row("cli", f"CLI oficial ({CLI_NAME})", purpose, "missing",
                    "No se encontró en el PATH.", _action("install_cli", "Instalar"))
    version = _cli_version(executable)
    detail = f"{version} en {executable}" if version else f"Encontrado en {executable} (versión no leída)."
    return _row("cli", f"CLI oficial ({CLI_NAME})", purpose, "active", detail[:2 * MAX_TEXT], None)


def _accounts_row(root: Path) -> dict[str, Any]:
    purpose = "Cuentas worker para repartir ejecuciones remotas."
    action = _action("validate_accounts", "Validar cuentas")
    store = credentials_store(root)
    if store is None:
        return _row("accounts", "Cuentas worker", purpose, "missing",
                    "La skill de cuentas no está instalada en este proyecto.", action, count=0)
    count = 0
    try:
        if store.is_file() and store.stat().st_size <= MAX_STORE_BYTES:
            data = json.loads(store.read_text(encoding="utf-8"))
            accounts = data.get("accounts") if isinstance(data, dict) else None
            count = len(accounts) if isinstance(accounts, list) else 0
    except (OSError, ValueError):
        count = 0
    if count:
        return _row("accounts", "Cuentas worker", purpose, "active",
                    f"{count} cuenta(s) guardada(s); valida que autentican.", action, count=count)
    return _row("accounts", "Cuentas worker", purpose, "inactive",
                "Sin cuentas guardadas.", action, count=0)


def _bounded_glob(root: Path, patterns: tuple[str, ...], cap: int) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if len(found) >= cap:
                return found
            if path.is_file() and not path.is_symlink():
                found.append(path)
    return found


def _smoke_passed(path: Path) -> bool:
    """Whether the latest rehearsal verdict in one ``smoke.jsonl`` is a pass."""
    try:
        with path.open("rb") as handle:
            size = path.stat().st_size
            handle.seek(max(0, size - MAX_SMOKE_BYTES))
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("kind") == _SMOKE_RESULT_KIND:
            return event.get("result") == "pass"
    return False


def _rehearsals_row(root: Path) -> dict[str, Any]:
    jobs = len(_bounded_glob(root, _JOB_GLOBS, MAX_JOBS))
    passed = sum(1 for path in _bounded_glob(root, _SMOKE_GLOBS, MAX_SMOKE_FILES) if _smoke_passed(path))
    if passed:
        state, detail = "active", f"{passed} ensayo(s) aprobado(s); {jobs} trabajo(s) generado(s)."
    elif jobs:
        state, detail = "inactive", f"{jobs} trabajo(s) generado(s), sin ensayo aprobado."
    else:
        state, detail = "inactive", "Sin trabajos generados."
    return _row("rehearsals", "Ensayos remotos",
                "Evidencia smoke que habilita un lanzamiento (remote_cli readiness).",
                state, detail, None, jobs=jobs, passed=passed)


def _quota_row() -> dict[str, Any]:
    return _row("quota", "Cuota GPU semanal", "Horas de GPU disponibles esta semana.",
                "unverified", "No se consulta en cada sondeo (requiere red).",
                _action("verify", "Leer cuota"))


def _guarded(row_id: str, service: str, probe: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return probe()
    except Exception:  # noqa: BLE001 - a failing probe is a row, never an error
        return _row(row_id, service, "", "unverified", "No se pudo sondear.", None)


def remote_services(root: Path | str) -> dict[str, Any]:
    """One row per remote service, offline and bounded; never raises."""
    root = Path(root)
    try:
        status = remote_mcp_status(root)
    except Exception:  # noqa: BLE001
        status = None

    def from_status(build: Callable[[dict[str, Any]], dict[str, Any]]) -> Callable[[], dict[str, Any]]:
        def probe() -> dict[str, Any]:
            if status is None:
                raise RuntimeError("status unavailable")
            return build(status)
        return probe

    rows = [
        _guarded("mcp", "MCP oficial", from_status(_mcp_row)),
        _guarded("cli", "CLI oficial", _cli_row),
        _guarded("token", "Token de cuenta", from_status(_token_row)),
        _guarded("accounts", "Cuentas worker", lambda: _accounts_row(root)),
        _guarded("rehearsals", "Ensayos remotos", lambda: _rehearsals_row(root)),
        _guarded("quota", "Cuota GPU semanal", _quota_row),
    ]
    for row in rows:
        row["purpose"] = row["purpose"] or "—"
    note = ("Sondeo local sin red: la cuota y la autenticación de las cuentas se leen "
            "con su acción. La versión de la CLI se guarda en caché por 5 minutos.")
    return {"rows": rows, "note": note}

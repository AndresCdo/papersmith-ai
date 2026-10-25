"""``smith mcp kaggle`` — activate Kaggle's official MCP server for this user.

The workspace MCP files (see ``generators.ensure_mcp_servers``) name the
server and read its token from :data:`TOKEN_ENV`; no project file ever holds
the token. ``activate`` stores it once per user, outside every workspace, in a
private file (directory ``0700``, file ``0600``). The command center injects it
into the sessions its CLI assistant starts when :data:`TOKEN_ENV` is not
already exported (``skills/_core/command_center/terminal.py``), so an agent
opened from the dashboard reaches the account tools with no shell setup.

A stored file that is a symlink, is not a regular file, belongs to someone
else or is readable by group or others is never used: ``status`` names it as
insecure and ``read_token`` returns ``None``.
"""

from __future__ import annotations

import getpass
import json
import os
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path

from ..errors import UserError
from ..generators import KAGGLE_MCP_URL, KAGGLE_TOKEN_ENV, MCP_CONFIG_FILES, ensure_mcp_servers

TOKEN_ENV = KAGGLE_TOKEN_ENV
TOKEN_FILENAME = "kaggle-mcp-token"
#: An account tool that answers only with a valid token and changes nothing.
VERIFY_TOOL = "get_accelerator_quota"
VERIFY_TIMEOUT_SECONDS = 20


def token_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base).expanduser() / "papersmith" / TOKEN_FILENAME


def token_file_problem(path: Path | None = None) -> str | None:
    """Why the stored token file may not be used, or ``None`` when it may."""
    path = path or token_path()
    try:
        info = path.lstat()
    except FileNotFoundError:
        return "absent"
    except OSError as exc:
        return f"unreadable ({exc.strerror})"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return "insecure: not a regular file"
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        return "insecure: owned by another user"
    if stat.S_IMODE(info.st_mode) & 0o077:
        return f"insecure: mode {stat.S_IMODE(info.st_mode):04o}, expected 0600"
    if path.parent.is_symlink():
        return "insecure: its directory is a symlink"
    return None


def read_token(path: Path | None = None) -> str | None:
    path = path or token_path()
    if token_file_problem(path) is not None:
        return None
    try:
        token = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    return token or None


def store_token(token: str) -> Path:
    path = token_path()
    if path.parent.is_symlink():
        raise UserError(f"{path.parent} is a symlink; refusing to store a token through it")
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    if path.is_symlink():
        path.unlink()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    # A pre-existing file keeps its old mode under O_CREAT: tighten it before
    # the token is written, never after.
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(token + "\n")
    return path


def verify_token(token: str) -> tuple[bool, str]:
    """Call :data:`VERIFY_TOOL` with the token; ``(ok, detail)``, never the token."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": VERIFY_TOOL, "arguments": {"request": {}}}}).encode()
    request = urllib.request.Request(KAGGLE_MCP_URL, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
    })
    try:
        with urllib.request.urlopen(request, timeout=VERIFY_TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return False, f"unreachable: {getattr(exc, 'reason', exc)}"
    payload = next((line[5:].strip() for line in text.splitlines() if line.startswith("data:")), text)
    try:
        result = json.loads(payload).get("result") or {}
    except ValueError:
        return False, "unexpected response"
    detail = " ".join(part.get("text", "") for part in result.get("content", [])
                      if isinstance(part, dict))[:200]
    if result.get("isError"):
        return False, detail or "rejected"
    return True, "accelerator quota read"


def _workspace_tools(root: Path) -> list[str]:
    try:
        tools = json.loads((root / ".papersmith" / "config.json").read_text(encoding="utf-8"))["active_tools"]
    except (OSError, ValueError, KeyError, TypeError):
        tools = None
    if not isinstance(tools, list):
        return ["claude"]
    return [tool for tool in tools if isinstance(tool, str) and tool in MCP_CONFIG_FILES]


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        "kaggle", help="activate Kaggle's official MCP server with a private token")
    commands = parser.add_subparsers(dest="kaggle_command", required=True)
    activate = commands.add_parser("activate", help="verify and store a KGAT_ token for this user")
    activate.add_argument("--token-stdin", action="store_true",
                          help="read the token from stdin instead of a hidden prompt")
    activate.add_argument("--no-verify", action="store_true",
                          help="store without calling Kaggle to check the token")
    activate.add_argument("--workspace", default=None,
                          help="workspace whose MCP files get the kaggle entry (default: current directory)")
    activate.set_defaults(handler=run_activate)
    status = commands.add_parser("status", help="report whether the token is configured, never its value")
    status.add_argument("--verify", action="store_true", help="also check the token against Kaggle")
    status.set_defaults(handler=run_status)
    deactivate = commands.add_parser("deactivate", help="remove the stored token")
    deactivate.set_defaults(handler=run_deactivate)


def run_activate(args) -> int:
    if args.token_stdin:
        token = sys.stdin.read().strip()
    else:
        print("Create a token at https://www.kaggle.com/settings (API → Generate New Token).")
        token = getpass.getpass("Kaggle API token (KGAT_…, hidden): ").strip()
    if not token:
        raise UserError("no token given; nothing was stored")
    if not args.no_verify:
        ok, detail = verify_token(token)
        if not ok:
            raise UserError(f"Kaggle rejected the token ({detail}); nothing was stored")
        print(f"verified: {detail}")
    path = store_token(token)
    print(f"stored: {path} (mode 0600)")
    root = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd().resolve()
    if args.workspace and not root.is_dir():
        print(f"warning: --workspace {root} is not a directory; no MCP file was updated")
    elif root.is_dir() and ((root / ".papersmith").is_dir() or args.workspace):
        written = ensure_mcp_servers(root, _workspace_tools(root))
        print("workspace MCP files: " + (", ".join(written) if written else "already carry the kaggle server"))
    print("Restart the agent (or open a new session in the dashboard CLI assistant) to load it.")
    return 0


def run_status(args) -> int:
    path = token_path()
    problem = token_file_problem(path)
    if os.environ.get(TOKEN_ENV):
        print(f"kaggle MCP: activated through the exported {TOKEN_ENV}")
    elif problem is None:
        print(f"kaggle MCP: activated, token stored at {path}")
    else:
        print(f"kaggle MCP: not activated ({path}: {problem})")
        if problem.startswith("insecure"):
            print(f"fix: chmod 600 {path}, or run `smith mcp kaggle activate` again")
        else:
            print("activate: smith mcp kaggle activate")
    if args.verify:
        token = os.environ.get(TOKEN_ENV) or read_token(path)
        if token:
            ok, detail = verify_token(token)
            print(f"verify: {'ok' if ok else 'failed'} ({detail})")
            return 0 if ok else 1
        print("verify: skipped, no usable token")
        return 1
    return 0


def run_deactivate(args) -> int:
    path = token_path()
    if path.is_dir() and not path.is_symlink():
        raise UserError(f"{path} is a directory, not a token file; remove it by hand")
    if path.is_symlink() or path.exists():
        path.unlink()
        print(f"removed: {path}")
    else:
        print(f"nothing to remove: {path}")
    if os.environ.get(TOKEN_ENV):
        print(f"note: {TOKEN_ENV} is still exported in this shell")
    return 0

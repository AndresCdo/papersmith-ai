"""Backend of the math panel's Socratic tutor (the `math-tutor` skill).

The command center stores what the reader brings — hand-written images and the
conversation, under ``.papersmith/math-tutor/`` — and runs ONE headless turn of
the `math-tutor` agent per message with the reader's own agent CLI, so no API
key ever lives in the dashboard:

* ``claude -p`` (preferred): the agent's doctrine as the system prompt, only the
  ``Read`` tool, the turn's JSON shape as ``--json-schema``, no session, no MCP,
  and only local settings (user plugins and hooks would multiply the cost of a
  tutoring turn by two orders of magnitude);
* ``pi -p`` (fallback): the same prompt, no tools, images passed as ``@file``,
  and the JSON turn read out of its text.

The agent never writes; this module is the only writer, and only of the
reader's uploads and the thread.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from . import math_view
from .terminal import find_executable, session_env

FOLDER = (".papersmith", "math-tutor")
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGES_PER_TURN = 6
MAX_MESSAGE = 8000
MAX_TURNS = 400
HISTORY_IN_PROMPT = 8
TIMEOUT_SECONDS = 300
MODES = ("ask", "explain", "evaluate")

_IMAGE_TYPES = (
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"RIFF", "webp", "image/webp"),
)
_ID = re.compile(r"[0-9a-f]{16}(?:\.(?:png|jpg|webp))?")

LEVELS = ("sin-evidencia", "reconoce", "explica", "deriva", "justifica")

TURN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["image_reading", "reply", "question", "latex", "assessment",
                 "novelty_link", "next_step"],
    "properties": {
        "image_reading": {"type": "string"},
        "reply": {"type": "string"},
        "question": {"type": "string"},
        "latex": {"type": "array", "items": {"type": "string"}},
        "assessment": {
            "type": "object",
            "additionalProperties": False,
            "required": ["level", "label", "evidence", "gaps"],
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 4},
                "label": {"type": "string", "enum": list(LEVELS)},
                "evidence": {"type": "string"},
                "gaps": {"type": "array", "items": {"type": "string"}},
            },
        },
        "novelty_link": {"type": "string"},
        "next_step": {"type": "string"},
    },
}

_FALLBACK_DOCTRINE = (
    "You are a Socratic math tutor. Read the reader's hand-written images, transcribe "
    "them into KaTeX-compatible LaTeX, ask exactly one question per turn, give the "
    "smallest useful hint, assess understanding 0-4 with evidence quoted from the "
    "reader, and always tie the step to the paper's novelty. Answer with one JSON "
    "object only."
)

_lock = threading.Lock()


class TutorError(Exception):
    """A request the tutor refuses, or an agent answer it cannot use."""


def folder(root: Path) -> Path:
    return Path(root).joinpath(*FOLDER)


# --------------------------------------------------------------------------
# images
# --------------------------------------------------------------------------
def save_image(root: Path, data_url: Any) -> dict[str, str]:
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        raise TutorError("send the image as a data:image/... URL")
    head, _, payload = data_url.partition(",")
    if ";base64" not in head:
        raise TutorError("the image must be base64-encoded")
    if len(payload) > (MAX_IMAGE_BYTES * 4) // 3 + 8:
        raise TutorError(f"images are limited to {MAX_IMAGE_BYTES // (1024 * 1024)} MiB")
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as error:
        raise TutorError("the image is not valid base64") from error
    if len(data) > MAX_IMAGE_BYTES:
        raise TutorError(f"images are limited to {MAX_IMAGE_BYTES // (1024 * 1024)} MiB")
    kind = next(((ext, mime) for magic, ext, mime in _IMAGE_TYPES
                 if data.startswith(magic) and (ext != "webp" or data[8:12] == b"WEBP")), None)
    if kind is None:
        raise TutorError("only PNG, JPEG and WebP images are accepted")
    ext, mime = kind
    if not _well_formed(ext, data):
        raise TutorError("the image is malformed or carries trailing data")
    image_id = hashlib.sha256(data).hexdigest()[:16]
    target = folder(root) / "images" / f"{image_id}.{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)
    return {"id": image_id, "type": mime}


def _well_formed(ext: str, data: bytes) -> bool:
    """The whole file is the image: it ends where its format says it ends, so
    a valid header followed by HTML or script (a polyglot) is refused."""
    if ext == "png":
        return data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82")
    if ext == "jpg":
        return data.endswith(b"\xff\xd9")
    return len(data) >= 12 and int.from_bytes(data[4:8], "little") + 8 == len(data)


def image_path(root: Path, image_id: Any) -> Path:
    if not isinstance(image_id, str) or not _ID.fullmatch(image_id):
        raise TutorError("unknown image")
    stem = image_id.split(".")[0]
    for _, ext, _ in _IMAGE_TYPES:
        candidate = folder(root) / "images" / f"{stem}.{ext}"
        if candidate.is_file():
            return candidate
    raise TutorError("unknown image")


def image_type(path: Path) -> str:
    return {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}[path.suffix[1:]]


# --------------------------------------------------------------------------
# thread
# --------------------------------------------------------------------------
def _thread_file(root: Path) -> Path:
    return folder(root) / "thread.json"


def load_thread(root: Path) -> dict[str, Any]:
    try:
        data = json.loads(_thread_file(root).read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("turns"), list):
            return data
    except (OSError, ValueError):
        pass
    return {"turns": []}


def _save_thread(root: Path, thread: dict[str, Any]) -> None:
    path = _thread_file(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    thread["turns"] = thread["turns"][-MAX_TURNS:]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(thread, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def reset_thread(root: Path) -> None:
    # Under the turn lock, so a reset during a running turn is not undone by it.
    with _lock:
        _save_thread(root, {"turns": []})


# --------------------------------------------------------------------------
# prompt
# --------------------------------------------------------------------------
def system_prompt(root: Path) -> str:
    parts = []
    for rel in (".claude/agents/math-tutor.md", "skills/math-tutor/SKILL.md"):
        try:
            parts.append(Path(root, rel).read_text(encoding="utf-8"))
        except OSError:
            continue
    doctrine = "\n\n---\n\n".join(parts) if parts else _FALLBACK_DOCTRINE
    return (doctrine + "\n\n---\n\nYou are running headless inside the dashboard's math panel "
            "as the Socratic tutor. Answer with exactly one JSON object in the turn shape; "
            "every formula is KaTeX-compatible LaTeX.")


def build_prompt(root: Path, message: str, image_rels: list[str], mode: str,
                 thread: dict[str, Any]) -> str:
    view = math_view.build(root)
    paper = {"source": view["source"], "lema": view["lema"], "novelty": view["novelty"],
             "equations": [{k: e[k] for k in ("tag", "heading", "latex", "connection")}
                           for e in view["equations"][:12]]}
    history = []
    for turn in thread["turns"][-HISTORY_IN_PROMPT:]:
        if turn.get("role") == "reader":
            history.append(f"READER ({turn.get('mode')}): {turn.get('message', '')[:1500]}"
                           + (f" [images: {', '.join(turn.get('images') or [])}]" if turn.get("images") else ""))
        else:
            a = turn.get("assessment") or {}
            history.append(f"TUTOR: asked \"{turn.get('question', '')[:500]}\"; "
                           f"assessed {a.get('level')} ({a.get('label')}): {a.get('evidence', '')[:300]}")
    images = "\n".join(f"- {rel}" for rel in image_rels) or "- (none)"
    return (
        f"mode: {mode}\n\n"
        f"The paper's mathematics (from /api/model/math):\n{json.dumps(paper, ensure_ascii=False)}\n\n"
        f"Conversation so far (oldest first):\n" + ("\n".join(history) or "(first turn)") + "\n\n"
        f"Images the reader attached this turn (read each with the Read tool before answering):\n"
        f"{images}\n\n"
        f"The reader says:\n{message}\n"
    )


# --------------------------------------------------------------------------
# agent runners
# --------------------------------------------------------------------------
def claude_argv(claude: str, system: str, prompt: str) -> list[str]:
    return [claude, "-p", "--output-format", "json", "--no-session-persistence",
            "--strict-mcp-config", "--setting-sources", "local",
            "--tools", "Read", "--allowedTools", "Read",
            "--system-prompt", system, "--json-schema", json.dumps(TURN_SCHEMA), prompt]


def extract_turn(text: str) -> dict[str, Any] | None:
    """The first JSON object in ``text`` that has a ``reply`` key."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(value, dict) and "reply" in value:
            return value
    return None


def run_agent(root: Path, system: str, prompt: str, images: list[Path]) -> tuple[dict[str, Any], str]:
    try:
        return _run_agent(root, system, prompt, images)
    except OSError as error:
        raise TutorError(f"could not start the agent CLI: {error}") from error


def _run_agent(root: Path, system: str, prompt: str, images: list[Path]) -> tuple[dict[str, Any], str]:
    claude = find_executable("claude")
    if claude:
        # stdin closed: `claude -p` appends whatever it can read there to the prompt.
        done = subprocess.run(claude_argv(claude, system, prompt), cwd=str(root),
                              env=session_env("claude", root), capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=TIMEOUT_SECONDS, check=False)
        try:
            payload = json.loads(done.stdout)
        except ValueError as error:
            raise TutorError(f"claude answered no JSON (exit {done.returncode}): "
                             f"{(done.stderr or done.stdout)[:300]}") from error
        if not isinstance(payload, dict):
            raise TutorError("claude answered JSON that is not a result object")
        if payload.get("is_error"):
            raise TutorError(f"claude refused: {str(payload.get('result'))[:300]}")
        turn = payload.get("structured_output") or extract_turn(str(payload.get("result") or ""))
        return turn, "claude"
    pi = find_executable("pi")
    if pi:
        argv = [pi, "-p", "--no-session", "--no-tools", "--system-prompt", system,
                *[f"@{path}" for path in images], prompt]
        done = subprocess.run(argv, cwd=str(root), env=session_env("pi", root),
                              capture_output=True, text=True, stdin=subprocess.DEVNULL,
                              timeout=TIMEOUT_SECONDS, check=False)
        return extract_turn(done.stdout), "pi"
    raise TutorError("no agent CLI found: install Claude Code (claude) or Pi (pi)")


def _valid(turn: Any) -> dict[str, Any]:
    if not isinstance(turn, dict):
        raise TutorError("the tutor's answer was not a JSON turn")
    for key in ("image_reading", "reply", "question", "novelty_link", "next_step"):
        if not isinstance(turn.get(key), str):
            raise TutorError(f"the tutor's answer has no text `{key}`")
    latex = turn.get("latex")
    if not isinstance(latex, list) or not all(isinstance(item, str) for item in latex):
        raise TutorError("the tutor's answer has no `latex` list")
    a = turn.get("assessment")
    if not (isinstance(a, dict) and type(a.get("level")) is int and 0 <= a["level"] <= 4
            and isinstance(a.get("evidence"), str) and isinstance(a.get("gaps"), list)
            and all(isinstance(gap, str) for gap in a["gaps"])):
        raise TutorError("the tutor's answer has no usable `assessment`")
    a["label"] = LEVELS[a["level"]]
    return {key: turn[key] for key in TURN_SCHEMA["required"]}


def run_turn(root: Path, message: Any, image_ids: Any, mode: Any, *,
             runner: Callable[..., tuple[Any, str]] | None = None) -> dict[str, Any]:
    root = Path(root)
    if mode not in MODES:
        raise TutorError(f"mode must be one of {', '.join(MODES)}")
    if not isinstance(message, str) or not message.strip() and not image_ids:
        raise TutorError("write a message or attach an image")
    if not isinstance(image_ids, list):
        raise TutorError("`images` must be a list of image ids")
    if len(image_ids) > MAX_IMAGES_PER_TURN:
        raise TutorError(f"attach at most {MAX_IMAGES_PER_TURN} images per turn")
    paths = [image_path(root, image_id) for image_id in image_ids]
    stems = [path.stem for path in paths]
    rels = [path.relative_to(root).as_posix() for path in paths]
    message = message.strip()[:MAX_MESSAGE]
    with _lock:
        thread = load_thread(root)
        prompt = build_prompt(root, message, rels, mode, thread)
        answer, agent = (runner or run_agent)(root, system_prompt(root), prompt, paths)
        turn = _valid(answer)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        thread["turns"].append({"role": "reader", "at": now, "mode": mode, "message": message,
                                "images": stems})
        thread["turns"].append({"role": "tutor", "at": now, "agent": agent, **turn})
        _save_thread(root, thread)
    return {**turn, "agent": agent, "at": now}


__all__ = ["TutorError", "save_image", "image_path", "image_type", "load_thread",
           "reset_thread", "run_turn", "run_agent", "extract_turn", "claude_argv",
           "TURN_SCHEMA", "MODES"]

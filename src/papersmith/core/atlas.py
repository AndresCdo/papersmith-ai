"""``papersmith atlas build``: regenerate a workspace's SOTA atlas page.

The same action as the dashboard's "Regenerar grafo" button. The rebuild lives
in the workspace's command center (``skills/_core/command_center/atlas_build.py``)
and runs the workspace's own plausibility checker and renderer; this command
only resolves the workspace and runs that module from its root. Both are
stdlib-only, so the current interpreter is enough.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ..errors import UserError
from . import fs

#: The workspace module that performs the rebuild.
ATLAS_BUILD_MODULE = "skills._core.command_center.atlas_build"
ATLAS_BUILD_ENTRY = Path("skills") / "_core" / "command_center" / "atlas_build.py"


def run_build(args) -> int:
    workspace = Path(args.directory).expanduser().resolve()
    if not fs.is_dir(workspace):
        raise UserError(f"not a directory: {workspace}")
    if not fs.is_regular_file(workspace / ATLAS_BUILD_ENTRY):
        raise UserError(f"{ATLAS_BUILD_ENTRY} not found in {workspace}: "
                        "run `papersmith upgrade` to refresh the workspace kit")
    argv = [sys.executable, "-B", "-m", ATLAS_BUILD_MODULE, "--root", str(workspace)]
    if args.json:
        argv.append("--json")
    completed = subprocess.run(argv, cwd=str(workspace), capture_output=True, text=True,
                               check=False)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return 0 if completed.returncode == 0 else 1


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        "atlas",
        help="SOTA atlas actions (the dashboard's graph buttons, from the terminal)",
        description="SOTA atlas actions shared with the Paper Command Center.",
    )
    actions = parser.add_subparsers(dest="atlas_action", metavar="<action>")
    actions.required = True
    build = actions.add_parser(
        "build",
        help="check sota-pool/atlas.json and re-render sota-pool/atlas.html",
        description=("Run the workspace's plausibility checker on sota-pool/atlas.json "
                     "(with --pool sota-pool/candidates.json when it exists) and, only "
                     "when it is green, re-render sota-pool/atlas.html. Exit 0 when the "
                     "page was written, 1 otherwise."),
    )
    build.add_argument("--json", action="store_true", help="print the result as JSON")
    build.add_argument("directory", nargs="?", default=".", metavar="<dir>")
    build.set_defaults(handler=run_build)


__all__ = ["register", "run_build", "ATLAS_BUILD_MODULE", "ATLAS_BUILD_ENTRY"]

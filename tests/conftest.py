"""Shared pytest fixtures.

The papersmith CLI uses a src-layout; expose ``src/`` so tests import the
package without an install step. The repository root is exposed too: the Paper
Command Center ships as ``skills/_core/command_center/`` (a kit tree member
that must stay importable standalone from a workspace root), not as a
``papersmith`` submodule.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The suite initializes and upgrades workspaces from this checkout, which is
# usually carrying uncommitted edits, and from throwaway kits outside git. Both
# refuse by design without an explicit override (`--allow-dirty-kit`); this is
# that override for the test process and the CLI children it spawns. The tests
# that pin the refusal itself (tests/test_kit_provenance.py) remove it first.
import os  # noqa: E402

os.environ.setdefault("PAPERSMITH_ALLOW_DIRTY_KIT", "1")

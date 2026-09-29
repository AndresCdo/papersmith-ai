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

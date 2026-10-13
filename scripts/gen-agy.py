#!/usr/bin/env python3
"""Generate or check the Antigravity (agy) projection for a papersmith workspace."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Re-use gen-antigravity's entrypoint
import importlib.util

spec = importlib.util.spec_from_file_location(
    "gen_antigravity", ROOT / "scripts" / "gen-antigravity.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load scripts/gen-antigravity.py")
gen_antigravity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_antigravity)

if __name__ == "__main__":
    raise SystemExit(gen_antigravity.main())

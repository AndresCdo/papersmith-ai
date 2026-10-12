"""X10: no test writes the shipped implementation engine.

Five mutation tests used to write a broken engine into
`skills/_core/implementation/engine/implementation_engine.py` and restore it in
a cleanup. Under `-n 8 --dist loadfile` every other worker reads that file, so
an unrelated test intermittently printed nothing or sealed a different digest,
and a killed run left the mutation in the tree. They now run a scratch forge
(`tests/scratch_forge.py`).

This holds the class shut: it parses every test module and refuses a
`write_text`/`write_bytes` call whose receiver is named `ENGINE`, the name
every test file in this suite binds to the shipped engine path. A mutation
belongs in `scratch_forge.build`.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WRITERS = frozenset({"write_text", "write_bytes"})


def _receiver_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def engine_writes(source: str) -> list[int]:
    """Line numbers of `<...>ENGINE.write_text(...)`/`write_bytes(...)`."""
    lines = []
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in WRITERS
                and _receiver_name(node.func.value) == "ENGINE"):
            lines.append(node.lineno)
    return lines


class ShippedEngineIsNeverWrittenTests(unittest.TestCase):

    def test_no_test_module_writes_the_shipped_engine(self):
        found = {}
        for path in sorted(TESTS.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            lines = engine_writes(path.read_text(encoding="utf-8"))
            if lines:
                found[str(path.relative_to(TESTS))] = lines
        self.assertEqual(found, {}, "write the mutation into scratch_forge.build instead")

    def test_the_detector_sees_both_spellings(self):
        self.assertEqual(engine_writes("ENGINE.write_text('x')\n"), [1])
        self.assertEqual(engine_writes("x = 1\nself.ENGINE.write_bytes(b'x')\n"), [2])
        self.assertEqual(engine_writes("scratch_engine.write_text('x')\n"), [])


if __name__ == "__main__":
    unittest.main()

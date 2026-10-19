"""A scratch copy of the forge for tests that would otherwise write the
shipped tree: a mutated engine, or a module dropped into a shipped skill
(X3, X10).

A mutation test proves a guard is reachable by running the engine with that
guard broken. Writing the broken source into the shipped
`skills/_core/implementation/engine/implementation_engine.py`, even with a
byte-identical restore in a cleanup, breaks every other test file that reads
the engine while the mutation is on disk -- in a parallel run that is most of
them, and the symptom (an empty stdout, a different seal digest) points
nowhere near the cause. A killed run also leaves the mutation behind.

`build` gives the test its own forge instead. The copy keeps the real nesting,
because the engine derives `FORGE_ROOT` from its own path (`parents[4]`) and
refuses a target outside `<forge>/implementations`: the whole
`_core/implementation` tree is copied, the chosen launcher is copied beside
it, and the skills the engine only reads by path are linked, not copied.

A launcher copied here has no `impl_profile.py` beside it, so the caller
names the profile explicitly through IMPLEMENTATION_DOMAIN_PROFILE, as the
fixture-profile tests already do.
"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import orphan_sweep

FORGE = Path(__file__).resolve().parents[1]
CORE = FORGE / "skills" / "_core" / "implementation"
ENGINE = CORE / "engine" / "implementation_engine.py"

#: Skills the engine imports read-only by path from `<forge>/skills`.
READ_ONLY_SKILLS = ("remote-execution",)


def build(case: unittest.TestCase, engine_source: str | None, launcher: Path,
          *, prefix: str = "mutation-forge-",
          copied_skills: tuple[str, ...] = ()) -> tuple[Path, Path]:
    """A scratch forge running `engine_source`; returns `(forge, launcher)`.

    `engine_source=None` runs the shipped source unchanged. A skill named in
    `copied_skills` is copied instead of linked, for a test that must add a
    file to it (a dropped adapter module) without writing the shipped tree.
    Removed by a cleanup registered on `case`. The shipped tree is only
    read, never written."""
    forge = orphan_sweep.allocate(prefix)
    case.addCleanup(shutil.rmtree, forge, ignore_errors=True)
    core = forge / CORE.relative_to(FORGE)
    shutil.copytree(CORE, core, ignore=shutil.ignore_patterns("__pycache__"))
    if engine_source is not None:
        (core / ENGINE.relative_to(CORE)).write_text(engine_source, encoding="utf-8")
    scratch_launcher = forge / launcher.relative_to(FORGE)
    scratch_launcher.parent.mkdir(parents=True)
    shutil.copy2(launcher, scratch_launcher)
    for name in READ_ONLY_SKILLS:
        if name in copied_skills:
            shutil.copytree(FORGE / "skills" / name, forge / "skills" / name,
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            (forge / "skills" / name).symlink_to(FORGE / "skills" / name,
                                                 target_is_directory=True)
    (forge / "implementations").mkdir()
    return forge, scratch_launcher

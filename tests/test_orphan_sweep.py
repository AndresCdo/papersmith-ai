"""orphan_sweep removes only the scratch directories the suite owns (#60).

The sweep used to remove any untracked `_`-prefixed entry older than an
hour under `implementations/` and `skills/*/scripts`, where an operator's
own repositories also live. Ownership is now a marker written into a
directory under the checkout's own temporary root; every test below runs
against an isolated root, never the live one.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import orphan_sweep
import scratch_forge

LAUNCHER = scratch_forge.FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"


class OperatorRepositoriesAreNeverSweptTests(unittest.TestCase):
    """Runs the module's real entry point from a copy rooted at an isolated
    forge, so its own roots -- whatever they are -- are the isolated ones."""

    def test_an_old_untracked_operator_repository_survives_the_sweep(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        forge = Path(holder.name).resolve()
        (forge / "tests").mkdir()
        shutil.copy2(orphan_sweep.__file__, forge / "tests" / "orphan_sweep.py")
        repos = [forge / "implementations" / "_operator_repo",
                 forge / "skills" / "mine" / "scripts" / "_notes"]
        a_month_ago = time.time() - 30 * 24 * 3600
        for repo in repos:
            (repo / ".git").mkdir(parents=True)
            (repo / "research.txt").write_text("operator work", encoding="utf-8")
            os.utime(repo, (a_month_ago, a_month_ago))
        spec = importlib.util.spec_from_file_location(
            "isolated_orphan_sweep", forge / "tests" / "orphan_sweep.py")
        isolated = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(isolated)

        with mock.patch.dict(os.environ):
            os.environ.pop("FORGE_SKIP_ORPHAN_SWEEP", None)
            isolated.sweep_and_report()

        for repo in repos:
            self.assertTrue((repo / "research.txt").exists(), f"{repo} was deleted")

    def test_the_temporary_root_is_outside_the_checkout_and_namespaced_by_it(self) -> None:
        root = orphan_sweep.SUITE_TEMP_ROOT
        self.assertFalse(root.is_relative_to(orphan_sweep.FORGE_ROOT))
        self.assertEqual(root.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(root.name.startswith("papersmith-suite-"))


class _IsolatedRoot(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.base = Path(holder.name).resolve()
        self.root = self.base / "suite"
        self.root.mkdir(mode=0o700)
        patcher = mock.patch.object(orphan_sweep, "SUITE_TEMP_ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _artifact(self, name: str, marker: bytes | None) -> Path:
        path = self.root / name
        path.mkdir(parents=True)
        (path / "sentinel").write_bytes(b"preserve unless owned")
        if marker is not None:
            (path / orphan_sweep.OWNER_MARKER).write_bytes(marker)
        os.utime(path, (1000, 1000))
        return path


class SweepRemovesOrphansTests(_IsolatedRoot):
    def test_an_old_owned_fixture_is_removed(self) -> None:
        orphan = orphan_sweep.allocate("killed-")
        os.utime(orphan, (1000, 1000))
        self.assertEqual(orphan_sweep.sweep(now=10000), [str(orphan)])
        self.assertFalse(orphan.exists())

    def test_a_fresh_owned_fixture_survives(self) -> None:
        live = orphan_sweep.allocate("live-")
        os.utime(live, (9999, 9999))
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(live.exists())

    def test_an_absent_root_is_not_an_error(self) -> None:
        self.root.rmdir()
        self.assertEqual(orphan_sweep.sweep(), [])

    def test_a_fixture_its_owner_removes_mid_sweep_is_not_reported(self) -> None:
        owned = orphan_sweep.allocate("concurrent-")
        os.utime(owned, (1000, 1000))
        real = Path.lstat

        def owner_cleans_up(path: Path) -> os.stat_result:
            if path == owned:
                shutil.rmtree(owned)
            return real(path)

        with mock.patch.object(Path, "lstat", owner_cleans_up):
            self.assertEqual(orphan_sweep.sweep(now=10000), [])

    def test_a_failed_removal_is_not_reported(self) -> None:
        owned = orphan_sweep.allocate("blocked-")
        os.utime(owned, (1000, 1000))
        with mock.patch.object(shutil, "rmtree", side_effect=PermissionError):
            self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(owned.exists())


class OwnershipTests(_IsolatedRoot):
    def test_the_prefix_and_the_exact_marker_are_both_required(self) -> None:
        paths = [self._artifact(name, marker) for name, marker in (
            (orphan_sweep.OWNED_PREFIX + "owned", orphan_sweep.OWNER_CONTENT),
            (orphan_sweep.OWNED_PREFIX + "unmarked", None),
            ("_operator_repo", orphan_sweep.OWNER_CONTENT),
            ("_legacy_123", None),
        )]
        self.assertEqual(orphan_sweep.sweep(now=10000), [str(paths[0])])
        self.assertTrue(all((p / "sentinel").exists() for p in paths[1:]))

    def test_invalid_marker_bytes_are_preserved(self) -> None:
        paths = [self._artifact(orphan_sweep.OWNED_PREFIX + str(i), content) for i, content in
                 enumerate((b"", b"{}", b"\xff", orphan_sweep.OWNER_CONTENT + b"extra"))]
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(all(p.exists() for p in paths))

    def test_a_marker_that_is_not_a_regular_file_is_preserved(self) -> None:
        path = self._artifact(orphan_sweep.OWNED_PREFIX + "directory", None)
        (path / orphan_sweep.OWNER_MARKER).mkdir()
        os.utime(path, (1000, 1000))
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(path.exists())

    def test_a_symlinked_marker_preserves_the_candidate_and_its_target(self) -> None:
        target = self.base / "external-marker"
        target.write_bytes(orphan_sweep.OWNER_CONTENT)
        path = self._artifact(orphan_sweep.OWNED_PREFIX + "linked-marker", None)
        (path / orphan_sweep.OWNER_MARKER).symlink_to(target)
        os.utime(path, (1000, 1000))
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(path.exists())
        self.assertEqual(target.read_bytes(), orphan_sweep.OWNER_CONTENT)

    def test_a_symlinked_candidate_preserves_its_target(self) -> None:
        target = self._artifact("external", orphan_sweep.OWNER_CONTENT)
        moved = self.base / "external-candidate"
        target.rename(moved)
        link = self.root / (orphan_sweep.OWNED_PREFIX + "link")
        link.symlink_to(moved, target_is_directory=True)
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertTrue(link.is_symlink())
        self.assertTrue((moved / "sentinel").exists())

    def test_a_regular_file_with_the_prefix_is_preserved(self) -> None:
        path = self.root / (orphan_sweep.OWNED_PREFIX + "file")
        path.write_bytes(orphan_sweep.OWNER_CONTENT)
        os.utime(path, (1000, 1000))
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertEqual(path.read_bytes(), orphan_sweep.OWNER_CONTENT)

    def test_a_symlinked_root_is_refused_by_sweep_and_allocate(self) -> None:
        owned = self._artifact(orphan_sweep.OWNED_PREFIX + "external", orphan_sweep.OWNER_CONTENT)
        external = self.base / "external"
        self.root.rename(external)
        self.root.symlink_to(external, target_is_directory=True)
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        with self.assertRaises(OSError):
            orphan_sweep.allocate("blocked-")
        self.assertTrue((external / owned.name / "sentinel").exists())

    def test_a_linked_ancestor_is_refused_before_allocate_writes(self) -> None:
        external = self.base / "external"
        external.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(external, target_is_directory=True)
        with mock.patch.object(orphan_sweep, "SUITE_TEMP_ROOT", alias / "suite"):
            with self.assertRaises(OSError):
                orphan_sweep.allocate("blocked-")
        self.assertEqual(list(external.iterdir()), [])


class RootPrivacyTests(_IsolatedRoot):
    """The root's path is predictable in a shared directory, so another user
    could create it first; such a root is never written into or swept."""

    def _old_owned(self) -> Path:
        return self._artifact(orphan_sweep.OWNED_PREFIX + "old", orphan_sweep.OWNER_CONTENT)

    def test_allocate_creates_the_root_private(self) -> None:
        self.root.rmdir()
        self.addCleanup(os.umask, os.umask(0o022))  # the common default, not this shell's
        orphan_sweep.allocate("first-")
        entry = self.root.lstat()
        self.assertEqual(entry.st_uid, os.getuid())
        self.assertEqual(stat.S_IMODE(entry.st_mode) & 0o077, 0)

    def test_a_root_others_can_enter_is_refused(self) -> None:
        owned = self._old_owned()
        self.root.chmod(0o755)
        with self.assertRaises(OSError):
            orphan_sweep.allocate("blocked-")
        self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertEqual(list(self.root.iterdir()), [owned])
        self.assertTrue((owned / "sentinel").exists())

    def test_a_root_another_user_owns_is_refused(self) -> None:
        owned = self._old_owned()
        with mock.patch.object(os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaises(OSError):
                orphan_sweep.allocate("blocked-")
            self.assertEqual(orphan_sweep.sweep(now=10000), [])
        self.assertEqual(list(self.root.iterdir()), [owned])
        self.assertTrue((owned / "sentinel").exists())


class AllocationTests(_IsolatedRoot):
    def test_allocation_is_unique_marked_and_keeps_the_label(self) -> None:
        paths = [orphan_sweep.allocate("caller-label-") for _ in range(2)]
        self.assertNotEqual(*paths)
        for path in paths:
            self.assertEqual(path.parent, self.root)
            self.assertTrue(path.name.startswith(orphan_sweep.OWNED_PREFIX + "caller-label-"))
            self.assertEqual((path / orphan_sweep.OWNER_MARKER).read_bytes(),
                             orphan_sweep.OWNER_CONTENT)

    def test_an_interrupted_allocation_is_owned_and_swept_once_old(self) -> None:
        old = orphan_sweep.allocate("interrupted-")
        fresh = orphan_sweep.allocate("interrupted-")
        os.utime(old, (1000, 1000))
        os.utime(fresh, (9999, 9999))
        self.assertEqual(orphan_sweep.sweep(now=10000), [str(old)])
        self.assertTrue(fresh.exists())

    def test_a_scratch_forge_is_marked_before_an_interrupted_copy(self) -> None:
        case = unittest.TestCase()
        self.addCleanup(case.doCleanups)
        with mock.patch.object(scratch_forge.shutil, "copytree", side_effect=InterruptedError):
            with self.assertRaises(InterruptedError):
                scratch_forge.build(case, None, LAUNCHER)
        [path] = list(self.root.iterdir())
        self.assertEqual((path / orphan_sweep.OWNER_MARKER).read_bytes(), orphan_sweep.OWNER_CONTENT)

    def test_a_scratch_forge_lives_under_the_root_and_is_cleaned_up(self) -> None:
        case = unittest.TestCase()
        self.addCleanup(case.doCleanups)
        forge, cli = scratch_forge.build(case, None, LAUNCHER, prefix="integration-")
        self.assertEqual(forge.parent, self.root)
        self.assertIn("integration-", forge.name)
        self.assertTrue(cli.is_file())
        self.assertTrue((forge / "implementations").is_dir())
        case.doCleanups()
        self.assertFalse(forge.exists())


if __name__ == "__main__":
    unittest.main()

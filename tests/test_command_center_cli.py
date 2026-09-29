"""`papersmith ui` resolves the workspace backend, picks a port, and spawns it."""

from __future__ import annotations

import argparse
import shutil
import socket
import sys
import tempfile
import unittest
from pathlib import Path

from papersmith.cli import build_parser
from papersmith.core import ui as ui_command
from papersmith.errors import SourceError, UserError

REPOSITORY = Path(__file__).resolve().parent.parent
COMMAND_CENTER = REPOSITORY / "skills" / "_core" / "command_center"


def _seed_command_center(root: Path) -> None:
    destination = root / ui_command.COMMAND_CENTER_ENTRY.parent
    shutil.copytree(COMMAND_CENTER, destination)


class CommandCenterResolutionTests(unittest.TestCase):
    def new_dir(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def test_ui_is_registered_on_the_top_level_parser(self) -> None:
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        assert "ui" in subparsers.choices

    def test_missing_command_center_refuses_with_a_source_error(self) -> None:
        root = self.new_dir()
        with self.assertRaises(SourceError):
            ui_command.command_center_entry(root)

    def test_command_center_entry_resolves_when_present(self) -> None:
        root = self.new_dir()
        _seed_command_center(root)
        entry = ui_command.command_center_entry(root)
        assert entry.name == "server.py"
        assert entry.is_file()

    def test_run_cli_rejects_a_missing_workspace(self) -> None:
        args = argparse.Namespace(directory="/does/not/exist", host="127.0.0.1",
                                  port=8080, no_browser=True, export_static=None)
        with self.assertRaises(UserError):
            ui_command.run_cli(args)


class PortSelectionTests(unittest.TestCase):
    def test_port_is_free_after_the_probe_releases_it(self) -> None:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        assert ui_command.port_is_free("127.0.0.1", port)

    def test_find_available_port_skips_an_occupied_port(self) -> None:
        occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(occupied.close)
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        port = occupied.getsockname()[1]

        chosen = ui_command.find_available_port("127.0.0.1", port)

        assert chosen > port

    def test_find_available_port_refuses_when_the_scan_is_exhausted(self) -> None:
        with self.assertRaises(UserError):
            ui_command.find_available_port("127.0.0.1", 9000, attempts=0)


class ServerArgvTests(unittest.TestCase):
    def test_argv_carries_root_host_and_port(self) -> None:
        argv = ui_command.build_server_argv(Path("/tmp/paper"), "127.0.0.1", 8123,
                                            no_browser=True)

        assert argv[0].endswith("python") or "python" in argv[0]
        assert ui_command.COMMAND_CENTER_MODULE in argv
        assert "--root" in argv and "/tmp/paper" in argv
        assert "--port" in argv and "8123" in argv
        assert "--no-browser" in argv

    def test_argv_omits_no_browser_when_a_browser_is_wanted(self) -> None:
        argv = ui_command.build_server_argv(Path("/tmp/paper"), "127.0.0.1", 8123,
                                            no_browser=False)
        assert "--no-browser" not in argv

    def test_argv_carries_export_static(self) -> None:
        argv = ui_command.build_server_argv(Path("/tmp/paper"), "127.0.0.1", 8123,
                                            no_browser=True, export_static="/tmp/out")
        assert "--export-static" in argv and "/tmp/out" in argv


class WorkspaceInterpreterTests(unittest.TestCase):
    def new_dir(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        return Path(holder.name).resolve()

    def seed_venv(self, root: Path) -> Path:
        interpreter = root / ".venv" / "bin" / "python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
        interpreter.chmod(0o755)
        return interpreter

    def test_workspace_venv_interpreter_is_preferred(self) -> None:
        root = self.new_dir()
        interpreter = self.seed_venv(root)

        assert ui_command.workspace_interpreter(root) == str(interpreter)

    def test_missing_venv_falls_back_to_the_running_interpreter(self) -> None:
        root = self.new_dir()

        assert ui_command.workspace_interpreter(root) == sys.executable

    def test_run_cli_spawns_the_workspace_interpreter(self) -> None:
        root = self.new_dir()
        _seed_command_center(root)
        interpreter = self.seed_venv(root)
        captured: list[list[str]] = []
        original = ui_command._run_child
        ui_command._run_child = lambda argv, workspace: captured.append(argv) or 0
        self.addCleanup(setattr, ui_command, "_run_child", original)

        args = argparse.Namespace(directory=str(root), host="127.0.0.1", port=8080,
                                  no_browser=True, export_static=str(root / "out"))
        code = ui_command.run_cli(args)

        assert code == 0
        assert captured[0][0] == str(interpreter)


class ExportStaticEndToEndTests(unittest.TestCase):
    def test_export_static_spawns_the_workspace_backend(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        _seed_command_center(root)
        build = root / "ui" / "dist"
        build.mkdir(parents=True)
        (build / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
        destination = root / "exported"

        args = argparse.Namespace(directory=str(root), host="127.0.0.1", port=8080,
                                  no_browser=True, export_static=str(destination))
        code = ui_command.run_cli(args)

        assert code == 0
        assert (destination / "index.html").read_text(encoding="utf-8") == "<html>dashboard</html>"

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

    def seed_provisioning(self, root: Path) -> Path:
        """A workspace carrying the shipped provisioning script and its env."""
        script = root / "scripts" / "setup_env.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "from pathlib import Path\n"
            "PROJECT_ROOT = Path(__file__).resolve().parent.parent\n"
            "MAMBA_ROOT = PROJECT_ROOT / '.micromamba'\n"
            "ENV_NAME = 'papersmith'\n",
            encoding="utf-8")
        binary = root / ".micromamba" / "envs" / "papersmith" / "bin"
        binary.mkdir(parents=True)
        interpreter = binary / "python"
        interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
        interpreter.chmod(0o755)
        return interpreter

    def test_workspace_venv_interpreter_is_preferred(self) -> None:
        root = self.new_dir()
        interpreter = self.seed_venv(root)

        assert ui_command.workspace_interpreter(root) == str(interpreter)

    def test_the_provisioned_environment_outranks_a_venv(self) -> None:
        """The path nothing creates used to be preferred over the one the shipped
        script builds, which is how `papersmith ui` failed for every
        `pipx install .` user while passing in this repository's own checkout."""
        root = self.new_dir()
        self.seed_venv(root)
        interpreter = self.seed_provisioning(root)

        assert ui_command.workspace_interpreter(root) == str(interpreter)

    def test_the_interpreter_path_is_read_from_the_workspace_script(self) -> None:
        """Derived, never restated: the script that builds the environment is the
        one declaration of where it lives."""
        root = self.new_dir()
        self.seed_provisioning(root)

        derived = ui_command.provisioned_interpreters(root)

        assert derived, "the derivation found nothing in a workspace carrying the script"
        # Absolute, because the workspace's own script resolves it against its own
        # root; the caller must not re-join it to the workspace.
        assert derived[0] == root / ".micromamba" / "envs" / "papersmith" / "bin" / "python"

    def test_no_provisioning_script_derives_nothing(self) -> None:
        """Non-vacuity the other way: the derivation must not invent a path."""
        assert ui_command.provisioned_interpreters(self.new_dir()) == ()

    def test_a_backend_that_cannot_be_imported_is_refused_with_a_remedy(self) -> None:
        """A child dying on ModuleNotFoundError reports a Python fact to somebody
        who asked for a dashboard and names no remedy. This must name one."""
        root = self.new_dir()
        self.seed_provisioning(root)

        with self.assertRaises(UserError) as caught:
            ui_command.require_runnable_backend(root, "/bin/false")

        message = str(caught.exception)
        assert "setup_env.py install" in message, message
        assert "fastapi" in message, message

    def test_a_runnable_interpreter_is_not_refused(self) -> None:
        """The preflight must not block the command it is protecting."""
        root = self.new_dir()
        self.seed_provisioning(root)
        capable = ui_command.workspace_interpreter(
            REPOSITORY) if ui_command.backend_is_importable(sys.executable) else None

        if capable is None:
            self.skipTest("the running interpreter cannot import the backend here")
        ui_command.require_runnable_backend(root, sys.executable)

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

"""`smith mcp kaggle activate|status|deactivate` and the dashboard's use of the stored token."""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "skills" / "_core"))

from papersmith.cli import main  # noqa: E402
from papersmith.core import kaggle_mcp  # noqa: E402
from command_center import terminal  # noqa: E402

TOKEN = "KGAT_test0123456789abcdef"


class _Env(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.config = self.tmp / "config"
        patcher = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config)})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(kaggle_mcp.TOKEN_ENV, None)
        self.token_file = self.config / "papersmith" / "kaggle-mcp-token"

    def run_cli(self, *argv: str, stdin: str = "") -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(list(argv))
        return code, out.getvalue()


class ActivateTests(_Env):
    def test_activate_verifies_and_stores_the_token_privately(self) -> None:
        workspace = self.tmp / "ws"
        workspace.mkdir()
        with mock.patch.object(kaggle_mcp, "verify_token", return_value=(True, "quota read")):
            code, out = self.run_cli("mcp", "kaggle", "activate", "--token-stdin",
                                     "--workspace", str(workspace), stdin=TOKEN + "\n")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.token_file.read_text(encoding="utf-8").strip(), TOKEN)
        self.assertEqual(stat.S_IMODE(self.token_file.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.token_file.parent.stat().st_mode), 0o700)
        self.assertNotIn(TOKEN, out)
        servers = json.loads((workspace / ".mcp.json").read_text())["mcpServers"]
        self.assertIn("kaggle", servers)
        self.assertNotIn(TOKEN, (workspace / ".mcp.json").read_text())

    def test_a_rejected_token_writes_nothing(self) -> None:
        with mock.patch.object(kaggle_mcp, "verify_token", return_value=(False, "Unauthenticated")):
            code, out = self.run_cli("mcp", "kaggle", "activate", "--token-stdin", stdin=TOKEN)
        self.assertNotEqual(code, 0)
        self.assertIn("Unauthenticated", out)
        self.assertFalse(self.token_file.exists())
        self.assertNotIn(TOKEN, out)

    def test_an_empty_token_is_refused_before_any_check(self) -> None:
        with mock.patch.object(kaggle_mcp, "verify_token") as verify:
            code, _ = self.run_cli("mcp", "kaggle", "activate", "--token-stdin", stdin="  \n")
        self.assertNotEqual(code, 0)
        verify.assert_not_called()
        self.assertFalse(self.token_file.exists())

    def test_no_verify_stores_without_a_network_call(self) -> None:
        with mock.patch.object(kaggle_mcp, "verify_token") as verify:
            code, _ = self.run_cli("mcp", "kaggle", "activate", "--token-stdin", "--no-verify",
                                   stdin=TOKEN)
        self.assertEqual(code, 0)
        verify.assert_not_called()
        self.assertTrue(self.token_file.is_file())


class StatusAndDeactivateTests(_Env):
    def test_status_reports_the_source_without_the_token(self) -> None:
        code, out = self.run_cli("mcp", "kaggle", "status")
        self.assertEqual(code, 0)
        self.assertIn("not activated", out)
        kaggle_mcp.store_token(TOKEN)
        code, out = self.run_cli("mcp", "kaggle", "status")
        self.assertIn("activated", out)
        self.assertIn(str(self.token_file), out)
        self.assertNotIn(TOKEN, out)
        with mock.patch.dict(os.environ, {kaggle_mcp.TOKEN_ENV: TOKEN}):
            code, out = self.run_cli("mcp", "kaggle", "status")
        self.assertIn(kaggle_mcp.TOKEN_ENV, out)
        self.assertNotIn(TOKEN, out)

    def test_a_readable_by_others_file_is_reported_and_never_used(self) -> None:
        kaggle_mcp.store_token(TOKEN)
        self.token_file.chmod(0o644)
        self.assertIsNone(kaggle_mcp.read_token())
        code, out = self.run_cli("mcp", "kaggle", "status")
        self.assertIn("insecure", out)

    def test_a_symlinked_token_file_is_never_followed(self) -> None:
        real = self.tmp / "elsewhere"
        real.write_text(TOKEN, encoding="utf-8")
        real.chmod(0o600)
        self.token_file.parent.mkdir(parents=True)
        self.token_file.symlink_to(real)
        self.assertIsNone(kaggle_mcp.read_token())

    def test_rewriting_an_open_file_tightens_its_mode_before_writing(self) -> None:
        self.token_file.parent.mkdir(parents=True)
        self.token_file.write_text("old", encoding="utf-8")
        self.token_file.chmod(0o644)
        kaggle_mcp.store_token(TOKEN)
        self.assertEqual(stat.S_IMODE(self.token_file.stat().st_mode), 0o600)

    def test_a_symlinked_config_directory_is_refused(self) -> None:
        real = self.tmp / "real-dir"
        real.mkdir()
        self.config.mkdir()
        (self.config / "papersmith").symlink_to(real)
        code, _ = self.run_cli("mcp", "kaggle", "activate", "--token-stdin", "--no-verify", stdin=TOKEN)
        self.assertNotEqual(code, 0)
        self.assertEqual(list(real.iterdir()), [])

    def test_status_verify_without_a_token_fails(self) -> None:
        code, out = self.run_cli("mcp", "kaggle", "status", "--verify")
        self.assertEqual(code, 1)
        self.assertIn("skipped", out)

    def test_deactivate_removes_the_stored_token(self) -> None:
        kaggle_mcp.store_token(TOKEN)
        code, _ = self.run_cli("mcp", "kaggle", "deactivate")
        self.assertEqual(code, 0)
        self.assertFalse(self.token_file.exists())


class DashboardTests(_Env):
    def test_dashboard_sessions_receive_the_stored_token(self) -> None:
        kaggle_mcp.store_token(TOKEN)
        env = terminal.session_env("claude", self.tmp)
        self.assertEqual(env[kaggle_mcp.TOKEN_ENV], TOKEN)

    def test_an_exported_token_wins_over_the_stored_one(self) -> None:
        kaggle_mcp.store_token(TOKEN)
        with mock.patch.dict(os.environ, {kaggle_mcp.TOKEN_ENV: "KGAT_exported"}):
            env = terminal.session_env("shell", self.tmp)
        self.assertEqual(env[kaggle_mcp.TOKEN_ENV], "KGAT_exported")

    def test_no_token_is_injected_from_an_insecure_file(self) -> None:
        kaggle_mcp.store_token(TOKEN)
        self.token_file.chmod(0o640)
        env = terminal.session_env("claude", self.tmp)
        self.assertNotIn(kaggle_mcp.TOKEN_ENV, env)

    def test_both_sides_agree_on_the_token_location(self) -> None:
        self.assertEqual(terminal.remote_mcp_token_path(), kaggle_mcp.token_path())

    def test_the_shell_offers_the_activation_commands(self) -> None:
        self.assertIn("smith mcp kaggle activate", terminal.SHELL_QUICK)
        self.assertIn("smith mcp kaggle status", terminal.SHELL_QUICK)

    def test_the_experiments_view_reports_activation_without_the_token(self) -> None:
        from command_center import experiments_view
        workspace = self.tmp / "ws"
        workspace.mkdir()
        (workspace / ".mcp.json").write_text(json.dumps({"mcpServers": {"kaggle": {}}}))
        state = experiments_view.get_experiments_view(workspace)["remote_mcp"]
        self.assertFalse(state["activated"])
        self.assertEqual(state["registered"], [".mcp.json"])
        kaggle_mcp.store_token(TOKEN)
        view = experiments_view.get_experiments_view(workspace)
        self.assertEqual(view["remote_mcp"]["source"], "file")
        self.assertNotIn(TOKEN, json.dumps(view))


class PanelTests(unittest.TestCase):
    def render(self, state: dict) -> str:
        import subprocess
        script = REPO / "skills" / "_core" / "command_center" / "static" / "experiments-panel.js"
        code = ("global.window = {}; eval(require('fs').readFileSync(process.argv[1], 'utf8'));"
                "process.stdout.write(window.ExperimentsPanel.render({remote_mcp: JSON.parse(process.argv[2])}));")
        return subprocess.run(["node", "-e", code, str(script), json.dumps(state)],
                              capture_output=True, text=True, check=True).stdout

    def test_the_panel_explains_activation_and_sends_it_to_the_cli_assistant(self) -> None:
        html = self.render({"activated": False, "problem": "absent", "registered": [".mcp.json"],
                            "activate": "smith mcp kaggle activate", "status": "smith mcp kaggle status",
                            "env": "KAGGLE_API_TOKEN", "token_path": "/home/u/.config/papersmith/kaggle-mcp-token"})
        self.assertIn("Activar Kaggle por MCP", html)
        self.assertIn('data-exp-cli="smith mcp kaggle activate"', html)
        self.assertIn('data-exp-cli="smith mcp kaggle status --verify"', html)
        self.assertIn("kaggle.com/settings", html)
        self.assertIn("sin activar", html)
        active = self.render({"activated": True, "source": "file", "registered": []})
        self.assertIn("token guardado", active)
        self.assertIn("smith upgrade", active)

    def test_clicking_a_cli_button_runs_it_in_the_shell_assistant(self) -> None:
        source = (REPO / "skills" / "_core" / "command_center" / "static" / "experiments-panel.js").read_text()
        self.assertIn("window.sendToCli(cli.getAttribute('data-exp-cli'), true, { kind: 'shell' })", source)


if __name__ == "__main__":
    unittest.main()

"""The command center HTTP surface: payloads, SSE framing, static export.

Endpoints are exercised through their ASGI route functions rather than a live
socket, so these stay fast and hermetic. The end-to-end HTTP journey lives in
``scripts/command-center-smoke.sh``.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import server


def _routes(app) -> dict:
    return {route.path: route.endpoint for route in app.routes if hasattr(route, "path")}


def _json(response) -> dict:
    return json.loads(bytes(response.body).decode("utf-8"))


class ServerEndpointTests(unittest.TestCase):
    def new_workspace(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve()
        (root / "sections").mkdir(parents=True)
        (root / "paper").mkdir()
        return root

    def test_state_endpoint_returns_the_contract_payload(self) -> None:
        root = self.new_workspace()
        app = server.create_app(root)
        payload = _json(_routes(app)["/api/state"]())

        assert set(payload) >= {"paper_metadata", "sections", "gates", "pipeline_stages"}

    def test_health_endpoint_reports_the_summary(self) -> None:
        root = self.new_workspace()
        app = server.create_app(root)
        payload = _json(_routes(app)["/api/health/wiring"]())

        assert payload["summary"]["components_total"] >= 1
        assert payload["summary"]["state"] in ("HEALTHY", "DEGRADED", "BLOCKED")

    def test_health_endpoint_caches_between_calls(self) -> None:
        root = self.new_workspace()
        app = server.create_app(root, health_ttl=60.0)
        endpoint = _routes(app)["/api/health/wiring"]

        first = _json(endpoint())
        second = _json(endpoint())

        assert first == second

    def test_run_wiring_smoke_reports_absence_without_crashing(self) -> None:
        root = self.new_workspace()
        app = server.create_app(root)
        payload = _json(_routes(app)["/api/health/run-wiring-smoke"]())

        assert payload["available"] is False
        assert payload["exit_code"] is None
        assert "cli-paper-wiring-smoke.sh" in payload["detail"]

    def test_placeholder_root_is_served_without_a_build(self) -> None:
        root = self.new_workspace()
        app = server.create_app(root)
        body = _routes(app)["/"]()
        assert "Paper Command Center" in body

    def test_export_static_refuses_an_empty_build(self) -> None:
        root = self.new_workspace()
        destination = root / "exported"
        assert server.export_static(root, destination) == 2
        assert not destination.exists()

    def test_export_static_copies_a_workspace_build(self) -> None:
        root = self.new_workspace()
        build = root / "ui" / "dist"
        build.mkdir(parents=True)
        (build / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
        destination = root / "exported"

        assert server.export_static(root, destination) == 0
        assert (destination / "index.html").read_text(encoding="utf-8") == "<html>dashboard</html>"

    def test_resolve_static_dir_prefers_the_env_override(self) -> None:
        root = self.new_workspace()
        override = root / "override"
        override.mkdir()
        (override / "index.html").write_text("<html>override</html>", encoding="utf-8")
        previous = os.environ.get("PAPERSMITH_UI_DIST")
        os.environ["PAPERSMITH_UI_DIST"] = str(override)
        self.addCleanup(self._restore_env, previous)

        assert server.resolve_static_dir(root) == override

    def test_resolve_static_dir_returns_none_without_assets(self) -> None:
        root = self.new_workspace()
        previous = os.environ.pop("PAPERSMITH_UI_DIST", None)
        self.addCleanup(self._restore_env, previous)

        assert server.resolve_static_dir(root) is None

    @staticmethod
    def _restore_env(previous: str | None) -> None:
        if previous is None:
            os.environ.pop("PAPERSMITH_UI_DIST", None)
        else:
            os.environ["PAPERSMITH_UI_DIST"] = previous


class SseFramingTests(unittest.TestCase):
    def test_format_sse_repeats_the_event_type_in_the_body(self) -> None:
        frame = server.format_sse("state_update", {"revision": 2})

        assert frame.startswith("event: state_update\ndata: ")
        assert frame.endswith("\n\n")
        body = json.loads(frame.split("data: ", 1)[1].strip())
        assert body == {"type": "state_update", "payload": {"revision": 2}}

    def test_event_stream_emits_ready_then_a_published_event(self) -> None:
        class FakeRequest:
            async def is_disconnected(self) -> bool:
                return False

        async def scenario() -> list[str]:
            bus = server.EventBus()
            bus.bind_loop(asyncio.get_running_loop())
            stream = server._event_stream(FakeRequest(), bus, Path("/tmp/x"))
            frames = [await anext(stream)]
            bus.publish("state_update", {"revision": 1})
            frames.append(await asyncio.wait_for(anext(stream), timeout=1.0))
            await stream.aclose()
            return frames

        frames = asyncio.run(scenario())
        assert "ready" in frames[0]
        assert "state_update" in frames[1]


class CliParserTests(unittest.TestCase):
    def test_parser_defaults_match_the_documented_flags(self) -> None:
        args = server.build_parser().parse_args([])

        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.no_browser is False
        assert args.export_static is None

    def test_parser_accepts_the_smoke_test_invocation(self) -> None:
        args = server.build_parser().parse_args(["--port", "9876", "--no-browser", "--root", "."])

        assert args.port == 9876
        assert args.no_browser is True

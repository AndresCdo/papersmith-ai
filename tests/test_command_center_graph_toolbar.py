"""The dashboard's graph toolbar and its links to the PDF and artifacts.

The page is a hand-written static file, so these pin its wiring: the two
graph buttons, the atlas message contract, and the panels that must survive
(the concept map and the smith phase flow)."""

from __future__ import annotations

import unittest
from pathlib import Path

from skills._core.command_center import server

PAGE = (Path(server.__file__).resolve().parent / "static" / "index.html").read_text(encoding="utf-8")


class GraphToolbarTests(unittest.TestCase):
    def test_regenerate_and_group_layout_buttons_sit_in_the_graph_toolbar(self) -> None:
        self.assertIn('id="btnBuildGraph" class="btn" onclick="triggerBuildAtlas()"', PAGE)
        self.assertIn('⚡ Regenerar grafo', PAGE)
        self.assertIn('id="btnGroupLayout" class="btn" onclick="toggleAtlasGroupLayout()"', PAGE)
        self.assertIn('🧩 Disposición de grupos', PAGE)

    def test_regenerate_posts_to_the_build_route_and_reloads_the_frame(self) -> None:
        self.assertIn("fetch('/api/atlas/build', { method: 'POST' })", PAGE)
        self.assertIn("iframe.src = `/api/atlas/view?v=${Date.now()}`", PAGE)

    def test_the_atlas_contract_is_spoken_and_heard(self) -> None:
        self.assertIn("postToGraph({ type: 'atlas-command', command: 'toggle-layout' })", PAGE)
        self.assertIn("e.source !== iframe.contentWindow", PAGE)
        self.assertIn("data.type === 'atlas-layout'", PAGE)
        self.assertIn("data.type === 'atlas-planet-selected'", PAGE)

    def test_a_selected_node_links_to_the_pdf_and_its_artifact(self) -> None:
        self.assertIn('onclick="atlasSelectionToPdf()"', PAGE)
        self.assertIn("findTextInPdf([atlasSelection.label, atlasSelection.systemTitle])", PAGE)
        self.assertIn("jumpToArtifact('sota-pool/atlas.json')", PAGE)


class PreservedPanelsTests(unittest.TestCase):
    def test_the_concept_map_panel_is_still_there(self) -> None:
        self.assertIn('id="pane-modelo"', PAGE)
        self.assertIn("Mapa Conceptual", PAGE)

    def test_the_graph_switches_and_smith_phase_run_are_unchanged(self) -> None:
        for kind in ("atlas", "novelty", "papers"):
            self.assertIn(f"onclick=\"switchGraph('{kind}')\"", PAGE)
        self.assertIn("fetch('/api/phase/run', {", PAGE)
        self.assertIn("onclick=\"triggerRunPhase('${escapeHtml(p.id)}', this)\"", PAGE)

    def test_the_tab_order_is_unchanged(self) -> None:
        order = ["pane-pipeline", "pane-flow", "pane-modelo", "pane-sections", "pane-gates",
                 "pane-telemetria", "pane-atlas", "pane-preview", "pane-artifacts"]
        positions = [PAGE.index(f'id="{pane}"') for pane in order]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()

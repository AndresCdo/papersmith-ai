"""A fresh workspace's dashboard shows its own data or neutral defaults, never
an older project's: the model spec, the novelty graph and its viewer."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import model_spec, novelty_graph

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class NeutralDefaultsTests(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name).resolve() / "moneeg-like-name"
        self.root.mkdir()
        (self.root / "papersmith.yaml").write_text("title: Fresh Paper\n", encoding="utf-8")

    def test_no_root_and_a_suggestive_name_both_get_the_neutral_spec(self) -> None:
        for spec in (model_spec.get_model_specification(None),
                     model_spec.get_model_specification(self.root)):
            text = json.dumps(spec, ensure_ascii=False)
            self.assertNotIn("ADS1299", text)
            self.assertEqual(spec["mathematical_model"]["equations"], [])
        self.assertEqual(model_spec.get_model_specification(self.root)["title"], "Fresh Paper")

    def test_the_novelty_graph_is_neutral_unless_the_workspace_provides_one(self) -> None:
        graph = novelty_graph.build_novelty_graph(self.root)
        self.assertEqual(graph["project"], "moneeg-like-name")
        self.assertNotIn("ADS1299", json.dumps(graph, ensure_ascii=False))
        (self.root / ".papersmith").mkdir()
        shutil.copy(FIXTURES / "moneeg" / "novelty_graph.json", self.root / ".papersmith" / "novelty_graph.json")
        own = novelty_graph.build_novelty_graph(self.root)
        self.assertGreater(len(own["nodes"]), 10)

    def test_the_viewer_names_the_project_and_escapes_its_title(self) -> None:
        (self.root / ".papersmith").mkdir()
        (self.root / ".papersmith" / "novelty_graph.json").write_text(json.dumps({
            "title": "<script>x</script>", "project": "Fresh", "nodes": [], "links": []}), encoding="utf-8")
        page = novelty_graph.build_novelty_viewer_html(self.root)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", page)
        self.assertIn("{ id: 'core', label: \"Fresh\"", page)


if __name__ == "__main__":
    unittest.main()

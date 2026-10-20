"""The phase drawer's console: guided prompts that send the stage's slash
command to an agent, real shell commands, and redirects to the owning panel."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import phase_actions, server

STATIC = Path(server.__file__).resolve().parent / "static"
PAGE = (STATIC / "index.html").read_text(encoding="utf-8")

# A minimal DOM: the drawer's inputs and hints, a click dispatcher, and spies
# for sendToCli / navigateTab / filterModelView / closeDrawer.
HARNESS = r"""
const fs = require('fs');
const calls = [];
const els = {};
const listeners = {};
function el(id) { return els[id] || (els[id] = { id, value: '', textContent: '', classList: { add(){}, remove(){} }, focus(){} }); }
global.window = {
  sendToCli: (t, r, o) => calls.push(['send', t, r, o && o.kind]),
  navigateTab: (t) => calls.push(['tab', t]),
  filterModelView: (s) => calls.push(['section', s]),
  closeDrawer: () => calls.push(['close']),
};
global.document = {
  getElementById: el,
  querySelectorAll: () => [],
  addEventListener: (type, fn) => { listeners[type] = fn; },
};
eval(fs.readFileSync(process.argv[1], 'utf8'));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = window.renderPhaseActions(input.phase);
function click(i) {
  listeners.click({ target: { closest: () => ({ dataset: { phaseAction: String(i) } }) } });
}
for (const step of input.steps) {
  if (step.type) el('phaseInput' + step.i).value = step.type;
  click(step.i);
}
console.log(JSON.stringify({ html, calls, hints: Object.fromEntries(Object.entries(els).map(([k, v]) => [k, v.textContent])) }));
"""


def run(phase: dict, steps: list[dict]) -> dict:
    out = subprocess.run(["node", "-e", HARNESS, str(STATIC / "phase-console.js")],
                         input=json.dumps({"phase": phase, "steps": steps}),
                         capture_output=True, text=True, cwd=tempfile.gettempdir(), check=True)
    return json.loads(out.stdout)


def phase(stage: str) -> dict:
    return {"stage_id": stage, "actions": phase_actions.ACTIONS[stage]["actions"]}


class PhaseConsoleTests(unittest.TestCase):
    def test_plausibility_shows_its_rules_and_refuses_a_one_sentence_idea(self) -> None:
        result = run(phase("plausibility"), [{"i": 0, "type": "Una sola idea."}])
        self.assertIn("dos oraciones", result["html"])
        self.assertIn('id="phaseInput0"', result["html"])
        self.assertEqual(result["calls"], [])
        self.assertIn("al menos 2 oraciones", result["hints"]["phaseHint0"])

    def test_plausibility_sends_the_idea_as_one_slash_command_line(self) -> None:
        idea = "EEG models fail across subjects.\nI propose a quantum kernel."
        result = run(phase("plausibility"), [{"i": 0, "type": idea}])
        self.assertEqual(result["calls"], [[
            "send", "/plausibility EEG models fail across subjects. I propose a quantum kernel.", True, "slash"]])

    def test_a_prefixed_prompt_and_an_optional_one(self) -> None:
        result = run(phase("declarations"), [{"i": 0, "type": "idioma: inglés"}])
        self.assertEqual(result["calls"][0][1], "/paper-writing mark idioma: inglés")
        result = run(phase("harness"), [{"i": 2}])
        self.assertEqual(result["calls"], [["send", "/upgrade-project", True, "slash"]])

    def test_a_required_prompt_left_empty_sends_nothing(self) -> None:
        result = run(phase("writing"), [{"i": 0}])
        self.assertEqual(result["calls"], [])
        self.assertIn("Escribe lo que pide la guía", result["hints"]["phaseHint0"])

    def test_commands_run_in_the_shell_and_placeholders_are_only_typed(self) -> None:
        result = run(phase("harness"), [{"i": 0}])
        self.assertEqual(result["calls"], [["send", "papersmith status .", True, "shell"]])
        result = run(phase("ingestion"), [{"i": 1}])
        self.assertEqual(result["calls"], [["send", "papersmith ingest <ruta-o-url> .", False, "shell"]])

    def test_the_concept_map_redirect_opens_its_section(self) -> None:
        result = run(phase("proposal"), [{"i": 1}])
        self.assertEqual(result["calls"], [["close"], ["tab", "modelo"], ["section", "mapa"]])

    def test_phase_text_is_escaped(self) -> None:
        hostile = {"actions": [{"kind": "redirect", "label": "<img src=x onerror=alert(1)>",
                                "tab": "atlas", "section": "", "desc": "\"><script>"}]}
        html = run(hostile, [])["html"]
        self.assertNotIn("<img", html)
        self.assertNotIn("<script>", html)

    def test_a_phase_without_actions_renders_nothing(self) -> None:
        self.assertEqual(run({"actions": []}, [])["html"], "")


class PageWiringTests(unittest.TestCase):
    def test_the_drawer_renders_the_phase_actions(self) -> None:
        self.assertIn('<script src="./phase-console.js?v=', PAGE)
        self.assertIn("window.renderPhaseActions ? window.renderPhaseActions(p) : ''", PAGE)
        self.assertNotIn("papersmith run --stage", PAGE)

    def test_slash_commands_switch_the_terminal_to_an_agent(self) -> None:
        script = (STATIC / "cli-console.js").read_text(encoding="utf-8")
        self.assertIn("const SLASH_AGENTS = ['claude', 'opencode', 'pi'];", script)
        self.assertIn("async function sendToCli(text, run, options)", script)
        # A startup question (folder trust) is never answered by the command's Enter.
        self.assertIn("const STARTUP_QUESTIONS = /trust this folder|Do you trust|Enter to confirm/i;", script)
        self.assertIn("if (kind === 'slash' && STARTUP_QUESTIONS.test(screenText()))", script)


if __name__ == "__main__":
    unittest.main()

"""The CLI session a phase runs in outlives the window around it: closing the
console hides it, a reload reattaches it while a phase run is live, replayed
output is drawn once, and the run can be interrupted without ending the
session. Runs the real cli-console.js in node with a stub DOM, xterm, fetch
and EventSource."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from skills._core.command_center import server

SCRIPT = Path(server.__file__).resolve().parent / "static" / "cli-console.js"

HARNESS = r"""
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync(0, 'utf8'));
const log = [];
const els = {};
function el(id) {
  if (!els[id]) {
    const cls = new Set();
    els[id] = { id, value: '', textContent: '', dataset: {}, disabled: false, innerHTML: '',
      classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c),
                   toggle: (c, on) => (on === undefined ? (cls.has(c) ? cls.delete(c) : cls.add(c)) : on ? cls.add(c) : cls.delete(c)) },
      setAttribute() {}, addEventListener() {}, appendChild() {}, focus() {} };
  }
  return els[id];
}
const store = { smith_terminal_agent: 'claude' };
if (cfg.stored) store['smith_terminal_session@local'] = JSON.stringify(cfg.stored);
global.localStorage = { getItem: (k) => store[k] ?? null, setItem: (k, v) => { store[k] = v; },
                        removeItem: (k) => { delete store[k]; } };
const docListeners = {};
const winListeners = {};
global.document = { getElementById: el, createElement: () => el('x' + Math.random()),
  addEventListener: (t, fn) => { docListeners[t] = fn; } };
global.ResizeObserver = class { observe() {} };
let sessions = 0;
global.fetch = async (path, opts = {}) => {
  const method = opts.method || 'GET';
  const body = opts.body ? JSON.parse(opts.body) : undefined;
  let data = {};
  let ok = true;
  if (path === '/api/terminal/agents') {
    data = { enabled: true, authorized: true, default: 'claude', quick: {},
             agents: ['claude', 'shell'].map((id) => ({ id, label: id, available: true })) };
  } else if (path === '/api/terminal/sessions' && method === 'POST') {
    sessions += 1; data = { id: 's' + sessions }; log.push(['open', body.agent]);
  } else if (/^\/api\/terminal\/sessions\/[^/]+$/.test(path) && method === 'GET') {
    log.push(['lookup', path.split('/')[4]]);
    if (cfg.lookupDown) throw new Error('network down');
    if (cfg.lookup) data = cfg.lookup; else { ok = false; data = { detail: 'no such session' }; }
  } else if (path.endsWith('/input')) {
    if ('data' in body) log.push(['input', path.split('/')[4], body.data]);
  } else if (method === 'DELETE') {
    log.push(['close', path.split('/')[4]]);
  }
  return { ok, status: ok ? 200 : 404, json: async () => data };
};
global.EventSource = class {
  constructor(url) {
    this.l = {};
    this.sid = url.split('/')[4];
    log.push(['stream', this.sid]);
    setTimeout(() => {
      if (this.closed) return;
      this.onopen && this.onopen();
      this.l.output && this.l.output({ data: JSON.stringify({ payload: { data: '' } }) });
      // A dropped connection: the browser reconnects and the server replays.
      setTimeout(() => { if (this.closed) return; this.onerror && this.onerror(); this.onopen && this.onopen(); }, 20);
    }, 10);
  }
  addEventListener(t, fn) { this.l[t] = fn; }
  close() { this.closed = true; log.push(['streamClose', this.sid]); }
};
global.window = {
  confirm: () => true,
  addEventListener: (t, fn) => { winListeners[t] = fn; },
  phaseRuns: { anyRunning: () => Boolean(cfg.running) },
  Terminal: class {
    constructor() { this.cols = 80; this.rows = 3; this.buffer = { active: { viewportY: 0, getLine: () => ({ translateToString: () => '' }) } }; }
    loadAddon() {} open() {} onData() {} onResize() {} write() {} focus() {} clear() {}
    reset() { log.push(['reset']); }
  },
};
eval(fs.readFileSync(process.argv[1], 'utf8'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  docListeners.DOMContentLoaded();
  await wait(150);
  const out = { afterLoad: window.smithTerminalActivity() };
  if (cfg.send) {
    await window.sendToCli('/plausibility idea', true, { kind: 'slash', agent: 'claude' });
    await wait(300);
    window.closeCliConsole();
    out.afterSend = window.smithTerminalActivity();
    out.logAfterClose = log.slice();
    if (cfg.reopen) {
      window.openCliConsole();
      await wait(300);
      out.logAfterReopen = log.slice();
    }
  }
  out.interrupt = await window.smithTerminalInterrupt();
  winListeners.beforeunload();
  await wait(50);
  out.stored = store['smith_terminal_session@local'] ? JSON.parse(store['smith_terminal_session@local']) : null;
  out.log = log;
  console.log(JSON.stringify(out));
})();
"""


def run(**cfg) -> dict:
    done = subprocess.run(["node", "-e", HARNESS, str(SCRIPT)], input=json.dumps(cfg),
                          capture_output=True, text=True, cwd=tempfile.gettempdir(),
                          timeout=60, check=True)
    return json.loads(done.stdout)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class CliSessionTests(unittest.TestCase):
    def test_a_reload_reattaches_the_live_session_of_a_running_phase(self) -> None:
        out = run(stored={"id": "s9", "agent": "claude"},
                  lookup={"id": "s9", "agent": "claude", "alive": True}, send=True, running=True)
        self.assertEqual(out["afterLoad"]["sessionId"], "s9")
        self.assertIn(["stream", "s9"], out["log"])
        # The phase command goes to the reattached session; nothing new opens.
        self.assertNotIn("open", [entry[0] for entry in out["log"]])
        self.assertIn(["input", "s9", "/plausibility idea"], out["log"])

    def test_a_session_that_is_gone_is_forgotten_and_a_new_one_opens(self) -> None:
        out = run(stored={"id": "s9", "agent": "claude"}, lookup=None, send=True, running=True)
        self.assertIsNone(out["afterLoad"]["sessionId"])
        self.assertIn(["open", "claude"], out["log"])
        self.assertIn(["input", "s1", "/plausibility idea"], out["log"])
        self.assertEqual(out["stored"], {"id": "s1", "agent": "claude"})

    def test_a_transient_lookup_failure_keeps_the_remembered_session(self) -> None:
        out = run(stored={"id": "s9", "agent": "claude"}, lookupDown=True, running=True)
        self.assertIsNone(out["afterLoad"]["sessionId"])
        self.assertEqual(out["stored"], {"id": "s9", "agent": "claude"})

    def test_closing_the_console_keeps_the_session(self) -> None:
        out = run(send=True, running=True)
        self.assertEqual(out["afterSend"]["sessionId"], "s1")
        self.assertNotIn("close", [entry[0] for entry in out["log"]])

    def test_a_reload_keeps_the_session_only_while_a_phase_runs(self) -> None:
        kept = run(send=True, running=True)
        self.assertNotIn("close", [entry[0] for entry in kept["log"]])
        self.assertEqual(kept["stored"], {"id": "s1", "agent": "claude"})
        closed = run(send=True, running=False)
        self.assertIn(["close", "s1"], closed["log"])
        self.assertIsNone(closed["stored"])

    def test_replayed_output_is_drawn_once(self) -> None:
        # A reconnect replays the session from its start: the screen is
        # cleared first, so the replay is drawn once.
        out = run(send=True, running=True)
        self.assertEqual([entry[0] for entry in out["log"]].count("reset"), 1)

    def test_stop_interrupts_the_agent_turn_and_keeps_the_session(self) -> None:
        out = run(send=True, running=True)
        self.assertTrue(out["interrupt"])
        self.assertIn(["input", "s1", "\u001b"], out["log"])
        self.assertNotIn("close", [entry[0] for entry in out["log"]])

    def test_closing_the_console_without_a_run_closes_only_its_stream(self) -> None:
        out = run(send=True, running=False, reopen=True)
        closed = out["logAfterClose"]
        self.assertIn(["streamClose", "s1"], closed)
        self.assertNotIn("close", [entry[0] for entry in closed])
        self.assertEqual(out["afterSend"]["sessionId"], "s1")
        # Opening the console again reattaches the same session.
        reopened = out["logAfterReopen"][len(closed):]
        self.assertIn(["stream", "s1"], reopened)
        self.assertNotIn("open", [entry[0] for entry in reopened])

    def test_closing_the_console_during_a_run_keeps_following_the_agent(self) -> None:
        out = run(send=True, running=True)
        self.assertNotIn(["streamClose", "s1"], out["logAfterClose"])

    def test_without_a_session_there_is_nothing_to_interrupt(self) -> None:
        out = run(running=False)
        self.assertFalse(out["interrupt"])


if __name__ == "__main__":
    unittest.main()

/* Smith CLI assistant ("CLI de apoyo") for the Paper Command Center.
 *
 * A floating xterm.js window, opened from the bottom-right FAB, bound to one
 * PTY session on the backend (skills/_core/command_center/terminal.py): herdr
 * (default), claude, opencode, pi or a login shell, started in the project
 * root. Output arrives over SSE; keys, resizes and closes go out as
 * same-origin JSON requests carrying the X-Papersmith-Terminal header, and the
 * server also requires the per-server cookie set by its printed login URL.
 *
 * Public surface (window): toggleSmithTerminal(), openCliConsole(),
 * closeCliConsole(), sendToCli(text, run).
 */
(function () {
  'use strict';

  const HEADERS = { 'Content-Type': 'application/json', 'X-Papersmith-Terminal': '1' };
  const AGENT_KEY = 'smith_terminal_agent';
  const INPUT_FLUSH_MS = 6;

  const state = {
    info: null,        // GET /api/terminal/agents
    tools: null,       // GET /api/terminal/tools
    term: null,
    fit: null,
    sessionId: null,
    source: null,
    agent: null,
    starting: null,
    exited: false,
    pendingInput: '',
    flushTimer: null,
    lastOutputAt: 0,
  };

  const $ = (id) => document.getElementById(id);

  function readAgent() {
    try { return localStorage.getItem(AGENT_KEY); } catch (_) { return null; }
  }
  function saveAgent(agent) {
    try { localStorage.setItem(AGENT_KEY, agent); } catch (_) { /* storage blocked */ }
  }

  async function api(path, method, body) {
    const res = await fetch(path, {
      method, headers: HEADERS, body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);
    return data;
  }

  // ---- status: header dot, FAB badge and footer agent ---------------------
  function setStatus(text, tone) {
    const label = $('terminalStatusText');
    if (label) label.textContent = text;
    const dot = $('terminalStatusDot');
    if (dot) {
      dot.classList.toggle('is-connected', tone === 'ok');
      dot.classList.toggle('is-connecting', tone === 'warn');
      dot.title = text;
    }
    const badge = $('smithFabBadge');
    if (badge) badge.dataset.tone = tone || 'off';
  }

  function agentLabel(id) {
    const agent = ((state.info && state.info.agents) || []).find((a) => a.id === id);
    return agent ? agent.label : id;
  }

  function renderFooter() {
    const agentEl = $('terminalFooterAgent');
    if (agentEl) agentEl.textContent = agentLabel(state.agent);
    const runEl = $('terminalFooterRun');
    if (runEl && state.tools) runEl.textContent = state.tools.monitored_path || '';
  }

  // ---- agents, tools and quick commands ------------------------------------
  async function loadInfo() {
    if (state.info) return state.info;
    const res = await fetch('/api/terminal/agents');
    state.info = res.ok ? await res.json() : { enabled: false, agents: [], quick: {} };
    const available = (state.info.agents || []).filter((a) => a.available).map((a) => a.id);
    const saved = readAgent();
    state.agent = available.includes(saved) ? saved : (state.info.default || available[0] || 'shell');
    const select = $('terminalAgentSelect');
    if (select) {
      select.innerHTML = '';
      for (const agent of state.info.agents || []) {
        const opt = document.createElement('option');
        opt.value = agent.id;
        opt.textContent = agent.available ? agent.label : `${agent.label} (no instalado)`;
        opt.disabled = !agent.available;
        opt.title = agent.desc || '';
        select.appendChild(opt);
      }
      select.value = state.agent;
    }
    renderQuick();
    if (!state.info.enabled) {
      setStatus('Terminal deshabilitada (solo se ofrece en 127.0.0.1)', 'bad');
    } else if (!state.info.authorized) {
      setStatus('Abre el tablero desde el enlace de acceso que imprime smith ui', 'bad');
    } else {
      loadTools();
    }
    renderFooter();
    return state.info;
  }

  async function loadTools() {
    try {
      const data = await api('/api/terminal/tools', 'GET');
      state.tools = data.tools;
    } catch (_) {
      state.tools = null;
    }
    const btn = $('btnLaunchExternalTerm');
    if (btn && state.tools) {
      const name = state.tools.preferred_terminal === 'wezterm' ? 'WezTerm' : 'Ghostty';
      btn.textContent = `🖥️ ${name}`;
      btn.disabled = !state.tools.ready;
      btn.title = state.tools.ready
        ? `Abrir herdr en ${name} sobre este proyecto`
        : `Falta: ${(state.tools.missing || []).join(', ')} (brew install --cask ghostty · brew install herdr)`;
    }
    renderFooter();
  }

  function renderQuick() {
    const select = $('terminalQuickSelect');
    if (!select || !state.info) return;
    const quick = state.info.quick || {};
    const items = state.agent === 'shell' ? (quick.shell || []) : (quick.agent || []);
    select.innerHTML = '<option value="">Comandos smith…</option>';
    for (const cmd of items) {
      const opt = document.createElement('option');
      opt.value = cmd;
      opt.textContent = cmd;
      select.appendChild(opt);
    }
    select.disabled = items.length === 0;
  }

  // ---- xterm ---------------------------------------------------------------
  function flushInput() {
    state.flushTimer = null;
    const data = state.pendingInput;
    state.pendingInput = '';
    if (data && state.sessionId) {
      api(`/api/terminal/sessions/${state.sessionId}/input`, 'POST', { data }).catch(() => {});
    }
  }

  // Keystrokes are coalesced for a few milliseconds: one request per burst
  // (a paste, a held key) instead of one per character.
  function queueInput(data) {
    if (!state.sessionId) {
      if (!state.exited) start().catch(() => {});
      return;
    }
    state.pendingInput += data;
    if (!state.flushTimer) state.flushTimer = setTimeout(flushInput, INPUT_FLUSH_MS);
  }

  function sendResize(redraw) {
    if (!state.sessionId || !state.term) return;
    api(`/api/terminal/sessions/${state.sessionId}/input`, 'POST', {
      cols: state.term.cols, rows: state.term.rows, redraw: Boolean(redraw),
    }).catch(() => {});
  }

  function refit(redraw) {
    try { state.fit && state.fit.fit(); } catch (_) { /* hidden container */ }
    if (redraw) sendResize(true);
  }

  function ensureTerm() {
    if (state.term) return state.term;
    if (!window.Terminal) {
      setStatus('xterm.js no está disponible', 'bad');
      return null;
    }
    const term = new window.Terminal({
      cursorBlink: true, fontSize: 13, lineHeight: 1.25, scrollback: 5000,
      // Nerd Fonts first, when installed, so herdr/opencode icons render.
      fontFamily: '"IosevkaTerm Nerd Font", "JetBrainsMono Nerd Font", "MesloLGS NF", '
        + '"Symbols Nerd Font Mono", ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
      theme: {
        background: '#080c14', foreground: '#f1f5f9', cursor: '#38bdf8',
        selectionBackground: 'rgba(56, 189, 248, 0.35)',
        black: '#1e293b', red: '#f87171', green: '#4ade80', yellow: '#facc15',
        blue: '#60a5fa', magenta: '#c084fc', cyan: '#22d3ee', white: '#e2e8f0',
        brightBlack: '#475569', brightRed: '#fca5a5', brightGreen: '#86efac',
        brightYellow: '#fde047', brightBlue: '#93c5fd', brightMagenta: '#d8b4fe',
        brightCyan: '#67e8f9', brightWhite: '#f8fafc',
      },
    });
    const fit = window.FitAddon ? new window.FitAddon.FitAddon() : null;
    if (fit) term.loadAddon(fit);
    const container = $('terminalContainer');
    term.open(container);
    container.addEventListener('mousedown', () => term.focus());
    term.onData(queueInput);
    term.onResize(() => sendResize(false));
    state.term = term;
    state.fit = fit;
    new ResizeObserver(() => refit(false)).observe(container);
    return term;
  }

  function decode(b64) {
    const raw = atob(b64);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    return bytes;
  }

  function attach(sessionId) {
    if (state.source) state.source.close();
    const source = new EventSource(`/api/terminal/sessions/${sessionId}/stream`);
    source.addEventListener('output', (event) => {
      state.lastOutputAt = Date.now();
      state.term.write(decode(JSON.parse(event.data).payload.data));
    });
    source.addEventListener('exit', () => {
      source.close();
      // Release the ended session so it stops counting toward the cap.
      api(`/api/terminal/sessions/${sessionId}`, 'DELETE', {}).catch(() => {});
      if (state.sessionId === sessionId) {
        state.sessionId = null;
        state.exited = true;
        state.term.write('\r\n\x1b[90m[Smith] Sesión finalizada — pulsa ⟳ para abrir otra\x1b[0m\r\n');
        setStatus('Sesión finalizada', 'off');
      }
    });
    source.onerror = () => { if (state.sessionId === sessionId) setStatus('Reconectando…', 'warn'); };
    source.onopen = () => setStatus(`Conectado · ${agentLabel(state.agent)}`, 'ok');
    state.source = source;
  }

  async function start() {
    if (state.sessionId) return state.sessionId;
    if (state.starting) return state.starting;
    state.starting = (async () => {
      const info = await loadInfo();
      if (!info.enabled) throw new Error('terminal deshabilitada');
      if (!info.authorized) throw new Error('sin acceso: usa el enlace de acceso de smith ui');
      const term = ensureTerm();
      if (!term) throw new Error('xterm.js no disponible');
      refit(false);
      setStatus(`Abriendo ${agentLabel(state.agent)}…`, 'warn');
      const created = await api('/api/terminal/sessions', 'POST', {
        agent: state.agent, cols: term.cols, rows: term.rows,
      });
      state.sessionId = created.id;
      state.exited = false;
      attach(created.id);
      term.focus();
      return created.id;
    })();
    try {
      return await state.starting;
    } catch (err) {
      setStatus(`No se pudo abrir: ${err.message}`, 'bad');
      throw err;
    } finally {
      state.starting = null;
    }
  }

  async function stop() {
    const sid = state.sessionId;
    state.sessionId = null;
    if (state.source) { state.source.close(); state.source = null; }
    if (sid) {
      try { await api(`/api/terminal/sessions/${sid}`, 'DELETE', {}); } catch (_) { /* gone */ }
    }
    setStatus('Sin sesión', 'off');
  }

  async function restart() {
    await stop();
    if (state.term) state.term.reset();
    state.exited = false;
    start().catch(() => {});
  }

  // ---- window --------------------------------------------------------------
  function isOpen() {
    const win = $('smithTerminalWindow');
    return Boolean(win && win.classList.contains('is-open'));
  }

  function openCliConsole() {
    const win = $('smithTerminalWindow');
    if (!win) return;
    win.classList.add('is-open');
    win.setAttribute('aria-hidden', 'false');
    $('smithAssistantFab')?.classList.add('is-active');
    loadInfo().then((info) => {
      if (!ensureTerm()) return;
      setTimeout(() => {
        refit(true);
        if (info.enabled && info.authorized && !state.sessionId && !state.exited) start().catch(() => {});
        state.term.focus();
      }, 100);
    });
  }

  // Hides the window only: the session keeps running behind the FAB.
  function closeCliConsole() {
    const win = $('smithTerminalWindow');
    if (!win) return;
    win.classList.remove('is-open');
    win.setAttribute('aria-hidden', 'true');
    $('smithAssistantFab')?.classList.remove('is-active');
  }

  function toggleSmithTerminal() {
    if (isOpen()) closeCliConsole(); else openCliConsole();
  }

  function toggleMaximize() {
    const win = $('smithTerminalWindow');
    if (!win) return;
    const maximized = win.classList.toggle('is-maximized');
    const btn = $('btnTerminalMaximize');
    if (btn) btn.textContent = maximized ? '🗗' : '⛶';
    setTimeout(() => refit(true), 150);
  }

  async function launchExternal() {
    try {
      const result = await api('/api/terminal/launch-external', 'POST', {});
      setStatus(`herdr abierto en ${result.terminal}`, 'ok');
    } catch (err) {
      setStatus(`No se pudo abrir la terminal externa: ${err.message}`, 'bad');
    }
  }

  // Agents that understand a harness slash command; herdr and the plain shell
  // do not, so a slash command switches the console to the first of these.
  const SLASH_AGENTS = ['claude', 'opencode', 'pi'];

  async function useAgent(kind) {
    const info = await loadInfo();
    const available = (info.agents || []).filter((a) => a.available).map((a) => a.id);
    let wanted = state.agent;
    if (kind === 'shell') wanted = 'shell';
    if (kind === 'slash' && !SLASH_AGENTS.includes(state.agent)) {
      wanted = SLASH_AGENTS.find((id) => available.includes(id)) || null;
      if (!wanted) throw new Error('no hay un agente (claude, opencode, pi) instalado');
    }
    if (wanted === state.agent) return false;
    state.agent = wanted;
    const select = $('terminalAgentSelect');
    if (select) select.value = wanted;
    renderQuick();
    renderFooter();
    await stop();
    if (state.term) state.term.reset();
    return true;
  }

  // A freshly started agent paints its prompt before it reads input: wait for
  // its first output and then a short quiet spell (bounded), so the text is
  // typed into the agent rather than lost while it boots.
  async function settle(maxMs) {
    const began = Date.now();
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    while (Date.now() - began < maxMs) {
      await sleep(250);
      if (state.lastOutputAt > began && Date.now() - state.lastOutputAt > 900) return;
    }
  }

  // Types `text` into the session (opening one if needed). run=true also sends
  // Enter, as a separate write so an agent does not read it as a paste.
  // options.kind: 'slash' runs it in an agent, 'shell' in the plain shell.
  async function sendToCli(text, run, options) {
    openCliConsole();
    try {
      const kind = options && options.kind;
      const switched = kind ? await useAgent(kind) : false;
      const fresh = switched || !state.sessionId;
      const sid = await start();
      if (fresh && state.agent !== 'shell') await settle(12000);
      await api(`/api/terminal/sessions/${sid}/input`, 'POST', { data: text });
      if (run) {
        setTimeout(() => {
          api(`/api/terminal/sessions/${sid}/input`, 'POST', { data: '\r' }).catch(() => {});
        }, 200);
      }
      state.term.focus();
    } catch (err) {
      setStatus(`No se pudo enviar: ${err.message}`, 'bad');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('smithAssistantFab')?.addEventListener('click', toggleSmithTerminal);
    $('btnTerminalClose')?.addEventListener('click', closeCliConsole);
    $('btnTerminalMaximize')?.addEventListener('click', toggleMaximize);
    $('btnTerminalRestart')?.addEventListener('click', restart);
    $('btnLaunchExternalTerm')?.addEventListener('click', launchExternal);
    $('btnTerminalClear')?.addEventListener('click', () => state.term && state.term.clear());
    const agentSelect = $('terminalAgentSelect');
    agentSelect?.addEventListener('change', () => {
      state.agent = agentSelect.value;
      saveAgent(state.agent);
      renderQuick();
      renderFooter();
      restart();
    });
    const quick = $('terminalQuickSelect');
    quick?.addEventListener('change', () => {
      if (quick.value) sendToCli(quick.value, true);
      quick.value = '';
    });
    // Back on the tab or window: refit and ask the program to repaint.
    const wake = () => { if (isOpen() && state.sessionId) refit(true); };
    document.addEventListener('visibilitychange', () => { if (!document.hidden) wake(); });
    window.addEventListener('focus', wake);
    window.addEventListener('resize', () => { if (isOpen()) refit(false); });
    window.addEventListener('beforeunload', () => {
      if (state.sessionId) {
        fetch(`/api/terminal/sessions/${state.sessionId}`, { method: 'DELETE', headers: HEADERS, body: '{}', keepalive: true });
      }
    });
    setStatus('Sin sesión', 'off');
  });

  window.toggleSmithTerminal = toggleSmithTerminal;
  window.openCliConsole = openCliConsole;
  window.closeCliConsole = closeCliConsole;
  window.sendToCli = sendToCli;
})();

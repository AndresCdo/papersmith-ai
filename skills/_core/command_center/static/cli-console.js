/* Support terminal ("CLI de apoyo") for the Paper Command Center.
 *
 * A floating xterm.js window bound to one PTY session on the backend
 * (skills/_core/command_center/terminal.py): output arrives over SSE, keys,
 * resizes and closes go out as same-origin JSON requests carrying the
 * X-Papersmith-Terminal header the server requires.
 *
 * Public surface (window): openCliConsole(), closeCliConsole(), sendToCli(text, run).
 */
(function () {
  'use strict';

  const HEADERS = { 'Content-Type': 'application/json', 'X-Papersmith-Terminal': '1' };
  const state = {
    info: null,        // GET /api/terminal/agents
    term: null,
    fit: null,
    sessionId: null,
    source: null,
    agent: 'shell',
    starting: null,
  };

  const $ = (id) => document.getElementById(id);

  async function api(path, method, body) {
    const res = await fetch(path, {
      method, headers: HEADERS, body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }

  function setStatus(text, tone) {
    const el = $('cliStatus');
    if (!el) return;
    el.textContent = text;
    el.dataset.tone = tone || 'muted';
  }

  async function loadInfo() {
    if (state.info) return state.info;
    const res = await fetch('/api/terminal/agents');
    state.info = res.ok ? await res.json() : { enabled: false, agents: [], quick: {} };
    const select = $('cliAgent');
    if (select) {
      select.innerHTML = '';
      for (const agent of state.info.agents || []) {
        const opt = document.createElement('option');
        opt.value = agent.id;
        opt.textContent = agent.available ? agent.label : `${agent.label} (no instalado)`;
        opt.disabled = !agent.available;
        select.appendChild(opt);
      }
      select.value = state.agent;
    }
    renderQuick();
    if (!state.info.enabled) {
      setStatus('Terminal deshabilitada (solo se ofrece en 127.0.0.1)', 'bad');
    }
    return state.info;
  }

  function renderQuick() {
    const bar = $('cliQuick');
    if (!bar || !state.info) return;
    const quick = state.info.quick || {};
    const items = state.agent === 'shell' ? (quick.shell || []) : (quick.agent || []);
    bar.innerHTML = '';
    for (const cmd of items) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'cli-quick__btn';
      b.textContent = cmd;
      b.title = 'Escribir en la terminal (Enter para ejecutar)';
      b.addEventListener('click', () => sendToCli(cmd, false));
      bar.appendChild(b);
    }
  }

  function ensureTerm() {
    if (state.term) return state.term;
    if (!window.Terminal) {
      setStatus('xterm.js no está disponible', 'bad');
      return null;
    }
    const term = new window.Terminal({
      cursorBlink: true, convertEol: false, fontSize: 13, scrollback: 5000,
      fontFamily: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace',
      theme: { background: '#0b0f19', foreground: '#e5e7eb', cursor: '#38bdf8' },
    });
    const fit = window.FitAddon ? new window.FitAddon.FitAddon() : null;
    if (fit) term.loadAddon(fit);
    term.open($('cliTerm'));
    term.onData((data) => {
      if (state.sessionId) api(`/api/terminal/sessions/${state.sessionId}/input`, 'POST', { data }).catch(() => {});
    });
    term.onResize(({ cols, rows }) => {
      if (state.sessionId) api(`/api/terminal/sessions/${state.sessionId}/input`, 'POST', { cols, rows }).catch(() => {});
    });
    state.term = term;
    state.fit = fit;
    new ResizeObserver(() => { try { fit && fit.fit(); } catch (_) {} }).observe($('cliTerm'));
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
      const frame = JSON.parse(event.data);
      state.term.write(decode(frame.payload.data));
    });
    source.addEventListener('exit', () => {
      source.close();
      if (state.sessionId === sessionId) {
        state.sessionId = null;
        state.term.write('\r\n\x1b[90m[sesión terminada — pulsa Conectar para abrir otra]\x1b[0m\r\n');
        setStatus('Sesión terminada', 'muted');
      }
    });
    source.onerror = () => setStatus('Reconectando…', 'warn');
    source.onopen = () => setStatus(`Conectado · ${state.agent}`, 'ok');
    state.source = source;
  }

  async function start() {
    if (state.sessionId) return state.sessionId;
    if (state.starting) return state.starting;
    state.starting = (async () => {
      const info = await loadInfo();
      if (!info.enabled) throw new Error('terminal deshabilitada');
      const term = ensureTerm();
      if (!term) throw new Error('xterm.js no disponible');
      try { state.fit && state.fit.fit(); } catch (_) {}
      setStatus('Abriendo sesión…', 'warn');
      const created = await api('/api/terminal/sessions', 'POST', {
        agent: state.agent, cols: term.cols, rows: term.rows,
      });
      state.sessionId = created.id;
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
      try { await api(`/api/terminal/sessions/${sid}`, 'DELETE', {}); } catch (_) {}
    }
    setStatus('Sin sesión', 'muted');
  }

  function openCliConsole() {
    const win = $('cliWindow');
    if (!win) return;
    win.classList.add('open');
    win.setAttribute('aria-hidden', 'false');
    loadInfo().then(() => {
      ensureTerm();
      try { state.fit && state.fit.fit(); } catch (_) {}
      if (state.term) state.term.focus();
    });
  }

  function closeCliConsole() {
    const win = $('cliWindow');
    if (!win) return;
    win.classList.remove('open');
    win.setAttribute('aria-hidden', 'true');
  }

  // Types `text` into the session (opening one if needed). With run=false the
  // command waits for the user's Enter: the dashboard never runs a phase alone.
  async function sendToCli(text, run) {
    openCliConsole();
    try {
      const sid = await start();
      await api(`/api/terminal/sessions/${sid}/input`, 'POST', { data: text + (run ? '\r' : '') });
      state.term.focus();
    } catch (_) { /* status line already explains */ }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const select = $('cliAgent');
    if (select) {
      select.addEventListener('change', async () => {
        state.agent = select.value;
        renderQuick();
        if (state.sessionId) { await stop(); await start(); }
      });
    }
    $('cliConnect')?.addEventListener('click', () => { start().catch(() => {}); });
    $('cliStop')?.addEventListener('click', () => { stop(); });
    $('cliClose')?.addEventListener('click', closeCliConsole);
    $('cliFab')?.addEventListener('click', () => {
      const win = $('cliWindow');
      if (win && win.classList.contains('open')) closeCliConsole(); else openCliConsole();
    });
    window.addEventListener('beforeunload', () => {
      if (state.sessionId) {
        fetch(`/api/terminal/sessions/${state.sessionId}`, { method: 'DELETE', headers: HEADERS, body: '{}', keepalive: true });
      }
    });
  });

  window.openCliConsole = openCliConsole;
  window.closeCliConsole = closeCliConsole;
  window.sendToCli = sendToCli;
})();

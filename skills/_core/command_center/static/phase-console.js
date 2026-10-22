/* Phase console: what a pipeline phase card lets the operator do.
 *
 * Each phase in GET /api/status carries `actions` (phase_actions.py):
 *   prompt   — a text box guided by the stage's rules; "Ejecutar" types
 *              `/<skill> <text>` into an agent of the support terminal;
 *   command  — a real `smith` command, run in the terminal's shell;
 *   redirect — opens the dashboard panel that owns the work.
 * Every value is escaped before insertion; handlers read the action back
 * from the rendered phase, never from markup.
 *
 * Public surface (window): renderPhaseActions(phase), phaseSentenceCount(text).
 */
(function () {
  'use strict';

  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);

  let current = [];
  let currentPhase = null;

  // How many sentences the text is worth: sentences end in . ! or ? before a
  // space or the end, and a long run-on idea counts one per WORDS_PER_SENTENCE
  // words, so a full paragraph written with commas is not refused.
  const WORDS_PER_SENTENCE = 12;
  function phaseSentenceCount(text) {
    const clean = String(text || '').trim();
    const parts = clean.split(/(?<=[.!?])\s+/).filter((p) => /\w/.test(p));
    const words = clean.split(/\s+/).filter((w) => /\w/.test(w)).length;
    return Math.max(parts.length, Math.floor(words / WORDS_PER_SENTENCE));
  }

  function promptCard(a, i) {
    const guide = (a.guide || []).map((g) => `<li>${esc(g)}</li>`).join('');
    const need = a.min_sentences ? ` · mínimo ${a.min_sentences} oraciones` : (a.optional ? ' · texto opcional' : '');
    return `<div class="phase-action phase-action--prompt">
        <div class="phase-action__head">
          <strong>${esc(a.label)}</strong>
          <code>${esc(a.slash)}${a.prefix ? ' ' + esc(a.prefix.trim()) : ''}</code>
        </div>
        <ul class="phase-action__guide">${guide}</ul>
        <textarea class="phase-action__input" id="phaseInput${i}" rows="4"
          placeholder="${esc(a.placeholder)}" aria-label="${esc(a.label)}"></textarea>
        <div class="phase-action__error" id="phaseError${i}" role="alert" hidden></div>
        <div class="phase-action__agent">
          <label>Agente <select id="phaseAgent${i}" data-phase-agent="${i}" aria-label="Agente que ejecuta la fase"></select></label>
          <label title="Cierra la sesión abierta y empieza otra"><input type="checkbox" id="phaseFresh${i}" data-phase-agent="${i}"> Nueva sesión</label>
          <span class="phase-action__note" id="phaseAgentNote${i}"></span>
        </div>
        <div class="phase-action__foot">
          <span class="phase-action__hint" id="phaseHint${i}">Se envía al agente de la terminal${esc(need)}</span>
          <button class="btn btn--primary btn--sm" data-phase-action="${i}">▶ Ejecutar</button>
        </div>
      </div>`;
  }

  // ---- agent picker --------------------------------------------------------
  const AGENT_KEY = 'smith_phase_agent';
  let agentInfo = { current: null, live: false, agents: [] };
  const remembered = () => { try { return localStorage.getItem(AGENT_KEY); } catch (_) { return null; } };
  const remember = (id) => { try { localStorage.setItem(AGENT_KEY, id); } catch (_) { /* blocked */ } };
  const label = (id) => (agentInfo.agents.find((a) => a.id === id) || {}).label || id;

  // The default keeps the session that is already following the pipeline;
  // without one, the agent the operator last chose, else the first installed.
  function defaultAgent() {
    const ids = agentInfo.agents.map((a) => a.id);
    if (agentInfo.live && ids.includes(agentInfo.current)) return agentInfo.current;
    const last = remembered();
    if (last && ids.includes(last)) return last;
    return ids[0] || '';
  }

  function agentNote(i) {
    const select = document.getElementById(`phaseAgent${i}`);
    const note = document.getElementById(`phaseAgentNote${i}`);
    if (!select || !note) return;
    const fresh = document.getElementById(`phaseFresh${i}`)?.checked;
    const same = agentInfo.live && select.value === agentInfo.current;
    note.textContent = !select.value ? 'No hay claude, opencode ni pi instalados.'
      : same && !fresh ? `Continúa en la sesión abierta de ${label(select.value)} (no se abre otra).`
        : agentInfo.live ? `Cerrará la sesión de ${label(agentInfo.current)} y abrirá ${fresh && same ? 'una nueva' : label(select.value)}.`
          : `Abrirá una sesión de ${label(select.value)} en la terminal.`;
  }

  // Re-read the terminal's agent and session (they can change from the
  // terminal's own selector) and redraw every note from it.
  async function refreshAgentInfo() {
    if (typeof window.smithTerminalAgents !== 'function') return false;
    try { agentInfo = await window.smithTerminalAgents(); } catch (_) { return false; }
    current.forEach((a, i) => { if (a.kind === 'prompt') agentNote(i); });
    return true;
  }

  async function fillAgents() {
    if (!(await refreshAgentInfo())) return;
    const choice = defaultAgent();
    current.forEach((a, i) => {
      if (a.kind !== 'prompt') return;
      const select = document.getElementById(`phaseAgent${i}`);
      if (!select) return;
      select.innerHTML = agentInfo.agents
        .map((g) => `<option value="${esc(g.id)}"${g.id === choice ? ' selected' : ''}>${esc(g.label)}</option>`).join('');
      select.value = choice;
      agentNote(i);
    });
  }

  function commandCard(a, i) {
    return `<div class="phase-action phase-action--command">
        <div class="phase-action__head"><strong>${esc(a.label)}</strong></div>
        <p class="phase-action__desc">${esc(a.desc)}</p>
        <div class="phase-action__foot">
          <code class="phase-action__cmd">$ ${esc(a.command)}</code>
          <button class="btn btn--sm" data-phase-action="${i}">▶ Ejecutar en shell</button>
        </div>
      </div>`;
  }

  function redirectCard(a, i) {
    return `<button class="phase-action phase-action--redirect" data-phase-action="${i}">
        <strong>↗ ${esc(a.label)}</strong><span>${esc(a.desc)}</span>
      </button>`;
  }

  function renderPhaseActions(phase) {
    current = Array.isArray(phase && phase.actions) ? phase.actions : [];
    currentPhase = phase || null;
    if (!current.length) return '';
    const locked = phase && phase.unlocked === false;
    const lock = locked ? `<div class="phase-lock">
        <strong>🔒 Bloqueada: requiere ${esc(phase.blocked_by)}</strong>
        <span>Se habilita cuando ${esc(phase.blocked_by)} quede verificada. Cada skill se niega si le falta su entrada, así que puedes adelantarla bajo tu responsabilidad.</span>
        <label><input type="checkbox" id="phaseOverride"> Ejecutar sin el requisito</label>
      </div>` : '';
    const cards = current.map((a, i) => (
      a.kind === 'prompt' ? promptCard(a, i) : a.kind === 'command' ? commandCard(a, i) : redirectCard(a, i)
    )).join('');
    setTimeout(fillAgents, 0);
    return `<div class="phase-actions">
        <h4 class="phase-actions__title">⚙️ Ejecutar esta fase</h4>
        ${lock}
        ${cards}
      </div>`;
  }

  // A locked phase runs only with the explicit override.
  // A visible error box under the prompt (the hint line alone was missed).
  function showError(i, msg) {
    const box = document.getElementById(`phaseError${i}`);
    const hint = document.getElementById(`phaseHint${i}`);
    if (hint) { hint.textContent = msg; hint.classList.add('is-error'); }
    if (box) {
      box.textContent = msg;
      box.hidden = false;
      if (box.scrollIntoView) box.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    document.getElementById(`phaseInput${i}`)?.classList.add('is-invalid');
  }
  function clearError(i) {
    const box = document.getElementById(`phaseError${i}`);
    if (box) { box.hidden = true; box.textContent = ''; }
    document.getElementById(`phaseInput${i}`)?.classList.remove('is-invalid');
  }

  function blocked(i) {
    if (!currentPhase || currentPhase.unlocked !== false) return false;
    if (document.getElementById('phaseOverride')?.checked) return false;
    if (i !== null) showError(i, `Bloqueada: primero verifica ${currentPhase.blocked_by}, o marca «Ejecutar sin el requisito».`);
    return true;
  }

  async function send(command, run, kind, i, extra) {
    const sent = await window.sendToCli?.(command, run, { kind, ...(extra || {}) });
    if (sent && run && currentPhase && window.phaseRuns) {
      window.phaseRuns.start(currentPhase, command);
      const host = document.getElementById('phaseRunTracker');
      if (host) {
        host.dataset.stage = currentPhase.stage_id;
        host.innerHTML = window.phaseRuns.renderTracker(currentPhase);
        if (host.scrollIntoView) host.scrollIntoView({ block: 'start', behavior: 'smooth' });
      }
    } else if (sent === false && i !== undefined && i !== null) {
      const why = (window.smithTerminalActivity?.() || {}).refusal || '';
      showError(i, why === 'trust'
        ? 'El agente pregunta si confías en esta carpeta. En la terminal (abajo a la derecha) elige «Yes, I trust this folder» y pulsa Ejecutar de nuevo.'
        : why === 'question'
          ? 'El agente espera una confirmación en la terminal (abajo a la derecha): respóndela y pulsa Ejecutar de nuevo.'
          : `No se pudo enviar a la terminal${why ? `: ${why}` : ''}. Revisa la ventana del CLI (abajo a la derecha).`);
    }
    return sent;
  }

  async function runPrompt(a, i) {
    await refreshAgentInfo();
    const input = document.getElementById(`phaseInput${i}`);
    const hint = document.getElementById(`phaseHint${i}`);
    const text = String(input ? input.value : '').replace(/\s+/g, ' ').trim();
    const fail = (msg) => { showError(i, msg); input?.focus(); };
    clearError(i);
    if (blocked(i)) return;
    if (!text && !a.optional) return fail('Escribe lo que pide la guía antes de ejecutar.');
    if (a.min_sentences && phaseSentenceCount(text) < a.min_sentences) {
      return fail(`La guía pide la idea en al menos ${a.min_sentences} oraciones (el problema y lo que propones); amplíala un poco.`);
    }
    const command = [a.slash, `${a.prefix || ''}${text}`.trim()].filter(Boolean).join(' ');
    const agent = document.getElementById(`phaseAgent${i}`)?.value || undefined;
    const fresh = Boolean(document.getElementById(`phaseFresh${i}`)?.checked);
    if (agent) remember(agent);
    if (hint) { hint.textContent = `Enviando a la terminal: ${command.slice(0, 80)}${command.length > 80 ? '…' : ''}`; hint.classList.remove('is-error'); }
    send(command, true, 'slash', i, { agent, fresh });
  }

  function redirect(a) {
    if (window.closeDrawer) window.closeDrawer();
    if (window.navigateTab) window.navigateTab(a.tab);
    if (a.tab === 'modelo' && a.section && window.filterModelView) {
      const btn = Array.from(document.querySelectorAll('.model-subnav-btn'))
        .find((b) => (b.getAttribute('onclick') || '').includes(`'${a.section}'`));
      window.filterModelView(a.section, btn);
    }
  }

  // Capture phase: the phase drawer stops click propagation
  // (onclick="event.stopPropagation()"), so a bubbling listener never fires.
  document.addEventListener('click', (event) => {
    const el = event.target.closest('[data-phase-action]');
    if (!el) return;
    const i = Number(el.dataset.phaseAction);
    const a = current[i];
    if (!a) return;
    if (a.kind === 'prompt') runPrompt(a, i);
    else if (a.kind === 'command') {
      // A command with a <placeholder> is typed, not run: the operator fills it.
      if (blocked(null)) return;
      send(a.command, !/<[^>]+>/.test(a.command), 'shell', null);
    } else redirect(a);
  }, true);

  document.addEventListener('change', (event) => {
    const el = event.target && event.target.closest && event.target.closest('[data-phase-agent]');
    if (el) refreshAgentInfo().then(() => agentNote(Number(el.dataset.phaseAgent)));
  }, true);
  document.addEventListener('focusin', (event) => {
    if (event.target && event.target.closest && event.target.closest('[data-phase-agent]')) refreshAgentInfo();
  }, true);

  window.renderPhaseActions = renderPhaseActions;
  window.phaseSentenceCount = phaseSentenceCount;
})();

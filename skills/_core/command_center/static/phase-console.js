/* Phase console: what a pipeline phase card lets the operator do.
 *
 * Each phase in GET /api/status carries `actions` (phase_actions.py):
 *   prompt   — a text box guided by the stage's rules; "Ejecutar" types
 *              `/<skill> <text>` into an agent of the support terminal;
 *   command  — a real `papersmith` command, run in the terminal's shell;
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
        <div class="phase-action__foot">
          <span class="phase-action__hint" id="phaseHint${i}">Se envía al agente de la terminal${esc(need)}</span>
          <button class="btn btn--primary btn--sm" data-phase-action="${i}">▶ Ejecutar</button>
        </div>
      </div>`;
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

  async function send(command, run, kind, i) {
    const sent = await window.sendToCli?.(command, run, { kind });
    if (sent && run && currentPhase && window.phaseRuns) {
      window.phaseRuns.start(currentPhase, command);
      const host = document.getElementById('phaseRunTracker');
      if (host) {
        host.dataset.stage = currentPhase.stage_id;
        host.innerHTML = window.phaseRuns.renderTracker(currentPhase);
        if (host.scrollIntoView) host.scrollIntoView({ block: 'start', behavior: 'smooth' });
      }
    } else if (sent === false && i !== undefined && i !== null) {
      showError(i, 'No se pudo enviar a la terminal: revisa el mensaje en la ventana del CLI (abajo a la derecha).');
    }
    return sent;
  }

  function runPrompt(a, i) {
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
    if (hint) { hint.textContent = `Enviando a la terminal: ${command.slice(0, 80)}${command.length > 80 ? '…' : ''}`; hint.classList.remove('is-error'); }
    send(command, true, 'slash', i);
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

  window.renderPhaseActions = renderPhaseActions;
  window.phaseSentenceCount = phaseSentenceCount;
})();

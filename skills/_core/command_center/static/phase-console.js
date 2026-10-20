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

  // Sentences end in . ! or ? followed by a space or the end of the text.
  function phaseSentenceCount(text) {
    const parts = String(text || '').trim().split(/(?<=[.!?])\s+/).filter((p) => /\w/.test(p));
    return parts.length;
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
    if (!current.length) return '';
    const cards = current.map((a, i) => (
      a.kind === 'prompt' ? promptCard(a, i) : a.kind === 'command' ? commandCard(a, i) : redirectCard(a, i)
    )).join('');
    return `<div class="phase-actions">
        <h4 class="phase-actions__title">⚙️ Ejecutar esta fase</h4>
        ${cards}
      </div>`;
  }

  function runPrompt(a, i) {
    const input = document.getElementById(`phaseInput${i}`);
    const hint = document.getElementById(`phaseHint${i}`);
    const text = String(input ? input.value : '').replace(/\s+/g, ' ').trim();
    const fail = (msg) => { if (hint) { hint.textContent = msg; hint.classList.add('is-error'); } input?.focus(); };
    if (!text && !a.optional) return fail('Escribe lo que pide la guía antes de ejecutar.');
    if (a.min_sentences && phaseSentenceCount(text) < a.min_sentences) {
      return fail(`La guía pide al menos ${a.min_sentences} oraciones; llevas ${phaseSentenceCount(text)}.`);
    }
    const command = [a.slash, `${a.prefix || ''}${text}`.trim()].filter(Boolean).join(' ');
    if (hint) { hint.textContent = `Enviado: ${command.slice(0, 80)}${command.length > 80 ? '…' : ''}`; hint.classList.remove('is-error'); }
    window.sendToCli?.(command, true, { kind: 'slash' });
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

  document.addEventListener('click', (event) => {
    const el = event.target.closest('[data-phase-action]');
    if (!el) return;
    const i = Number(el.dataset.phaseAction);
    const a = current[i];
    if (!a) return;
    if (a.kind === 'prompt') runPrompt(a, i);
    else if (a.kind === 'command') {
      // A command with a <placeholder> is typed, not run: the operator fills it.
      window.sendToCli?.(a.command, !/<[^>]+>/.test(a.command), { kind: 'shell' });
    } else redirect(a);
  });

  window.renderPhaseActions = renderPhaseActions;
  window.phaseSentenceCount = phaseSentenceCount;
})();

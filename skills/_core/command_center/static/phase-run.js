/* Phase run tracker: what happens after "Ejecutar" on a pipeline phase.
 *
 * A run starts when a phase action is sent. From then on every status poll
 * (GET /api/status) is compared with the snapshot taken at the start:
 *   1. Comando enviado      — the command reached the support terminal;
 *   2. Agente trabajando    — the terminal printed output since the start;
 *   3. Artefactos           — the phase's evidence files appeared or changed;
 *   4. Etapa verificada     — the server's verdict for the phase is PASS;
 *   5. Siguiente etapa      — the phases the verdict unlocked.
 * The verdict is always the server's: this file never marks a phase done.
 * Runs survive a reload through localStorage when it is available.
 *
 * Public surface (window.phaseRuns): start, onStatus, renderTracker,
 * cardBadge, isRunning, dismiss, justUnlocked.
 */
(function () {
  'use strict';

  const KEY = 'smith_phase_runs';
  const FAST_POLL_MS = 3000;
  const QUIET_MS = 30 * 60 * 1000;
  const UNLOCK_GLOW_MS = 15000;

  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (_) { return {}; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(runs)); } catch (_) { /* storage blocked */ }
  }

  let runs = load();
  let fastTimer = null;
  let tickTimer = null;
  const glow = {}; // stage id -> until (ms)

  const now = () => Date.now();
  const fases = (data) => (data && Array.isArray(data.fases) ? data.fases : []);
  const snapshot = (phase) => Object.fromEntries((phase.evidence || []).map((e) => [e.path, [e.count, e.mtime]]));

  function changedEvidence(run, phase) {
    return (phase.evidence || []).filter((e) => {
      const [count, mtime] = run.baseline[e.path] || [0, 0];
      return e.count > count || e.mtime > mtime;
    });
  }

  function start(phase, command) {
    if (!phase || !phase.stage_id) return;
    const status = window.currentStatus || null;
    runs[phase.stage_id] = {
      stage: phase.stage_id,
      phaseId: phase.id,
      name: phase.name,
      command: String(command || ''),
      startedAt: now(),
      baseline: snapshot(phase),
      unlockedBefore: fases(status).filter((f) => f.unlocked).map((f) => f.stage_id),
      changed: [],
      status: phase.status || 'PENDING',
      verifiedAt: 0,
      unlocked: [],
      lastChangeAt: now(),
    };
    save();
    ensurePolling();
    refreshTracker(phase.stage_id);
  }

  function onStatus(data) {
    const list = fases(data);
    let touched = false;
    for (const run of Object.values(runs)) {
      if (run.verifiedAt) continue;
      const phase = list.find((f) => f.stage_id === run.stage);
      if (!phase) continue;
      const changed = changedEvidence(run, phase).map((e) => ({ label: e.label, path: e.path, count: e.count }));
      if (JSON.stringify(changed) !== JSON.stringify(run.changed)) {
        run.changed = changed;
        run.lastChangeAt = now();
        touched = true;
      }
      if (phase.status !== run.status) { run.status = phase.status; touched = true; }
      if (phase.status === 'PASS') {
        run.verifiedAt = now();
        run.unlocked = list
          .filter((f) => f.unlocked && !run.unlockedBefore.includes(f.stage_id))
          .map((f) => ({ stage: f.stage_id, id: f.id, name: f.name }));
        for (const u of run.unlocked) glow[u.stage] = now() + UNLOCK_GLOW_MS;
        announce(run);
        touched = true;
      }
    }
    if (touched) save();
    for (const run of Object.values(runs)) refreshTracker(run.stage);
    ensurePolling();
  }

  function isRunning(stage) {
    const run = runs[stage];
    return Boolean(run && !run.verifiedAt);
  }

  function anyRunning() {
    return Object.values(runs).some((r) => !r.verifiedAt);
  }

  function ensurePolling() {
    if (anyRunning() && !fastTimer && typeof window.loadStatus === 'function') {
      fastTimer = setInterval(() => window.loadStatus(), FAST_POLL_MS);
    }
    if (!anyRunning() && fastTimer) { clearInterval(fastTimer); fastTimer = null; }
    if (anyRunning() && !tickTimer) {
      tickTimer = setInterval(() => { for (const r of Object.values(runs)) if (!r.verifiedAt) refreshTracker(r.stage); }, 1000);
    }
    if (!anyRunning() && tickTimer) { clearInterval(tickTimer); tickTimer = null; }
  }

  function elapsed(ms) {
    const s = Math.max(0, Math.round(ms / 1000));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  function terminalWorking(run) {
    const act = typeof window.smithTerminalActivity === 'function' ? window.smithTerminalActivity() : null;
    if (!act || !act.lastOutputAt || act.lastOutputAt < run.startedAt) return { state: 'wait', text: 'Esperando salida del agente en la terminal…' };
    const ago = now() - act.lastOutputAt;
    return ago < 5000
      ? { state: 'run', text: `Trabajando (${esc(act.agent || 'agente')}): salida hace ${Math.round(ago / 1000)} s` }
      : { state: 'done', text: `El agente respondió (última salida hace ${elapsed(ago)})` };
  }

  function step(state, title, body) {
    const icon = { done: '✓', run: '●', wait: '○', warn: '!' }[state] || '○';
    return `<li class="run-step run-step--${state}"><span class="run-step__icon">${icon}</span>
        <div><strong>${title}</strong>${body ? `<div class="run-step__body">${body}</div>` : ''}</div></li>`;
  }

  function renderTracker(phase) {
    const run = phase && runs[phase.stage_id];
    if (!run) return '';
    const verified = Boolean(run.verifiedAt);
    const term = terminalWorking(run);
    const quiet = !verified && now() - run.lastChangeAt > QUIET_MS;
    const evidence = (phase.evidence || []).map((e) => {
      const hit = run.changed.some((c) => c.path === e.path);
      return `<li class="${hit ? 'is-new' : ''}">${hit ? '✓' : '·'} ${esc(e.label)} <code>${esc(e.path)}</code>${e.count ? ` · ${e.count}` : ''}</li>`;
    }).join('');
    const unlocked = run.unlocked.length
      ? run.unlocked.map((u) => `<strong>${esc(u.id)}</strong> ${esc(u.name)}`).join(', ')
      : (verified ? 'No había etapas bloqueadas detrás de esta.' : 'Se habilita cuando la etapa quede verificada.');
    const head = verified
      ? `<span class="badge badge--ok">✅ Etapa verificada en ${elapsed(run.verifiedAt - run.startedAt)}</span>`
      : `<span class="badge badge--info">⏳ En ejecución · ${elapsed(now() - run.startedAt)}</span>`;
    return `<div class="run-tracker${verified ? ' is-verified' : ''}" data-run-stage="${esc(run.stage)}">
        <div class="run-tracker__head">
          <strong>Seguimiento de la ejecución</strong>${head}
        </div>
        <ol class="run-steps">
          ${step('done', 'Comando enviado', `<code>${esc(run.command)}</code>`)}
          ${step(verified ? 'done' : term.state, 'Agente trabajando', term.text)}
          ${step(run.changed.length ? 'done' : (verified ? 'done' : 'wait'), 'Artefactos de la etapa', `<ul class="run-evidence">${evidence}</ul>`)}
          ${step(verified ? 'done' : (quiet ? 'warn' : 'wait'), 'Etapa verificada',
              verified ? 'El servidor confirmó la evidencia en disco (PASS).'
                : (quiet ? 'Sin cambios desde hace 30 min: revisa la terminal.' : `Estado actual: ${esc(run.status)}. Se verifica en cada actualización.`))}
          ${step(run.unlocked.length ? 'done' : (verified ? 'done' : 'wait'), 'Etapas siguientes', unlocked)}
        </ol>
        <div class="run-tracker__foot">
          ${verified ? '' : `<button class="btn btn--sm" data-run-verify="${esc(run.phaseId)}">⟳ Verificar ahora</button>`}
          <button class="btn btn--sm" data-run-dismiss="${esc(run.stage)}">${verified ? 'Cerrar seguimiento' : 'Dejar de seguir'}</button>
        </div>
      </div>`;
  }

  function refreshTracker(stage) {
    const host = document.getElementById('phaseRunTracker');
    if (!host || host.dataset.stage !== stage) return;
    const phase = fases(window.currentStatus).find((f) => f.stage_id === stage);
    if (phase) host.innerHTML = renderTracker(phase);
  }

  function cardBadge(stage) {
    const run = runs[stage];
    if (!run) return '';
    return run.verifiedAt
      ? '<span class="badge badge--ok">✅ verificada</span>'
      : '<span class="badge badge--info run-pulse">⏳ en ejecución</span>';
  }

  function justUnlocked(stage) {
    return (glow[stage] || 0) > now();
  }

  function dismiss(stage) {
    delete runs[stage];
    save();
    ensurePolling();
    const host = document.getElementById('phaseRunTracker');
    if (host && host.dataset.stage === stage) host.innerHTML = '';
  }

  function announce(run) {
    const names = run.unlocked.map((u) => u.id).join(', ');
    const text = `✅ ${run.phaseId} verificada${names ? ` · habilitada: ${names}` : ''}`;
    let toast = document.getElementById('phaseToast');
    if (!toast && document.body) {
      toast = document.createElement('div');
      toast.id = 'phaseToast';
      toast.className = 'phase-toast';
      toast.setAttribute('role', 'status');
      document.body.appendChild(toast);
    }
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add('is-visible');
    setTimeout(() => toast.classList.remove('is-visible'), 6000);
  }

  document.addEventListener('click', (event) => {
    const verify = event.target.closest && event.target.closest('[data-run-verify]');
    if (verify && typeof window.triggerRunPhase === 'function') {
      window.triggerRunPhase(verify.dataset.runVerify, null);
      return;
    }
    const close = event.target.closest && event.target.closest('[data-run-dismiss]');
    if (close) dismiss(close.dataset.runDismiss);
  });

  window.phaseRuns = { start, onStatus, renderTracker, cardBadge, isRunning, dismiss, justUnlocked };
  ensurePolling();
})();

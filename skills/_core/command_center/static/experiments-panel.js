/* Experiments tab: proof of concept and full experiments, read from disk.
 *
 * GET /api/experiments answers experiments_view.get_experiments_view(root):
 * the latest experiments protocol (expected reports approved in
 * deliberation), every product folder under implementations/ with its
 * convergence histories, figures, tables, significance tests, pinned
 * artifacts and remote runs, the datasets registry (toy and full sets with
 * their license, qc and remote state), the remote-services table (one row
 * per service with its state and activating action), plus a remote-accounts
 * readiness hint. Convergence is
 * always drawn (inline SVG); when nothing produces it yet, the empty state
 * says which file does. Every value is escaped before insertion.
 *
 * Public surface (window): refreshExperimentsPanel(), ExperimentsPanel.render(view).
 */
(function () {
  'use strict';

  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
  const empty = (text) => `<p class="exp-empty">${esc(text)}</p>`;
  const artifactUrl = (path) => `/api/artifact?path=${encodeURIComponent(path)}`;
  const PALETTE = ['#38bdf8', '#f59e0b', '#10b981', '#ef4444', '#a78bfa', '#f472b6', '#14b8a6', '#eab308',
    '#60a5fa', '#fb923c', '#4ade80', '#f87171'];
  const IMAGE_EXT = /\.(png|svg|jpe?g)$/i;
  const logCharts = new Set();
  let lastView = null;

  const fmt = (v, digits = 3) => {
    if (v === null || v === undefined || v === '') return '—';
    const n = Number(v);
    if (!Number.isFinite(n)) return esc(v);
    if (n !== 0 && (Math.abs(n) < 1e-3 || Math.abs(n) >= 1e5)) return n.toExponential(2);
    return String(Number(n.toFixed(digits)));
  };

  // ---------------------------------------------------------------- charts
  // loss and val_loss share one chart; so do acc and val_acc.
  const metricFamily = (name) => String(name).replace(/^(val|train|test|valid)[_-]/i, '');
  const isLossLike = (name) => /loss|error|mse|nll|cost/i.test(name);

  function chart(id, title, xKey, series) {
    const W = 520, H = 240, L = 52, R = 12, T = 14, B = 34;
    const useLog = logCharts.has(id) && series.every((s) => s.points.some((p) => p[1] > 0));
    const ty = (y) => (useLog ? Math.log10(y) : y);
    const pts = series.map((s) => s.points.filter((p) => !useLog || p[1] > 0));
    const all = pts.flat();
    if (!all.length) return '';
    let xMin = Math.min(...all.map((p) => p[0])), xMax = Math.max(...all.map((p) => p[0]));
    let yMin = Math.min(...all.map((p) => ty(p[1]))), yMax = Math.max(...all.map((p) => ty(p[1])));
    if (xMax === xMin) { xMax += 1; }
    if (yMax === yMin) { yMax += 1; yMin -= 1; }
    const sx = (x) => L + ((x - xMin) / (xMax - xMin)) * (W - L - R);
    const sy = (y) => T + (1 - (ty(y) - yMin) / (yMax - yMin)) * (H - T - B);
    const ticks = [0, 0.25, 0.5, 0.75, 1];
    const yTicks = ticks.map((f) => {
      const v = yMin + f * (yMax - yMin);
      const y = T + (1 - f) * (H - T - B);
      const label = useLog ? fmt(10 ** v) : fmt(v);
      return `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" class="exp-grid"/>`
        + `<text x="${L - 6}" y="${y + 3}" text-anchor="end">${label}</text>`;
    }).join('');
    const xTicks = ticks.map((f) => {
      const v = xMin + f * (xMax - xMin);
      return `<text x="${sx(v)}" y="${H - B + 14}" text-anchor="middle">${fmt(v, 1)}</text>`;
    }).join('');
    const lines = series.map((s, i) => {
      const colour = PALETTE[i % PALETTE.length];
      const d = pts[i].map((p) => `${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`).join(' ');
      return `<polyline fill="none" stroke="${colour}" stroke-width="1.6" points="${d}"><title>${esc(s.label)}</title></polyline>`;
    }).join('');
    const legend = series.map((s, i) => `<span class="exp-legend__item"><i style="background:${PALETTE[i % PALETTE.length]}"></i>${esc(s.label)}</span>`).join('');
    const canLog = series.some((s) => isLossLike(s.name));
    const toggle = canLog
      ? `<button type="button" class="btn exp-log-toggle" data-exp-log="${esc(id)}" aria-pressed="${useLog}">${useLog ? 'Escala lineal' : 'Escala log'}</button>`
      : '';
    return `<figure class="exp-chart">
      <figcaption><strong>${esc(title)}</strong>${toggle}</figcaption>
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}" class="exp-chart__svg">
        <g class="exp-axis">${yTicks}${xTicks}
          <line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/><line x1="${L}" x2="${L}" y1="${T}" y2="${H - B}"/>
          <text x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle">${esc(xKey)}</text>
        </g>${lines}
      </svg>
      <div class="exp-legend">${legend}</div>
    </figure>`;
  }

  function convergence(product) {
    const histories = product.convergence || [];
    if (!histories.length) {
      return empty('Sin curvas de convergencia todavía: las produce Results/history*.json|jsonl|csv '
        + '(o Results/shards/*/history*) con una columna epoch o step y métricas numéricas (loss, val_loss, acc…).');
    }
    return histories.map((h, hi) => {
      const families = new Map();
      (h.series || []).forEach((s) => {
        const key = metricFamily(s.name);
        if (!families.has(key)) families.set(key, []);
        families.get(key).push({ ...s, label: s.group ? `${s.name} · ${s.group}` : s.name });
      });
      const charts = Array.from(families.entries()).map(([family, list]) => (
        chart(`${product.path}|${hi}|${family}`, `${family} — ${h.file.split('/').pop()}`, h.x_key, list)
      )).join('');
      return `<div class="exp-chart-group"><div class="exp-file">${esc(h.file)}</div><div class="exp-chart-grid">${charts}</div></div>`;
    }).join('');
  }

  // ---------------------------------------------------------------- artifacts
  function artifact(path) {
    const name = String(path).split('/').pop();
    if (IMAGE_EXT.test(path)) {
      return `<a class="exp-figure" href="${artifactUrl(path)}" target="_blank" rel="noopener">
        <img src="${artifactUrl(path)}" alt="${esc(name)}" loading="lazy"><span>${esc(name)}</span></a>`;
    }
    return `<a class="exp-figure exp-figure--file" href="${artifactUrl(path)}" target="_blank" rel="noopener">
      <span class="badge badge--info">${esc((name.split('.').pop() || '').toUpperCase())}</span><span>${esc(name)}</span></a>`;
  }

  function table(headers, rows, opts = {}) {
    const head = headers.map((h) => `<th>${esc(h)}</th>`).join('');
    const body = rows.map((r) => `<tr>${headers.map((_, i) => {
      const cell = r[i];
      return cell === '' || cell === undefined
        ? `<td class="exp-pending">${opts.pending ? 'pendiente' : ''}</td>`
        : `<td>${esc(cell)}</td>`;
    }).join('')}</tr>`).join('');
    return `<div class="table-responsive"><table class="table exp-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function tables(product) {
    const list = product.tables || [];
    if (!list.length) return '';
    return `<h4 class="exp-h4">Tablas</h4>` + list.map((t) => `<div class="exp-file">${esc(t.path)}</div>${table(t.headers || [], t.rows || [])}`).join('');
  }

  function significance(product) {
    const rows = product.significance || [];
    if (!rows.length) {
      return `<h4 class="exp-h4">Significancia estadística</h4>`
        + empty('Sin pruebas todavía: las produce Results/significance*.json (comparison, test, statistic, p_value, p_adjusted, correction, effect_size, ci_low, ci_high, n, alpha).');
    }
    const body = rows.map((r) => {
      const alpha = Number.isFinite(Number(r.alpha)) && r.alpha !== null ? Number(r.alpha) : 0.05;
      const p = r.p_adjusted ?? r.p_value;
      const sig = p !== null && p !== undefined && Number(p) < alpha;
      const ci = (r.ci_low ?? null) !== null || (r.ci_high ?? null) !== null ? `[${fmt(r.ci_low)}, ${fmt(r.ci_high)}]` : '—';
      const effect = r.effect_size === null || r.effect_size === undefined ? '—'
        : `${fmt(r.effect_size)}${r.effect_size_name ? ` <small>(${esc(r.effect_size_name)})</small>` : ''}`;
      return `<tr class="${sig ? 'exp-sig' : ''}">
        <td>${esc(r.test || '—')}</td><td>${esc(r.comparison || '—')}</td><td>${fmt(r.statistic)}</td>
        <td>${fmt(r.p_value)}</td><td>${fmt(r.p_adjusted)}${r.correction ? ` <small>${esc(r.correction)}</small>` : ''}</td>
        <td>${effect}</td><td>${ci}</td><td>${fmt(r.n, 0)}</td>
        <td>${sig ? `<span class="badge badge--ok">p &lt; ${fmt(alpha)}</span>` : `<span class="badge">n.s.</span>`}</td></tr>`;
    }).join('');
    return `<h4 class="exp-h4">Significancia estadística</h4><div class="table-responsive"><table class="table exp-table">
      <thead><tr><th>Prueba</th><th>Comparación</th><th>Estadístico</th><th>p</th><th>p ajustado</th><th>Tamaño del efecto</th><th>IC</th><th>n</th><th></th></tr></thead>
      <tbody>${body}</tbody></table></div>`;
  }

  const STATE_LABEL = { submitted: ['badge--info', 'enviado'], returned: ['badge--ok', 'retornado'], errored: ['badge--bad', 'con error'] };
  function runs(product) {
    const r = product.runs || {};
    if (!r.count) return '<span class="badge">sin ejecuciones remotas</span>';
    const chips = Object.entries(r.by_state || {}).map(([state, n]) => {
      const [cls, label] = STATE_LABEL[state] || ['', state];
      return `<span class="badge ${cls}">${esc(label)}: ${esc(n)}</span>`;
    }).join(' ');
    const latest = (r.latest || []).map((e) => {
      const [cls, label] = STATE_LABEL[e.state] || ['', e.state];
      return `<li><span class="badge ${cls}">${esc(label)}</span> <code>${esc(e.entrypoint)}</code>
        ${e.worker ? `· ${esc(e.worker)}` : ''} ${e.ts ? `· <small>${esc(e.ts)}</small>` : ''}
        ${e.reason ? `<div class="exp-reason">${esc(e.reason)}</div>` : ''}</li>`;
    }).join('');
    return `${chips}<details class="exp-runs"><summary>Últimas ejecuciones (${esc(r.count)})</summary><ul>${latest}</ul></details>`;
  }

  function product(p) {
    const pinned = p.pinned || [];
    const figures = (p.figures || []).filter((f) => !pinned.includes(f));
    const warnings = p.warnings || [];
    return `<article class="exp-product">
      <header class="exp-product__header">
        <div><strong>${esc(p.name)}</strong> <small class="exp-muted">${esc(p.path)}</small></div>
        <div class="exp-chips">${runs(p)}</div>
      </header>
      ${pinned.length ? `<h4 class="exp-h4">Artefactos aprobados en deliberación</h4><div class="exp-gallery">${pinned.map(artifact).join('')}</div>` : ''}
      <h4 class="exp-h4">Convergencia</h4>${convergence(p)}
      ${figures.length ? `<h4 class="exp-h4">Figuras</h4><div class="exp-gallery">${figures.map(artifact).join('')}</div>` : ''}
      ${tables(p)}
      ${significance(p)}
      ${warnings.length ? `<details class="exp-warnings"><summary>${esc(warnings.length)} aviso(s) de lectura</summary><ul>${warnings.map((w) => `<li>${esc(w)}</li>`).join('')}</ul></details>` : ''}
    </article>`;
  }

  function group(title, intro, list, emptyText) {
    return `<section class="panel exp-section">
      <div class="panel__header"><div class="panel__title">${esc(title)}</div><span class="panel__meta">${esc(list.length)} producto(s)</span></div>
      <p class="exp-intro">${esc(intro)}</p>
      ${list.length ? list.map(product).join('') : empty(emptyText)}
    </section>`;
  }

  // ---------------------------------------------------------------- protocol
  function protocol(proto) {
    if (!proto) {
      return `<section class="panel exp-section"><div class="panel__header"><div class="panel__title">Protocolo experimental</div></div>
        ${empty('Sin protocolo todavía: /experimental-deliberation escribe experiments/experiments-<slug>-vNN.md.')}</section>`;
    }
    const exps = (proto.experiments || []).map((e) => {
      const reports = (e.expected_reports || []).map((r) => `<div class="exp-file">${esc(r.title)} <span class="badge badge--warn">PENDIENTE</span></div>${table(r.headers || [], r.rows || [], { pending: true })}`).join('')
        || empty('Este experimento no declara un reporte esperado.');
      return `<details class="exp-protocol-item">
        <summary><strong>${esc(e.id)}</strong> ${esc(e.title)} ${e.priority ? `<span class="badge badge--info">${esc(e.priority)}</span>` : ''}</summary>
        ${e.hypothesis ? `<p><strong>Hipótesis:</strong> ${esc(e.hypothesis)}</p>` : ''}
        ${e.success_criterion ? `<p><strong>Criterio de éxito:</strong> ${esc(e.success_criterion)}</p>` : ''}
        ${e.cost ? `<p><strong>Costo estimado:</strong> ${esc(e.cost)}</p>` : ''}
        ${reports}
      </details>`;
    }).join('');
    return `<section class="panel exp-section">
      <div class="panel__header"><div class="panel__title">Protocolo experimental</div><span class="panel__meta">${esc(proto.file)} · v${esc(String(proto.revision).padStart(2, '0'))}</span></div>
      ${proto.validation_scheme ? `<p class="exp-intro"><strong>Esquema de validación:</strong> ${esc(proto.validation_scheme)}</p>` : ''}
      <p class="exp-intro">Reportes esperados aprobados en deliberación: se llenan cuando la implementación experimental escribe sus resultados.</p>
      ${exps || empty('El protocolo no declara experimentos [exp:…].')}
    </section>`;
  }

  // ---------------------------------------------------------- MCP activation
  // The commands run in the dashboard's CLI assistant (window.sendToCli, shell
  // kind): the token is typed there into a hidden prompt, never into this page.
  function cliButton(command, label) {
    return `<button type="button" class="btn" data-exp-cli="${esc(command)}">${esc(label)}</button>`;
  }

  function mcpActivation(state) {
    const st = state || {};
    const activate = st.activate || 'smith mcp kaggle activate';
    const check = st.status || 'smith mcp kaggle status';
    const env = st.environment || {};
    const envVar = st.env || 'KAGGLE_API_TOKEN';
    const tokenPath = env.token_path || st.token_path || '~/.kaggle/access_token';
    const sysLabel = { macos: 'macOS', linux: 'Linux', wsl: 'Windows (WSL)', windows: 'Windows' }[env.system] || 'desconocido';
    const badge = st.activated
      ? `<span class="badge badge--ok">activo (${st.source === 'env' ? `variable ${esc(st.env || 'KAGGLE_API_TOKEN')}` : 'token guardado'})</span>`
      : `<span class="badge badge--warn">${st.problem === 'insecure' ? 'token con permisos inseguros' : 'sin activar'}</span>`;
    const registered = (st.registered || []).length
      ? `registrado en ${(st.registered || []).map((f) => `<code>${esc(f)}</code>`).join(', ')}`
      : 'no registrado en este proyecto: ejecuta <code>smith upgrade</code>';
    return `<section class="panel exp-mcp" id="expMcpActivation">
      <h3 class="panel__title">Activar Kaggle por MCP</h3>
      <p class="exp-intro">Estado: ${badge} · servidor <code>kaggle</code> ${registered}.</p>
      ${env.system ? `<p class="exp-intro">Entorno detectado: <strong>${esc(sysLabel)}</strong> · shell <code>${esc(env.shell || 'sh')}</code>${env.user ? ` · usuario <code>${esc(env.user)}</code>` : ''}.</p>` : ''}
      ${env.note ? `<p class="exp-intro"><span class="badge badge--warn">${esc(sysLabel)}</span> ${esc(env.note)}</p>` : ''}
      <ol>
        <li>Crea un token en <a href="${esc(st.token_page || 'https://www.kaggle.com/settings')}" target="_blank" rel="noopener">kaggle.com/settings</a> → pestaña <em>Account</em> → sección <em>API</em> → <em>Generate New Token</em> (empieza por <code>KGAT_</code>).</li>
        <li>Pulsa <strong>Activar</strong>: abre el asistente CLI smith del tablero y ejecuta <code>${esc(activate)}</code>. Pega el token en la terminal (la entrada queda oculta); smith lo verifica contra Kaggle y lo guarda solo para tu usuario en <code>${esc(tokenPath)}</code>${env.system === 'windows' ? '' : ' (permisos 0600)'}, el mismo archivo que usan la CLI y el SDK oficiales de Kaggle, nunca dentro del proyecto. Si ya tenías otro token ahí, añade <code>--replace</code>.</li>
        <li>Abre una sesión nueva de Claude, OpenCode o Pi desde el asistente: el tablero le pasa <code>${esc(envVar)}</code> y el MCP <code>kaggle</code> queda autenticado. Fuera del tablero, en tu shell: <code>${esc(env.export_command || `export ${envVar}="$(cat ~/.kaggle/access_token)"`)}</code>; para que quede en cada sesión nueva, añade esa línea a <code>${esc(env.profile_file || '~/.profile')}</code>.</li>
        <li>Comprueba con <code>${esc(check)} --verify</code> (lee tu cuota semanal de GPU); <code>smith mcp kaggle deactivate</code> borra el token.</li>
      </ol>
      <div class="exp-mcp__actions">
        ${cliButton(activate, 'Activar en el asistente CLI')}
        ${cliButton(`${check} --verify`, 'Verificar')}
        <button type="button" class="btn" data-exp-refresh="1">Recargar estado</button>
      </div>
    </section>`;
  }

  // ------------------------------------------------------- remote services
  // One offline row per service (experiments_view's `remote_services`). The
  // action is a server-side constant, run in the CLI assistant like the MCP box.
  const SERVICE_STATE = {
    active: ['badge--ok', 'activo'], inactive: ['badge--warn', 'inactivo'],
    missing: ['badge--warn', 'no instalado'], unverified: ['badge--info', 'sin verificar'],
  };

  function remoteServices(state) {
    const rows = state && Array.isArray(state.rows) ? state.rows : [];
    if (!rows.length) return '';
    const body = rows.map((row) => {
      const [cls, label] = SERVICE_STATE[row.state] || SERVICE_STATE.unverified;
      const action = row.action && row.action.command
        ? cliButton(row.action.command, row.action.label || 'Ejecutar')
        : '<span class="exp-muted">—</span>';
      return `<tr><td><strong>${esc(row.service)}</strong></td><td>${esc(row.purpose)}</td>`
        + `<td><span class="badge ${esc(cls)}">${esc(label)}</span>${row.detail ? ` <small>${esc(row.detail)}</small>` : ''}</td>`
        + `<td>${action}</td></tr>`;
    }).join('');
    return `<section class="panel exp-services" id="expRemoteServices">
      <h3 class="panel__title">Servicios de Kaggle</h3>
      ${state.note ? `<p class="exp-intro">${esc(state.note)}</p>` : ''}
      <div class="table-responsive"><table class="table exp-table"><thead><tr><th>Servicio</th><th>Para qué</th><th>Estado</th><th>Acción</th></tr></thead>
      <tbody>${body}</tbody></table></div>
      <div class="exp-mcp__actions"><button type="button" class="btn" data-exp-refresh="1">Recargar estado</button></div>
    </section>`;
  }

  // ---------------------------------------------------------------- help
  function help(accounts) {
    const k = accounts || {};
    const status = `<p class="exp-intro">Estado local: almacén de cuentas Kaggle
      ${k.accounts_store_present ? '<span class="badge badge--ok">presente</span>' : '<span class="badge badge--warn">ausente</span>'}
      · credenciales en <code>${esc(k.inbox || 'kaggle-inbox')}/</code>: <strong>${esc(k.inbox_count ?? 0)}</strong></p>`;
    return `<details class="panel exp-help">
      <summary class="panel__title">Ayuda: lanzar y monitorear en Kaggle (CLI o MCP)</summary>
      ${status}
      <h4 class="exp-h4">1. Flujo: prueba de concepto vs. experimentos completos</h4>
      <ol>
        <li><code>/proposal-implementation</code> construye la <strong>prueba de concepto</strong> (carpeta con <code>AGREED.md</code>).</li>
        <li><code>/experimental-implementation</code> construye los <strong>experimentos completos</strong> del protocolo (carpeta con <code>Experimental_AGREED.md</code>).</li>
        <li><code>/kaggle-accounts validate</code> comprueba que las cuentas autentican (deja <code>kaggle.json</code> en <code>kaggle-inbox/</code>).</li>
        <li><code>/remote-execution</code>, con la forma exacta <code>python skills/remote-execution/scripts/remote_cli.py &lt;verbo&gt;</code>:
          <code>readiness</code> → <code>smoke</code> → <code>generate-job</code> → <code>submit</code> → <code>status</code> / <code>poll</code> → <code>fetch</code>.</li>
        <li>Solo el operador autoriza un lanzamiento: ningún agente ejecuta <code>submit</code> por su cuenta.</li>
      </ol>
      <h4 class="exp-h4">2. GPU</h4>
      <ul>
        <li>El adaptador Kaggle de papersmith ya empuja con <code>enable_gpu: true</code> y <code>machine_shape: "NvidiaTeslaT4"</code>; un <code>enable_gpu</code> solo puede caer en una P100 y fallar.</li>
        <li>Verifica en el log del job: <code>import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))</code>.</li>
        <li>Cuota semanal de GPU en Kaggle: ~30 h (varía); sesión máxima de 9 h. En papersmith.yaml, <code>compute_targets.kaggle-gpu-pool.max_timeout_hours</code> la acota.</li>
      </ul>
      <h4 class="exp-h4">3. Alternativa: Kaggle CLI directo</h4>
      <pre><code>kaggle kernels push -p &lt;dir&gt;          # kernel-metadata.json con "enable_gpu": true
kaggle kernels status &lt;user/slug&gt;
kaggle kernels output &lt;user/slug&gt; -p &lt;dest&gt;</code></pre>
      <p class="exp-intro">El CLI directo no escribe el ledger: el panel no verá esas corridas.</p>
      <h4 class="exp-h4">4. MCP</h4>
      <ul>
        <li>papersmith registra el servidor MCP oficial de Kaggle (<code>https://www.kaggle.com/mcp</code>) como <code>kaggle</code> en <code>.mcp.json</code>, <code>opencode.json</code>, <code>.pi/mcp.json</code> y <code>.agents/mcp_config.json</code> al hacer <code>smith init</code> o <code>smith upgrade</code>.</li>
        <li>Las herramientas públicas (<code>search_datasets</code>, <code>search_notebooks</code>) responden sin token. Las de cuenta piden un token <code>KGAT_…</code> (Kaggle → Settings → API): actívalo con <code>smith mcp kaggle activate</code> desde el asistente CLI (recuadro <em>Activar Kaggle por MCP</em>, que muestra el comando exacto para tu sistema y tu shell); nunca lo escribas en un archivo del proyecto.</li>
        <li>Lanzar con GPU: <code>save_notebook</code> con <code>enableGpuNullable: true</code> y <code>machineShapeNullable: "NvidiaTeslaT4"</code>; monitorear con <code>get_notebook_session_status</code>, <code>list_notebook_session_output</code> y <code>download_notebook_output</code>; cuota semanal con <code>get_accelerator_quota</code>; cancelar con <code>cancel_notebook_session</code>.</li>
        <li>Úsalo para pruebas de concepto rápidas y para monitorear; solo el operador autoriza un lanzamiento.</li>
        <li>Para lanzar, prefiere la ruta CLI de papersmith: registra el ledger (<code>.remote-execution/ledger.jsonl</code>) que este panel lee.</li>
      </ul>
      <h4 class="exp-h4">5. Optimización</h4>
      <ul>
        <li>Circuitos statevector pequeños (≤ ~10 qubits) suelen correr más rápido en CPU o en lote con backprop de torch (PennyLane <code>default.qubit</code>, <code>diff_method="backprop"</code>) que con parameter-shift.</li>
        <li>Pon el backbone clásico en GPU; usa precisión mixta en la parte clásica.</li>
        <li>Reparte shards entre cuentas con <code>distribute</code>.</li>
        <li>Cachea épocas preprocesadas en <code>Data/</code>; fija semillas.</li>
      </ul>
      <h4 class="exp-h4">6. Qué prueba estadística reportar</h4>
      <ul>
        <li>2 modelos en validación cruzada: t-test de remuestreo corregido (Nadeau–Bengio) o 5x2cv.</li>
        <li>≥ 3 modelos: Friedman + post-hoc Nemenyi o Holm.</li>
        <li>Un único conjunto de prueba: McNemar (aciertos) o DeLong (AUC).</li>
        <li>Corrige comparaciones múltiples con Holm; reporta tamaño del efecto e IC.</li>
        <li>Wilcoxon necesita n ≥ 6 pares para poder alcanzar p &lt; 0.05.</li>
      </ul>
    </details>`;
  }

  // ---------------------------------------------------------------- datasets
  const DATASET_LICENSE = {
    allowed: ['badge--ok', 'permitida'], overridden: ['badge--warn', 'aceptada por el operador'],
    refused: ['badge--warn', 'rechazada'],
  };
  const DATASET_QC = { pass: ['badge--ok', 'QC ok'], warn: ['badge--warn', 'QC con avisos'], fail: ['badge--warn', 'QC falla'] };
  const badge = (pair, fallback) => {
    const [cls, label] = pair || ['badge--info', fallback];
    return `<span class="badge ${esc(cls)}">${esc(label)}</span>`;
  };

  function datasets(state) {
    const d = state || {};
    const items = Array.isArray(d.items) ? d.items : [];
    const intro = '<p class="exp-intro">Registro de <code>datasets/registry.json</code> (skill <code>/datasets</code>): el conjunto toy para la prueba de concepto y los datasets completos con su licencia, control de calidad, preparación oficial y estado remoto.</p>';
    if (!items.length) {
      return `<section class="panel exp-datasets"><h3 class="panel__title">Datasets (toy y completos)</h3>${intro}`
        + empty('Sin datasets registrados: /datasets synth crea el conjunto toy con semilla; /datasets search busca datasets reales y deja datasets/search-<fecha>.json.')
        + '</section>';
    }
    const rows = items.map((item) => {
      const remote = item.remote_ref
        ? `<code>${esc(item.remote_ref)}</code> ${badge(item.visibility === 'public' ? ['badge--warn', 'público'] : ['badge--ok', 'privado'])}${item.remote_version != null ? ` <small>v${esc(item.remote_version)}</small>` : ''}`
        : '<span class="badge badge--info">sin publicar</span>';
      const prep = item.prepared
        ? `<span class="badge badge--ok">preparado${item.preparation_version != null ? ` v${esc(item.preparation_version)}` : ''}</span>`
        : '<span class="badge badge--info">sin preparar</span>';
      return `<tr><td><code>${esc(item.slug)}</code></td>`
        + `<td>${badge(item.role === 'toy' ? ['badge--info', 'toy'] : ['badge--info', 'completo'])}</td>`
        + `<td>${esc(item.title)}</td>`
        + `<td>${badge(DATASET_LICENSE[item.license], 'sin licencia')}${item.host_license ? ` <small>${esc(item.host_license)}</small>` : ''}</td>`
        + `<td>${badge(DATASET_QC[item.qc], 'sin QC')}</td><td>${prep}</td><td>${remote}</td></tr>`;
    }).join('');
    const searches = (d.searches || []).length
      ? `<p class="exp-intro">Búsquedas: ${(d.searches || []).map((f) => `<a href="${artifactUrl(f)}" target="_blank" rel="noopener"><code>${esc(f)}</code></a>`).join(', ')}</p>`
      : '';
    return `<section class="panel exp-datasets"><h3 class="panel__title">Datasets (toy y completos)</h3>${intro}
      <div class="table-responsive"><table class="table exp-table"><thead><tr><th>Slug</th><th>Rol</th><th>Título</th><th>Licencia</th><th>QC</th><th>Preparación</th><th>Remoto</th></tr></thead>
      <tbody>${rows}</tbody></table></div>${searches}</section>`;
  }

  // ---------------------------------------------------------------- page
  function render(view) {
    const v = view || {};
    const products = v.products || [];
    const poc = products.filter((p) => p.kind === 'poc');
    const full = products.filter((p) => p.kind === 'full');
    const other = products.filter((p) => p.kind !== 'poc' && p.kind !== 'full');
    return [
      mcpActivation(v.remote_mcp),
      remoteServices(v.remote_services),
      help(v.remote_accounts),
      datasets(v.datasets),
      group('Prueba de concepto', 'Productos de /proposal-implementation (AGREED.md): convergencia, figuras y tablas principales.',
        poc, 'Sin pruebas de concepto: /proposal-implementation crea implementations/<repo>/<Nombre>/ con AGREED.md; sus curvas salen de Results/history*.json|csv.'),
      group('Experimentos completos', 'Productos de /experimental-implementation (Experimental_AGREED.md): convergencia, tablas, figuras y significancia.',
        full, 'Sin experimentos completos: /experimental-implementation crea la carpeta con Experimental_AGREED.md; sus curvas salen de Results/history*.json|csv.'),
      other.length ? group('Sin clasificar', 'Carpetas con Results/ pero sin AGREED.md ni Experimental_AGREED.md.', other, '') : '',
      protocol(v.protocol),
    ].join('');
  }

  function paint() {
    const host = typeof document !== 'undefined' && document.getElementById
      ? document.getElementById('experimentsRoot') : null;
    if (host && lastView) host.innerHTML = render(lastView);
  }

  async function refreshExperimentsPanel() {
    const host = document.getElementById('experimentsRoot');
    if (!host) return;
    try {
      const response = await fetch('/api/experiments', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      lastView = await response.json();
      paint();
    } catch (err) {
      host.innerHTML = empty(`No se pudo leer /api/experiments: ${err.message}`);
    }
  }

  if (typeof document !== 'undefined' && document.addEventListener) {
    document.addEventListener('click', (event) => {
      const closest = (sel) => (event.target && event.target.closest ? event.target.closest(sel) : null);
      const cli = closest('[data-exp-cli]');
      if (cli) {
        if (typeof window.sendToCli === 'function') {
          window.sendToCli(cli.getAttribute('data-exp-cli'), true, { kind: 'shell' });
        }
        return;
      }
      if (closest('[data-exp-refresh]')) { refreshExperimentsPanel(); return; }
      const button = closest('[data-exp-log]');
      if (!button) return;
      const id = button.getAttribute('data-exp-log');
      if (logCharts.has(id)) logCharts.delete(id); else logCharts.add(id);
      paint();
    });
  }

  window.refreshExperimentsPanel = refreshExperimentsPanel;
  window.ExperimentsPanel = { render, mcpActivation, remoteServices, datasets };
})();

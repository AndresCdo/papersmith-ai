import { useCallback, useEffect, useState } from 'react';
import { useWorkspaceEvents } from './hooks/useWorkspaceEvents';
import PipelineGraph from './components/dag/PipelineGraph';
import HarnessStatus from './components/health/HarnessStatus';
import WiringMatrix from './components/health/WiringMatrix';
import DiagnosticLog from './components/health/DiagnosticLog';
import SectionMatrix from './components/sections/SectionMatrix';
import ArtifactViewer from './components/artifacts/ArtifactViewer';
import { StatusBadge } from './components/StatusBadge';
import { asText, formatCount, formatTime } from './lib/format';
import type { WorkspaceState } from './types';

const TABS = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'health', label: 'Health' },
  { id: 'sections', label: 'Sections' },
  { id: 'artifacts', label: 'Artifacts' },
] as const;

type TabId = (typeof TABS)[number]['id'];
const DEFAULT_TAB: TabId = 'pipeline';

/** Hash routing: no router dependency, one durable URL per tab. */
function readHash(): TabId {
  const value = window.location.hash.replace(/^#/, '');
  return TABS.some((tab) => tab.id === value) ? (value as TabId) : DEFAULT_TAB;
}

function TotalsBar({ state }: { state: WorkspaceState | null }) {
  const totals = state?.totals;
  const chips: { label: string; value: string }[] = [
    { label: 'sections', value: formatCount(totals?.sections) },
    { label: 'blocks', value: `${formatCount(totals?.blocks_written)}/${formatCount(totals?.blocks_total)}` },
    { label: 'words', value: formatCount(totals?.word_count) },
    { label: 'placeholder citations', value: formatCount(totals?.placeholder_citations) },
    { label: 'gates passed', value: `${formatCount(totals?.gates_passed)}/${formatCount(totals?.gates_total)}` },
  ];
  return (
    <div className="totals">
      {chips.map((chip) => (
        <span key={chip.label} className="totals__chip">
          <strong>{chip.value}</strong>
          {chip.label}
        </span>
      ))}
    </div>
  );
}

export default function App() {
  const { state, health, connected, lastChanged, loading, error, smoke, runSmoke, clearSmoke } =
    useWorkspaceEvents();
  const [tab, setTab] = useState<TabId>(() => readHash());

  useEffect(() => {
    const onHashChange = () => setTab(readHash());
    window.addEventListener('hashchange', onHashChange);
    // Normalize `#` and unknown fragments to a real tab on first paint.
    if (window.location.hash.replace(/^#/, '') !== tab) {
      window.location.hash = tab;
    }
    return () => window.removeEventListener('hashchange', onHashChange);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initial normalization only
  }, []);

  const selectTab = useCallback((next: TabId) => {
    window.location.hash = next;
    setTab(next);
  }, []);

  const workspace = state?.workspace;
  const paper = state?.paper_metadata;
  const authors = (paper?.authors ?? []).map(asText).filter((author): author is string => Boolean(author));

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__identity">
          <h1>Paper Command Center</h1>
          <p className="topbar__subtitle">
            {workspace?.name ?? paper?.title ?? 'no workspace loaded'}
            {workspace?.version ? ` · v${workspace.version}` : ''}
            {state?.generated_at ? ` · state read ${formatTime(state.generated_at)}` : ''}
          </p>
        </div>
        <div className="topbar__status">
          <StatusBadge label={connected ? 'LIVE' : 'RECONNECTING'} tone={connected ? 'ok' : 'warn'} />
          {lastChanged.length > 0 ? (
            <span className="topbar__changed" title={lastChanged.join('\n')}>
              changed: {lastChanged.slice(0, 3).join(', ')}
              {lastChanged.length > 3 ? ` (+${lastChanged.length - 3})` : ''}
            </span>
          ) : null}
        </div>
      </header>

      <nav className="tabs" aria-label="Dashboard sections">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className="tabs__button"
            data-active={tab === entry.id}
            aria-current={tab === entry.id ? 'page' : undefined}
            onClick={() => selectTab(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {error ? <p className="banner banner--bad">{error}</p> : null}

        {tab === 'pipeline' ? (
          <>
            <section className="panel panel--paper">
              <div className="panel__header">
                <h2>{paper?.title ?? paper?.name ?? 'Paper metadata unavailable'}</h2>
                <span className="panel__meta">
                  {paper?.venue_target ?? 'no venue target'} · {paper?.domain_profile ?? 'no domain profile'}
                </span>
              </div>
              <dl className="meta-strip">
                <div>
                  <dt>Topic</dt>
                  <dd>{paper?.topic ?? '—'}</dd>
                </div>
                <div>
                  <dt>Authors</dt>
                  <dd>{authors.length > 0 ? authors.join(', ') : '—'}</dd>
                </div>
                <div>
                  <dt>Compute target</dt>
                  <dd>{paper?.compute_target ?? '—'}</dd>
                </div>
                <div>
                  <dt>Active tools</dt>
                  <dd>{(paper?.tools ?? []).map(asText).filter(Boolean).join(', ') || '—'}</dd>
                </div>
                <div>
                  <dt>Workspace root</dt>
                  <dd className="mono">{workspace?.root ?? '—'}</dd>
                </div>
              </dl>
              <TotalsBar state={state} />
            </section>

            <PipelineGraph state={state} />

            <section className="panel">
              <div className="panel__header">
                <h2>Gate detail</h2>
                <span className="panel__meta">{formatCount(state?.gates?.length)} gate(s)</span>
              </div>
              {(state?.gates ?? []).length === 0 ? (
                <p className="panel__empty">No gate results in the latest state payload.</p>
              ) : (
                <ul className="gate-list">
                  {(state?.gates ?? []).map((gate) => (
                    <li key={gate.id} className="gate-list__item">
                      <div className="gate-list__head">
                        <span className="cell-title">{gate.name ?? gate.id}</span>
                        <StatusBadge
                          label={gate.state ?? 'UNKNOWN'}
                          tone={
                            gate.state === 'PASSED' ? 'ok' : gate.state === 'BLOCKED' ? 'bad' : 'warn'
                          }
                        />
                      </div>
                      <p className="mono gate-list__id">{gate.id}</p>
                      {(gate.reasons ?? []).length > 0 ? (
                        <ul className="reason-list">
                          {(gate.reasons ?? []).map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="cell-sub">no blocking reason</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}

        {tab === 'health' ? (
          <>
            <HarnessStatus health={health} />
            <WiringMatrix health={health} />
            <DiagnosticLog smoke={smoke} runSmoke={runSmoke} clearSmoke={clearSmoke} connected={connected} />
          </>
        ) : null}

        {tab === 'sections' ? <SectionMatrix sections={state?.sections ?? []} /> : null}

        {tab === 'artifacts' ? <ArtifactViewer state={state} /> : null}

        {loading && state === null && health === null ? (
          <p className="banner banner--info">Loading the workspace snapshot…</p>
        ) : null}
      </main>
    </div>
  );
}

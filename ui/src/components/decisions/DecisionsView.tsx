import { useState } from 'react';
import { StatusBadge, type BadgeTone } from '../StatusBadge';
import type { DecisionEvent, DecisionSourceInfo, DecisionsPayload } from '../../types';

interface Props {
  data: DecisionsPayload | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  retry: () => void;
}

/** Known sources in the backend's order, with the label shown to the reader. */
const SOURCE_LABELS: Record<string, string> = {
  declarations: 'declarations',
  proposal: 'proposal',
  experiment: 'experiment',
  'remote-execution': 'remote ledger',
};

const STATUS_TONE: Record<string, BadgeTone> = { ok: 'ok', absent: 'idle', unreadable: 'bad', too_large: 'warn' };

const UNVERIFIED_TITLE = 'Read from the lifecycle files without hash or consistency checks.';

const sourceLabel = (source: string) => SOURCE_LABELS[source] ?? source;

/** `2026-03-02T10:15:30Z` -> `2026-03-02 10:15:30 UTC`; a zone-less value is read as UTC;
 * unparseable values are shown as given. */
function formatUtc(ts: string): string {
  // `new Date()` reads a zone-less date-time as LOCAL time; the backend treats
  // it as UTC, so say so explicitly before parsing.
  const naive = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(ts.trim());
  const parsed = new Date(naive ? `${ts.trim().replace(' ', 'T')}Z` : ts);
  if (Number.isNaN(parsed.getTime())) return ts;
  return `${parsed.toISOString().slice(0, 19).replace('T', ' ')} UTC`;
}

function SourceStatus({ sources }: { sources: Record<string, DecisionSourceInfo> }) {
  return (
    <ul className="decisions-sources" aria-label="Source status">
      {Object.entries(sources).map(([name, info]) => (
        <li key={name} className="decisions-sources__item">
          <span className="cell-title">{sourceLabel(name)}</span>
          <StatusBadge label={info.status} tone={STATUS_TONE[info.status] ?? 'idle'} />
          <span className="panel__meta">{info.count} event(s)</span>
          {info.truncated ? <StatusBadge label="truncated" tone="warn" /> : null}
          {info.detail ? <span className="panel__meta">{info.detail}</span> : null}
        </li>
      ))}
    </ul>
  );
}

function Row({ event }: { event: DecisionEvent }) {
  return (
    <li className="decision">
      <div className="decision__head">
        <span className="decision__time mono">{event.ts ? formatUtc(event.ts) : 'no timestamp'}</span>
        <span className="decision__source" data-source={event.source}>
          {sourceLabel(event.source)}
        </span>
        <span className="decision__kind">{event.kind}</span>
        {event.verified === false ? (
          <span className="decision__unverified" title={UNVERIFIED_TITLE}>
            unverified
          </span>
        ) : null}
      </div>
      <p className="decision__summary">{event.summary}</p>
      <p className="decision__ref mono">{event.ref}</p>
      {event.note ? <p className="panel__meta">{event.note}</p> : null}
    </li>
  );
}

/** Decisions tab: a read-only timeline merged from the workspace's persisted records. */
export default function DecisionsView({ data, loading, error, refresh, retry }: Props) {
  const [hidden, setHidden] = useState<ReadonlySet<string>>(new Set());
  const toggle = (name: string) =>
    setHidden((current) => {
      const next = new Set(current);
      if (!next.delete(name)) next.add(name);
      return next;
    });

  const events = (data?.events ?? []).filter((entry) => !hidden.has(entry.source));
  const dated = events.filter((entry) => entry.ts !== null);
  const undated = events.filter((entry) => entry.ts === null);
  return (
    <div className="decisions" aria-busy={loading}>
      <div className="atlas__toolbar">
        <button type="button" className="button button--ghost" onClick={refresh} disabled={loading}>
          Refresh
        </button>
        <span className="panel__meta">The decision sources are not watched; refresh to re-read them.</span>
      </div>
      {error ? (
        <p className="banner banner--bad" role="alert">
          {error}{' '}
          <button type="button" className="button button--ghost" onClick={retry}>
            Retry
          </button>
        </p>
      ) : null}
      {data === null ? (
        loading ? <p className="banner banner--info">Loading the decisions…</p> : null
      ) : (
        <section className="panel" aria-labelledby="decisions-title">
          <div className="panel__header">
            <h2 id="decisions-title">Decisions</h2>
            {data.truncated ? <span className="panel__meta">{`Showing ${data.events.length} of ${data.total}`}</span> : null}
          </div>
          <SourceStatus sources={data.sources} />
          <fieldset className="decisions-filter">
            <legend className="panel__meta">Show sources</legend>
            {Object.keys(data.sources).map((name) => (
              <label key={name} className="decisions-filter__option">
                <input type="checkbox" checked={!hidden.has(name)} onChange={() => toggle(name)} />
                {sourceLabel(name)}
              </label>
            ))}
          </fieldset>
          {data.events.length === 0 ? (
            <p className="panel__empty">No recorded decisions yet</p>
          ) : events.length === 0 ? (
            <p className="panel__empty">No decisions match the selected sources</p>
          ) : null}
          {dated.length > 0 ? (
            <ol className="decision-list" aria-label="Dated decisions">
              {dated.map((entry, index) => (
                <Row key={`${entry.source}:${entry.ref}:${index}`} event={entry} />
              ))}
            </ol>
          ) : null}
          {undated.length > 0 ? (
            <>
              <h3 className="subheading">Undated</h3>
              <p className="panel__meta">Revision receipts carry no timestamp, so these records cannot be placed in time.</p>
              <ol className="decision-list" aria-label="Undated decisions">
                {undated.map((entry, index) => (
                  <Row key={`${entry.source}:${entry.ref}:${index}`} event={entry} />
                ))}
              </ol>
            </>
          ) : null}
        </section>
      )}
    </div>
  );
}

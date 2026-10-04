import { useMemo, useState } from 'react';
import { filterEntries, groupForDisplay, type HistoryState } from '../../lib/history';
import HistoryList from './HistoryList';

interface Props {
  history: HistoryState;
  error: string | null;
  presentIds: ReadonlySet<string>;
  /** Open an element in the pipeline tab. */
  onSelect: (elementId: string) => void;
}

/** History tab: what changed since the dashboard server started. */
export default function HistoryView({ history, error, presentIds, onSelect }: Props) {
  const [kind, setKind] = useState<string | null>(null);
  const [element, setElement] = useState<string | null>(null);

  const kinds = useMemo(() => [...new Set(history.entries.map((entry) => entry.kind))].sort(), [history.entries]);
  const elements = useMemo(
    () => [...new Set(history.entries.map((entry) => entry.element_id).filter((id): id is string => id !== null))].sort(),
    [history.entries],
  );
  const rows = useMemo(
    () => groupForDisplay(filterEntries(history.entries, { kind, element })),
    [history.entries, kind, element],
  );

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>History since the dashboard started</h2>
        <span className="panel__meta">{history.entries.length} change(s) recorded in memory</span>
      </div>
      {error ? (
        <p className="banner banner--bad" role="alert">
          {error}
        </p>
      ) : null}
      {history.gap ? (
        <p className="banner banner--warn">Some earlier entries were dropped.</p>
      ) : null}
      <div className="history-filters">
        <label>
          Kind
          <select value={kind ?? ''} onChange={(event) => setKind(event.target.value || null)}>
            <option value="">All kinds</option>
            {kinds.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Element
          <select value={element ?? ''} onChange={(event) => setElement(event.target.value || null)}>
            <option value="">All elements</option>
            {elements.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>
      {rows.length === 0 ? (
        <p className="panel__empty">No changes recorded yet.</p>
      ) : (
        <HistoryList rows={rows} showElement presentIds={presentIds} onSelect={onSelect} />
      )}
    </section>
  );
}

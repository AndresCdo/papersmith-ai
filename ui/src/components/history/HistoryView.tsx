import { useEffect, useMemo, useState } from 'react';
import { filterEntries, groupForDisplay, type HistoryState } from '../../lib/history';
import HistoryList from './HistoryList';

interface Props {
  history: HistoryState;
  error: string | null;
  /** Element ids in the current diagram; null while the workspace state is unknown. */
  presentIds: ReadonlySet<string> | null;
  /** Open an element in the pipeline tab. */
  onSelect: (elementId: string) => void;
}

/** History tab: what changed since the dashboard server started. */
export default function HistoryView({ history, error, presentIds, onSelect }: Props) {
  const [selectedKind, setKind] = useState<string | null>(null);
  const [selectedElement, setElement] = useState<string | null>(null);

  const kinds = useMemo(() => [...new Set(history.entries.map((entry) => entry.kind))].sort(), [history.entries]);
  const elements = useMemo(
    () => [...new Set(history.entries.map((entry) => entry.element_id).filter((id): id is string => id !== null))].sort(),
    [history.entries],
  );
  // A filter whose value is no longer among the options falls back to "all".
  const kind = selectedKind !== null && kinds.includes(selectedKind) ? selectedKind : null;
  const element = selectedElement !== null && elements.includes(selectedElement) ? selectedElement : null;
  useEffect(() => {
    if (kind !== selectedKind) setKind(null);
    if (element !== selectedElement) setElement(null);
  }, [kind, selectedKind, element, selectedElement]);
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
        history.entries.length > 0 ? (
          <div className="panel__empty">
            <p>No changes match the current filter</p>
            <button
              type="button"
              className="button button--ghost"
              onClick={() => {
                setKind(null);
                setElement(null);
              }}
            >
              Clear filters
            </button>
          </div>
        ) : (
          <p className="panel__empty">No changes recorded yet.</p>
        )
      ) : (
        <HistoryList rows={rows} showElement presentIds={presentIds ?? undefined} onSelect={onSelect} />
      )}
    </section>
  );
}

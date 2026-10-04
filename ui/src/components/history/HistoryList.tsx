import type { DisplayRow } from '../../lib/history';

interface Props {
  rows: DisplayRow[];
  /** Show the element of each row as a link; the element panel hides it. */
  showElement: boolean;
  /** Element ids that exist in the current diagram. */
  presentIds?: ReadonlySet<string>;
  onSelect?: (elementId: string) => void;
}

function formatEntryTime(ts: number): string {
  const date = new Date(ts * 1000);
  return Number.isNaN(date.getTime()) ? String(ts) : date.toLocaleTimeString();
}

/** Newest-first list of history rows; a grouped row collapses word-count runs. */
export default function HistoryList({ rows, showElement, presentIds, onSelect }: Props) {
  return (
    <ul className="history-list">
      {rows.map((row) => {
        const newest = row.entries[0];
        const oldest = row.entries[row.entries.length - 1];
        const elementId = newest.element_id;
        const vanished = showElement && elementId !== null && presentIds !== undefined && !presentIds.has(elementId);
        return (
          <li key={row.key} className="history-list__item">
            <div className="history-list__head">
              <time className="mono history-list__time">{formatEntryTime(newest.ts)}</time>
              <span className="history-list__kind">{newest.kind}</span>
              {showElement && elementId !== null ? (
                <button type="button" className="button button--ghost mono" onClick={() => onSelect?.(elementId)}>
                  {elementId}
                </button>
              ) : null}
              {vanished ? <span className="cell-sub">No longer present</span> : null}
            </div>
            {row.grouped ? (
              <p className="history-list__summary">
                {row.entries.length} word-count changes: {String(oldest.before)} to {String(newest.after)} words
              </p>
            ) : (
              <p className="history-list__summary">{newest.summary}</p>
            )}
          </li>
        );
      })}
    </ul>
  );
}

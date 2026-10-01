import { useMemo, useState } from 'react';
import { StatusBadge, toneForWiringState } from '../StatusBadge';
import { formatCount } from '../../lib/format';
import type { MatrixRow, WiringHealth } from '../../types';

const FILTERS = ['all', 'problems', 'gates'] as const;
type Filter = (typeof FILTERS)[number];

const FILTER_LABEL: Record<Filter, string> = {
  all: 'All rows',
  problems: 'Non-WIRED',
  gates: 'Gate-mapped',
};

function rowKey(row: MatrixRow, index: number): string {
  return [row.harness, row.agent, row.skill, row.gate, index].join('|');
}

/**
 * The `[Harness] -> [Agent] -> [Skill] -> [Gate]` trace table. Badge vocabulary
 * is the backend's: WIRED, DRIFT, UNBOUND, TOOL_MISSING, UNVERIFIED.
 */
export default function WiringMatrix({ health }: { health: WiringHealth | null }) {
  const [filter, setFilter] = useState<Filter>('all');
  const rows = health?.matrix ?? [];

  const visible = useMemo(() => {
    if (filter === 'problems') return rows.filter((row) => row.state !== 'WIRED');
    if (filter === 'gates') return rows.filter((row) => Boolean(row.gate));
    return rows;
  }, [filter, rows]);

  const counts = useMemo(() => {
    const tally = new Map<string, number>();
    for (const row of rows) {
      const key = row.state ?? 'UNKNOWN';
      tally.set(key, (tally.get(key) ?? 0) + 1);
    }
    return [...tally.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Wiring matrix</h2>
        <span className="panel__meta">
          {formatCount(rows.length)} trace row(s)
          {counts.length > 0 ? ` · ${counts.map(([state, count]) => `${state} ${count}`).join(', ')}` : ''}
        </span>
      </div>

      <div className="toolbar">
        {FILTERS.map((option) => (
          <button
            key={option}
            type="button"
            className="toolbar__button"
            data-active={filter === option}
            onClick={() => setFilter(option)}
          >
            {FILTER_LABEL[option]}
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="panel__empty">No matrix rows in the wiring-health payload.</p>
      ) : visible.length === 0 ? (
        <p className="panel__empty">No rows match this filter.</p>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Harness</th>
                <th scope="col">Harness state</th>
                <th scope="col">Agent</th>
                <th scope="col">Skill</th>
                <th scope="col">Gate</th>
                <th scope="col">Row state</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row, index) => (
                <tr key={rowKey(row, index)}>
                  <td className="mono">{row.harness ?? '—'}</td>
                  <td>
                    <StatusBadge
                      label={row.harness_state ?? 'UNKNOWN'}
                      tone={toneForHarnessState(row.harness_state)}
                    />
                  </td>
                  <td className="mono">{row.agent ?? '—'}</td>
                  <td className="mono">{row.skill ?? '—'}</td>
                  <td className="mono">{row.gate ?? '—'}</td>
                  <td>
                    <StatusBadge label={row.state ?? 'UNKNOWN'} tone={toneForWiringState(row.state)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

/** Harness rows reuse the sync vocabulary, so map it onto the wiring tones. */
function toneForHarnessState(state: string | undefined) {
  if (state === 'IN_SYNC') return 'ok' as const;
  if (state === 'DRIFT_DETECTED') return 'warn' as const;
  return 'idle' as const;
}

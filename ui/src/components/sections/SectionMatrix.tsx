import { useEffect, useMemo, useState } from 'react';
import { ProgressBar, StatusBadge, toneForSectionStatus } from '../StatusBadge';
import { formatCount, formatPercent } from '../../lib/format';
import SectionDetail, { extentLabel } from './SectionDetail';
import type { Section } from '../../types';

function wordFraction(section: Section): number {
  const max = section.extent?.max_words;
  const min = section.extent?.min_words;
  const words = section.word_count ?? 0;
  const ceiling = typeof max === 'number' && max > 0 ? max : min;
  if (typeof ceiling !== 'number' || ceiling <= 0) return words > 0 ? 1 : 0;
  return Math.min(1, words / ceiling);
}

/**
 * Ten-section matrix: lifecycle badge, word-count progress against the
 * contract's declared `extent`, fact counters, and a drawer that exposes the
 * unwritten blocks and unresolved citation keys for one section.
 */
export default function SectionMatrix({ sections }: { sections: Section[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = useMemo(
    () => sections.find((section) => section.id === selectedId) ?? null,
    [sections, selectedId],
  );

  useEffect(() => {
    if (selectedId === null) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedId(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [selectedId]);

  const totals = useMemo(() => {
    const words = sections.reduce((sum, section) => sum + (section.word_count ?? 0), 0);
    const written = sections.reduce((sum, section) => sum + (section.blocks_written ?? 0), 0);
    const blocks = sections.reduce((sum, section) => sum + (section.blocks_total ?? 0), 0);
    const placeholders = sections.reduce((sum, section) => sum + (section.citations?.placeholders ?? 0), 0);
    return { words, written, blocks, placeholders };
  }, [sections]);

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Sections</h2>
        <span className="panel__meta">
          {formatCount(sections.length)} section(s) · {formatCount(totals.written)}/{formatCount(totals.blocks)} blocks ·{' '}
          {formatCount(totals.words)} words · {formatCount(totals.placeholders)} placeholder citations
        </span>
      </div>

      {sections.length === 0 ? (
        <p className="panel__empty">No section contracts found in this workspace.</p>
      ) : (
        <div className="table-scroll">
          <table className="data-table data-table--sections">
            <thead>
              <tr>
                <th scope="col">Section</th>
                <th scope="col">Status</th>
                <th scope="col">Words</th>
                <th scope="col">Blocks</th>
                <th scope="col">Facts produces/demands</th>
                <th scope="col">Citations</th>
                <th scope="col" aria-label="Open detail" />
              </tr>
            </thead>
            <tbody>
              {sections.map((section) => {
                const produces = section.facts?.produces?.length ?? 0;
                const demands = section.facts?.demands?.length ?? 0;
                const verified = section.citations?.verified ?? 0;
                const placeholders = section.citations?.placeholders ?? 0;
                const width = wordFraction(section);
                return (
                  <tr
                    key={section.id}
                    className={selectedId === section.id ? 'is-selected' : undefined}
                    onClick={() => setSelectedId(section.id)}
                  >
                    <td>
                      <span className="cell-title">{section.section ?? section.id}</span>
                      <span className="cell-sub mono">{section.id}</span>
                    </td>
                    <td>
                      <StatusBadge label={section.status ?? 'UNKNOWN'} tone={toneForSectionStatus(section.status)} />
                      {section.has_contract === false ? <span className="cell-sub">no contract</span> : null}
                    </td>
                    <td className="cell-words">
                      <ProgressBar
                        fraction={width}
                        tone={width >= 1 ? 'ok' : 'info'}
                        label={`${formatCount(section.word_count)} (${formatPercent(width)})`}
                      />
                      <span className="cell-sub">{extentLabel(section)}</span>
                    </td>
                    <td className="mono">
                      {formatCount(section.blocks_written)}/{formatCount(section.blocks_total)}
                    </td>
                    <td className="cell-words">
                      <span className="fact-balance" data-balanced={produces >= demands}>
                        {formatCount(produces)} produced / {formatCount(demands)} demanded
                      </span>
                      <span className="cell-sub">
                        {formatCount(section.facts?.declarations?.length ?? 0)} declaration(s)
                      </span>
                    </td>
                    <td>
                      <span className="cell-title">{formatCount(verified)} verified</span>
                      <span className="cell-sub" data-alert={placeholders > 0}>
                        {formatCount(placeholders)} placeholder(s)
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedId(section.id);
                        }}
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected ? (
        <div className="drawer">
          <button
            type="button"
            className="drawer__backdrop"
            aria-label="Close section detail"
            onClick={() => setSelectedId(null)}
          />
          <aside className="drawer__panel" aria-label={`Section detail: ${selected.id}`}>
            <header className="drawer__header">
              <div>
                <h3>{selected.section ?? selected.id}</h3>
                <p className="mono">{selected.id}</p>
              </div>
              <button type="button" className="button button--ghost" onClick={() => setSelectedId(null)}>
                Close
              </button>
            </header>

            <SectionDetail section={selected} />
          </aside>
        </div>
      ) : null}
    </section>
  );
}

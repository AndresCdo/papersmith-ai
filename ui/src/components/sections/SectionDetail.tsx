import { StatusBadge, toneForSectionStatus } from '../StatusBadge';
import { asText, formatCount } from '../../lib/format';
import type { Section } from '../../types';

export function extentLabel(section: Section): string {
  const min = section.extent?.min_words;
  const max = section.extent?.max_words;
  if (typeof min === 'number' && typeof max === 'number') return `${min}–${max} words`;
  if (typeof max === 'number') return `≤ ${max} words`;
  if (typeof min === 'number') return `≥ ${min} words`;
  return 'extent not declared';
}

/**
 * The contract detail of one section (status, extent, citations, blocks, fact
 * contract). Shared by the Sections drawer and the diagram's element panel;
 * it owns no chrome, no title and no key handling.
 */
export default function SectionDetail({ section: selected }: { section: Section }) {
  return (
    <>
    <dl className="detail-grid">
      <div>
        <dt>Status</dt>
        <dd>
          <StatusBadge label={selected.status ?? 'UNKNOWN'} tone={toneForSectionStatus(selected.status)} />
        </dd>
      </div>
      <div>
        <dt>File</dt>
        <dd className="mono">{selected.file ?? '—'}</dd>
      </div>
      <div>
        <dt>Mode</dt>
        <dd>{asText(selected.mode) ?? '—'}</dd>
      </div>
      <div>
        <dt>Position</dt>
        <dd>{asText(selected.position) ?? '—'}</dd>
      </div>
      <div>
        <dt>Extent</dt>
        <dd>{extentLabel(selected)}</dd>
      </div>
      <div>
        <dt>Words</dt>
        <dd>{formatCount(selected.word_count)}</dd>
      </div>
      <div>
        <dt>Blocks</dt>
        <dd>
          {formatCount(selected.blocks_written)}/{formatCount(selected.blocks_total)} written
        </dd>
      </div>
      <div>
        <dt>Citations</dt>
        <dd>
          {formatCount(selected.citations?.verified)} verified · {formatCount(selected.citations?.placeholders)}{' '}
          placeholder(s)
        </dd>
      </div>
    </dl>

    {selected.citations?.unresolved_keys?.length ? (
      <div className="drawer__section">
        <h4>Unresolved citation keys</h4>
        <ul className="chip-list chip-list--alert">
          {selected.citations.unresolved_keys.map((key) => (
            <li key={key} className="mono">
              {key}
            </li>
          ))}
        </ul>
      </div>
    ) : (
      <p className="banner banner--ok">No unresolved citation keys.</p>
    )}

    <div className="drawer__section">
      <h4>Blocks</h4>
      {selected.blocks?.length ? (
        <ul className="block-list">
          {selected.blocks.map((block, index) => (
            <li key={block.id ?? `block-${index}`} data-written={block.written === true}>
              <div className="block-list__row">
                <span className="mono">{block.id ?? `block ${index + 1}`}</span>
                <StatusBadge label={block.written ? 'WRITTEN' : 'PENDING'} tone={block.written ? 'ok' : 'idle'} />
                {block.optional ? <StatusBadge label="OPTIONAL" tone="info" /> : null}
              </div>
              <div className="block-list__facts">
                <span>requires: {asText(block.requires_facts) ?? '—'}</span>
                <span>produces: {asText(block.produces_facts) ?? '—'}</span>
                <span>declarations: {asText(block.requires_declarations) ?? '—'}</span>
                {asText(block.citations) ? <span>citations: {asText(block.citations)}</span> : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="panel__empty">This section contract declares no blocks.</p>
      )}
    </div>

    <div className="drawer__section">
      <h4>Fact contract</h4>
      <div className="fact-columns">
        <div>
          <h5>Produces</h5>
          <ul className="chip-list">
            {(selected.facts?.produces ?? []).map((fact) => (
              <li key={fact} className="mono">
                {fact}
              </li>
            ))}
            {(selected.facts?.produces ?? []).length === 0 ? <li className="chip-list__empty">none</li> : null}
          </ul>
        </div>
        <div>
          <h5>Demands</h5>
          <ul className="chip-list">
            {(selected.facts?.demands ?? []).map((fact) => (
              <li key={fact} className="mono">
                {fact}
              </li>
            ))}
            {(selected.facts?.demands ?? []).length === 0 ? <li className="chip-list__empty">none</li> : null}
          </ul>
        </div>
        <div>
          <h5>Declarations</h5>
          <ul className="chip-list">
            {(selected.facts?.declarations ?? []).map((fact) => (
              <li key={fact} className="mono">
                {fact}
              </li>
            ))}
            {(selected.facts?.declarations ?? []).length === 0 ? <li className="chip-list__empty">none</li> : null}
          </ul>
        </div>
      </div>
    </div>
    </>
  );
}

import { StatusBadge, type BadgeTone } from '../StatusBadge';
import type { AtlasPayload, AtlasSummary, AtlasValidation } from '../../types';

interface Props {
  data: AtlasPayload | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  retry: () => void;
}

const JSON_NOTES: Record<string, string> = {
  too_large: 'sota-pool/atlas.json is too large to summarize.',
  unsafe: 'sota-pool/atlas.json was skipped as unsafe: it is not a regular file inside the workspace.',
  unreadable: 'sota-pool/atlas.json could not be read.',
  invalid: 'sota-pool/atlas.json is not valid JSON.',
};

const HTML_NOTES: Record<string, string> = {
  too_large: 'sota-pool/atlas.html is too large to show.',
  unsafe: 'sota-pool/atlas.html was skipped as unsafe: it is not a regular file inside the workspace.',
};

const VALIDATION_TONE: Record<AtlasValidation['status'], BadgeTone> = { ok: 'ok', failed: 'bad', unavailable: 'warn' };
const VALIDATION_LABEL: Record<AtlasValidation['status'], string> = { ok: 'valid', failed: 'failed', unavailable: 'unavailable' };

function ValidationChip({ validation }: { validation: AtlasValidation }) {
  const errors = validation.errors ?? [];
  const more = (validation.error_count ?? errors.length) - errors.length;
  return (
    <div className="atlas-validation" role="group" aria-label="Validation">
      <StatusBadge label={VALIDATION_LABEL[validation.status] ?? validation.status} tone={VALIDATION_TONE[validation.status] ?? 'idle'} />
      {validation.status === 'unavailable' && validation.detail ? <p className="panel__meta">{validation.detail}</p> : null}
      {validation.status === 'failed' ? (
        <>
          <ul className="reason-list">
            {errors.map((message, index) => (
              <li key={index}>{message}</li>
            ))}
          </ul>
          {more > 0 ? <p className="panel__meta">{more} more</p> : null}
        </>
      ) : null}
    </div>
  );
}

function SummaryPanel({ summary, validation }: { summary: AtlasSummary; validation: AtlasValidation }) {
  const rels = Object.entries(summary.rels);
  return (
    <section className="panel atlas-summary" aria-labelledby="atlas-summary-title">
      <div className="panel__header">
        <h2 id="atlas-summary-title">Atlas summary</h2>
        <span className="panel__meta">{summary.systems.length} system(s)</span>
      </div>
      <ValidationChip validation={validation} />
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">System</th>
              <th scope="col">Planets</th>
              <th scope="col">Families</th>
            </tr>
          </thead>
          <tbody>
            {summary.systems.map((system, index) => (
              <tr key={`${system.id}:${index}`}>
                <td className="cell-title">{system.title || system.id}</td>
                <td>{system.planets}</td>
                <td>{system.families.length > 0 ? system.families.join(', ') : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="panel__meta">{summary.links} link(s)</p>
      {rels.length > 0 ? (
        <ul className="chip-list" aria-label="Link kinds">
          {rels.map(([rel, count]) => (
            <li key={rel}>{`${rel}: ${count}`}</li>
          ))}
        </ul>
      ) : null}
      <h3 className="subheading">Evidence</h3>
      <p className="panel__meta">{`showing ${summary.evidence.length} of ${summary.evidence_total}`}</p>
      {summary.evidence.length > 0 ? (
        <ul className="atlas-evidence">
          {summary.evidence.map((entry, index) => (
            <li key={`${entry.system}:${entry.planet}:${index}`}>
              <span className="mono">{`${entry.system}/${entry.planet}`}</span>
              <span>{entry.origin}</span>
              <span className="panel__meta">{entry.retrieved}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function Constellation({ data }: { data: AtlasPayload }) {
  const note = HTML_NOTES[data.html.status];
  return (
    <section className="panel atlas-view" aria-labelledby="atlas-view-title">
      <div className="panel__header">
        <h2 id="atlas-view-title">Constellation</h2>
        {data.stale === true ? <StatusBadge label="STALE: atlas.json is newer than atlas.html; re-render" tone="warn" /> : null}
      </div>
      {data.html.status === 'ok' ? (
        <iframe
          className="atlas-view__frame"
          title="SOTA constellation"
          src="/api/atlas/view"
          sandbox="allow-scripts"
          referrerPolicy="no-referrer"
        />
      ) : note ? (
        <p className="panel__empty">{note}</p>
      ) : data.json.status === 'ok' ? (
        <p className="panel__empty" data-testid="atlas-html-missing">
          JSON present, HTML missing: the constellation is rendered from atlas.json by{' '}
          <span className="mono">scripts/render_atlas.py</span>; run it to produce sota-pool/atlas.html.
        </p>
      ) : null}
    </section>
  );
}

/** Atlas tab: native summary of atlas.json next to the sandboxed constellation. */
export default function AtlasView({ data, loading, error, refresh, retry }: Props) {
  const jsonStatus = data?.json.status;
  return (
    <div className="atlas" aria-busy={loading}>
      <div className="atlas__toolbar">
        <button type="button" className="button button--ghost" onClick={refresh} disabled={loading}>
          Refresh
        </button>
        <span className="panel__meta">The atlas files are not watched; refresh after re-running the plausibility skill.</span>
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
        loading ? <p className="banner banner--info">Loading the atlas…</p> : null
      ) : (
        <>
          {jsonStatus === 'absent' && data.html.status === 'absent' ? (
            <p className="banner banner--info">No atlas yet. Run the plausibility skill to scout and map the SOTA pool.</p>
          ) : null}
          {jsonStatus === 'absent' && data.html.status === 'ok' ? (
            <p className="banner banner--warn">atlas.html exists but atlas.json is missing, so there is no summary to show.</p>
          ) : null}
          {jsonStatus && JSON_NOTES[jsonStatus] ? (
            <p className="banner banner--warn" data-testid="atlas-json-note">
              {JSON_NOTES[jsonStatus]}
            </p>
          ) : null}
          <div className="atlas__layout">
            {data.summary ? <SummaryPanel summary={data.summary} validation={data.validation} /> : null}
            {data.html.status === 'absent' && jsonStatus === 'absent' ? null : <Constellation data={data} />}
          </div>
        </>
      )}
    </div>
  );
}

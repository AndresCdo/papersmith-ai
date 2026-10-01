import { formatCount } from '../../lib/format';
import type { WorkspaceState } from '../../types';

function LedgerCard({
  title,
  count,
  hint,
  items,
  emptyLabel,
}: {
  title: string;
  count: number;
  hint: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <article className="ledger">
      <header className="ledger__header">
        <h3>{title}</h3>
        <span className="ledger__count">{formatCount(count)}</span>
      </header>
      <p className="ledger__hint">{hint}</p>
      {items.length > 0 ? (
        <ul className="file-list">
          {items.map((item) => (
            <li key={item} className="mono">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="ledger__empty">{emptyLabel}</p>
      )}
    </article>
  );
}

function FigureTile({ name, kind }: { name: string; kind: 'pdf' | 'raster' }) {
  return (
    <li className="figure-tile" data-kind={kind} title={name}>
      <span className="figure-tile__glyph" aria-hidden="true">
        {kind === 'pdf' ? 'PDF' : 'PNG'}
      </span>
      <span className="figure-tile__name mono">{name}</span>
    </li>
  );
}

/**
 * Artifact ledger: compiled figures and rasters from `figures`, the
 * `experiments` files, and the workspace's ingestion inbox drop list.
 *
 * The inbox's own directory name comes from the payload, never from this file:
 * which skill owns a drop-zone is the workspace's business, and a label spelled
 * here would be one target's vocabulary shipped to every other one.
 *
 * The API exposes figure names only, so tiles are name plates. Inline previews
 * would require a served path for `paper/Figures/*`, which the command center
 * deliberately does not mount.
 */
export default function ArtifactViewer({ state }: { state: WorkspaceState | null }) {
  const figures = state?.figures;
  const experiments = state?.experiments;
  const inbox = state?.inbox;

  const pdf = figures?.pdf ?? [];
  const rasters = figures?.rasters ?? [];

  return (
    <div className="artifacts">
      <section className="panel">
        <div className="panel__header">
          <h2>Figures</h2>
          <span className="panel__meta">
            {formatCount(figures?.count)} entr(ies) in paper/Figures/ · {formatCount(pdf.length)} compiled PDF ·{' '}
            {formatCount(rasters.length)} raster
          </span>
        </div>

        <h3 className="subheading">Compiled PDF</h3>
        {pdf.length > 0 ? (
          <ul className="figure-grid">
            {pdf.map((name) => (
              <FigureTile key={name} name={name} kind="pdf" />
            ))}
          </ul>
        ) : (
          <p className="panel__empty">No compiled figure PDF in this workspace.</p>
        )}

        <h3 className="subheading">Rasters</h3>
        {rasters.length > 0 ? (
          <ul className="figure-grid">
            {rasters.map((name) => (
              <FigureTile key={name} name={name} kind="raster" />
            ))}
          </ul>
        ) : (
          <p className="panel__empty">No raster figures in this workspace.</p>
        )}
      </section>

      <div className="ledger-grid">
        <LedgerCard
          title="Experiment artifacts"
          count={experiments?.count ?? 0}
          hint="Files under experiments/ tracked by the state extractor."
          items={experiments?.files ?? []}
          emptyLabel="No experiment artifacts recorded."
        />
        <LedgerCard
          title="Ingestion inbox"
          count={inbox?.count ?? 0}
          hint={
            inbox?.directory
              ? `Entries waiting under ${inbox.directory}/ for ingestion.`
              : 'No skill in this workspace declares an ingestion drop-zone.'
          }
          items={inbox?.paths ?? []}
          emptyLabel="Inbox is empty."
        />
      </div>
    </div>
  );
}

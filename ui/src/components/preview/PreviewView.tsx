import { StatusBadge, toneForSectionStatus } from '../StatusBadge';
import type { PaperPreview, PreviewBlock } from '../../types';
import { cacheToken, withVersion } from '../cacheToken';

interface Props {
  data: PaperPreview | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

const FILE_URL = '/api/paper/file?name=';

const MAIN_TEX_NOTES: Record<string, string> = {
  absent: 'There is no paper/main.tex yet, so no block has been written.',
  too_large: 'paper/main.tex is too large to preview.',
  unsafe: 'paper/main.tex was skipped as unsafe: it is not a regular file inside the workspace.',
  unreadable: 'paper/main.tex could not be read.',
};

const figureUrl = (id: string, kind: string) => `${FILE_URL}figures/${encodeURIComponent(id)}.${kind}`;
const formatSize = (bytes: number) => (bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KiB` : `${bytes} B`);

function BlockView({ block }: { block: PreviewBlock }) {
  return (
    <li className="preview-block" data-testid="preview-block">
      <p className="preview-block__id mono">
        {block.id}
        {block.written ? <span className="panel__meta"> · {block.words} word(s)</span> : null}
      </p>
      {block.duplicate ? (
        <p className="banner banner--warn">Duplicate block id in main.tex; only the first occurrence is shown.</p>
      ) : null}
      {block.written ? (
        <>
          {/* React text node: markup in the paper is shown literally, never parsed. */}
          <p className="preview-block__text">{block.text}</p>
          {block.truncated ? (
            <p className="banner banner--warn">This block is cut short by the preview size limit.</p>
          ) : null}
          {block.citations.length > 0 ? (
            <ul className="chip-list" aria-label="Citations">
              {block.citations.map((key) => (
                <li key={key} className="mono">
                  {key}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : (
        <p className="panel__empty">
          Not written yet: <span className="mono">{block.id}</span>
        </p>
      )}
    </li>
  );
}

function PdfPane({ pdf }: { pdf: PaperPreview['pdf'] }) {
  const main = pdf?.main ?? null;
  const figures = pdf?.figures ?? [];
  return (
    <section className="panel preview-pdf" aria-labelledby="preview-pdf-title">
      <div className="panel__header">
        <h2 id="preview-pdf-title">Compiled PDF</h2>
        {main?.stale ? <StatusBadge label="stale: main.tex is newer than main.pdf" tone="warn" /> : null}
      </div>
      {main ? (
        <iframe
          key={cacheToken(main)}
          className="preview-pdf__frame"
          title="Compiled paper PDF"
          src={withVersion(`${FILE_URL}main.pdf`, main)}
          referrerPolicy="no-referrer"
        />
      ) : (
        <p className="panel__empty">
          No compiled PDF found. papersmith does not compile the whole paper; build it yourself and it will appear here.
        </p>
      )}
      <h3 className="subheading">Figures</h3>
      {figures.length === 0 ? (
        <p className="panel__empty">No compiled figures in paper/Figures.</p>
      ) : (
        <ul className="preview-figures">
          {figures.map((figure) => (
            <li key={`${figure.id}.${figure.kind}`} className="preview-figures__item">
              <span className="mono">{figure.id}</span>
              <span className="panel__meta">
                {figure.kind} · {formatSize(figure.size)}
              </span>
              <a href={figureUrl(figure.id, figure.kind)} target="_blank" rel="noopener noreferrer">
                Open<span className="sr-only"> {figure.id}.{figure.kind}</span>
              </a>
              {figure.kind === 'png' ? (
                <img
                  key={cacheToken(figure)}
                  className="preview-figures__thumb"
                  src={withVersion(figureUrl(figure.id, figure.kind), figure)}
                  alt={`Figure ${figure.id}`}
                  loading="lazy"
                />
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Preview tab: block text of the paper next to the compiled PDF, read-only. */
export default function PreviewView({ data, loading, error, retry }: Props) {
  return (
    <div className="preview" aria-busy={loading}>
      {error ? (
        <p className="banner banner--bad" role="alert">
          {error}{' '}
          <button type="button" className="button button--ghost" onClick={retry}>
            Retry
          </button>
        </p>
      ) : null}
      {data === null ? (
        loading ? <p className="banner banner--info">Loading the paper preview…</p> : null
      ) : (
        <div className="preview__layout">
          <section className="panel preview-text" aria-labelledby="preview-text-title">
            <div className="panel__header">
              <h2 id="preview-text-title">Paper text</h2>
              <span className="panel__meta">{data.sections.length} section(s)</span>
            </div>
            {data.truncated ? <p className="banner banner--warn">Preview truncated</p> : null}
            {data.main_tex.status !== 'ok' ? (
              <p className="banner banner--info">
                {MAIN_TEX_NOTES[data.main_tex.status] ?? `paper/main.tex status: ${data.main_tex.status}`}
              </p>
            ) : null}
            {data.sections.length === 0 ? (
              <p className="panel__empty">No sections yet</p>
            ) : (
              data.sections.map((section) => (
                <section
                  key={section.id}
                  className="preview-section"
                  aria-label={section.title ?? section.id}
                >
                  <div className="preview-section__head">
                    <h3>{section.title ?? section.id}</h3>
                    {section.title ? <span className="mono panel__meta">{section.id}</span> : null}
                    <StatusBadge label={section.status} tone={toneForSectionStatus(section.status)} />
                  </div>
                  <ol className="preview-blocks">
                    {section.blocks.map((block, index) => (
                      // a contract may declare the same block id twice: the index keeps keys unique
                      <BlockView key={`${index}:${block.id}`} block={block} />
                    ))}
                  </ol>
                </section>
              ))
            )}
          </section>
          <PdfPane pdf={data.pdf} />
        </div>
      )}
    </div>
  );
}

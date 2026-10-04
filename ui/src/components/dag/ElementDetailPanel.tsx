import { useEffect, useRef, type ReactNode } from 'react';
import { ProgressBar, StatusBadge, toneForGateState } from '../StatusBadge';
import SectionDetail from '../sections/SectionDetail';
import { formatPercent } from '../../lib/format';
import type { GraphModel } from './graph';
import type { WorkspaceState } from '../../types';

interface Props {
  elementId: string;
  state: WorkspaceState | null;
  graph: GraphModel;
  /** Select another element, or null to close the panel. */
  onSelect: (id: string | null) => void;
}

interface Connection {
  edgeId: string;
  relation: string;
  neighbourId: string;
  direction: 'in' | 'out';
}

function titleOf(graph: GraphModel, id: string): string {
  const data = graph.nodes.find((node) => node.id === id)?.data;
  const value = data?.title ?? data?.name ?? data?.label;
  return typeof value === 'string' && value ? value : id;
}

function Connections({ id, graph, onSelect }: { id: string; graph: GraphModel; onSelect: Props['onSelect'] }) {
  const connections: Connection[] = graph.edges
    .filter((edge) => edge.source === id || edge.target === id)
    .map((edge) => ({
      edgeId: edge.id,
      relation: String(edge.data?.relation ?? 'related'),
      neighbourId: edge.source === id ? edge.target : edge.source,
      direction: edge.source === id ? 'out' : 'in',
    }));
  return (
    <div className="drawer__section">
      <h4>Connections</h4>
      {connections.length === 0 ? (
        <p className="panel__empty">No connections.</p>
      ) : (
        <ul className="connection-list">
          {connections.map((connection) => (
            <li key={connection.edgeId}>
              <button type="button" className="button button--ghost" onClick={() => onSelect(connection.neighbourId)}>
                {titleOf(graph, connection.neighbourId)}
              </button>
              <button type="button" className="button button--ghost" onClick={() => onSelect(connection.edgeId)}>
                {connection.direction === 'out' ? 'to' : 'from'}: {connection.relation}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * Drawer for the element selected in the pipeline diagram. Non-modal (the
 * canvas stays clickable), owns the single Escape listener, moves focus into
 * itself on open and returns it to the previously focused element on close.
 */
export default function ElementDetailPanel({ elementId, state, graph, onSelect }: Props) {
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    rootRef.current?.focus();
    return () => {
      if (previous && previous.isConnected) previous.focus();
    };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onSelect(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onSelect]);

  const edge = graph.edges.find((entry) => entry.id === elementId);
  const node = edge ? undefined : graph.nodes.find((entry) => entry.id === elementId);
  const kind = node ? elementId.slice(0, elementId.indexOf(':')) : null;
  const rawId = node ? elementId.slice(elementId.indexOf(':') + 1) : '';

  let title = elementId;
  let body: ReactNode;

  if (edge) {
    title = 'Connection';
    body = (
      <>
        <dl className="detail-grid">
          <div>
            <dt>Relation</dt>
            <dd>{String(edge.data?.relation ?? 'related')}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>
              <button type="button" className="button button--ghost" onClick={() => onSelect(edge.source)}>
                {titleOf(graph, edge.source)}
              </button>
            </dd>
          </div>
          <div>
            <dt>Target</dt>
            <dd>
              <button type="button" className="button button--ghost" onClick={() => onSelect(edge.target)}>
                {titleOf(graph, edge.target)}
              </button>
            </dd>
          </div>
        </dl>
      </>
    );
  } else if (node && kind === 'stage') {
    const stage = state?.pipeline_stages?.find((entry) => entry.id === rawId);
    title = stage?.title ?? rawId;
    const progress = typeof stage?.progress === 'number' ? stage.progress : 0;
    body = (
      <>
        <dl className="detail-grid">
          <div>
            <dt>State</dt>
            <dd>{stage?.active ? 'active' : 'idle'}</dd>
          </div>
          <div>
            <dt>Progress</dt>
            <dd>
              <ProgressBar fraction={progress} tone={progress >= 1 ? 'ok' : 'info'} label={formatPercent(progress)} />
            </dd>
          </div>
          <div>
            <dt>Detail</dt>
            <dd>{stage?.detail || '—'}</dd>
          </div>
          <div>
            <dt>Workers</dt>
            <dd>{stage?.workers?.length ? stage.workers.join(', ') : 'no worker agents'}</dd>
          </div>
        </dl>
        <Connections id={elementId} graph={graph} onSelect={onSelect} />
      </>
    );
  } else if (node && kind === 'gate') {
    const gate = state?.gates?.find((entry) => entry.id === rawId);
    title = gate?.name ?? rawId;
    const sources = graph.edges.filter((entry) => entry.target === elementId && entry.source.startsWith('stage:'));
    body = (
      <>
        <dl className="detail-grid">
          <div>
            <dt>State</dt>
            <dd>
              <StatusBadge label={gate?.state ?? 'UNKNOWN'} tone={toneForGateState(gate?.state)} />
            </dd>
          </div>
          <div>
            <dt>Source stages</dt>
            <dd>{sources.length ? sources.map((entry) => titleOf(graph, entry.source)).join(', ') : '—'}</dd>
          </div>
        </dl>
        <div className="drawer__section">
          <h4>Reasons</h4>
          {gate?.reasons?.length ? (
            <ul className="reason-list">
              {gate.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          ) : (
            <p className="cell-sub">no blocking reason</p>
          )}
        </div>
        <Connections id={elementId} graph={graph} onSelect={onSelect} />
      </>
    );
  } else if (node && kind === 'section') {
    const section = state?.sections?.find((entry) => entry.id === rawId);
    title = section?.section ?? rawId;
    body = (
      <>
        {section ? (
          <SectionDetail section={section} />
        ) : null}
        <Connections id={elementId} graph={graph} onSelect={onSelect} />
      </>
    );
  } else {
    body = <p className="banner banner--warn">No longer present in the latest state.</p>;
  }

  return (
    <aside
      ref={rootRef}
      tabIndex={-1}
      className="element-panel"
      data-testid="element-detail-panel"
      aria-label={`Element detail: ${elementId}`}
    >
      <header className="drawer__header">
        <div>
          <h3>{title}</h3>
          <p className="mono">{elementId}</p>
        </div>
        <button type="button" className="button button--ghost" onClick={() => onSelect(null)}>
          Close
        </button>
      </header>
      {body}
    </aside>
  );
}

import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { ProgressBar } from '../../StatusBadge';
import { formatPercent } from '../../../lib/format';

export type StageNodeData = {
  title: string;
  active: boolean;
  progress: number;
  detail: string;
  workers: string[];
  /** True while the stage has work in flight; drives the animated edges. */
  mutating: boolean;
};

export type StageFlowNode = Node<StageNodeData, 'stage'>;

/** One pipeline stage (`ingestion` … `publishing`) as a graph node. */
export default function StageNode({ data }: NodeProps<StageFlowNode>) {
  return (
    <div className={`dag-node dag-node--stage${data.mutating ? ' is-mutating' : ''}`}>
      <Handle type="target" position={Position.Top} className="dag-handle" />
      <header className="dag-node__header">
        <span className="dag-node__title">{data.title}</span>
        <span className="dag-pill" data-active={data.active}>
          {data.active ? 'active' : 'idle'}
        </span>
      </header>
      <ProgressBar
        fraction={data.progress}
        tone={data.progress >= 1 ? 'ok' : 'info'}
        label={formatPercent(data.progress)}
      />
      <p className="dag-node__detail">{data.detail}</p>
      {data.workers.length > 0 ? (
        <ul className="dag-node__workers">
          {data.workers.slice(0, 3).map((worker) => (
            <li key={worker}>{worker}</li>
          ))}
          {data.workers.length > 3 ? (
            <li className="dag-node__workers-more">+{data.workers.length - 3}</li>
          ) : null}
        </ul>
      ) : (
        <p className="dag-node__muted">no worker agents</p>
      )}
      <Handle type="source" position={Position.Bottom} className="dag-handle" />
    </div>
  );
}

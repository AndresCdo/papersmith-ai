import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { StatusBadge, toneForGateState } from '../../StatusBadge';

export type GateNodeData = {
  name: string;
  state: string;
  reasons: string[];
  /** Scalar / array-length summary of `gate.parts`. */
  parts: { key: string; value: string }[];
  /** A gate still measuring is "mutating", so its edges animate. */
  mutating: boolean;
};

export type GateFlowNode = Node<GateNodeData, 'gate'>;

/** One quality gate (`writing-readiness` … `diagram-raster`) as a graph node. */
export default function GateNode({ data }: NodeProps<GateFlowNode>) {
  return (
    <div className={`dag-node dag-node--gate${data.mutating ? ' is-mutating' : ''}`}>
      <Handle type="target" position={Position.Top} className="dag-handle" />
      <header className="dag-node__header">
        <span className="dag-node__title">{data.name}</span>
        <StatusBadge label={data.state} tone={toneForGateState(data.state)} />
      </header>
      {data.parts.length > 0 ? (
        <ul className="dag-node__parts">
          {data.parts.map((part) => (
            <li key={part.key}>
              <span className="dag-node__parts-key">{part.key}</span>
              <span className="dag-node__parts-value">{part.value}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {data.reasons.length > 0 ? (
        <p className="dag-node__reason" title={data.reasons.join('\n')}>
          {data.reasons[0]}
          {data.reasons.length > 1 ? ` (+${data.reasons.length - 1} more)` : ''}
        </p>
      ) : (
        <p className="dag-node__muted">no blocking reason</p>
      )}
      <Handle type="source" position={Position.Bottom} className="dag-handle" />
    </div>
  );
}

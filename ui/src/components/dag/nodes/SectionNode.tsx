import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { StatusBadge, toneForSectionStatus } from '../../StatusBadge';
import { formatCount } from '../../../lib/format';

export type SectionNodeData = {
  label: string;
  status: string;
  wordCount: number;
  maxWords: number | null;
  blocksWritten: number;
  blocksTotal: number;
  placeholders: number;
  /** True while the section still has unwritten blocks. */
  mutating: boolean;
};

export type SectionFlowNode = Node<SectionNodeData, 'section'>;

/** One section contract / draft as a graph node. */
export default function SectionNode({ data }: NodeProps<SectionFlowNode>) {
  const fraction =
    typeof data.maxWords === 'number' && data.maxWords > 0
      ? Math.min(1, data.wordCount / data.maxWords)
      : 0;
  return (
    <div className={`dag-node dag-node--section${data.mutating ? ' is-mutating' : ''}`}>
      <Handle type="target" position={Position.Top} className="dag-handle" />
      <header className="dag-node__header">
        <span className="dag-node__title">{data.label}</span>
        <StatusBadge label={data.status || 'UNKNOWN'} tone={toneForSectionStatus(data.status)} />
      </header>
      <div className="dag-node__words">
        <span>
          {formatCount(data.wordCount)}
          {data.maxWords ? ` / ${data.maxWords}` : ''} words
        </span>
        <span>
          {formatCount(data.blocksWritten)}/{formatCount(data.blocksTotal)} blocks
        </span>
      </div>
      <div className="progress progress--slim">
        <div className="progress-track">
          <div className="progress-fill" data-tone={fraction >= 1 ? 'ok' : 'info'} style={{ width: `${fraction * 100}%` }} />
        </div>
      </div>
      {data.placeholders > 0 ? (
        <p className="dag-node__reason">{data.placeholders} citation placeholder(s)</p>
      ) : (
        <p className="dag-node__muted">citations clean</p>
      )}
      <Handle type="source" position={Position.Bottom} className="dag-handle" />
    </div>
  );
}

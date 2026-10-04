import { useCallback, useEffect, useMemo, useRef } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  Panel,
  ReactFlow,
  type EdgeChange,
  type NodeChange,
  type NodeTypes,
  type EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode from './nodes/StageNode';
import GateNode from './nodes/GateNode';
import SectionNode from './nodes/SectionNode';
import AnimatedEdge from './edges/AnimatedEdge';
import type { GraphModel } from './graph';
import { reduceSelection, type AnyChange } from '../../lib/selection';

const nodeTypes = {
  stage: StageNode,
  gate: GateNode,
  section: SectionNode,
} satisfies NodeTypes;

const edgeTypes = {
  animated: AnimatedEdge,
} satisfies EdgeTypes;

/**
 * The pipeline DAG: six stages in a top-to-bottom chain, the four quality gates
 * hanging off the stage they inspect, and every section placed between
 * `drafting` and `auditing`. Edges animate while either endpoint is mutating.
 */
export default function PipelineGraph({
  graph,
  selectedId,
  onSelect,
}: {
  graph: GraphModel;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}) {
  const { width, height } = graph;

  // Layout (dagre) is computed once per state upstream; selection only maps
  // copies, so clicks and live updates never re-run the layout.
  const nodes = useMemo(
    () => graph.nodes.map((node) => ({ ...node, selected: node.id === selectedId })),
    [graph.nodes, selectedId],
  );
  const edges = useMemo(
    () => graph.edges.map((edge) => ({ ...edge, selected: edge.id === selectedId })),
    [graph.edges, selectedId],
  );

  // React Flow reports node and edge selection (clicks and its own Enter/Space/
  // Escape handling on focused wrappers) as `select` changes on two callbacks.
  // Collect them and resolve the whole interaction once per microtask.
  const pending = useRef<AnyChange[]>([]);
  const currentId = useRef(selectedId);
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    currentId.current = selectedId;
    onSelectRef.current = onSelect;
  });

  const collect = useCallback((changes: (NodeChange | EdgeChange)[]) => {
    const selects = changes.filter((change) => change.type === 'select');
    if (selects.length === 0) return;
    const first = pending.current.length === 0;
    pending.current.push(...(selects as AnyChange[]));
    if (!first) return;
    queueMicrotask(() => {
      const batch = pending.current;
      pending.current = [];
      const next = reduceSelection(batch, currentId.current);
      if (next !== null && next.id !== currentId.current) onSelectRef.current(next.id);
    });
  }, []);

  if (graph.nodes.length === 0) {
    return (
      <div className="panel panel--empty">
        <h2>Pipeline</h2>
        <p>No pipeline stages in the latest state payload. The command center is waiting for the first read.</p>
      </div>
    );
  }

  return (
    // The shell takes the graph's own aspect ratio, so fitView fills the width
    // at a readable zoom and the page (not the canvas) scrolls vertically.
    <div className="graph-shell" style={{ aspectRatio: `${width} / ${height}`, width: '100%', maxWidth: width, marginInline: 'auto' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ maxZoom: 1, padding: 0.02 }}
        minZoom={0.3}
        maxZoom={1.75}
        zoomOnScroll={false}
        preventScrolling={false}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        edgesFocusable
        nodesFocusable
        multiSelectionKeyCode={null}
        selectionKeyCode={null}
        deleteKeyCode={null}
        onNodesChange={collect}
        onEdgesChange={collect}
        onNodeClick={(_event, node) => onSelect(node.id)}
        onEdgeClick={(_event, edge) => onSelect(edge.id)}
        onPaneClick={() => onSelect(null)}
        defaultEdgeOptions={{ type: 'animated' }}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1} />
        <Controls showInteractive={false} />
        <Panel position="top-left" className="graph-legend">
          <span className="graph-legend__title">Pipeline DAG</span>
          <span className="graph-legend__item">
            <i className="legend-swatch" data-kind="stage" /> stage
          </span>
          <span className="graph-legend__item">
            <i className="legend-swatch" data-kind="gate" /> gate
          </span>
          <span className="graph-legend__item">
            <i className="legend-swatch" data-kind="section" /> section
          </span>
          <span className="graph-legend__item">
            <i className="legend-swatch" data-kind="edge" /> mutating
          </span>
        </Panel>
      </ReactFlow>
    </div>
  );
}

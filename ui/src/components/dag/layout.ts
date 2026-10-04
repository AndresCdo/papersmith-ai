import dagre from '@dagrejs/dagre';
import type { Edge, Node } from '@xyflow/react';

export const NODE_SIZE: Record<string, { width: number; height: number }> = {
  stage: { width: 260, height: 176 },
  gate: { width: 240, height: 184 },
  section: { width: 240, height: 158 },
};

/** The widest row the graph allows; wider dagre ranks wrap into several rows. */
export const MAX_PER_ROW = 4;

const MARGIN = 32;
const ROW_GAP = 44;
const RANK_GAP = 78;
const COLUMN_GAP = 36;

type AnyFlowNode = Node<Record<string, unknown>>;

export interface GraphLayout {
  nodes: AnyFlowNode[];
  width: number;
  height: number;
}

function sizeOf(node: AnyFlowNode) {
  return NODE_SIZE[node.type ?? 'stage'] ?? NODE_SIZE.stage;
}

/** Split `count` items into the fewest rows of at most MAX_PER_ROW, as evenly as possible. */
function rowSizes(count: number): number[] {
  const rows = Math.ceil(count / MAX_PER_ROW);
  const base = Math.floor(count / rows);
  const extra = count % rows;
  return Array.from({ length: rows }, (_, index) => base + (index < extra ? 1 : 0));
}

/**
 * Top-to-bottom layout. Dagre decides the ranks and the order inside each rank;
 * a rank wider than MAX_PER_ROW is then wrapped into several centred rows so the
 * whole graph stays narrow enough to read at laptop widths (a single rank of
 * 14 sections and gates would otherwise force a zoom below 0.3).
 */
export function layoutGraph(nodes: AnyFlowNode[], edges: Edge[]): GraphLayout {
  if (nodes.length === 0) return { nodes, width: 0, height: 0 };

  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: 'TB', nodesep: COLUMN_GAP, ranksep: RANK_GAP, marginx: MARGIN, marginy: MARGIN });
  for (const node of nodes) {
    const size = sizeOf(node);
    graph.setNode(node.id, { width: size.width, height: size.height });
  }
  for (const edge of edges) graph.setEdge(edge.source, edge.target);
  dagre.layout(graph);

  const ranks = new Map<number, { node: AnyFlowNode; x: number }[]>();
  for (const node of nodes) {
    const point = graph.node(node.id);
    const key = Math.round(point.y);
    ranks.set(key, [...(ranks.get(key) ?? []), { node, x: point.x }]);
  }
  const centre = (graph.graph().width ?? 0) / 2;

  const placed: AnyFlowNode[] = [];
  let cursor = 0;
  for (const key of [...ranks.keys()].sort((a, b) => a - b)) {
    const members = ranks.get(key)!.sort((a, b) => a.x - b.x);
    let offset = 0;
    const sizes = rowSizes(members.length);
    sizes.forEach((count, rowIndex) => {
      const row = members.slice(offset, offset + count);
      offset += count;
      const rowHeight = Math.max(...row.map(({ node }) => sizeOf(node).height));
      const rowWidth = row.reduce((sum, { node }) => sum + sizeOf(node).width, 0) + (row.length - 1) * COLUMN_GAP;
      // Every row centres on one axis: dagre's own x spread comes from the wide rank and would
      // push the single-node ranks far to the side once that rank is wrapped.
      let left = centre - rowWidth / 2;
      for (const { node } of row) {
        const size = sizeOf(node);
        placed.push({
          ...node,
          width: size.width,
          height: size.height,
          position: { x: left, y: cursor + (rowHeight - size.height) / 2 },
        });
        left += size.width + COLUMN_GAP;
      }
      cursor += rowHeight + (rowIndex === sizes.length - 1 ? RANK_GAP : ROW_GAP);
    });
  }

  const minLeft = Math.min(...placed.map((node) => node.position.x));
  const shifted = placed.map((node) => ({
    ...node,
    position: { x: node.position.x - minLeft + MARGIN, y: node.position.y + MARGIN },
  }));
  const maxRight = Math.max(...shifted.map((node) => node.position.x + sizeOf(node).width));
  const maxBottom = Math.max(...shifted.map((node) => node.position.y + sizeOf(node).height));
  // Restore the input order so memoised consumers keep stable node indexes.
  const order = new Map(shifted.map((node) => [node.id, node]));
  return {
    nodes: nodes.map((node) => order.get(node.id)!),
    width: maxRight + MARGIN,
    height: maxBottom + MARGIN,
  };
}

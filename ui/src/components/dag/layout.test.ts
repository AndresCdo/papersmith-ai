import { describe, expect, it } from 'vitest';
import type { Edge, Node } from '@xyflow/react';
import { NODE_SIZE, layoutGraph, MAX_PER_ROW } from './layout';

function pipeline(sectionCount: number, gateCount = 0) {
  const stage = (id: string): Node => ({ id: `stage:${id}`, type: 'stage', position: { x: 0, y: 0 }, data: {} });
  const nodes: Node[] = ['ingestion', 'deliberation', 'drafting', 'auditing', 'publishing'].map(stage);
  const edges: Edge[] = [
    ['ingestion', 'deliberation'],
    ['deliberation', 'drafting'],
    ['auditing', 'publishing'],
  ].map(([a, b]) => ({ id: `stage:${a}->stage:${b}`, source: `stage:${a}`, target: `stage:${b}` }));
  for (let index = 0; index < sectionCount; index += 1) {
    const id = `section:s${index}`;
    nodes.push({ id, type: 'section', position: { x: 0, y: 0 }, data: {} });
    edges.push({ id: `stage:drafting->${id}`, source: 'stage:drafting', target: id });
    edges.push({ id: `${id}->stage:auditing`, source: id, target: 'stage:auditing' });
  }
  for (let index = 0; index < gateCount; index += 1) {
    const id = `gate:g${index}`;
    nodes.push({ id, type: 'gate', position: { x: 0, y: 0 }, data: {} });
    edges.push({ id: `stage:drafting->${id}`, source: 'stage:drafting', target: id });
    edges.push({ id: `${id}->stage:auditing`, source: id, target: 'stage:auditing' });
  }
  return { nodes, edges };
}

function rect(node: Node) {
  const size = NODE_SIZE[node.type ?? 'stage'];
  return { left: node.position.x, top: node.position.y, right: node.position.x + size.width, bottom: node.position.y + size.height };
}

describe('layoutGraph', () => {
  it('wraps a wide rank of sections and gates into several rows', () => {
    const { nodes, edges } = pipeline(10, 4);
    const result = layoutGraph(nodes, edges);
    const rows = new Map<number, number>();
    for (const node of result.nodes) rows.set(node.position.y, (rows.get(node.position.y) ?? 0) + 1);
    expect(Math.max(...rows.values())).toBeLessThanOrEqual(MAX_PER_ROW);
    // 14 nodes in the middle rank need at least ceil(14 / MAX_PER_ROW) rows.
    const middle = result.nodes.filter((node) => node.type !== 'stage');
    expect(new Set(middle.map((node) => node.position.y)).size).toBeGreaterThanOrEqual(Math.ceil(14 / MAX_PER_ROW));
  });

  it('keeps the graph narrow enough to stay legible at laptop widths', () => {
    const { nodes, edges } = pipeline(10, 4);
    const result = layoutGraph(nodes, edges);
    const widest = MAX_PER_ROW * NODE_SIZE.section.width + (MAX_PER_ROW + 1) * 60;
    expect(result.width).toBeLessThanOrEqual(widest);
  });

  it('never overlaps two nodes and keeps every node inside the reported bounds', () => {
    const { nodes, edges } = pipeline(10, 4);
    const result = layoutGraph(nodes, edges);
    const rects = result.nodes.map(rect);
    for (const box of rects) {
      expect(box.left).toBeGreaterThanOrEqual(0);
      expect(box.top).toBeGreaterThanOrEqual(0);
      expect(box.right).toBeLessThanOrEqual(result.width);
      expect(box.bottom).toBeLessThanOrEqual(result.height);
    }
    for (let a = 0; a < rects.length; a += 1) {
      for (let b = a + 1; b < rects.length; b += 1) {
        const separate =
          rects[a].right <= rects[b].left ||
          rects[b].right <= rects[a].left ||
          rects[a].bottom <= rects[b].top ||
          rects[b].bottom <= rects[a].top;
        expect(separate, `${result.nodes[a].id} vs ${result.nodes[b].id}`).toBe(true);
      }
    }
  });

  it('keeps the chain order top to bottom', () => {
    const { nodes, edges } = pipeline(10, 4);
    const byId = new Map(layoutGraph(nodes, edges).nodes.map((node) => [node.id, node]));
    const y = (id: string) => byId.get(id)!.position.y;
    expect(y('stage:ingestion')).toBeLessThan(y('stage:deliberation'));
    expect(y('stage:deliberation')).toBeLessThan(y('stage:drafting'));
    expect(y('stage:drafting')).toBeLessThan(y('section:s0'));
    expect(y('section:s9')).toBeLessThan(y('stage:auditing'));
    expect(y('stage:auditing')).toBeLessThan(y('stage:publishing'));
  });

  it('returns empty bounds for an empty graph', () => {
    expect(layoutGraph([], [])).toEqual({ nodes: [], width: 0, height: 0 });
  });
});

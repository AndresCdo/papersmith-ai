import { describe, expect, it, vi } from 'vitest';
import { buildGraph, graphSignature, relationKind } from './graph';
import * as layoutModule from './layout';
import type { WorkspaceState } from '../../types';

// Wrap the real layout so every test still lays out for real while calls are countable.
vi.mock('./layout', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./layout')>();
  return { ...actual, layoutGraph: vi.fn(actual.layoutGraph) };
});

const state: WorkspaceState = {
  pipeline_stages: [
    { id: 'ingestion' },
    { id: 'deliberation' },
    { id: 'drafting' },
    { id: 'auditing' },
    { id: 'publishing' },
  ],
  gates: [{ id: 'writing-readiness', name: 'Writing readiness', state: 'BLOCKED', reasons: ['x'] }],
  sections: [{ id: 'Related Work', section: 'Related Work' }],
};

describe('relationKind', () => {
  it('derives the relation from the id prefixes', () => {
    expect(relationKind('stage:a', 'stage:b')).toBe('next stage');
    expect(relationKind('stage:a', 'gate:b')).toBe('gate input');
    expect(relationKind('gate:a', 'stage:b')).toBe('gate releases');
    expect(relationKind('stage:a', 'section:b')).toBe('drafts');
    expect(relationKind('section:a', 'stage:b')).toBe('audited by');
  });

  it('maps unknown prefixes to related', () => {
    expect(relationKind('foo:a', 'stage:b')).toBe('related');
    expect(relationKind('gate:a', 'section:b')).toBe('related');
  });
});

describe('buildGraph', () => {
  const graph = buildGraph(state);
  const edge = (id: string) => graph.edges.find((entry) => entry.id === id);

  it('ids nodes as <kind>:<raw id>', () => {
    expect(graph.nodes.map((node) => node.id).sort()).toEqual(
      ['gate:writing-readiness', 'section:Related Work', 'stage:auditing', 'stage:deliberation', 'stage:drafting', 'stage:ingestion', 'stage:publishing'].sort(),
    );
  });

  it('ids edges as source->target and tags the relation kind', () => {
    expect(edge('stage:ingestion->stage:deliberation')?.data?.relation).toBe('next stage');
    expect(edge('stage:deliberation->gate:writing-readiness')?.data?.relation).toBe('gate input');
    expect(edge('gate:writing-readiness->stage:auditing')?.data?.relation).toBe('gate releases');
    expect(edge('stage:drafting->section:Related Work')?.data?.relation).toBe('drafts');
    expect(edge('section:Related Work->stage:auditing')?.data?.relation).toBe('audited by');
  });

  it('returns an empty graph for a null state', () => {
    expect(buildGraph(null).nodes).toEqual([]);
  });
});

describe('buildGraph layout memoisation', () => {
  const layout = vi.mocked(layoutModule.layoutGraph);
  const frame = (patch: Partial<WorkspaceState> = {}): WorkspaceState => ({ ...state, ...patch });

  it('lays out once across two frames with the same structure and keeps positions', () => {
    layout.mockClear();
    const first = buildGraph(frame({ sections: [{ id: 'Zeta Layout', section: 'Zeta Layout' }] }));
    const second = buildGraph(
      frame({ sections: [{ id: 'Zeta Layout', section: 'Zeta Layout', status: 'DRAFTING', word_count: 40 }] }),
    );
    expect(layout).toHaveBeenCalledTimes(1);
    expect(second.nodes.map((node) => node.position)).toEqual(first.nodes.map((node) => node.position));
    expect(second.width).toBe(first.width);
    expect(second.nodes.find((node) => node.id === 'section:Zeta Layout')?.data.status).toBe('DRAFTING');
  });

  it('recomputes when a node appears', () => {
    buildGraph(frame());
    layout.mockClear();
    buildGraph(frame({ sections: [...(state.sections ?? []), { id: 'Method', section: 'Method' }] }));
    expect(layout).toHaveBeenCalledTimes(1);
  });

  it('signs a different structure when only an edge changes', () => {
    const nodes = buildGraph(frame()).nodes;
    const edge = (id: string, source: string, target: string) => ({ id, source, target });
    const base = [edge('a->b', 'stage:ingestion', 'stage:drafting')];
    const rewired = [edge('a->c', 'stage:ingestion', 'stage:auditing')];
    expect(graphSignature(nodes, base)).toBe(graphSignature(nodes, [...base]));
    expect(graphSignature(nodes, rewired)).not.toBe(graphSignature(nodes, base));
  });
});

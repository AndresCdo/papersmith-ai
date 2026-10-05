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
  pipeline_stages: [{ id: 'proposal' }, { id: 'writing' }, { id: 'audit' }],
  pipeline_chain: [{ from: 'proposal', to: 'writing', label: 'rNN revision' }],
  gate_links: { 'writing-readiness': { from: 'proposal', label: 'contracts', consumed_by: 'audit' } },
  gates: [{ id: 'writing-readiness', name: 'Writing readiness', state: 'BLOCKED', reasons: ['x'] }],
  sections: [{ id: 'Related Work', section: 'Related Work' }],
};

describe('relationKind', () => {
  it('derives the relation from the id prefixes', () => {
    expect(relationKind('stage:a', 'stage:b')).toBe('next stage');
    expect(relationKind('stage:a', 'gate:b')).toBe('gate input');
    expect(relationKind('gate:a', 'stage:b')).toBe('gate releases');
    expect(relationKind('section:a', 'section:b')).toBe('next section');
  });

  it('maps unknown prefixes to related', () => {
    expect(relationKind('foo:a', 'stage:b')).toBe('related');
    expect(relationKind('gate:a', 'section:b')).toBe('related');
  });
});

describe('buildGraph', () => {
  const graph = buildGraph(state);
  const edge = (id: string) => graph.edges.find((entry) => entry.id === id);

  it('ids nodes as <kind>:<raw id>, and the general flow carries no section', () => {
    expect(graph.nodes.map((node) => node.id).sort()).toEqual(
      ['gate:writing-readiness', 'stage:audit', 'stage:proposal', 'stage:writing'].sort(),
    );
  });

  it('ids edges as source->target and tags the relation kind', () => {
    expect(edge('stage:proposal->stage:writing')?.data?.relation).toBe('next stage');
    expect(edge('stage:proposal->gate:writing-readiness')?.data?.relation).toBe('gate input');
    expect(edge('gate:writing-readiness->stage:audit')?.data?.relation).toBe('gate releases');
  });

  it('draws the chain the payload carries, not one of its own', () => {
    const rewired = buildGraph({ ...state, pipeline_chain: [{ from: 'writing', to: 'audit' }] });

    expect(rewired.edges.map((entry) => entry.id)).not.toContain('stage:proposal->stage:writing');
    expect(rewired.edges.map((entry) => entry.id)).toContain('stage:writing->stage:audit');
  });

  it('drops a chain edge whose endpoint the stage list does not carry', () => {
    const ghost = buildGraph({ ...state, pipeline_chain: [{ from: 'ghost', to: 'writing' }] });

    expect(ghost.edges.map((entry) => entry.id)).not.toContain('stage:ghost->stage:writing');
    expect(ghost.nodes.map((node) => node.id)).not.toContain('stage:ghost');
  });

  it('returns an empty graph for a null state', () => {
    expect(buildGraph(null).nodes).toEqual([]);
  });
});

describe('buildGraph writing flow', () => {
  const sections = [
    { id: '01-materials-and-methods', section: 'Materials and methods' },
    { id: '02-experimental-setup', section: 'Experimental setup' },
    { id: '03-results-and-discussion', section: 'Results' },
  ];

  it('carries only the sections, chained in the order the payload gives them', () => {
    const graph = buildGraph({ ...state, sections }, 'writing');

    expect(graph.nodes.map((node) => node.id)).toEqual([
      'section:01-materials-and-methods',
      'section:02-experimental-setup',
      'section:03-results-and-discussion',
    ]);
    expect(graph.edges.map((entry) => entry.id)).toEqual([
      'section:01-materials-and-methods->section:02-experimental-setup',
      'section:02-experimental-setup->section:03-results-and-discussion',
    ]);
    expect(graph.edges.every((entry) => entry.data?.relation === 'next section')).toBe(true);
  });

  it('does not draw the general flow in the same canvas', () => {
    const graph = buildGraph({ ...state, sections }, 'writing');

    expect(graph.nodes.some((node) => node.id.startsWith('stage:'))).toBe(false);
    expect(graph.nodes.some((node) => node.id.startsWith('gate:'))).toBe(false);
  });

  it('is empty, not wrong, when the workspace has no sections', () => {
    expect(buildGraph({ ...state, sections: [] }, 'writing').nodes).toEqual([]);
  });
});

describe('buildGraph layout memoisation', () => {
  const layout = vi.mocked(layoutModule.layoutGraph);
  const frame = (patch: Partial<WorkspaceState> = {}): WorkspaceState => ({ ...state, ...patch });

  it('lays out once across two frames with the same structure and keeps positions', () => {
    layout.mockClear();
    const first = buildGraph(frame({ sections: [{ id: 'Zeta Layout', section: 'Zeta Layout' }] }), 'writing');
    const second = buildGraph(
      frame({ sections: [{ id: 'Zeta Layout', section: 'Zeta Layout', status: 'DRAFTING', word_count: 40 }] }),
      'writing',
    );
    expect(layout).toHaveBeenCalledTimes(1);
    expect(second.nodes.map((node) => node.position)).toEqual(first.nodes.map((node) => node.position));
    expect(second.width).toBe(first.width);
    expect(second.nodes.find((node) => node.id === 'section:Zeta Layout')?.data.status).toBe('DRAFTING');
  });

  it('recomputes when a node appears', () => {
    buildGraph(frame(), 'writing');
    layout.mockClear();
    buildGraph(frame({ sections: [...(state.sections ?? []), { id: 'Method', section: 'Method' }] }), 'writing');
    expect(layout).toHaveBeenCalledTimes(1);
  });

  it('signs a different structure when only an edge changes', () => {
    const nodes = buildGraph(frame()).nodes;
    const edge = (id: string, source: string, target: string) => ({ id, source, target });
    const base = [edge('a->b', 'stage:proposal', 'stage:writing')];
    const rewired = [edge('a->c', 'stage:proposal', 'stage:audit')];
    expect(graphSignature(nodes, base)).toBe(graphSignature(nodes, [...base]));
    expect(graphSignature(nodes, rewired)).not.toBe(graphSignature(nodes, base));
  });
});

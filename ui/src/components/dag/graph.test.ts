import { describe, expect, it } from 'vitest';
import { buildGraph, relationKind } from './graph';
import type { WorkspaceState } from '../../types';

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

import type { Edge, Node } from '@xyflow/react';
import type { StageNodeData } from './nodes/StageNode';
import type { GateNodeData } from './nodes/GateNode';
import type { SectionNodeData } from './nodes/SectionNode';
import { NODE_SIZE, layoutGraph, type GraphLayout } from './layout';
import type { Gate, PipelineStage, Section, WorkspaceState } from '../../types';
import { formatCount } from '../../lib/format';

/** `ingestion -> deliberation`, guarded by presence on both ends. */
const STAGE_CHAIN: readonly (readonly [string, string])[] = [
  ['ingestion', 'deliberation'],
  ['deliberation', 'drafting'],
  ['experiments', 'drafting'],
  ['drafting', 'auditing'],
  ['auditing', 'publishing'],
];

/** Which stage each gate inspects, with the `parts` key that explains the link. */
const GATE_SOURCES: Record<string, { from: string; label: string }> = {
  'writing-readiness': { from: 'deliberation', label: 'contracts' },
  'coupling-verification': { from: 'drafting', label: 'facts' },
  'grounding-style-leak': { from: 'drafting', label: 'citations' },
  'diagram-raster': { from: 'experiments', label: 'figures' },
};

export type AnyFlowNode = Node<Record<string, unknown>>;

function stageIsMutating(stage: PipelineStage): boolean {
  if (stage.active !== true) return false;
  return typeof stage.progress === 'number' ? stage.progress < 1 : true;
}

function sectionIsMutating(section: Section): boolean {
  if (section.status === 'DRAFTING') return true;
  const total = section.blocks_total ?? 0;
  const written = section.blocks_written ?? 0;
  return total > 0 && written > 0 && written < total && section.status !== 'SEALED';
}

function gateIsMutating(gate: Gate): boolean {
  return gate.state === 'VERIFYING';
}

/** Render a `gate.parts` entry as a compact `key: value` chip. */
function summarizeParts(gate: Gate): { key: string; value: string }[] {
  const parts = gate.parts;
  if (!parts || typeof parts !== 'object') return [];
  return Object.entries(parts)
    .slice(0, 4)
    .map(([key, value]) => {
      if (Array.isArray(value)) return { key, value: formatCount(value.length) };
      if (typeof value === 'number' || typeof value === 'boolean') return { key, value: String(value) };
      return null;
    })
    .filter((entry): entry is { key: string; value: string } => entry !== null);
}

const kindOf = (id: string): string => id.slice(0, id.indexOf(':'));

/** Human label for an edge, derived from the `<kind>:` prefixes of its ends. */
export function relationKind(source: string, target: string): string {
  const pair = `${kindOf(source)}->${kindOf(target)}`;
  switch (pair) {
    case 'stage->stage':
      return 'next stage';
    case 'stage->gate':
      return 'gate input';
    case 'gate->stage':
      return 'gate releases';
    case 'stage->section':
      return 'drafts';
    case 'section->stage':
      return 'audited by';
    default:
      return 'related';
  }
}

export interface GraphModel {
  nodes: AnyFlowNode[];
  edges: Edge[];
  width: number;
  height: number;
}

/**
 * Everything dagre's result depends on: node ids, their kind (which fixes the
 * dimensions in NODE_SIZE) and edge endpoints. Node data (progress, status text)
 * is deliberately absent, so ordinary state frames reuse the previous positions.
 */
export function graphSignature(nodes: AnyFlowNode[], edges: Edge[]): string {
  const dims = (node: AnyFlowNode) => {
    const size = NODE_SIZE[node.type ?? 'stage'] ?? NODE_SIZE.stage;
    return `${node.id}@${size.width}x${size.height}`;
  };
  return JSON.stringify([nodes.map(dims), edges.map((edge) => `${edge.id}:${edge.source}>${edge.target}`)]);
}

// One live pipeline is on screen at a time, so a single remembered layout is enough.
let lastLayout: { signature: string; laid: GraphLayout } | null = null;

function layoutOnStructure(nodes: AnyFlowNode[], edges: Edge[]): GraphLayout {
  const signature = graphSignature(nodes, edges);
  if (lastLayout?.signature !== signature) {
    lastLayout = { signature, laid: layoutGraph(nodes, edges) };
    return lastLayout.laid;
  }
  // Same structure: keep the computed geometry, carry over this frame's fresh node data.
  const placed = new Map(lastLayout.laid.nodes.map((node) => [node.id, node]));
  return {
    ...lastLayout.laid,
    nodes: nodes.map((node) => {
      const { position, width, height } = placed.get(node.id)!;
      return { ...node, position, width, height };
    }),
  };
}

export function buildGraph(state: WorkspaceState | null): GraphModel {
  const stages = state?.pipeline_stages ?? [];
  const gates = state?.gates ?? [];
  const sections = state?.sections ?? [];

  const nodes: AnyFlowNode[] = [];
  const edges: Edge[] = [];
  const mutatingNodes = new Set<string>();
  const stageIds = new Set(stages.map((stage) => stage.id));

  for (const stage of stages) {
    const mutating = stageIsMutating(stage);
    if (mutating) mutatingNodes.add(`stage:${stage.id}`);
    const data: StageNodeData = {
      title: stage.title ?? stage.id,
      active: stage.active === true,
      progress: typeof stage.progress === 'number' ? stage.progress : 0,
      detail: stage.detail ?? '',
      workers: stage.workers ?? [],
      mutating,
    };
    nodes.push({ id: `stage:${stage.id}`, type: 'stage', position: { x: 0, y: 0 }, data, draggable: false });
  }

  for (const gate of gates) {
    const mutating = gateIsMutating(gate);
    if (mutating) mutatingNodes.add(`gate:${gate.id}`);
    const data: GateNodeData = {
      name: gate.name ?? gate.id,
      state: gate.state ?? 'UNKNOWN',
      reasons: gate.reasons ?? [],
      parts: summarizeParts(gate),
      mutating,
    };
    nodes.push({ id: `gate:${gate.id}`, type: 'gate', position: { x: 0, y: 0 }, data, draggable: false });
  }

  for (const section of sections) {
    const mutating = sectionIsMutating(section);
    if (mutating) mutatingNodes.add(`section:${section.id}`);
    const data: SectionNodeData = {
      label: section.section ?? section.id,
      status: section.status ?? 'UNKNOWN',
      wordCount: section.word_count ?? 0,
      maxWords: section.extent?.max_words ?? null,
      blocksWritten: section.blocks_written ?? 0,
      blocksTotal: section.blocks_total ?? 0,
      placeholders: section.citations?.placeholders ?? 0,
      mutating,
    };
    nodes.push({ id: `section:${section.id}`, type: 'section', position: { x: 0, y: 0 }, data, draggable: false });
  }

  const link = (source: string, target: string, label?: string) => {
    const animated = mutatingNodes.has(source) || mutatingNodes.has(target);
    edges.push({
      id: `${source}->${target}`,
      source,
      target,
      type: 'animated',
      animated,
      label,
      data: { animated, relation: relationKind(source, target) },
    });
  };

  for (const [from, to] of STAGE_CHAIN) {
    if (stageIds.has(from) && stageIds.has(to)) link(`stage:${from}`, `stage:${to}`);
  }

  // Figure obligations are declared by section contracts; the diagram gate is
  // reachable only when the figure pipeline has an `experiments` stage to feed it.
  for (const gate of gates) {
    const source = GATE_SOURCES[gate.id]?.from ?? 'auditing';
    const label = GATE_SOURCES[gate.id]?.label;
    if (stageIds.has(source)) link(`stage:${source}`, `gate:${gate.id}`, label);
    if (stageIds.has('auditing')) link(`gate:${gate.id}`, 'stage:auditing');
    else if (stageIds.has('publishing')) link(`gate:${gate.id}`, 'stage:publishing');
  }

  for (const section of sections) {
    if (stageIds.has('drafting')) link('stage:drafting', `section:${section.id}`);
    if (stageIds.has('auditing')) link(`section:${section.id}`, 'stage:auditing');
  }

  const laid = layoutOnStructure(nodes, edges);
  return { nodes: laid.nodes, edges, width: laid.width, height: laid.height };
}

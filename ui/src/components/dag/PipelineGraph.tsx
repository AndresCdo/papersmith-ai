import { useMemo } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  Panel,
  ReactFlow,
  type Edge,
  type Node,
  type NodeTypes,
  type EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode, { type StageNodeData } from './nodes/StageNode';
import GateNode, { type GateNodeData } from './nodes/GateNode';
import SectionNode, { type SectionNodeData } from './nodes/SectionNode';
import AnimatedEdge from './edges/AnimatedEdge';
import { layoutGraph } from './layout';
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

type AnyFlowNode = Node<Record<string, unknown>>;

const nodeTypes = {
  stage: StageNode,
  gate: GateNode,
  section: SectionNode,
} satisfies NodeTypes;

const edgeTypes = {
  animated: AnimatedEdge,
} satisfies EdgeTypes;

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

function buildGraph(state: WorkspaceState | null): { nodes: AnyFlowNode[]; edges: Edge[]; width: number; height: number } {
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
      data: { animated },
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

  const laid = layoutGraph(nodes, edges);
  return { nodes: laid.nodes, edges, width: laid.width, height: laid.height };
}

/**
 * The pipeline DAG: six stages in a top-to-bottom chain, the four quality gates
 * hanging off the stage they inspect, and every section placed between
 * `drafting` and `auditing`. Edges animate while either endpoint is mutating.
 */
export default function PipelineGraph({ state }: { state: WorkspaceState | null }) {
  const { nodes, edges, width, height } = useMemo(() => buildGraph(state), [state]);

  if (nodes.length === 0) {
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
        elementsSelectable={false}
        edgesFocusable={false}
        nodesFocusable={false}
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

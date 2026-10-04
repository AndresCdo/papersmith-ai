// jsdom never lays out SVG handles, so React Flow renders no edges here. The
// edge paths are therefore verified in a real browser by the visual checker
// (--click-check); this file stands in for React Flow and calls the handler
// props PipelineGraph passes to it, covering the edge and batching logic.
import { act, render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { buildGraph } from './graph';
import { diagramState } from './fixtures';

type Props = Record<string, unknown> & {
  onNodesChange: (changes: unknown[]) => void;
  onEdgesChange: (changes: unknown[]) => void;
  onEdgeClick: (event: unknown, edge: { id: string }) => void;
  onNodeClick: (event: unknown, node: { id: string }) => void;
  onPaneClick: () => void;
};

const captured: { props: Props | null } = { props: null };

vi.mock('@xyflow/react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@xyflow/react')>();
  return {
    ...actual,
    ReactFlow: (props: Props) => {
      captured.props = props;
      return null;
    },
  };
});

const { default: PipelineGraph } = await import('./PipelineGraph');
const graph = buildGraph(diagramState);
const EDGE = 'stage:drafting->stage:auditing';

const select = (id: string, selected: boolean) => ({ type: 'select', id, selected });
const flush = () => act(async () => { await Promise.resolve(); });

describe('PipelineGraph handler props', () => {
  const onSelect = vi.fn();
  beforeEach(() => {
    onSelect.mockClear();
  });

  const mount = (selectedId: string | null) =>
    render(<PipelineGraph graph={graph} selectedId={selectedId} onSelect={onSelect} />);

  it('turns off multi-selection, box selection and deletion, and dragging', () => {
    mount(null);
    expect(captured.props).toMatchObject({
      multiSelectionKeyCode: null,
      selectionKeyCode: null,
      deleteKeyCode: null,
      nodesDraggable: false,
      elementsSelectable: true,
    });
  });

  it('selects an edge on click', () => {
    mount(null);
    captured.props?.onEdgeClick({}, { id: EDGE });
    expect(onSelect).toHaveBeenLastCalledWith(EDGE);
  });

  it('maps the selection onto copies without touching the layout objects', () => {
    mount(EDGE);
    const edges = captured.props?.edges as { id: string; selected: boolean }[];
    expect(edges.find((edge) => edge.id === EDGE)?.selected).toBe(true);
    expect(graph.edges.find((edge) => edge.id === EDGE)?.selected).toBeUndefined();
  });

  it('applies an edge select change from the keyboard path', async () => {
    mount(null);
    captured.props?.onEdgesChange([select(EDGE, true)]);
    await flush();
    expect(onSelect).toHaveBeenCalledExactlyOnceWith(EDGE);
  });

  it('switches edge to node in one batch: the new selection wins over the deselect', async () => {
    mount(EDGE);
    captured.props?.onEdgesChange([select(EDGE, false)]);
    captured.props?.onNodesChange([select('stage:auditing', true)]);
    await flush();
    expect(onSelect).toHaveBeenCalledExactlyOnceWith('stage:auditing');
  });

  it('clears when the current element is deselected and nothing else is selected', async () => {
    mount(EDGE);
    captured.props?.onEdgesChange([select(EDGE, false)]);
    await flush();
    expect(onSelect).toHaveBeenCalledExactlyOnceWith(null);
  });

  it('ignores a deselect of an element that is not selected and non-select changes', async () => {
    mount(EDGE);
    captured.props?.onNodesChange([select('stage:ingestion', false), { type: 'position', id: 'stage:ingestion' }]);
    await flush();
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('clears on a pane click', () => {
    mount(EDGE);
    captured.props?.onPaneClick();
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });
});

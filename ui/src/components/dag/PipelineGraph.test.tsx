import { fireEvent, render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import PipelineGraph from './PipelineGraph';
import { buildGraph } from './graph';
import { diagramState } from './fixtures';

const graph = buildGraph(diagramState);

function renderGraph(selectedId: string | null = null) {
  const onSelect = vi.fn();
  const view = render(<PipelineGraph graph={graph} selectedId={selectedId} onSelect={onSelect} />);
  return { onSelect, ...view };
}

const node = (container: HTMLElement, id: string) =>
  container.querySelector(`.react-flow__node[data-id="${id}"]`) as HTMLElement;

describe('PipelineGraph selection', () => {
  it('renders nodes as focusable, selectable wrappers', async () => {
    const { container } = renderGraph();
    const wrapper = await vi.waitFor(() => {
      const found = node(container, 'stage:writing');
      expect(found).toBeTruthy();
      return found;
    });
    expect(wrapper).toHaveAttribute('tabindex', '0');
  });

  it('selects a node on click', async () => {
    const { container, onSelect } = renderGraph();
    // fireEvent, not user-event: user-event's mousedown carries a null `view`, which d3-zoom
    // (React Flow's pan handler) cannot take in jsdom.
    fireEvent.click(node(container, 'gate:writing-readiness'));
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith('gate:writing-readiness'));
  });

  it('marks the selected node and keeps non-selected nodes plain', () => {
    const { container } = renderGraph('stage:writing');
    expect(node(container, 'stage:writing')).toHaveClass('selected');
    expect(node(container, 'stage:audit')).not.toHaveClass('selected');
  });

  it('selects the focused node with Enter (React Flow keyboard handler)', async () => {
    const { container, onSelect } = renderGraph();
    const wrapper = node(container, 'stage:writing');
    wrapper.focus();
    await userEvent.keyboard('{Enter}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith('stage:writing'));
  });

  it('switches the selection when another node is focused and activated', async () => {
    const { container, onSelect } = renderGraph('stage:writing');
    node(container, 'stage:audit').focus();
    await userEvent.keyboard('{Enter}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith('stage:audit'));
  });

  it('clears the selection with Escape on the selected node', async () => {
    const { container, onSelect } = renderGraph('stage:writing');
    node(container, 'stage:writing').focus();
    await userEvent.keyboard('{Escape}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith(null));
  });

  it('clears the selection on a pane click', async () => {
    const { container, onSelect } = renderGraph('stage:writing');
    fireEvent.click(container.querySelector('.react-flow__pane') as HTMLElement);
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith(null));
  });

  it('does not offer dragging or deletion', () => {
    const { container, onSelect } = renderGraph('stage:writing');
    const wrapper = node(container, 'stage:writing');
    wrapper.focus();
    fireEvent.keyDown(wrapper, { key: 'Delete' });
    fireEvent.keyDown(wrapper, { key: 'Backspace' });
    expect(onSelect).not.toHaveBeenCalled();
    expect(container.querySelector('.react-flow__node.draggable')).toBeNull();
  });
});

describe('PipelineGraph across state frames', () => {
  it('keeps the selection mapped when a later frame reuses the layout', () => {
    const onSelect = vi.fn();
    const { container, rerender } = render(<PipelineGraph graph={graph} selectedId="stage:writing" onSelect={onSelect} />);
    const next = buildGraph({
      ...diagramState,
      pipeline_stages: diagramState.pipeline_stages?.map((stage) => ({ ...stage, detail: 'updated' })),
    });
    expect(next.nodes.map((n) => n.position)).toEqual(graph.nodes.map((n) => n.position));
    rerender(<PipelineGraph graph={next} selectedId="stage:writing" onSelect={onSelect} />);
    expect(node(container, 'stage:writing')).toHaveClass('selected');
    expect(node(container, 'stage:audit')).not.toHaveClass('selected');
  });
});

describe('PipelineGraph writing flow', () => {
  const writingGraph = buildGraph(diagramState, 'writing');

  it('draws the sections and says which flow this is', async () => {
    const { container } = render(
      <PipelineGraph flow="writing" graph={writingGraph} selectedId={null} onSelect={vi.fn()} />,
    );

    const section = await vi.waitFor(() => {
      const found = node(container, 'section:Related Work');
      expect(found).toBeTruthy();
      return found;
    });

    expect(section).toHaveAttribute('tabindex', '0');
    expect(container.querySelector('.graph-legend__title')).toHaveTextContent('Writing flow');
    expect(container.querySelector('.react-flow__node[data-id="stage:writing"]')).toBeNull();
  });

  it('names an empty canvas after the flow it is waiting on', () => {
    const empty = buildGraph({ ...diagramState, sections: [] }, 'writing');
    const { getByRole } = render(
      <PipelineGraph flow="writing" graph={empty} selectedId={null} onSelect={vi.fn()} />,
    );

    expect(getByRole('heading', { name: 'Writing' })).toBeInTheDocument();
  });
});

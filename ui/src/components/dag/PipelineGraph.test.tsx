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
      const found = node(container, 'stage:drafting');
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
    const { container } = renderGraph('stage:drafting');
    expect(node(container, 'stage:drafting')).toHaveClass('selected');
    expect(node(container, 'stage:auditing')).not.toHaveClass('selected');
  });

  it('selects the focused node with Enter (React Flow keyboard handler)', async () => {
    const { container, onSelect } = renderGraph();
    const wrapper = node(container, 'section:Related Work');
    wrapper.focus();
    await userEvent.keyboard('{Enter}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith('section:Related Work'));
  });

  it('switches the selection when another node is focused and activated', async () => {
    const { container, onSelect } = renderGraph('stage:drafting');
    node(container, 'stage:auditing').focus();
    await userEvent.keyboard('{Enter}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith('stage:auditing'));
  });

  it('clears the selection with Escape on the selected node', async () => {
    const { container, onSelect } = renderGraph('stage:drafting');
    node(container, 'stage:drafting').focus();
    await userEvent.keyboard('{Escape}');
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith(null));
  });

  it('clears the selection on a pane click', async () => {
    const { container, onSelect } = renderGraph('stage:drafting');
    fireEvent.click(container.querySelector('.react-flow__pane') as HTMLElement);
    await vi.waitFor(() => expect(onSelect).toHaveBeenLastCalledWith(null));
  });

  it('does not offer dragging or deletion', () => {
    const { container, onSelect } = renderGraph('stage:drafting');
    const wrapper = node(container, 'stage:drafting');
    wrapper.focus();
    fireEvent.keyDown(wrapper, { key: 'Delete' });
    fireEvent.keyDown(wrapper, { key: 'Backspace' });
    expect(onSelect).not.toHaveBeenCalled();
    expect(container.querySelector('.react-flow__node.draggable')).toBeNull();
  });
});

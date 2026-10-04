import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ElementDetailPanel from './ElementDetailPanel';
import { buildGraph } from './graph';
import { diagramState } from './fixtures';
import type { HistoryEntry } from '../../types';

const graph = buildGraph(diagramState);

function entry(seq: number, element: string | null, summary: string): HistoryEntry {
  return { id: `b-${seq}`, boot_id: 'b', seq, ts: 1_700_000_000 + seq, kind: 'stage', element_id: element, summary, before: null, after: null };
}

function open(elementId: string, entries: HistoryEntry[] = []) {
  const onSelect = vi.fn();
  render(
    <ElementDetailPanel
      elementId={elementId}
      state={diagramState}
      graph={graph}
      history={{ bootId: 'b', entries, gap: false }}
      onSelect={onSelect}
    />,
  );
  return { onSelect, panel: screen.getByTestId('element-detail-panel') };
}

describe('ElementDetailPanel', () => {
  it('shows the real fields of a stage and its linked gates and sections', () => {
    const { panel } = open('stage:drafting');
    expect(within(panel).getByRole('heading', { name: 'Drafting' })).toBeInTheDocument();
    expect(panel).toHaveTextContent('writing blocks');
    expect(panel).toHaveTextContent('40%');
    expect(panel).toHaveTextContent('redactor');
    expect(panel).toHaveTextContent('active');
    expect(within(panel).getByRole('button', { name: /Related Work/ })).toBeInTheDocument();
    expect(within(panel).getByRole('button', { name: /Coupling verification/ })).toBeInTheDocument();
  });

  it('shows the state, reasons and source stages of a gate', () => {
    const { panel } = open('gate:writing-readiness');
    expect(within(panel).getByRole('heading', { name: 'Writing readiness' })).toBeInTheDocument();
    expect(panel).toHaveTextContent('BLOCKED');
    expect(panel).toHaveTextContent('contract missing');
    expect(panel).toHaveTextContent('no extent');
    expect(within(panel).getByRole('button', { name: /Deliberation/ })).toBeInTheDocument();
  });

  it('reuses SectionDetail for a section', () => {
    const { panel } = open('section:Related Work');
    expect(within(panel).getByRole('heading', { name: 'Related Work' })).toBeInTheDocument();
    expect(panel).toHaveTextContent('paper/sections/related.md');
    expect(panel).toHaveTextContent('smith2020');
  });

  it('shows source, target and relation kind of an edge', () => {
    const { panel } = open('stage:deliberation->gate:writing-readiness');
    expect(panel).toHaveTextContent('gate input');
    expect(within(panel).getByRole('button', { name: /Deliberation/ })).toBeInTheDocument();
    expect(within(panel).getByRole('button', { name: /Writing readiness/ })).toBeInTheDocument();
  });

  it('selects a neighbour from the Connections list', async () => {
    const { panel, onSelect } = open('stage:drafting');
    await userEvent.click(within(panel).getByRole('button', { name: /Related Work/ }));
    expect(onSelect).toHaveBeenLastCalledWith('section:Related Work');
  });

  it('says "No longer present" for a vanished element', () => {
    const { panel } = open('section:Gone');
    expect(panel).toHaveTextContent('No longer present');
    expect(panel).toHaveTextContent('section:Gone');
  });

  it('closes with Escape and with the close button', async () => {
    const { onSelect } = open('stage:drafting');
    await userEvent.keyboard('{Escape}');
    expect(onSelect).toHaveBeenLastCalledWith(null);
    onSelect.mockClear();
    await userEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });

  it('moves focus into the panel and restores it on unmount', () => {
    const trigger = document.createElement('button');
    document.body.appendChild(trigger);
    trigger.focus();
    const { unmount } = render(
      <ElementDetailPanel elementId="stage:drafting" state={diagramState} graph={graph} history={{ bootId: null, entries: [], gap: false }} onSelect={() => {}} />,
    );
    expect(screen.getByTestId('element-detail-panel').contains(document.activeElement)).toBe(true);
    unmount();
    expect(document.activeElement).toBe(trigger);
    trigger.remove();
  });

  it('lists only the history entries of the selected element, newest first', () => {
    const { panel } = open('stage:drafting', [
      entry(1, 'stage:drafting', 'older drafting change'),
      entry(2, 'stage:other', 'other stage change'),
      entry(3, 'stage:drafting', 'newer drafting change'),
    ]);
    const section = within(panel).getByRole('region', { name: 'History' });
    const items = within(section).getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent('newer drafting change');
    expect(within(section).queryByText('other stage change')).toBeNull();
  });

  it('says so when the selected element has no history yet', () => {
    const { panel } = open('stage:drafting');
    expect(within(panel).getByRole('region', { name: 'History' })).toHaveTextContent('No changes recorded');
  });

  it('shows a loading message instead of "No longer present" while the state is null', () => {
    render(
      <ElementDetailPanel
        elementId="stage:drafting"
        state={null}
        graph={buildGraph(null)}
        history={{ bootId: null, entries: [], gap: false }}
        onSelect={() => {}}
      />,
    );
    const panel = screen.getByTestId('element-detail-panel');
    expect(panel).toHaveTextContent(/not loaded|unavailable/i);
    expect(panel).not.toHaveTextContent('No longer present');
  });

  it('moves focus to the heading and announces the new element when the selection changes', () => {
    const props = { state: diagramState, graph, history: { bootId: 'b', entries: [], gap: false }, onSelect: () => {} };
    const { rerender } = render(<ElementDetailPanel elementId="stage:drafting" {...props} />);
    const region = screen.getByRole('status');
    expect(region).toHaveAttribute('aria-live', 'polite');
    rerender(<ElementDetailPanel elementId="stage:auditing" {...props} />);
    const heading = screen.getByRole('heading', { level: 3 });
    expect(document.activeElement).toBe(heading);
    expect(screen.getByRole('status')).toHaveTextContent(heading.textContent ?? 'missing');
  });

  it('renders duplicate gate reasons without key collisions', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    const gateState = {
      ...diagramState,
      gates: diagramState.gates?.map((gate, index) =>
        index === 0 ? { ...gate, reasons: ['same reason', 'same reason'] } : gate,
      ),
    };
    const gateId = `gate:${diagramState.gates?.[0].id}`;
    render(
      <ElementDetailPanel elementId={gateId} state={gateState} graph={buildGraph(gateState)} history={{ bootId: 'b', entries: [], gap: false }} onSelect={() => {}} />,
    );
    expect(screen.getAllByText('same reason')).toHaveLength(2);
    expect(error).not.toHaveBeenCalled();
    error.mockRestore();
  });
});

import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ElementDetailPanel from './ElementDetailPanel';
import { buildGraph } from './graph';
import { diagramState } from './fixtures';

const graph = buildGraph(diagramState);

function open(elementId: string) {
  const onSelect = vi.fn();
  render(<ElementDetailPanel elementId={elementId} state={diagramState} graph={graph} onSelect={onSelect} />);
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
      <ElementDetailPanel elementId="stage:drafting" state={diagramState} graph={graph} onSelect={() => {}} />,
    );
    expect(screen.getByTestId('element-detail-panel').contains(document.activeElement)).toBe(true);
    unmount();
    expect(document.activeElement).toBe(trigger);
    trigger.remove();
  });
});

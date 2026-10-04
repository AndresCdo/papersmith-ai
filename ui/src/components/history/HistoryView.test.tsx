import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import HistoryView from './HistoryView';
import { emptyHistory, type HistoryState } from '../../lib/history';
import type { HistoryEntry } from '../../types';

function entry(seq: number, extra: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    id: `b-${seq}`, boot_id: 'b', seq, ts: 1_700_000_000 + seq, kind: 'section_status',
    element_id: 'section:intro', summary: `Section intro status ${seq}`, before: null, after: null, ...extra,
  };
}

const present = new Set(['section:intro', 'gate:g', 'stage:drafting']);

function view(
  history: HistoryState,
  extra: { error?: string | null; onSelect?: (id: string) => void; presentIds?: ReadonlySet<string> | null } = {},
) {
  const onSelect = extra.onSelect ?? vi.fn();
  render(<HistoryView history={history} error={extra.error ?? null} presentIds={extra.presentIds === undefined ? present : extra.presentIds} onSelect={onSelect} />);
  return { onSelect };
}

const held = (entries: HistoryEntry[], gap = false): HistoryState => ({ bootId: 'b', entries, gap });

describe('HistoryView', () => {
  it('states that the history only covers the time since the dashboard started', () => {
    view(emptyHistory);
    expect(screen.getByText('History since the dashboard started')).toBeInTheDocument();
    expect(screen.getByText(/No changes recorded yet/)).toBeInTheDocument();
  });

  it('lists entries newest first', () => {
    view(held([entry(1), entry(2), entry(3)]));
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent('status 3');
    expect(items[2]).toHaveTextContent('status 1');
  });

  it('warns when earlier entries were dropped', () => {
    view(held([entry(5)], true));
    expect(screen.getByText(/Some earlier entries were dropped/)).toBeInTheDocument();
  });

  it('shows an inline message for a failed request', () => {
    view(emptyHistory, { error: 'could not load history: Error: /api/history responded 422' });
    expect(screen.getByRole('alert')).toHaveTextContent('422');
  });

  it('filters by kind', async () => {
    view(held([entry(1), entry(2, { kind: 'gate', element_id: 'gate:g', summary: 'Gate g flipped' })]));
    await userEvent.selectOptions(screen.getByLabelText('Kind'), 'gate');
    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByText('Gate g flipped')).toBeInTheDocument();
  });

  it('filters by element', async () => {
    view(held([entry(1), entry(2, { kind: 'gate', element_id: 'gate:g', summary: 'Gate g flipped' })]));
    await userEvent.selectOptions(screen.getByLabelText('Element'), 'gate:g');
    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByText('Gate g flipped')).toBeInTheDocument();
  });

  it('groups consecutive word-count entries of one section', () => {
    const words = (seq: number) => entry(seq, { kind: 'section_words', summary: `words ${seq}`, before: seq, after: seq + 1 });
    view(held([words(1), words(2), words(3)]));
    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByText(/3 word-count changes/)).toBeInTheDocument();
  });

  it('navigates to the pipeline element when a row with an element id is clicked', async () => {
    const { onSelect } = view(held([entry(1)]));
    await userEvent.click(screen.getByRole('button', { name: 'section:intro' }));
    expect(onSelect).toHaveBeenCalledWith('section:intro');
  });

  it('does not render a link for a null element id', () => {
    view(held([entry(1, { kind: 'health', element_id: null, summary: 'Wiring health: A -> B' })]));
    expect(screen.queryByRole('button', { name: /section:|gate:|stage:/ })).toBeNull();
    expect(screen.getByText('Wiring health: A -> B')).toBeInTheDocument();
  });

  it('marks a vanished element as no longer present but keeps the link', () => {
    view(held([entry(1, { element_id: 'section:gone' })]));
    const row = screen.getAllByRole('listitem')[0];
    expect(within(row).getByText('No longer present')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'section:gone' })).toBeInTheDocument();
  });

  it('does not mark rows as no longer present while the workspace state is unknown', () => {
    view(held([entry(1, { element_id: 'section:gone' })]), { presentIds: null });
    expect(screen.queryByText('No longer present')).toBeNull();
  });

  it('resets a kind filter to all when its kind is no longer among the options', async () => {
    const gate = entry(2, { kind: 'gate', element_id: 'gate:g', summary: 'Gate g flipped' });
    const { rerender } = render(
      <HistoryView history={held([entry(1), gate])} error={null} presentIds={present} onSelect={() => {}} />,
    );
    await userEvent.selectOptions(screen.getByLabelText('Kind'), 'gate');
    rerender(<HistoryView history={held([entry(3)])} error={null} presentIds={present} onSelect={() => {}} />);
    expect(screen.getByLabelText('Kind')).toHaveValue('');
    expect(screen.getByText('Section intro status 3')).toBeInTheDocument();
  });

  it('resets an element filter to all when the element is no longer among the options', async () => {
    const gate = entry(2, { kind: 'gate', element_id: 'gate:g', summary: 'Gate g flipped' });
    const { rerender } = render(
      <HistoryView history={held([entry(1), gate])} error={null} presentIds={present} onSelect={() => {}} />,
    );
    await userEvent.selectOptions(screen.getByLabelText('Element'), 'gate:g');
    rerender(<HistoryView history={held([entry(3)])} error={null} presentIds={present} onSelect={() => {}} />);
    expect(screen.getByLabelText('Element')).toHaveValue('');
    expect(screen.getByText('Section intro status 3')).toBeInTheDocument();
  });

  it('says the filter hides every row and offers Clear filters', async () => {
    view(held([entry(1), entry(2, { kind: 'gate', element_id: 'gate:g', summary: 'Gate g flipped' })]));
    await userEvent.selectOptions(screen.getByLabelText('Kind'), 'gate');
    await userEvent.selectOptions(screen.getByLabelText('Element'), 'gate:g');
    // gate:g + a kind that only matches another element hides every row
    await userEvent.selectOptions(screen.getByLabelText('Kind'), 'section_status');
    expect(screen.getByText('No changes match the current filter')).toBeInTheDocument();
    expect(screen.queryByText(/No changes recorded yet/)).toBeNull();
    await userEvent.click(screen.getByRole('button', { name: 'Clear filters' }));
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });
});

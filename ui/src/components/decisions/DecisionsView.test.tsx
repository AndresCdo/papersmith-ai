import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import DecisionsView from './DecisionsView';
import type { DecisionEvent, DecisionsPayload } from '../../types';

const event = (over: Partial<DecisionEvent> = {}): DecisionEvent => ({
  ts: '2026-03-02T10:15:30Z',
  source: 'declarations',
  kind: 'declaration',
  summary: 'Declared claim-1',
  ref: 'paper/main.tex#claim-1',
  ...over,
});

const payload = (over: Partial<DecisionsPayload> = {}): DecisionsPayload => ({
  events: [
    event(),
    event({ ts: '2026-02-01T00:00:00+00:00', source: 'remote-execution', kind: 'submitted', summary: 'Submitted run.py to w1', ref: 'implementations/r/N/.remote-execution/ledger.jsonl#1' }),
    event({ ts: null, source: 'proposal', kind: 'revision_receipt', summary: 'Revision a -> b (edit), 2 patches', ref: '.proposal-deliberation/receipts/r.json', verified: false }),
  ],
  sources: {
    declarations: { status: 'ok', count: 1, truncated: false },
    proposal: { status: 'ok', count: 1, truncated: false },
    experiment: { status: 'absent', count: 0, truncated: false },
    'remote-execution': { status: 'ok', count: 1, truncated: false },
  },
  truncated: false,
  total: 3,
  ...over,
});

function view(data: DecisionsPayload | null, extra: { loading?: boolean; error?: string | null } = {}) {
  const props = { refresh: vi.fn(), retry: vi.fn() };
  const utils = render(<DecisionsView data={data} loading={extra.loading ?? false} error={extra.error ?? null} {...props} />);
  return { ...props, ...utils };
}

describe('DecisionsView', () => {
  it('shows a loading state before the first response', () => {
    view(null, { loading: true });
    expect(screen.getByText(/Loading the decisions/)).toBeInTheDocument();
  });

  it('shows an inline error with Retry', async () => {
    const { retry } = view(null, { error: 'could not load the decisions: boom' });
    expect(screen.getByRole('alert')).toHaveTextContent('boom');
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(retry).toHaveBeenCalled();
  });

  it('refreshes on demand', async () => {
    const { refresh } = view(payload());
    await userEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it('shows the empty state when there are no events', () => {
    view(payload({ events: [], total: 0 }));
    expect(screen.getByText('No recorded decisions yet')).toBeInTheDocument();
  });

  it('lists dated events first and undated ones under an Undated heading', () => {
    view(payload());
    const dated = screen.getByRole('list', { name: 'Dated decisions' });
    const items = within(dated).getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent('2026-03-02 10:15:30 UTC');
    expect(items[1]).toHaveTextContent('2026-02-01 00:00:00 UTC');
    expect(screen.getByRole('heading', { name: 'Undated' })).toBeInTheDocument();
    expect(screen.getByText(/receipts carry no timestamp/i)).toBeInTheDocument();
    const undated = screen.getByRole('list', { name: 'Undated decisions' });
    expect(within(undated).getByText(/Revision a -> b/)).toBeInTheDocument();
  });

  it('renders source chip, kind, summary and ref per row', () => {
    view(payload());
    const row = screen.getAllByRole('listitem').find((li) => li.textContent?.includes('Declared claim-1'))!;
    expect(within(row).getByText('declarations', { selector: '.decision__source' })).toBeInTheDocument();
    expect(within(row).getByText('declaration', { selector: '.decision__kind' })).toBeInTheDocument();
    expect(within(row).getByText('paper/main.tex#claim-1')).toBeInTheDocument();
    expect(within(row).queryByRole('link')).toBeNull();
  });

  it('labels the remote ledger source', () => {
    view(payload());
    const row = screen.getAllByRole('listitem').find((li) => li.textContent?.includes('Submitted run.py'))!;
    expect(within(row).getByText('remote ledger', { selector: '.decision__source' })).toBeInTheDocument();
  });

  it('marks unverified rows with an explanatory title and shows notes', () => {
    view(payload({ events: [event({ note: 'Only the current state is stored.' }), event({ ts: null, verified: false, summary: 'u' })], total: 2 }));
    const label = screen.getByText('unverified');
    expect(label).toHaveAttribute('title', 'Read from the lifecycle files without hash or consistency checks.');
    expect(screen.getByText('Only the current state is stored.')).toBeInTheDocument();
  });

  it('renders summaries literally, never as markup', () => {
    const { container } = view(payload({ events: [event({ summary: '<script>alert(1)</script><b>x</b>' })], total: 1 }));
    expect(screen.getByText('<script>alert(1)</script><b>x</b>')).toBeInTheDocument();
    expect(container.querySelector('script, b')).toBeNull();
  });

  it('shows a status chip with count for every source state, with detail and truncation', () => {
    view(
      payload({
        sources: {
          declarations: { status: 'ok', count: 4, truncated: true },
          proposal: { status: 'unreadable', count: 0, truncated: false, detail: '2 unreadable' },
          experiment: { status: 'too_large', count: 0, truncated: false, detail: 'more than 500 files' },
          'remote-execution': { status: 'absent', count: 0, truncated: false },
        },
      }),
    );
    const chips = screen.getByRole('list', { name: 'Source status' });
    expect(within(chips).getByText(/declarations/).closest('li')).toHaveTextContent('ok');
    expect(within(chips).getByText(/declarations/).closest('li')).toHaveTextContent('4');
    expect(within(chips).getByText(/declarations/).closest('li')).toHaveTextContent('truncated');
    expect(within(chips).getByText(/proposal/).closest('li')).toHaveTextContent('unreadable');
    expect(within(chips).getByText(/proposal/).closest('li')).toHaveTextContent('2 unreadable');
    expect(within(chips).getByText(/experiment/).closest('li')).toHaveTextContent('too_large');
    expect(within(chips).getByText(/experiment/).closest('li')).toHaveTextContent('more than 500 files');
    expect(within(chips).getByText(/remote ledger/).closest('li')).toHaveTextContent('absent');
  });

  it('shows the top-level truncated notice', () => {
    view(payload({ truncated: true, total: 1500 }));
    expect(screen.getByText('Showing 3 of 1500')).toBeInTheDocument();
  });

  it('filters the fetched events client-side by source', async () => {
    const { refresh } = view(payload());
    await userEvent.click(screen.getByRole('checkbox', { name: 'declarations' }));
    expect(screen.queryByText('Declared claim-1')).toBeNull();
    expect(screen.getByText('Submitted run.py to w1')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('checkbox', { name: 'remote ledger' }));
    await userEvent.click(screen.getByRole('checkbox', { name: 'proposal' }));
    expect(screen.getByText('No decisions match the selected sources')).toBeInTheDocument();
    expect(refresh).not.toHaveBeenCalled();
  });
});

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import AtlasView from './AtlasView';
import type { AtlasEvidence, AtlasPayload } from '../../types';

const payload = (over: Partial<AtlasPayload> = {}): AtlasPayload => ({
  json: { status: 'ok', size: 100 },
  html: { status: 'ok', size: 200 },
  stale: false,
  validation: { status: 'ok', errors: [], error_count: 0 },
  summary: {
    systems: [
      { id: 's1', title: 'Transformers', planets: 5, families: ['attention', 'scaling'] },
      { id: 's2', title: 'State spaces', planets: 3, families: [] },
    ],
    links: 4,
    rels: { extends: 3, contradicts: 1 },
    evidence: [{ system: 's1', planet: 'p1', origin: 'arxiv:1706.03762', retrieved: '2026-01-02' }],
    evidence_total: 1,
  },
  ...over,
});

function view(data: AtlasPayload | null, extra: { loading?: boolean; error?: string | null } = {}) {
  const props = { refresh: vi.fn(), retry: vi.fn() };
  render(<AtlasView data={data} loading={extra.loading ?? false} error={extra.error ?? null} {...props} />);
  return props;
}

describe('AtlasView', () => {
  it('shows a loading state before the first response', () => {
    view(null, { loading: true });
    expect(screen.getByText(/Loading the atlas/)).toBeInTheDocument();
  });

  it('shows an inline error with Retry', async () => {
    const { retry } = view(null, { error: 'could not load the atlas: boom' });
    expect(screen.getByRole('alert')).toHaveTextContent('boom');
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(retry).toHaveBeenCalled();
  });

  it('refreshes on demand', async () => {
    const { refresh } = view(payload());
    await userEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it('renders the systems table, link count and rel breakdown', () => {
    view(payload());
    const row = screen.getByRole('row', { name: /Transformers/ });
    expect(row).toHaveTextContent('5');
    expect(row).toHaveTextContent('attention, scaling');
    expect(screen.getByRole('row', { name: /State spaces/ })).toBeInTheDocument();
    expect(screen.getByText(/4 link\(s\)/)).toBeInTheDocument();
    expect(screen.getByText('extends: 3')).toBeInTheDocument();
    expect(screen.getByText('contradicts: 1')).toBeInTheDocument();
  });

  it('renders titles literally, never as markup', () => {
    const data = payload();
    data.summary!.systems[0].title = '<script>alert(1)</script><b>bold</b>';
    const { container } = render(<AtlasView data={data} loading={false} error={null} refresh={vi.fn()} retry={vi.fn()} />);
    expect(screen.getByText('<script>alert(1)</script><b>bold</b>')).toBeInTheDocument();
    expect(container.querySelector('script, b')).toBeNull();
  });

  it('says how many evidence entries are shown of the total', () => {
    const evidence: AtlasEvidence[] = Array.from({ length: 3 }, (_, i) => ({ system: 's1', planet: `p${i}`, origin: `o${i}`, retrieved: '2026' }));
    const data = payload();
    data.summary!.evidence = evidence;
    data.summary!.evidence_total = 250;
    view(data);
    expect(screen.getByText('showing 3 of 250')).toBeInTheDocument();
    expect(screen.getByText('o2')).toBeInTheDocument();
  });

  it('renders the three validation states', () => {
    const { unmount } = render(<AtlasView data={payload()} loading={false} error={null} refresh={vi.fn()} retry={vi.fn()} />);
    expect(screen.getByLabelText('Validation')).toHaveTextContent('valid');
    unmount();
    const failed = payload({ validation: { status: 'failed', errors: ['E1', 'E2'], error_count: 5 } });
    const second = render(<AtlasView data={failed} loading={false} error={null} refresh={vi.fn()} retry={vi.fn()} />);
    expect(screen.getByLabelText('Validation')).toHaveTextContent('failed');
    expect(screen.getByText('E1')).toBeInTheDocument();
    expect(screen.getByText('3 more')).toBeInTheDocument();
    second.unmount();
    view(payload({ validation: { status: 'unavailable', detail: 'checker missing' } }));
    expect(screen.getByLabelText('Validation')).toHaveTextContent('unavailable');
    expect(screen.getByText('checker missing')).toBeInTheDocument();
  });

  it('shows the empty state when atlas.json is absent', () => {
    view(payload({ json: { status: 'absent' }, html: { status: 'absent' }, stale: null, summary: null }));
    expect(screen.getByText('No atlas yet. Run the plausibility skill to scout and map the SOTA pool.')).toBeInTheDocument();
    expect(screen.queryByTitle('SOTA constellation')).toBeNull();
  });

  it.each([
    ['too_large', /too large/],
    ['unsafe', /unsafe/],
    ['unreadable', /could not be read/],
    ['invalid', /not valid JSON/],
  ])('explains a %s atlas.json', (status, pattern) => {
    view(payload({ json: { status }, summary: null }));
    expect(screen.getByTestId('atlas-json-note')).toHaveTextContent(pattern);
  });

  it('explains JSON present with the HTML missing', () => {
    view(payload({ html: { status: 'absent' }, stale: null }));
    expect(screen.getByText(/JSON present, HTML missing/)).toHaveTextContent('scripts/render_atlas.py');
    expect(screen.queryByTitle('SOTA constellation')).toBeNull();
  });

  it('explains HTML present with the JSON absent', () => {
    view(payload({ json: { status: 'absent' }, stale: null, summary: null }));
    expect(screen.getByText(/atlas\.html exists but atlas\.json is missing/)).toBeInTheDocument();
  });

  it('shows a STALE badge only when stale is true', () => {
    const { unmount } = render(<AtlasView data={payload({ stale: true })} loading={false} error={null} refresh={vi.fn()} retry={vi.fn()} />);
    expect(screen.getByText(/atlas\.json is newer than atlas\.html; re-render/)).toBeInTheDocument();
    unmount();
    view(payload({ stale: null }));
    expect(screen.queryByText(/re-render/)).toBeNull();
  });

  it('embeds the constellation in an iframe sandboxed to allow-scripts only', () => {
    view(payload());
    const frame = screen.getByTitle('SOTA constellation');
    expect(frame.getAttribute('src')).toBe('/api/atlas/view');
    expect(frame.getAttribute('sandbox')).toBe('allow-scripts');
    expect(frame.getAttribute('referrerpolicy')).toBe('no-referrer');
    expect(frame.getAttributeNames().join(' ')).not.toContain('allow-same-origin');
    expect(frame.outerHTML).not.toContain('allow-same-origin');
  });

  it('replaces the iframe by a message when the HTML is not ok', () => {
    view(payload({ html: { status: 'too_large' }, stale: null }));
    expect(screen.queryByTitle('SOTA constellation')).toBeNull();
    expect(screen.getByText(/atlas\.html is too large/)).toBeInTheDocument();
  });
});

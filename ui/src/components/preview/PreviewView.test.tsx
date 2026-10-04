import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi, afterEach } from 'vitest';
import PreviewView from './PreviewView';
import type { PaperPreview, PreviewBlock } from '../../types';

const block = (id: string, extra: Partial<PreviewBlock> = {}): PreviewBlock => ({
  id, written: true, text: `text of ${id}`, words: 3, citations: [], truncated: false, duplicate: false, ...extra,
});

const base = (over: Partial<PaperPreview> = {}): PaperPreview => ({
  sections: [{ id: 'intro', title: 'Introduction', position: 1, status: 'DRAFTING', blocks: [block('intro.motivation')] }],
  truncated: false,
  caps: {},
  main_tex: { status: 'ok' },
  pdf: null,
  ...over,
});

function view(data: PaperPreview | null, extra: { loading?: boolean; error?: string | null; retry?: () => void } = {}) {
  const retry = extra.retry ?? vi.fn();
  render(<PreviewView data={data} loading={extra.loading ?? false} error={extra.error ?? null} retry={retry} />);
  return { retry };
}

describe('PreviewView', () => {
  it('shows a loading state before the first response', () => {
    view(null, { loading: true });
    expect(screen.getByText(/Loading the paper preview/)).toBeInTheDocument();
  });

  it('shows an inline error with a working Retry', async () => {
    const { retry } = view(null, { error: 'could not load preview: 500' });
    expect(screen.getByRole('alert')).toHaveTextContent('500');
    screen.getByRole('button', { name: 'Retry' }).click();
    expect(retry).toHaveBeenCalled();
  });

  it('shows the empty state when there are no sections', () => {
    view(base({ sections: [] }));
    expect(screen.getByText('No sections yet')).toBeInTheDocument();
  });

  it('renders sections with title, id, status and blocks in order', () => {
    view(base({
      sections: [{ id: 'intro', title: 'Introduction', position: 1, status: 'DRAFTING', blocks: [block('intro.a'), block('intro.b')] }],
    }));
    const region = screen.getByRole('region', { name: 'Introduction' });
    expect(within(region).getByText('DRAFTING')).toBeInTheDocument();
    expect(within(region).getByText('intro')).toBeInTheDocument();
    const texts = within(region).getAllByTestId('preview-block').map((node) => node.textContent);
    expect(texts[0]).toContain('text of intro.a');
    expect(texts[1]).toContain('text of intro.b');
  });

  it('renders block text as escaped plain text, never as markup', () => {
    const evil = '<script>alert(1)</script> and <b>bold</b>';
    const { container } = render(
      <PreviewView
        data={base({ sections: [{ id: 's', title: null, position: 1, status: 'DRAFTING', blocks: [block('s.x', { text: evil })] }] })}
        loading={false} error={null} retry={() => {}}
      />,
    );
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('b')).toBeNull();
    expect(screen.getByText(evil)).toBeInTheDocument();
  });

  it('shows citation keys as chips', () => {
    view(base({ sections: [{ id: 's', title: null, position: 1, status: 'DRAFTING', blocks: [block('s.x', { citations: ['smith2020', 'lee2021'] })] }] }));
    const chips = screen.getByRole('list', { name: 'Citations' });
    expect(within(chips).getByText('smith2020')).toBeInTheDocument();
    expect(within(chips).getByText('lee2021')).toBeInTheDocument();
  });

  it('shows a placeholder with the block id for an unwritten block', () => {
    view(base({ sections: [{ id: 's', title: null, position: 1, status: 'CONTRACTED', blocks: [block('s.todo', { written: false, text: null })] }] }));
    expect(screen.getByText(/Not written yet/)).toHaveTextContent('s.todo');
  });

  it('flags truncated and duplicate blocks and a truncated preview', () => {
    view(base({
      truncated: true,
      sections: [{ id: 's', title: null, position: 1, status: 'DRAFTING', blocks: [block('s.a', { truncated: true }), block('s.b', { duplicate: true })] }],
    }));
    expect(screen.getByText('Preview truncated')).toBeInTheDocument();
    expect(screen.getByText(/This block is cut short/)).toBeInTheDocument();
    expect(screen.getByText(/Duplicate block id/)).toBeInTheDocument();
  });

  it.each([
    ['absent', /no paper\/main\.tex/i],
    ['too_large', /too large/i],
    ['unsafe', /unsafe/i],
    ['unreadable', /could not be read/i],
  ])('explains main.tex status %s', (status, pattern) => {
    view(base({ main_tex: { status } }));
    expect(screen.getByText(pattern)).toBeInTheDocument();
  });

  it('embeds the compiled PDF with a relative src', () => {
    view(base({ pdf: { main: { present: true, size: 10, stale: false, mtime: 1700000000000 }, figures: [] } }));
    const frame = screen.getByTitle('Compiled paper PDF');
    expect(frame).toHaveAttribute('src', '/api/paper/file?name=main.pdf&v=1700000000000-10');
    expect(frame).toHaveAttribute('referrerpolicy', 'no-referrer');
    expect(screen.queryByText(/stale/i)).toBeNull();
  });

  it('badges a stale PDF', () => {
    view(base({ pdf: { main: { present: true, size: 10, stale: true, mtime: 1700000000000 }, figures: [] } }));
    expect(screen.getByText(/stale: main\.tex is newer than main\.pdf/)).toBeInTheDocument();
  });

  it('explains an absent PDF', () => {
    view(base({ pdf: { main: null, figures: [] } }));
    expect(screen.queryByTitle('Compiled paper PDF')).toBeNull();
    expect(screen.getByText(/No compiled PDF found/)).toBeInTheDocument();
  });

  it('lists figures with encoded safe links and a png preview', () => {
    view(base({ pdf: { main: null, figures: [{ id: 'fig one', kind: 'png', size: 2048, mtime: 1700000000001 }, { id: 'arch', kind: 'pdf', size: 10 }] } }));
    const links = screen.getAllByRole('link', { name: /Open/ });
    expect(links[0]).toHaveAttribute('href', '/api/paper/file?name=figures/fig%20one.png');
    expect(links[0]).toHaveAttribute('target', '_blank');
    expect(links[0]).toHaveAttribute('rel', 'noopener noreferrer');
    expect(links[1]).toHaveAttribute('href', '/api/paper/file?name=figures/arch.pdf');
    expect(screen.getByAltText('Figure fig one')).toHaveAttribute('src', '/api/paper/file?name=figures/fig%20one.png&v=1700000000001-2048');
    expect(screen.queryByAltText('Figure arch')).toBeNull();
  });

  it('reloads the PDF and the figure thumbnails when their metadata changes', () => {
    const pdf = (mtime: number, size: number) => ({
      main: { present: true, size, stale: false, mtime },
      figures: [{ id: 'plot', kind: 'png' as const, size: 5, mtime }],
    });
    const props = { loading: false, error: null, retry: vi.fn() };
    const { rerender } = render(<PreviewView data={base({ pdf: pdf(100, 10) })} {...props} />);
    const frame = screen.getByTitle('Compiled paper PDF');
    const image = screen.getByAltText('Figure plot');
    rerender(<PreviewView data={base({ pdf: pdf(100, 10) })} {...props} />);
    expect(screen.getByTitle('Compiled paper PDF')).toBe(frame);
    expect(screen.getByAltText('Figure plot')).toBe(image);
    rerender(<PreviewView data={base({ pdf: pdf(200, 11) })} {...props} />);
    expect(screen.getByTitle('Compiled paper PDF')).not.toBe(frame);
    expect(screen.getByTitle('Compiled paper PDF').getAttribute('src')).toBe('/api/paper/file?name=main.pdf&v=200-11');
    expect(screen.getByAltText('Figure plot')).not.toBe(image);
    expect(screen.getByAltText('Figure plot').getAttribute('src')).toBe('/api/paper/file?name=figures/plot.png&v=200-5');
  });

  it('falls back to the size when the payload has no mtime', () => {
    view(base({ pdf: { main: { present: true, size: 10, stale: false }, figures: [] } }));
    expect(screen.getByTitle('Compiled paper PDF').getAttribute('src')).toBe('/api/paper/file?name=main.pdf&v=10');
  });

  describe('duplicate block ids', () => {
    afterEach(() => vi.restoreAllMocks());

    it('renders both entries without a React duplicate-key warning', () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
      view(base({
        sections: [{
          id: 'intro', title: 'Introduction', position: 1, status: 'DRAFTING',
          blocks: [block('intro.dup', { text: 'first' }), block('intro.dup', { text: 'second', duplicate: true })],
        }],
      }));
      expect(screen.getAllByTestId('preview-block')).toHaveLength(2);
      const keyWarnings = spy.mock.calls.filter((call) => String(call[0]).includes('same key'));
      expect(keyWarnings).toHaveLength(0);
    });
  });
});

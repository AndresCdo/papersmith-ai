import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { diagramState } from './components/dag/fixtures';

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  listeners = new Map<string, ((event: MessageEvent<string>) => void)[]>();
  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }
  addEventListener(name: string, handler: (event: MessageEvent<string>) => void) {
    this.listeners.set(name, [...(this.listeners.get(name) ?? []), handler]);
  }
  close() {}
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('App', () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    delete document.body.dataset.ready;
    vi.stubGlobal('EventSource', FakeEventSource);
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) =>
        url.includes('/api/health') ? jsonResponse({ overall: 'WIRED' }) : jsonResponse({ stages: [], gates: [], sections: [] }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('marks the body ready once the state is applied', async () => {
    render(<App />);
    await waitFor(() => expect(document.body.dataset.ready).toBe('1'));
  });

  it('marks the body as errored when the state fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) =>
        url.includes('/api/health') ? jsonResponse({ overall: 'WIRED' }) : new Response('boom', { status: 500 }),
      ),
    );
    render(<App />);
    await waitFor(() => expect(document.body.dataset.ready).toBe('error'));
  });

  it('renders the tab bar', async () => {
    render(<App />);
    const nav = screen.getByRole('navigation', { name: 'Dashboard sections' });
    expect(nav).toBeInTheDocument();
    for (const label of ['Pipeline', 'Health', 'Sections', 'Artifacts']) {
      expect(await screen.findByRole('button', { name: label })).toBeInTheDocument();
    }
  });

  describe('hash routing', () => {
    afterEach(() => {
      window.history.replaceState(null, '', '#');
    });

    it('normalizes an empty or unknown fragment to the default tab', () => {
      window.history.replaceState(null, '', '#bogus');
      render(<App />);
      expect(window.location.hash).toBe('#pipeline');
    });

    it('keeps the element id of a deep link on mount', () => {
      window.history.replaceState(null, '', '#pipeline?el=stage%3Adrafting');
      render(<App />);
      expect(window.location.hash).toBe('#pipeline?el=stage%3Adrafting');
    });

    it('follows hashchange for the tab', async () => {
      window.history.replaceState(null, '', '#pipeline');
      render(<App />);
      act(() => {
        window.history.replaceState(null, '', '#health');
        window.dispatchEvent(new HashChangeEvent('hashchange'));
      });
      expect(screen.getByRole('button', { name: 'Health' })).toHaveAttribute('aria-current', 'page');
    });

    it('drops the element id when another tab is chosen', async () => {
      window.history.replaceState(null, '', '#pipeline?el=stage%3Adrafting');
      render(<App />);
      await userEvent.click(screen.getByRole('button', { name: 'Sections' }));
      expect(window.location.hash).toBe('#sections');
    });
  });

  describe('diagram selection', () => {
    afterEach(() => {
      window.history.replaceState(null, '', '#');
    });

    const withDiagram = () =>
      vi.stubGlobal(
        'fetch',
        vi.fn(async (url: string) =>
          url.includes('/api/health') ? jsonResponse({ overall: 'WIRED' }) : jsonResponse(diagramState),
        ),
      );

    it('opens the panel for a deep-linked element', async () => {
      withDiagram();
      window.history.replaceState(null, '', '#pipeline?el=gate%3Awriting-readiness');
      render(<App />);
      const panel = await screen.findByTestId('element-detail-panel');
      expect(panel).toHaveTextContent('contract missing');
    });

    it('selecting writes the hash, closing clears it', async () => {
      withDiagram();
      window.history.replaceState(null, '', '#pipeline');
      const { container } = render(<App />);
      const wrapper = await waitFor(() => {
        const found = container.querySelector('.react-flow__node[data-id="stage:drafting"]') as HTMLElement;
        expect(found).toBeTruthy();
        return found;
      });
      fireEvent.click(wrapper); // see PipelineGraph.test.tsx: user-event mousedown breaks d3-zoom in jsdom
      await screen.findByTestId('element-detail-panel');
      expect(window.location.hash).toBe('#pipeline?el=stage%3Adrafting');
      await userEvent.click(screen.getByRole('button', { name: 'Close' }));
      expect(screen.queryByTestId('element-detail-panel')).not.toBeInTheDocument();
      expect(window.location.hash).toBe('#pipeline');
    });

    it('clears the selection and the hash on a pane click', async () => {
      withDiagram();
      window.history.replaceState(null, '', '#pipeline?el=stage%3Adrafting');
      const { container } = render(<App />);
      await screen.findByTestId('element-detail-panel');
      fireEvent.click(container.querySelector('.react-flow__pane') as HTMLElement);
      await waitFor(() => expect(screen.queryByTestId('element-detail-panel')).not.toBeInTheDocument());
      expect(window.location.hash).toBe('#pipeline');
    });

    it('shows "No longer present" when the state loses the element', async () => {
      withDiagram();
      window.history.replaceState(null, '', '#pipeline?el=section%3AGone');
      render(<App />);
      expect(await screen.findByText(/No longer present/)).toBeInTheDocument();
    });
  });
});

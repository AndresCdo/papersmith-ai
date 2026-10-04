import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

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
});

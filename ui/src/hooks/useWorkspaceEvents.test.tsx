import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useWorkspaceEvents } from './useWorkspaceEvents';

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  listeners = new Map<string, ((event: MessageEvent<string>) => void)[]>();
  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }
  addEventListener(name: string, handler: (event: MessageEvent<string>) => void) {
    this.listeners.set(name, [...(this.listeners.get(name) ?? []), handler]);
  }
  emit(name: string, payload: unknown) {
    const event = { data: JSON.stringify({ type: name, payload }) } as MessageEvent<string>;
    for (const handler of this.listeners.get(name) ?? []) handler(event);
  }
  close() {}
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

/** A promise the test resolves by hand, to control when a fetch answers. */
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe('useWorkspaceEvents load ordering', () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    vi.stubGlobal('EventSource', FakeEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('applies the state as soon as it resolves, without waiting for health', async () => {
    const health = deferred<Response>();
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        url.includes('/api/health') ? health.promise : Promise.resolve(jsonResponse({ stages: [], marker: 'initial' })),
      ),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.state).not.toBeNull());
    expect(result.current.health).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('applies the health when it resolves after the state', async () => {
    const health = deferred<Response>();
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        url.includes('/api/health') ? health.promise : Promise.resolve(jsonResponse({ stages: [] })),
      ),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.state).not.toBeNull());
    await act(async () => {
      health.resolve(jsonResponse({ overall: 'WIRED' }));
    });
    await waitFor(() => expect(result.current.health).toEqual({ overall: 'WIRED' }));
  });

  it('applies the health even when the state is still pending', async () => {
    const state = deferred<Response>();
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        url.includes('/api/health') ? Promise.resolve(jsonResponse({ overall: 'WIRED' })) : state.promise,
      ),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.health).toEqual({ overall: 'WIRED' }));
    expect(result.current.state).toBeNull();
    expect(result.current.loading).toBe(true);
  });

  it('ignores the initial state response when a state_update was already applied', async () => {
    const state = deferred<Response>();
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        url.includes('/api/health') ? Promise.resolve(jsonResponse({ overall: 'WIRED' })) : state.promise,
      ),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    act(() => {
      FakeEventSource.instances[0].emit('state_update', { state: { marker: 'live' }, changed: [] });
    });
    expect(result.current.state).toEqual({ marker: 'live' });
    await act(async () => {
      state.resolve(jsonResponse({ marker: 'stale-initial' }));
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.state).toEqual({ marker: 'live' });
  });
});

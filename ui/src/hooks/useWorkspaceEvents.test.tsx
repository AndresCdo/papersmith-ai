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

describe('useWorkspaceEvents history', () => {
  const BOOT = 'boot a/b';

  function hEntry(seq: number, boot = BOOT) {
    return {
      id: `${boot}-${seq}`, boot_id: boot, seq, ts: 1000 + seq, kind: 'section_status',
      element_id: 'section:intro', summary: `change ${seq}`, before: null, after: null,
    };
  }

  function hPage(entries: ReturnType<typeof hEntry>[], extra: Record<string, unknown> = {}) {
    return { boot_id: BOOT, entries, has_more: false, reset: false, gap: false, ...extra };
  }

  /** Routes fetches: history requests go to `history`, the rest to a trivial state/health. */
  function stubFetch(history: (url: string) => Response | Promise<Response>) {
    const fetchMock = vi.fn(async (url: string) =>
      url.startsWith('/api/history') ? history(url) : jsonResponse({ stages: [] }),
    );
    vi.stubGlobal('fetch', fetchMock);
    return () => fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.startsWith('/api/history'));
  }

  beforeEach(() => {
    FakeEventSource.instances = [];
    vi.stubGlobal('EventSource', FakeEventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('loads the first page on mount without a boot id', async () => {
    const calls = stubFetch(() => jsonResponse(hPage([hEntry(1), hEntry(2)])));
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(2));
    expect(calls()[0]).toBe('/api/history?after_seq=0');
  });

  it('pages with the encoded boot id and cursor until has_more is false', async () => {
    const calls = stubFetch((url) =>
      url.includes('after_seq=0')
        ? jsonResponse(hPage([hEntry(1), hEntry(2)], { has_more: true }))
        : jsonResponse(hPage([hEntry(3)])),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(3));
    expect(calls()).toEqual([
      '/api/history?after_seq=0',
      `/api/history?boot_id=${encodeURIComponent(BOOT)}&after_seq=2`,
    ]);
  });

  it('catches up from the last seq on every EventSource open', async () => {
    const calls = stubFetch((url) =>
      url.includes('after_seq=1') ? jsonResponse(hPage([hEntry(2)])) : jsonResponse(hPage([hEntry(1)])),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(1));
    act(() => FakeEventSource.instances[0].emit('open', {}));
    await waitFor(() => expect(result.current.history.entries).toHaveLength(2));
    expect(calls().at(-1)).toBe(`/api/history?boot_id=${encodeURIComponent(BOOT)}&after_seq=1`);
  });

  it('discards its entries on a reset and reloads', async () => {
    let boot = BOOT;
    stubFetch((url) =>
      url.includes('boot_id=')
        ? jsonResponse(hPage([hEntry(1, 'new')], { boot_id: 'new', reset: true }))
        : jsonResponse(hPage([hEntry(1), hEntry(2)], { boot_id: boot })),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(2));
    boot = 'new';
    act(() => FakeEventSource.instances[0].emit('open', {}));
    await waitFor(() => expect(result.current.history.bootId).toBe('new'));
    expect(result.current.history.entries.map((e) => e.id)).toEqual(['new-1']);
  });

  it('reports a gap from the server', async () => {
    stubFetch(() => jsonResponse(hPage([hEntry(7)], { gap: true })));
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.gap).toBe(true));
  });

  it('appends a live history_append entry when it is the next seq, without fetching', async () => {
    const calls = stubFetch(() => jsonResponse(hPage([hEntry(1)])));
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(1));
    const before = calls().length;
    act(() => FakeEventSource.instances[0].emit('history_append', hEntry(2)));
    expect(result.current.history.entries.map((e) => e.seq)).toEqual([1, 2]);
    expect(calls()).toHaveLength(before);
  });

  it('catches up through paging when a live entry skips a seq', async () => {
    stubFetch((url) =>
      url.includes('after_seq=1') ? jsonResponse(hPage([hEntry(2), hEntry(3), hEntry(4)])) : jsonResponse(hPage([hEntry(1)])),
    );
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.history.entries).toHaveLength(1));
    act(() => FakeEventSource.instances[0].emit('history_append', hEntry(4)));
    await waitFor(() => expect(result.current.history.entries.map((e) => e.seq)).toEqual([1, 2, 3, 4]));
  });

  it('shows an inline message when the server answers 422', async () => {
    stubFetch(() => new Response('{"detail":"bad"}', { status: 422 }));
    const { result } = renderHook(() => useWorkspaceEvents());
    await waitFor(() => expect(result.current.historyError).toMatch(/422/));
    expect(result.current.history.entries).toEqual([]);
  });
});

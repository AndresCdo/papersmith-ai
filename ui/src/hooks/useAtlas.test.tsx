import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useAtlas } from './useAtlas';
import type { AtlasPayload } from '../types';

const atlas = (marker: string): AtlasPayload => ({
  json: { status: 'ok' },
  html: { status: 'ok' },
  stale: false,
  validation: { status: 'ok', errors: [], error_count: 0 },
  summary: { systems: [{ id: marker, title: marker, planets: 1, families: [] }], links: 0, rels: {}, evidence: [], evidence_total: 0 },
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe('useAtlas', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('does not fetch while closed and fetches once when the tab opens', async () => {
    const fetchMock = vi.fn(async (_url: string) => json(atlas('a')));
    vi.stubGlobal('fetch', fetchMock);
    const { result, rerender } = renderHook(({ active }) => useAtlas(active), { initialProps: { active: false } });
    expect(fetchMock).not.toHaveBeenCalled();
    rerender({ active: true });
    await waitFor(() => expect(result.current.data?.summary?.systems[0].id).toBe('a'));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/atlas');
  });

  it('refetches on demand and never overlaps requests', async () => {
    const first = deferred<Response>();
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => first.promise)
      .mockImplementation(async () => json(atlas('latest')));
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => useAtlas(true));
    act(() => result.current.refresh());
    act(() => result.current.refresh());
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await act(async () => first.resolve(json(atlas('stale'))));
    await waitFor(() => expect(result.current.data?.summary?.systems[0].id).toBe('latest'));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('reports an error, retries on demand and keeps the last good data', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => new Response('x', { status: 500, statusText: 'Boom' }))
      .mockImplementationOnce(async () => json(atlas('ok')))
      .mockImplementation(async () => new Response('x', { status: 503 }));
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => useAtlas(true));
    await waitFor(() => expect(result.current.error).toMatch(/500/));
    expect(result.current.data).toBeNull();
    act(() => result.current.retry());
    await waitFor(() => expect(result.current.data?.summary?.systems[0].id).toBe('ok'));
    expect(result.current.error).toBeNull();
    act(() => result.current.refresh());
    await waitFor(() => expect(result.current.error).toMatch(/503/));
    expect(result.current.data?.summary?.systems[0].id).toBe('ok');
  });
});

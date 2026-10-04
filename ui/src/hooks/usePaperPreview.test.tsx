import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { usePaperPreview } from './usePaperPreview';
import type { PaperPreview } from '../types';

const preview = (marker: string): PaperPreview => ({
  sections: [{ id: marker, title: null, position: 1, status: 'DRAFTING', blocks: [] }],
  truncated: false,
  caps: {},
  main_tex: { status: 'ok' },
  pdf: null,
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

describe('usePaperPreview', () => {
  beforeEach(() => vi.useRealTimers());
  afterEach(() => vi.unstubAllGlobals());

  it('does not fetch while the tab is closed and fetches once when it opens', async () => {
    const fetchMock = vi.fn(async (_url: string) => json(preview('a')));
    vi.stubGlobal('fetch', fetchMock);
    const { result, rerender } = renderHook(({ active }) => usePaperPreview(active, 0), {
      initialProps: { active: false },
    });
    expect(fetchMock).not.toHaveBeenCalled();
    rerender({ active: true });
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('a'));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/paper/preview');
  });

  it('refetches when the revision changes while open', async () => {
    const fetchMock = vi.fn(async () => json(preview(`r${fetchMock.mock.calls.length}`)));
    vi.stubGlobal('fetch', fetchMock);
    const { result, rerender } = renderHook(({ revision }) => usePaperPreview(true, revision), {
      initialProps: { revision: 1 },
    });
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('r1'));
    rerender({ revision: 2 });
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('r2'));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('collapses a burst of revision changes during an in-flight request into one extra fetch', async () => {
    const first = deferred<Response>();
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => first.promise)
      .mockImplementation(async () => json(preview('latest')));
    vi.stubGlobal('fetch', fetchMock);
    const { result, rerender } = renderHook(({ revision }) => usePaperPreview(true, revision), {
      initialProps: { revision: 1 },
    });
    rerender({ revision: 2 });
    rerender({ revision: 3 });
    rerender({ revision: 4 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await act(async () => first.resolve(json(preview('stale'))));
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('latest'));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('reports an error and retries on demand', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => new Response('nope', { status: 500, statusText: 'Boom' }))
      .mockImplementation(async () => json(preview('ok')));
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => usePaperPreview(true, 0));
    await waitFor(() => expect(result.current.error).toMatch(/500/));
    expect(result.current.data).toBeNull();
    act(() => result.current.retry());
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('ok'));
    expect(result.current.error).toBeNull();
  });

  it('keeps the previous data when a refetch fails', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => json(preview('kept')))
      .mockImplementation(async () => new Response('x', { status: 503 }));
    vi.stubGlobal('fetch', fetchMock);
    const { result, rerender } = renderHook(({ revision }) => usePaperPreview(true, revision), {
      initialProps: { revision: 1 },
    });
    await waitFor(() => expect(result.current.data?.sections[0].id).toBe('kept'));
    rerender({ revision: 2 });
    await waitFor(() => expect(result.current.error).toMatch(/503/));
    expect(result.current.data?.sections[0].id).toBe('kept');
  });
});

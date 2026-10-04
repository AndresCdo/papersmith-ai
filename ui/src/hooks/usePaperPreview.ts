import { useCallback, useEffect, useRef, useState } from 'react';
import type { PaperPreview } from '../types';

const PREVIEW_URL = '/api/paper/preview';

export interface PaperPreviewHook {
  data: PaperPreview | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

/**
 * Lazily fetch the paper preview while its tab is `active`, and refetch when
 * the workspace `revision` changes. Requests never overlap: a change that
 * arrives mid-flight sets one pending flag and costs exactly one more fetch.
 * A failed refetch keeps the last good data and surfaces the error inline.
 */
export function usePaperPreview(active: boolean, revision: number): PaperPreviewHook {
  const [data, setData] = useState<PaperPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const inFlight = useRef(false);
  const pending = useRef(false);
  const alive = useRef(true);

  const load = useCallback(async () => {
    if (inFlight.current) {
      pending.current = true;
      return;
    }
    inFlight.current = true;
    setLoading(true);
    try {
      do {
        pending.current = false;
        try {
          const response = await fetch(PREVIEW_URL, { headers: { Accept: 'application/json' } });
          if (!response.ok) throw new Error(`${PREVIEW_URL} responded ${response.status} ${response.statusText}`);
          const body = (await response.json()) as PaperPreview;
          if (!alive.current) return;
          setData(body);
          setError(null);
        } catch (reason) {
          if (!alive.current) return;
          setError(`could not load the preview: ${String(reason)}`);
        }
      } while (pending.current);
    } finally {
      inFlight.current = false;
      if (alive.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    if (active) void load();
  }, [active, revision, retryToken, load]);

  const retry = useCallback(() => setRetryToken((value) => value + 1), []);
  return { data, loading, error, retry };
}

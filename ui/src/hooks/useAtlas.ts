import { useCallback, useEffect, useRef, useState } from 'react';
import type { AtlasPayload } from '../types';

const ATLAS_URL = '/api/atlas';

export interface AtlasHook {
  data: AtlasPayload | null;
  loading: boolean;
  error: string | null;
  /** Fetch again (the atlas files are not watched, so there is no SSE refetch). */
  refresh: () => void;
  retry: () => void;
}

/**
 * Lazily fetch the atlas summary while its tab is `active`, and again on
 * demand. Requests never overlap: a refresh during a request sets one pending
 * flag and costs exactly one more fetch. A failed refetch keeps the last good
 * data and surfaces the error inline.
 */
export function useAtlas(active: boolean): AtlasHook {
  const [data, setData] = useState<AtlasPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState(0);
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
          const response = await fetch(ATLAS_URL, { headers: { Accept: 'application/json' } });
          if (!response.ok) throw new Error(`${ATLAS_URL} responded ${response.status} ${response.statusText}`);
          const body = (await response.json()) as AtlasPayload;
          if (!alive.current) return;
          setData(body);
          setError(null);
        } catch (reason) {
          if (!alive.current) return;
          setError(`could not load the atlas: ${String(reason)}`);
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
  }, [active, token, load]);

  const refresh = useCallback(() => setToken((value) => value + 1), []);
  return { data, loading, error, refresh, retry: refresh };
}

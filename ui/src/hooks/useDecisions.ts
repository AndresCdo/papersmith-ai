import { useCallback, useEffect, useRef, useState } from 'react';
import type { DecisionsPayload } from '../types';

const DECISIONS_URL = '/api/decisions';

export interface DecisionsHook {
  data: DecisionsPayload | null;
  loading: boolean;
  error: string | null;
  /** Fetch again (the decision sources are not watched, so there is no SSE refetch). */
  refresh: () => void;
  retry: () => void;
}

/**
 * Lazily fetch the decisions timeline while its tab is `active`, and again on
 * demand. Requests never overlap: a refresh during a request sets one pending
 * flag and costs exactly one more fetch. A failed refetch keeps the last good
 * data and surfaces the error inline.
 */
export function useDecisions(active: boolean): DecisionsHook {
  const [data, setData] = useState<DecisionsPayload | null>(null);
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
          const response = await fetch(DECISIONS_URL, { headers: { Accept: 'application/json' } });
          if (!response.ok) throw new Error(`${DECISIONS_URL} responded ${response.status} ${response.statusText}`);
          const body = (await response.json()) as DecisionsPayload;
          if (!alive.current) return;
          setData(body);
          setError(null);
        } catch (reason) {
          if (!alive.current) return;
          setError(`could not load the decisions: ${String(reason)}`);
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

import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  StateUpdatePayload,
  WiringHealth,
  WiringSmokeLinePayload,
  WiringSmokeResult,
  WorkspaceState,
} from '../types';

const STATE_URL = '/api/state';
const HEALTH_URL = '/api/health/wiring';
const EVENTS_URL = '/api/events';
const SMOKE_URL = '/api/health/run-wiring-smoke';

/**
 * Live workspace snapshot for the dashboard.
 *
 * The hook primes both payloads over HTTP on mount (so a first paint never
 * waits for an event), then keeps them current from the `/api/events` SSE
 * stream. `state_update` frames carry the whole state payload, so the retained
 * snapshot is replaced rather than patched.
 */
export interface SmokeRun {
  running: boolean;
  /** `false` when the workspace has no wiring-smoke script to run. */
  available: boolean | null;
  exitCode: number | null;
  detail: string | null;
  output: string[];
}

export interface WorkspaceEventsHook {
  state: WorkspaceState | null;
  health: WiringHealth | null;
  connected: boolean;
  /** Workspace-relative paths reported by the last `state_update` frame. */
  lastChanged: string[];
  loading: boolean;
  error: string | null;
  smoke: SmokeRun;
  runSmoke: () => Promise<void>;
  clearSmoke: () => void;
}

const EMPTY_SMOKE: SmokeRun = {
  running: false,
  available: null,
  exitCode: null,
  detail: null,
  output: [],
};

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!response.ok) {
    throw new Error(`${url} responded ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

function parseFrame<T>(event: MessageEvent<string>): T | null {
  try {
    return JSON.parse(event.data) as T;
  } catch {
    return null;
  }
}

export function useWorkspaceEvents(): WorkspaceEventsHook {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [health, setHealth] = useState<WiringHealth | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastChanged, setLastChanged] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [smoke, setSmoke] = useState<SmokeRun>(EMPTY_SMOKE);

  const smokeRequestRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      const [stateResult, healthResult] = await Promise.allSettled([
        fetchJson<WorkspaceState>(STATE_URL),
        fetchJson<WiringHealth>(HEALTH_URL),
      ]);
      if (cancelled) return;
      if (stateResult.status === 'fulfilled') {
        setState(stateResult.value);
      } else {
        setError(`could not load ${STATE_URL}: ${String(stateResult.reason)}`);
      }
      if (healthResult.status === 'fulfilled') {
        setHealth(healthResult.value);
      } else {
        setError((previous) => previous ?? `could not load ${HEALTH_URL}: ${String(healthResult.reason)}`);
      }
      setLoading(false);
    })();

    const source = new EventSource(EVENTS_URL);

    source.addEventListener('open', () => {
      setConnected(true);
      setError(null);
    });

    // EventSource reconnects on its own; the badge only reflects the gap.
    source.addEventListener('error', () => setConnected(false));

    source.addEventListener('ready', () => {
      setConnected(true);
      setError(null);
    });

    source.addEventListener('state_update', (event) => {
      const payload = parseFrame<StateUpdatePayload>(event as MessageEvent<string>);
      if (!payload) return;
      if (payload.state) setState(payload.state);
      if (payload.changed) setLastChanged(payload.changed);
    });

    source.addEventListener('health_update', (event) => {
      const payload = parseFrame<WiringHealth>(event as MessageEvent<string>);
      if (payload) setHealth(payload);
    });

    source.addEventListener('wiring_smoke', (event) => {
      const payload = parseFrame<WiringSmokeLinePayload>(event as MessageEvent<string>);
      if (!payload?.line && payload?.line !== '') return;
      const line = payload.line ?? '';
      setSmoke((previous) => ({ ...previous, running: true, output: [...previous.output, line] }));
    });

    source.addEventListener('wiring_smoke_started', () => {
      setSmoke({ ...EMPTY_SMOKE, running: true, output: [] });
    });

    source.addEventListener('wiring_smoke_done', (event) => {
      const payload = parseFrame<{ exit_code?: number | null; detail?: string }>(
        event as MessageEvent<string>,
      );
      setSmoke((previous) => ({
        ...previous,
        running: false,
        exitCode: payload?.exit_code ?? previous.exitCode,
        detail: payload?.detail ?? previous.detail,
      }));
    });

    return () => {
      cancelled = true;
      source.close();
      setConnected(false);
    };
  }, []);

  const runSmoke = useCallback(async () => {
    if (smokeRequestRef.current) return;
    smokeRequestRef.current = true;
    setSmoke({ ...EMPTY_SMOKE, running: true, output: [] });
    try {
      const response = await fetch(SMOKE_URL, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`POST ${SMOKE_URL} responded ${response.status} ${response.statusText}`);
      }
      const result = (await response.json()) as WiringSmokeResult;
      setSmoke((previous) => ({
        ...previous,
        running: false,
        available: result.available ?? null,
        exitCode: result.exit_code ?? previous.exitCode,
        detail: result.detail ?? null,
        // Streamed lines already arrived over SSE; the response body is the
        // fallback for a client that missed them.
        output: previous.output.length ? previous.output : (result.output ?? '').split('\n').filter(Boolean),
      }));
    } catch (reason) {
      setSmoke({ ...EMPTY_SMOKE, detail: String(reason) });
      setError(String(reason));
    } finally {
      smokeRequestRef.current = false;
    }
  }, []);

  const clearSmoke = useCallback(() => setSmoke(EMPTY_SMOKE), []);

  return { state, health, connected, lastChanged, loading, error, smoke, runSmoke, clearSmoke };
}

import { useCallback, useEffect, useRef, useState } from 'react';
import { applyAppend, applyPage, emptyHistory, lastSeq, type HistoryState } from '../lib/history';
import type {
  HistoryEntry,
  HistoryPage,
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
const HISTORY_URL = '/api/history';

/**
 * Live workspace snapshot for the dashboard.
 *
 * The hook primes both payloads over HTTP on mount (so a first paint never
 * waits for an event), then keeps them current from the `/api/events` SSE
 * stream. `state_update` frames carry the whole state payload, so the retained
 * snapshot is replaced rather than patched. The server sends neither payload
 * when a stream connects, so the hook asks for both again on every open: a
 * change made while the stream was down shows at once, not with the next one.
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
  /** Count of `state_update` frames (or the server revision): changes when the workspace changes. */
  revision: number;
  loading: boolean;
  error: string | null;
  smoke: SmokeRun;
  /** In-memory history since the dashboard server started (oldest first). */
  history: HistoryState;
  /** Inline message when a history request failed (for example a 422). */
  historyError: string | null;
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

/**
 * Orders one payload's snapshot requests against each other and against its
 * live frames, without assuming the server answers requests in the order they
 * were sent. Only the latest request's answer is applied, and only if no live
 * frame for the payload landed after that request was sent. The server builds
 * an answer only after it receives the request, from data at least as new as
 * anything it sent before (the state is computed per request; the health
 * cache is refreshed by every measurement the server publishes). So the
 * answer is at least as new as everything shown before the request went out:
 * an earlier answer, or a frame that had already landed. An older request's
 * answer is dropped even when it arrives first, since the latest answer could
 * then move the dashboard backwards.
 */
function snapshotOrder() {
  let sent = 0;
  let frames = 0;
  return {
    /** Call as a request is sent. */
    send() {
      const ticket = ++sent;
      const framesWhenSent = frames;
      return {
        /** No newer request was sent since this one. */
        latest: () => ticket === sent,
        /** Its answer may be applied: still the latest, and no live frame landed since it was sent. */
        current: () => ticket === sent && frames === framesWhenSent,
      };
    },
    /** Call when a live frame replaces the payload. */
    frame() {
      frames += 1;
    },
  };
}

/**
 * One SSE frame body as the backend emits it: the event name plus its
 * payload, JSON-encoded by `format_sse`. The event type is repeated in the
 * body so a client that reads only `data:` still sees it.
 */
interface ServerFrame {
  type?: string;
  payload?: unknown;
}

function parseFrame<T>(event: MessageEvent<string>): T | null {
  try {
    const body = JSON.parse(event.data) as T & ServerFrame;
    // Every `/api/events` frame wraps its payload as `{type, payload}`; return
    // the inner payload so consumers read `payload.state`/`payload.changed`.
    // The initial HTTP snapshots do not go through `parseFrame`, so they keep
    // their unwrapped shape. A frame that already carries its fields at the
    // top level (older server) is returned as-is.
    if (body && typeof body === 'object' && 'payload' in body) {
      return body.payload as T;
    }
    return body;
  } catch {
    return null;
  }
}

export function useWorkspaceEvents(): WorkspaceEventsHook {
  const [state, setState] = useState<WorkspaceState | null>(null);
  const [health, setHealth] = useState<WiringHealth | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastChanged, setLastChanged] = useState<string[]>([]);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [smoke, setSmoke] = useState<SmokeRun>(EMPTY_SMOKE);

  const [history, setHistory] = useState<HistoryState>(emptyHistory);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const historyRef = useRef<HistoryState>(emptyHistory);

  const smokeRequestRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const commitHistory = (next: HistoryState) => {
      historyRef.current = next;
      setHistory(next);
    };

    // Page `/api/history` from the held cursor until has_more is false. Runs
    // on mount, on every EventSource open and when a live entry skips a seq;
    // overlapping requests collapse into one extra pass.
    let catchingUp = false;
    let again = false;
    const catchUp = async () => {
      if (catchingUp) {
        again = true;
        return;
      }
      catchingUp = true;
      try {
        do {
          again = false;
          for (;;) {
            const held = historyRef.current;
            const params = held.bootId ? `boot_id=${encodeURIComponent(held.bootId)}&` : '';
            const page = await fetchJson<HistoryPage>(
              `${HISTORY_URL}?${params}after_seq=${encodeURIComponent(String(lastSeq(held)))}`,
            );
            if (cancelled) return;
            commitHistory(applyPage(historyRef.current, page));
            setHistoryError(null);
            if (!page.has_more || page.entries.length === 0) break;
          }
        } while (again);
      } catch (reason) {
        if (!cancelled) setHistoryError(`could not load history: ${String(reason)}`);
      } finally {
        catchingUp = false;
      }
    };
    void catchUp();

    // State and health are each asked for on mount and again on every
    // EventSource open: the server sends neither when a stream connects, so
    // the snapshots an open asks for are what cover a change made while the
    // stream was down. `loading` ends when the latest state request settles.
    const stateOrder = snapshotOrder();
    const healthOrder = snapshotOrder();
    const loadState = () => {
      const request = stateOrder.send();
      fetchJson<WorkspaceState>(STATE_URL).then(
        (value) => {
          if (cancelled) return;
          if (request.current()) setState(value);
          if (request.latest()) setLoading(false);
        },
        (reason) => {
          if (cancelled) return;
          if (request.current()) setError(`could not load ${STATE_URL}: ${String(reason)}`);
          if (request.latest()) setLoading(false);
        },
      );
    };
    const loadHealth = () => {
      const request = healthOrder.send();
      fetchJson<WiringHealth>(HEALTH_URL).then(
        (value) => {
          if (!cancelled && request.current()) setHealth(value);
        },
        (reason) => {
          if (!cancelled && request.current()) {
            setError((previous) => previous ?? `could not load ${HEALTH_URL}: ${String(reason)}`);
          }
        },
      );
    };

    // State and health load independently: neither waits for the other, so a
    // slow health measurement never keeps the dashboard on "Loading".
    loadState();
    loadHealth();

    const source = new EventSource(EVENTS_URL);

    source.addEventListener('open', () => {
      setConnected(true);
      setError(null);
      void catchUp();
      loadState();
      loadHealth();
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
      if (payload.state) {
        stateOrder.frame();
        setState(payload.state);
      }
      if (payload.changed) setLastChanged(payload.changed);
      setRevision((previous) => (typeof payload.revision === 'number' ? payload.revision : previous + 1));
    });

    source.addEventListener('health_update', (event) => {
      const payload = parseFrame<WiringHealth>(event as MessageEvent<string>);
      if (payload) {
        healthOrder.frame();
        setHealth(payload);
      }
    });

    source.addEventListener('history_append', (event) => {
      const entry = parseFrame<HistoryEntry>(event as MessageEvent<string>);
      if (!entry || typeof entry.seq !== 'number') return;
      const result = applyAppend(historyRef.current, entry);
      if (result.state !== historyRef.current) commitHistory(result.state);
      if (result.catchUp) void catchUp();
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

  return {
    state, health, connected, lastChanged, revision, loading, error, smoke, history, historyError, runSmoke, clearSmoke,
  };
}

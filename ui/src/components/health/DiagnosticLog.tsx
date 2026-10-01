import { useEffect, useRef, useState } from 'react';
import type { SmokeRun } from '../../hooks/useWorkspaceEvents';
import { StatusBadge } from '../StatusBadge';

interface DiagnosticLogProps {
  smoke: SmokeRun;
  runSmoke: () => Promise<void>;
  clearSmoke: () => void;
  connected: boolean;
}

function exitTone(exitCode: number | null, running: boolean) {
  if (running) return 'info' as const;
  if (exitCode === 0) return 'ok' as const;
  if (exitCode === null) return 'idle' as const;
  return 'bad' as const;
}

/**
 * Slide-over terminal pane for the wiring smoke test. Lines arrive from the
 * `wiring_smoke` SSE frames; the button only starts the run.
 */
export default function DiagnosticLog({ smoke, runSmoke, clearSmoke, connected }: DiagnosticLogProps) {
  const [open, setOpen] = useState(false);
  const logRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const node = logRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [smoke.output.length, open]);

  // A run started from anywhere (this pane, another tab, the CLI) unveils the
  // log so its streamed lines are visible without a second click.
  useEffect(() => {
    if (smoke.running) setOpen(true);
  }, [smoke.running]);

  return (
    <>
      <div className="console-bar">
        <button type="button" className="button" onClick={() => void runSmoke()} disabled={smoke.running}>
          {smoke.running ? 'Wiring smoke running…' : 'Run Wiring Smoke Test'}
        </button>
        <button type="button" className="button button--ghost" onClick={() => setOpen((value) => !value)}>
          {open ? 'Hide log' : `Show log${smoke.output.length ? ` (${smoke.output.length})` : ''}`}
        </button>
        <StatusBadge
          label={smoke.running ? 'RUNNING' : smoke.exitCode === null ? 'NO RUN' : `EXIT ${smoke.exitCode}`}
          tone={exitTone(smoke.exitCode, smoke.running)}
        />
        <span className="console-bar__meta">{connected ? 'stream live' : 'stream offline'}</span>
      </div>

      {open ? (
        <aside className="slide-over" aria-label="Wiring smoke output">
          <header className="slide-over__header">
            <span className="slide-over__title">wiring smoke</span>
            <div className="slide-over__actions">
              <button type="button" className="button button--ghost" onClick={clearSmoke} disabled={smoke.running}>
                Clear
              </button>
              <button type="button" className="button button--ghost" onClick={() => setOpen(false)}>
                Close
              </button>
            </div>
          </header>

          {smoke.available === false ? (
            <p className="slide-over__note">This workspace has no wiring-smoke script to run.</p>
          ) : null}
          {smoke.detail ? <p className="slide-over__note">{smoke.detail}</p> : null}

          <pre className="console" ref={logRef}>
            {smoke.output.length > 0 ? smoke.output.join('\n') : 'no output yet — press “Run Wiring Smoke Test”'}
          </pre>
        </aside>
      ) : null}
    </>
  );
}

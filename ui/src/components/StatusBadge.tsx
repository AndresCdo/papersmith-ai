import type { ReactNode } from 'react';

export type BadgeTone = 'ok' | 'warn' | 'bad' | 'info' | 'idle' | 'sealed';

/**
 * One badge renderer for every state vocabulary the backend emits. Unknown
 * values fall back to the neutral tone, so a new backend state renders as an
 * unstyled label instead of breaking the page.
 */
export function StatusBadge({
  label,
  tone = 'idle',
  title,
}: {
  label: string;
  tone?: BadgeTone;
  title?: string;
}) {
  return (
    <span className="badge" data-tone={tone} title={title ?? label}>
      {label}
    </span>
  );
}

export function toneForSectionStatus(status: string | undefined): BadgeTone {
  switch (status) {
    case 'SEALED':
      return 'sealed';
    case 'AUDITED':
      return 'ok';
    case 'DRAFTING':
      return 'info';
    case 'CONTRACTED':
      return 'warn';
    case 'SCAFFOLDED':
      return 'idle';
    default:
      return 'idle';
  }
}

export function toneForGateState(state: string | undefined): BadgeTone {
  switch (state) {
    case 'PASSED':
      return 'ok';
    case 'BLOCKED':
      return 'bad';
    case 'VERIFYING':
      return 'warn';
    default:
      return 'idle';
  }
}

export function toneForWiringState(state: string | undefined): BadgeTone {
  switch (state) {
    case 'WIRED':
      return 'ok';
    case 'DRIFT':
      return 'warn';
    case 'UNBOUND':
    case 'TOOL_MISSING':
      return 'bad';
    case 'UNVERIFIED':
      return 'idle';
    default:
      return 'idle';
  }
}

export function toneForHarnessSync(state: string | undefined): BadgeTone {
  switch (state) {
    case 'IN_SYNC':
      return 'ok';
    case 'DRIFT_DETECTED':
      return 'warn';
    case 'UNKNOWN':
      return 'idle';
    default:
      return 'idle';
  }
}

export function toneForSummaryState(state: string | undefined): BadgeTone {
  switch (state) {
    case 'HEALTHY':
      return 'ok';
    case 'DEGRADED':
      return 'warn';
    case 'BLOCKED':
      return 'bad';
    default:
      return 'idle';
  }
}

/** A labelled progress bar used by the DAG nodes and the section matrix. */
export function ProgressBar({
  fraction,
  tone,
  label,
}: {
  fraction: number;
  tone?: 'ok' | 'warn' | 'bad' | 'info';
  label?: ReactNode;
}) {
  const clamped = Math.min(1, Math.max(0, Number.isFinite(fraction) ? fraction : 0));
  return (
    <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(clamped * 100)}>
      <div className="progress-track">
        <div className="progress-fill" data-tone={tone ?? 'info'} style={{ width: `${clamped * 100}%` }} />
      </div>
      {label ? <span className="progress-label">{label}</span> : null}
    </div>
  );
}

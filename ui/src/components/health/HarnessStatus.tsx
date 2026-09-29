import type { CSSProperties } from 'react';
import { StatusBadge, toneForHarnessSync, toneForSummaryState, toneForWiringState } from '../StatusBadge';
import { formatCount, formatPercent, formatTime } from '../../lib/format';
import type { WiringHealth } from '../../types';

function ring(fraction: number): CSSProperties {
  const sweep = Math.round(Math.min(1, Math.max(0, fraction)) * 360);
  return { '--meter-sweep': `${sweep}deg` } as CSSProperties;
}

/**
 * Hero readiness meter for the wiring diagnostics: `components_healthy` over
 * `components_total`, the warning banners the backend raised, the per-harness
 * sync rows, and the environment probes.
 */
export default function HarnessStatus({ health }: { health: WiringHealth | null }) {
  const summary = health?.summary;
  const total = summary?.components_total ?? 0;
  const healthy = summary?.components_healthy ?? 0;
  const fraction = total > 0 ? healthy / total : 0;
  const warnings = summary?.warnings ?? [];
  const harnesses = health?.harness_sync?.harnesses ?? [];
  const environment = health?.environment;
  const packages = environment?.packages ?? [];

  if (!health) {
    return (
      <div className="panel panel--empty">
        <h2>Harness readiness</h2>
        <p>No wiring-health payload yet. Waiting for the command center to answer `/api/health/wiring`.</p>
      </div>
    );
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Harness readiness</h2>
        <span className="panel__meta">measured {formatTime(health.generated_at)}</span>
      </div>

      <div className="readiness">
        <div className="meter" style={ring(fraction)} role="img" aria-label={`${healthy} of ${total} components healthy`}>
          <div className="meter__inner">
            <strong>{formatPercent(fraction)}</strong>
            <span>
              {formatCount(healthy)}/{formatCount(total)}
            </span>
          </div>
        </div>
        <div className="readiness__facts">
          <StatusBadge label={summary?.state ?? 'UNKNOWN'} tone={toneForSummaryState(summary?.state)} />
          <p className="readiness__caption">
            {formatCount(healthy)} of {formatCount(total)} wired components healthy in this workspace.
          </p>
          <div className="readiness__rows">
            <span>
              harness sync
              <StatusBadge
                label={health.harness_sync?.state ?? 'UNKNOWN'}
                tone={toneForHarnessSync(health.harness_sync?.state)}
              />
            </span>
            <span>
              skills wired
              {formatCount((health.skills ?? []).filter((row) => row.state === 'WIRED').length)}/
              {formatCount((health.skills ?? []).length)}
            </span>
            <span>
              agents wired
              {formatCount((health.agents ?? []).filter((row) => row.state === 'WIRED').length)}/
              {formatCount((health.agents ?? []).length)}
            </span>
            <span>
              CLI front doors
              {formatCount((health.cli_entrypoints ?? []).filter((row) => row.state === 'WIRED').length)}/
              {formatCount((health.cli_entrypoints ?? []).length)}
            </span>
          </div>
        </div>
      </div>

      {warnings.length > 0 ? (
        <ul className="banner-list">
          {warnings.map((warning) => (
            <li key={warning} className="banner banner--warn">
              {warning}
            </li>
          ))}
        </ul>
      ) : (
        <p className="banner banner--ok">No wiring warnings reported.</p>
      )}

      <div className="columns">
        <div className="columns__col">
          <h3>Harness projections</h3>
          <ul className="kv-list">
            {harnesses.length > 0 ? (
              harnesses.map((row) => (
                <li key={row.tool ?? row.prefix}>
                  <span className="kv-list__key">{row.prefix ?? row.tool ?? 'unknown'}</span>
                  <StatusBadge label={row.state ?? 'UNKNOWN'} tone={toneForHarnessSync(row.state)} title={row.detail} />
                  <span className="kv-list__detail" title={row.detail}>
                    {row.detail ?? ''}
                  </span>
                </li>
              ))
            ) : (
              <li className="kv-list__empty">no harness rows reported</li>
            )}
          </ul>
        </div>
        <div className="columns__col">
          <h3>Environment</h3>
          <ul className="kv-list">
            <li>
              <span className="kv-list__key">python</span>
              <StatusBadge label={environment?.python?.state ?? 'UNKNOWN'} tone={toneForWiringState(environment?.python?.state)} />
              <span className="kv-list__detail">{environment?.python?.version ?? ''}</span>
            </li>
            <li>
              <span className="kv-list__key">latex</span>
              <StatusBadge label={environment?.latex?.state ?? 'UNKNOWN'} tone={toneForWiringState(environment?.latex?.state)} />
              <span className="kv-list__detail">{environment?.latex?.engine ?? 'no engine found'}</span>
            </li>
            <li>
              <span className="kv-list__key">node</span>
              <StatusBadge label={environment?.node?.state ?? 'UNKNOWN'} tone={toneForWiringState(environment?.node?.state)} />
              <span className="kv-list__detail">{environment?.node?.executable ?? 'not on PATH'}</span>
            </li>
            {packages.map((pkg) => (
              <li key={pkg.name ?? 'package'}>
                <span className="kv-list__key">pkg {pkg.name ?? '?'}</span>
                <StatusBadge label={pkg.state ?? 'UNKNOWN'} tone={toneForWiringState(pkg.state)} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

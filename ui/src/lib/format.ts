/** Small presentation helpers shared by the dashboard panels. */

/** Render an unknown backend value as text, or `null` when it carries nothing. */
export function asText(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') return value.trim() === '' ? null : value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    const parts = value.map(asText).filter((part): part is string => part !== null);
    return parts.length ? parts.join(', ') : null;
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return null;
    }
  }
  return null;
}

/** Clamp a fraction into `[0, 1]`; a non-finite input becomes `0`. */
function clampFraction(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function formatPercent(fraction: number): string {
  return `${Math.round(clampFraction(fraction) * 100)}%`;
}

export function formatCount(value: number | undefined | null): string {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : '—';
}

/** `2024-01-01T10:00:00Z` -> `10:00:00`; anything unparsable is echoed raw. */
export function formatTime(timestamp: string | undefined | null): string {
  if (!timestamp) return '—';
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return timestamp;
  return parsed.toLocaleTimeString();
}

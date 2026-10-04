export const TABS = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'health', label: 'Health' },
  { id: 'sections', label: 'Sections' },
  { id: 'artifacts', label: 'Artifacts' },
] as const;

export type TabId = (typeof TABS)[number]['id'];
export const DEFAULT_TAB: TabId = 'pipeline';

export interface HashRoute {
  tab: TabId;
  /** Diagram element id (`<kind>:<raw id>`), or null when nothing is selected. */
  el: string | null;
}

/**
 * Parse `#<tab>` or `#<tab>?el=<encoded element id>`. Unknown tabs fall back to
 * the default tab (and drop the element); a missing or malformed `el` is null.
 */
export function parseHash(hash: string): HashRoute {
  const fragment = hash.replace(/^#/, '');
  const queryAt = fragment.indexOf('?');
  const tabPart = queryAt === -1 ? fragment : fragment.slice(0, queryAt);
  const query = queryAt === -1 ? '' : fragment.slice(queryAt + 1);
  const tab = TABS.find((entry) => entry.id === tabPart);
  if (!tab) return { tab: DEFAULT_TAB, el: null };
  const match = /(?:^|&)el=([^&]*)/.exec(query);
  return { tab: tab.id, el: match ? decodeElement(match[1]) : null };
}

function decodeElement(raw: string): string | null {
  try {
    const value = decodeURIComponent(raw);
    return value.length > 0 ? value : null;
  } catch {
    return null; // malformed percent-encoding
  }
}

/** Inverse of `parseHash`; element ids are encoded with encodeURIComponent. */
export function formatHash(tab: TabId, el?: string | null): string {
  return el ? `#${tab}?el=${encodeURIComponent(el)}` : `#${tab}`;
}

// Pure helpers for scripts/command-center-visual-check.mjs. Nothing here touches
// the network, the filesystem or a browser, so they run in the Node CI job.

export const DEFAULT_TABS = ['pipeline', 'health', 'sections', 'artifacts', 'history', 'preview', 'atlas'];
export const DEFAULT_VIEWPORTS = [
  { width: 1280, height: 800 },
  { width: 1600, height: 1000 },
  { width: 700, height: 900 },
];

const DEFAULTS = {
  url: 'http://127.0.0.1:8099/',
  timeoutMs: 20000,
  chromium: '/usr/bin/chromium',
  dragCheck: false,
  fullPage: false,
  clickCheck: false,
};

function takeValue(argv, index, flag) {
  const value = argv[index + 1];
  if (value === undefined || value.startsWith('--')) {
    throw new Error(`${flag} needs a value`);
  }
  return value;
}

function parseViewport(text) {
  const match = /^(\d+)x(\d+)$/.exec(text);
  if (!match) throw new Error(`invalid viewport "${text}", expected WIDTHxHEIGHT`);
  return { width: Number(match[1]), height: Number(match[2]) };
}

/** Parse the checker's command line. `--out` is required. */
export function parseArgs(argv) {
  const parsed = {
    ...DEFAULTS,
    out: null,
    tabs: [...DEFAULT_TABS],
    viewports: DEFAULT_VIEWPORTS.map((viewport) => ({ ...viewport })),
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    switch (flag) {
      case '--out':
        parsed.out = takeValue(argv, index, flag);
        index += 1;
        break;
      case '--url':
        parsed.url = new URL(takeValue(argv, index, flag)).href;
        index += 1;
        break;
      case '--timeout': {
        const seconds = Number(takeValue(argv, index, flag));
        if (!Number.isFinite(seconds) || seconds <= 0) {
          throw new Error('--timeout must be a positive number of seconds');
        }
        parsed.timeoutMs = Math.round(seconds * 1000);
        index += 1;
        break;
      }
      case '--tabs':
        parsed.tabs = takeValue(argv, index, flag).split(',').filter(Boolean);
        index += 1;
        break;
      case '--viewports':
        parsed.viewports = takeValue(argv, index, flag).split(',').filter(Boolean).map(parseViewport);
        index += 1;
        break;
      case '--chromium':
        parsed.chromium = takeValue(argv, index, flag);
        index += 1;
        break;
      case '--drag-check':
        parsed.dragCheck = true;
        break;
      case '--full-page':
        parsed.fullPage = true;
        break;
      case '--click-check':
        parsed.clickCheck = true;
        break;
      default:
        throw new Error(`unknown option ${flag}`);
    }
  }
  if (!parsed.out) throw new Error('--out DIR is required');
  return parsed;
}

/** `document.body.dataset.ready` values that mean the app finished loading. */
export function isReadyValue(value) {
  return value === '1' || value === 'error';
}

// The SSE stream reconnects on its own; Chromium logs each drop as a console
// error that says nothing about the page being broken.
const EVENT_SOURCE_NOISE = [/\/api\/events/, /EventSource/];

export function isAllowedConsoleMessage(text) {
  return EVENT_SOURCE_NOISE.some((pattern) => pattern.test(text));
}

/** Console errors that should fail the check. */
export function classifyConsoleEntries(entries) {
  return entries.filter((entry) => entry.level === 'error' && !isAllowedConsoleMessage(entry.text));
}

/** Milliseconds from navigation to readiness, or null when never ready. */
export function timeToFirstData(startMs, readyMs) {
  if (readyMs === null || readyMs === undefined) return null;
  return Math.max(0, readyMs - startMs);
}

export function shotName(tab, viewport) {
  return `${tab}-${viewport.width}x${viewport.height}.png`;
}

/** Centre point of a DOMRect-like object. */
export function rectCenter(rect) {
  return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
}

/** One element id per kind (first stage, gate, section, edge) for the click check. */
export function pickClickTargets({ nodes, edges }) {
  const picked = {};
  for (const kind of ['stage', 'gate', 'section']) {
    const id = nodes.find((candidate) => candidate.startsWith(`${kind}:`));
    if (id) picked[kind] = id;
  }
  if (edges.length > 0) picked.edge = edges[0];
  return picked;
}

export function clickShotName(kind, viewport) {
  return `click-${kind}-${viewport.width}x${viewport.height}.png`;
}

/**
 * Selector that proves a lazily fetched tab has rendered its content (or its
 * inline error); null for tabs that paint from the already-ready state.
 */
export function tabContentSelector(tab) {
  if (tab === 'preview') return '.preview__layout, .preview [role="alert"]';
  if (tab === 'atlas') return '.atlas__layout, .atlas [role="alert"]';
  return null;
}

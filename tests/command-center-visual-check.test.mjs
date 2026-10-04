import assert from 'node:assert/strict';
import test from 'node:test';

import {
  DEFAULT_TABS,
  DEFAULT_VIEWPORTS,
  classifyConsoleEntries,
  isAllowedConsoleMessage,
  isReadyValue,
  clickShotName,
  parseArgs,
  pickClickTargets,
  rectCenter,
  shotName,
  timeToFirstData,
} from '../scripts/lib/visual-check.mjs';

test('parseArgs applies defaults and requires --out', () => {
  const parsed = parseArgs(['--out', '/tmp/shots']);
  assert.equal(parsed.out, '/tmp/shots');
  assert.equal(parsed.url, 'http://127.0.0.1:8099/');
  assert.equal(parsed.timeoutMs, 20000);
  assert.equal(parsed.dragCheck, false);
  assert.equal(parsed.fullPage, false);
  assert.equal(parsed.clickCheck, false);
  assert.deepEqual(parsed.tabs, DEFAULT_TABS);
  assert.deepEqual(parsed.viewports, DEFAULT_VIEWPORTS);
  assert.throws(() => parseArgs([]), /--out/);
});

test('the default tab list covers every dashboard tab, History included', () => {
  assert.deepEqual(DEFAULT_TABS, ['pipeline', 'health', 'sections', 'artifacts', 'history']);
});

test('parseArgs reads every option', () => {
  const parsed = parseArgs([
    '--out', '/x', '--url', 'http://localhost:5173', '--timeout', '5',
    '--tabs', 'pipeline,health', '--viewports', '800x600,1024x768',
    '--chromium', '/opt/chrome', '--drag-check', '--full-page', '--click-check',
  ]);
  assert.equal(parsed.url, 'http://localhost:5173/');
  assert.equal(parsed.timeoutMs, 5000);
  assert.deepEqual(parsed.tabs, ['pipeline', 'health']);
  assert.deepEqual(parsed.viewports, [
    { width: 800, height: 600 },
    { width: 1024, height: 768 },
  ]);
  assert.equal(parsed.chromium, '/opt/chrome');
  assert.equal(parsed.dragCheck, true);
  assert.equal(parsed.fullPage, true);
  assert.equal(parsed.clickCheck, true);
});

test('parseArgs rejects unknown flags, bad numbers and bad viewports', () => {
  assert.throws(() => parseArgs(['--out', '/x', '--nope']), /unknown option/);
  assert.throws(() => parseArgs(['--out', '/x', '--timeout', 'abc']), /--timeout/);
  assert.throws(() => parseArgs(['--out', '/x', '--viewports', '1280']), /viewport/);
  assert.throws(() => parseArgs(['--out']), /--out/);
});

test('isReadyValue accepts only "1" and "error"', () => {
  assert.equal(isReadyValue('1'), true);
  assert.equal(isReadyValue('error'), true);
  assert.equal(isReadyValue(undefined), false);
  assert.equal(isReadyValue(null), false);
  assert.equal(isReadyValue(''), false);
  assert.equal(isReadyValue('0'), false);
});

test('isAllowedConsoleMessage tolerates only EventSource reconnect noise', () => {
  assert.equal(
    isAllowedConsoleMessage('Failed to load resource: net::ERR_INCOMPLETE_CHUNKED_ENCODING http://127.0.0.1:8099/api/events'),
    true,
  );
  assert.equal(isAllowedConsoleMessage('EventSource connection to http://x/api/events failed'), true);
  assert.equal(isAllowedConsoleMessage('Uncaught TypeError: x is undefined'), false);
  assert.equal(isAllowedConsoleMessage('Failed to load resource: the server responded with a status of 500 (/api/state)'), false);
});

test('classifyConsoleEntries keeps only disallowed errors', () => {
  const entries = [
    { level: 'error', text: 'Uncaught ReferenceError: foo' },
    { level: 'error', text: 'EventSource connection to /api/events failed' },
    { level: 'warning', text: 'deprecated thing' },
    { level: 'log', text: 'hello' },
  ];
  assert.deepEqual(classifyConsoleEntries(entries), [entries[0]]);
});

test('timeToFirstData measures from navigation to readiness', () => {
  assert.equal(timeToFirstData(1000, 1450), 450);
  assert.equal(timeToFirstData(1000, null), null);
  assert.equal(timeToFirstData(1000, 900), 0);
});

test('shotName is filesystem safe and carries tab and viewport', () => {
  assert.equal(shotName('pipeline', { width: 1280, height: 800 }), 'pipeline-1280x800.png');
});

test('rectCenter returns the centre of a bounding rectangle', () => {
  assert.deepEqual(rectCenter({ x: 10, y: 20, width: 100, height: 40 }), { x: 60, y: 40 });
});

test('pickClickTargets takes the first stage, gate, section and edge id', () => {
  const picked = pickClickTargets({
    nodes: ['gate:g1', 'stage:a', 'section:Related Work', 'stage:b', 'section:x'],
    edges: ['stage:a->stage:b', 'stage:a->gate:g1'],
  });
  assert.deepEqual(picked, {
    stage: 'stage:a',
    gate: 'gate:g1',
    section: 'section:Related Work',
    edge: 'stage:a->stage:b',
  });
});

test('pickClickTargets leaves a kind out when the diagram has none of it', () => {
  assert.deepEqual(pickClickTargets({ nodes: ['stage:a'], edges: [] }), { stage: 'stage:a' });
});

test('clickShotName names the screenshot by kind and viewport', () => {
  assert.equal(clickShotName('gate', { width: 1280, height: 800 }), 'click-gate-1280x800.png');
});

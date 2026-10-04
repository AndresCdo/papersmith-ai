import assert from 'node:assert/strict';
import test from 'node:test';

import {
  DEFAULT_TABS,
  DEFAULT_VIEWPORTS,
  classifyConsoleEntries,
  isAllowedConsoleMessage,
  isReadyValue,
  parseArgs,
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
  assert.deepEqual(parsed.tabs, DEFAULT_TABS);
  assert.deepEqual(parsed.viewports, DEFAULT_VIEWPORTS);
  assert.throws(() => parseArgs([]), /--out/);
});

test('parseArgs reads every option', () => {
  const parsed = parseArgs([
    '--out', '/x', '--url', 'http://localhost:5173', '--timeout', '5',
    '--tabs', 'pipeline,health', '--viewports', '800x600,1024x768',
    '--chromium', '/opt/chrome', '--drag-check', '--full-page',
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

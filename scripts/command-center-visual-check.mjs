#!/usr/bin/env node
// Visual checker for the Paper Command Center. Drives a headless Chromium over
// the DevTools protocol (Node's global WebSocket, no dependencies), opens every
// tab at each viewport, waits for the app's readiness signal, captures PNGs and
// reports time-to-first-data. A development tool: CI runners have no Chromium.
//
//   node scripts/command-center-visual-check.mjs --out DIR [--url URL]
//        [--timeout SECONDS] [--tabs a,b] [--viewports 1280x800,1600x1000,700x900]
//        [--chromium PATH] [--drag-check] [--full-page] [--click-check]

import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

import {
  classifyConsoleEntries,
  clickShotName,
  isReadyValue,
  parseArgs,
  pickClickTargets,
  rectCenter,
  shotName,
  tabContentSelector,
  tabFrameReadyExpression,
  timeToFirstData,
} from './lib/visual-check.mjs';

// Selector the detail panel will carry once the diagram is clickable; the drag
// check asserts that a canvas drag never opens it.
const DETAIL_PANEL_SELECTOR = '[data-testid="element-detail-panel"]';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

class Cdp {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = [];
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id !== undefined) {
        const entry = this.pending.get(message.id);
        if (!entry) return;
        this.pending.delete(message.id);
        if (message.error) entry.reject(new Error(`${entry.method}: ${message.error.message}`));
        else entry.resolve(message.result);
      } else {
        for (const listener of this.listeners) listener(message);
      }
    });
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', () => reject(new Error(`cannot open ${url}`)), { once: true });
    });
    return new Cdp(socket);
  }

  send(method, params = {}, sessionId) {
    const id = this.nextId++;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, method });
      this.socket.send(JSON.stringify(payload));
    });
  }

  onEvent(listener) {
    this.listeners.push(listener);
  }

  close() {
    this.socket.close();
  }
}

async function launchChromium(binary, profileDir) {
  const child = spawn(
    binary,
    [
      '--headless=new',
      '--no-sandbox',
      '--disable-gpu',
      '--hide-scrollbars',
      // A page kept in the back/forward cache keeps its EventSource open; after
      // about eight loads the browser's per-host connection limit starves the next page.
      '--disable-features=BackForwardCache',
      '--remote-debugging-port=0',
      `--user-data-dir=${profileDir}`,
      'about:blank',
    ],
    { stdio: 'ignore' },
  );
  const portFile = path.join(profileDir, 'DevToolsActivePort');
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      const [port, wsPath] = (await readFile(portFile, 'utf8')).trim().split('\n');
      if (port && wsPath) return { child, wsUrl: `ws://127.0.0.1:${port}${wsPath}` };
    } catch {
      // The file appears once the browser is listening.
    }
    await sleep(100);
  }
  child.kill();
  throw new Error(`Chromium did not expose a DevTools port (${binary})`);
}

async function evaluate(cdp, sessionId, expression) {
  const result = await cdp.send(
    'Runtime.evaluate',
    { expression, returnByValue: true, awaitPromise: true },
    sessionId,
  );
  if (result.exceptionDetails) {
    throw new Error(`evaluate failed: ${result.exceptionDetails.text}`);
  }
  return result.result.value;
}

async function waitFor(cdp, sessionId, expression, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const value = await evaluate(cdp, sessionId, expression);
    if (value) return value;
    await sleep(100);
  }
  throw new Error(`timed out after ${timeoutMs} ms waiting for ${label}`);
}

const twoFrames = (cdp, sessionId) =>
  evaluate(
    cdp,
    sessionId,
    'new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))))',
  );

async function dragCheck(cdp, sessionId) {
  const box = await evaluate(
    cdp,
    sessionId,
    `(() => { const el = document.querySelector('.react-flow__pane') ?? document.querySelector('.react-flow'); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; })()`,
  );
  if (!box) return { ok: false, detail: 'no canvas found to drag across' };
  const startX = box.x + box.width * 0.2;
  const endX = box.x + box.width * 0.7;
  const y = box.y + box.height * 0.5;
  const mouse = (type, x, extra = {}) =>
    cdp.send('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1, ...extra }, sessionId);
  await mouse('mouseMoved', startX, { button: 'none', clickCount: 0 });
  await mouse('mousePressed', startX);
  for (let step = 1; step <= 10; step += 1) {
    await mouse('mouseMoved', startX + ((endX - startX) * step) / 10, { buttons: 1 });
  }
  await mouse('mouseReleased', endX);
  await twoFrames(cdp, sessionId);
  const opened = await evaluate(cdp, sessionId, `document.querySelector(${JSON.stringify(DETAIL_PANEL_SELECTOR)}) !== null`);
  return { ok: !opened, detail: opened ? 'a detail panel opened after a drag' : 'no detail panel opened' };
}

const q = (value) => JSON.stringify(value);
const PANEL_TITLE = `document.querySelector(${q(DETAIL_PANEL_SELECTOR)})?.querySelector('h3')?.textContent ?? null`;

async function pointer(cdp, sessionId, type, point) {
  await cdp.send(
    'Input.dispatchMouseEvent',
    { type, x: point.x, y: point.y, button: type === 'mouseMoved' ? 'none' : 'left', clickCount: type === 'mouseMoved' ? 0 : 1 },
    sessionId,
  );
}

async function clickAt(cdp, sessionId, point) {
  await pointer(cdp, sessionId, 'mouseMoved', point);
  await pointer(cdp, sessionId, 'mousePressed', point);
  await pointer(cdp, sessionId, 'mouseReleased', point);
}

async function pressKey(cdp, sessionId, key) {
  const keys = { Enter: { code: 'Enter', vk: 13, text: '\r' }, Escape: { code: 'Escape', vk: 27 } }[key];
  const base = { key, code: keys.code, windowsVirtualKeyCode: keys.vk, nativeVirtualKeyCode: keys.vk };
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', ...base, text: keys.text }, sessionId);
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', ...base }, sessionId);
}

// Screen point to click for a node (centre of its wrapper) or an edge (midpoint
// of its path), after scrolling it into view. An edge that another element
// covers at that point is skipped by the caller choosing the next candidate.
const pointOf = (kind, id) => `(() => {
  const id = ${q(id)};
  if (${q(kind)} === 'edge') {
    const edge = document.querySelector('.react-flow__edge[data-id=' + CSS.escape(id) + ']');
    const path = edge && edge.querySelector('path.react-flow__edge-path');
    if (!path) return null;
    path.scrollIntoView({ block: 'center', inline: 'center' });
    const len = path.getTotalLength();
    const pt = path.getPointAtLength(len / 2);
    const m = path.getScreenCTM();
    const x = m.a * pt.x + m.c * pt.y + m.e;
    const y = m.b * pt.x + m.d * pt.y + m.f;
    const hit = document.elementFromPoint(x, y);
    const owner = hit && hit.closest('.react-flow__edge');
    return owner && owner.dataset.id === id ? { x, y } : { covered: true };
  }
  const node = document.querySelector('.react-flow__node[data-id=' + CSS.escape(id) + ']');
  if (!node) return null;
  node.scrollIntoView({ block: 'center', inline: 'center' });
  const r = node.getBoundingClientRect();
  return { rect: { x: r.x, y: r.y, width: r.width, height: r.height } };
})()`;

const closePanel = async (cdp, sessionId) => {
  await pressKey(cdp, sessionId, 'Escape');
  await sleep(150);
};

// Real-browser selection check: click one stage, gate, section and edge, then
// select a node and an edge from the keyboard, asserting the panel each time.
async function clickCheck(cdp, sessionId, options, viewport) {
  const failures = [];
  const log = [];
  const size = `${viewport.width}x${viewport.height}`;
  const ids = await evaluate(
    cdp,
    sessionId,
    `({ nodes: [...document.querySelectorAll('.react-flow__node')].map((n) => n.dataset.id),
        edges: [...document.querySelectorAll('.react-flow__edge')].map((e) => e.dataset.id) })`,
  );
  const targets = pickClickTargets(ids);
  const expectTitle = async (kind, id, mode) => {
    await waitFor(cdp, sessionId, `${PANEL_TITLE} !== null`, 3000, `${mode} ${id} panel`).catch(() => {});
    const title = await evaluate(cdp, sessionId, PANEL_TITLE);
    const wanted =
      kind === 'edge'
        ? 'Connection'
        : await evaluate(
            cdp,
            sessionId,
            `document.querySelector('.react-flow__node[data-id=' + CSS.escape(${q(id)}) + '] .dag-node__title')?.textContent ?? null`,
          );
    const hash = await evaluate(cdp, sessionId, 'location.hash');
    const ok = title !== null && title === (wanted ?? title) && hash.includes(`el=${encodeURIComponent(id)}`);
    log.push({ viewport: size, mode, kind, id, title, hash, ok });
    if (!ok) failures.push(`click check ${size} ${mode} ${kind} ${id}: panel title ${q(title)}, expected ${q(wanted)}, hash ${hash}`);
    return ok;
  };

  for (const [kind, id] of Object.entries(targets)) {
    const locate = async (k, i) => {
      const found = await evaluate(cdp, sessionId, pointOf(k, i));
      return found?.rect ? rectCenter(found.rect) : found;
    };
    let point = await locate(kind, id);
    if (!point || point.covered) {
      // Fall back to another edge whose midpoint is not covered.
      const others = kind === 'edge' ? ids.edges.slice(1) : [];
      for (const other of others) {
        point = await locate('edge', other);
        if (point && !point.covered) {
          targets.edge = other;
          break;
        }
      }
    }
    const target = kind === 'edge' ? targets.edge : id;
    if (!point || point.covered) {
      failures.push(`click check ${size}: no clickable point for ${kind} ${id}`);
      continue;
    }
    await clickAt(cdp, sessionId, point);
    await twoFrames(cdp, sessionId);
    if (await expectTitle(kind, target, 'click')) {
      const file = path.join(options.out, clickShotName(kind, viewport));
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png' }, sessionId);
      await writeFile(file, Buffer.from(shot.data, 'base64'));
      log.push({ viewport: size, shot: file });
    }
    await closePanel(cdp, sessionId);
    const stillOpen = await evaluate(cdp, sessionId, `document.querySelector(${q(DETAIL_PANEL_SELECTOR)}) !== null || location.hash.includes('el=')`);
    if (stillOpen) failures.push(`click check ${size}: Escape did not close the panel after ${kind} ${id}`);
  }

  // Keyboard: focus a node wrapper and an edge wrapper, press Enter.
  for (const [kind, id] of [['stage', targets.stage], ['edge', targets.edge]]) {
    if (!id) continue;
    const selector = kind === 'edge' ? '.react-flow__edge' : '.react-flow__node';
    const focused = await evaluate(
      cdp,
      sessionId,
      `(() => { const el = document.querySelector(${q(selector)} + '[data-id=' + CSS.escape(${q(id)}) + ']'); if (!el) return false; el.focus({ preventScroll: true }); return document.activeElement === el; })()`,
    );
    if (!focused) {
      failures.push(`click check ${size}: could not focus ${kind} ${id}`);
      continue;
    }
    await pressKey(cdp, sessionId, 'Enter');
    await twoFrames(cdp, sessionId);
    await expectTitle(kind, id, 'keyboard');
    await closePanel(cdp, sessionId);
  }
  return { failures, log };
}

async function run(options) {
  await mkdir(options.out, { recursive: true });
  const profileDir = await mkdtemp(path.join(tmpdir(), 'cc-visual-check-'));
  const { child, wsUrl } = await launchChromium(options.chromium, profileDir);
  const cdp = await Cdp.connect(wsUrl);
  const report = { url: options.url, shots: [], timings: [], consoleErrors: [], dragChecks: [], clickChecks: [], failures: [] };
  const consoleByTarget = new Map();

  try {
    const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
    consoleByTarget.set(sessionId, []);
    cdp.onEvent((message) => {
      if (message.sessionId !== sessionId) return;
      const bucket = consoleByTarget.get(sessionId);
      if (message.method === 'Runtime.consoleAPICalled') {
        const text = message.params.args.map((arg) => arg.value ?? arg.description ?? '').join(' ');
        bucket.push({ level: message.params.type === 'warning' ? 'warning' : message.params.type, text });
      } else if (message.method === 'Runtime.exceptionThrown') {
        bucket.push({ level: 'error', text: message.params.exceptionDetails.exception?.description ?? message.params.exceptionDetails.text });
      } else if (message.method === 'Log.entryAdded') {
        bucket.push({ level: message.params.entry.level, text: `${message.params.entry.text} ${message.params.entry.url ?? ''}`.trim() });
      }
    });
    for (const domain of ['Page', 'Runtime', 'Log']) await cdp.send(`${domain}.enable`, {}, sessionId);

    for (const viewport of options.viewports) {
      await cdp.send(
        'Emulation.setDeviceMetricsOverride',
        { ...viewport, deviceScaleFactor: 1, mobile: false },
        sessionId,
      );
      for (const tab of options.tabs) {
        const target = new URL(options.url);
        target.hash = tab;
        const started = Date.now();
        // A distinct blank page first, so a same-document hash change cannot
        // reuse state from the previous tab or viewport.
        await cdp.send('Page.navigate', { url: 'about:blank' }, sessionId);
        await cdp.send('Page.navigate', { url: target.href }, sessionId);
        try {
          await waitFor(
            cdp,
            sessionId,
            `(() => { const v = document.body && document.body.dataset.ready; return v === '1' || v === 'error' ? v : null; })()`,
            options.timeoutMs,
            'document.body.dataset.ready',
          );
          const readyValue = await evaluate(cdp, sessionId, 'document.body.dataset.ready');
          if (!isReadyValue(readyValue)) throw new Error(`unexpected ready value ${readyValue}`);
          const readyAt = Date.now();
          if (readyValue === 'error') report.failures.push(`${tab} ${viewport.width}x${viewport.height}: data-ready is "error"`);
          if (tab === 'pipeline') {
            await waitFor(
              cdp,
              sessionId,
              `document.querySelector('.react-flow__node, .panel--empty') !== null`,
              options.timeoutMs,
              'a .react-flow__node or the empty state',
            );
          }
          const contentSelector = tabContentSelector(tab);
          if (contentSelector) {
            await waitFor(
              cdp,
              sessionId,
              `document.querySelector(${JSON.stringify(contentSelector)}) !== null`,
              options.timeoutMs,
              `the ${tab} tab content`,
            );
          }
          const frameReady = tabFrameReadyExpression(tab);
          if (frameReady) await waitFor(cdp, sessionId, frameReady, options.timeoutMs, `the ${tab} tab frame`);
          await twoFrames(cdp, sessionId);
          const capture = { format: 'png' };
          if (options.fullPage) {
            // Capture the whole scrollable page, not just the first viewport.
            const metrics = await cdp.send('Page.getLayoutMetrics', {}, sessionId);
            const size = metrics.cssContentSize ?? metrics.contentSize;
            capture.captureBeyondViewport = true;
            capture.clip = { x: 0, y: 0, width: size.width, height: Math.ceil(size.height), scale: 1 };
          }
          const shot = await cdp.send('Page.captureScreenshot', capture, sessionId);
          const file = path.join(options.out, shotName(tab, viewport));
          await writeFile(file, Buffer.from(shot.data, 'base64'));
          report.shots.push(file);
          // Headless Chromium's PDF viewer frame stalls the next Page.navigate
          // on the same session; drop embedded frames once the shot is taken.
          await evaluate(cdp, sessionId, "document.querySelectorAll('iframe').forEach((frame) => frame.remove())");
          report.timings.push({ tab, viewport: `${viewport.width}x${viewport.height}`, ms: timeToFirstData(started, readyAt) });
          if (options.dragCheck && tab === 'pipeline') {
            const result = await dragCheck(cdp, sessionId);
            report.dragChecks.push({ viewport: `${viewport.width}x${viewport.height}`, ...result });
            if (!result.ok) report.failures.push(`drag check ${viewport.width}x${viewport.height}: ${result.detail}`);
          }
          if (options.clickCheck && tab === 'pipeline') {
            const result = await clickCheck(cdp, sessionId, options, viewport);
            report.clickChecks.push(...result.log);
            report.failures.push(...result.failures);
          }
        } catch (error) {
          report.failures.push(`${tab} ${viewport.width}x${viewport.height}: ${error.message}`);
        }
      }
    }
    report.consoleErrors = classifyConsoleEntries(consoleByTarget.get(sessionId));
    for (const entry of report.consoleErrors) report.failures.push(`console error: ${entry.text}`);
  } finally {
    cdp.close();
    child.kill();
    await sleep(200);
    await rm(profileDir, { recursive: true, force: true }).catch(() => {});
  }
  return report;
}

async function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(`command-center-visual-check: ${error.message}`);
    process.exit(2);
  }
  const report = await run(options);
  for (const timing of report.timings) {
    console.log(`time-to-first-data ${timing.tab} ${timing.viewport}: ${timing.ms} ms`);
  }
  for (const shot of report.shots) console.log(`screenshot ${shot}`);
  for (const result of report.dragChecks) {
    console.log(`drag-check ${result.viewport}: ${result.ok ? 'ok' : 'FAIL'} (${result.detail})`);
  }
  for (const entry of report.clickChecks) {
    if (entry.shot) console.log(`click-check screenshot ${entry.shot}`);
    else console.log(`click-check ${entry.viewport} ${entry.mode} ${entry.kind} ${entry.id}: ${entry.ok ? 'ok' : 'FAIL'} (panel "${entry.title}")`);
  }
  if (report.failures.length > 0) {
    for (const failure of report.failures) console.error(`FAIL ${failure}`);
    process.exit(1);
  }
  console.log(`OK ${report.shots.length} screenshot(s), no disallowed console errors`);
}

main().catch((error) => {
  console.error(`command-center-visual-check: ${error.stack ?? error}`);
  process.exit(1);
});

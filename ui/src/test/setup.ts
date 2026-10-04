import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Globals are off, so Testing Library cannot register its own cleanup.
afterEach(() => cleanup());

// React Flow measures nodes through ResizeObserver; jsdom has no layout, so the
// stub reports a fixed non-zero size as soon as an element is observed. Without
// it handle bounds stay zero and edges are never rendered.
class ResizeObserverStub {
  constructor(private readonly callback: ResizeObserverCallback) {}

  observe(target: Element) {
    const rect = { x: 0, y: 0, top: 0, left: 0, right: 200, bottom: 100, width: 200, height: 100 };
    const entry = {
      target,
      contentRect: { ...rect, toJSON: () => rect },
      borderBoxSize: [{ inlineSize: 200, blockSize: 100 }],
      contentBoxSize: [{ inlineSize: 200, blockSize: 100 }],
      devicePixelContentBoxSize: [{ inlineSize: 200, blockSize: 100 }],
    } as unknown as ResizeObserverEntry;
    this.callback([entry], this as unknown as ResizeObserver);
  }

  unobserve() {}
  disconnect() {}
}

class DOMMatrixReadOnlyStub {
  m22: number;
  constructor(transform?: string) {
    const scale = transform?.match(/scale\(([\d.]+)\)/)?.[1];
    this.m22 = scale ? Number(scale) : 1;
  }
}

globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
globalThis.DOMMatrixReadOnly = DOMMatrixReadOnlyStub as unknown as typeof DOMMatrixReadOnly;

Object.defineProperties(HTMLElement.prototype, {
  offsetWidth: { configurable: true, get: () => 200 },
  offsetHeight: { configurable: true, get: () => 100 },
});

Element.prototype.getBoundingClientRect = function getBoundingClientRect() {
  const rect = { x: 0, y: 0, top: 0, left: 0, right: 200, bottom: 100, width: 200, height: 100 };
  return { ...rect, toJSON: () => rect } as DOMRect;
};

import { describe, expect, it } from 'vitest';
import {
  applyAppend,
  applyPage,
  emptyHistory,
  filterEntries,
  groupForDisplay,
  lastSeq,
  MAX_HELD_ENTRIES,
} from './history';
import type { HistoryEntry, HistoryPage } from '../types';

function entry(seq: number, extra: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    id: `boot-${seq}`,
    boot_id: 'boot',
    seq,
    ts: 1000 + seq,
    kind: 'section_status',
    element_id: 'section:intro',
    summary: `change ${seq}`,
    before: null,
    after: null,
    ...extra,
  };
}

function page(entries: HistoryEntry[], extra: Partial<HistoryPage> = {}): HistoryPage {
  return { boot_id: 'boot', entries, has_more: false, reset: false, gap: false, ...extra };
}

describe('history state', () => {
  it('starts empty with no cursor', () => {
    expect(emptyHistory.entries).toEqual([]);
    expect(lastSeq(emptyHistory)).toBe(0);
  });

  it('appends a page and moves the cursor to the last seq', () => {
    const next = applyPage(emptyHistory, page([entry(1), entry(2)]));
    expect(next.bootId).toBe('boot');
    expect(lastSeq(next)).toBe(2);
  });

  it('dedups pages by id', () => {
    const first = applyPage(emptyHistory, page([entry(1), entry(2)]));
    const second = applyPage(first, page([entry(2), entry(3)]));
    expect(second.entries.map((e) => e.seq)).toEqual([1, 2, 3]);
  });

  it('discards what it holds on a reset and keeps the new page', () => {
    const first = applyPage(emptyHistory, page([entry(1), entry(2)]));
    const other = [entry(1, { boot_id: 'new', id: 'new-1' })];
    const next = applyPage(first, page(other, { boot_id: 'new', reset: true }));
    expect(next.bootId).toBe('new');
    expect(next.entries.map((e) => e.id)).toEqual(['new-1']);
  });

  it('records a gap and keeps it sticky across later pages', () => {
    const first = applyPage(emptyHistory, page([entry(5)], { gap: true }));
    expect(first.gap).toBe(true);
    expect(applyPage(first, page([entry(6)])).gap).toBe(true);
  });

  it('appends a live entry only when seq = last + 1', () => {
    const base = applyPage(emptyHistory, page([entry(1)]));
    const ok = applyAppend(base, entry(2));
    expect(ok.catchUp).toBe(false);
    expect(lastSeq(ok.state)).toBe(2);
  });

  it('asks for a catch-up on a seq jump and does not append', () => {
    const base = applyPage(emptyHistory, page([entry(1)]));
    const jump = applyAppend(base, entry(4));
    expect(jump.catchUp).toBe(true);
    expect(lastSeq(jump.state)).toBe(1);
  });

  it('ignores a duplicate live entry', () => {
    const base = applyPage(emptyHistory, page([entry(1), entry(2)]));
    const dup = applyAppend(base, entry(2));
    expect(dup.catchUp).toBe(false);
    expect(dup.state.entries).toHaveLength(2);
  });

  it('asks for a catch-up when the live entry belongs to another boot', () => {
    const base = applyPage(emptyHistory, page([entry(1)]));
    const other = applyAppend(base, entry(2, { boot_id: 'new', id: 'new-2' }));
    expect(other.catchUp).toBe(true);
  });

  it('accepts the first live entry when nothing is loaded and seq is 1', () => {
    const first = applyAppend(emptyHistory, entry(1));
    expect(first.catchUp).toBe(false);
    expect(lastSeq(first.state)).toBe(1);
  });
});

describe('filterEntries', () => {
  const entries = [
    entry(1),
    entry(2, { kind: 'gate', element_id: 'gate:g' }),
    entry(3, { kind: 'health', element_id: null }),
  ];

  it('filters by kind', () => {
    expect(filterEntries(entries, { kind: 'gate', element: null }).map((e) => e.seq)).toEqual([2]);
  });

  it('filters by element', () => {
    expect(filterEntries(entries, { kind: null, element: 'section:intro' }).map((e) => e.seq)).toEqual([1]);
  });

  it('keeps everything with no filter', () => {
    expect(filterEntries(entries, { kind: null, element: null })).toHaveLength(3);
  });
});

describe('groupForDisplay', () => {
  const words = (seq: number, element = 'section:intro', from = seq - 1, to = seq) =>
    entry(seq, { kind: 'section_words', element_id: element, before: from, after: to, summary: `w ${seq}` });

  it('returns newest first', () => {
    const rows = groupForDisplay([entry(1), entry(2)]);
    expect(rows.map((r) => r.entries[0].seq)).toEqual([2, 1]);
  });

  it('groups consecutive word-count entries of one section', () => {
    const rows = groupForDisplay([words(1), words(2), words(3)]);
    expect(rows).toHaveLength(1);
    expect(rows[0].entries.map((e) => e.seq)).toEqual([3, 2, 1]);
    expect(rows[0].grouped).toBe(true);
  });

  it('does not group across another section or an interleaved kind', () => {
    const rows = groupForDisplay([words(1), words(2, 'section:other'), words(3), entry(4), words(5), words(6)]);
    expect(rows.map((r) => r.entries.map((e) => e.seq))).toEqual([[6, 5], [4], [3], [2], [1]]);
  });

  it('leaves a single word-count entry ungrouped', () => {
    const rows = groupForDisplay([words(1)]);
    expect(rows[0].grouped).toBe(false);
  });
});

describe('history cap', () => {
  const many = (from: number, to: number) =>
    Array.from({ length: to - from + 1 }, (_, index) => entry(from + index));

  it('holds at most 1,000 entries and drops the oldest from a page', () => {
    expect(MAX_HELD_ENTRIES).toBe(1000);
    const next = applyPage(emptyHistory, page(many(1, 1200)));
    expect(next.entries).toHaveLength(1000);
    expect(next.entries[0].seq).toBe(201);
    expect(lastSeq(next)).toBe(1200);
  });

  it('drops the oldest when a live append passes the cap', () => {
    const full = applyPage(emptyHistory, page(many(1, 1000)));
    const { state, catchUp } = applyAppend(full, entry(1001));
    expect(catchUp).toBe(false);
    expect(state.entries).toHaveLength(1000);
    expect(state.entries[0].seq).toBe(2);
    expect(lastSeq(state)).toBe(1001);
  });
});

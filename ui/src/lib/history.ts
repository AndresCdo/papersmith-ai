import type { HistoryEntry, HistoryPage } from '../types';

/**
 * Client copy of the server's in-memory history. Entries are stored oldest
 * first, keyed by the server's `boot_id`; the cursor is the last `seq` held.
 */
export interface HistoryState {
  bootId: string | null;
  entries: HistoryEntry[];
  /** Some earlier entries were evicted before this client could read them. */
  gap: boolean;
}

/** Entries the client keeps; the oldest are dropped past this (the server ring is the same size). */
export const MAX_HELD_ENTRIES = 1000;

export const emptyHistory: HistoryState = { bootId: null, entries: [], gap: false };

export function lastSeq(state: HistoryState): number {
  return state.entries.length > 0 ? state.entries[state.entries.length - 1].seq : 0;
}

function mergeEntries(held: HistoryEntry[], incoming: HistoryEntry[]): HistoryEntry[] {
  const seen = new Set(held.map((entry) => entry.id));
  const merged = [...held];
  for (const entry of incoming) {
    if (seen.has(entry.id)) continue;
    seen.add(entry.id);
    merged.push(entry);
  }
  merged.sort((a, b) => a.seq - b.seq);
  return merged.length > MAX_HELD_ENTRIES ? merged.slice(merged.length - MAX_HELD_ENTRIES) : merged;
}

/** Apply one `/api/history` page: a reset discards what is held first. */
export function applyPage(state: HistoryState, page: HistoryPage): HistoryState {
  const base = page.reset ? emptyHistory : state;
  return {
    bootId: page.boot_id,
    entries: mergeEntries(base.entries, page.entries),
    gap: base.gap || page.gap,
  };
}

/**
 * Apply one live `history_append` entry. It is appended only when it is the
 * next one (seq = last + 1, same boot); anything else asks for a catch-up
 * through the paged endpoint and leaves the state untouched.
 */
export function applyAppend(
  state: HistoryState,
  entry: HistoryEntry,
): { state: HistoryState; catchUp: boolean } {
  if (state.entries.some((held) => held.id === entry.id)) return { state, catchUp: false };
  const sameBoot = state.bootId === null || state.bootId === entry.boot_id;
  if (!sameBoot || entry.seq !== lastSeq(state) + 1) return { state, catchUp: true };
  return {
    state: {
      ...state,
      bootId: entry.boot_id,
      entries: [...state.entries, entry].slice(-MAX_HELD_ENTRIES),
    },
    catchUp: false,
  };
}

export interface HistoryFilter {
  kind: string | null;
  element: string | null;
}

export function filterEntries(entries: HistoryEntry[], filter: HistoryFilter): HistoryEntry[] {
  return entries.filter(
    (entry) =>
      (filter.kind === null || entry.kind === filter.kind) &&
      (filter.element === null || entry.element_id === filter.element),
  );
}

export interface DisplayRow {
  key: string;
  /** Newest first; more than one only for a grouped run of word counts. */
  entries: HistoryEntry[];
  grouped: boolean;
}

/**
 * Newest-first rows for display. Consecutive word-count entries of one
 * section collapse into one row; the stored entries are never changed.
 */
export function groupForDisplay(entries: HistoryEntry[]): DisplayRow[] {
  const rows: DisplayRow[] = [];
  for (const entry of [...entries].reverse()) {
    const previous = rows[rows.length - 1];
    const head = previous?.entries[0];
    if (
      previous &&
      head &&
      entry.kind === 'section_words' &&
      head.kind === 'section_words' &&
      head.element_id === entry.element_id
    ) {
      previous.entries.push(entry);
      previous.grouped = true;
    } else {
      rows.push({ key: entry.id, entries: [entry], grouped: false });
    }
  }
  return rows;
}

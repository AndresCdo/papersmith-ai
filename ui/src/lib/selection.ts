/** The part of a React Flow node/edge change this app cares about. */
export interface AnyChange {
  type: string;
  id?: string;
  selected?: boolean;
}

/**
 * Resolve one interaction's batch of node and edge changes into the next
 * selection. Only `select` changes count. If any change selects, the last
 * selected id wins; otherwise a deselect clears the selection only when it
 * names the current one. Returns null when the selection must not change.
 */
export function reduceSelection(
  changes: readonly AnyChange[],
  currentId: string | null,
): { id: string | null } | null {
  const selects = changes.filter((change) => change.type === 'select' && change.id !== undefined);
  const picked = selects.filter((change) => change.selected === true);
  if (picked.length > 0) return { id: picked[picked.length - 1].id as string };
  if (currentId !== null && selects.some((change) => change.id === currentId)) return { id: null };
  return null;
}

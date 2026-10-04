import { describe, expect, it } from 'vitest';
import { reduceSelection } from './selection';

const on = (id: string) => ({ type: 'select' as const, id, selected: true });
const off = (id: string) => ({ type: 'select' as const, id, selected: false });

describe('reduceSelection', () => {
  it('returns null when the batch holds no select change', () => {
    expect(reduceSelection([{ type: 'position', id: 'a' }, { type: 'dimensions', id: 'b' }], 'a')).toBeNull();
    expect(reduceSelection([], null)).toBeNull();
  });

  it('selects the last selected:true id of the batch', () => {
    expect(reduceSelection([on('a'), on('b')], null)).toEqual({ id: 'b' });
  });

  it('lets a selected:true win over a deselect of the previous selection', () => {
    expect(reduceSelection([off('a'), on('b')], 'a')).toEqual({ id: 'b' });
    expect(reduceSelection([on('b'), off('a')], 'a')).toEqual({ id: 'b' });
  });

  it('clears only when the deselected id is the current selection', () => {
    expect(reduceSelection([off('a')], 'a')).toEqual({ id: null });
    expect(reduceSelection([off('x')], 'a')).toBeNull();
    expect(reduceSelection([off('a')], null)).toBeNull();
  });

  it('ignores non-select changes mixed into the batch', () => {
    expect(reduceSelection([{ type: 'position', id: 'z' }, on('a')], null)).toEqual({ id: 'a' });
  });
});

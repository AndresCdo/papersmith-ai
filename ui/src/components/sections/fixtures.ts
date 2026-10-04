import type { Section } from '../../types';

export const draftingSection: Section = {
  id: 'Related Work',
  section: 'Related Work',
  file: 'paper/sections/related.md',
  mode: 'synthesis',
  position: 2,
  status: 'DRAFTING',
  extent: { min_words: 300, max_words: 600 },
  word_count: 120,
  blocks_total: 2,
  blocks_written: 1,
  blocks: [
    { id: 'intro', written: true, produces_facts: ['f1'] },
    { id: 'gap', written: false, optional: true, requires_facts: ['f1'] },
  ],
  facts: { produces: ['f1'], demands: ['f2'], declarations: [] },
  citations: { verified: 3, placeholders: 1, unresolved_keys: ['smith2020'] },
};

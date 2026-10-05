import type { WorkspaceState } from '../../types';

/**
 * One state payload shaped like the extractor's, with the two flows it carries:
 * `pipeline_stages` plus `pipeline_chain` and `gate_links` for the general
 * flow, and `sections` for the writing flow. The ids are real tramo ids, so a
 * test that passes here is a test about a stage the board can actually draw.
 */
export const diagramState: WorkspaceState = {
  pipeline_stages: [
    { id: 'plausibility', title: 'Plausibility', active: false, progress: 1, detail: 'sota-pool/: atlas.json', workers: [] },
    { id: 'ingestion', title: 'Ingestion', active: false, progress: 1, detail: 'papers ingested', workers: [] },
    { id: 'proposal', title: 'Proposal deliberation', active: true, progress: 0.5, detail: 'proposal open', workers: ['deliberation-publish'] },
    { id: 'writing', title: 'Writing', active: true, progress: 0.4, detail: 'writing blocks', workers: ['redactor', 'auditor'] },
    { id: 'figures', title: 'Figures and grounding', active: false, progress: 0, detail: 'not started', workers: [] },
    { id: 'paper', title: 'Paper', active: false, progress: 0, detail: 'not started', workers: [] },
    { id: 'audit', title: 'Audit (transversal)', active: false, progress: 0, detail: '1/2 gates passed', workers: [] },
  ],
  pipeline_chain: [
    { from: 'plausibility', to: 'ingestion', label: 'top-5 to ingest' },
    { from: 'ingestion', to: 'proposal', label: 'guidance/' },
    { from: 'proposal', to: 'writing', label: 'rNN revision' },
    { from: 'writing', to: 'figures', label: 'sections' },
    { from: 'figures', to: 'paper', label: 'anchors' },
  ],
  gate_links: {
    'writing-readiness': { from: 'proposal', label: 'contracts', consumed_by: 'audit' },
    'coupling-verification': { from: 'writing', label: 'facts', consumed_by: 'audit' },
  },
  gates: [
    { id: 'writing-readiness', name: 'Writing readiness', state: 'BLOCKED', reasons: ['contract missing', 'no extent'] },
    { id: 'coupling-verification', name: 'Coupling verification', state: 'PASSED', reasons: [] },
  ],
  sections: [
    {
      id: 'Related Work',
      section: 'Related Work',
      file: 'paper/sections/related.md',
      status: 'DRAFTING',
      word_count: 120,
      blocks_total: 2,
      blocks_written: 1,
      citations: { verified: 3, placeholders: 1, unresolved_keys: ['smith2020'] },
    },
  ],
};

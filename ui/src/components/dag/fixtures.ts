import type { WorkspaceState } from '../../types';

export const diagramState: WorkspaceState = {
  pipeline_stages: [
    { id: 'ingestion', title: 'Ingestion', active: false, progress: 1, detail: 'papers ingested', workers: [] },
    { id: 'deliberation', title: 'Deliberation', active: true, progress: 0.5, detail: 'proposal open', workers: ['tutor'] },
    { id: 'drafting', title: 'Drafting', active: true, progress: 0.4, detail: 'writing blocks', workers: ['redactor', 'auditor'] },
    { id: 'auditing', title: 'Auditing', active: false, progress: 0, detail: 'not started', workers: [] },
    { id: 'publishing', title: 'Publishing', active: false, progress: 0, detail: 'not started', workers: [] },
  ],
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

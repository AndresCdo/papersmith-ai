/**
 * Shapes of the Paper Command Center API payloads.
 *
 * The backend lives in `skills/_core/command_center/`. Only keys the backend
 * documents are modelled here, and every collection is optional: the dashboard
 * must degrade gracefully when a payload arrives partial, or when an older
 * server build is paired with a newer bundle.
 */

export type SectionStatus = 'SCAFFOLDED' | 'CONTRACTED' | 'DRAFTING' | 'AUDITED' | 'SEALED';
export type GateState = 'PASSED' | 'BLOCKED' | 'VERIFYING';
export type WiringState = 'WIRED' | 'DRIFT' | 'UNBOUND' | 'TOOL_MISSING' | 'UNVERIFIED';
export type HarnessSyncState = 'IN_SYNC' | 'DRIFT_DETECTED' | 'UNKNOWN';

export interface SectionExtent {
  min_words?: number | null;
  max_words?: number | null;
}

export interface SectionBlock {
  id?: string | null;
  optional?: boolean;
  citations?: unknown;
  requires_facts?: string[];
  produces_facts?: string[];
  requires_declarations?: string[];
  written?: boolean;
}

export interface SectionFacts {
  demands?: string[];
  produces?: string[];
  declarations?: string[];
}

export interface SectionCitations {
  verified?: number;
  placeholders?: number;
  unresolved_keys?: string[];
}

export interface Section {
  id: string;
  file?: string;
  section?: string;
  position?: unknown;
  mode?: unknown;
  status?: string;
  has_contract?: boolean;
  extent?: SectionExtent;
  word_count?: number;
  blocks?: SectionBlock[];
  facts?: SectionFacts;
  citations?: SectionCitations;
  blocks_total?: number;
  blocks_written?: number;
}

export interface Gate {
  id: string;
  name?: string;
  state?: string;
  reasons?: string[];
  parts?: Record<string, unknown>;
}

export interface PipelineStage {
  id: string;
  title?: string;
  active?: boolean;
  progress?: number;
  detail?: string;
  workers?: string[];
}

export interface WorkspaceTotals {
  sections?: number;
  blocks_total?: number;
  blocks_written?: number;
  word_count?: number;
  placeholder_citations?: number;
  gates_passed?: number;
  gates_total?: number;
}

export interface PaperMetadata {
  name?: string;
  title?: string;
  topic?: string;
  venue_target?: string;
  authors?: unknown[];
  domain_profile?: string;
  tools?: unknown[];
  compute_target?: string;
}

export interface WorkspaceEventsSnapshot {
  revision?: number;
  changed?: string[];
  state?: WorkspaceState;
}

export interface WorkspaceState {
  generated_at?: string;
  workspace?: { root?: string; name?: string; version?: string | null };
  paper_metadata?: PaperMetadata;
  sections?: Section[];
  gates?: Gate[];
  pipeline_stages?: PipelineStage[];
  experiments?: { count?: number; files?: string[] };
  figures?: { count?: number; pdf?: string[]; rasters?: string[] };
  inbox?: { count?: number; paths?: string[]; directory?: string | null };
  totals?: WorkspaceTotals;
}

export interface HarnessRow {
  tool?: string;
  prefix?: string;
  state?: string;
  source?: string;
  detail?: string;
}

export interface SkillRow {
  name?: string;
  path?: string;
  state?: string;
  core?: boolean;
  bytes?: number;
}

export interface CliRow {
  skill?: string;
  path?: string;
  state?: string;
  exit_code?: number | null;
  detail?: string;
}

export interface AgentRow {
  name?: string;
  path?: string;
  state?: string;
  detail?: string;
  skills?: string[];
  tools?: string[];
  unbound_tools?: string[];
  stretch?: unknown;
}

export interface EnvironmentPackage {
  name?: string;
  state?: string;
}

export interface EnvironmentRow {
  python?: { executable?: string; version?: string; state?: string };
  latex?: { engine?: string | null; state?: string };
  node?: { executable?: string | null; state?: string; required?: boolean };
  packages?: EnvironmentPackage[];
}

export interface MatrixRow {
  harness?: string;
  harness_state?: string;
  agent?: string;
  skill?: string | null;
  gate?: string | null;
  state?: string;
}

export interface WiringHealth {
  generated_at?: string;
  summary?: {
    state?: string;
    components_total?: number;
    components_healthy?: number;
    warnings?: string[];
  };
  harness_sync?: { state?: string; harnesses?: HarnessRow[] };
  skills?: SkillRow[];
  cli_entrypoints?: CliRow[];
  agents?: AgentRow[];
  environment?: EnvironmentRow;
  matrix?: MatrixRow[];
}

/** `GET /api/state` SSE frame payload. */
export type StateUpdatePayload = WorkspaceEventsSnapshot;

/** `GET /api/events` `wiring_smoke` frame payload. */
export interface WiringSmokeLinePayload {
  line?: string;
}

/** `POST /api/health/run-wiring-smoke` response body. */
export interface WiringSmokeResult {
  available?: boolean;
  exit_code?: number | null;
  script?: string;
  output?: string;
  detail?: string;
}

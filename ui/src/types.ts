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

/** One immutable `GET /api/history` entry (also the `history_append` payload). */
export interface HistoryEntry {
  id: string;
  boot_id: string;
  seq: number;
  ts: number;
  kind: string;
  element_id: string | null;
  summary: string;
  before: unknown;
  after: unknown;
}

/** `GET /api/history` response body. */
export interface HistoryPage {
  boot_id: string;
  entries: HistoryEntry[];
  has_more: boolean;
  reset: boolean;
  gap: boolean;
}

/** `GET /api/paper/preview`: bounded, read-only block text of the paper. */
export interface PreviewBlock {
  id: string;
  written: boolean;
  /** Plain text of the block body; null when unwritten or cut by the total cap. */
  text: string | null;
  words: number;
  citations: string[];
  truncated: boolean;
  duplicate: boolean;
}

export interface PreviewSection {
  id: string;
  title: string | null;
  position: number | null;
  status: string;
  blocks: PreviewBlock[];
}

export interface PreviewFigure {
  id: string;
  kind: 'pdf' | 'png';
  size: number;
  /** Modification time in integer milliseconds; a cache-busting token. */
  mtime?: number;
}

export interface PaperPreview {
  sections: PreviewSection[];
  truncated: boolean;
  caps: Record<string, number>;
  /** `ok`, `absent`, `too_large`, `unsafe` or `unreadable`. */
  main_tex: { status: string };
  pdf: { main: { present: boolean; size: number; stale: boolean; mtime?: number } | null; figures: PreviewFigure[] } | null;
}

/** `GET /api/atlas`: state of the SOTA atlas files plus a bounded summary. */
export interface AtlasSystem {
  id: string;
  title: string;
  planets: number;
  families: string[];
}

export interface AtlasEvidence {
  system: string;
  planet: string;
  origin: string;
  retrieved: string;
}

export interface AtlasSummary {
  systems: AtlasSystem[];
  links: number;
  rels: Record<string, number>;
  evidence: AtlasEvidence[];
  evidence_total: number;
}

export interface AtlasValidation {
  status: 'ok' | 'failed' | 'unavailable';
  errors?: string[];
  error_count?: number;
  detail?: string;
}

export interface AtlasPayload {
  /** `ok`, `absent`, `too_large`, `unsafe`, `unreadable` or `invalid`. */
  json: { status: string; size?: number; mtime?: number };
  /** `ok`, `absent`, `too_large` or `unsafe`. */
  html: { status: string; size?: number; mtime?: number };
  /** True when atlas.json is newer than atlas.html; null when either is missing. */
  stale: boolean | null;
  validation: AtlasValidation;
  summary: AtlasSummary | null;
}

/** `GET /api/decisions`: a read-only timeline merged from persisted records. */
export interface DecisionEvent {
  /** ISO date-time, or null when the record carries no timestamp (receipts). */
  ts: string | null;
  source: string;
  kind: string;
  summary: string;
  /** Workspace-relative path of the record, as text. */
  ref: string;
  /** `false` when read without hash or consistency checks. */
  verified?: boolean;
  note?: string;
}

export interface DecisionSourceInfo {
  /** `ok`, `absent`, `unreadable` or `too_large`. */
  status: string;
  count: number;
  truncated: boolean;
  detail?: string;
}

export interface DecisionsPayload {
  events: DecisionEvent[];
  sources: Record<string, DecisionSourceInfo>;
  truncated: boolean;
  total: number;
  note?: string;
}

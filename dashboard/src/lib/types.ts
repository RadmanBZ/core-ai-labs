export enum LeadStatus {
  QUALIFIED = "QUALIFIED",
  UNQUALIFIED = "UNQUALIFIED",
  NURTURING_REQUIRED = "NURTURING_REQUIRED",
  PENDING = "PENDING",
}

export interface ExtractedLeadInfo {
  customer_name: string | null;
  company_name: string | null;
  budget_range: string | null;
  primary_pain_point: string | null;
  timeline: string | null;
}

export interface LeadScoreMetadata {
  budget_fit: number;
  intent_strength: number;
  authority_level: number;
  justification: string;
}

export interface ConversationMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface PipelineState {
  session_id: string;
  conversation_history: ConversationMessage[];
  extracted_data: ExtractedLeadInfo;
  evaluation: LeadScoreMetadata | null;
  status: LeadStatus;
}

export interface LatencyMetric {
  timestamp: number;
  latencyMs: number;
  tokens: number;
}

export interface NodeHealth {
  inbound: "online" | "degraded" | "offline";
  extractor: "online" | "degraded" | "offline";
  scorer: "online" | "degraded" | "offline";
  orchestrator: "online" | "degraded" | "offline";
}

export interface SystemTelemetry {
  nodeHealth: NodeHealth;
  pipelineLatencyMs: number;
  activeSessions: number;
  latencyHistory: LatencyMetric[];
  funnelDistribution: Record<LeadStatus, number>;
}

export interface LedgerEntry {
  session_id: string;
  customer_name: string | null;
  company_name: string | null;
  budget_range: string | null;
  status: LeadStatus;
  composite_score: number | null;
  updated_at: string;
}

export type DashboardView = "telemetry" | "analytics" | "ledger";

export type AgentPhase = "idle" | "inbound" | "extracting" | "scoring" | "complete";

export interface StreamEvent {
  type:
    | "message"
    | "extract_field"
    | "evaluation"
    | "status"
    | "phase"
    | "latency"
    | "ledger";
  payload: unknown;
}

export interface TelemetryBridgePayload {
  session: PipelineState;
  activeSessionId: string;
  sessions: PipelineState[];
  agentPhase: AgentPhase;
  isStreaming: boolean;
  telemetry: SystemTelemetry;
  ledger: LedgerEntry[];
  updated_at: string;
}

export const EMPTY_EXTRACTED: ExtractedLeadInfo = {
  customer_name: null,
  company_name: null,
  budget_range: null,
  primary_pain_point: null,
  timeline: null,
};

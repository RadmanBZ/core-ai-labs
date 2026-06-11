import { readFile } from "fs/promises";
import path from "path";

import { createInitialLedger, createInitialTelemetry, IDLE_SESSION_ID } from "./mock-stream";
import {
  AgentPhase,
  LeadStatus,
  LedgerEntry,
  PipelineState,
  TelemetryBridgePayload,
} from "./types";

let liveBridgeState: TelemetryBridgePayload | null = null;

const SHARED_STATE_PATH = path.join(process.cwd(), "..", "shared_state.json");

function defaultPayload(): TelemetryBridgePayload {
  const idleSession: PipelineState = {
    session_id: IDLE_SESSION_ID,
    conversation_history: [],
    extracted_data: {
      customer_name: null,
      company_name: null,
      budget_range: null,
      primary_pain_point: null,
      timeline: null,
    },
    evaluation: null,
    status: LeadStatus.PENDING,
  };

  return {
    session: idleSession,
    activeSessionId: IDLE_SESSION_ID,
    sessions: [idleSession],
    agentPhase: "idle" as AgentPhase,
    isStreaming: false,
    telemetry: createInitialTelemetry(),
    ledger: createInitialLedger(),
    updated_at: new Date(0).toISOString(),
  };
}

function mergeSessions(
  existing: PipelineState[],
  incoming: PipelineState[]
): PipelineState[] {
  const map = new Map(existing.map((session) => [session.session_id, session]));
  for (const session of incoming) {
    map.set(session.session_id, session);
  }
  return Array.from(map.values()).sort((a, b) =>
    b.session_id.localeCompare(a.session_id)
  );
}

function mergeLedger(existing: LedgerEntry[], incoming: LedgerEntry[]): LedgerEntry[] {
  const map = new Map(existing.map((entry) => [entry.session_id, entry]));
  for (const entry of incoming) {
    map.set(entry.session_id, entry);
  }
  return Array.from(map.values()).sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at)
  );
}

export function setLiveBridgeState(payload: TelemetryBridgePayload): void {
  if (!liveBridgeState) {
    liveBridgeState = {
      ...payload,
      sessions: payload.sessions?.length ? payload.sessions : [payload.session],
      ledger: payload.ledger ?? [],
    };
    return;
  }

  const mergedSessions = mergeSessions(
    liveBridgeState.sessions ?? [liveBridgeState.session],
    payload.sessions?.length ? payload.sessions : [payload.session]
  );
  const activeSession =
    mergedSessions.find((session) => session.session_id === payload.activeSessionId) ??
    payload.session;

  liveBridgeState = {
    ...payload,
    session: activeSession,
    activeSessionId: payload.activeSessionId,
    sessions: mergedSessions,
    ledger: mergeLedger(liveBridgeState.ledger, payload.ledger ?? []),
  };
}

export async function getLiveBridgeState(): Promise<TelemetryBridgePayload> {
  if (liveBridgeState) {
    return liveBridgeState;
  }

  try {
    const raw = await readFile(SHARED_STATE_PATH, "utf-8");
    const parsed = JSON.parse(raw) as TelemetryBridgePayload;
    liveBridgeState = {
      ...parsed,
      sessions: parsed.sessions?.length ? parsed.sessions : [parsed.session],
    };
    return liveBridgeState;
  } catch {
    return defaultPayload();
  }
}

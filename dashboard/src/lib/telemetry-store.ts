import { readFile } from "fs/promises";
import path from "path";

import { createInitialLedger, createInitialTelemetry } from "./mock-stream";
import {
  AgentPhase,
  LeadStatus,
  TelemetryBridgePayload,
} from "./types";

let liveBridgeState: TelemetryBridgePayload | null = null;

const SHARED_STATE_PATH = path.join(process.cwd(), "..", "shared_state.json");

function defaultPayload(): TelemetryBridgePayload {
  return {
    session: {
      session_id: "idle",
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
    },
    agentPhase: "idle" as AgentPhase,
    isStreaming: false,
    telemetry: createInitialTelemetry(),
    ledger: createInitialLedger(),
    updated_at: new Date(0).toISOString(),
  };
}

export function setLiveBridgeState(payload: TelemetryBridgePayload): void {
  liveBridgeState = payload;
}

export async function getLiveBridgeState(): Promise<TelemetryBridgePayload> {
  if (liveBridgeState) {
    return liveBridgeState;
  }

  try {
    const raw = await readFile(SHARED_STATE_PATH, "utf-8");
    const parsed = JSON.parse(raw) as TelemetryBridgePayload;
    liveBridgeState = parsed;
    return parsed;
  } catch {
    return defaultPayload();
  }
}

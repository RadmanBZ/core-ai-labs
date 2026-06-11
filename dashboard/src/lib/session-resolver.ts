import { LedgerEntry, LeadScoreMetadata, PipelineState } from "./types";

export function resolveSessionDetail(
  sessionId: string | null,
  sessions: PipelineState[],
  ledger: LedgerEntry[]
): PipelineState | null {
  if (!sessionId) return null;

  const fromSessions = sessions.find((item) => item.session_id === sessionId);
  if (fromSessions) return fromSessions;

  const entry = ledger.find((item) => item.session_id === sessionId);
  if (!entry) return null;

  return {
    session_id: entry.session_id,
    conversation_history: [],
    extracted_data: {
      customer_name: entry.customer_name,
      company_name: entry.company_name,
      budget_range: entry.budget_range,
      primary_pain_point: null,
      timeline: null,
    },
    evaluation: evaluationFromComposite(entry.composite_score),
    status: entry.status,
  };
}

function evaluationFromComposite(
  compositeScore: number | null
): LeadScoreMetadata | null {
  if (compositeScore === null) return null;
  const rounded = Math.min(10, Math.max(0, Math.round(compositeScore)));
  return {
    budget_fit: rounded,
    intent_strength: rounded,
    authority_level: rounded,
    justification: "Composite score restored from ledger archive.",
  };
}

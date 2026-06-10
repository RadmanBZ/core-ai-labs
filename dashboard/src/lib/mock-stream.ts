import {
  AgentPhase,
  EMPTY_EXTRACTED,
  ExtractedLeadInfo,
  LatencyMetric,
  LeadScoreMetadata,
  LeadStatus,
  LedgerEntry,
  PipelineState,
  StreamEvent,
  SystemTelemetry,
} from "./types";

const SCENARIOS: Array<{
  session_id: string;
  messages: Array<{ role: "user" | "assistant"; content: string }>;
  extracted: ExtractedLeadInfo;
  evaluation: LeadScoreMetadata;
  status: LeadStatus;
}> = [
  {
    session_id: "a7f3c912",
    messages: [
      {
        role: "user",
        content:
          "We're Muscat Logistics — manual invoice ingestion is killing our ops team. Looking at automation within Q3.",
      },
      {
        role: "assistant",
        content:
          "Understood. Rayza specializes in high-throughput document automation for logistics operators. What volume are you processing monthly, and do you have a budget envelope in mind?",
      },
      {
        role: "user",
        content:
          "Roughly 18k invoices. Budget is around OMR 50,000. I'm Ali Al-Busaddi, Head of Operations — I sign off on this.",
      },
      {
        role: "assistant",
        content:
          "Excellent context, Ali. With that scale and authority level, we can architect a sub-second ingestion pipeline. I'll route your profile for executive qualification.",
      },
    ],
    extracted: {
      customer_name: "Ali Al-Busaddi",
      company_name: "Muscat Logistics",
      budget_range: "OMR 50,000",
      primary_pain_point: "Manual invoice ingestion latency",
      timeline: "Q3 2026",
    },
    evaluation: {
      budget_fit: 9,
      intent_strength: 8,
      authority_level: 9,
      justification:
        "High budget alignment, explicit Q3 timeline, and decision-maker authority confirmed.",
    },
    status: LeadStatus.QUALIFIED,
  },
  {
    session_id: "b2e8d441",
    messages: [
      {
        role: "user",
        content:
          "Hi, we're exploring AI chatbots for our retail chain. Not sure on budget yet.",
      },
      {
        role: "assistant",
        content:
          "Happy to consult. Which customer touchpoints are highest priority — support, sales, or internal ops?",
      },
      {
        role: "user",
        content:
          "Mostly support. I'm a marketing coordinator gathering options for our CTO.",
      },
      {
        role: "assistant",
        content:
          "Got it. I'll capture your requirements and recommend a phased discovery path aligned to your evaluation cycle.",
      },
    ],
    extracted: {
      customer_name: null,
      company_name: "Retail Chain (undisclosed)",
      budget_range: null,
      primary_pain_point: "Customer support automation exploration",
      timeline: "6–12 months",
    },
    evaluation: {
      budget_fit: 4,
      intent_strength: 5,
      authority_level: 3,
      justification:
        "Early-stage exploration without budget signal; contact lacks direct purchasing authority.",
    },
    status: LeadStatus.NURTURING_REQUIRED,
  },
];

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomLatency(): number {
  return Math.floor(420 + Math.random() * 380);
}

function randomTokens(): number {
  return Math.floor(180 + Math.random() * 220);
}

export function createInitialTelemetry(): SystemTelemetry {
  return {
    nodeHealth: {
      inbound: "online",
      extractor: "online",
      scorer: "online",
      orchestrator: "online",
    },
    pipelineLatencyMs: 742,
    activeSessions: 3,
    latencyHistory: Array.from({ length: 24 }, (_, i) => ({
      timestamp: Date.now() - (23 - i) * 4000,
      latencyMs: 520 + Math.sin(i / 3) * 120 + Math.random() * 80,
      tokens: 200 + Math.cos(i / 4) * 40 + Math.random() * 30,
    })),
    funnelDistribution: {
      [LeadStatus.QUALIFIED]: 12,
      [LeadStatus.NURTURING_REQUIRED]: 8,
      [LeadStatus.UNQUALIFIED]: 5,
      [LeadStatus.PENDING]: 2,
    },
  };
}

export function createInitialLedger(): LedgerEntry[] {
  return [
    {
      session_id: "f91ac0de",
      customer_name: "Salem Al-Rashdi",
      company_name: "Gulf FinTech",
      budget_range: "OMR 15,000",
      status: LeadStatus.QUALIFIED,
      composite_score: 8.3,
      updated_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      session_id: "c44b8910",
      customer_name: "Nadia Hassan",
      company_name: "Desert Retail Group",
      budget_range: null,
      status: LeadStatus.NURTURING_REQUIRED,
      composite_score: 5.7,
      updated_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      session_id: "8d22ef11",
      customer_name: null,
      company_name: "Anonymous Inquiry",
      budget_range: "$2,000",
      status: LeadStatus.UNQUALIFIED,
      composite_score: 2.3,
      updated_at: new Date(Date.now() - 10800000).toISOString(),
    },
  ];
}

export function createEmptySession(sessionId: string): PipelineState {
  return {
    session_id: sessionId,
    conversation_history: [],
    extracted_data: { ...EMPTY_EXTRACTED },
    evaluation: null,
    status: LeadStatus.PENDING,
  };
}

type StreamCallback = (event: StreamEvent) => void;

export class PipelineStreamSimulator {
  private running = false;
  private scenarioIndex = 0;

  async start(sessionId: string, onEvent: StreamCallback): Promise<void> {
    if (this.running) return;
    this.running = true;

    const scenario = SCENARIOS[this.scenarioIndex % SCENARIOS.length];
    this.scenarioIndex += 1;

    onEvent({ type: "phase", payload: "inbound" satisfies AgentPhase });

    for (const message of scenario.messages) {
      if (!this.running) return;
      await delay(message.role === "user" ? 900 : 1400);
      onEvent({ type: "message", payload: message });
      const metric: LatencyMetric = {
        timestamp: Date.now(),
        latencyMs: randomLatency(),
        tokens: randomTokens(),
      };
      onEvent({ type: "latency", payload: metric });
    }

    onEvent({ type: "phase", payload: "extracting" satisfies AgentPhase });
    const fieldKeys = Object.keys(scenario.extracted) as Array<keyof ExtractedLeadInfo>;

    for (const key of fieldKeys) {
      if (!this.running) return;
      await delay(650 + Math.random() * 400);
      onEvent({
        type: "extract_field",
        payload: { key, value: scenario.extracted[key] },
      });
    }

    onEvent({ type: "phase", payload: "scoring" satisfies AgentPhase });
    await delay(1100);
    onEvent({ type: "evaluation", payload: scenario.evaluation });
    await delay(500);
    onEvent({ type: "status", payload: scenario.status });
    onEvent({ type: "phase", payload: "complete" satisfies AgentPhase });

    const ledgerEntry: LedgerEntry = {
      session_id: sessionId,
      customer_name: scenario.extracted.customer_name,
      company_name: scenario.extracted.company_name,
      budget_range: scenario.extracted.budget_range,
      status: scenario.status,
      composite_score:
        (scenario.evaluation.budget_fit +
          scenario.evaluation.intent_strength +
          scenario.evaluation.authority_level) /
        3,
      updated_at: new Date().toISOString(),
    };
    onEvent({ type: "ledger", payload: ledgerEntry });
    this.running = false;
  }

  stop(): void {
    this.running = false;
  }
}

export function generateSessionId(): string {
  return crypto.randomUUID().slice(0, 8);
}

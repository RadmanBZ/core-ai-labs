"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createEmptySession,
  createInitialLedger,
  createInitialTelemetry,
  generateSessionId,
  PipelineStreamSimulator,
} from "@/lib/mock-stream";
import {
  AgentPhase,
  DashboardView,
  ExtractedLeadInfo,
  LatencyMetric,
  LeadScoreMetadata,
  LeadStatus,
  LedgerEntry,
  PipelineState,
  SystemTelemetry,
} from "@/lib/types";

export function usePipelineStream() {
  const [activeView, setActiveView] = useState<DashboardView>("telemetry");
  const [session, setSession] = useState<PipelineState>(() =>
    createEmptySession(generateSessionId())
  );
  const [telemetry, setTelemetry] = useState<SystemTelemetry>(createInitialTelemetry);
  const [ledger, setLedger] = useState<LedgerEntry[]>(createInitialLedger);
  const [agentPhase, setAgentPhase] = useState<AgentPhase>("idle");
  const [isStreaming, setIsStreaming] = useState(false);
  const [parsingFields, setParsingFields] = useState<Set<keyof ExtractedLeadInfo>>(
    new Set()
  );

  const simulatorRef = useRef<PipelineStreamSimulator | null>(null);

  useEffect(() => {
    simulatorRef.current = new PipelineStreamSimulator();
    return () => simulatorRef.current?.stop();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry((prev) => {
        const metric: LatencyMetric = {
          timestamp: Date.now(),
          latencyMs: 480 + Math.random() * 320,
          tokens: 160 + Math.random() * 180,
        };
        const history = [...prev.latencyHistory.slice(-23), metric];
        const avg =
          history.slice(-5).reduce((sum, h) => sum + h.latencyMs, 0) /
          Math.min(5, history.length);
        return {
          ...prev,
          pipelineLatencyMs: Math.round(avg),
          latencyHistory: history,
        };
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const resetSession = useCallback(() => {
    simulatorRef.current?.stop();
    const newId = generateSessionId();
    setSession(createEmptySession(newId));
    setAgentPhase("idle");
    setParsingFields(new Set());
    setIsStreaming(false);
  }, []);

  const startSimulation = useCallback(async () => {
    if (isStreaming) return;
    const sessionId = generateSessionId();
    setSession(createEmptySession(sessionId));
    setParsingFields(new Set());
    setIsStreaming(true);
    setAgentPhase("inbound");

    await simulatorRef.current?.start(sessionId, (event) => {
      switch (event.type) {
        case "message": {
          const msg = event.payload as { role: "user" | "assistant"; content: string };
          setSession((prev) => ({
            ...prev,
            conversation_history: [...prev.conversation_history, msg],
          }));
          break;
        }
        case "extract_field": {
          const { key, value } = event.payload as {
            key: keyof ExtractedLeadInfo;
            value: string | null;
          };
          setParsingFields((prev) => new Set(prev).add(key));
          setTimeout(() => {
            setSession((prev) => ({
              ...prev,
              extracted_data: { ...prev.extracted_data, [key]: value },
            }));
            setParsingFields((prev) => {
              const next = new Set(prev);
              next.delete(key);
              return next;
            });
          }, 380);
          break;
        }
        case "evaluation":
          setSession((prev) => ({
            ...prev,
            evaluation: event.payload as LeadScoreMetadata,
          }));
          break;
        case "status":
          setSession((prev) => ({
            ...prev,
            status: event.payload as LeadStatus,
          }));
          setTelemetry((prev) => {
            const status = event.payload as LeadStatus;
            return {
              ...prev,
              funnelDistribution: {
                ...prev.funnelDistribution,
                [status]: prev.funnelDistribution[status] + 1,
              },
            };
          });
          break;
        case "phase":
          setAgentPhase(event.payload as AgentPhase);
          if (event.payload === "complete") setIsStreaming(false);
          break;
        case "latency": {
          const metric = event.payload as LatencyMetric;
          setTelemetry((prev) => ({
            ...prev,
            pipelineLatencyMs: metric.latencyMs,
            latencyHistory: [...prev.latencyHistory.slice(-23), metric],
          }));
          break;
        }
        case "ledger":
          setLedger((prev) => [event.payload as LedgerEntry, ...prev]);
          setTelemetry((prev) => ({
            ...prev,
            activeSessions: prev.activeSessions + 1,
          }));
          break;
        default:
          break;
      }
    });
  }, [isStreaming]);

  return {
    activeView,
    setActiveView,
    session,
    telemetry,
    ledger,
    agentPhase,
    isStreaming,
    parsingFields,
    resetSession,
    startSimulation,
  };
}

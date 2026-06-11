"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createEmptySession,
  createInitialLedger,
  createInitialTelemetry,
  generateSessionId,
  IDLE_SESSION_ID,
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
  TelemetryBridgePayload,
} from "@/lib/types";

const POLL_INTERVAL_MS = 1500;

export function usePipelineStream() {
  const [activeView, setActiveView] = useState<DashboardView>("telemetry");
  const [session, setSession] = useState<PipelineState>(() =>
    createEmptySession(IDLE_SESSION_ID)
  );
  const [sessions, setSessions] = useState<PipelineState[]>(() => [
    createEmptySession(IDLE_SESSION_ID),
  ]);
  const [telemetry, setTelemetry] = useState<SystemTelemetry>(createInitialTelemetry);
  const [ledger, setLedger] = useState<LedgerEntry[]>(createInitialLedger);
  const [agentPhase, setAgentPhase] = useState<AgentPhase>("idle");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [parsingFields, setParsingFields] = useState<Set<keyof ExtractedLeadInfo>>(
    new Set()
  );

  const simulatorRef = useRef<PipelineStreamSimulator | null>(null);
  const lastSyncRef = useRef<string>("");

  useEffect(() => {
    simulatorRef.current = new PipelineStreamSimulator();
    return () => simulatorRef.current?.stop();
  }, []);

  const applyBridgePayload = useCallback((payload: TelemetryBridgePayload) => {
    if (payload.updated_at === lastSyncRef.current) {
      return;
    }
    lastSyncRef.current = payload.updated_at;
    const activeSession =
      payload.sessions?.find((item) => item.session_id === payload.activeSessionId) ??
      payload.session;
    setSession(activeSession);
    setSessions(payload.sessions?.length ? payload.sessions : [activeSession]);
    setTelemetry(payload.telemetry);
    setLedger(payload.ledger);
    setAgentPhase(payload.agentPhase);
    setIsStreaming(payload.isStreaming);
    setParsingFields(new Set());
    setIsLiveConnected(true);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const pollTelemetry = async () => {
      try {
        const response = await fetch("/api/telemetry", { cache: "no-store" });
        if (!response.ok) return;
        const payload = (await response.json()) as TelemetryBridgePayload;
        if (!cancelled) {
          applyBridgePayload(payload);
        }
      } catch {
        if (!cancelled) {
          setIsLiveConnected(false);
        }
      }
    };

    pollTelemetry();
    const interval = setInterval(pollTelemetry, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [applyBridgePayload]);

  useEffect(() => {
    if (isLiveConnected) return;

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
  }, [isLiveConnected]);

  const resetSession = useCallback(() => {
    simulatorRef.current?.stop();
    const newId = generateSessionId();
    setSession(createEmptySession(newId));
    setAgentPhase("idle");
    setParsingFields(new Set());
    setIsStreaming(false);
    lastSyncRef.current = "";
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
    sessions,
    telemetry,
    ledger,
    agentPhase,
    isStreaming,
    isLiveConnected,
    parsingFields,
    resetSession,
    startSimulation,
  };
};

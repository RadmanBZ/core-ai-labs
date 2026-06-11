"use client";

import { useEffect, useState } from "react";
import { LeadScoringGauge } from "@/components/analytics/LeadScoringGauge";
import { LatencyTokenChart } from "@/components/analytics/LatencyTokenChart";
import { PipelineFunnelChart } from "@/components/analytics/PipelineFunnelChart";
import { LeadLedgerTable } from "@/components/crm/LeadLedgerTable";
import { Sidebar } from "@/components/shell/Sidebar";
import { AgentStateMonitor } from "@/components/telemetry/AgentStateMonitor";
import { LiveChatStream } from "@/components/telemetry/LiveChatStream";
import { MetricCard } from "@/components/ui/MetricCard";
import { usePipelineStream } from "@/hooks/usePipelineStream";
import { compositeScore } from "@/lib/utils";
import { Activity, Gauge, Layers, Users } from "lucide-react";

export function DashboardClient() {
  const {
    activeView,
    setActiveView,
    session,
    telemetry,
    ledger,
    agentPhase,
    isStreaming,
    isLiveConnected,
    parsingFields,
    resetSession,
    startSimulation,
  } = usePipelineStream();

  const score = compositeScore(session.evaluation);
  const [clock, setClock] = useState("");

  useEffect(() => {
    const tick = () =>
      setClock(new Date().toLocaleTimeString("en-US", { hour12: false }));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-[#050A12] text-slate-100">
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        pipelineLatencyMs={telemetry.pipelineLatencyMs}
        activeSessions={telemetry.activeSessions}
        nodeHealth={telemetry.nodeHealth}
        session={session}
        isStreaming={isStreaming}
        onStartSimulation={startSimulation}
        onResetSession={resetSession}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center justify-between border-b border-white/[0.06] bg-[#050A12]/80 px-6 py-4 backdrop-blur-md">
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white">
              {activeView === "telemetry" && "Live Agent Telemetry Hub"}
              {activeView === "analytics" && "Executive Analytics Matrix"}
              {activeView === "ledger" && "Lead Management Ledger"}
            </h1>
            <p className="text-xs text-slate-500">
              Rayza Multi-Agent B2B Sales Pipeline — Production Telemetry Console
            </p>
          </div>
          <div className="hidden items-center gap-3 md:flex">
            <span
              className={
                isLiveConnected
                  ? "rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-400"
                  : "rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-400"
              }
            >
              {isLiveConnected ? "Live CLI Bridge Active" : "Mock Telemetry Mode"}
            </span>
            <span className="font-mono text-xs text-slate-500" suppressHydrationWarning>
              {clock || "--:--:--"}
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {activeView === "telemetry" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  label="Pipeline Latency"
                  value={`${telemetry.pipelineLatencyMs}ms`}
                  sublabel={telemetry.pipelineLatencyMs < 900 ? "Within SLA" : "Above target"}
                  icon={Gauge}
                  accent={telemetry.pipelineLatencyMs < 900 ? "emerald" : "amber"}
                />
                <MetricCard
                  label="Composite Score"
                  value={session.evaluation ? score.toFixed(1) : "—"}
                  sublabel="ScorerAgent output"
                  icon={Activity}
                  accent="cyan"
                />
                <MetricCard
                  label="Active Sessions"
                  value={String(telemetry.activeSessions)}
                  sublabel="Concurrent pipelines"
                  icon={Users}
                  accent="emerald"
                />
                <MetricCard
                  label="Agent Phase"
                  value={agentPhase.toUpperCase()}
                  sublabel="Current orchestration step"
                  icon={Layers}
                  accent="cyan"
                />
              </div>

              <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <LiveChatStream
                  messages={session.conversation_history}
                  isStreaming={isStreaming}
                />
                <AgentStateMonitor
                  session={session}
                  agentPhase={agentPhase}
                  parsingFields={parsingFields}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <LeadScoringGauge evaluation={session.evaluation} />
                <PipelineFunnelChart distribution={telemetry.funnelDistribution} />
                <LatencyTokenChart history={telemetry.latencyHistory} />
              </div>
            </div>
          )}

          {activeView === "analytics" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                <LeadScoringGauge evaluation={session.evaluation} />
                <PipelineFunnelChart distribution={telemetry.funnelDistribution} />
                <LatencyTokenChart history={telemetry.latencyHistory} />
              </div>
              <LatencyTokenChart history={telemetry.latencyHistory} />
            </div>
          )}

          {activeView === "ledger" && <LeadLedgerTable entries={ledger} />}
        </div>
      </main>
    </div>
  );
}

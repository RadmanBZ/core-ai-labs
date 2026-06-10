"use client";

import { StatusBadge } from "@/components/ui/StatusBadge";
import { DashboardView, NodeHealth, PipelineState } from "@/lib/types";
import { cn, hashSessionId } from "@/lib/utils";
import {
  Activity,
  BarChart3,
  Cpu,
  LayoutDashboard,
  Radio,
  Table2,
  Zap,
} from "lucide-react";

interface SidebarProps {
  activeView: DashboardView;
  onViewChange: (view: DashboardView) => void;
  pipelineLatencyMs: number;
  activeSessions: number;
  nodeHealth: NodeHealth;
  session: PipelineState;
  isStreaming: boolean;
  onStartSimulation: () => void;
  onResetSession: () => void;
}

const NAV_ITEMS: Array<{ id: DashboardView; label: string; icon: typeof Activity }> = [
  { id: "telemetry", label: "Telemetry Hub", icon: Radio },
  { id: "analytics", label: "Analytics Matrix", icon: BarChart3 },
  { id: "ledger", label: "Lead Ledger", icon: Table2 },
];

const NODE_LABELS: Array<{ key: keyof NodeHealth; label: string }> = [
  { key: "orchestrator", label: "Orchestrator" },
  { key: "inbound", label: "Inbound Agent" },
  { key: "extractor", label: "Extractor Agent" },
  { key: "scorer", label: "Scorer Agent" },
];

function healthDot(status: NodeHealth[keyof NodeHealth]) {
  const colors = {
    online: "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]",
    degraded: "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]",
    offline: "bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.8)]",
  };
  return colors[status];
}

export function Sidebar({
  activeView,
  onViewChange,
  pipelineLatencyMs,
  activeSessions,
  nodeHealth,
  session,
  isStreaming,
  onStartSimulation,
  onResetSession,
}: SidebarProps) {
  const latencyHealthy = pipelineLatencyMs < 900;

  return (
    <aside className="flex h-full w-[260px] shrink-0 flex-col border-r border-white/[0.06] bg-[#040810]/90 backdrop-blur-xl">
      <div className="border-b border-white/[0.06] px-5 py-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-400/30 bg-cyan-400/10">
            <LayoutDashboard className="h-4 w-4 text-cyan-400" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-white">Rayza</p>
            <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
              Sales Core
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onViewChange(id)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-all duration-200",
              activeView === id
                ? "bg-cyan-400/10 text-cyan-300 shadow-[inset_0_0_0_1px_rgba(34,211,238,0.2)]"
                : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </button>
        ))}
      </nav>

      <div className="space-y-4 border-t border-white/[0.06] px-4 py-4">
        <div>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Node Health
          </p>
          <div className="space-y-2">
            {NODE_LABELS.map(({ key, label }) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-slate-400">{label}</span>
                <span className="flex items-center gap-1.5 capitalize text-slate-300">
                  <span className={cn("h-1.5 w-1.5 rounded-full", healthDot(nodeHealth[key]))} />
                  {nodeHealth[key]}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
              <Zap className="h-3 w-3" />
              Latency
            </div>
            <p
              className={cn(
                "mt-1 font-mono text-lg font-semibold tabular-nums",
                latencyHealthy ? "text-emerald-400" : "text-amber-400"
              )}
            >
              {pipelineLatencyMs}
              <span className="text-xs text-slate-500">ms</span>
            </p>
            <p className="text-[10px] text-slate-600">
              Target &lt;900ms
            </p>
          </div>
          <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
              <Cpu className="h-3 w-3" />
              Sessions
            </div>
            <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-cyan-400">
              {activeSessions}
            </p>
            <p className="text-[10px] text-slate-600">Active pipelines</p>
          </div>
        </div>

        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <p className="text-[10px] uppercase tracking-widest text-slate-500">
            Current Session
          </p>
          <p className="mt-1 font-mono text-xs text-cyan-300">
            {hashSessionId(session.session_id)}
          </p>
          <div className="mt-2">
            <StatusBadge status={session.status} pulse={isStreaming} />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={onStartSimulation}
            disabled={isStreaming}
            className="flex items-center justify-center gap-2 rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-300 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Activity className="h-3.5 w-3.5" />
            {isStreaming ? "Streaming…" : "Inject Live Session"}
          </button>
          <button
            type="button"
            onClick={onResetSession}
            className="rounded-lg border border-white/[0.08] px-3 py-2 text-xs text-slate-400 transition hover:bg-white/[0.04] hover:text-slate-200"
          >
            Reset Session
          </button>
        </div>
      </div>
    </aside>
  );
}

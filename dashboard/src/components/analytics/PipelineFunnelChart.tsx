"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { STATUS_COLORS } from "@/lib/constants";
import { LeadStatus } from "@/lib/types";
import { statusLabel } from "@/lib/utils";

interface PipelineFunnelChartProps {
  distribution: Record<LeadStatus, number>;
}

const FUNNEL_ORDER = [
  LeadStatus.QUALIFIED,
  LeadStatus.NURTURING_REQUIRED,
  LeadStatus.UNQUALIFIED,
];

export function PipelineFunnelChart({ distribution }: PipelineFunnelChartProps) {
  const maxValue = Math.max(...FUNNEL_ORDER.map((s) => distribution[s]), 1);
  const total = Object.values(distribution).reduce((a, b) => a + b, 0);

  return (
    <GlassPanel className="p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Pipeline Conversion Funnel
      </h3>
      <p className="mt-0.5 text-[10px] text-slate-600">
        Session distribution across LeadStatus states
      </p>

      <div className="mt-5 space-y-3">
        {FUNNEL_ORDER.map((status, index) => {
          const count = distribution[status];
          const widthPct = Math.max((count / maxValue) * 100, 12);
          const color = STATUS_COLORS[status];

          return (
            <div key={status} className="animate-in fade-in duration-500" style={{ animationDelay: `${index * 80}ms` }}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span style={{ color }}>{statusLabel(status)}</span>
                <span className="font-mono text-slate-400">
                  {count}{" "}
                  <span className="text-slate-600">
                    ({total > 0 ? Math.round((count / total) * 100) : 0}%)
                  </span>
                </span>
              </div>
              <div className="flex justify-center">
                <div
                  className="h-9 rounded-md border transition-all duration-700 ease-out"
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: `${color}18`,
                    borderColor: `${color}40`,
                    boxShadow: `0 0 24px -8px ${color}60`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-white/[0.06] pt-3 text-[10px] text-slate-500">
        <span>Pending: {distribution[LeadStatus.PENDING]}</span>
        <span>Total tracked: {total}</span>
      </div>
    </GlassPanel>
  );
}

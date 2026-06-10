"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { LeadScoreMetadata } from "@/lib/types";
import { compositeScore } from "@/lib/utils";
import {
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
} from "recharts";

interface LeadScoringGaugeProps {
  evaluation: LeadScoreMetadata | null;
}

export function LeadScoringGauge({ evaluation }: LeadScoringGaugeProps) {
  const score = compositeScore(evaluation);
  const percentage = Math.round((score / 10) * 100);

  const data = [
    {
      name: "Composite",
      value: percentage,
      fill: score >= 7 ? "#34D399" : score >= 4 ? "#22D3EE" : "#FB7185",
    },
  ];

  return (
    <GlassPanel className="p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Lead Scoring Gauge
      </h3>
      <p className="mt-0.5 text-[10px] text-slate-600">
        Composite algorithmic score — ScorerAgent
      </p>

      <div className="relative mx-auto mt-2 h-[200px] w-full max-w-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="70%"
            innerRadius="55%"
            outerRadius="95%"
            barSize={14}
            data={data}
            startAngle={180}
            endAngle={0}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              background={{ fill: "rgba(255,255,255,0.04)" }}
              dataKey="value"
              cornerRadius={8}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-x-0 bottom-6 text-center">
          <p className="font-mono text-4xl font-bold tabular-nums text-white">
            {evaluation ? score.toFixed(1) : "—"}
          </p>
          <p className="text-[10px] uppercase tracking-widest text-slate-500">
            out of 10.0
          </p>
        </div>
      </div>

      {evaluation && (
        <div className="mt-2 grid grid-cols-3 gap-2 border-t border-white/[0.06] pt-3">
          <MetricPill label="Budget" value={evaluation.budget_fit} />
          <MetricPill label="Intent" value={evaluation.intent_strength} />
          <MetricPill label="Authority" value={evaluation.authority_level} />
        </div>
      )}
    </GlassPanel>
  );
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-2 py-1.5 text-center">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="font-mono text-sm font-semibold text-cyan-300">{value}</p>
    </div>
  );
}

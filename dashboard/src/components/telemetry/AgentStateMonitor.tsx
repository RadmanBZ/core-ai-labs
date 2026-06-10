"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { SkeletonField } from "@/components/ui/SkeletonField";
import { EXTRACTOR_FIELDS } from "@/lib/constants";
import { AgentPhase, ExtractedLeadInfo, PipelineState } from "@/lib/types";
import { Brain, ScanSearch, Target } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentStateMonitorProps {
  session: PipelineState;
  agentPhase: AgentPhase;
  parsingFields: Set<keyof ExtractedLeadInfo>;
}

const PHASE_STEPS: AgentPhase[] = ["inbound", "extracting", "scoring", "complete"];

function phaseIndex(phase: AgentPhase): number {
  if (phase === "idle") return -1;
  return PHASE_STEPS.indexOf(phase);
}

export function AgentStateMonitor({
  session,
  agentPhase,
  parsingFields,
}: AgentStateMonitorProps) {
  const currentIdx = phaseIndex(agentPhase);
  const evaluation = session.evaluation;

  return (
    <GlassPanel glow="emerald" className="flex h-full min-h-[420px] flex-col overflow-hidden">
      <div className="border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">Agent State Monitor</h2>
        </div>
        <div className="mt-3 flex items-center gap-1">
          {PHASE_STEPS.map((step, idx) => (
            <div key={step} className="flex flex-1 items-center gap-1">
              <div
                className={cn(
                  "h-1 flex-1 rounded-full transition-all duration-500",
                  idx <= currentIdx ? "bg-emerald-400" : "bg-white/[0.06]"
                )}
              />
            </div>
          ))}
        </div>
        <p className="mt-2 text-[10px] uppercase tracking-widest text-slate-500">
          Pipeline: Inbound → Extractor → Scorer
        </p>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-4">
        <section>
          <div className="mb-3 flex items-center gap-2">
            <ScanSearch
              className={cn(
                "h-3.5 w-3.5",
                agentPhase === "extracting" ? "animate-pulse text-cyan-400" : "text-slate-500"
              )}
            />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              ExtractorAgent — Structured Parse
            </h3>
          </div>
          <div className="grid gap-2">
            {EXTRACTOR_FIELDS.map(({ key, label }) => {
              const value = session.extracted_data[key];
              const isParsing = parsingFields.has(key);
              const isFilled = Boolean(value) && !isParsing;
              return (
                <SkeletonField
                  key={key}
                  label={label}
                  value={value}
                  isParsing={isParsing}
                  isFilled={isFilled}
                />
              );
            })}
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center gap-2">
            <Target
              className={cn(
                "h-3.5 w-3.5",
                agentPhase === "scoring" ? "animate-pulse text-emerald-400" : "text-slate-500"
              )}
            />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              ScorerAgent — Evaluation Matrix
            </h3>
          </div>
          {evaluation ? (
            <div className="space-y-2 animate-in fade-in duration-500">
              <ScoreBar label="Budget Fit" value={evaluation.budget_fit} color="cyan" />
              <ScoreBar label="Intent Strength" value={evaluation.intent_strength} color="emerald" />
              <ScoreBar label="Authority Level" value={evaluation.authority_level} color="amber" />
              <div className="mt-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                <p className="text-[10px] uppercase tracking-widest text-slate-500">
                  Justification
                </p>
                <p className="mt-1 text-xs leading-relaxed text-slate-300">
                  {evaluation.justification}
                </p>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-white/[0.08] p-6 text-center">
              <p className="text-xs text-slate-600">
                {agentPhase === "scoring"
                  ? "Computing qualification matrix…"
                  : "Awaiting extraction completion"}
              </p>
            </div>
          )}
        </section>
      </div>
    </GlassPanel>
  );
}

function ScoreBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "cyan" | "emerald" | "amber";
}) {
  const colorClass = {
    cyan: "bg-cyan-400",
    emerald: "bg-emerald-400",
    amber: "bg-amber-400",
  }[color];

  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-slate-200">{value}/10</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className={cn("h-full rounded-full transition-all duration-700 ease-out", colorClass)}
          style={{ width: `${value * 10}%` }}
        />
      </div>
    </div>
  );
}

import { GlassPanel } from "@/components/ui/GlassPanel";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  sublabel?: string;
  icon: LucideIcon;
  accent?: "cyan" | "emerald" | "amber";
  className?: string;
}

const accentMap = {
  cyan: "text-cyan-400",
  emerald: "text-emerald-400",
  amber: "text-amber-400",
};

export function MetricCard({
  label,
  value,
  sublabel,
  icon: Icon,
  accent = "cyan",
  className,
}: MetricCardProps) {
  return (
    <GlassPanel className={cn("p-4", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-widest text-slate-500">
            {label}
          </p>
          <p className={cn("mt-1 font-mono text-2xl font-semibold tabular-nums", accentMap[accent])}>
            {value}
          </p>
          {sublabel && (
            <p className="mt-0.5 text-xs text-slate-500">{sublabel}</p>
          )}
        </div>
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-2">
          <Icon className={cn("h-4 w-4", accentMap[accent])} />
        </div>
      </div>
    </GlassPanel>
  );
}

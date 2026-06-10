import { cn } from "@/lib/utils";

interface SkeletonFieldProps {
  label: string;
  value: string | null;
  isParsing?: boolean;
  isFilled?: boolean;
}

export function SkeletonField({
  label,
  value,
  isParsing = false,
  isFilled = false,
}: SkeletonFieldProps) {
  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2.5 transition-all duration-500",
        isParsing && "border-cyan-400/40 bg-cyan-400/[0.06] shadow-[0_0_20px_-8px_rgba(34,211,238,0.5)]",
        isFilled && !isParsing && "border-emerald-400/30 bg-emerald-400/[0.04]",
        !isParsing && !isFilled && "border-white/[0.06] bg-white/[0.02]"
      )}
    >
      <p className="text-[10px] font-medium uppercase tracking-widest text-slate-500">
        {label}
      </p>
      {isParsing ? (
        <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-cyan-400/20" />
      ) : value ? (
        <p className="mt-1 text-sm font-medium text-slate-100 transition-opacity duration-500 animate-in fade-in">
          {value}
        </p>
      ) : (
        <p className="mt-1 text-sm text-slate-600">—</p>
      )}
    </div>
  );
}

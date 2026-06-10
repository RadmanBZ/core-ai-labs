import { STATUS_COLORS } from "@/lib/constants";
import { LeadStatus } from "@/lib/types";
import { cn, statusLabel } from "@/lib/utils";

interface StatusBadgeProps {
  status: LeadStatus;
  className?: string;
  pulse?: boolean;
}

export function StatusBadge({ status, className, pulse = false }: StatusBadgeProps) {
  const color = STATUS_COLORS[status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
        className
      )}
      style={{
        color,
        borderColor: `${color}40`,
        backgroundColor: `${color}12`,
      }}
    >
      {pulse && (
        <span
          className="h-1.5 w-1.5 rounded-full animate-pulse"
          style={{ backgroundColor: color }}
        />
      )}
      {statusLabel(status)}
    </span>
  );
}

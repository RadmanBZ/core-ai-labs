import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  glow?: "cyan" | "emerald" | "none";
}

export function GlassPanel({ children, className, glow = "none" }: GlassPanelProps) {
  const glowClass =
    glow === "cyan"
      ? "shadow-[0_0_40px_-12px_rgba(34,211,238,0.25)]"
      : glow === "emerald"
        ? "shadow-[0_0_40px_-12px_rgba(52,211,153,0.25)]"
        : "";

  return (
    <div
      className={cn(
        "rounded-xl border border-white/[0.08] bg-[rgba(12,20,35,0.72)] backdrop-blur-xl",
        glowClass,
        className
      )}
    >
      {children}
    </div>
  );
}

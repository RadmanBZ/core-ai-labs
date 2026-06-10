import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { LeadScoreMetadata, LeadStatus } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function compositeScore(evaluation: LeadScoreMetadata | null): number {
  if (!evaluation) return 0;
  return (
    (evaluation.budget_fit + evaluation.intent_strength + evaluation.authority_level) / 3
  );
}

export function statusLabel(status: LeadStatus): string {
  const labels: Record<LeadStatus, string> = {
    [LeadStatus.QUALIFIED]: "Qualified",
    [LeadStatus.UNQUALIFIED]: "Unqualified",
    [LeadStatus.NURTURING_REQUIRED]: "Nurturing",
    [LeadStatus.PENDING]: "Pending",
  };
  return labels[status];
}

export function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function hashSessionId(id: string): string {
  return `RZ-${id.slice(0, 8).toUpperCase()}`;
}

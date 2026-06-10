import { LeadStatus } from "./types";

export const THEME = {
  base: "#050A12",
  panel: "rgba(12, 20, 35, 0.72)",
  border: "rgba(255, 255, 255, 0.08)",
  cyan: "#22D3EE",
  emerald: "#34D399",
  amber: "#FBBF24",
  rose: "#FB7185",
} as const;

export const STATUS_COLORS: Record<LeadStatus, string> = {
  [LeadStatus.QUALIFIED]: THEME.emerald,
  [LeadStatus.NURTURING_REQUIRED]: THEME.cyan,
  [LeadStatus.UNQUALIFIED]: THEME.rose,
  [LeadStatus.PENDING]: "#94A3B8",
};

export const EXTRACTOR_FIELDS = [
  { key: "customer_name" as const, label: "Customer Name" },
  { key: "company_name" as const, label: "Company" },
  { key: "budget_range" as const, label: "Budget Range" },
  { key: "primary_pain_point" as const, label: "Pain Point" },
  { key: "timeline" as const, label: "Timeline" },
];

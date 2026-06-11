"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LedgerEntry } from "@/lib/types";
import { cn, formatTimestamp, hashSessionId } from "@/lib/utils";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

interface LeadLedgerTableProps {
  entries: LedgerEntry[];
  selectedSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
}

export function LeadLedgerTable({
  entries,
  selectedSessionId,
  onSelectSession,
}: LeadLedgerTableProps) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      (e) =>
        e.session_id.toLowerCase().includes(q) ||
        e.customer_name?.toLowerCase().includes(q) ||
        e.company_name?.toLowerCase().includes(q) ||
        e.budget_range?.toLowerCase().includes(q)
    );
  }, [entries, query]);

  return (
    <GlassPanel className="overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-white/[0.06] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">Lead Management Ledger</h2>
          <p className="text-[10px] text-slate-500">
            High-density CRM view — click any row to open session intelligence
          </p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter sessions…"
            className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] py-2 pl-9 pr-3 text-xs text-slate-200 placeholder:text-slate-600 outline-none transition focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20 sm:w-56"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-wider text-slate-500">
              <th className="px-4 py-3 font-medium">Session ID</th>
              <th className="px-4 py-3 font-medium">Contact</th>
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">Budget</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Priority</th>
              <th className="px-4 py-3 font-medium">Updated</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-slate-600">
                  No ledger entries match your filter.
                </td>
              </tr>
            ) : (
              filtered.map((entry) => {
                const isSelected = selectedSessionId === entry.session_id;
                return (
                  <tr
                    key={entry.session_id}
                    onClick={() => onSelectSession(entry.session_id)}
                    className={cn(
                      "cursor-pointer border-b border-white/[0.04] transition-all duration-200",
                      isSelected
                        ? "bg-cyan-400/[0.08] shadow-[inset_2px_0_0_0_rgba(34,211,238,0.8)]"
                        : "hover:bg-white/[0.03] hover:shadow-[inset_2px_0_0_0_rgba(34,211,238,0.35)]"
                    )}
                  >
                    <td className="px-4 py-3 font-mono text-cyan-300/90">
                      {hashSessionId(entry.session_id)}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {entry.customer_name ?? <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {entry.company_name ?? <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-4 py-3 font-mono text-emerald-300/90">
                      {entry.budget_range ?? <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-4 py-3 font-mono tabular-nums text-slate-300">
                      {entry.composite_score !== null
                        ? entry.composite_score.toFixed(1)
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={entry.status} pulse={isSelected} />
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatTimestamp(entry.updated_at)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
}

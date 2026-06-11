"use client";

import { LeadScoringGauge } from "@/components/analytics/LeadScoringGauge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EXTRACTOR_FIELDS } from "@/lib/constants";
import { PipelineState } from "@/lib/types";
import { cn, hashSessionId } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";
import { Building2, MessageSquare, Sparkles, User, X } from "lucide-react";
import { useEffect } from "react";

interface SessionDetailDrawerProps {
  session: PipelineState | null;
  isOpen: boolean;
  onClose: () => void;
}

export function SessionDetailDrawer({
  session,
  isOpen,
  onClose,
}: SessionDetailDrawerProps) {
  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && session && (
        <>
          <motion.button
            type="button"
            aria-label="Close session details"
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={onClose}
          />

          <motion.aside
            key={session.session_id}
            role="dialog"
            aria-modal="true"
            aria-labelledby="session-detail-title"
            className="fixed inset-y-0 right-0 z-50 flex w-full max-w-5xl flex-col border-l border-white/[0.08] bg-[#040810]/95 shadow-[-24px_0_80px_-20px_rgba(34,211,238,0.15)] backdrop-blur-xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <header className="border-b border-white/[0.06] bg-[#050A12]/90 px-6 py-5">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    <p className="text-[10px] uppercase tracking-[0.28em] text-slate-500">
                      Session Intelligence Deep-Dive
                    </p>
                  </div>
                  <h2
                    id="session-detail-title"
                    className="font-mono text-xl font-semibold tracking-tight text-white"
                  >
                    {hashSessionId(session.session_id)}
                  </h2>
                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    <span className="inline-flex items-center gap-1.5 text-slate-300">
                      <User className="h-3.5 w-3.5 text-cyan-400" />
                      {session.extracted_data.customer_name ?? "Unidentified Contact"}
                    </span>
                    <span className="inline-flex items-center gap-1.5 text-slate-400">
                      <Building2 className="h-3.5 w-3.5 text-emerald-400" />
                      {session.extracted_data.company_name ?? "Company Pending"}
                    </span>
                    <StatusBadge status={session.status} pulse />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-white/[0.08] bg-white/[0.03] p-2 text-slate-400 transition hover:border-rose-400/30 hover:bg-rose-400/10 hover:text-rose-300"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </header>

            <div className="grid flex-1 grid-cols-1 gap-0 overflow-hidden lg:grid-cols-2">
              <section className="flex min-h-0 flex-col border-b border-white/[0.06] lg:border-b-0 lg:border-r">
                <div className="border-b border-white/[0.06] px-5 py-3">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                      Live Agent Stream History
                    </h3>
                  </div>
                </div>
                <div className="flex-1 space-y-3 overflow-y-auto p-5 font-mono text-[13px] leading-relaxed scrollbar-thin">
                  {session.conversation_history.length === 0 ? (
                    <p className="text-center text-sm text-slate-600">
                      No archived dialogue for this session yet.
                    </p>
                  ) : (
                    session.conversation_history.map((message, index) => {
                      const isUser = message.role === "user";
                      return (
                        <motion.div
                          key={`${session.session_id}-${message.role}-${index}`}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.25, delay: index * 0.04 }}
                        >
                          <p
                            className={cn(
                              "mb-1 text-[10px] uppercase tracking-widest",
                              isUser ? "text-cyan-400/80" : "text-emerald-400/80"
                            )}
                          >
                            {isUser ? "[Client/Lead]" : "[Rayza Exec Agent]"}
                          </p>
                          <div
                            className={cn(
                              "rounded-lg px-3 py-2.5",
                              isUser
                                ? "border border-cyan-400/20 bg-cyan-400/[0.06] text-slate-100"
                                : "border border-emerald-400/20 bg-emerald-400/[0.05] text-slate-200"
                            )}
                          >
                            {message.content}
                          </div>
                        </motion.div>
                      );
                    })
                  )}
                </div>
              </section>

              <section className="flex min-h-0 flex-col overflow-y-auto p-5 scrollbar-thin">
                <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Structured Parsing & Scoring Matrix
                </h3>

                <div className="mb-5 grid gap-2">
                  {EXTRACTOR_FIELDS.map(({ key, label }) => (
                    <div
                      key={key}
                      className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2.5"
                    >
                      <p className="text-[10px] uppercase tracking-widest text-slate-500">
                        {label}
                      </p>
                      <p className="mt-1 text-sm text-slate-100">
                        {session.extracted_data[key] ?? (
                          <span className="text-slate-600">—</span>
                        )}
                      </p>
                    </div>
                  ))}
                </div>

                <LeadScoringGauge evaluation={session.evaluation} />

                {session.evaluation?.justification && (
                  <div className="mt-4 rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
                    <p className="text-[10px] uppercase tracking-widest text-slate-500">
                      ScorerAgent Justification
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-300">
                      {session.evaluation.justification}
                    </p>
                  </div>
                )}
              </section>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

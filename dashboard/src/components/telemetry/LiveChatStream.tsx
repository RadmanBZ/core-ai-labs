"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { ConversationMessage } from "@/lib/types";
import { MessageSquare, Terminal } from "lucide-react";
import { useEffect, useRef } from "react";

interface LiveChatStreamProps {
  messages: ConversationMessage[];
  isStreaming: boolean;
}

export function LiveChatStream({ messages, isStreaming }: LiveChatStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <GlassPanel glow="cyan" className="flex h-full min-h-[420px] flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Live Agent Stream</h2>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              Live
            </span>
          )}
          <span className="font-mono text-[10px] text-slate-500">
            {messages.length} events
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto p-4 font-mono text-[13px] leading-relaxed scrollbar-thin"
      >
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-slate-600">
            <MessageSquare className="mb-3 h-8 w-8 opacity-40" />
            <p className="text-sm">Awaiting inbound signal…</p>
            <p className="mt-1 text-xs">
              Inject a live session from the sidebar to begin telemetry capture.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={`${msg.role}-${index}`}
                className="animate-in fade-in slide-in-from-bottom-2 duration-300"
              >
                <p
                  className={
                    isUser
                      ? "mb-1 text-[10px] uppercase tracking-widest text-cyan-400/80"
                      : "mb-1 text-[10px] uppercase tracking-widest text-emerald-400/80"
                  }
                >
                  {isUser ? "[Client/Lead]" : "[Rayza Exec Agent]"}
                </p>
                <div
                  className={
                    isUser
                      ? "rounded-lg rounded-tl-sm border border-cyan-400/20 bg-cyan-400/[0.06] px-3 py-2.5 text-slate-100 transition hover:border-cyan-400/30"
                      : "rounded-lg rounded-tr-sm border border-emerald-400/20 bg-emerald-400/[0.05] px-3 py-2.5 text-slate-200 transition hover:border-emerald-400/30"
                  }
                >
                  {msg.content}
                </div>
              </div>
            );
          })
        )}
        {isStreaming && (
          <div className="flex items-center gap-2 text-cyan-400/60">
            <span className="inline-flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400 [animation-delay:0ms]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400 [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400 [animation-delay:300ms]" />
            </span>
            <span className="text-[10px] uppercase tracking-wider">Processing turn</span>
          </div>
        )}
      </div>
    </GlassPanel>
  );
}

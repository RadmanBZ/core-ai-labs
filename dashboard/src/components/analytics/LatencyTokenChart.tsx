"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { LatencyMetric } from "@/lib/types";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface LatencyTokenChartProps {
  history: LatencyMetric[];
}

export function LatencyTokenChart({ history }: LatencyTokenChartProps) {
  const chartData = history.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
    latency: Math.round(point.latencyMs),
    tokens: Math.round(point.tokens),
  }));

  return (
    <GlassPanel className="p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Latency & Token Efficiency
      </h3>
      <p className="mt-0.5 text-[10px] text-slate-600">
        Real-time response speed and API token burn-rate
      </p>

      <div className="mt-4 h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="latencyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22D3EE" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#22D3EE" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="tokenGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#34D399" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#34D399" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fill: "#64748B", fontSize: 9 }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: "#64748B", fontSize: 9 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(12,20,35,0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#94A3B8" }}
            />
            <Area
              type="monotone"
              dataKey="latency"
              name="Latency (ms)"
              stroke="#22D3EE"
              strokeWidth={2}
              fill="url(#latencyGrad)"
              dot={false}
              activeDot={{ r: 3, fill: "#22D3EE" }}
            />
            <Area
              type="monotone"
              dataKey="tokens"
              name="Tokens"
              stroke="#34D399"
              strokeWidth={1.5}
              fill="url(#tokenGrad)"
              dot={false}
              activeDot={{ r: 3, fill: "#34D399" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassPanel>
  );
}

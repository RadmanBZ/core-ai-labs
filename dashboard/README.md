# Rayza Sales Pipeline — Executive Dashboard

Enterprise B2B telemetry console for the Multi-Agent Sales Pipeline. Noir Tech aesthetic with live mock streaming aligned to `PipelineState` models.

## Stack

- Next.js 14 (App Router) + TypeScript
- Tailwind CSS
- Lucide React
- Recharts

## Run

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use **Inject Live Session** in the sidebar to simulate a full Inbound → Extractor → Scorer pipeline cycle.

## Filesystem

```text
dashboard/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout, fonts, metadata
│   │   ├── page.tsx            # Dashboard entry
│   │   └── globals.css         # Noir theme tokens
│   ├── components/
│   │   ├── dashboard/
│   │   │   └── DashboardClient.tsx
│   │   ├── shell/
│   │   │   └── Sidebar.tsx
│   │   ├── telemetry/
│   │   │   ├── LiveChatStream.tsx
│   │   │   └── AgentStateMonitor.tsx
│   │   ├── analytics/
│   │   │   ├── LeadScoringGauge.tsx
│   │   │   ├── PipelineFunnelChart.tsx
│   │   │   └── LatencyTokenChart.tsx
│   │   ├── crm/
│   │   │   └── LeadLedgerTable.tsx
│   │   └── ui/
│   │       ├── GlassPanel.tsx
│   │       ├── StatusBadge.tsx
│   │       ├── MetricCard.tsx
│   │       └── SkeletonField.tsx
│   ├── hooks/
│   │   └── usePipelineStream.ts
│   └── lib/
│       ├── types.ts            # Mirrors Python Pydantic models
│       ├── mock-stream.ts      # WebSocket-style event simulator
│       ├── constants.ts
│       └── utils.ts
├── package.json
└── tailwind.config.ts
```

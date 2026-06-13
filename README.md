# 🌌 Core AI Labs (core-ai-labs)

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Multi--Agent-050A12?style=for-the-badge&logo=ai&logoColor=00E5FF" alt="Architecture" />
  <img src="https://img.shields.io/badge/Core-Google%20Gemini%201.5-blue?style=for-the-badge&logo=google&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/Runtime-Asynchronous%20AsyncIO-🟢?style=for-the-badge" alt="Runtime" />
</p>

Welcome to **Core AI Labs**, an elite, production-grade research and development monorepo dedicated to cutting-edge artificial intelligence architectures, high-throughput data processing pipelines, and sub-second latency automation systems. 

This repository serves as a master portfolio of enterprise-level, production-ready AI systems engineered with strict software craftsmanship, algorithmic optimization, and strategic business viability.

---

## 💎 Core Philosophy & Engineering Standards

Every pipeline, agent, and engine incubated in this repository adheres to high-end software development paradigms:

* **⚡ Sub-Second Real-Time Latency:** Eliminating heavy framework overheads (e.g., LangChain/CrewAI) by implementing clean, native asynchronous workflows (`asyncio` concurrent routing loops).
* **🛡️ Strict Structural Type-Safety:** Total enforcement of runtime validation schemas leveraging Pydantic V2 and Gemini structured JSON outputs.
* **📈 Corporate Metric-Driven Design:** Every module built is engineered to solve a high-stakes business pain point, directly scaling conversion rates or radically minimizing operational overhead.
* **📺 Deterministic Telemetry & Observability:** Production-ready colorized logging systems mapping absolute operational states and background data extractions.

---
Front-End
cd dashboard
npm run dev

Back-End
cd modules/sales_agent_pipeline
python demo_cli.py
---


## 🏗️ Monorepo Architectural Layout

The repository is organized as a modular, decoupled suite of tools, allowing for isolation of dependencies and optimal package resolution traversal:

```text
core-ai-labs/
│
├── modules/
│   └── sales_agent_pipeline/      # [ACTIVE] Multi-Agent B2B Sales & Qualification Suite
│       ├── core/                  # Conversational, background extraction, and scoring engines
│       ├── utils/                 # Native telemetry, state loggers, and formatters
│       ├── tests/                 # Asynchronous unit testing suite via pytest
│       ├── config.py              # Central system prompt engineering maps
│       ├── models.py              # Pydantic data schemas & state models
│       └── demo_cli.py            # Asynchronous terminal interface entrypoint
│
├── dashboard/                     # Next.js 14 Premium Executive Analytical Dashboard Frontend
├── requirements.txt               # Unified environment dependency registry
└── README.md                      # Global workspace blueprint
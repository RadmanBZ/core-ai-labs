# Multi-Agent B2B Sales & Qualifier Pipeline

An enterprise-grade, high-performance asynchronous multi-agent system designed to automatically engage corporate leads, extract structured commercial metadata, and algorithmically evaluate and score conversion viability.

## Architecture Blueprint

The ecosystem deploys a native, non-blocking cascading agent network utilizing raw asynchronous loops to ensure sub-second interaction throughput:

1. **Inbound Agent:** Manages conversational state flow using sophisticated B2B positioning strategies.
2. **Extractor Agent:** Continuously runs in the background leveraging strict structural schema parsing to isolate customer pain points, corporate budgets, and timelines into JSON models.
3. **Scorer Agent:** Evaluates parameters across custom matrix fields to calculate qualification status (`QUALIFIED`, `NURTURING_REQUIRED`, `UNQUALIFIED`).

## Quick Start

### 1. Provision Dependencies
```bash
pip install -r requirements.txt
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from modules.sales_agent_pipeline.models import LeadStatus, PipelineState
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

_REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_STATE_PATH = _REPO_ROOT / "shared_state.json"
TELEMETRY_API_URL = "http://localhost:3000/api/telemetry"

_accumulator: dict[str, Any] = {
    "funnel_distribution": {
        LeadStatus.QUALIFIED.value: 0,
        LeadStatus.NURTURING_REQUIRED.value: 0,
        LeadStatus.UNQUALIFIED.value: 0,
        LeadStatus.PENDING.value: 1,
    },
    "latency_history": [],
    "ledger": [],
    "active_sessions": 0,
    "last_status": None,
}


def _composite_score(state: PipelineState) -> float | None:
    if not state.evaluation:
        return None
    scores = state.evaluation
    return (scores.budget_fit + scores.intent_strength + scores.authority_level) / 3.0


def _build_payload(state: PipelineState, latency_ms: int = 420) -> dict[str, Any]:
    global _accumulator

    if _accumulator["last_status"] != state.status.value:
        previous = _accumulator["last_status"]
        if previous and previous in _accumulator["funnel_distribution"]:
            _accumulator["funnel_distribution"][previous] = max(
                0, _accumulator["funnel_distribution"][previous] - 1
            )
        _accumulator["funnel_distribution"][state.status.value] = (
            _accumulator["funnel_distribution"].get(state.status.value, 0) + 1
        )
        _accumulator["last_status"] = state.status.value

    metric = {
        "timestamp": int(time.time() * 1000),
        "latencyMs": latency_ms,
        "tokens": 180 + len(state.conversation_history) * 40,
    }
    _accumulator["latency_history"] = (
        _accumulator["latency_history"][-23:] + [metric]
    )
    _accumulator["active_sessions"] = max(1, _accumulator["active_sessions"])

    ledger_entry = {
        "session_id": state.session_id,
        "customer_name": state.extracted_data.customer_name,
        "company_name": state.extracted_data.company_name,
        "budget_range": state.extracted_data.budget_range,
        "status": state.status.value,
        "composite_score": _composite_score(state),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    existing_ids = {entry["session_id"] for entry in _accumulator["ledger"]}
    if state.session_id in existing_ids:
        _accumulator["ledger"] = [
            ledger_entry if entry["session_id"] == state.session_id else entry
            for entry in _accumulator["ledger"]
        ]
    else:
        _accumulator["ledger"] = [ledger_entry, *_accumulator["ledger"]]

    return {
        "session": state.model_dump(mode="json"),
        "agentPhase": "complete",
        "isStreaming": False,
        "telemetry": {
            "nodeHealth": {
                "inbound": "online",
                "extractor": "online",
                "scorer": "online",
                "orchestrator": "online",
            },
            "pipelineLatencyMs": latency_ms,
            "activeSessions": _accumulator["active_sessions"],
            "latencyHistory": _accumulator["latency_history"],
            "funnelDistribution": _accumulator["funnel_distribution"],
        },
        "ledger": _accumulator["ledger"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _write_shared_state(payload: dict[str, Any]) -> None:
    SHARED_STATE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _post_payload(url: str, payload: dict[str, Any]) -> bool:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            return response.status == 200
    except (error.URLError, TimeoutError, OSError):
        return False


async def push_telemetry(state: PipelineState, latency_ms: int = 420) -> None:
    """Publish pipeline state to shared JSON and the Next.js telemetry API."""
    payload = _build_payload(state, latency_ms=latency_ms)

    def _persist() -> tuple[bool, bool]:
        file_ok = False
        api_ok = False
        try:
            _write_shared_state(payload)
            file_ok = True
        except OSError as exc:
            logger.warning(f"Shared state write failed: {exc}")
        api_ok = _post_payload(TELEMETRY_API_URL, payload)
        return file_ok, api_ok

    file_ok, api_ok = await asyncio.to_thread(_persist)

    if file_ok and api_ok:
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"Status {state.status.value} | API + shared_state.json"
        )
    elif file_ok:
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"Status {state.status.value} | shared_state.json (dashboard offline)"
        )
    elif api_ok:
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"Status {state.status.value} | API only"
        )
    else:
        logger.warning("Telemetry bridge sync failed — no file or API target available")

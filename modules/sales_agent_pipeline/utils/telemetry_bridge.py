import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.models import LeadStatus, PipelineState
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

_REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_STATE_PATH = _REPO_ROOT / "shared_state.json"

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


def _extract_port(url: str) -> int:
    # http://localhost:4000/api/telemetry -> 4000
    return int(url.split(":")[2].split("/")[0])


def _post_payload(url: str, payload: dict[str, Any]) -> tuple[bool, int | None, str | None]:
    """POST telemetry payload; returns (success, http_status, error_message)."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            status = response.status
            if status == 200:
                return True, status, None
            return False, status, f"HTTP {status}"
    except error.HTTPError as exc:
        return False, exc.code, f"HTTP {exc.code}: {exc.reason}"
    except error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, None, f"URLError: {reason}"
    except TimeoutError:
        return False, None, "TimeoutError: connection timed out after 3s"
    except OSError as exc:
        return False, None, f"OSError: {exc}"


def _push_with_port_fallback(payload: dict[str, Any]) -> tuple[bool, int | None, str | None]:
    """Try configured port first, then fall back across supported dashboard ports."""
    errors: list[str] = []

    for url in PipelineConfig.telemetry_api_urls():
        port = _extract_port(url)
        success, status, err = _post_payload(url, payload)
        if success:
            return True, port, None

        detail = err or (f"HTTP {status}" if status else "unknown error")
        errors.append(f"localhost:{port} -> {detail}")
        logger.debug(f"Telemetry handshake failed on port {port}: {detail}")

    return False, None, " | ".join(errors)


async def push_telemetry(state: PipelineState, latency_ms: int = 420) -> None:
    """Publish pipeline state to shared JSON and the Next.js telemetry API."""
    payload = _build_payload(state, latency_ms=latency_ms)

    def _persist() -> tuple[bool, bool, int | None, str | None]:
        file_ok = False
        api_ok = False
        synced_port: int | None = None
        api_error: str | None = None

        try:
            _write_shared_state(payload)
            file_ok = True
        except OSError as exc:
            logger.warning(f"Shared state write failed: {exc}")

        api_ok, synced_port, api_error = _push_with_port_fallback(payload)
        return file_ok, api_ok, synced_port, api_error

    file_ok, api_ok, synced_port, api_error = await asyncio.to_thread(_persist)

    if api_ok and synced_port:
        success_msg = (
            f"[SUCCESS] Telemetry Bridge Active -> Dashboard Synced on Port {synced_port}"
        )
        print(success_msg)
        logger.info(success_msg)
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"Status {state.status.value} | API:{synced_port} + shared_state.json"
            if file_ok
            else f"Telemetry bridge synced | Session {state.session_id} | API:{synced_port}"
        )
    elif file_ok:
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"Status {state.status.value} | shared_state.json (dashboard offline)"
        )
        if api_error:
            print(f"[ERROR] Telemetry Bridge Failed -> {api_error}")
            logger.warning(f"Telemetry bridge API unreachable: {api_error}")
    else:
        print(f"[ERROR] Telemetry Bridge Failed -> {api_error or 'no targets available'}")
        logger.warning(
            f"Telemetry bridge sync failed — {api_error or 'no file or API target available'}"
        )

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

_sessions_store: dict[str, dict[str, Any]] = {}
_session_status_map: dict[str, str] = {}
_hydrated = False

_accumulator: dict[str, Any] = {
    "funnel_distribution": {
        LeadStatus.QUALIFIED.value: 0,
        LeadStatus.NURTURING_REQUIRED.value: 0,
        LeadStatus.UNQUALIFIED.value: 0,
        LeadStatus.PENDING.value: 0,
    },
    "latency_history": [],
    "ledger": [],
}


def _composite_score(state: PipelineState) -> float | None:
    if not state.evaluation:
        return None
    scores = state.evaluation
    return (scores.budget_fit + scores.intent_strength + scores.authority_level) / 3.0


def _hydrate_from_disk() -> None:
    global _hydrated
    if _hydrated or not SHARED_STATE_PATH.exists():
        _hydrated = True
        return

    try:
        payload = json.loads(SHARED_STATE_PATH.read_text(encoding="utf-8"))
        for session in payload.get("sessions", []):
            _sessions_store[session["session_id"]] = session
        for entry in payload.get("ledger", []):
            if entry["session_id"] not in {e["session_id"] for e in _accumulator["ledger"]}:
                _accumulator["ledger"].append(entry)
        telemetry = payload.get("telemetry", {})
        if telemetry.get("funnelDistribution"):
            _accumulator["funnel_distribution"] = telemetry["funnelDistribution"]
        if telemetry.get("latencyHistory"):
            _accumulator["latency_history"] = telemetry["latencyHistory"]
        for session in _sessions_store.values():
            _session_status_map[session["session_id"]] = session.get("status", LeadStatus.PENDING.value)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.debug(f"Telemetry hydrate skipped: {exc}")
    finally:
        _hydrated = True


def _update_funnel_for_session(session_id: str, status: str) -> None:
    previous = _session_status_map.get(session_id)
    if previous == status:
        return

    funnel = _accumulator["funnel_distribution"]
    if previous and previous in funnel:
        funnel[previous] = max(0, funnel[previous] - 1)
    funnel[status] = funnel.get(status, 0) + 1
    _session_status_map[session_id] = status


def _upsert_session(state: PipelineState) -> None:
    _sessions_store[state.session_id] = state.model_dump(mode="json")
    _update_funnel_for_session(state.session_id, state.status.value)


def _upsert_ledger_entry(state: PipelineState) -> None:
    ledger_entry = {
        "session_id": state.session_id,
        "customer_name": state.extracted_data.customer_name,
        "company_name": state.extracted_data.company_name,
        "budget_range": state.extracted_data.budget_range,
        "status": state.status.value,
        "composite_score": _composite_score(state),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    ledger = _accumulator["ledger"]
    for index, entry in enumerate(ledger):
        if entry["session_id"] == state.session_id:
            ledger[index] = ledger_entry
            return
    _accumulator["ledger"] = [ledger_entry, *ledger]


def _build_payload(state: PipelineState, latency_ms: int = 420) -> dict[str, Any]:
    _hydrate_from_disk()
    _upsert_session(state)
    _upsert_ledger_entry(state)

    metric = {
        "timestamp": int(time.time() * 1000),
        "latencyMs": latency_ms,
        "tokens": 180 + len(state.conversation_history) * 40,
    }
    _accumulator["latency_history"] = _accumulator["latency_history"][-23:] + [metric]

    sessions = sorted(
        _sessions_store.values(),
        key=lambda item: item.get("session_id", ""),
        reverse=True,
    )

    return {
        "session": _sessions_store[state.session_id],
        "activeSessionId": state.session_id,
        "sessions": sessions,
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
            "activeSessions": len(_sessions_store),
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
    return int(url.split(":")[2].split("/")[0])


def _post_payload(url: str, payload: dict[str, Any]) -> tuple[bool, int | None, str | None]:
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
            f"Status {state.status.value} | Sessions={len(_sessions_store)} | "
            f"Ledger={len(_accumulator['ledger'])}"
        )
    elif file_ok:
        logger.info(
            f"Telemetry bridge synced | Session {state.session_id} | "
            f"shared_state.json (dashboard offline)"
        )
        if api_error:
            print(f"[ERROR] Telemetry Bridge Failed -> {api_error}")
            logger.warning(f"Telemetry bridge API unreachable: {api_error}")
    else:
        print(f"[ERROR] Telemetry Bridge Failed -> {api_error or 'no targets available'}")
        logger.warning(
            f"Telemetry bridge sync failed — {api_error or 'no file or API target available'}"
        )

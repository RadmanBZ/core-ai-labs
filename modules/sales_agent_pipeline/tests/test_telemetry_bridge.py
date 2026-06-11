import json
import pytest

from modules.sales_agent_pipeline.models import (
    ExtractedLeadInfo,
    LeadScoreMetadata,
    LeadStatus,
    PipelineState,
)
from modules.sales_agent_pipeline.utils import telemetry_bridge


@pytest.mark.asyncio
async def test_telemetry_bridge_writes_shared_state(tmp_path, monkeypatch):
    shared_file = tmp_path / "shared_state.json"
    monkeypatch.setattr(telemetry_bridge, "SHARED_STATE_PATH", shared_file)
    monkeypatch.setattr(telemetry_bridge, "_sessions_store", {})
    monkeypatch.setattr(telemetry_bridge, "_session_status_map", {})
    monkeypatch.setattr(telemetry_bridge, "_hydrated", True)
    monkeypatch.setattr(
        telemetry_bridge,
        "_push_with_port_fallback",
        lambda *_args, **_kwargs: (False, None, "mock offline"),
    )

    state = PipelineState(
        session_id="test-abc",
        extracted_data=ExtractedLeadInfo(
            customer_name="رادمان",
            company_name="آژانس املاک",
            budget_range="5,000 OMR (ریال عمان)",
            primary_pain_point="راه‌اندازی کال‌سنتر هوشمند",
            timeline="فوری",
        ),
        evaluation=LeadScoreMetadata(
            budget_fit=10,
            intent_strength=9,
            authority_level=8,
            justification="High-value bilingual sandbox lead.",
        ),
        status=LeadStatus.QUALIFIED,
        conversation_history=[
            {"role": "user", "content": "من رادمان هستم"},
            {"role": "assistant", "content": "با درود و احترام"},
        ],
    )

    await telemetry_bridge.push_telemetry(state)

    assert shared_file.exists()
    payload = json.loads(shared_file.read_text(encoding="utf-8"))
    assert payload["session"]["extracted_data"]["customer_name"] == "رادمان"
    assert payload["session"]["status"] == "QUALIFIED"
    assert payload["telemetry"]["funnelDistribution"]["QUALIFIED"] >= 1
    assert payload["ledger"][0]["session_id"] == "test-abc"
    assert payload["activeSessionId"] == "test-abc"
    assert len(payload["sessions"]) == 1

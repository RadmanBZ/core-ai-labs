import json
import pytest

from modules.sales_agent_pipeline.core.sandbox_engine import extract_customer_identity
from modules.sales_agent_pipeline.models import (
    ExtractedLeadInfo,
    LeadScoreMetadata,
    LeadStatus,
    PipelineState,
)
from modules.sales_agent_pipeline.utils.session_manager import (
    evaluate_session_routing,
    format_session_label,
    identities_match,
    is_new_session_command,
    should_cycle_session,
)
from modules.sales_agent_pipeline.utils import telemetry_bridge


def test_new_session_command_detection():
    assert is_new_session_command("/new") is True
    assert is_new_session_command("/reset") is True
    assert is_new_session_command("hello") is False


def test_extract_maryam_short_persian_intro():
    assert extract_customer_identity("مریم هستم بودجه ۴۰۰ ریال عمان دارم") == "مریم"


def test_identity_shift_radman_to_ali():
    state = PipelineState(
        session_id="radman-01",
        extracted_data=ExtractedLeadInfo(customer_name="رادمان"),
        evaluation=LeadScoreMetadata(
            budget_fit=9,
            intent_strength=8,
            authority_level=8,
            justification="Qualified lead.",
        ),
        conversation_history=[{"role": "user", "content": "من رادمان هستم"}],
        status=LeadStatus.QUALIFIED,
    )

    assert should_cycle_session(state, "من علی البلوشی هستم") is True
    assert should_cycle_session(state, "سلام دوباره") is False


def test_identity_shift_ali_to_maryam_chain():
    ali_state = PipelineState(
        session_id="227712d9",
        extracted_data=ExtractedLeadInfo(
            customer_name="Ali Al-Balooshi",
            budget_range="50,000 OMR",
        ),
        evaluation=LeadScoreMetadata(
            budget_fit=10,
            intent_strength=9,
            authority_level=8,
            justification="Qualified Ali lead.",
        ),
        conversation_history=[
            {"role": "user", "content": "I'm Ali Al-Balooshi, budget 50,000 OMR"},
            {"role": "assistant", "content": "Thank you Ali."},
        ],
        status=LeadStatus.QUALIFIED,
    )

    routing = evaluate_session_routing(ali_state, "مریم هستم بودجه ۴۰۰ ریال عمان")
    assert routing.should_cycle is True
    assert routing.incoming_identity == "مریم"


def test_identities_match_partial_english_names():
    assert identities_match("Ali", "Ali Al-Balooshi") is True
    assert identities_match("Ali Al-Balooshi", "Maryam") is False


def test_format_session_label():
    assert format_session_label("71370232") == "RZ-713702"


@pytest.mark.asyncio
async def test_multi_session_ledger_appends_three_leads(tmp_path, monkeypatch):
    shared_file = tmp_path / "shared_state.json"
    monkeypatch.setattr(telemetry_bridge, "SHARED_STATE_PATH", shared_file)
    monkeypatch.setattr(telemetry_bridge, "_sessions_store", {})
    monkeypatch.setattr(telemetry_bridge, "_session_status_map", {})
    monkeypatch.setattr(telemetry_bridge, "_hydrated", True)
    monkeypatch.setattr(
        telemetry_bridge,
        "_accumulator",
        {
            "funnel_distribution": {
                "QUALIFIED": 0,
                "NURTURING_REQUIRED": 0,
                "UNQUALIFIED": 0,
                "PENDING": 0,
            },
            "latency_history": [],
            "ledger": [],
        },
    )
    monkeypatch.setattr(
        telemetry_bridge,
        "_push_with_port_fallback",
        lambda *_args, **_kwargs: (False, None, "mock offline"),
    )

    radman = PipelineState(
        session_id="sess-rad",
        extracted_data=ExtractedLeadInfo(customer_name="رادمان", budget_range="5,000 OMR"),
        evaluation=LeadScoreMetadata(
            budget_fit=10, intent_strength=9, authority_level=8, justification="Lead one"
        ),
        status=LeadStatus.QUALIFIED,
        conversation_history=[{"role": "user", "content": "من رادمان هستم"}],
    )
    ali = PipelineState(
        session_id="sess-ali",
        extracted_data=ExtractedLeadInfo(
            customer_name="Ali Al-Balooshi", budget_range="50,000 OMR"
        ),
        evaluation=LeadScoreMetadata(
            budget_fit=10, intent_strength=9, authority_level=8, justification="Lead two"
        ),
        status=LeadStatus.QUALIFIED,
        conversation_history=[{"role": "user", "content": "I'm Ali Al-Balooshi"}],
    )
    maryam = PipelineState(
        session_id="sess-mry",
        extracted_data=ExtractedLeadInfo(customer_name="مریم", budget_range="400 OMR"),
        evaluation=LeadScoreMetadata(
            budget_fit=7, intent_strength=6, authority_level=6, justification="Lead three"
        ),
        status=LeadStatus.NURTURING_REQUIRED,
        conversation_history=[{"role": "user", "content": "مریم هستم بودجه ۴۰۰ ریال عمان"}],
    )

    await telemetry_bridge.push_telemetry(radman)
    await telemetry_bridge.push_telemetry(ali)
    await telemetry_bridge.push_telemetry(maryam)

    payload = json.loads(shared_file.read_text(encoding="utf-8"))
    assert len(payload["sessions"]) == 3
    assert len(payload["ledger"]) == 3
    assert payload["activeSessionId"] == "sess-mry"
    ledger_names = {entry["customer_name"] for entry in payload["ledger"]}
    assert {"رادمان", "Ali Al-Balooshi", "مریم"} <= ledger_names

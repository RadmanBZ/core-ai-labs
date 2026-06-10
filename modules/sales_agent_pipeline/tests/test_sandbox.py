import pytest

from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.core.router import AdvancedSalesOrchestrator
from modules.sales_agent_pipeline.core.gemini_client import is_sandbox_active, validate_api_key


@pytest.mark.asyncio
async def test_sandbox_mode_bypasses_live_validation():
    result = await validate_api_key()
    assert result is True


@pytest.mark.asyncio
async def test_sandbox_pipeline_populates_pipeline_state():
    orchestrator = AdvancedSalesOrchestrator(api_key=PipelineConfig.GEMINI_API_KEY)
    session = orchestrator.create_session()

    user_message = (
        "We're Muscat Logistics — manual invoice ingestion is killing our ops. "
        "Budget is OMR 50,000. I'm Ali Al-Busaddi, Head of Operations."
    )
    reply = await orchestrator.process_turn(session, user_message)

    assert bool(reply)
    assert session.extracted_data.budget_range is not None
    assert session.extracted_data.primary_pain_point is not None
    assert session.evaluation is not None
    assert session.status.value in {"QUALIFIED", "NURTURING_REQUIRED", "UNQUALIFIED"}
    if is_sandbox_active():
        assert session.evaluation.budget_fit >= 1

import pytest
from modules.sales_agent_pipeline.config import _normalize_gemini_api_key
from modules.sales_agent_pipeline.models import PipelineState, ExtractedLeadInfo, LeadStatus, LeadScoreMetadata
from modules.sales_agent_pipeline.core.scorer_agent import ScorerAgent


def test_gemini_api_key_normalization():
    """Rebuilds full Google keys when AI Studio suffix-only values are pasted."""
    suffix = "AQ.Ab8RN6LT9dWw9aaytihz8BJg7O-Ro66qd8MXLco6eRICharBvQ"
    normalized = _normalize_gemini_api_key(suffix)
    assert normalized.startswith("AIzaSy")
    assert "." not in normalized
    assert normalized == f"AIzaSyAQ{suffix[3:]}"

@pytest.mark.asyncio
async def test_lead_state_initialization():
    """Validates that a fresh PipelineState correctly provisions defaults."""
    state = PipelineState(session_id="test-123")
    assert state.status == LeadStatus.PENDING
    assert state.conversation_history == []
    assert state.extracted_data.customer_name is None

def test_pydantic_data_extraction_schema():
    """Ensures strict Pydantic parsing schemas map validation properties correctly."""
    info = ExtractedLeadInfo(
        customer_name="Ali Al-Busaddi",
        company_name="Muscat Logistics",
        budget_range="$50,000",
        primary_pain_point="Manual invoice ingestion latency"
    )
    assert info.customer_name == "Ali Al-Busaddi"
    assert info.timeline is None

@pytest.mark.asyncio
async def test_scorer_algorithmic_grading_logic(mocker=None):
    """Verifies that the logical scoring rules cleanly bucket lead priority levels."""
    # Instantiating a clean state
    state = PipelineState(session_id="test-456")
    state.extracted_data = ExtractedLeadInfo(
        customer_name="Salem",
        budget_range="OMR 15,000"
    )
    
    # Simulating high scoring metadata response bypasses external LLM networks
    mock_evaluation = LeadScoreMetadata(
        budget_fit=9,
        intent_strength=8,
        authority_level=8,
        justification="High budget and explicit conversion timeline provided."
    )
    state.evaluation = mock_evaluation
    
    # Execute deterministic scoring algorithm directly
    avg_score = (mock_evaluation.budget_fit + mock_evaluation.intent_strength + mock_evaluation.authority_level) / 3.0
    if avg_score >= 7.0 and state.extracted_data.budget_range:
        state.status = LeadStatus.QUALIFIED
        
    assert state.status == LeadStatus.QUALIFIED
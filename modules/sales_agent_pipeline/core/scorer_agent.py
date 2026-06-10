from modules.sales_agent_pipeline.core.gemini_client import generate_structured
from modules.sales_agent_pipeline.models import LeadScoreMetadata, LeadStatus, PipelineState


class ScorerAgent:
    """Decision-making agent that calculates the lead viability score and computes status."""

    async def execute(self, state: PipelineState) -> PipelineState:
        """Evaluates extracted lead criteria and updates lead operational pipeline state."""
        data = state.extracted_data

        prompt = (
            f"Review this structured corporate client data:\n"
            f"Name: {data.customer_name}, Company: {data.company_name}, Budget: {data.budget_range}, "
            f"Pain Point: {data.primary_pain_point}, Timeline: {data.timeline}.\n\n"
            "Score each parameter out of 10 and write your engineering justification."
        )

        score_meta = await generate_structured(
            prompt,
            LeadScoreMetadata,
            system_instruction=(
                "You are a B2B lead qualification analyst. "
                "Score leads objectively using the required schema fields only."
            ),
            temperature=0.0,
        )

        state.evaluation = score_meta

        avg_score = (
            score_meta.budget_fit + score_meta.intent_strength + score_meta.authority_level
        ) / 3.0

        if avg_score >= 7.0 and data.budget_range:
            state.status = LeadStatus.QUALIFIED
        elif 4.0 <= avg_score < 7.0:
            state.status = LeadStatus.NURTURING_REQUIRED
        else:
            state.status = LeadStatus.UNQUALIFIED

        return state

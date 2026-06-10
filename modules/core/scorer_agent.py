from openai import AsyncOpenAI
from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.models import PipelineState, LeadScoreMetadata, LeadStatus

class ScorerAgent:
    """Decision-making agent that calculates the lead viability score and computes status."""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def execute(self, state: PipelineState) -> PipelineState:
        """Evaluates extracted lead criteria and updates lead operational pipeline state."""
        data = state.extracted_data
        
        prompt = (
            f"Review this structured corporate client data:\n"
            f"Name: {data.customer_name}, Company: {data.company_name}, Budget: {data.budget_range}, "
            f"Pain Point: {data.primary_pain_point}, Timeline: {data.timeline}.\n\n"
            "Score each parameter out of 10 and write your engineering justification."
        )

        response = await self.client.beta.chat.completions.parse(
            model=PipelineConfig.DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=LeadScoreMetadata,
            temperature=0.0
        )

        score_meta = response.choices[0].message.parsed
        state.evaluation = score_meta

        # Business Logic Algorithm: Quantifying conversion viability
        avg_score = (score_meta.budget_fit + score_meta.intent_strength + score_meta.authority_level) / 3.0

        if avg_score >= 7.0 and data.budget_range:
            state.status = LeadStatus.QUALIFIED
        elif 4.0 <= avg_score < 7.0:
            state.status = LeadStatus.NURTURING_REQUIRED
        else:
            state.status = LeadStatus.UNQUALIFIED

        return state
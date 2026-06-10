from openai import AsyncOpenAI
from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.models import PipelineState, ExtractedLeadInfo

class ExtractorAgent:
    """Background intelligence agent that extracts structured criteria from conversation logs."""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def execute(self, state: PipelineState) -> ExtractedLeadInfo:
        """Analyzes history and forces the LLM to output a strictly formatted Pydantic dataset."""
        if not state.conversation_history:
            return state.extracted_data

        prompt = (
            "Analyze the following conversation logs and carefully extract the B2B lead specifications. "
            "If a field is missing, leave it as null. Do not hallucinate data.\n\n"
            f"Logs:\n{state.conversation_history}"
        )

        # Utilizing strict json/pydantic parsing schema from OpenAI
        response = await self.client.beta.chat.completions.parse(
            model=PipelineConfig.DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=ExtractedLeadInfo,
            temperature=0.0
        )
        
        extracted_info = response.choices[0].message.parsed
        state.extracted_data = extracted_info
        return extracted_info

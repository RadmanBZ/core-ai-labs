from modules.sales_agent_pipeline.core.gemini_client import generate_structured
from modules.sales_agent_pipeline.models import ExtractedLeadInfo, PipelineState


class ExtractorAgent:
    """Background intelligence agent that extracts structured criteria from conversation logs."""

    async def execute(self, state: PipelineState) -> ExtractedLeadInfo:
        """Analyzes history and forces Gemini to output a strictly formatted Pydantic dataset."""
        if not state.conversation_history:
            return state.extracted_data

        prompt = (
            "Analyze the following conversation logs and carefully extract the B2B lead specifications. "
            "If a field is missing, return null for that field. Do not hallucinate data.\n\n"
            f"Logs:\n{state.conversation_history}"
        )

        extracted_info = await generate_structured(
            prompt,
            ExtractedLeadInfo,
            system_instruction=(
                "You are a precision B2B data extraction engine. "
                "Return only structured lead intelligence matching the required schema."
            ),
            temperature=0.0,
        )

        state.extracted_data = extracted_info
        return extracted_info

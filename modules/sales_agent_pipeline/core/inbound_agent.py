from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.core.gemini_client import generate_text, to_gemini_history
from modules.sales_agent_pipeline.models import PipelineState


class InboundAgent:
    """First-line AI Agent responsible for managing high-touch corporate conversations."""

    async def execute(self, state: PipelineState, user_input: str) -> str:
        """Appends user message, runs inference, and updates global conversation history."""
        state.conversation_history.append({"role": "user", "content": user_input})

        prior_history = to_gemini_history(state.conversation_history[:-1])
        ai_reply = await generate_text(
            user_input,
            system_instruction=PipelineConfig.INBOUND_SYSTEM_PROMPT,
            history=prior_history,
            temperature=0.4,
        )

        state.conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply

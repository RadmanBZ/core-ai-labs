from openai import AsyncOpenAI
from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.models import PipelineState

class InboundAgent:
    """First-line AI Agent responsible for managing high-touch corporate conversations."""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def execute(self, state: PipelineState, user_input: str) -> str:
        """Appends user message, runs inference, and updates global conversation history."""
        state.conversation_history.append({"role": "user", "content": user_input})
        
        messages = [{"role": "system", "content": PipelineConfig.INBOUND_SYSTEM_PROMPT}]
        messages.extend(state.conversation_history)

        response = await self.client.chat.completions.create(
            model=PipelineConfig.DEFAULT_MODEL,
            messages=messages,
            temperature=0.4
        )
        
        ai_reply = response.choices[0].message.content
        state.conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply
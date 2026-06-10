import uuid
from openai import AsyncOpenAI
from modules.sales_agent_pipeline.models import PipelineState, LeadStatus
from modules.sales_agent_pipeline.core.inbound_agent import InboundAgent
from modules.sales_agent_pipeline.core.extractor_agent import ExtractorAgent
from modules.sales_agent_pipeline.core.scorer_agent import ScorerAgent
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

class AdvancedSalesOrchestrator:
    """The master runtime engine coordinating asynchronous workflow transitions between all AI agents."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.inbound = InboundAgent(self.client)
        self.extractor = ExtractorAgent(self.client)
        self.scorer = ScorerAgent(self.client)

    def create_session(self) -> PipelineState:
        """Generates a fresh state session for a new corporate contact client."""
        session_id = str(uuid.uuid4())[:8]
        logger.info(f"Initialized secure session tracking: Session-{session_id}")
        return PipelineState(session_id=session_id)

    async def process_turn(self, state: PipelineState, user_message: str) -> str:
        """Executes one full asynchronous pipeline cycle: Inbound -> Extractor -> Scorer evaluation."""
        logger.debug(f"[Session {state.session_id}] Processing incoming B2B chunk...")
        
        # 1. Run conversational fronting
        reply = await self.inbound.execute(state, user_message)
        
        # 2. Extract meta indicators concurrently backgrounded
        await self.extractor.execute(state)
        
        # 3. Grade intent profile matrix
        await self.scorer.execute(state)
        
        logger.info(
            f"[Session {state.session_id}] Telemetry Status: {state.status.value} | "
            f"Budget Fit Score: {state.evaluation.budget_fit if state.evaluation else 0}/10"
        )
        return reply
import uuid

from modules.sales_agent_pipeline.core.extractor_agent import ExtractorAgent
from modules.sales_agent_pipeline.core.gemini_client import configure_gemini, is_sandbox_active
from modules.sales_agent_pipeline.core.inbound_agent import InboundAgent
from modules.sales_agent_pipeline.core.scorer_agent import ScorerAgent
from modules.sales_agent_pipeline.models import PipelineState
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger
from modules.sales_agent_pipeline.utils.telemetry_bridge import push_telemetry

logger = get_pipeline_logger()


class AdvancedSalesOrchestrator:
    """The master runtime engine coordinating asynchronous workflow transitions between all AI agents."""

    def __init__(self, api_key: str):
        configure_gemini(api_key)
        self.inbound = InboundAgent()
        self.extractor = ExtractorAgent()
        self.scorer = ScorerAgent()

        if is_sandbox_active():
            logger.info(
                "Pipeline booted in Autonomous Local Sandbox Mode - "
                "gemini-1.5-flash emulation active (no live Google network calls)."
            )

    def create_session(self) -> PipelineState:
        """Generates a fresh state session for a new corporate contact client."""
        session_id = str(uuid.uuid4())[:8]
        logger.info(f"Initialized secure session tracking: Session-{session_id}")
        return PipelineState(session_id=session_id)

    async def process_turn(self, state: PipelineState, user_message: str) -> str:
        """Executes one full asynchronous pipeline cycle: Inbound -> Extractor -> Scorer evaluation."""
        logger.debug(f"[Session {state.session_id}] Processing incoming B2B chunk...")

        try:
            reply = await self.inbound.execute(state, user_message)
            await self.extractor.execute(state)
            await self.scorer.execute(state)
        except Exception as exc:
            if not is_sandbox_active():
                from modules.sales_agent_pipeline.core.gemini_client import activate_sandbox_mode

                activate_sandbox_mode(f"pipeline fault recovery: {exc}")
                reply = await self.inbound.execute(state, user_message)
                await self.extractor.execute(state)
                await self.scorer.execute(state)
            else:
                raise

        logger.info(
            f"[Session {state.session_id}] Telemetry Status: {state.status.value} | "
            f"Budget Fit Score: {state.evaluation.budget_fit if state.evaluation else 0}/10"
        )
        await push_telemetry(state)
        return reply

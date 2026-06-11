import asyncio

from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.core.gemini_client import is_sandbox_active, validate_api_key
from modules.sales_agent_pipeline.core.router import AdvancedSalesOrchestrator
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger
from modules.sales_agent_pipeline.utils.session_manager import (
    evaluate_session_routing,
    format_session_label,
    is_new_session_command,
)
from modules.sales_agent_pipeline.utils.telemetry_bridge import push_telemetry

logger = get_pipeline_logger()


async def _cycle_session(orchestrator: AdvancedSalesOrchestrator, reason: str):
    """Atomically isolate a fresh lead session with a new cryptographic session id."""
    session = orchestrator.create_session()
    await push_telemetry(session)
    label = format_session_label(session.session_id)
    cycle_msg = f"[CYCLE] Context shift detected -> Routing to fresh Session: {label}"
    print(f"\n\033[93m{cycle_msg}\033[0m")
    print(f"\033[90mReason: {reason}\033[0m\n")
    logger.info(f"{cycle_msg} | reason={reason}")
    return session


async def run_live_pipeline():
    api_key = PipelineConfig.GEMINI_API_KEY
    if not api_key and not PipelineConfig.is_sandbox_key():
        logger.critical("Initialization Failed: GEMINI_API_KEY is not set in the root .env file.")
        print("\n[!] Add GEMINI_API_KEY to the repository root .env file and retry.\n")
        return

    logger.info("Initializing Rayza Advanced Multi-Agent Sales Orchestrator (Gemini)...")
    orchestrator = AdvancedSalesOrchestrator(api_key=api_key)

    await validate_api_key()

    if is_sandbox_active():
        logger.info(
            "Pipeline booted in Autonomous Local Sandbox Mode successfully - "
            "all agents routed through local gemini-1.5-flash emulation."
        )
        print("\n\033[93m[~] Autonomous Local Sandbox Mode - no live Google API calls.\033[0m")

    session_state = orchestrator.create_session()
    await push_telemetry(session_state)

    mode_label = "SANDBOX" if is_sandbox_active() else "GEMINI LIVE"
    print("\n" + "=" * 60)
    print(f"  RAYZA MULTI-AGENT SALES B2B CORE - {mode_label} DEMO")
    print("=" * 60)
    print("Type 'exit' or 'quit' to terminate the session.")
    print("Type '/new' to force a fresh lead session.")
    ports = ", ".join(
        str(int(url.split(":")[2].split("/")[0]))
        for url in PipelineConfig.telemetry_api_urls()
    )
    print(
        f"Dashboard sync: shared_state.json + /api/telemetry "
        f"(ports {ports}, primary {PipelineConfig.DASHBOARD_PORT})\n"
    )
    print(
        f"\033[90mActive Session: {format_session_label(session_state.session_id)}\033[0m\n"
    )

    while True:
        try:
            user_input = input("\033[94m[Client/Lead] -> \033[0m")
            if user_input.strip().lower() in ["exit", "quit"]:
                logger.info("Closing active session safely.")
                break

            if not user_input.strip():
                continue

            if is_new_session_command(user_input):
                session_state = await _cycle_session(orchestrator, "manual /new command")
                print(
                    f"\033[90mActive Session: {format_session_label(session_state.session_id)}\033[0m\n"
                )
                continue

            routing = evaluate_session_routing(session_state, user_input)
            if routing.should_cycle:
                session_state = await _cycle_session(orchestrator, routing.reason)

            ai_response = await orchestrator.process_turn(session_state, user_input)

            print(f"\n\033[92m[Rayza Exec Agent] ->\033[0m {ai_response}\n")
            print(
                f"\033[90m--- Telemetry Sync | Session: {format_session_label(session_state.session_id)} | "
                f"Status: {session_state.status.value} | "
                f"Extracted Name: {session_state.extracted_data.customer_name} | "
                f"Budget: {session_state.extracted_data.budget_range} ---\033[0m\n"
            )

        except KeyboardInterrupt:
            print("\n")
            logger.warning("Session interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Execution pipeline error encountered: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run_live_pipeline())

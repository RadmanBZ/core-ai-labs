import asyncio
import os
from modules.sales_agent_pipeline.core.router import AdvancedSalesOrchestrator
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

async def run_live_pipeline():
    # Retrieve the API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your-api-key" in api_key:
        logger.critical("Initialization Failed: OPENAI_API_KEY environment variable is not set properly.")
        print("\n[!] Please set your API key in terminal: export OPENAI_API_KEY='your_real_key'\n")
        return

    logger.info("Initializing Rayza Advanced Multi-Agent Sales Orchestrator...")
    orchestrator = AdvancedSalesOrchestrator(api_key=api_key)
    
    # Establish a fresh tracking session
    session_state = orchestrator.create_session()
    
    print("\n" + "="*60)
    print("  RAYZA MULTI-AGENT SALES B2B CORE - RUNNING LIVE DEMO")
    print("="*60)
    print("Type 'exit' or 'quit' to terminate the session.\n")

    while True:
        try:
            user_input = input("\033[94m[Client/Lead] -> \033[0m")
            if user_input.strip().lower() in ['exit', 'quit']:
                logger.info("Closing active session safely.")
                break
                
            if not user_input.strip():
                continue

            # Process the turn through Inbound -> Extractor -> Scorer chain
            ai_response = await orchestrator.process_turn(session_state, user_input)
            
            print(f"\n\033[92m[Rayza Exec Agent] ->\033[0m {ai_response}\n")
            
            # Print a subtle background state telemetry for debugging
            print(f"\033[90m--- Telemetry Sync | Current Status: {session_state.status.value} | Extracted Name: {session_state.extracted_data.customer_name} ---\033[0m\n")
            
        except KeyboardInterrupt:
            print("\n")
            logger.warning("Session interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Execution pipeline error encountered: {str(e)}")

if __name__ == "__main__":
    # Run the async loop
    asyncio.run(run_live_pipeline())
import os
from pathlib import Path

from dotenv import load_dotenv

# Load the repository root .env regardless of current working directory
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

class PipelineConfig:
    """Central configuration for Core AI Labs Sales Agent Engine."""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = "gpt-4o-mini"
    
    INBOUND_SYSTEM_PROMPT: str = (
        "You are an elite, smooth, and highly professional B2B Sales Executive representing Rayza Technology Agency. "
        "Your goal is to converse with the lead, maintain an executive tone, understand their core software or automation needs, "
        "and keep them engaged. Do NOT be pushy. Act like a consultant. Gather their requirements organically."
    )
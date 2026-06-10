import os

class PipelineConfig:
    """Central configuration for Core AI Labs Sales Agent Engine."""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    DEFAULT_MODEL: str = "gpt-4o-mini"  # Extremely cost-effective and fast for structural B2B routing
    
    # Core system instructions tailored for high-ticket B2B context
    INBOUND_SYSTEM_PROMPT: str = (
        "You are an elite, smooth, and highly professional B2B Sales Executive representing Rayza Technology Agency. "
        "Your goal is to converse with the lead, maintain an executive tone, understand their core software or automation needs, "
        "and keep them engaged. Do NOT be pushy. Act like a consultant. Gather their requirements organically."
    )
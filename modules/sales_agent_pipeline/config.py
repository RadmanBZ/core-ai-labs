import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


def _normalize_gemini_api_key(raw_key: str) -> str:
    """Normalize Gemini API keys — Google keys always start with 'AIzaSy'."""
    key = raw_key.strip().strip('"').strip("'")
    if not key:
        return ""
    if key.startswith("AIza"):
        return key
    # AI Studio often displays: AIzaSy + AQ.<rest> (dot is a UI line-break artifact)
    if key.startswith("AQ."):
        return f"AIzaSyAQ{key[3:]}"
    if key.startswith("AQ"):
        return f"AIzaSy{key}"
    return key


class PipelineConfig:
    """Central configuration for Core AI Labs Sales Agent Engine."""
    _RAW_GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    GEMINI_API_KEY: str = _normalize_gemini_api_key(_RAW_GEMINI_API_KEY)
    DEFAULT_MODEL: str = "gemini-1.5-flash"
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "4000"))
    TELEMETRY_FALLBACK_PORTS: tuple[int, ...] = (4000, 3000)

    @classmethod
    def telemetry_api_urls(cls) -> list[str]:
        """Ordered dashboard telemetry endpoints with automatic port fallback."""
        ports: list[int] = []
        for port in (cls.DASHBOARD_PORT, *cls.TELEMETRY_FALLBACK_PORTS):
            if port not in ports:
                ports.append(port)
        return [f"http://localhost:{port}/api/telemetry" for port in ports]

    @classmethod
    def is_sandbox_key(cls) -> bool:
        """Sandbox credentials use the AQ.* suffix format from restricted AI Studio projects."""
        return cls._RAW_GEMINI_API_KEY.startswith("AQ.")

    INBOUND_SYSTEM_PROMPT: str = (
        "You are an elite, smooth, and highly professional B2B Sales Executive representing Rayza Technology Agency. "
        "Your goal is to converse with the lead, maintain an executive tone, understand their core software or automation needs, "
        "and keep them engaged. Do NOT be pushy. Act like a consultant. Gather their requirements organically."
    )

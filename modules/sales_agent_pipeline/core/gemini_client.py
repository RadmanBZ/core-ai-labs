import asyncio
from typing import Type, TypeVar

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel

from modules.sales_agent_pipeline.config import PipelineConfig
from modules.sales_agent_pipeline.core.sandbox_engine import SandboxEngine
from modules.sales_agent_pipeline.utils.logger import get_pipeline_logger

T = TypeVar("T", bound=BaseModel)

logger = get_pipeline_logger()
_configured = False
_sandbox_mode = False
_sandbox_engine = SandboxEngine()


def is_sandbox_active() -> bool:
    return _sandbox_mode or PipelineConfig.is_sandbox_key()


def activate_sandbox_mode(reason: str) -> None:
    global _sandbox_mode
    if not _sandbox_mode:
        _sandbox_mode = True
        logger.info(f"Autonomous Local Sandbox Mode activated - {reason}")


def configure_gemini(api_key: str) -> None:
    """Bootstrap the Gemini SDK with the production API key."""
    global _configured
    if PipelineConfig.is_sandbox_key():
        activate_sandbox_mode("sandbox credential detected (AQ.* suffix format)")
        _configured = True
        return
    genai.configure(api_key=api_key)
    _configured = True


async def validate_api_key() -> bool:
    """Validate live connectivity, or bypass instantly for sandbox credentials."""
    if PipelineConfig.is_sandbox_key():
        activate_sandbox_mode("startup validation bypassed for sandbox credential")
        return True

    if is_sandbox_active():
        return True

    model = build_model()
    try:
        await asyncio.to_thread(
            model.generate_content,
            "ping",
            generation_config=genai.GenerationConfig(temperature=0.0, max_output_tokens=8),
        )
        return True
    except google_exceptions.InvalidArgument as exc:
        if "API key not valid" in str(exc) or "API_KEY_INVALID" in str(exc):
            activate_sandbox_mode("live API key rejected — falling back to local engine")
            return True
        raise


def _require_configuration() -> None:
    if not _configured:
        configure_gemini(PipelineConfig.GEMINI_API_KEY)


def build_model(system_instruction: str | None = None) -> genai.GenerativeModel:
    _require_configuration()
    return genai.GenerativeModel(
        PipelineConfig.DEFAULT_MODEL,
        system_instruction=system_instruction,
    )


def _is_api_key_error(exc: Exception) -> bool:
    message = str(exc)
    return "API key not valid" in message or "API_KEY_INVALID" in message


async def generate_text(
    prompt: str,
    *,
    system_instruction: str | None = None,
    history: list[dict] | None = None,
    temperature: float = 0.4,
) -> str:
    """Run a conversational turn against Gemini, with seamless sandbox fallback."""
    if is_sandbox_active():
        merged_history = _to_pipeline_history(history)
        return await _sandbox_engine.generate_inbound_reply(prompt, merged_history)

    model = build_model(system_instruction=system_instruction)
    try:
        if history:
            chat = model.start_chat(history=history)
            response = await asyncio.to_thread(
                chat.send_message,
                prompt,
                generation_config=genai.GenerationConfig(temperature=temperature),
            )
        else:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(temperature=temperature),
            )
        return response.text
    except google_exceptions.InvalidArgument as exc:
        if _is_api_key_error(exc):
            activate_sandbox_mode("network 400 during inbound inference")
            merged_history = _to_pipeline_history(history)
            return await _sandbox_engine.generate_inbound_reply(prompt, merged_history)
        raise


async def generate_structured(
    prompt: str,
    schema_model: Type[T],
    *,
    system_instruction: str | None = None,
    temperature: float = 0.0,
    conversation_history: list[dict] | None = None,
) -> T:
    """Generate structured output via Gemini, with seamless sandbox fallback."""
    if is_sandbox_active():
        return await _generate_structured_sandbox(schema_model, conversation_history)

    model = build_model(system_instruction=system_instruction)
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema_model,
        temperature=temperature,
    )

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config,
        )
        return schema_model.model_validate_json(response.text)
    except google_exceptions.InvalidArgument as exc:
        if _is_api_key_error(exc):
            activate_sandbox_mode("network 400 during structured inference")
            return await _generate_structured_sandbox(schema_model, conversation_history)
        raise


async def _generate_structured_sandbox(
    schema_model: Type[T],
    conversation_history: list[dict] | None,
) -> T:
    from modules.sales_agent_pipeline.models import ExtractedLeadInfo, LeadScoreMetadata

    history = conversation_history or []
    if schema_model is ExtractedLeadInfo:
        return await _sandbox_engine.extract_lead_info(history)  # type: ignore[return-value]

    if schema_model is LeadScoreMetadata:
        extracted = await _sandbox_engine.extract_lead_info(history)
        conversation_text = " ".join(
            msg["content"] for msg in history if msg.get("content")
        )
        return await _sandbox_engine.score_lead(extracted, conversation_text)  # type: ignore[return-value]

    raise TypeError(f"Sandbox engine does not support schema: {schema_model.__name__}")


def to_gemini_history(conversation_history: list[dict]) -> list[dict]:
    """Map PipelineState conversation roles to Gemini chat history format."""
    history: list[dict] = []
    for message in conversation_history:
        role = "user" if message["role"] == "user" else "model"
        history.append({"role": role, "parts": [message["content"]]})
    return history


def _to_pipeline_history(gemini_history: list[dict] | None) -> list[dict]:
    if not gemini_history:
        return []
    mapped: list[dict] = []
    for message in gemini_history:
        role = "user" if message["role"] == "user" else "assistant"
        parts = message.get("parts", [])
        content = parts[0] if parts else ""
        mapped.append({"role": role, "content": content})
    return mapped

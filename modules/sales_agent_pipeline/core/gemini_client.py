import asyncio
from typing import Type, TypeVar

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel

from modules.sales_agent_pipeline.config import PipelineConfig

T = TypeVar("T", bound=BaseModel)

_configured = False


def configure_gemini(api_key: str) -> None:
    """Bootstrap the Gemini SDK with the production API key."""
    global _configured
    genai.configure(api_key=api_key)
    _configured = True


async def validate_api_key() -> None:
    """Fail fast with a clear message when the Gemini API key is rejected."""
    model = build_model()
    try:
        await asyncio.to_thread(
            model.generate_content,
            "ping",
            generation_config=genai.GenerationConfig(temperature=0.0, max_output_tokens=8),
        )
    except google_exceptions.InvalidArgument as exc:
        if "API key not valid" in str(exc) or "API_KEY_INVALID" in str(exc):
            raise ValueError(
                "Gemini API key rejected by Google. Copy the full key from "
                "https://aistudio.google.com/apikey — it must start with 'AIzaSy'. "
                "If AI Studio shows 'AQ.<rest>', paste only that suffix into GEMINI_API_KEY; "
                "the system will reconstruct the full key automatically."
            ) from exc
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


async def generate_text(
    prompt: str,
    *,
    system_instruction: str | None = None,
    history: list[dict] | None = None,
    temperature: float = 0.4,
) -> str:
    """Run a conversational turn against Gemini with optional chat history."""
    model = build_model(system_instruction=system_instruction)

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


async def generate_structured(
    prompt: str,
    schema_model: Type[T],
    *,
    system_instruction: str | None = None,
    temperature: float = 0.0,
) -> T:
    """Generate a Gemini response constrained to a Pydantic schema."""
    model = build_model(system_instruction=system_instruction)
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema_model,
        temperature=temperature,
    )

    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
        generation_config=generation_config,
    )

    return schema_model.model_validate_json(response.text)


def to_gemini_history(conversation_history: list[dict]) -> list[dict]:
    """Map PipelineState conversation roles to Gemini chat history format."""
    history: list[dict] = []
    for message in conversation_history:
        role = "user" if message["role"] == "user" else "model"
        history.append({"role": role, "parts": [message["content"]]})
    return history

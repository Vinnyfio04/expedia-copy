"""Backend-only Gemini structured-output transport for hotel RAG requests."""

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .config import get_gemini_api_key, get_gemini_model


GEMINI_INTERACTIONS_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1/interactions"
)
GEMINI_TIMEOUT_SECONDS = 60.0
GEMINI_MAX_OUTPUT_TOKENS = 4_096
GEMINI_RESPONSE_BYTES_LIMIT = 1_000_000

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class GeminiProviderError(RuntimeError):
    """Raised when Gemini cannot provide a usable structured response."""

    def __init__(self, message: str, *, code: str = "provider_unavailable") -> None:
        super().__init__(message)
        self.code = code


def _model_output_text(payload: Any) -> str | None:
    """Extract the final text content from a completed Gemini interaction."""
    if not isinstance(payload, dict) or payload.get("status") != "completed":
        return None
    steps = payload.get("steps")
    if not isinstance(steps, list):
        return None

    for step in reversed(steps):
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        content = step.get("content")
        if not isinstance(content, list):
            return None
        text_blocks = [
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
        output_text = "".join(text_blocks).strip()
        return output_text or None
    return None


async def request_gemini_structured_output(
    prompt: str,
    response_model: type[StructuredOutput],
    *,
    system_instruction: str | None = None,
    max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
) -> StructuredOutput:
    """Request stateless JSON from Gemini and validate it into a typed contract."""
    if not prompt.strip():
        raise ValueError("A nonblank Gemini prompt is required.")
    if max_output_tokens < 1 or max_output_tokens > GEMINI_MAX_OUTPUT_TOKENS:
        raise ValueError(
            f"max_output_tokens must be between 1 and {GEMINI_MAX_OUTPUT_TOKENS}."
        )

    api_key = get_gemini_api_key()
    if api_key is None:
        raise GeminiProviderError(
            "Gemini is not configured.",
            code="not_configured",
        )

    request_body: dict[str, Any] = {
        "model": get_gemini_model(),
        "input": prompt.strip(),
        "store": False,
        "background": False,
        "response_format": [
            {
                "type": "text",
                "mime_type": "application/json",
                "schema": response_model.model_json_schema(),
            }
        ],
        "generation_config": {
            "max_output_tokens": max_output_tokens,
            "thinking_level": "minimal",
            "thinking_summaries": "none",
        },
    }
    if system_instruction is not None and system_instruction.strip():
        request_body["system_instruction"] = system_instruction.strip()

    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GEMINI_INTERACTIONS_ENDPOINT,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
            if len(response.content) > GEMINI_RESPONSE_BYTES_LIMIT:
                raise GeminiProviderError(
                    "Gemini returned an invalid response.",
                    code="invalid_provider_response",
                )
            payload = response.json()
    except GeminiProviderError:
        raise
    except httpx.HTTPStatusError as error:
        code = (
            "provider_rate_limited"
            if error.response.status_code == 429
            else "provider_unavailable"
        )
        raise GeminiProviderError("Gemini request failed.", code=code) from None
    except (httpx.HTTPError, ValueError, TypeError):
        raise GeminiProviderError("Gemini request failed.") from None

    output_text = _model_output_text(payload)
    if output_text is None:
        raise GeminiProviderError(
            "Gemini returned an invalid response.",
            code="invalid_provider_response",
        )

    try:
        return response_model.model_validate_json(output_text)
    except (ValidationError, ValueError, TypeError):
        raise GeminiProviderError(
            "Gemini returned an invalid response.",
            code="invalid_provider_response",
        ) from None

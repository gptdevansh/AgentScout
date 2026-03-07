"""
OpenAI-compatible client for Azure AI Foundry models.

Wraps the official `openai` async SDK and normalises responses
into the application's `ChatResponse` schema.  Works for any model
deployed behind an OpenAI-compatible endpoint (GPT, DeepSeek, etc.).
"""

import logging
from typing import Any

from openai import AsyncAzureOpenAI

from app.integrations.ai_models.base import BaseAIClient, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAIClient):
    """Async client that talks to an Azure-hosted OpenAI-compatible model."""

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str,
        api_version: str,
        model_name: str,
        default_temperature: float = 0.7,
        default_max_tokens: int = 4096,
    ) -> None:
        self._model_name = model_name
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens

        self._client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )
        logger.info("Initialised OpenAIClient for model=%s", model_name)

    # ── Public API ───────────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Send a chat-completion request.

        Args:
            messages: Conversation history as ChatMessage objects.
            temperature: Sampling temperature override.
            max_tokens: Max tokens override.

        Returns:
            A normalised ChatResponse.
        """
        payload: list[dict[str, str]] = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        temperature = temperature if temperature is not None else self._default_temperature
        max_tokens = max_tokens if max_tokens is not None else self._default_max_tokens

        logger.debug(
            "chat → model=%s msgs=%d temp=%.2f max_tokens=%d",
            self._model_name,
            len(payload),
            temperature,
            max_tokens,
        )

        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=payload,  # type: ignore[arg-type]
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return ChatResponse(
            content=choice.message.content or "",
            model=response.model or self._model_name,
            usage=usage,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    async def close(self) -> None:
        """Close the underlying HTTP transport."""
        await self._client.close()
        logger.info("Closed OpenAIClient for model=%s", self._model_name)

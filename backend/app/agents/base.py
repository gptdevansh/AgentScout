"""
Base agent abstraction.

Every AI agent in the system extends BaseAgent, which standardises
how agents receive their AI client dependency and exposes a
convenience `_call` helper for chat completions.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.integrations.ai_models.base import BaseAIClient, ChatMessage, ChatResponse

# Max seconds to wait for a single AI API call before giving up.
_CALL_TIMEOUT_SECONDS = 60

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Shared foundation for all AI agents.

    Sub-classes must implement `run()` with their own signature
    and return type.  The `_call` helper keeps prompt building
    and error handling consistent across agents.
    """

    def __init__(self, *, client: BaseAIClient, name: str = "agent") -> None:
        self._client = client
        self._name = name

    # ── Helpers available to every agent ─────────────────────────────────

    async def _call(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Send a chat-completion request through the injected AI client.

        Logs the request and response at DEBUG level for observability.
        """
        kwargs: dict[str, Any] = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        logger.debug(
            "[%s] calling AI model  msgs=%d  %s",
            self._name,
            len(messages),
            kwargs,
        )

        try:
            response = await asyncio.wait_for(
                self._client.chat(messages, **kwargs),
                timeout=_CALL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"[{self._name}] AI call timed out after {_CALL_TIMEOUT_SECONDS}s"
            )

        logger.debug(
            "[%s] AI response  model=%s  tokens=%s  content_len=%d",
            self._name,
            response.model,
            response.usage,
            len(response.content),
        )
        return response

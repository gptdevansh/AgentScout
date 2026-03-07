"""
Abstract base class for AI model clients.

All AI model integrations implement this interface so that agents
depend on an abstraction, not a concrete SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChatMessage:
    """A single message in a conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Normalised response from any AI model."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict | None = None  # preserve full provider payload if needed


class BaseAIClient(ABC):
    """Contract that every AI model client must fulfil."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        """Send a chat-completion request and return a normalised response."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release any underlying connections / resources."""
        ...

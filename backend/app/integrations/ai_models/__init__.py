"""
AI model integrations package.

Re-exports the public surface so consumers can write:
    from app.integrations.ai_models import BaseAIClient, ChatMessage
"""

from app.integrations.ai_models.base import BaseAIClient, ChatMessage, ChatResponse  # noqa: F401
from app.integrations.ai_models.factory import build_deepseek_client, build_gpt_client  # noqa: F401
from app.integrations.ai_models.openai_client import OpenAIClient  # noqa: F401
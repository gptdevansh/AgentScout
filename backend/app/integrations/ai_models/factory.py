"""
Pre-configured factory functions for the two AI models.

Each function returns a fully initialised OpenAIClient bound to the
correct Azure deployment.  Agents should depend on `BaseAIClient`
and receive the concrete instance via dependency injection.
"""

from app.core.config import Settings
from app.integrations.ai_models.openai_client import OpenAIClient


def build_gpt_client(settings: Settings) -> OpenAIClient:
    """Return an OpenAIClient configured for GPT-5.1-chat (writing)."""
    return OpenAIClient(
        api_key=settings.azure_openai_api_key,
        endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        model_name=settings.gpt_model_name,
        default_temperature=0.8,   # slightly creative for writing
        default_max_tokens=4096,
    )


def build_deepseek_client(settings: Settings) -> OpenAIClient:
    """Return an OpenAIClient configured for DeepSeek-R1 (reasoning)."""
    return OpenAIClient(
        api_key=settings.azure_openai_api_key,
        endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        model_name=settings.deepseek_model_name,
        default_temperature=0.3,   # more deterministic for reasoning
        default_max_tokens=4096,
    )

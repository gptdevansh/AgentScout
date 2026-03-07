"""
Pre-configured factory functions for the two AI models.

Each function returns a fully initialised OpenAIClient bound to the
correct Azure deployment.  Agents should depend on `BaseAIClient`
and receive the concrete instance via dependency injection.
"""

from app.core.config import Settings
from app.integrations.ai_models.openai_client import OpenAIClient


def build_gpt_client(settings: Settings) -> OpenAIClient:
    """Return an OpenAIClient configured for GPT-5.1-chat (writing).

    GPT-5.1-chat does not support the ``temperature`` parameter
    (only the default value of 1 is accepted), so we disable it.
    """
    return OpenAIClient(
        api_key=settings.azure_openai_api_key,
        endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        model_name=settings.gpt_model_name,
        default_temperature=1.0,
        default_max_tokens=4096,
        supports_temperature=False,  # gpt-5.1-chat rejects temperature != 1
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

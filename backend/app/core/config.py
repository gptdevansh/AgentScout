"""
Application configuration module.

Loads settings from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "AgentScout"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    postgres_user: str = "agentscout"
    postgres_password: str = "agentscout"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agentscout"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Build async PostgreSQL DSN from individual components."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Synchronous DSN used by Alembic migrations."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    # ── AI Models (Azure OpenAI) ─────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"

    gpt_model_name: str = "gpt-5.1-chat"
    deepseek_model_name: str = "deepseek-r1"

    # ── Apify ────────────────────────────────────────────────────────────
    apify_api_token: str = ""

    # ── Rate Limits / Tuning ─────────────────────────────────────────────
    max_search_queries: int = Field(default=3, ge=1, le=100)
    max_posts_per_query: int = Field(default=3, ge=1, le=50)
    debate_rounds: int = Field(default=1, ge=1, le=10)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()

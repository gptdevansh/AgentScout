"""
FastAPI application factory.

Creates and configures the FastAPI application instance,
registers routers, middleware, and lifecycle events.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.routes import health, pipeline, posts, comments
from app.integrations.ai_models.factory import build_deepseek_client, build_gpt_client
from app.integrations.apify.client import build_apify_client
from app.services.scraping import ScraperRegistry, ScrapingService
from app.services.scraping.platforms.linkedin import LinkedInScraper
from app.agents.query_generator import QueryGeneratorAgent
from app.agents.post_analysis import PostAnalysisAgent
from app.agents.writer import WriterAgent
from app.agents.critic import CriticAgent
from app.agents.judge import JudgeAgent
from app.agents.debate import DebateOrchestrator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — runs on startup and shutdown."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting %s v%s (debug=%s)",
        settings.app_name,
        settings.app_version,
        settings.debug,
    )

    # ── Initialise shared clients ────────────────────────────────────────
    app.state.gpt_client = build_gpt_client(settings)
    app.state.deepseek_client = build_deepseek_client(settings)
    app.state.apify_client = build_apify_client(settings)
    logger.info("External integration clients initialised")

    # ── Build scraping service with platform registry ────────────────────
    registry = ScraperRegistry()
    registry.register(LinkedInScraper(apify_client=app.state.apify_client))
    app.state.scraping_service = ScrapingService(registry=registry)
    logger.info(
        "Scraping service ready — platforms: %s",
        registry.available_platforms,
    )

    # ── Initialise AI agents ─────────────────────────────────────────────
    app.state.query_generator_agent = QueryGeneratorAgent(
        client=app.state.deepseek_client,
    )
    app.state.post_analysis_agent = PostAnalysisAgent(
        client=app.state.deepseek_client,
    )

    # ── Debate agents ────────────────────────────────────────────────────
    app.state.writer_agent = WriterAgent(client=app.state.gpt_client)
    app.state.critic_agent = CriticAgent(client=app.state.deepseek_client)
    app.state.judge_agent = JudgeAgent(client=app.state.deepseek_client)

    app.state.debate_orchestrator = DebateOrchestrator(
        writer=app.state.writer_agent,
        critic=app.state.critic_agent,
        judge=app.state.judge_agent,
        rounds=settings.debate_rounds,
        num_comments=1,  # 1 candidate keeps critic/judge calls minimal
    )
    logger.info("AI agents initialised (including debate system)")

    yield

    # ── Teardown ─────────────────────────────────────────────────────────
    await app.state.gpt_client.close()
    await app.state.deepseek_client.close()
    await app.state.apify_client.close()
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory.  Returns a fully configured FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(comments.router, prefix="/api/v1")

    return app


app = create_app()

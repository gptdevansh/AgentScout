"""
FastAPI dependency injection providers.

All shared dependencies (DB sessions, settings, external clients)
are provided through this module to keep coupling low.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_async_session
from app.integrations.ai_models.base import BaseAIClient
from app.integrations.apify.client import ApifyClient
from app.services.scraping.service import ScrapingService
from app.agents.query_generator import QueryGeneratorAgent
from app.agents.post_analysis import PostAnalysisAgent
from app.agents.writer import WriterAgent
from app.agents.critic import CriticAgent
from app.agents.judge import JudgeAgent
from app.agents.debate import DebateOrchestrator


async def _get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and ensure it is closed after use."""
    async for session in get_async_session():
        yield session


def _get_gpt_client(request: Request) -> BaseAIClient:
    """Retrieve the GPT client stored on app state during lifespan."""
    return request.app.state.gpt_client


def _get_deepseek_client(request: Request) -> BaseAIClient:
    """Retrieve the DeepSeek client stored on app state during lifespan."""
    return request.app.state.deepseek_client


def _get_apify_client(request: Request) -> ApifyClient:
    """Retrieve the Apify client stored on app state during lifespan."""
    return request.app.state.apify_client


def _get_scraping_service(request: Request) -> ScrapingService:
    """Retrieve the scraping service stored on app state during lifespan."""
    return request.app.state.scraping_service


def _get_query_generator(request: Request) -> QueryGeneratorAgent:
    """Retrieve the query generator agent from app state."""
    return request.app.state.query_generator_agent


def _get_post_analysis_agent(request: Request) -> PostAnalysisAgent:
    """Retrieve the post analysis agent from app state."""
    return request.app.state.post_analysis_agent


def _get_writer_agent(request: Request) -> WriterAgent:
    """Retrieve the writer agent from app state."""
    return request.app.state.writer_agent


def _get_critic_agent(request: Request) -> CriticAgent:
    """Retrieve the critic agent from app state."""
    return request.app.state.critic_agent


def _get_judge_agent(request: Request) -> JudgeAgent:
    """Retrieve the judge agent from app state."""
    return request.app.state.judge_agent


def _get_debate_orchestrator(request: Request) -> DebateOrchestrator:
    """Retrieve the debate orchestrator from app state."""
    return request.app.state.debate_orchestrator


# ── Re-usable Annotated dependencies for route signatures ───────────────
SettingsDep = Annotated[Settings, Depends(get_settings)]
DBSessionDep = Annotated[AsyncSession, Depends(_get_db_session)]
GPTClientDep = Annotated[BaseAIClient, Depends(_get_gpt_client)]
DeepSeekClientDep = Annotated[BaseAIClient, Depends(_get_deepseek_client)]
ApifyClientDep = Annotated[ApifyClient, Depends(_get_apify_client)]
ScrapingServiceDep = Annotated[ScrapingService, Depends(_get_scraping_service)]
QueryGeneratorDep = Annotated[QueryGeneratorAgent, Depends(_get_query_generator)]
PostAnalysisAgentDep = Annotated[PostAnalysisAgent, Depends(_get_post_analysis_agent)]
WriterAgentDep = Annotated[WriterAgent, Depends(_get_writer_agent)]
CriticAgentDep = Annotated[CriticAgent, Depends(_get_critic_agent)]
JudgeAgentDep = Annotated[JudgeAgent, Depends(_get_judge_agent)]
DebateOrchestratorDep = Annotated[DebateOrchestrator, Depends(_get_debate_orchestrator)]

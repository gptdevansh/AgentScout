"""
Post Analysis Agent.

Uses DeepSeek-R1 to evaluate scraped posts for relevance to a target
problem, detecting intent, emotion, and engagement opportunity.
Returns structured analysis results that map to the PostAnalysis model.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.agents.prompts.post_analysis import SYSTEM_PROMPT, USER_PROMPT
from app.integrations.ai_models.base import BaseAIClient, ChatMessage
from app.services.scraping.models import ScrapedPost

logger = logging.getLogger(__name__)

# ── Valid classification enums ───────────────────────────────────────────
_VALID_INTENTS = {
    "question", "rant", "seeking_advice", "sharing_experience",
    "recommendation", "announcement", "discussion", "other",
}
_VALID_EMOTIONS = {
    "frustration", "curiosity", "excitement", "disappointment",
    "neutral", "confusion", "hope", "anger", "satisfaction", "other",
}


@dataclass
class PostAnalysisResult:
    """Structured output from the Post Analysis Agent."""

    relevance_score: float
    opportunity_score: float
    intent: str
    emotion: str
    reasoning: str


class PostAnalysisAgent(BaseAgent):
    """Analyse posts for relevance, intent, emotion, and opportunity."""

    def __init__(self, *, client: BaseAIClient) -> None:
        super().__init__(client=client, name="post_analysis")

    async def run(
        self,
        post: ScrapedPost,
        *,
        problem_description: str,
        product_description: str | None = None,
    ) -> PostAnalysisResult:
        """Analyse a single post against a problem description.

        Args:
            post: The scraped post to evaluate.
            problem_description: The problem we're searching for.
            product_description: Optional product context.

        Returns:
            A PostAnalysisResult with scores and classifications.
        """
        product_context = (
            f"Product context:\n{product_description}"
            if product_description
            else ""
        )

        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=USER_PROMPT.format(
                    problem_description=problem_description,
                    product_context=product_context,
                    platform=post.platform,
                    author=post.author or "Unknown",
                    content=post.content[:3000],  # cap to avoid token overflow
                    likes=post.likes,
                    comments_count=post.comments_count,
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.2,  # very deterministic for scoring
            max_tokens=1024,
        )

        result = self._parse_response(response.content)
        logger.info(
            "[%s] post=%s  relevance=%.2f  opportunity=%.2f  intent=%s  emotion=%s",
            self._name,
            post.post_url[:60],
            result.relevance_score,
            result.opportunity_score,
            result.intent,
            result.emotion,
        )
        return result

    async def run_batch(
        self,
        posts: list[ScrapedPost],
        *,
        problem_description: str,
        product_description: str | None = None,
        min_relevance: float = 0.0,
    ) -> list[tuple[ScrapedPost, PostAnalysisResult]]:
        """Analyse multiple posts and optionally filter by relevance.

        Args:
            posts: List of scraped posts.
            problem_description: The problem we're searching for.
            product_description: Optional product context.
            min_relevance: Minimum relevance_score to include (0.0 = all).

        Returns:
            List of (post, analysis) tuples sorted by relevance descending.
        """
        results: list[tuple[ScrapedPost, PostAnalysisResult]] = []

        for i, post in enumerate(posts, 1):
            try:
                analysis = await self.run(
                    post,
                    problem_description=problem_description,
                    product_description=product_description,
                )
                if analysis.relevance_score >= min_relevance:
                    results.append((post, analysis))
            except Exception:
                logger.warning(
                    "[%s] Failed to analyse post=%s, skipping",
                    self._name,
                    post.post_url[:60],
                    exc_info=True,
                )

            # Pause every 3 calls to stay under DeepSeek 20 req/min limit
            if i % 3 == 0:
                await asyncio.sleep(4)

        # Sort by relevance descending, then opportunity descending
        results.sort(
            key=lambda pair: (pair[1].relevance_score, pair[1].opportunity_score),
            reverse=True,
        )

        logger.info(
            "[%s] batch complete: %d/%d posts passed min_relevance=%.2f",
            self._name,
            len(results),
            len(posts),
            min_relevance,
        )
        return results

    # ── Parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw: str) -> PostAnalysisResult:
        """Extract a PostAnalysisResult from the model's raw output.

        Handles DeepSeek <think> blocks and markdown fences.
        Falls back to safe defaults if parsing fails.
        """
        # Strip <think>…</think> reasoning
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"```", "", cleaned).strip()

        data: dict = {}

        # Try direct JSON parse
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find a JSON object anywhere
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("Could not parse post-analysis JSON; using defaults")

        return PostAnalysisResult(
            relevance_score=_clamp_float(data.get("relevance_score", 0.0)),
            opportunity_score=_clamp_float(data.get("opportunity_score", 0.0)),
            intent=_validate_enum(data.get("intent", "other"), _VALID_INTENTS),
            emotion=_validate_enum(data.get("emotion", "neutral"), _VALID_EMOTIONS),
            reasoning=str(data.get("reasoning", ""))[:2000],
        )


def _clamp_float(value: object, lo: float = 0.0, hi: float = 1.0) -> float:
    """Safely coerce to float and clamp to [lo, hi]."""
    try:
        return max(lo, min(hi, float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _validate_enum(value: object, valid: set[str]) -> str:
    """Return value if it's in the valid set, else 'other'."""
    s = str(value).lower().strip()
    return s if s in valid else "other"

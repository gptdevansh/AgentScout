"""
Query Generator Agent.

Uses DeepSeek-R1 to transform a problem description into a list of
diverse search queries suitable for social-media keyword search.
"""

import json
import logging
import re
from typing import Any

from app.agents.base import BaseAgent
from app.agents.prompts.query_generator import SYSTEM_PROMPT, USER_PROMPT
from app.integrations.ai_models.base import BaseAIClient, ChatMessage
from app.services.scraping.models import ScrapingWeapon
from app.integrations.ai_models.base import BaseAIClient, ChatMessage

logger = logging.getLogger(__name__)

# Fallback ceiling if the caller doesn't specify
_DEFAULT_NUM_QUERIES = 5


class QueryGeneratorAgent(BaseAgent):
    """Generate search queries from a problem description using DeepSeek."""

    def __init__(self, *, client: BaseAIClient) -> None:
        super().__init__(client=client, name="query_generator")

    async def run(
        self,
        problem_description: str,
        *,
        product_description: str | None = None,
        num_queries: int = _DEFAULT_NUM_QUERIES,
    ) -> list[ScrapingWeapon]:
        """Generate search queries for a given problem.

        Args:
            problem_description: Free-text description of the problem.
            product_description: Optional product context to sharpen results.
            num_queries: How many queries to generate (default 25).

        Returns:
            A list of ScrapingWeapon objects.
        """
        product_context = (
            f"Product context:\n{product_description}"
            if product_description
            else ""
        )

        messages = [
            ChatMessage(
                role="system",
                content=SYSTEM_PROMPT.format(num_queries=num_queries),
            ),
            ChatMessage(
                role="user",
                content=USER_PROMPT.format(
                    problem_description=problem_description,
                    product_context=product_context,
                    num_queries=num_queries,
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.4,   # low-ish for structured output
            max_tokens=2048,
        )

        queries = self._parse_response(response.content, num_queries=num_queries)
        logger.info(
            "[%s] generated %d queries for problem=%r",
            self._name,
            len(queries),
            problem_description[:80],
        )
        return queries

    # ── Parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw: str, *, num_queries: int) -> list[ScrapingWeapon]:
        """Extract a list of ScrapingWeapon objects from the model's raw output.

        Handles:
        - Clean JSON arrays
        - Markdown-wrapped JSON (```json ... ```)
        - Reasoning-wrapped output (<think>...</think> followed by JSON)
        """
        # Strip <think>…</think> blocks (DeepSeek-R1 reasoning)
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"```", "", cleaned)
        cleaned = cleaned.strip()

        # Helper to parse array of dicts
        def to_weapons(parsed: Any) -> list[ScrapingWeapon]:
            weapons = []
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "type" in item and "value" in item:
                        try:
                            weapons.append(ScrapingWeapon(**item))
                        except Exception:
                            pass
                    elif isinstance(item, str):
                        # Fallback for unexpected string output
                        weapons.append(ScrapingWeapon(type="keyword", value=str(item)))
            return _deduplicate(weapons)[:num_queries]

        # Attempt JSON parse
        try:
            parsed = json.loads(cleaned)
            if weapons := to_weapons(parsed):
                return weapons
        except json.JSONDecodeError:
            pass

        # Try to find a JSON array anywhere in the text
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                if weapons := to_weapons(parsed):
                    return weapons
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse query-generator output cleanly; returning raw content as fallback keyword")
        return [ScrapingWeapon(type="keyword", value=cleaned[:500])] if cleaned else []


def _deduplicate(items: list[ScrapingWeapon]) -> list[ScrapingWeapon]:
    """Preserve order while removing duplicates by value (case-insensitive)."""
    seen: set[str] = set()
    result: list[ScrapingWeapon] = []
    for item in items:
        key = item.value.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

"""
Comment Writer Agent (GPT-5.1-chat).

Generates initial comment candidates for a LinkedIn post, and rewrites
them based on structured critic feedback.
"""

import json
import logging
import re

from app.agents.base import BaseAgent
from app.agents.prompts.writer import GENERATE_PROMPT, REWRITE_PROMPT, SYSTEM_PROMPT
from app.integrations.ai_models.base import BaseAIClient, ChatMessage

logger = logging.getLogger(__name__)

# Reasonable defaults
_DEFAULT_NUM_COMMENTS = 3
_MAX_CONTENT_CHARS = 3000


class WriterAgent(BaseAgent):
    """Generate and rewrite LinkedIn comment candidates using GPT."""

    def __init__(self, *, client: BaseAIClient) -> None:
        super().__init__(client=client, name="writer")

    # ── Public API ───────────────────────────────────────────────────────

    async def generate(
        self,
        *,
        problem_description: str,
        product_description: str | None = None,
        platform: str,
        author: str,
        content: str,
        num_comments: int = _DEFAULT_NUM_COMMENTS,
    ) -> list[str]:
        """Generate initial comment candidates for a post.

        Returns a list of comment strings.
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
                content=GENERATE_PROMPT.format(
                    problem_description=problem_description,
                    product_context=product_context,
                    platform=platform,
                    author=author or "Unknown",
                    content=content[:_MAX_CONTENT_CHARS],
                    num_comments=num_comments,
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.8,  # creative for comment writing
            max_tokens=2048,
        )

        comments = self._parse_generate_response(response.content, num_comments)
        logger.info(
            "[%s] generated %d comments for author=%s",
            self._name,
            len(comments),
            (author or "Unknown")[:30],
        )
        return comments

    async def rewrite(
        self,
        *,
        comment: str,
        critique: str,
        author: str,
        content: str,
    ) -> str:
        """Rewrite a comment based on critic feedback.

        Returns the rewritten comment text.
        """
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=REWRITE_PROMPT.format(
                    comment=comment,
                    critique=critique,
                    author=author or "Unknown",
                    content_snippet=content[:500],
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.7,  # slightly less creative for targeted rewrite
            max_tokens=1024,
        )

        rewritten = self._parse_rewrite_response(response.content)
        logger.info(
            "[%s] rewrote comment (len %d → %d)",
            self._name,
            len(comment),
            len(rewritten),
        )
        return rewritten

    # ── Parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_generate_response(raw: str, expected: int) -> list[str]:
        """Extract a list of comment strings from the model output.

        Handles JSON arrays, markdown fences, and falls back to
        splitting numbered lines.
        """
        cleaned = _strip_wrappers(raw)

        # Try JSON array
        comments = _try_json_array(cleaned)
        if comments:
            return comments[:expected]

        # Try finding JSON array substring
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            comments = _try_json_array(match.group())
            if comments:
                return comments[:expected]

        # Fallback: numbered list (1. foo  2. bar ...)
        lines = re.findall(r"^\s*\d+[.)]\s*(.+)", cleaned, re.MULTILINE)
        if lines:
            return [l.strip().strip('"').strip("'") for l in lines][:expected]

        # Last resort: whole output as a single comment
        if cleaned:
            return [cleaned]
        return []

    @staticmethod
    def _parse_rewrite_response(raw: str) -> str:
        """Extract the rewritten comment text.

        The prompt asks for plain text only.  Strip common wrappers.
        """
        cleaned = _strip_wrappers(raw)

        # Remove leading/trailing quotes if present
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1]

        return cleaned.strip()


# ── Module-level helpers ─────────────────────────────────────────────────

def _strip_wrappers(text: str) -> str:
    """Remove <think> blocks, markdown fences, and surrounding whitespace."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def _try_json_array(text: str) -> list[str] | None:
    """Try to parse text as a JSON array of strings."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(c).strip() for c in parsed if c and str(c).strip()]
    except (json.JSONDecodeError, ValueError):
        pass
    return None

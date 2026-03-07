"""
Comment Critic Agent (DeepSeek-R1).

Reviews proposed LinkedIn comments and returns structured feedback
with scores to drive iterative improvement in the debate loop.
"""

import json
import logging
import re
from dataclasses import dataclass, field

from app.agents.base import BaseAgent
from app.agents.prompts.critic import CRITIQUE_PROMPT, SYSTEM_PROMPT
from app.integrations.ai_models.base import BaseAIClient, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class CritiqueResult:
    """Structured output from the Critic Agent."""

    strengths: str = ""
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    score: float = 0.0

    @property
    def summary(self) -> str:
        """Human-readable summary for the writer's rewrite prompt."""
        parts: list[str] = []
        if self.strengths:
            parts.append(f"Strengths: {self.strengths}")
        if self.weaknesses:
            parts.append("Weaknesses: " + "; ".join(self.weaknesses))
        if self.suggestions:
            parts.append("Suggestions: " + "; ".join(self.suggestions))
        parts.append(f"Score: {self.score:.2f}")
        return "\n".join(parts)


class CriticAgent(BaseAgent):
    """Critique LinkedIn comment candidates using DeepSeek."""

    def __init__(self, *, client: BaseAIClient) -> None:
        super().__init__(client=client, name="critic")

    async def critique(
        self,
        *,
        comment: str,
        problem_description: str,
        platform: str,
        author: str,
        content: str,
        version: int = 1,
    ) -> CritiqueResult:
        """Evaluate a single comment and return structured feedback.

        Args:
            comment:            The comment text to evaluate.
            problem_description: Problem context for relevance check.
            platform:           Source platform (e.g. 'linkedin').
            author:             Post author name.
            content:            Original post content.
            version:            Iteration number of the comment.

        Returns:
            A CritiqueResult with strengths, weaknesses, suggestions, and score.
        """
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=CRITIQUE_PROMPT.format(
                    problem_description=problem_description,
                    platform=platform,
                    author=author or "Unknown",
                    content=content[:3000],
                    version=version,
                    comment=comment,
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.2,  # deterministic scoring
            max_tokens=1024,
        )

        result = self._parse_response(response.content)
        logger.info(
            "[%s] critique v%d  score=%.2f  weaknesses=%d  suggestions=%d",
            self._name,
            version,
            result.score,
            len(result.weaknesses),
            len(result.suggestions),
        )
        return result

    # ── Parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw: str) -> CritiqueResult:
        """Extract CritiqueResult from raw model output.

        Handles <think> blocks, markdown fences, and malformed JSON
        with graceful degradation.
        """
        cleaned = _strip_wrappers(raw)

        data: dict = {}
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("Could not parse critic JSON; using defaults")

        return CritiqueResult(
            strengths=str(data.get("strengths", "")),
            weaknesses=_to_str_list(data.get("weaknesses", [])),
            suggestions=_to_str_list(data.get("suggestions", [])),
            score=_clamp_float(data.get("score", 0.0)),
        )


# ── Module-level helpers ─────────────────────────────────────────────────

def _strip_wrappers(text: str) -> str:
    """Remove <think> blocks, markdown fences, and whitespace."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def _clamp_float(value: object, lo: float = 0.0, hi: float = 1.0) -> float:
    """Safely coerce to float and clamp to [lo, hi]."""
    try:
        return max(lo, min(hi, float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _to_str_list(value: object) -> list[str]:
    """Coerce a value into a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if isinstance(value, str) and value:
        return [value]
    return []

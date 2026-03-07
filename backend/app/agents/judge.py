"""
Comment Judge Agent (DeepSeek-R1).

Makes the final selection after debate rounds, picking the best 1-2
comments from all comment candidates associated with a post.
"""

import json
import logging
import re
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.agents.prompts.judge import JUDGE_PROMPT, SYSTEM_PROMPT
from app.integrations.ai_models.base import BaseAIClient, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class JudgeSelection:
    """A single winner selected by the judge."""

    index: int
    comment: str
    final_score: float
    justification: str


class JudgeAgent(BaseAgent):
    """Select the best comment(s) from debate candidates using DeepSeek."""

    def __init__(self, *, client: BaseAIClient) -> None:
        super().__init__(client=client, name="judge")

    async def judge(
        self,
        *,
        candidates: list[str],
        problem_description: str,
        platform: str,
        author: str,
        content: str,
    ) -> list[JudgeSelection]:
        """Evaluate the final candidate set and select the winners.

        Args:
            candidates:          List of comment texts to choose from.
            problem_description: Problem context for relevance evaluation.
            platform:            Source platform (e.g. 'linkedin').
            author:              Post author name.
            content:             Original post content.

        Returns:
            A list of 1-2 JudgeSelection objects ordered by score descending.
        """
        candidates_block = self._format_candidates(candidates)

        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=JUDGE_PROMPT.format(
                    problem_description=problem_description,
                    platform=platform,
                    author=author or "Unknown",
                    content=content[:3000],
                    candidates_block=candidates_block,
                ),
            ),
        ]

        response = await self._call(
            messages,
            temperature=0.2,  # deterministic judging
            max_tokens=1024,
        )

        selections = self._parse_response(response.content, candidates)
        logger.info(
            "[%s] selected %d winner(s) from %d candidates",
            self._name,
            len(selections),
            len(candidates),
        )
        return selections

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _format_candidates(candidates: list[str]) -> str:
        """Build a numbered block for the prompt."""
        lines: list[str] = []
        for i, comment in enumerate(candidates):
            lines.append(f"[{i}] {comment}")
        return "\n\n".join(lines)

    @staticmethod
    def _parse_response(
        raw: str,
        candidates: list[str],
    ) -> list[JudgeSelection]:
        """Extract JudgeSelection list from the model output.

        Handles <think> blocks, markdown fences, and malformed JSON.
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
                    logger.warning("Could not parse judge JSON; returning empty")
                    return []

        raw_selections = data.get("selections", [])
        if not isinstance(raw_selections, list):
            return []

        selections: list[JudgeSelection] = []
        for item in raw_selections:
            if not isinstance(item, dict):
                continue
            idx = _safe_int(item.get("index", -1))
            # Validate index is within bounds
            if idx < 0 or idx >= len(candidates):
                # Try to match by comment text
                idx = _find_closest_candidate(
                    item.get("comment", ""), candidates,
                )
                if idx < 0:
                    continue

            selections.append(
                JudgeSelection(
                    index=idx,
                    comment=candidates[idx],  # canonical version
                    final_score=_clamp_float(item.get("final_score", 0.0)),
                    justification=str(item.get("justification", "")),
                )
            )

        # Sort by score descending, limit to 2
        selections.sort(key=lambda s: s.final_score, reverse=True)
        return selections[:2]


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


def _safe_int(value: object) -> int:
    """Safely coerce to int, defaulting to -1."""
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return -1


def _find_closest_candidate(text: str, candidates: list[str]) -> int:
    """Find the candidate that most closely matches text (simple overlap)."""
    if not text:
        return -1
    text_lower = text.lower()
    best_idx = -1
    best_overlap = 0
    for i, c in enumerate(candidates):
        # Count shared words
        c_words = set(c.lower().split())
        t_words = set(text_lower.split())
        overlap = len(c_words & t_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_idx = i
    return best_idx if best_overlap >= 3 else -1

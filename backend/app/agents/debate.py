"""
Debate Orchestrator.

Runs an iterative Writer → Critic → Rewrite debate loop, then asks
the Judge to select the winning comment(s).

Flow per post:
  1. Writer generates N initial comment candidates.
  2. For each debate round:
     a. Critic scores every active comment.
     b. Comments already excellent (score ≥ threshold) are parked.
     c. Writer rewrites the remaining comments using critic feedback.
  3. Judge picks the best 1-2 comments from all final candidates.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from app.agents.critic import CriticAgent, CritiqueResult
from app.agents.judge import JudgeAgent, JudgeSelection
from app.agents.writer import WriterAgent
from app.services.scraping.models import ScrapedPost

logger = logging.getLogger(__name__)

# Comments with this score or above are "parked" — no further rewrites.
_EXCELLENCE_THRESHOLD = 0.9


@dataclass
class CommentEvolution:
    """Tracks a comment through the debate rounds."""

    text: str
    version: int = 1
    critiques: list[CritiqueResult] = field(default_factory=list)

    @property
    def latest_score(self) -> float:
        return self.critiques[-1].score if self.critiques else 0.0

    @property
    def latest_critique_summary(self) -> str:
        return self.critiques[-1].summary if self.critiques else ""


@dataclass
class DebateResult:
    """Complete result of a debate for one post."""

    post: ScrapedPost
    evolutions: list[CommentEvolution]
    selections: list[JudgeSelection]


class DebateOrchestrator:
    """Run the multi-round Writer/Critic/Judge debate for a post.

    Args:
        writer:  WriterAgent instance (GPT).
        critic:  CriticAgent instance (DeepSeek).
        judge:   JudgeAgent instance (DeepSeek).
        rounds:  Number of critique-rewrite iterations (default 3).
        num_comments: Initial candidates to generate per post.
    """

    def __init__(
        self,
        *,
        writer: WriterAgent,
        critic: CriticAgent,
        judge: JudgeAgent,
        rounds: int = 3,
        num_comments: int = 3,
    ) -> None:
        self._writer = writer
        self._critic = critic
        self._judge = judge
        self._rounds = rounds
        self._num_comments = num_comments

    async def run(
        self,
        post: ScrapedPost,
        *,
        problem_description: str,
        product_description: str | None = None,
    ) -> DebateResult:
        """Execute the full debate loop for a single post.

        Returns a DebateResult with the full comment evolutions and
        final judge selections.
        """
        logger.info(
            "[debate] starting debate for post=%s  rounds=%d  num_comments=%d",
            post.post_url[:60],
            self._rounds,
            self._num_comments,
        )

        # ── Step 1: Generate initial comments ────────────────────────────
        initial_comments = await self._writer.generate(
            problem_description=problem_description,
            product_description=product_description,
            platform=post.platform,
            author=post.author or "Unknown",
            content=post.content,
            num_comments=self._num_comments,
        )

        evolutions = [
            CommentEvolution(text=c, version=1) for c in initial_comments
        ]

        logger.info(
            "[debate] generated %d initial comments", len(evolutions),
        )

        # ── Step 2: Debate rounds ────────────────────────────────────────
        for round_num in range(1, self._rounds + 1):
            logger.info("[debate] ── round %d/%d ──", round_num, self._rounds)

            for evo in evolutions:
                # Skip comments already excellent
                if evo.latest_score >= _EXCELLENCE_THRESHOLD:
                    logger.debug(
                        "[debate] skipping comment (score=%.2f ≥ %.2f)",
                        evo.latest_score,
                        _EXCELLENCE_THRESHOLD,
                    )
                    continue

                # ── 2a: Critique ─────────────────────────────────────────
                critique_result = await self._critic.critique(
                    comment=evo.text,
                    problem_description=problem_description,
                    platform=post.platform,
                    author=post.author or "Unknown",
                    content=post.content,
                    version=evo.version,
                )
                evo.critiques.append(critique_result)

                # ── 2b: Rewrite (if room for improvement) ───────────────
                if critique_result.score < _EXCELLENCE_THRESHOLD:
                    rewritten = await self._writer.rewrite(
                        comment=evo.text,
                        critique=critique_result.summary,
                        author=post.author or "Unknown",
                        content=post.content,
                    )
                    evo.text = rewritten
                    evo.version += 1

            logger.info(
                "[debate] round %d complete  scores=%s",
                round_num,
                [f"{e.latest_score:.2f}" for e in evolutions],
            )

        # ── Step 3: Judge selects winners ────────────────────────────────
        final_comments = [evo.text for evo in evolutions]

        selections = await self._judge.judge(
            candidates=final_comments,
            problem_description=problem_description,
            platform=post.platform,
            author=post.author or "Unknown",
            content=post.content,
        )

        logger.info(
            "[debate] judge selected %d winner(s) with scores %s",
            len(selections),
            [f"{s.final_score:.2f}" for s in selections],
        )

        return DebateResult(
            post=post,
            evolutions=evolutions,
            selections=selections,
        )

    async def run_batch(
        self,
        posts: list[ScrapedPost],
        *,
        problem_description: str,
        product_description: str | None = None,
    ) -> list[DebateResult]:
        """Run the debate loop for multiple posts sequentially.

        Sequential to respect rate-limits on the AI endpoints.
        """
        results: list[DebateResult] = []
        for i, post in enumerate(posts, 1):
            logger.info(
                "[debate] processing post %d/%d  url=%s",
                i,
                len(posts),
                post.post_url[:60],
            )
            try:
                result = await self.run(
                    post,
                    problem_description=problem_description,
                    product_description=product_description,
                )
                results.append(result)
            except Exception:
                logger.warning(
                    "[debate] failed on post=%s, skipping",
                    post.post_url[:60],
                    exc_info=True,
                )

            # Pause between posts to stay under rate limits
            if i < len(posts):
                await asyncio.sleep(5)

        logger.info(
            "[debate] batch complete: %d/%d posts processed",
            len(results),
            len(posts),
        )
        return results

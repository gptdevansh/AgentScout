"""
LinkedIn scraper implementation.

Uses Apify's LinkedIn post search actor to discover posts
matching a keyword query, then normalises the raw results
into the platform-agnostic ScrapedPost schema.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.integrations.apify.client import ApifyClient
from app.services.scraping.base import ScraperPlatform
from app.services.scraping.models import ScrapedPost, ScrapingWeapon

logger = logging.getLogger(__name__)

# Apify actor: apimaestro/linkedin-posts-search-scraper-no-cookies
# Uses '~' separator as required by the Apify REST API.
_LINKEDIN_SEARCH_ACTOR = "apimaestro~linkedin-posts-search-scraper-no-cookies"


class ApifyLinkedInScraper(ScraperPlatform):
    """Scrapes LinkedIn posts via Apify."""

    def __init__(self, apify_client: ApifyClient) -> None:
        self._apify = apify_client

    # ── ScraperPlatform interface ────────────────────────────────────────

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def search_posts(
        self,
        query: str | ScrapingWeapon,
        *,
        max_results: int = 10,
    ) -> list[ScrapedPost]:
        """Search LinkedIn for posts matching *query* via Apify.

        Args:
            query: Keyword search string or ScrapingWeapon object.
            max_results: Maximum posts to return.

        Returns:
            List of normalised ScrapedPost objects.
        """
        actor_input = self._build_actor_input(query, max_results)

        query_str = query.value if isinstance(query, ScrapingWeapon) else query

        logger.info(
            "LinkedIn search: query=%r  max_results=%d",
            query_str,
            max_results,
        )

        raw_items = await self._apify.run_actor(
            _LINKEDIN_SEARCH_ACTOR,
            actor_input,
            timeout_secs=120,
            memory_mbytes=256,
        )

        posts = self._normalise_results(raw_items, source_query=query_str)
        logger.info("LinkedIn search returned %d posts for query=%r", len(posts), query_str)
        return posts

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _build_actor_input(query: str | ScrapingWeapon, max_results: int) -> dict[str, Any]:
        """Construct the JSON input payload for the Apify actor."""
        payload = {
            "maxResults": max_results,
            "sortBy": "relevance",
        }
        
        if isinstance(query, ScrapingWeapon):
            if query.type == "url":
                payload["startUrls"] = [{"url": query.value}]
            else:
                payload["searchTerms"] = [query.value]
        else:
            payload["searchTerms"] = [query]
            
        return payload

    @classmethod
    def _normalise_results(
        cls,
        raw_items: list[dict[str, Any]],
        *,
        source_query: str,
    ) -> list[ScrapedPost]:
        """Transform raw Apify output into ScrapedPost objects.

        Silently skips items that cannot be parsed (missing URL or content).
        """
        posts: list[ScrapedPost] = []
        for item in raw_items:
            try:
                post = cls._parse_item(item, source_query=source_query)
                if post is not None:
                    posts.append(post)
            except Exception:
                logger.warning("Skipping unparseable LinkedIn item: %s", item.get("post_url", "??"))
        return posts

    @staticmethod
    def _parse_item(
        item: dict[str, Any],
        *,
        source_query: str,
    ) -> ScrapedPost | None:
        """Parse a single Apify result dict into a ScrapedPost.

        The actor ``apimaestro~linkedin-posts-search-scraper-no-cookies``
        returns items shaped like::

            {
                "post_url": "https://www.linkedin.com/posts/...",
                "text": "post body…",
                "author": {"name": "...", "headline": "..."},
                "stats": {"total_reactions": 14, "comments": 4, "shares": 0},
                "posted_at": {"date": "2026-03-06 18:44:23", "timestamp": 1772819063948},
                ...
            }

        Returns None if required fields (post_url, text) are missing.
        """
        post_url = item.get("post_url") or item.get("url") or item.get("link")
        content = item.get("text") or item.get("content") or item.get("body")

        if not post_url or not content:
            return None

        # ── Author (nested object or flat string) ────────────────────────
        author_raw = item.get("author")
        if isinstance(author_raw, dict):
            author_name = author_raw.get("name") or author_raw.get("profileName")
        else:
            author_name = author_raw or item.get("authorName") or item.get("profileName")

        # ── Engagement stats (nested object or flat fields) ──────────────
        stats = item.get("stats") or {}
        likes = int(stats.get("total_reactions", 0) or item.get("likes", 0) or 0)
        comments_count = int(stats.get("comments", 0) or item.get("commentsCount", 0) or 0)

        # ── Timestamp (nested or flat) ───────────────────────────────────
        posted_at = item.get("posted_at") or {}
        raw_ts = (
            posted_at.get("timestamp")
            or posted_at.get("date")
            or item.get("postedAt")
            or item.get("timestamp")
            or item.get("date")
        )
        post_timestamp: datetime | None = None
        if raw_ts:
            try:
                if isinstance(raw_ts, (int, float)):
                    # Apify sometimes returns milliseconds
                    ts = raw_ts / 1000 if raw_ts > 1e12 else raw_ts
                    post_timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    post_timestamp = datetime.fromisoformat(str(raw_ts))
            except (ValueError, OSError):
                post_timestamp = None

        return ScrapedPost(
            platform="linkedin",
            post_url=str(post_url),
            author=author_name,
            content=str(content),
            likes=likes,
            comments_count=comments_count,
            post_timestamp=post_timestamp,
            source_query=source_query,
        )

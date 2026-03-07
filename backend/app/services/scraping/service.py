"""
Scraping service.

Orchestrates the scraping pipeline: resolves the correct platform
scraper, executes the search, and returns normalised results.
This is the single entry-point the rest of the application uses
for all scraping operations.
"""

import asyncio
import logging

from app.services.scraping.models import ScrapedPost
from app.services.scraping.registry import ScraperRegistry

logger = logging.getLogger(__name__)


class ScrapingService:
    """High-level scraping facade used by orchestrators and routes."""

    def __init__(self, registry: ScraperRegistry) -> None:
        self._registry = registry

    async def search(
        self,
        query: str,
        *,
        platform: str = "linkedin",
        max_results: int = 10,
    ) -> list[ScrapedPost]:
        """Search a single platform for posts matching *query*.

        Args:
            query: Free-text search query.
            platform: Target platform name (must be registered).
            max_results: Upper bound on the number of posts to return.

        Returns:
            List of normalised ScrapedPost objects.

        Raises:
            KeyError: If the requested platform is not registered.
        """
        scraper = self._registry.get(platform)
        logger.info("Scraping platform=%s  query=%r  max=%d", platform, query, max_results)
        return await scraper.search_posts(query, max_results=max_results)

    async def search_multiple_queries(
        self,
        queries: list[str],
        *,
        platform: str = "linkedin",
        max_results_per_query: int = 10,
    ) -> list[ScrapedPost]:
        """Run multiple search queries against a platform and deduplicate.

        Args:
            queries: List of search query strings.
            platform: Target platform name.
            max_results_per_query: Max posts per individual query.

        Returns:
            Deduplicated list of ScrapedPost objects.
        """
        scraper = self._registry.get(platform)
        logger.info(
            "Multi-query scrape: platform=%s  queries=%d  max_per_query=%d",
            platform,
            len(queries),
            max_results_per_query,
        )

        tasks = [
            scraper.search_posts(q, max_results=max_results_per_query)
            for q in queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and deduplicate by URL
        seen_urls: set[str] = set()
        unique_posts: list[ScrapedPost] = []

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Query failed: %s", result)
                continue
            for post in result:
                if post.post_url not in seen_urls:
                    seen_urls.add(post.post_url)
                    unique_posts.append(post)

        logger.info(
            "Multi-query scrape complete: %d unique posts from %d queries",
            len(unique_posts),
            len(queries),
        )
        return unique_posts

    @property
    def available_platforms(self) -> list[str]:
        """Return the list of registered platform names."""
        return self._registry.available_platforms

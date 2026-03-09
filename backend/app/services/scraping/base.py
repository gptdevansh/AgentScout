"""
Abstract base class for platform scrapers.

Every supported platform (LinkedIn, Twitter, Reddit, …) must provide
a concrete implementation of this interface.  The scraping service
operates only through this contract, making the system trivially
extensible to new platforms.
"""

from abc import ABC, abstractmethod

from app.services.scraping.models import ScrapedPost, ScrapingWeapon


class ScraperPlatform(ABC):
    """Contract that every platform scraper must fulfil."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the canonical platform identifier (e.g. 'linkedin')."""
        ...

    @abstractmethod
    async def search_posts(
        self,
        query: str | ScrapingWeapon,
        *,
        max_results: int = 10,
    ) -> list[ScrapedPost]:
        """Search the platform for posts matching *query*.

        Args:
            query: Free-text search query.
            max_results: Upper bound on the number of posts to return.

        Returns:
            A list of normalised ScrapedPost objects.
        """
        ...

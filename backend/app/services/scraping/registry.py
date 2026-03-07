"""
Platform scraper registry.

Provides a central place to register and look up platform scrapers
by name.  New platforms are added by calling `registry.register(scraper)`
— no changes needed in the scraping service itself.
"""

import logging

from app.services.scraping.base import ScraperPlatform

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """Thread-safe registry mapping platform names → scraper instances."""

    def __init__(self) -> None:
        self._scrapers: dict[str, ScraperPlatform] = {}

    def register(self, scraper: ScraperPlatform) -> None:
        """Register a platform scraper.

        Args:
            scraper: A concrete ScraperPlatform implementation.

        Raises:
            ValueError: If a scraper for this platform is already registered.
        """
        name = scraper.platform_name
        if name in self._scrapers:
            raise ValueError(f"Scraper already registered for platform '{name}'")
        self._scrapers[name] = scraper
        logger.info("Registered scraper for platform=%s", name)

    def get(self, platform: str) -> ScraperPlatform:
        """Look up a scraper by platform name.

        Args:
            platform: The canonical platform identifier (e.g. 'linkedin').

        Returns:
            The registered ScraperPlatform instance.

        Raises:
            KeyError: If no scraper is registered for the given platform.
        """
        try:
            return self._scrapers[platform]
        except KeyError:
            available = ", ".join(sorted(self._scrapers)) or "(none)"
            raise KeyError(
                f"No scraper registered for platform '{platform}'. "
                f"Available: {available}"
            )

    @property
    def available_platforms(self) -> list[str]:
        """Return sorted list of registered platform names."""
        return sorted(self._scrapers)

    def __contains__(self, platform: str) -> bool:
        return platform in self._scrapers

    def __len__(self) -> int:
        return len(self._scrapers)

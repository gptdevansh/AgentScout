"""
Scraping service package.

Public surface:
    ScraperPlatform  – interface for platform scrapers
    ScrapedPost      – normalised post DTO
    ScraperRegistry  – platform look-up registry
    ScrapingService  – high-level scraping facade
"""

from app.services.scraping.base import ScraperPlatform  # noqa: F401
from app.services.scraping.models import ScrapedPost  # noqa: F401
from app.services.scraping.registry import ScraperRegistry  # noqa: F401
from app.services.scraping.service import ScrapingService  # noqa: F401
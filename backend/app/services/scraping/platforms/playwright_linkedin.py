"""
Playwright LinkedIn scraper implementation.

Uses Playwright to search for LinkedIn posts via DuckDuckGo
and normalises the raw results into the platform-agnostic ScrapedPost schema.
"""

import logging
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, Page
from playwright_stealth import Stealth

from app.services.scraping.base import ScraperPlatform
from app.services.scraping.models import ScrapedPost, ScrapingWeapon

logger = logging.getLogger(__name__)


class PlaywrightLinkedInScraper(ScraperPlatform):
    """Scrapes LinkedIn posts using Playwright (via DuckDuckGo search)."""

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def search_posts(
        self,
        query: str | ScrapingWeapon,
        *,
        max_results: int = 10,
    ) -> list[ScrapedPost]:
        """Search LinkedIn for posts matching *query* via Playwright.

        Args:
            query: Keyword search string or ScrapingWeapon object.
            max_results: Maximum posts to return.

        Returns:
            List of normalised ScrapedPost objects.
        """
        query_str = query.value if isinstance(query, ScrapingWeapon) else query

        logger.info(
            "Playwright LinkedIn search: query=%r max_results=%d",
            query_str,
            max_results,
        )

        posts: list[ScrapedPost] = []
        try:
            async with async_playwright() as p:
                # Launch Chromium (headless by default)
                browser: Browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # Use a specific user agent to look less like a bot
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page: Page = await context.new_page()
                await Stealth().apply_stealth_async(page)

                # Build the search query
                if isinstance(query, ScrapingWeapon) and query.type == "url":
                    # If it's a specific URL, just try and 'find' that URL's content (rough approach)
                    search_query = f"site:linkedin.com/posts/ \"{query.value}\""
                else:
                    search_query = f"site:linkedin.com/posts/ {query_str}"

                # Using Yahoo Search because Bing/Google are aggressively blocking headless browsers with CAPTCHAs
                url = f"https://search.yahoo.com/search?p={search_query}"
                
                logger.debug("Navigating to: %s", url)
                await page.goto(url, wait_until="domcontentloaded")
                # Wait briefly to let JS load and prevent immediate detection
                await page.wait_for_timeout(2000)

                results = await page.query_selector_all(".algo")
                
                if not results:
                    html_snippet = await page.content()
                    logger.warning("No elements found on Yahoo. HTML snippet: %s", html_snippet[:500])
                
                for idx, result in enumerate(results):
                    if len(posts) >= max_results:
                        break
                        
                    try:
                        # Extract link
                        link_el = await result.query_selector("a")
                        if not link_el:
                            continue
                            
                        post_url = await link_el.get_attribute("href")
                        if not post_url or "linkedin.com/posts/" not in post_url:
                            continue

                        # Extract title
                        title_el = await result.query_selector("h3.title")
                        title = await title_el.inner_text() if title_el else ""
                            
                        # Extract snippet for content
                        snippet_el = await result.query_selector(".compText p")
                        content = await snippet_el.inner_text() if snippet_el else ""
                        
                        if not content:
                            content = title
                        
                        # Very heuristic author parsing
                        author = "Unknown"
                        if " on LinkedIn:" in title:
                            author = title.split(" on LinkedIn:")[0].strip()
                        elif " - LinkedIn" in title:
                             author = title.split(" - LinkedIn")[0].strip()
                        elif " | LinkedIn" in title:
                             author = title.split(" | LinkedIn")[0].strip()
                             
                        post = ScrapedPost(
                            platform="linkedin",
                            post_url=post_url,
                            author=author,
                            content=content,
                            likes=0,  # Cannot reliably get likes from DDG snippets
                            comments_count=0,
                            post_timestamp=None, # Likewise for exact timestamp
                            source_query=query_str,
                        )
                        posts.append(post)
                        logger.debug("Scraped via Playwright: %s", post.post_url)
                        
                    except Exception as e:
                        logger.warning("Failed to parse DDG result %d: %s", idx, e)

                await browser.close()
                
        except Exception as e:
             logger.error("Playwright scraping failed: %s", e)

        logger.info("Playwright LinkedIn search returned %d posts for query=%r", len(posts), query_str)
        return posts

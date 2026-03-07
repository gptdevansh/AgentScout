"""
Apify HTTP client.

Provides a thin async wrapper around the Apify REST API for
running actors and retrieving their results.  Platform-specific
actor configurations are kept separate in dedicated modules.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

_APIFY_BASE_URL = "https://api.apify.com/v2"


class ApifyClient:
    """Async client for interacting with the Apify platform."""

    def __init__(self, *, api_token: str) -> None:
        self._api_token = api_token
        self._http = httpx.AsyncClient(
            base_url=_APIFY_BASE_URL,
            timeout=httpx.Timeout(connect=10, read=120, write=10, pool=10),
            headers={"Content-Type": "application/json"},
        )
        logger.info("Initialised ApifyClient")

    # ── Public API ───────────────────────────────────────────────────────

    async def run_actor(
        self,
        actor_id: str,
        run_input: dict[str, Any],
        *,
        memory_mbytes: int = 4096,
        timeout_secs: int = 300,
    ) -> list[dict[str, Any]]:
        """Run an Apify actor synchronously and return the dataset items.

        This calls the *run-sync-get-dataset-items* convenience endpoint
        which blocks until the run finishes and returns results directly.

        Args:
            actor_id: Actor identifier, e.g. "apify/linkedin-posts-scraper".
            run_input: JSON-serialisable input payload for the actor.
            memory_mbytes: Memory allocation for the run.
            timeout_secs: Maximum wall-clock time before the run is aborted.

        Returns:
            A list of result items (dicts).

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        url = f"/acts/{actor_id}/run-sync-get-dataset-items"
        params = {
            "token": self._api_token,
            "memory": memory_mbytes,
            "timeout": timeout_secs,
        }

        logger.info(
            "Running Apify actor=%s  memory=%dMB  timeout=%ds",
            actor_id,
            memory_mbytes,
            timeout_secs,
        )
        logger.debug("Actor input: %s", run_input)

        response = await self._http.post(url, params=params, json=run_input)
        response.raise_for_status()

        items: list[dict[str, Any]] = response.json()
        logger.info("Actor %s returned %d items", actor_id, len(items))
        return items

    async def run_actor_async(
        self,
        actor_id: str,
        run_input: dict[str, Any],
        *,
        memory_mbytes: int = 4096,
    ) -> dict[str, Any]:
        """Start an actor run without waiting for completion.

        Args:
            actor_id: Actor identifier.
            run_input: JSON payload.
            memory_mbytes: Memory allocation.

        Returns:
            Run metadata dict containing 'id', 'status', etc.
        """
        url = f"/acts/{actor_id}/runs"
        params = {"token": self._api_token, "memory": memory_mbytes}

        response = await self._http.post(url, params=params, json=run_input)
        response.raise_for_status()

        run_data: dict[str, Any] = response.json().get("data", {})
        logger.info("Started async actor run id=%s", run_data.get("id"))
        return run_data

    async def get_dataset_items(
        self,
        dataset_id: str,
        *,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch items from an Apify dataset.

        Args:
            dataset_id: Dataset identifier.
            limit: Max items to retrieve.
            offset: Pagination offset.

        Returns:
            List of item dicts.
        """
        url = f"/datasets/{dataset_id}/items"
        params = {
            "token": self._api_token,
            "limit": limit,
            "offset": offset,
        }

        response = await self._http.get(url, params=params)
        response.raise_for_status()
        items: list[dict[str, Any]] = response.json()
        logger.info("Fetched %d items from dataset=%s", len(items), dataset_id)
        return items

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying HTTP transport."""
        await self._http.aclose()
        logger.info("Closed ApifyClient")


def build_apify_client(settings: Settings) -> ApifyClient:
    """Factory: create an ApifyClient from application settings."""
    return ApifyClient(api_token=settings.apify_api_token)

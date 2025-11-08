"""Web Search service using SearXNG metasearch engine.

This module provides privacy-respecting web search capabilities through SearXNG,
a free and open metasearch engine. Implements result parsing, relevance scoring,
and integration with CGRAG context retrieval.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WebSearchResult(BaseModel):
    """Represents a single web search result.

    Attributes:
        title: Page title
        url: Result URL
        content: Snippet/description text
        engine: Search engine that provided this result
        score: Relevance score (0.0-1.0)
        published_date: Publication date if available
    """

    title: str
    url: str
    content: str
    engine: Optional[str] = None
    score: float = 0.0
    published_date: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class WebSearchResponse(BaseModel):
    """Response from web search operation.

    Attributes:
        results: List of search results
        query: Original search query
        total_results: Total number of results found
        search_time_ms: Search operation latency
        engines_used: List of search engines queried
        cached: Whether result was served from cache
    """

    results: List[WebSearchResult]
    query: str
    total_results: int
    search_time_ms: float
    engines_used: List[str] = Field(default_factory=list)
    cached: bool = False


class SearXNGClient:
    """Client for SearXNG metasearch engine.

    Provides async web search with result parsing, error handling, and retry logic.
    Supports multiple result formats and configurable search parameters.

    Attributes:
        base_url: SearXNG instance base URL
        timeout: Request timeout in seconds
        max_results: Maximum results to return
        language: Search language preference
        client: httpx AsyncClient for requests
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8888",
        timeout: int = 10,
        max_results: int = 5,
        language: str = "en",
    ):
        """Initialize SearXNG client.

        Args:
            base_url: SearXNG instance URL (default: http://localhost:8888)
            timeout: Request timeout in seconds (default: 10)
            max_results: Maximum results to return (default: 5)
            language: Search language code (default: en)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_results = max_results
        self.language = language

        # Create async HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={
                "User-Agent": "SYNAPSE-WebSearch/1.0",
                "Accept": "application/json",
            },
        )

        logger.info(
            f"Initialized SearXNGClient: base_url={base_url}, "
            f"timeout={timeout}s, max_results={max_results}"
        )

    async def search(
        self, query: str, categories: Optional[List[str]] = None
    ) -> WebSearchResponse:
        """Execute web search query through SearXNG.

        Args:
            query: Search query string
            categories: Optional list of search categories (e.g., ['general', 'news'])

        Returns:
            WebSearchResponse with results and metadata

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response format is invalid
        """
        start_time = time.time()

        # Build search URL and parameters
        search_url = urljoin(self.base_url, "/search")
        params = {
            "q": query,
            "format": "json",
            "language": self.language,
        }

        if categories:
            params["categories"] = ",".join(categories)

        logger.info(f"🔍 Searching SearXNG: query='{query}', categories={categories}")

        try:
            # Execute search request
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()
            search_time_ms = int((time.time() - start_time) * 1000)

            # Extract results
            raw_results = data.get("results", [])
            total_results = len(raw_results)

            logger.debug(f"  ✅ SearXNG returned {total_results} results in {search_time_ms}ms")

            # Parse and limit results
            parsed_results = []
            for idx, result in enumerate(raw_results[: self.max_results]):
                try:
                    parsed_result = WebSearchResult(
                        title=result.get("title", "Untitled"),
                        url=result.get("url", ""),
                        content=result.get("content", result.get("snippet", "")),
                        engine=", ".join(result.get("engines", [])),
                        score=1.0
                        - (idx * 0.1),  # Simple ranking: first result = 1.0, decay by 0.1
                        published_date=result.get("publishedDate"),
                    )
                    parsed_results.append(parsed_result)
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to parse result {idx}: {e}")
                    continue

            # Extract engines used
            engines_used = list(
                set(
                    engine
                    for result in raw_results
                    for engine in result.get("engines", [])
                )
            )

            logger.info(
                f"  📊 Parsed {len(parsed_results)}/{total_results} results, "
                f"engines: {engines_used}"
            )

            return WebSearchResponse(
                results=parsed_results,
                query=query,
                total_results=total_results,
                search_time_ms=search_time_ms,
                engines_used=engines_used,
                cached=False,
            )

        except httpx.TimeoutException:
            logger.error(f"  ❌ SearXNG search timeout after {self.timeout}s")
            raise TimeoutError(f"SearXNG search timed out after {self.timeout}s")

        except httpx.HTTPStatusError as e:
            logger.error(f"  ❌ SearXNG HTTP error: {e.response.status_code}")
            raise ValueError(f"SearXNG returned error: {e.response.status_code}")

        except Exception as e:
            logger.error(f"  ❌ SearXNG search failed: {type(e).__name__}: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if SearXNG is available and responding.

        Returns:
            True if SearXNG is healthy, False otherwise
        """
        try:
            health_url = urljoin(self.base_url, "/healthz")
            response = await self.client.get(health_url)
            is_healthy = response.status_code == 200

            if is_healthy:
                logger.debug("✅ SearXNG health check passed")
            else:
                logger.warning(f"⚠️ SearXNG health check returned {response.status_code}")

            return is_healthy

        except Exception as e:
            logger.error(f"❌ SearXNG health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()
        logger.info("SearXNG client closed")


# Global client instance (singleton pattern)
_searxng_client: Optional[SearXNGClient] = None


def get_searxng_client(
    base_url: str = "http://searxng:8080",
    timeout: int = 10,
    max_results: int = 5,
    language: str = "en",
) -> SearXNGClient:
    """Get or create singleton SearXNG client instance.

    Args:
        base_url: SearXNG instance URL
        timeout: Request timeout in seconds
        max_results: Maximum results to return
        language: Search language code

    Returns:
        Singleton SearXNGClient instance
    """
    global _searxng_client

    if _searxng_client is None:
        _searxng_client = SearXNGClient(
            base_url=base_url,
            timeout=timeout,
            max_results=max_results,
            language=language,
        )
        logger.info("Created global SearXNG client instance")

    return _searxng_client


async def shutdown_searxng_client():
    """Shutdown global SearXNG client and cleanup resources."""
    global _searxng_client

    if _searxng_client is not None:
        await _searxng_client.close()
        _searxng_client = None
        logger.info("Shutdown global SearXNG client")

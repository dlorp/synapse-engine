"""Web Search Augmentation for CRAG - Fallback to web search when local context insufficient.

This module implements web search augmentation for the IRRELEVANT category in CRAG.
Converts SearXNG search results to DocumentChunk format for unified pipeline processing.
"""

import logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSearchAugmenter:
    """Augments CGRAG with web search when local context is insufficient.

    When CRAG evaluates retrieval as IRRELEVANT (low relevance score),
    this component falls back to web search via SearXNG and converts
    results to DocumentChunk format for unified downstream processing.

    Attributes:
        searxng_client: SearXNG client for web search
        max_results: Maximum web search results to return
    """

    def __init__(self, max_results: int = 5):
        """Initialize web search augmenter.

        Args:
            max_results: Maximum web search results to return (default: 5)
        """
        # Import here to avoid circular dependency
        from app.services.websearch import get_searxng_client

        self.searxng_client = get_searxng_client(
            base_url="http://searxng:8080", timeout=5, max_results=max_results
        )
        self.max_results = max_results

        logger.info(f"Initialized WebSearchAugmenter: max_results={max_results}")

    async def augment(self, query: str) -> List:
        """Perform web search and convert results to DocumentChunk format.

        Executes web search via SearXNG and converts search results to
        DocumentChunk objects compatible with CGRAG pipeline.

        Args:
            query: Search query

        Returns:
            List of DocumentChunk objects from web search results

        Raises:
            No exceptions raised - returns empty list on failure for graceful degradation
        """
        # Import here to avoid circular dependency
        from app.services.cgrag import DocumentChunk

        try:
            logger.info(f"[WEB_AUGMENT] Executing web search: query='{query[:50]}...'")

            # Execute web search via SearXNG
            search_response = await self.searxng_client.search(query)

            if not search_response.results:
                logger.warning("[WEB_AUGMENT] No web search results found")
                return []

            # Convert web results to DocumentChunk format
            chunks = []
            for idx, result in enumerate(search_response.results):
                # Combine title and content for chunk text
                chunk_content = f"{result.title}\n\n{result.content}"

                chunk = DocumentChunk(
                    file_path=result.url,  # Use URL as "file path" for tracking
                    content=chunk_content,
                    chunk_index=idx,
                    start_pos=0,
                    end_pos=len(chunk_content),
                    language="web",  # Special marker to identify web results
                    modified_time=datetime.utcnow(),
                    relevance_score=result.score,
                )
                chunks.append(chunk)

            logger.info(
                f"[WEB_AUGMENT] Retrieved {len(chunks)} web results in "
                f"{search_response.search_time_ms:.1f}ms"
            )

            return chunks

        except Exception as e:
            # Graceful degradation - log error but don't raise
            logger.error(
                f"[WEB_AUGMENT] Web search failed: {type(e).__name__}: {e}. "
                f"Returning empty list for graceful degradation."
            )
            return []

    async def health_check(self) -> bool:
        """Check if SearXNG service is available.

        Returns:
            True if SearXNG is healthy, False otherwise
        """
        try:
            return await self.searxng_client.health_check()
        except Exception as e:
            logger.error(f"[WEB_AUGMENT] Health check failed: {e}")
            return False

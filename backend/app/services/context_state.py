"""Context allocation state manager for query token tracking.

This module provides a centralized state management service for context window
allocations. It stores token allocation data for queries and provides retrieval
APIs for the Context Window Allocation Viewer feature.

The manager uses an in-memory dictionary for fast access with automatic cleanup
of old allocations to prevent memory growth.

Author: Backend Architect
Feature: Context Window Allocation Viewer
"""

import asyncio
import time
from typing import Dict, Optional

from app.core.logging import get_logger
from app.models.context import (
    ContextAllocation,
    ContextAllocationRequest,
    ContextComponent,
)
from app.services.token_counter import get_token_counter

logger = get_logger(__name__)


class ContextStateManager:
    """Manages context allocation state for queries.

    Tracks the context window allocation for each query, storing token counts
    for each component (system prompt, CGRAG context, user query, response budget).
    Provides retrieval APIs for frontend visualization.

    Architecture:
        - In-memory dict for fast access (sub-millisecond latency)
        - Auto-cleanup of old allocations after 1 hour
        - Thread-safe operations with asyncio.Lock
        - Token counting with tiktoken for accuracy

    Attributes:
        _allocations: Dict mapping query_id to ContextAllocation
        _lock: AsyncIO lock for thread-safe operations
        _cleanup_task: Background task for auto-cleanup
    """

    def __init__(self, cleanup_interval: int = 300, ttl_seconds: int = 3600):
        """Initialize context state manager.

        Args:
            cleanup_interval: How often to run cleanup task (seconds)
            ttl_seconds: How long to keep allocations (seconds)
        """
        self._allocations: Dict[str, tuple[ContextAllocation, float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._ttl_seconds = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"ContextStateManager initialized (cleanup_interval={cleanup_interval}s, "
            f"ttl={ttl_seconds}s)"
        )

    async def start(self) -> None:
        """Start the state manager and cleanup background task."""
        if self._running:
            logger.warning("ContextStateManager already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("ContextStateManager started")

    async def stop(self) -> None:
        """Stop the state manager and cleanup task."""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("ContextStateManager stopped")

    async def store_allocation(
        self, request: ContextAllocationRequest
    ) -> ContextAllocation:
        """Store context allocation for a query.

        Calculates token counts for each component, determines utilization
        percentage, and generates warnings if necessary.

        Args:
            request: Context allocation request with query data

        Returns:
            ContextAllocation with calculated token distributions
        """
        async with self._lock:
            # Get token counter
            token_counter = get_token_counter()

            # Count tokens for each component
            system_prompt_tokens = token_counter.count_tokens(request.system_prompt)
            cgrag_tokens = token_counter.count_tokens(request.cgrag_context)
            query_tokens = token_counter.count_tokens(request.user_query)

            # Calculate totals
            total_tokens_used = system_prompt_tokens + cgrag_tokens + query_tokens
            tokens_remaining = max(0, request.context_window_size - total_tokens_used)
            utilization_percentage = (
                total_tokens_used / request.context_window_size
            ) * 100

            # Generate warning if >80% utilized
            warning = None
            if utilization_percentage > 80:
                warning = f"Context window {utilization_percentage:.1f}% utilized - response may be truncated"

            # Create component objects
            components = [
                ContextComponent(
                    component="system_prompt",
                    tokens_used=system_prompt_tokens,
                    tokens_allocated=system_prompt_tokens,
                    percentage=(system_prompt_tokens / request.context_window_size)
                    * 100,
                    content_preview=request.system_prompt[:100]
                    if request.system_prompt
                    else None,
                ),
                ContextComponent(
                    component="cgrag_context",
                    tokens_used=cgrag_tokens,
                    tokens_allocated=cgrag_tokens,
                    percentage=(cgrag_tokens / request.context_window_size) * 100,
                    content_preview=request.cgrag_context[:100]
                    if request.cgrag_context
                    else None,
                ),
                ContextComponent(
                    component="user_query",
                    tokens_used=query_tokens,
                    tokens_allocated=query_tokens,
                    percentage=(query_tokens / request.context_window_size) * 100,
                    content_preview=request.user_query[:100]
                    if request.user_query
                    else None,
                ),
                ContextComponent(
                    component="response_budget",
                    tokens_used=0,
                    tokens_allocated=tokens_remaining,
                    percentage=(tokens_remaining / request.context_window_size) * 100,
                    content_preview=None,
                ),
            ]

            # Create allocation object
            allocation = ContextAllocation(
                query_id=request.query_id,
                model_id=request.model_id,
                context_window_size=request.context_window_size,
                total_tokens_used=total_tokens_used,
                tokens_remaining=tokens_remaining,
                utilization_percentage=utilization_percentage,
                components=components,
                cgrag_artifacts=request.cgrag_artifacts or [],
                warning=warning,
            )

            # Store with timestamp
            self._allocations[request.query_id] = (allocation, time.time())

            logger.info(
                f"Stored context allocation for query {request.query_id}: "
                f"{total_tokens_used}/{request.context_window_size} tokens "
                f"({utilization_percentage:.1f}%)",
                extra={
                    "query_id": request.query_id,
                    "model_id": request.model_id,
                    "total_tokens": total_tokens_used,
                    "context_size": request.context_window_size,
                    "utilization": round(utilization_percentage, 2),
                },
            )

            return allocation

    async def get_allocation(self, query_id: str) -> Optional[ContextAllocation]:
        """Retrieve context allocation for a query.

        Args:
            query_id: Unique query identifier

        Returns:
            ContextAllocation if found, None otherwise
        """
        async with self._lock:
            allocation_tuple = self._allocations.get(query_id)
            if allocation_tuple:
                return allocation_tuple[0]
            return None

    async def _cleanup_loop(self) -> None:
        """Background task that periodically cleans up old allocations.

        Removes allocations older than TTL to prevent memory growth.
        """
        logger.info("Context allocation cleanup loop started")

        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)

                async with self._lock:
                    current_time = time.time()
                    to_remove = []

                    for query_id, (allocation, timestamp) in self._allocations.items():
                        # Remove if older than TTL
                        if current_time - timestamp > self._ttl_seconds:
                            to_remove.append(query_id)

                    # Remove old allocations
                    for query_id in to_remove:
                        del self._allocations[query_id]

                    if to_remove:
                        logger.info(
                            f"Cleaned up {len(to_remove)} old context allocations",
                            extra={"removed_count": len(to_remove)},
                        )

            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Prevent tight error loop

        logger.info("Context allocation cleanup loop stopped")

    def get_stats(self) -> Dict:
        """Get context state manager statistics.

        Returns:
            Dictionary with statistics (total allocations, avg utilization)
        """
        if not self._allocations:
            return {"total_allocations": 0, "avg_utilization_percentage": 0.0}

        allocations_list = [alloc for alloc, _ in self._allocations.values()]
        avg_utilization = sum(a.utilization_percentage for a in allocations_list) / len(
            allocations_list
        )

        return {
            "total_allocations": len(self._allocations),
            "avg_utilization_percentage": round(avg_utilization, 2),
        }


# Global instance (initialized in main.py lifespan)
_context_state_manager: Optional[ContextStateManager] = None


def get_context_state_manager() -> ContextStateManager:
    """Get the global context state manager instance.

    Returns:
        Global ContextStateManager instance

    Raises:
        RuntimeError: If manager not initialized
    """
    if _context_state_manager is None:
        raise RuntimeError(
            "ContextStateManager not initialized - call init_context_state_manager() first"
        )
    return _context_state_manager


def init_context_state_manager(
    cleanup_interval: int = 300, ttl_seconds: int = 3600
) -> ContextStateManager:
    """Initialize the global context state manager instance.

    Should be called during application startup (in lifespan context).

    Args:
        cleanup_interval: How often to run cleanup task (seconds)
        ttl_seconds: How long to keep allocations (seconds)

    Returns:
        Initialized ContextStateManager instance
    """
    global _context_state_manager
    _context_state_manager = ContextStateManager(
        cleanup_interval=cleanup_interval, ttl_seconds=ttl_seconds
    )
    return _context_state_manager

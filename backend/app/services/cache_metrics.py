"""Redis Cache Metrics Tracking Service.

This module provides thread-safe cache performance metrics collection for
monitoring Redis cache effectiveness in production. Tracks hits, misses,
hit rate percentage, and cache size.

The cache metrics are used for:
- Production monitoring and alerting
- Cache optimization decisions
- Performance tuning
- Capacity planning

Author: Backend Architect
Phase: Production Metrics Implementation
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheMetrics:
    """Thread-safe Redis cache performance metrics tracker.

    This class provides atomic counters for tracking cache operations and
    calculating performance statistics. All operations are thread-safe using
    asyncio locks.

    Metrics Tracked:
        - hits: Number of cache hits (data found in cache)
        - misses: Number of cache misses (data not in cache)
        - total_requests: Total cache lookup attempts
        - hit_rate_percent: Percentage of requests served from cache
        - cache_size: Current number of keys in Redis
        - sets: Number of cache write operations
        - evictions: Number of keys evicted (future: from Redis INFO)

    Thread Safety:
        All counter updates use asyncio locks to prevent race conditions
        when multiple concurrent requests update metrics.

    Example Usage:
        # In a service method
        cache_metrics = get_cache_metrics()

        # On cache lookup
        value = redis_client.get(key)
        if value:
            await cache_metrics.record_hit()
        else:
            await cache_metrics.record_miss()

        # On cache write
        redis_client.set(key, value)
        await cache_metrics.record_set()

        # Get statistics
        stats = await cache_metrics.get_stats()
        logger.info(f"Cache hit rate: {stats['hit_rate_percent']:.1f}%")

    Attributes:
        _hits: Total cache hits counter
        _misses: Total cache misses counter
        _sets: Total cache writes counter
        _total_requests: Total lookup attempts counter
        _lock: AsyncIO lock for thread-safe operations
        _start_time: Timestamp when metrics tracking started
    """

    def __init__(self) -> None:
        """Initialize cache metrics tracker with zero counters."""
        self._hits: int = 0
        self._misses: int = 0
        self._sets: int = 0
        self._total_requests: int = 0
        self._lock = asyncio.Lock()
        self._start_time = time.time()

        logger.info("Cache metrics tracker initialized")

    async def record_hit(self) -> None:
        """Record a cache hit (data found in cache).

        Thread-safe increment of hit counter and total requests.
        Use this when a cache lookup returns data.
        """
        async with self._lock:
            self._hits += 1
            self._total_requests += 1

    async def record_miss(self) -> None:
        """Record a cache miss (data not in cache).

        Thread-safe increment of miss counter and total requests.
        Use this when a cache lookup returns no data.
        """
        async with self._lock:
            self._misses += 1
            self._total_requests += 1

    async def record_set(self) -> None:
        """Record a cache write operation.

        Thread-safe increment of set counter.
        Use this when writing data to cache.
        """
        async with self._lock:
            self._sets += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate percentage.

        Returns:
            Hit rate as percentage (0.0-100.0). Returns 0.0 if no requests yet.
        """
        if self._total_requests == 0:
            return 0.0
        return (self._hits / self._total_requests) * 100.0

    async def get_cache_size(self) -> int:
        """Get current number of keys in Redis cache.

        Queries Redis DBSIZE command to get key count. This is an O(1) operation.
        Returns 0 if Redis connection fails.

        Returns:
            Number of keys currently in Redis database
        """
        try:
            from app.core.config import get_config
            import redis

            config = get_config()
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
                socket_connect_timeout=2,
                decode_responses=True,
            )

            # DBSIZE is O(1) - returns number of keys in current DB
            cache_size = redis_client.dbsize()
            return cache_size

        except Exception as e:
            logger.warning(f"Failed to get cache size: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns all cache metrics including counters, rates, and metadata.
        Thread-safe snapshot of current metrics state.

        Returns:
            Dictionary containing:
                - hits: Total cache hits
                - misses: Total cache misses
                - sets: Total cache writes
                - total_requests: Total lookup attempts
                - hit_rate_percent: Hit rate percentage (0.0-100.0)
                - cache_size: Current number of keys in Redis
                - uptime_seconds: Time since metrics tracking started
                - timestamp: ISO timestamp of stats snapshot
        """
        async with self._lock:
            hits = self._hits
            misses = self._misses
            sets = self._sets
            total_requests = self._total_requests

        hit_rate = self.get_hit_rate()
        cache_size = await self.get_cache_size()
        uptime = time.time() - self._start_time

        return {
            "hits": hits,
            "misses": misses,
            "sets": sets,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": cache_size,
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def reset(self) -> None:
        """Reset all cache metrics counters to zero.

        Thread-safe reset of all counters. Use for testing or periodic resets.
        Resets start time to current time.
        """
        async with self._lock:
            self._hits = 0
            self._misses = 0
            self._sets = 0
            self._total_requests = 0
            self._start_time = time.time()

        logger.info("Cache metrics reset")


# Global cache metrics instance (initialized in main.py lifespan)
_cache_metrics: Optional[CacheMetrics] = None


def get_cache_metrics() -> CacheMetrics:
    """Get the global cache metrics instance.

    Returns:
        Global CacheMetrics instance

    Raises:
        RuntimeError: If cache metrics not initialized
    """
    if _cache_metrics is None:
        raise RuntimeError(
            "CacheMetrics not initialized - call init_cache_metrics() first"
        )
    return _cache_metrics


def init_cache_metrics() -> CacheMetrics:
    """Initialize the global cache metrics instance.

    Should be called during application startup (in lifespan context).

    Returns:
        Initialized CacheMetrics instance
    """
    global _cache_metrics
    _cache_metrics = CacheMetrics()
    return _cache_metrics

"""Tests for the CacheMetrics service.

This module tests the Redis cache metrics tracking functionality including:
- Recording hits, misses, and sets
- Hit rate calculation
- Statistics retrieval
- Thread-safe operations
- Singleton initialization
"""

import pytest
from unittest.mock import patch, AsyncMock

from app.services.cache_metrics import (
    CacheMetrics,
    get_cache_metrics,
    init_cache_metrics,
)


class TestCacheMetrics:
    """Tests for the CacheMetrics class."""

    @pytest.fixture
    def cache_metrics(self) -> CacheMetrics:
        """Create a fresh CacheMetrics instance for testing."""
        return CacheMetrics()

    async def test_init_zero_counters(self, cache_metrics: CacheMetrics) -> None:
        """Test CacheMetrics initializes with zero counters."""
        assert cache_metrics._hits == 0
        assert cache_metrics._misses == 0
        assert cache_metrics._sets == 0
        assert cache_metrics._total_requests == 0

    async def test_record_hit(self, cache_metrics: CacheMetrics) -> None:
        """Test recording a cache hit."""
        await cache_metrics.record_hit()

        assert cache_metrics._hits == 1
        assert cache_metrics._total_requests == 1
        assert cache_metrics._misses == 0

    async def test_record_multiple_hits(self, cache_metrics: CacheMetrics) -> None:
        """Test recording multiple cache hits."""
        for _ in range(5):
            await cache_metrics.record_hit()

        assert cache_metrics._hits == 5
        assert cache_metrics._total_requests == 5

    async def test_record_miss(self, cache_metrics: CacheMetrics) -> None:
        """Test recording a cache miss."""
        await cache_metrics.record_miss()

        assert cache_metrics._misses == 1
        assert cache_metrics._total_requests == 1
        assert cache_metrics._hits == 0

    async def test_record_multiple_misses(self, cache_metrics: CacheMetrics) -> None:
        """Test recording multiple cache misses."""
        for _ in range(3):
            await cache_metrics.record_miss()

        assert cache_metrics._misses == 3
        assert cache_metrics._total_requests == 3

    async def test_record_set(self, cache_metrics: CacheMetrics) -> None:
        """Test recording a cache set operation."""
        await cache_metrics.record_set()

        assert cache_metrics._sets == 1
        # Set doesn't affect total_requests (which is for lookups)
        assert cache_metrics._total_requests == 0

    async def test_record_multiple_sets(self, cache_metrics: CacheMetrics) -> None:
        """Test recording multiple cache set operations."""
        for _ in range(4):
            await cache_metrics.record_set()

        assert cache_metrics._sets == 4

    async def test_get_hit_rate_no_requests(self, cache_metrics: CacheMetrics) -> None:
        """Test hit rate calculation with no requests."""
        hit_rate = cache_metrics.get_hit_rate()
        assert hit_rate == 0.0

    async def test_get_hit_rate_all_hits(self, cache_metrics: CacheMetrics) -> None:
        """Test hit rate calculation with 100% hits."""
        for _ in range(10):
            await cache_metrics.record_hit()

        hit_rate = cache_metrics.get_hit_rate()
        assert hit_rate == 100.0

    async def test_get_hit_rate_all_misses(self, cache_metrics: CacheMetrics) -> None:
        """Test hit rate calculation with 0% hits."""
        for _ in range(10):
            await cache_metrics.record_miss()

        hit_rate = cache_metrics.get_hit_rate()
        assert hit_rate == 0.0

    async def test_get_hit_rate_mixed(self, cache_metrics: CacheMetrics) -> None:
        """Test hit rate calculation with mixed hits and misses."""
        # 3 hits, 2 misses = 60% hit rate
        for _ in range(3):
            await cache_metrics.record_hit()
        for _ in range(2):
            await cache_metrics.record_miss()

        hit_rate = cache_metrics.get_hit_rate()
        assert hit_rate == 60.0

    async def test_get_stats(self, cache_metrics: CacheMetrics) -> None:
        """Test getting comprehensive statistics."""
        # Record some activity
        await cache_metrics.record_hit()
        await cache_metrics.record_hit()
        await cache_metrics.record_miss()
        await cache_metrics.record_set()

        # Mock Redis connection to avoid actual Redis dependency
        with patch.object(
            cache_metrics, "get_cache_size", new_callable=AsyncMock
        ) as mock_size:
            mock_size.return_value = 100

            stats = await cache_metrics.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["total_requests"] == 3
        assert stats["hit_rate_percent"] == pytest.approx(66.67, rel=0.01)
        assert stats["cache_size"] == 100
        assert "uptime_seconds" in stats
        assert "timestamp" in stats

    async def test_get_cache_size_redis_failure(
        self, cache_metrics: CacheMetrics
    ) -> None:
        """Test get_cache_size returns 0 on Redis failure."""
        with patch("app.core.config.get_config") as mock_config:
            # Make config raise an exception
            mock_config.side_effect = Exception("Redis connection failed")

            size = await cache_metrics.get_cache_size()
            assert size == 0

    async def test_reset(self, cache_metrics: CacheMetrics) -> None:
        """Test resetting all metrics."""
        # Record some activity
        await cache_metrics.record_hit()
        await cache_metrics.record_miss()
        await cache_metrics.record_set()

        # Reset
        await cache_metrics.reset()

        assert cache_metrics._hits == 0
        assert cache_metrics._misses == 0
        assert cache_metrics._sets == 0
        assert cache_metrics._total_requests == 0


class TestCacheMetricsConcurrency:
    """Tests for CacheMetrics thread-safety."""

    async def test_concurrent_hits(self) -> None:
        """Test concurrent hit recording is thread-safe."""
        import asyncio

        cache_metrics = CacheMetrics()

        async def record_many_hits():
            for _ in range(100):
                await cache_metrics.record_hit()

        # Run multiple concurrent tasks
        await asyncio.gather(
            record_many_hits(),
            record_many_hits(),
            record_many_hits(),
        )

        # Should have exactly 300 hits
        assert cache_metrics._hits == 300
        assert cache_metrics._total_requests == 300

    async def test_concurrent_mixed_operations(self) -> None:
        """Test concurrent mixed operations are thread-safe."""
        import asyncio

        cache_metrics = CacheMetrics()

        async def record_hits():
            for _ in range(50):
                await cache_metrics.record_hit()

        async def record_misses():
            for _ in range(30):
                await cache_metrics.record_miss()

        async def record_sets():
            for _ in range(20):
                await cache_metrics.record_set()

        await asyncio.gather(
            record_hits(),
            record_misses(),
            record_sets(),
        )

        assert cache_metrics._hits == 50
        assert cache_metrics._misses == 30
        assert cache_metrics._sets == 20
        assert cache_metrics._total_requests == 80


class TestCacheMetricsSingleton:
    """Tests for cache metrics singleton functions."""

    def test_get_cache_metrics_uninitialized_raises(self) -> None:
        """Test get_cache_metrics raises when not initialized."""
        # Reset global state
        import app.services.cache_metrics as cm

        original = cm._cache_metrics
        cm._cache_metrics = None

        try:
            with pytest.raises(RuntimeError, match="not initialized"):
                get_cache_metrics()
        finally:
            cm._cache_metrics = original

    def test_init_cache_metrics_creates_instance(self) -> None:
        """Test init_cache_metrics creates and returns instance."""
        import app.services.cache_metrics as cm

        original = cm._cache_metrics
        cm._cache_metrics = None

        try:
            instance = init_cache_metrics()
            assert isinstance(instance, CacheMetrics)
            assert cm._cache_metrics is instance
        finally:
            cm._cache_metrics = original

    def test_get_cache_metrics_after_init(self) -> None:
        """Test get_cache_metrics returns initialized instance."""
        import app.services.cache_metrics as cm

        original = cm._cache_metrics
        cm._cache_metrics = None

        try:
            init_cache_metrics()
            instance = get_cache_metrics()
            assert isinstance(instance, CacheMetrics)
        finally:
            cm._cache_metrics = original

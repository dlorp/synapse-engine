"""Tests for metrics models.

Tests validation and model behavior for system metrics,
query metrics, and resource utilization models.
"""

import pytest
from pydantic import ValidationError

from app.models.metrics import (
    QueryMetrics,
    TierMetrics,
    TierMetricsResponse,
    VRAMMetrics,
    CPUMetrics,
    MemoryMetrics,
    ThreadPoolStatus,
    DiskIOMetrics,
    NetworkThroughputMetrics,
    ResourceMetrics,
)


class TestQueryMetrics:
    """Tests for QueryMetrics model."""

    def test_valid_metrics(self):
        """Test creating valid query metrics."""
        metrics = QueryMetrics(
            timestamps=["2025-01-30T10:00:00Z", "2025-01-30T10:01:00Z"],
            query_rate=[10.5, 12.3],
            total_queries=1500,
            avg_latency_ms=45.5,
            tier_distribution={"Q2": 800, "Q3": 500, "Q4": 200},
        )
        assert len(metrics.timestamps) == 2
        assert metrics.total_queries == 1500
        assert metrics.avg_latency_ms == 45.5

    def test_empty_timestamps(self):
        """Test metrics with empty timestamps (no data yet)."""
        metrics = QueryMetrics(
            timestamps=[],
            query_rate=[],
            total_queries=0,
            avg_latency_ms=0.0,
            tier_distribution={"Q2": 0, "Q3": 0, "Q4": 0},
        )
        assert len(metrics.timestamps) == 0
        assert metrics.total_queries == 0

    def test_negative_total_queries_rejected(self):
        """Test negative total queries is rejected."""
        with pytest.raises(ValidationError):
            QueryMetrics(
                timestamps=[],
                query_rate=[],
                total_queries=-1,
                avg_latency_ms=0.0,
                tier_distribution={"Q2": 0},
            )

    def test_negative_latency_rejected(self):
        """Test negative latency is rejected."""
        with pytest.raises(ValidationError):
            QueryMetrics(
                timestamps=[],
                query_rate=[],
                total_queries=0,
                avg_latency_ms=-1.0,
                tier_distribution={"Q2": 0},
            )

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        metrics = QueryMetrics(
            timestamps=["2025-01-30T10:00:00Z"],
            query_rate=[5.0],
            total_queries=100,
            avg_latency_ms=30.0,
            tier_distribution={"Q2": 50, "Q3": 50},
        )
        data = metrics.model_dump(by_alias=True)
        assert "queryRate" in data
        assert "totalQueries" in data
        assert "avgLatencyMs" in data
        assert "tierDistribution" in data


class TestTierMetrics:
    """Tests for TierMetrics model."""

    def test_valid_tier_metrics(self):
        """Test creating valid tier metrics."""
        metrics = TierMetrics(
            name="Q2",
            tokens_per_sec=[150.0, 155.0, 148.0],
            latency_ms=[45.0, 42.0, 48.0],
            request_count=500,
            error_rate=0.02,
        )
        assert metrics.name == "Q2"
        assert len(metrics.tokens_per_sec) == 3
        assert metrics.error_rate == 0.02

    def test_all_tiers_valid(self):
        """Test all tier names are valid."""
        for tier in ["Q2", "Q3", "Q4"]:
            metrics = TierMetrics(
                name=tier,
                tokens_per_sec=[100.0],
                latency_ms=[50.0],
                request_count=100,
                error_rate=0.0,
            )
            assert metrics.name == tier

    def test_invalid_tier_rejected(self):
        """Test invalid tier name is rejected."""
        with pytest.raises(ValidationError):
            TierMetrics(
                name="Q5",  # Invalid
                tokens_per_sec=[100.0],
                latency_ms=[50.0],
                request_count=100,
                error_rate=0.0,
            )

    def test_negative_request_count_rejected(self):
        """Test negative request count is rejected."""
        with pytest.raises(ValidationError):
            TierMetrics(
                name="Q2",
                tokens_per_sec=[100.0],
                latency_ms=[50.0],
                request_count=-1,
                error_rate=0.0,
            )

    def test_error_rate_bounds(self):
        """Test error rate must be 0.0-1.0."""
        # Valid at 0
        metrics = TierMetrics(
            name="Q2",
            tokens_per_sec=[100.0],
            latency_ms=[50.0],
            request_count=100,
            error_rate=0.0,
        )
        assert metrics.error_rate == 0.0

        # Valid at 1.0 (100% error rate)
        metrics = TierMetrics(
            name="Q2",
            tokens_per_sec=[100.0],
            latency_ms=[50.0],
            request_count=100,
            error_rate=1.0,
        )
        assert metrics.error_rate == 1.0

    def test_error_rate_over_1_rejected(self):
        """Test error rate over 1.0 is rejected."""
        with pytest.raises(ValidationError):
            TierMetrics(
                name="Q2",
                tokens_per_sec=[100.0],
                latency_ms=[50.0],
                request_count=100,
                error_rate=1.1,
            )

    def test_error_rate_negative_rejected(self):
        """Test negative error rate is rejected."""
        with pytest.raises(ValidationError):
            TierMetrics(
                name="Q2",
                tokens_per_sec=[100.0],
                latency_ms=[50.0],
                request_count=100,
                error_rate=-0.1,
            )

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        metrics = TierMetrics(
            name="Q3",
            tokens_per_sec=[120.0],
            latency_ms=[60.0],
            request_count=200,
            error_rate=0.01,
        )
        data = metrics.model_dump(by_alias=True)
        assert "tokensPerSec" in data
        assert "latencyMs" in data
        assert "requestCount" in data
        assert "errorRate" in data


class TestTierMetricsResponse:
    """Tests for TierMetricsResponse model."""

    def test_response_with_tiers(self):
        """Test creating response with tier metrics."""
        tier_q2 = TierMetrics(
            name="Q2",
            tokens_per_sec=[150.0],
            latency_ms=[40.0],
            request_count=300,
            error_rate=0.01,
        )
        tier_q3 = TierMetrics(
            name="Q3",
            tokens_per_sec=[100.0],
            latency_ms=[80.0],
            request_count=200,
            error_rate=0.02,
        )
        response = TierMetricsResponse(tiers=[tier_q2, tier_q3])
        assert len(response.tiers) == 2

    def test_empty_response(self):
        """Test creating empty response."""
        response = TierMetricsResponse(tiers=[])
        assert len(response.tiers) == 0


class TestVRAMMetrics:
    """Tests for VRAMMetrics model."""

    def test_valid_vram_metrics(self):
        """Test creating valid VRAM metrics."""
        metrics = VRAMMetrics(
            used=12.5,
            total=24.0,
            percent=52.1,
        )
        assert metrics.used == 12.5
        assert metrics.total == 24.0
        assert metrics.percent == 52.1

    def test_zero_usage(self):
        """Test zero VRAM usage is valid."""
        metrics = VRAMMetrics(
            used=0.0,
            total=16.0,
            percent=0.0,
        )
        assert metrics.used == 0.0

    def test_full_usage(self):
        """Test full VRAM usage is valid."""
        metrics = VRAMMetrics(
            used=24.0,
            total=24.0,
            percent=100.0,
        )
        assert metrics.percent == 100.0

    def test_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            VRAMMetrics(used=-1.0, total=24.0, percent=0.0)
        with pytest.raises(ValidationError):
            VRAMMetrics(used=0.0, total=-1.0, percent=0.0)

    def test_percent_over_100_rejected(self):
        """Test percentage over 100 is rejected."""
        with pytest.raises(ValidationError):
            VRAMMetrics(used=25.0, total=24.0, percent=104.0)


class TestCPUMetrics:
    """Tests for CPUMetrics model."""

    def test_valid_cpu_metrics(self):
        """Test creating valid CPU metrics."""
        metrics = CPUMetrics(
            percent=45.5,
            cores=8,
        )
        assert metrics.percent == 45.5
        assert metrics.cores == 8

    def test_idle_cpu(self):
        """Test idle CPU (0%) is valid."""
        metrics = CPUMetrics(percent=0.0, cores=4)
        assert metrics.percent == 0.0

    def test_full_cpu(self):
        """Test full CPU (100%) is valid."""
        metrics = CPUMetrics(percent=100.0, cores=16)
        assert metrics.percent == 100.0

    def test_percent_over_100_rejected(self):
        """Test percentage over 100 is rejected."""
        with pytest.raises(ValidationError):
            CPUMetrics(percent=100.1, cores=8)

    def test_negative_percent_rejected(self):
        """Test negative percentage is rejected."""
        with pytest.raises(ValidationError):
            CPUMetrics(percent=-1.0, cores=8)

    def test_zero_cores_rejected(self):
        """Test zero cores is rejected."""
        with pytest.raises(ValidationError):
            CPUMetrics(percent=50.0, cores=0)


class TestMemoryMetrics:
    """Tests for MemoryMetrics model."""

    def test_valid_memory_metrics(self):
        """Test creating valid memory metrics."""
        metrics = MemoryMetrics(
            used=32.5,
            total=64.0,
            percent=50.8,
        )
        assert metrics.used == 32.5
        assert metrics.total == 64.0

    def test_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            MemoryMetrics(used=-1.0, total=64.0, percent=0.0)

    def test_percent_bounds(self):
        """Test percentage bounds."""
        # Valid at 0
        metrics = MemoryMetrics(used=0.0, total=64.0, percent=0.0)
        assert metrics.percent == 0.0

        # Valid at 100
        metrics = MemoryMetrics(used=64.0, total=64.0, percent=100.0)
        assert metrics.percent == 100.0


class TestThreadPoolStatus:
    """Tests for ThreadPoolStatus model."""

    def test_valid_status(self):
        """Test creating valid thread pool status."""
        status = ThreadPoolStatus(
            active=5,
            queued=10,
        )
        assert status.active == 5
        assert status.queued == 10

    def test_idle_pool(self):
        """Test idle thread pool (all zeros)."""
        status = ThreadPoolStatus(active=0, queued=0)
        assert status.active == 0
        assert status.queued == 0

    def test_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            ThreadPoolStatus(active=-1, queued=0)
        with pytest.raises(ValidationError):
            ThreadPoolStatus(active=0, queued=-1)


class TestDiskIOMetrics:
    """Tests for DiskIOMetrics model."""

    def test_valid_disk_io(self):
        """Test creating valid disk I/O metrics."""
        metrics = DiskIOMetrics(
            read_mbps=150.5,
            write_mbps=75.3,
        )
        assert metrics.read_mbps == 150.5
        assert metrics.write_mbps == 75.3

    def test_idle_disk(self):
        """Test idle disk (no I/O)."""
        metrics = DiskIOMetrics(read_mbps=0.0, write_mbps=0.0)
        assert metrics.read_mbps == 0.0

    def test_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            DiskIOMetrics(read_mbps=-1.0, write_mbps=0.0)
        with pytest.raises(ValidationError):
            DiskIOMetrics(read_mbps=0.0, write_mbps=-1.0)

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        metrics = DiskIOMetrics(read_mbps=100.0, write_mbps=50.0)
        data = metrics.model_dump(by_alias=True)
        assert "readMBps" in data
        assert "writeMBps" in data


class TestNetworkThroughputMetrics:
    """Tests for NetworkThroughputMetrics model."""

    def test_valid_network_metrics(self):
        """Test creating valid network metrics."""
        metrics = NetworkThroughputMetrics(
            rx_mbps=250.0,
            tx_mbps=125.0,
        )
        assert metrics.rx_mbps == 250.0
        assert metrics.tx_mbps == 125.0

    def test_no_traffic(self):
        """Test no network traffic."""
        metrics = NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=0.0)
        assert metrics.rx_mbps == 0.0

    def test_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            NetworkThroughputMetrics(rx_mbps=-1.0, tx_mbps=0.0)
        with pytest.raises(ValidationError):
            NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=-1.0)

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        metrics = NetworkThroughputMetrics(rx_mbps=100.0, tx_mbps=50.0)
        data = metrics.model_dump(by_alias=True)
        assert "rxMBps" in data
        assert "txMBps" in data


class TestResourceMetrics:
    """Tests for ResourceMetrics model."""

    def test_valid_resource_metrics(self):
        """Test creating valid resource metrics."""
        vram = VRAMMetrics(used=12.0, total=24.0, percent=50.0)
        cpu = CPUMetrics(percent=45.0, cores=8)
        memory = MemoryMetrics(used=32.0, total=64.0, percent=50.0)
        thread_pool = ThreadPoolStatus(active=5, queued=2)
        disk_io = DiskIOMetrics(read_mbps=100.0, write_mbps=50.0)
        network = NetworkThroughputMetrics(rx_mbps=200.0, tx_mbps=100.0)

        metrics = ResourceMetrics(
            vram=vram,
            cpu=cpu,
            memory=memory,
            faiss_index_size=1024000,
            redis_cache_size=512000,
            active_connections=25,
            thread_pool_status=thread_pool,
            disk_io=disk_io,
            network_throughput=network,
        )
        assert metrics.faiss_index_size == 1024000
        assert metrics.active_connections == 25

    def test_zero_sizes(self):
        """Test zero sizes are valid (fresh system)."""
        vram = VRAMMetrics(used=0.0, total=24.0, percent=0.0)
        cpu = CPUMetrics(percent=0.0, cores=8)
        memory = MemoryMetrics(used=0.0, total=64.0, percent=0.0)
        thread_pool = ThreadPoolStatus(active=0, queued=0)
        disk_io = DiskIOMetrics(read_mbps=0.0, write_mbps=0.0)
        network = NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=0.0)

        metrics = ResourceMetrics(
            vram=vram,
            cpu=cpu,
            memory=memory,
            faiss_index_size=0,
            redis_cache_size=0,
            active_connections=0,
            thread_pool_status=thread_pool,
            disk_io=disk_io,
            network_throughput=network,
        )
        assert metrics.faiss_index_size == 0
        assert metrics.redis_cache_size == 0

    def test_negative_sizes_rejected(self):
        """Test negative sizes are rejected."""
        vram = VRAMMetrics(used=0.0, total=24.0, percent=0.0)
        cpu = CPUMetrics(percent=0.0, cores=8)
        memory = MemoryMetrics(used=0.0, total=64.0, percent=0.0)
        thread_pool = ThreadPoolStatus(active=0, queued=0)
        disk_io = DiskIOMetrics(read_mbps=0.0, write_mbps=0.0)
        network = NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=0.0)

        with pytest.raises(ValidationError):
            ResourceMetrics(
                vram=vram,
                cpu=cpu,
                memory=memory,
                faiss_index_size=-1,
                redis_cache_size=0,
                active_connections=0,
                thread_pool_status=thread_pool,
                disk_io=disk_io,
                network_throughput=network,
            )

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        vram = VRAMMetrics(used=12.0, total=24.0, percent=50.0)
        cpu = CPUMetrics(percent=45.0, cores=8)
        memory = MemoryMetrics(used=32.0, total=64.0, percent=50.0)
        thread_pool = ThreadPoolStatus(active=5, queued=2)
        disk_io = DiskIOMetrics(read_mbps=100.0, write_mbps=50.0)
        network = NetworkThroughputMetrics(rx_mbps=200.0, tx_mbps=100.0)

        metrics = ResourceMetrics(
            vram=vram,
            cpu=cpu,
            memory=memory,
            faiss_index_size=1000,
            redis_cache_size=500,
            active_connections=10,
            thread_pool_status=thread_pool,
            disk_io=disk_io,
            network_throughput=network,
        )
        data = metrics.model_dump(by_alias=True)
        assert "faissIndexSize" in data
        assert "redisCacheSize" in data
        assert "activeConnections" in data
        assert "threadPoolStatus" in data
        assert "diskIO" in data
        assert "networkThroughput" in data

#!/usr/bin/env python3
"""Test script for time-series metrics API endpoints.

This script tests the new time-series metrics endpoints by:
1. Recording some sample metrics
2. Querying the endpoints with different parameters
3. Verifying the response structure

Run this AFTER starting the backend server:
    docker-compose up -d synapse_core
    python scripts/test_timeseries_api.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.services.metrics_aggregator import init_metrics_aggregator
from app.models.timeseries import MetricType, TimeRange


async def test_metrics_aggregator():
    """Test the metrics aggregator service."""
    print("=" * 70)
    print("TESTING METRICS AGGREGATOR SERVICE")
    print("=" * 70)

    # Initialize aggregator
    print("\n1. Initializing metrics aggregator...")
    aggregator = init_metrics_aggregator()
    await aggregator.start()
    print("✅ Aggregator started")

    # Record sample metrics
    print("\n2. Recording sample metrics...")
    for i in range(10):
        await aggregator.record_metric(
            metric_name=MetricType.RESPONSE_TIME,
            value=1000.0 + (i * 100),
            metadata={"model_id": "test_model_q2", "tier": "Q2", "query_mode": "auto"},
        )
        await aggregator.record_metric(
            metric_name=MetricType.TOKENS_PER_SECOND,
            value=45.0 + (i * 2),
            metadata={"model_id": "test_model_q2", "tier": "Q2", "query_mode": "auto"},
        )
        await aggregator.record_metric(
            metric_name=MetricType.COMPLEXITY_SCORE,
            value=3.0 + (i * 0.5),
            metadata={"model_id": "test_model_q2", "tier": "Q2", "query_mode": "auto"},
        )
    print("✅ Recorded 30 sample metrics")

    # Test get_time_series
    print("\n3. Testing get_time_series()...")
    result = await aggregator.get_time_series(
        metric_name=MetricType.RESPONSE_TIME, time_range=TimeRange.ONE_HOUR, tier="Q2"
    )
    print(f"   Metric: {result.metric_name}")
    print(f"   Time range: {result.time_range}")
    print(f"   Unit: {result.unit}")
    print(f"   Data points: {len(result.data_points)}")
    print(
        f"   Summary: min={result.summary.min}, max={result.summary.max}, avg={result.summary.avg}"
    )
    print("✅ get_time_series() working")

    # Test get_summary
    print("\n4. Testing get_summary()...")
    summary = await aggregator.get_summary(
        metric_name=MetricType.TOKENS_PER_SECOND, time_range=TimeRange.ONE_HOUR
    )
    print(f"   Min: {summary.min}")
    print(f"   Max: {summary.max}")
    print(f"   Avg: {summary.avg}")
    print(f"   P95: {summary.p95}")
    print(f"   P99: {summary.p99}")
    print("✅ get_summary() working")

    # Test get_comparison
    print("\n5. Testing get_comparison()...")
    comparison = await aggregator.get_comparison(
        metric_names=[
            MetricType.RESPONSE_TIME,
            MetricType.TOKENS_PER_SECOND,
            MetricType.COMPLEXITY_SCORE,
        ],
        time_range=TimeRange.ONE_HOUR,
    )
    print(f"   Time range: {comparison.time_range}")
    print(f"   Labels: {len(comparison.chart_data.labels)} timestamps")
    print(f"   Datasets: {len(comparison.chart_data.datasets)}")
    for dataset in comparison.chart_data.datasets:
        print(
            f"     - {dataset.label}: {len(dataset.data)} points, unit={dataset.metadata.get('unit')}"
        )
    print("✅ get_comparison() working")

    # Test get_model_breakdown
    print("\n6. Testing get_model_breakdown()...")
    breakdown = await aggregator.get_model_breakdown(
        metric_name=MetricType.RESPONSE_TIME, time_range=TimeRange.ONE_HOUR
    )
    print(f"   Metric: {breakdown.metric_name}")
    print(f"   Models: {len(breakdown.models)}")
    for model in breakdown.models:
        print(
            f"     - {model.model_id} ({model.tier}): {len(model.data_points)} points"
        )
        print(f"       Summary: avg={model.summary.avg}, p95={model.summary.p95}")
    print("✅ get_model_breakdown() working")

    # Cleanup
    print("\n7. Stopping aggregator...")
    await aggregator.stop()
    print("✅ Aggregator stopped")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)


async def test_api_endpoints():
    """Test the REST API endpoints (requires running backend)."""
    import httpx

    base_url = "http://localhost:8000"

    print("\n" + "=" * 70)
    print("TESTING REST API ENDPOINTS")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Test /api/timeseries endpoint
        print("\n1. Testing GET /api/timeseries...")
        try:
            response = await client.get(
                f"{base_url}/api/timeseries",
                params={"metric": "response_time", "range": "1h", "tier": "Q2"},
                timeout=10.0,
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Metric: {data['metricName']}")
                print(f"   Data points: {len(data['dataPoints'])}")
                print("✅ GET /api/timeseries working")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test /api/timeseries/summary endpoint
        print("\n2. Testing GET /api/timeseries/summary...")
        try:
            response = await client.get(
                f"{base_url}/api/timeseries/summary",
                params={"metric": "response_time", "range": "24h"},
                timeout=10.0,
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Min: {data['min']}")
                print(f"   Max: {data['max']}")
                print(f"   Avg: {data['avg']}")
                print("✅ GET /api/timeseries/summary working")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test /api/timeseries/comparison endpoint
        print("\n3. Testing GET /api/timeseries/comparison...")
        try:
            response = await client.get(
                f"{base_url}/api/timeseries/comparison",
                params={"metrics": "response_time,tokens_per_second", "range": "6h"},
                timeout=10.0,
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Labels: {len(data['chartData']['labels'])}")
                print(f"   Datasets: {len(data['chartData']['datasets'])}")
                print("✅ GET /api/timeseries/comparison working")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test /api/timeseries/models endpoint
        print("\n4. Testing GET /api/timeseries/models...")
        try:
            response = await client.get(
                f"{base_url}/api/timeseries/models",
                params={"metric": "response_time", "range": "7d"},
                timeout=10.0,
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Models: {len(data['models'])}")
                print("✅ GET /api/timeseries/models working")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║     TIME-SERIES METRICS API TEST SUITE                       ║
║     S.Y.N.A.P.S.E. ENGINE - Phase 4 Component 3              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Test 1: Metrics aggregator service
    print("\n[TEST SUITE 1: Metrics Aggregator Service]")
    asyncio.run(test_metrics_aggregator())

    # Test 2: REST API endpoints (optional, requires running backend)
    print("\n\n[TEST SUITE 2: REST API Endpoints]")
    print("NOTE: This requires the backend server to be running.")
    print("      Start with: docker-compose up -d synapse_core")
    print("\nPress Enter to test API endpoints, or Ctrl+C to skip...")
    try:
        input()
        asyncio.run(test_api_endpoints())
    except KeyboardInterrupt:
        print("\n\nSkipping API endpoint tests.")

    print("\n\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)

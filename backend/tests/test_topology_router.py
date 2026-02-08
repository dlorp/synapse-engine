"""Tests for topology router endpoints.

Comprehensive tests for the /api/topology endpoints including:
- GET /api/topology/ - Complete system topology
- GET /api/topology/health/{component_id} - Component health metrics
- GET /api/topology/dataflow/{query_id} - Query data flow path
- GET /api/topology/nodes - All topology nodes
- GET /api/topology/connections - All topology connections

Tests cover success cases, error handling (404, 503, 500), and edge cases.

Author: Backend Architect Agent
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.topology import (
    ComponentConnection,
    ComponentNode,
    DataFlowPath,
    HealthMetrics,
    SystemTopology,
)
from app.routers import topology

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def app():
    """Create FastAPI app with topology router."""
    app = FastAPI()
    app.include_router(topology.router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_nodes():
    """Sample topology nodes for testing."""
    return [
        ComponentNode(
            id="orchestrator",
            type="orchestrator",
            label="Neural Substrate Orchestrator",
            status="healthy",
            metadata={"version": "5.0.0", "uptime_hours": 24.5},
            position={"x": 100, "y": 200},
        ),
        ComponentNode(
            id="q2_fast_1",
            type="model",
            label="Q2 FAST #1",
            status="healthy",
            metadata={"tier": "Q2", "memory_usage_mb": 2048.5},
            position={"x": 100, "y": 350},
        ),
        ComponentNode(
            id="faiss_index",
            type="storage",
            label="FAISS Vector Index",
            status="healthy",
            metadata={"vectors": 50000},
            position={"x": 300, "y": 200},
        ),
    ]


@pytest.fixture
def sample_connections():
    """Sample topology connections for testing."""
    return [
        ComponentConnection(
            source="frontend",
            target="orchestrator",
            type="data_flow",
            label="User queries",
            active=True,
            metadata={"throughput_qps": 12.5, "avg_latency_ms": 150},
        ),
        ComponentConnection(
            source="orchestrator",
            target="q2_fast_1",
            type="data_flow",
            label="Q2 routing",
            active=False,
            metadata={"queries_routed": 100},
        ),
    ]


@pytest.fixture
def sample_topology(sample_nodes, sample_connections):
    """Complete sample topology for testing."""
    return SystemTopology(
        nodes=sample_nodes,
        connections=sample_connections,
        last_updated=datetime(2025, 1, 15, 10, 30, 0),
        overall_health="healthy",
    )


@pytest.fixture
def sample_health_metrics():
    """Sample health metrics for testing."""
    return HealthMetrics(
        component_id="orchestrator",
        status="healthy",
        uptime_seconds=172800,
        memory_usage_mb=2048.5,
        cpu_percent=45.2,
        error_rate=0.5,
        avg_latency_ms=1850.0,
        last_check=datetime(2025, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_data_flow():
    """Sample data flow path for testing."""
    return DataFlowPath(
        query_id="550e8400-e29b-41d4-a716-446655440000",
        path=["orchestrator", "cgrag_engine", "q3_balanced_1"],
        timestamps={
            "orchestrator": "2025-01-15T10:30:00.123000",
            "cgrag_engine": "2025-01-15T10:30:00.198000",
            "q3_balanced_1": "2025-01-15T10:30:00.245000",
        },
        status="completed",
    )


# =============================================================================
# GET /api/topology/ Tests
# =============================================================================


class TestGetSystemTopology:
    """Tests for GET /api/topology/ endpoint."""

    def test_get_topology_success(self, client, sample_topology):
        """Successfully retrieve complete system topology."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        assert response.status_code == 200
        data = response.json()

        assert "nodes" in data
        assert "connections" in data
        assert "last_updated" in data
        assert "overall_health" in data

        assert len(data["nodes"]) == 3
        assert len(data["connections"]) == 2
        assert data["overall_health"] == "healthy"

    def test_get_topology_returns_all_node_fields(self, client, sample_topology):
        """Verify all node fields are returned correctly."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        data = response.json()
        orchestrator_node = next(n for n in data["nodes"] if n["id"] == "orchestrator")

        assert orchestrator_node["id"] == "orchestrator"
        assert orchestrator_node["type"] == "orchestrator"
        assert orchestrator_node["label"] == "Neural Substrate Orchestrator"
        assert orchestrator_node["status"] == "healthy"
        assert orchestrator_node["metadata"]["version"] == "5.0.0"
        assert orchestrator_node["position"]["x"] == 100

    def test_get_topology_returns_all_connection_fields(self, client, sample_topology):
        """Verify all connection fields are returned correctly."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        data = response.json()
        first_conn = data["connections"][0]

        assert first_conn["source"] == "frontend"
        assert first_conn["target"] == "orchestrator"
        assert first_conn["type"] == "data_flow"
        assert first_conn["label"] == "User queries"
        assert first_conn["active"] is True
        assert first_conn["metadata"]["throughput_qps"] == 12.5

    def test_get_topology_manager_not_initialized(self, client):
        """Return 503 when topology manager not initialized."""
        with patch(
            "app.routers.topology.get_topology_manager",
            side_effect=RuntimeError("Topology manager not initialized"),
        ):
            response = client.get("/api/topology/")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_get_topology_internal_error(self, client):
        """Return 500 on internal error."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(side_effect=Exception("Database connection failed"))

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        assert response.status_code == 500
        assert "Failed to get topology" in response.json()["detail"]

    def test_get_topology_degraded_health(self, client, sample_nodes, sample_connections):
        """Correctly return degraded overall health status."""
        degraded_topology = SystemTopology(
            nodes=sample_nodes,
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="degraded",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=degraded_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        assert response.status_code == 200
        assert response.json()["overall_health"] == "degraded"


# =============================================================================
# GET /api/topology/health/{component_id} Tests
# =============================================================================


class TestGetComponentHealth:
    """Tests for GET /api/topology/health/{component_id} endpoint."""

    def test_get_component_health_success(self, client, sample_health_metrics):
        """Successfully retrieve component health metrics."""
        mock_manager = MagicMock()
        mock_manager.get_component_health = AsyncMock(return_value=sample_health_metrics)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/health/orchestrator")

        assert response.status_code == 200
        data = response.json()

        assert data["component_id"] == "orchestrator"
        assert data["status"] == "healthy"
        assert data["uptime_seconds"] == 172800
        assert data["memory_usage_mb"] == 2048.5
        assert data["cpu_percent"] == 45.2
        assert data["error_rate"] == 0.5
        assert data["avg_latency_ms"] == 1850.0

    def test_get_component_health_not_found(self, client):
        """Return 404 when component not found."""
        mock_manager = MagicMock()
        mock_manager.get_component_health = AsyncMock(return_value=None)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/health/unknown-component")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_component_health_manager_not_initialized(self, client):
        """Return 503 when topology manager not initialized."""
        with patch(
            "app.routers.topology.get_topology_manager",
            side_effect=RuntimeError("Topology manager not initialized"),
        ):
            response = client.get("/api/topology/health/orchestrator")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_get_component_health_internal_error(self, client):
        """Return 500 on internal error."""
        mock_manager = MagicMock()
        mock_manager.get_component_health = AsyncMock(side_effect=Exception("Health check failed"))

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/health/orchestrator")

        assert response.status_code == 500
        assert "Failed to get component health" in response.json()["detail"]

    def test_get_component_health_unhealthy_status(self, client):
        """Correctly return unhealthy component status."""
        unhealthy_metrics = HealthMetrics(
            component_id="q3_balanced_1",
            status="unhealthy",
            uptime_seconds=0,
            memory_usage_mb=0,
            cpu_percent=0,
            error_rate=100.0,
            avg_latency_ms=0,
            last_check=datetime.now(timezone.utc),
        )

        mock_manager = MagicMock()
        mock_manager.get_component_health = AsyncMock(return_value=unhealthy_metrics)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/health/q3_balanced_1")

        assert response.status_code == 200
        assert response.json()["status"] == "unhealthy"
        assert response.json()["error_rate"] == 100.0

    def test_get_component_health_special_characters_in_id(self, client):
        """Handle component IDs with special characters."""
        mock_manager = MagicMock()
        mock_manager.get_component_health = AsyncMock(return_value=None)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            # URL-encoded special characters
            response = client.get("/api/topology/health/component_with-dash.and_underscore")

        assert response.status_code == 404


# =============================================================================
# GET /api/topology/dataflow/{query_id} Tests
# =============================================================================


class TestGetDataFlowPath:
    """Tests for GET /api/topology/dataflow/{query_id} endpoint."""

    def test_get_data_flow_success(self, client, sample_data_flow):
        """Successfully retrieve data flow path for query."""
        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(return_value=sample_data_flow)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/550e8400-e29b-41d4-a716-446655440000")

        assert response.status_code == 200
        data = response.json()

        assert data["query_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["path"] == ["orchestrator", "cgrag_engine", "q3_balanced_1"]
        assert data["status"] == "completed"
        assert "orchestrator" in data["timestamps"]
        assert "cgrag_engine" in data["timestamps"]
        assert "q3_balanced_1" in data["timestamps"]

    def test_get_data_flow_not_found(self, client):
        """Return 404 when query data flow not found."""
        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(return_value=None)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/unknown-query-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_data_flow_manager_not_initialized(self, client):
        """Return 503 when topology manager not initialized."""
        with patch(
            "app.routers.topology.get_topology_manager",
            side_effect=RuntimeError("Topology manager not initialized"),
        ):
            response = client.get("/api/topology/dataflow/some-query-id")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_get_data_flow_internal_error(self, client):
        """Return 500 on internal error."""
        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(
            side_effect=Exception("Data flow lookup failed")
        )

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/some-query-id")

        assert response.status_code == 500
        assert "Failed to get data flow path" in response.json()["detail"]

    def test_get_data_flow_active_status(self, client):
        """Correctly return active data flow status."""
        active_flow = DataFlowPath(
            query_id="active-query",
            path=["orchestrator", "cgrag_engine"],
            timestamps={
                "orchestrator": datetime.now(timezone.utc).isoformat(),
                "cgrag_engine": datetime.now(timezone.utc).isoformat(),
            },
            status="active",
        )

        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(return_value=active_flow)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/active-query")

        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_get_data_flow_failed_status(self, client):
        """Correctly return failed data flow status."""
        failed_flow = DataFlowPath(
            query_id="failed-query",
            path=["orchestrator"],
            timestamps={"orchestrator": datetime.now(timezone.utc).isoformat()},
            status="failed",
        )

        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(return_value=failed_flow)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/failed-query")

        assert response.status_code == 200
        assert response.json()["status"] == "failed"


# =============================================================================
# GET /api/topology/nodes Tests
# =============================================================================


class TestGetTopologyNodes:
    """Tests for GET /api/topology/nodes endpoint."""

    def test_get_nodes_success(self, client, sample_topology):
        """Successfully retrieve all topology nodes."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

        # Verify node structure
        node_ids = [n["id"] for n in data]
        assert "orchestrator" in node_ids
        assert "q2_fast_1" in node_ids
        assert "faiss_index" in node_ids

    def test_get_nodes_returns_all_fields(self, client, sample_topology):
        """Verify all node fields are present."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        data = response.json()
        node = data[0]

        assert "id" in node
        assert "type" in node
        assert "label" in node
        assert "status" in node
        assert "metadata" in node
        assert "position" in node

    def test_get_nodes_manager_not_initialized(self, client):
        """Return 503 when topology manager not initialized."""
        with patch(
            "app.routers.topology.get_topology_manager",
            side_effect=RuntimeError("Topology manager not initialized"),
        ):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_get_nodes_internal_error(self, client):
        """Return 500 on internal error."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(side_effect=Exception("Failed to load nodes"))

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 500
        assert "Failed to get topology nodes" in response.json()["detail"]

    def test_get_nodes_empty_list(self, client, sample_connections):
        """Handle topology with no nodes."""
        empty_nodes_topology = SystemTopology(
            nodes=[],
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="degraded",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=empty_nodes_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        assert response.json() == []


# =============================================================================
# GET /api/topology/connections Tests
# =============================================================================


class TestGetTopologyConnections:
    """Tests for GET /api/topology/connections endpoint."""

    def test_get_connections_success(self, client, sample_topology):
        """Successfully retrieve all topology connections."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/connections")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        # Verify connection sources/targets
        sources = [c["source"] for c in data]
        targets = [c["target"] for c in data]
        assert "frontend" in sources
        assert "orchestrator" in targets

    def test_get_connections_returns_all_fields(self, client, sample_topology):
        """Verify all connection fields are present."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/connections")

        data = response.json()
        conn = data[0]

        assert "source" in conn
        assert "target" in conn
        assert "type" in conn
        assert "label" in conn
        assert "active" in conn
        assert "metadata" in conn

    def test_get_connections_manager_not_initialized(self, client):
        """Return 503 when topology manager not initialized."""
        with patch(
            "app.routers.topology.get_topology_manager",
            side_effect=RuntimeError("Topology manager not initialized"),
        ):
            response = client.get("/api/topology/connections")

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

    def test_get_connections_internal_error(self, client):
        """Return 500 on internal error."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(side_effect=Exception("Failed to load connections"))

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/connections")

        assert response.status_code == 500
        assert "Failed to get topology connections" in response.json()["detail"]

    def test_get_connections_empty_list(self, client, sample_nodes):
        """Handle topology with no connections."""
        empty_connections_topology = SystemTopology(
            nodes=sample_nodes,
            connections=[],
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=empty_connections_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/connections")

        assert response.status_code == 200
        assert response.json() == []


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestTopologyRouterIntegration:
    """Integration-style tests for topology router."""

    def test_nodes_and_connections_consistency(self, client, sample_topology):
        """Verify nodes and connections endpoints return consistent data."""
        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            nodes_response = client.get("/api/topology/nodes")
            connections_response = client.get("/api/topology/connections")
            full_response = client.get("/api/topology/")

        # Both should succeed
        assert nodes_response.status_code == 200
        assert connections_response.status_code == 200
        assert full_response.status_code == 200

        # Data should match full topology
        full_data = full_response.json()
        assert nodes_response.json() == full_data["nodes"]
        assert connections_response.json() == full_data["connections"]

    def test_all_connection_types_handled(self, client, sample_nodes):
        """Verify all connection types are supported."""
        all_types_connections = [
            ComponentConnection(
                source="frontend",
                target="orchestrator",
                type="data_flow",
                label="Data flow connection",
                active=True,
            ),
            ComponentConnection(
                source="orchestrator",
                target="event_bus",
                type="control",
                label="Control connection",
                active=False,
            ),
            ComponentConnection(
                source="cgrag_engine",
                target="faiss_index",
                type="dependency",
                label="Dependency connection",
                active=True,
            ),
        ]

        topology = SystemTopology(
            nodes=sample_nodes,
            connections=all_types_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/connections")

        assert response.status_code == 200
        data = response.json()
        types = {c["type"] for c in data}

        assert "data_flow" in types
        assert "control" in types
        assert "dependency" in types

    def test_all_node_types_handled(self, client, sample_connections):
        """Verify all node types are supported."""
        all_types_nodes = [
            ComponentNode(
                id="orchestrator",
                type="orchestrator",
                label="Orchestrator",
                status="healthy",
                position={"x": 0, "y": 0},
            ),
            ComponentNode(
                id="q2_fast_1",
                type="model",
                label="Model Node",
                status="healthy",
                position={"x": 100, "y": 0},
            ),
            ComponentNode(
                id="event_bus",
                type="service",
                label="Service Node",
                status="healthy",
                position={"x": 200, "y": 0},
            ),
            ComponentNode(
                id="faiss_index",
                type="storage",
                label="Storage Node",
                status="healthy",
                position={"x": 300, "y": 0},
            ),
        ]

        topology = SystemTopology(
            nodes=all_types_nodes,
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        data = response.json()
        types = {n["type"] for n in data}

        assert "orchestrator" in types
        assert "model" in types
        assert "service" in types
        assert "storage" in types

    def test_all_node_statuses_handled(self, client, sample_connections):
        """Verify all node status values are supported."""
        all_status_nodes = [
            ComponentNode(
                id="node1",
                type="service",
                label="Healthy Node",
                status="healthy",
                position={"x": 0, "y": 0},
            ),
            ComponentNode(
                id="node2",
                type="service",
                label="Degraded Node",
                status="degraded",
                position={"x": 100, "y": 0},
            ),
            ComponentNode(
                id="node3",
                type="service",
                label="Unhealthy Node",
                status="unhealthy",
                position={"x": 200, "y": 0},
            ),
            ComponentNode(
                id="node4",
                type="service",
                label="Offline Node",
                status="offline",
                position={"x": 300, "y": 0},
            ),
        ]

        topology = SystemTopology(
            nodes=all_status_nodes,
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="degraded",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        data = response.json()
        statuses = {n["status"] for n in data}

        assert "healthy" in statuses
        assert "degraded" in statuses
        assert "unhealthy" in statuses
        assert "offline" in statuses


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestTopologyRouterEdgeCases:
    """Edge case tests for topology router."""

    def test_large_topology(self, client):
        """Handle topology with many nodes and connections."""
        # Create 100 nodes and 200 connections
        nodes = [
            ComponentNode(
                id=f"node_{i}",
                type="service",
                label=f"Node {i}",
                status="healthy",
                position={"x": i * 10, "y": i * 10},
            )
            for i in range(100)
        ]

        connections = [
            ComponentConnection(
                source=f"node_{i}",
                target=f"node_{(i + 1) % 100}",
                type="data_flow",
                active=True,
            )
            for i in range(200)
        ]

        large_topology = SystemTopology(
            nodes=nodes,
            connections=connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=large_topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 100
        assert len(data["connections"]) == 200

    def test_unicode_in_labels(self, client, sample_connections):
        """Handle unicode characters in labels and metadata."""
        unicode_nodes = [
            ComponentNode(
                id="japanese_node",
                type="service",
                label="日本語サービス",
                status="healthy",
                metadata={"description": "テスト説明"},
                position={"x": 0, "y": 0},
            ),
            ComponentNode(
                id="emoji_node",
                type="service",
                label="Service 🚀",
                status="healthy",
                metadata={"emoji": "🎉"},
                position={"x": 100, "y": 0},
            ),
        ]

        topology = SystemTopology(
            nodes=unicode_nodes,
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        data = response.json()

        labels = [n["label"] for n in data]
        assert "日本語サービス" in labels
        assert "Service 🚀" in labels

    def test_null_optional_fields(self, client, sample_connections):
        """Handle null values in optional fields."""
        nodes_with_nulls = [
            ComponentNode(
                id="minimal_node",
                type="service",
                label="Minimal Node",
                status="healthy",
                metadata={},  # Empty metadata
                position=None,  # No position
            ),
        ]

        topology = SystemTopology(
            nodes=nodes_with_nulls,
            connections=sample_connections,
            last_updated=datetime.now(timezone.utc),
            overall_health="healthy",
        )

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=topology)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/nodes")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["metadata"] == {}
        assert data[0]["position"] is None

    def test_data_flow_with_long_path(self, client):
        """Handle data flow with many components in path."""
        long_path = [f"component_{i}" for i in range(50)]
        timestamps = {comp: datetime.now(timezone.utc).isoformat() for comp in long_path}

        long_flow = DataFlowPath(
            query_id="long-query",
            path=long_path,
            timestamps=timestamps,
            status="completed",
        )

        mock_manager = MagicMock()
        mock_manager.get_data_flow_path = AsyncMock(return_value=long_flow)

        with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
            response = client.get("/api/topology/dataflow/long-query")

        assert response.status_code == 200
        data = response.json()
        assert len(data["path"]) == 50
        assert len(data["timestamps"]) == 50

    def test_concurrent_requests(self, client, sample_topology):
        """Handle multiple concurrent requests."""
        import concurrent.futures

        mock_manager = MagicMock()
        mock_manager.get_topology = AsyncMock(return_value=sample_topology)

        def make_request():
            with patch("app.routers.topology.get_topology_manager", return_value=mock_manager):
                return client.get("/api/topology/")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

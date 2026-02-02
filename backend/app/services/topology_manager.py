"""System topology and health management service.

This module provides the TopologyManager service that maintains the system
architecture topology, tracks component health, and records query data flow
paths for visualization in the Dashboard System Architecture Diagram.

Author: Backend Architect
Phase: 4 - Dashboard Features (Component 4)
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import psutil
import redis

from app.core.logging import get_logger
from app.models.topology import (
    ComponentConnection,
    ComponentNode,
    DataFlowPath,
    HealthMetrics,
    SystemTopology,
)
from app.services.event_bus import get_event_bus
from app.models.events import SystemEvent, EventType, EventSeverity

logger = get_logger(__name__)


class TopologyManager:
    """Manages system topology, component health, and data flow tracking.

    The TopologyManager maintains the current system architecture state,
    performs periodic health checks on all components, tracks query data
    flow paths, and emits WebSocket events for real-time UI updates.

    Attributes:
        nodes: Current system component nodes
        connections: Current system component connections
        health_metrics: Current health metrics by component_id
        data_flow_paths: Recent query data flow paths (TTL: 1 hour)
        _health_check_task: Background health check loop task
        _http_client: Async HTTP client for health checks
        _start_time: Service start timestamp for uptime calculation
    """

    def __init__(self) -> None:
        """Initialize TopologyManager with empty state."""
        self.nodes: Dict[str, ComponentNode] = {}
        self.connections: List[ComponentConnection] = []
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.data_flow_paths: Dict[str, DataFlowPath] = {}

        self._health_check_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._start_time = time.time()
        self._running = False

        # Initialize static topology structure
        self._initialize_topology()

    def _initialize_topology(self) -> None:
        """Initialize static system topology with default nodes and connections.

        Defines the S.Y.N.A.P.S.E. ENGINE architecture with all known
        components and their interconnections. Uses suggested positions
        for React Flow layout.
        """
        # Define component nodes with suggested positions
        self.nodes = {
            "frontend": ComponentNode(
                id="frontend",
                type="service",
                label="React Frontend",
                status="healthy",
                metadata={"version": "5.0.0", "framework": "React 19"},
                position={"x": 100, "y": 50},
            ),
            "orchestrator": ComponentNode(
                id="orchestrator",
                type="orchestrator",
                label="Neural Substrate Orchestrator",
                status="healthy",
                metadata={
                    "version": "5.0.0",
                    "uptime_hours": 0.0,
                    "queries_processed": 0,
                },
                position={"x": 100, "y": 200},
            ),
            "cgrag_engine": ComponentNode(
                id="cgrag_engine",
                type="service",
                label="CGRAG Engine",
                status="offline",
                metadata={"retrieval_count": 0, "cache_hit_rate": 0.0},
                position={"x": 300, "y": 200},
            ),
            "faiss_index": ComponentNode(
                id="faiss_index",
                type="storage",
                label="FAISS Vector Index",
                status="offline",
                metadata={"chunks_indexed": 0, "dimensions": 384},
                position={"x": 500, "y": 200},
            ),
            "redis_cache": ComponentNode(
                id="redis_cache",
                type="storage",
                label="Redis Cache",
                status="offline",
                metadata={"hit_rate": 0.0, "keys_count": 0},
                position={"x": 300, "y": 350},
            ),
            "event_bus": ComponentNode(
                id="event_bus",
                type="service",
                label="Event Bus",
                status="healthy",
                metadata={"connected_clients": 0, "events_sent": 0},
                position={"x": 300, "y": 50},
            ),
            # Model nodes (will be dynamically updated based on running models)
            "q2_fast_1": ComponentNode(
                id="q2_fast_1",
                type="model",
                label="Q2 FAST #1",
                status="offline",
                metadata={"tier": "Q2", "memory_usage_mb": 0.0},
                position={"x": 100, "y": 350},
            ),
            "q2_fast_2": ComponentNode(
                id="q2_fast_2",
                type="model",
                label="Q2 FAST #2",
                status="offline",
                metadata={"tier": "Q2", "memory_usage_mb": 0.0},
                position={"x": 100, "y": 450},
            ),
            "q3_balanced_1": ComponentNode(
                id="q3_balanced_1",
                type="model",
                label="Q3 BALANCED #1",
                status="offline",
                metadata={"tier": "Q3", "memory_usage_mb": 0.0},
                position={"x": 100, "y": 550},
            ),
            "q4_deep_1": ComponentNode(
                id="q4_deep_1",
                type="model",
                label="Q4 POWERFUL #1",
                status="offline",
                metadata={"tier": "Q4", "memory_usage_mb": 0.0},
                position={"x": 100, "y": 650},
            ),
        }

        # Define component connections
        self.connections = [
            ComponentConnection(
                source="frontend",
                target="orchestrator",
                type="data_flow",
                label="User queries",
                active=False,
                metadata={"throughput_qps": 0.0, "avg_latency_ms": 0.0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="cgrag_engine",
                type="control",
                label="Context retrieval",
                active=False,
                metadata={"requests_per_min": 0.0},
            ),
            ComponentConnection(
                source="cgrag_engine",
                target="faiss_index",
                type="dependency",
                label="Vector search",
                active=False,
                metadata={"search_latency_ms": 0.0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="redis_cache",
                type="dependency",
                label="Cache lookup",
                active=False,
                metadata={"hit_rate": 0.0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="q2_fast_1",
                type="data_flow",
                label="Q2 routing",
                active=False,
                metadata={"queries_routed": 0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="q2_fast_2",
                type="data_flow",
                label="Q2 routing",
                active=False,
                metadata={"queries_routed": 0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="q3_balanced_1",
                type="data_flow",
                label="Q3 routing",
                active=False,
                metadata={"queries_routed": 0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="q4_deep_1",
                type="data_flow",
                label="Q4 routing",
                active=False,
                metadata={"queries_routed": 0},
            ),
            ComponentConnection(
                source="orchestrator",
                target="event_bus",
                type="control",
                label="Status updates",
                active=True,
                metadata={"events_per_sec": 0.0},
            ),
            ComponentConnection(
                source="event_bus",
                target="frontend",
                type="data_flow",
                label="Real-time events",
                active=True,
                metadata={"websocket_connections": 0},
            ),
        ]

        logger.info(
            f"Topology initialized with {len(self.nodes)} nodes and "
            f"{len(self.connections)} connections"
        )

    async def start(self) -> None:
        """Start the topology manager and begin health checks."""
        if self._running:
            logger.warning("TopologyManager already running")
            return

        self._running = True
        self._http_client = httpx.AsyncClient(timeout=5.0)

        # Start background health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("TopologyManager started - health checks running every 10s")

    async def stop(self) -> None:
        """Stop the topology manager and cleanup resources."""
        if not self._running:
            return

        self._running = False

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()

        logger.info("TopologyManager stopped")

    async def get_topology(self) -> SystemTopology:
        """Get current system topology with health status.

        Returns:
            Complete system topology with nodes and connections
        """
        # Calculate overall health status
        health_statuses = [node.status for node in self.nodes.values()]
        if all(status == "healthy" for status in health_statuses):
            overall_health = "healthy"
        elif any(status == "unhealthy" for status in health_statuses):
            overall_health = "unhealthy"
        else:
            overall_health = "degraded"

        return SystemTopology(
            nodes=list(self.nodes.values()),
            connections=self.connections,
            last_updated=datetime.utcnow(),
            overall_health=overall_health,
        )

    async def get_component_health(self, component_id: str) -> Optional[HealthMetrics]:
        """Get health metrics for a specific component.

        Args:
            component_id: Component identifier

        Returns:
            Health metrics if available, None otherwise
        """
        return self.health_metrics.get(component_id)

    async def get_data_flow_path(self, query_id: str) -> Optional[DataFlowPath]:
        """Get data flow path for a specific query.

        Args:
            query_id: Unique query identifier

        Returns:
            Data flow path if available, None otherwise
        """
        return self.data_flow_paths.get(query_id)

    async def update_component_health(
        self, component_id: str, metrics: HealthMetrics
    ) -> None:
        """Update health metrics for a component.

        Args:
            component_id: Component identifier
            metrics: New health metrics
        """
        old_status = self.health_metrics.get(component_id)
        self.health_metrics[component_id] = metrics

        # Update node status
        if component_id in self.nodes:
            self.nodes[component_id].status = metrics.status
            self.nodes[component_id].metadata.update(
                {
                    "memory_usage_mb": metrics.memory_usage_mb,
                    "cpu_percent": metrics.cpu_percent,
                    "error_rate": metrics.error_rate,
                    "avg_latency_ms": metrics.avg_latency_ms,
                }
            )

        # Emit event if status changed
        if old_status is None or old_status.status != metrics.status:
            try:
                event_bus = get_event_bus()
                await event_bus.publish_event(
                    SystemEvent(
                        timestamp=time.time(),
                        type=EventType.MODEL_STATE,
                        message=f"Component {component_id} status changed to {metrics.status}",
                        severity=(
                            EventSeverity.ERROR
                            if metrics.status == "unhealthy"
                            else EventSeverity.WARNING
                            if metrics.status == "degraded"
                            else EventSeverity.INFO
                        ),
                        metadata={
                            "component_id": component_id,
                            "previous_status": old_status.status
                            if old_status
                            else "unknown",
                            "current_status": metrics.status,
                            "memory_usage_mb": metrics.memory_usage_mb,
                            "cpu_percent": metrics.cpu_percent,
                        },
                    )
                )
            except RuntimeError:
                # Event bus not initialized - skip
                pass

    async def record_data_flow(self, query_id: str, component_id: str) -> None:
        """Record query entering a component for data flow tracking.

        Args:
            query_id: Unique query identifier
            component_id: Component identifier
        """
        # Get or create data flow path
        if query_id not in self.data_flow_paths:
            self.data_flow_paths[query_id] = DataFlowPath(
                query_id=query_id, path=[], timestamps={}, status="active"
            )

        flow = self.data_flow_paths[query_id]

        # Add component to path if not already present
        if component_id not in flow.path:
            flow.path.append(component_id)
            flow.timestamps[component_id] = datetime.utcnow().isoformat()

            logger.debug(
                f"Recorded data flow: query {query_id} -> {component_id}",
                extra={"query_id": query_id, "component_id": component_id},
            )

        # Cleanup old paths (TTL: 1 hour, max 100 paths)
        await self._cleanup_old_data_flows()

    async def _cleanup_old_data_flows(self) -> None:
        """Remove old data flow paths beyond TTL or max count."""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        # Remove paths older than TTL
        expired_ids = []
        for query_id, flow in self.data_flow_paths.items():
            # Get oldest timestamp in path
            if flow.timestamps:
                oldest_timestamp = min(
                    datetime.fromisoformat(ts) for ts in flow.timestamps.values()
                )
                if oldest_timestamp < cutoff_time:
                    expired_ids.append(query_id)

        for query_id in expired_ids:
            del self.data_flow_paths[query_id]

        # Keep only last 100 paths
        if len(self.data_flow_paths) > 100:
            # Sort by oldest timestamp and remove oldest paths
            sorted_paths = sorted(
                self.data_flow_paths.items(),
                key=lambda item: min(
                    datetime.fromisoformat(ts) for ts in item[1].timestamps.values()
                ),
            )
            for query_id, _ in sorted_paths[:-100]:
                del self.data_flow_paths[query_id]

    async def _health_check_loop(self) -> None:
        """Background health check loop that polls component health every 10s."""
        logger.info("Health check loop started")

        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Health check loop error: {e}", exc_info=True)
                await asyncio.sleep(10)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all components."""
        # Check orchestrator (always healthy if we're running)
        orchestrator_uptime = int(time.time() - self._start_time)

        # Get actual process metrics using psutil
        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logger.warning(f"Failed to get process metrics: {e}")
            cpu_percent = 0.0
            memory_usage_mb = 0.0

        await self.update_component_health(
            "orchestrator",
            HealthMetrics(
                component_id="orchestrator",
                status="healthy",
                uptime_seconds=orchestrator_uptime,
                memory_usage_mb=round(memory_usage_mb, 2),
                cpu_percent=round(cpu_percent, 2),
                error_rate=0.0,
                avg_latency_ms=0.0,
                last_check=datetime.utcnow(),
            ),
        )

        # Check model servers via LlamaServerManager
        try:
            from app import main

            if main.server_manager is not None:
                server_manager = main.server_manager
                status_summary = server_manager.get_status_summary()

                # Update status for each tracked model server
                for server_status in status_summary.get("servers", []):
                    model_id = server_status.get("model_id", "unknown")
                    is_running = server_status.get("is_running", False)
                    is_ready = server_status.get("is_ready", False)
                    uptime = server_status.get("uptime_seconds", 0)

                    # Determine health status based on server state
                    if is_running and is_ready:
                        status = "healthy"
                    elif is_running and not is_ready:
                        status = "degraded"  # Running but not ready yet
                    else:
                        status = "offline"

                    # Create HealthMetrics for this model
                    # Note: Memory/CPU metrics would need to come from llama.cpp /health endpoint
                    # For now, we track basic availability
                    await self.update_component_health(
                        model_id,
                        HealthMetrics(
                            component_id=model_id,
                            status=status,
                            uptime_seconds=uptime,
                            memory_usage_mb=0.0,  # llama.cpp doesn't expose this yet
                            cpu_percent=0.0,  # llama.cpp doesn't expose this yet
                            error_rate=0.0,
                            avg_latency_ms=0.0,
                            last_check=datetime.utcnow(),
                        ),
                    )
        except Exception as e:
            logger.debug(f"Failed to update model health from server_manager: {e}")

        # Check CGRAG/FAISS availability
        try:
            # Use the same path function as CGRAG service for consistency
            from app.services.cgrag import get_cgrag_index_paths

            _, index_path, metadata_path = get_cgrag_index_paths("docs")

            if index_path.exists() and metadata_path.exists():
                await self.update_component_health(
                    "faiss_index",
                    HealthMetrics(
                        component_id="faiss_index",
                        status="healthy",
                        uptime_seconds=orchestrator_uptime,
                        memory_usage_mb=0.0,
                        cpu_percent=0.0,
                        error_rate=0.0,
                        avg_latency_ms=0.0,
                        last_check=datetime.utcnow(),
                    ),
                )
                await self.update_component_health(
                    "cgrag_engine",
                    HealthMetrics(
                        component_id="cgrag_engine",
                        status="healthy",
                        uptime_seconds=orchestrator_uptime,
                        memory_usage_mb=0.0,
                        cpu_percent=0.0,
                        error_rate=0.0,
                        avg_latency_ms=0.0,
                        last_check=datetime.utcnow(),
                    ),
                )
        except Exception as e:
            logger.debug(f"CGRAG health check failed: {e}")

        # Check Redis health
        try:
            redis_host = os.environ.get("MEMEX_HOST", "synapse_redis")
            redis_password = os.environ.get("MEMEX_PASSWORD")
            redis_port = int(os.environ.get("MEMEX_PORT", "6379"))

            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                socket_timeout=2.0,
            )

            if r.ping():
                # Get Redis info for metadata
                info = r.info()
                keys_count = r.dbsize()
                memory_used_mb = info.get("used_memory", 0) / (1024 * 1024)

                await self.update_component_health(
                    "redis_cache",
                    HealthMetrics(
                        component_id="redis_cache",
                        status="healthy",
                        uptime_seconds=info.get("uptime_in_seconds", 0),
                        memory_usage_mb=round(memory_used_mb, 2),
                        cpu_percent=0.0,
                        error_rate=0.0,
                        avg_latency_ms=0.0,
                        last_check=datetime.utcnow(),
                    ),
                )
                # Update metadata with keys count
                if "redis_cache" in self.nodes:
                    self.nodes["redis_cache"].metadata["keys_count"] = keys_count
            else:
                await self.update_component_health(
                    "redis_cache",
                    HealthMetrics(
                        component_id="redis_cache",
                        status="offline",
                        uptime_seconds=0,
                        memory_usage_mb=0.0,
                        cpu_percent=0.0,
                        error_rate=0.0,
                        avg_latency_ms=0.0,
                        last_check=datetime.utcnow(),
                    ),
                )
            r.close()
        except Exception as e:
            logger.debug(f"Redis health check failed: {e}")
            # Mark as offline if we can't connect
            await self.update_component_health(
                "redis_cache",
                HealthMetrics(
                    component_id="redis_cache",
                    status="offline",
                    uptime_seconds=0,
                    memory_usage_mb=0.0,
                    cpu_percent=0.0,
                    error_rate=0.0,
                    avg_latency_ms=0.0,
                    last_check=datetime.utcnow(),
                ),
            )

        # Event bus (always healthy if we're running)
        try:
            get_event_bus()
            await self.update_component_health(
                "event_bus",
                HealthMetrics(
                    component_id="event_bus",
                    status="healthy",
                    uptime_seconds=orchestrator_uptime,
                    memory_usage_mb=0.0,
                    cpu_percent=0.0,
                    error_rate=0.0,
                    avg_latency_ms=0.0,
                    last_check=datetime.utcnow(),
                ),
            )
        except RuntimeError:
            pass


# Global topology manager instance
_topology_manager: Optional[TopologyManager] = None


def init_topology_manager() -> TopologyManager:
    """Initialize the global topology manager instance.

    Returns:
        Initialized TopologyManager instance
    """
    global _topology_manager

    if _topology_manager is None:
        _topology_manager = TopologyManager()
        logger.info("TopologyManager initialized")

    return _topology_manager


def get_topology_manager() -> TopologyManager:
    """Get the global topology manager instance.

    Returns:
        TopologyManager instance

    Raises:
        RuntimeError: If topology manager not initialized
    """
    if _topology_manager is None:
        raise RuntimeError(
            "TopologyManager not initialized. Call init_topology_manager() first."
        )

    return _topology_manager

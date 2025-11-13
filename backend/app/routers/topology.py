"""System topology and health endpoints.

This module provides REST API endpoints for system architecture topology,
component health metrics, and query data flow path visualization. Used by
the Dashboard's System Architecture Diagram component.

Author: Backend Architect
Phase: 4 - Dashboard Features (Component 4)
"""

from typing import List

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.topology import (
    ComponentConnection,
    ComponentNode,
    DataFlowPath,
    HealthMetrics,
    SystemTopology
)
from app.services.topology_manager import get_topology_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/topology")


@router.get("/", response_model=SystemTopology)
async def get_system_topology() -> SystemTopology:
    """Get complete system topology with health status.

    Returns the full system architecture including all component nodes,
    connections, and current health status for visualization in the
    Dashboard System Architecture Diagram.

    Returns:
        Complete system topology with nodes and connections

    Example Response:
        ```json
        {
          "nodes": [
            {
              "id": "orchestrator",
              "type": "orchestrator",
              "label": "Neural Substrate Orchestrator",
              "status": "healthy",
              "metadata": {
                "version": "5.0.0",
                "uptime_hours": 48.5,
                "queries_processed": 1250
              },
              "position": {"x": 100, "y": 200}
            },
            {
              "id": "q2_fast_1",
              "type": "model",
              "label": "Q2 FAST #1",
              "status": "healthy",
              "metadata": {
                "tier": "Q2",
                "memory_usage_mb": 2048.5
              },
              "position": {"x": 100, "y": 350}
            }
          ],
          "connections": [
            {
              "source": "frontend",
              "target": "orchestrator",
              "type": "data_flow",
              "label": "User queries",
              "active": true,
              "metadata": {
                "throughput_qps": 12.5,
                "avg_latency_ms": 150
              }
            }
          ],
          "last_updated": "2025-11-12T10:30:00Z",
          "overall_health": "healthy"
        }
        ```
    """
    try:
        topology_manager = get_topology_manager()
        topology = await topology_manager.get_topology()
        return topology
    except RuntimeError as e:
        logger.error(f"Topology manager not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Topology manager not available"
        )
    except Exception as e:
        logger.error(f"Failed to get topology: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get topology: {str(e)}"
        )


@router.get("/health/{component_id}", response_model=HealthMetrics)
async def get_component_health(component_id: str) -> HealthMetrics:
    """Get health metrics for a specific component.

    Returns detailed health metrics including uptime, resource usage,
    error rates, and latency for a single system component.

    Args:
        component_id: Component identifier (e.g., "orchestrator", "q2_fast_1")

    Returns:
        Component health metrics

    Raises:
        HTTPException: 404 if component not found, 503 if manager unavailable

    Example Response:
        ```json
        {
          "component_id": "q2_fast_1",
          "status": "healthy",
          "uptime_seconds": 172800,
          "memory_usage_mb": 2048.5,
          "cpu_percent": 45.2,
          "error_rate": 0.5,
          "avg_latency_ms": 1850.0,
          "last_check": "2025-11-12T10:30:00Z"
        }
        ```
    """
    try:
        topology_manager = get_topology_manager()
        metrics = await topology_manager.get_component_health(component_id)

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{component_id}' not found"
            )

        return metrics
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Topology manager not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Topology manager not available"
        )
    except Exception as e:
        logger.error(
            f"Failed to get health for {component_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get component health: {str(e)}"
        )


@router.get("/dataflow/{query_id}", response_model=DataFlowPath)
async def get_data_flow_path(query_id: str) -> DataFlowPath:
    """Get data flow path for a specific query.

    Returns the ordered sequence of system components that a query
    traversed, with timestamps for each component entry. Used for
    visualizing query routing and processing flow.

    Args:
        query_id: Unique query identifier

    Returns:
        Query data flow path with timestamps

    Raises:
        HTTPException: 404 if query not found, 503 if manager unavailable

    Example Response:
        ```json
        {
          "query_id": "550e8400-e29b-41d4-a716-446655440000",
          "path": ["orchestrator", "cgrag_engine", "q3_balanced_1"],
          "timestamps": {
            "orchestrator": "2025-11-12T10:30:00.123Z",
            "cgrag_engine": "2025-11-12T10:30:00.198Z",
            "q3_balanced_1": "2025-11-12T10:30:00.245Z"
          },
          "status": "completed"
        }
        ```
    """
    try:
        topology_manager = get_topology_manager()
        flow_path = await topology_manager.get_data_flow_path(query_id)

        if flow_path is None:
            raise HTTPException(
                status_code=404,
                detail=f"Data flow path for query '{query_id}' not found"
            )

        return flow_path
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Topology manager not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Topology manager not available"
        )
    except Exception as e:
        logger.error(
            f"Failed to get data flow for {query_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data flow path: {str(e)}"
        )


@router.get("/nodes", response_model=List[ComponentNode])
async def get_topology_nodes() -> List[ComponentNode]:
    """Get all system component nodes (lighter payload than full topology).

    Returns only the component nodes without connections for scenarios
    where connection data is not needed, reducing payload size.

    Returns:
        List of all system component nodes

    Example Response:
        ```json
        [
          {
            "id": "orchestrator",
            "type": "orchestrator",
            "label": "Neural Substrate Orchestrator",
            "status": "healthy",
            "metadata": {"version": "5.0.0"},
            "position": {"x": 100, "y": 200}
          },
          {
            "id": "q2_fast_1",
            "type": "model",
            "label": "Q2 FAST #1",
            "status": "healthy",
            "metadata": {"tier": "Q2"},
            "position": {"x": 100, "y": 350}
          }
        ]
        ```
    """
    try:
        topology_manager = get_topology_manager()
        topology = await topology_manager.get_topology()
        return topology.nodes
    except RuntimeError as e:
        logger.error(f"Topology manager not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Topology manager not available"
        )
    except Exception as e:
        logger.error(f"Failed to get topology nodes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get topology nodes: {str(e)}"
        )


@router.get("/connections", response_model=List[ComponentConnection])
async def get_topology_connections() -> List[ComponentConnection]:
    """Get all system component connections (lighter payload than full topology).

    Returns only the component connections without nodes for scenarios
    where node data is not needed, reducing payload size.

    Returns:
        List of all system component connections

    Example Response:
        ```json
        [
          {
            "source": "frontend",
            "target": "orchestrator",
            "type": "data_flow",
            "label": "User queries",
            "active": true,
            "metadata": {
              "throughput_qps": 12.5,
              "avg_latency_ms": 150
            }
          },
          {
            "source": "orchestrator",
            "target": "q2_fast_1",
            "type": "data_flow",
            "label": "Q2 routing",
            "active": false,
            "metadata": {
              "queries_routed": 0
            }
          }
        ]
        ```
    """
    try:
        topology_manager = get_topology_manager()
        topology = await topology_manager.get_topology()
        return topology.connections
    except RuntimeError as e:
        logger.error(f"Topology manager not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Topology manager not available"
        )
    except Exception as e:
        logger.error(f"Failed to get topology connections: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get topology connections: {str(e)}"
        )

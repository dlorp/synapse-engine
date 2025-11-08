"""Health check endpoints per S.Y.N.A.P.S.E. SYSTEM_IDENTITY standard.

Implements standardized health check endpoints:
- /healthz: Liveness probe (fast <50ms)
- /ready: Readiness probe (checks dependencies)
- /health: Legacy endpoint (redirects to liveness)
"""

import time
from typing import Optional

from fastapi import APIRouter, Request, Response

from app.models.model import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

# Track application start time for uptime calculation
_app_start_time = time.time()


@router.get("/healthz", response_model=HealthResponse, response_model_by_alias=True)
async def liveness_probe(request: Request, response: Response) -> HealthResponse:
    """Liveness probe - fast health check (<50ms).

    This endpoint performs a minimal health check to verify the application
    is alive and responding. It does not check dependencies.

    Returns:
        HealthResponse with basic status information
    """
    # Extract trace ID from headers if present
    trace_id = request.headers.get("X-TRACE-ID") or request.headers.get("x-trace-id")

    # Set trace ID in response headers
    if trace_id:
        response.headers["X-TRACE-ID"] = trace_id

    uptime = time.time() - _app_start_time

    return HealthResponse(
        status="ok",
        uptime=uptime,
        components={"praxis": "alive"},
        trace_id=trace_id
    )


@router.get("/ready", response_model=HealthResponse, response_model_by_alias=True)
async def readiness_probe(request: Request, response: Response) -> HealthResponse:
    """Readiness probe - checks dependencies.

    This endpoint performs a comprehensive health check including:
    - Redis (MEMEX) connectivity
    - FAISS (RECALL) index availability
    - Model registry status
    - Host API (NEURAL) availability

    Returns:
        HealthResponse with component health status
    """
    # Extract trace ID from headers if present
    trace_id = request.headers.get("X-TRACE-ID") or request.headers.get("x-trace-id")

    # Set trace ID in response headers
    if trace_id:
        response.headers["X-TRACE-ID"] = trace_id

    uptime = time.time() - _app_start_time

    # Component health checks
    components = {}
    overall_status = "ok"

    # TODO: Implement actual dependency checks
    # For now, return basic status
    components["praxis"] = "ready"
    components["memex"] = "unknown"  # Redis check
    components["recall"] = "unknown"  # FAISS check
    components["neural"] = "unknown"  # Host API check

    # If any component is unhealthy, mark overall status as degraded
    if "error" in components.values():
        overall_status = "error"
    elif "degraded" in components.values() or "unknown" in components.values():
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        uptime=uptime,
        components=components,
        trace_id=trace_id
    )


@router.get("", response_model=HealthResponse, response_model_by_alias=True)
async def legacy_health(request: Request, response: Response) -> HealthResponse:
    """Legacy health endpoint - redirects to liveness probe.

    This endpoint maintains backward compatibility with existing health checks.

    Returns:
        HealthResponse from liveness probe
    """
    return await liveness_probe(request, response)

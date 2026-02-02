"""Health check endpoints per S.Y.N.A.P.S.E. SYSTEM_IDENTITY standard.

Implements standardized health check endpoints:
- /healthz: Liveness probe (fast <50ms)
- /ready: Readiness probe (checks dependencies)
- /health: Legacy endpoint (redirects to liveness)
"""

import time

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
        status="ok", uptime=uptime, components={"praxis": "alive"}, trace_id=trace_id
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

    # Check PRAXIS (FastAPI backend itself - always ready if this code is running)
    components["praxis"] = "ready"

    # Check MEMEX (Redis) connectivity
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
        redis_client.ping()
        components["memex"] = "ready"
    except Exception:
        components["memex"] = "unavailable"
        overall_status = "degraded"

    # Check RECALL (FAISS Index) availability
    try:
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        index_path = project_root / "data" / "faiss_indexes" / "docs.index"

        if index_path.exists():
            components["recall"] = "ready"
        else:
            components["recall"] = "not_indexed"
    except Exception:
        components["recall"] = "unavailable"

    # Check NEURAL (Model Servers) availability
    try:
        # Import the global server_manager from main module
        from app import main

        if main.server_manager is not None:
            status_summary = main.server_manager.get_status_summary()
            active_count = status_summary.get("running_servers", 0)

            if active_count > 0:
                components["neural"] = f"{active_count}_active"
            else:
                components["neural"] = "no_models_running"
        else:
            components["neural"] = "not_initialized"
    except Exception:
        components["neural"] = "unknown"

    # If any component is unhealthy, mark overall status as degraded
    if "error" in components.values():
        overall_status = "error"
    elif "unavailable" in components.values() or "degraded" in components.values():
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status, uptime=uptime, components=components, trace_id=trace_id
    )


@router.get("", response_model=HealthResponse, response_model_by_alias=True)
async def legacy_health(request: Request, response: Response) -> HealthResponse:
    """Legacy health endpoint - redirects to liveness probe.

    This endpoint maintains backward compatibility with existing health checks.

    Returns:
        HealthResponse from liveness probe
    """
    return await liveness_probe(request, response)

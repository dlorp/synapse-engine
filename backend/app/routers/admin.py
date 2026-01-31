"""Admin and testing endpoints for S.Y.N.A.P.S.E. ENGINE system management.

This module provides admin/testing endpoints for browser-based system operations:
- Model discovery
- System health diagnostics
- API endpoint testing
- Server management
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any
import platform
import sys
import os
import httpx
import time

from app.core.logging import get_logger
from app.models.api import ExternalServerStatusResponse, ExternalServerItem

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# Import global state from main
def get_app_state():
    """Get application state from main module.

    Returns:
        Tuple of (model_registry, server_manager, profile_manager, discovery_service)
    """
    from app.main import (
        model_registry, server_manager, profile_manager,
        discovery_service
    )
    return model_registry, server_manager, profile_manager, discovery_service


@router.post("/discover")
async def run_discovery() -> Dict[str, Any]:
    """Run model discovery and save registry.

    This endpoint scans the configured model directory for GGUF files,
    identifies models, and updates the model registry.

    Returns:
        Discovery results including:
        - message: Success message
        - models_found: Number of models discovered
        - scan_path: Directory that was scanned
        - timestamp: ISO-formatted scan timestamp

    Raises:
        HTTPException: If discovery service unavailable or discovery fails
    """
    model_registry, _, _, discovery_service = get_app_state()

    if not discovery_service:
        raise HTTPException(
            status_code=503,
            detail="Discovery service not initialized. Check server logs."
        )

    try:
        logger.info("Running model discovery from admin UI...")

        # Run discovery
        registry = discovery_service.discover_models()

        # Save registry
        registry_path = Path("data/model_registry.json")
        discovery_service.save_registry(registry, registry_path)

        # Update global state
        import app.main
        app.main.model_registry = registry

        # Also update router state for backward compatibility
        from app.routers import models as models_router
        models_router.model_registry = registry

        logger.info(
            f"Discovery complete: {len(registry.models)} models found",
            extra={
                'models_found': len(registry.models),
                'scan_path': registry.scan_path
            }
        )

        return {
            "message": "Discovery complete",
            "models_found": len(registry.models),
            "scan_path": registry.scan_path,
            "timestamp": registry.last_scan
        }

    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Discovery failed: {str(e)}"
        )


@router.get("/health/detailed")
async def get_detailed_health() -> Dict[str, Any]:
    """Get detailed system health information.

    Returns comprehensive health status of all system components including:
    - Overall system status
    - Model registry status
    - Server manager status
    - Profile manager status

    Returns:
        Health information dictionary with timestamp, status, and component details
    """
    model_registry, server_manager, profile_manager, discovery_service = get_app_state()

    health_info = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "components": {}
    }

    # Registry health
    if model_registry:
        enabled_count = len([m for m in model_registry.models.values() if m.enabled])
        health_info["components"]["registry"] = {
            "status": "healthy",
            "models_count": len(model_registry.models),
            "enabled_count": enabled_count,
            "last_scan": model_registry.last_scan
        }
    else:
        health_info["components"]["registry"] = {
            "status": "unavailable",
            "message": "No registry found. Run discovery first."
        }
        health_info["status"] = "degraded"

    # Server manager health
    if server_manager:
        status = server_manager.get_status_summary()
        all_ready = status["ready_servers"] == status["total_servers"]
        health_info["components"]["servers"] = {
            "status": "healthy" if all_ready else "degraded",
            "total": status["total_servers"],
            "ready": status["ready_servers"],
            "servers": status["servers"]
        }

        if not all_ready and health_info["status"] == "healthy":
            health_info["status"] = "degraded"
    else:
        health_info["components"]["servers"] = {
            "status": "unavailable",
            "message": "Server manager not initialized"
        }
        health_info["status"] = "degraded"

    # Profile manager health
    if profile_manager:
        profiles = profile_manager.list_profiles()
        health_info["components"]["profiles"] = {
            "status": "healthy",
            "available": profiles,
            "count": len(profiles)
        }
    else:
        health_info["components"]["profiles"] = {
            "status": "unavailable",
            "message": "Profile manager not initialized"
        }

    # Discovery service health
    if discovery_service:
        health_info["components"]["discovery"] = {
            "status": "healthy",
            "scan_path": discovery_service.scan_path
        }
    else:
        health_info["components"]["discovery"] = {
            "status": "unavailable",
            "message": "Discovery service not initialized"
        }

    logger.info(
        f"Health check completed: {health_info['status']}",
        extra={'overall_status': health_info['status']}
    )

    return health_info


@router.get("/external-servers/status", response_model=ExternalServerStatusResponse, response_model_by_alias=True)
async def check_external_servers_status() -> ExternalServerStatusResponse:
    """Check if external Metal servers are reachable.

    This endpoint checks the health of external llama-server instances
    running natively on the macOS host with Metal acceleration.

    Returns:
        ExternalServerStatusResponse with:
        - are_reachable: True if all enabled servers are online
        - use_external_servers: True if system is configured for external servers
        - servers: List of per-server status details
        - message: Human-readable status summary
        - checked_at: ISO timestamp of check
    """
    model_registry, server_manager, _, _ = get_app_state()

    # Check if external servers mode is enabled
    if not server_manager or not server_manager.use_external_servers:
        logger.debug("External servers not configured")
        return ExternalServerStatusResponse(
            are_reachable=False,
            use_external_servers=False,
            servers=[],
            message="External servers mode is not enabled. System uses Docker-internal servers.",
            checked_at=datetime.now().isoformat()
        )

    # Get all enabled models from registry
    if not model_registry:
        logger.warning("No model registry available for external server check")
        return ExternalServerStatusResponse(
            are_reachable=False,
            use_external_servers=True,
            servers=[],
            message="Model registry not initialized. Run discovery first.",
            checked_at=datetime.now().isoformat()
        )

    enabled_models = [
        model for model in model_registry.models.values()
        if model.enabled and model.port
    ]

    if not enabled_models:
        logger.info("No enabled models with assigned ports")
        return ExternalServerStatusResponse(
            are_reachable=False,
            use_external_servers=True,
            servers=[],
            message="No enabled models with assigned ports. Enable models in Model Management.",
            checked_at=datetime.now().isoformat()
        )

    # Check health of each external server
    server_items = []
    all_reachable = True
    online_count = 0

    async with httpx.AsyncClient() as client:
        for model in enabled_models:
            port = model.port
            health_url = f"http://host.docker.internal:{port}/health"

            try:
                start_time = time.time()
                response = await client.get(health_url, timeout=5.0)
                response_time_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    server_items.append(ExternalServerItem(
                        port=port,
                        status="online",
                        response_time_ms=response_time_ms,
                        error_message=None
                    ))
                    online_count += 1
                    logger.debug(f"External server on port {port} is online ({response_time_ms}ms)")
                else:
                    server_items.append(ExternalServerItem(
                        port=port,
                        status="error",
                        response_time_ms=response_time_ms,
                        error_message=f"HTTP {response.status_code}"
                    ))
                    all_reachable = False
                    logger.warning(f"External server on port {port} returned {response.status_code}")

            except httpx.TimeoutException:
                server_items.append(ExternalServerItem(
                    port=port,
                    status="offline",
                    response_time_ms=None,
                    error_message="Connection timeout (5s)"
                ))
                all_reachable = False
                logger.warning(f"External server on port {port} timed out")

            except Exception as e:
                server_items.append(ExternalServerItem(
                    port=port,
                    status="offline",
                    response_time_ms=None,
                    error_message=str(e)
                ))
                all_reachable = False
                logger.warning(f"External server on port {port} unreachable: {e}")

    # Generate human-readable message
    total_servers = len(enabled_models)
    if all_reachable:
        message = f"All {total_servers} external server{'s' if total_servers != 1 else ''} online"
    elif online_count == 0:
        message = f"All {total_servers} external server{'s' if total_servers != 1 else ''} offline. Run: ./scripts/start-host-llama-servers.sh"
    else:
        message = f"{online_count}/{total_servers} external servers online"

    logger.info(
        f"External server check completed: {online_count}/{total_servers} online",
        extra={'online_count': online_count, 'total_count': total_servers}
    )

    return ExternalServerStatusResponse(
        are_reachable=all_reachable,
        use_external_servers=True,
        servers=server_items,
        message=message,
        checked_at=datetime.now().isoformat()
    )


@router.post("/test/endpoints")
async def test_all_endpoints() -> Dict[str, Any]:
    """Test all API endpoints and return results.

    Performs health checks on all major API endpoints to verify
    system functionality.

    Returns:
        Test results including:
        - total: Total number of tests run
        - passed: Number of tests passed
        - failed: Number of tests failed
        - tests: List of individual test results
    """
    model_registry, server_manager, profile_manager, discovery_service = get_app_state()

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    # Test 1: Registry endpoint
    try:
        if model_registry:
            results["tests"].append({
                "endpoint": "GET /api/models/registry",
                "status": "passed",
                "message": f"Returned {len(model_registry.models)} models"
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "endpoint": "GET /api/models/registry",
                "status": "failed",
                "message": "Registry not initialized"
            })
            results["failed"] += 1
        results["total"] += 1
    except Exception as e:
        results["tests"].append({
            "endpoint": "GET /api/models/registry",
            "status": "failed",
            "message": str(e)
        })
        results["failed"] += 1
        results["total"] += 1

    # Test 2: Server status
    try:
        if server_manager:
            status = server_manager.get_status_summary()
            results["tests"].append({
                "endpoint": "GET /api/models/servers",
                "status": "passed",
                "message": f"{status['ready_servers']}/{status['total_servers']} servers ready"
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "endpoint": "GET /api/models/servers",
                "status": "failed",
                "message": "Server manager not initialized"
            })
            results["failed"] += 1
        results["total"] += 1
    except Exception as e:
        results["tests"].append({
            "endpoint": "GET /api/models/servers",
            "status": "failed",
            "message": str(e)
        })
        results["failed"] += 1
        results["total"] += 1

    # Test 3: Profiles
    try:
        if profile_manager:
            profiles = profile_manager.list_profiles()
            results["tests"].append({
                "endpoint": "GET /api/models/profiles",
                "status": "passed",
                "message": f"Found {len(profiles)} profiles"
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "endpoint": "GET /api/models/profiles",
                "status": "failed",
                "message": "Profile manager not initialized"
            })
            results["failed"] += 1
        results["total"] += 1
    except Exception as e:
        results["tests"].append({
            "endpoint": "GET /api/models/profiles",
            "status": "failed",
            "message": str(e)
        })
        results["failed"] += 1
        results["total"] += 1

    # Test 4: Discovery service
    try:
        if discovery_service:
            results["tests"].append({
                "endpoint": "Discovery Service",
                "status": "passed",
                "message": f"Scan path: {discovery_service.scan_path}"
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "endpoint": "Discovery Service",
                "status": "failed",
                "message": "Discovery service not initialized"
            })
            results["failed"] += 1
        results["total"] += 1
    except Exception as e:
        results["tests"].append({
            "endpoint": "Discovery Service",
            "status": "failed",
            "message": str(e)
        })
        results["failed"] += 1
        results["total"] += 1

    # Test 5: Health endpoint
    try:
        # Import httpx for internal API call
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                results["tests"].append({
                    "endpoint": "GET /health",
                    "status": "passed",
                    "message": f"Status code: {response.status_code}"
                })
                results["passed"] += 1
            else:
                results["tests"].append({
                    "endpoint": "GET /health",
                    "status": "failed",
                    "message": f"Unexpected status: {response.status_code}"
                })
                results["failed"] += 1
        results["total"] += 1
    except Exception as e:
        results["tests"].append({
            "endpoint": "GET /health",
            "status": "failed",
            "message": str(e)
        })
        results["failed"] += 1
        results["total"] += 1

    logger.info(
        f"Endpoint tests completed: {results['passed']}/{results['total']} passed",
        extra={'passed': results['passed'], 'failed': results['failed']}
    )

    return results


@router.get("/system/info")
async def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information.

    Returns:
        System information including:
        - python: Python version and platform details
        - environment: Environment variables and configuration
        - services: Initialization status of all services
    """
    model_registry, server_manager, profile_manager, discovery_service = get_app_state()

    return {
        "python": {
            "version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "environment": {
            "profile": os.getenv("PRAXIS_PROFILE", "development"),
            "scan_path": os.getenv("MODEL_SCAN_PATH", "/models"),
            "llama_server_path": os.getenv("LLAMA_SERVER_PATH", "/usr/local/bin/llama-server"),
        },
        "services": {
            "registry_initialized": model_registry is not None,
            "server_manager_initialized": server_manager is not None,
            "profile_manager_initialized": profile_manager is not None,
            "discovery_service_initialized": discovery_service is not None,
        }
    }


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get Redis cache performance statistics.

    Returns comprehensive cache metrics including hit rate, request counts,
    and cache size. Used for production monitoring and optimization.

    Returns:
        Cache statistics including:
        - hits: Total cache hits
        - misses: Total cache misses
        - sets: Total cache writes
        - total_requests: Total lookup attempts
        - hit_rate: Hit rate as formatted percentage string
        - hit_rate_percent: Raw hit rate percentage value
        - cache_size: Current number of keys in Redis
        - uptime_seconds: Time since metrics tracking started
        - timestamp: ISO timestamp of stats snapshot

    Raises:
        HTTPException: If cache metrics not initialized

    Example Response:
        {
            "hits": 245,
            "misses": 32,
            "sets": 277,
            "total_requests": 277,
            "hit_rate": "88.4%",
            "hit_rate_percent": 88.45,
            "cache_size": 156,
            "uptime_seconds": 3600.52,
            "timestamp": "2025-11-13T12:34:56.789Z"
        }
    """
    try:
        from app.services.cache_metrics import get_cache_metrics

        cache_metrics = get_cache_metrics()
        stats = await cache_metrics.get_stats()

        # Add formatted hit rate string for display
        stats["hit_rate"] = f"{stats['hit_rate_percent']:.1f}%"

        logger.info(
            f"Cache stats retrieved: {stats['hit_rate']} hit rate, "
            f"{stats['cache_size']} keys",
            extra={
                'hit_rate': stats['hit_rate_percent'],
                'cache_size': stats['cache_size']
            }
        )

        return stats

    except RuntimeError as e:
        logger.warning(f"Cache metrics not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Cache metrics service not initialized"
        )
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache stats: {str(e)}"
        )


@router.post("/cache/reset")
async def reset_cache_stats() -> Dict[str, str]:
    """Reset cache metrics counters to zero.

    Use this endpoint to reset all cache performance counters. Useful for
    testing or when starting fresh metrics collection after system changes.

    WARNING: This resets all cache hit/miss counters. Use with caution in
    production environments.

    Returns:
        Success message with timestamp

    Raises:
        HTTPException: If cache metrics not initialized or reset fails
    """
    try:
        from app.services.cache_metrics import get_cache_metrics

        cache_metrics = get_cache_metrics()
        await cache_metrics.reset()

        logger.info("Cache metrics reset via admin endpoint")

        return {
            "message": "Cache metrics reset successfully",
            "timestamp": datetime.now().isoformat()
        }

    except RuntimeError as e:
        logger.warning(f"Cache metrics not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Cache metrics service not initialized"
        )
    except Exception as e:
        logger.error(f"Failed to reset cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset cache stats: {str(e)}"
        )


@router.get("/health/monitor-status")
async def get_health_monitor_status() -> Dict[str, Any]:
    """Get health monitor service status.

    Returns current status of the health monitoring service including
    whether it's running, last known health status, and degradation info.

    Returns:
        Health monitor status including:
        - running: Whether monitor is active
        - last_status: Last known health status ("ok" or "degraded")
        - degraded_since: ISO timestamp if degraded, None otherwise
        - check_interval: Seconds between health checks

    Raises:
        HTTPException: If health monitor not initialized

    Example Response:
        {
            "running": true,
            "last_status": "ok",
            "degraded_since": null,
            "check_interval": 60
        }
    """
    try:
        from app.services.health_monitor import get_health_monitor

        health_monitor = get_health_monitor()
        status = health_monitor.get_status()

        logger.debug(f"Health monitor status: {status['last_status']}")

        return status

    except RuntimeError as e:
        logger.warning(f"Health monitor not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Health monitor service not initialized"
        )
    except Exception as e:
        logger.error(f"Failed to get health monitor status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve health monitor status: {str(e)}"
        )


@router.post("/servers/restart")
async def restart_servers() -> Dict[str, Any]:
    """Stop all servers and restart based on current profile.

    WARNING: This will stop all running model servers and restart them
    according to the current profile configuration.

    Returns:
        Restart results including:
        - message: Success message
        - total_servers: Total number of configured servers
        - ready_servers: Number of servers ready after restart

    Raises:
        HTTPException: If services not initialized or restart fails
    """
    model_registry, server_manager, profile_manager, discovery_service = get_app_state()

    if not server_manager:
        raise HTTPException(
            status_code=503,
            detail="Server manager not initialized"
        )

    try:
        logger.info("Restarting all servers from admin UI...")

        # Stop all servers
        await server_manager.stop_all()
        logger.info("All servers stopped")

        # Get enabled models from registry
        if model_registry:
            enabled = [m for m in model_registry.models.values() if m.enabled]
            logger.info(f"Restarting {len(enabled)} enabled models...")

            # Restart servers
            await server_manager.start_all(enabled)

            # Wait a moment for servers to initialize
            await asyncio.sleep(2)

            status = server_manager.get_status_summary()

            logger.info(
                f"Servers restarted: {status['ready_servers']}/{status['total_servers']} ready",
                extra={
                    'total': status['total_servers'],
                    'ready': status['ready_servers']
                }
            )

            return {
                "message": "Servers restarted",
                "total_servers": status["total_servers"],
                "ready_servers": status["ready_servers"]
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="No registry available. Run discovery first."
            )

    except Exception as e:
        logger.error(f"Server restart failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Restart failed: {str(e)}"
        )


@router.post("/servers/stop")
async def stop_servers() -> Dict[str, Any]:
    """Stop all running model servers.

    WARNING: This will stop all running model servers.
    Use /servers/restart to bring them back up.

    Returns:
        Stop results including message

    Raises:
        HTTPException: If server manager not initialized or stop fails
    """
    _, server_manager, _, _ = get_app_state()

    if not server_manager:
        raise HTTPException(
            status_code=503,
            detail="Server manager not initialized"
        )

    try:
        logger.info("Stopping all servers from admin UI...")
        await server_manager.stop_all()

        return {
            "message": "All servers stopped",
            "total_servers": 0,
            "ready_servers": 0
        }

    except Exception as e:
        logger.error(f"Server stop failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Stop failed: {str(e)}"
        )

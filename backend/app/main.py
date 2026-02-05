"""S.Y.N.A.P.S.E. CORE (PRAXIS) - FastAPI Orchestrator

Service: CORE:PRAXIS
Log Tag: prx:
Metrics: prx_*

This module initializes the FastAPI application, configures middleware,
registers routers, and sets up application lifecycle events.
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import load_config
from app.core.exceptions import SynapseException
from app.core.logging import (
    setup_logging,
    set_request_id,
    clear_request_id,
    get_logger,
    ServiceTag,
)
from app.routers import (
    health,
    models,
    query,
    admin,
    settings,
    proxy,
    events,
    orchestrator,
    metrics,
    pipeline,
    context,
    timeseries,
    topology,
    logs,
    instances,
    cgrag,
)
from app.services.llama_server_manager import LlamaServerManager
from app.services.model_discovery import ModelDiscoveryService
from app.services.profile_manager import ProfileManager
from app.services.websocket_manager import WebSocketManager
from app.services.event_bus import init_event_bus, get_event_bus
from app.services.pipeline_state import (
    init_pipeline_state_manager,
    get_pipeline_state_manager,
)
from app.services.context_state import (
    init_context_state_manager,
    get_context_state_manager,
)
from app.services.metrics_aggregator import (
    init_metrics_aggregator,
    get_metrics_aggregator,
)
from app.services.topology_manager import init_topology_manager, get_topology_manager
from app.services.cache_metrics import init_cache_metrics
from app.services.health_monitor import init_health_monitor, get_health_monitor
from app.services.log_aggregator import init_log_aggregator
from app.services.instance_manager import init_instance_manager, InstanceManager
from app.core.logging_handler import AggregatorHandler
from app.models.discovered_model import ModelRegistry

# Track application start time
_app_start_time = time.time()

# Global state - services initialized during startup
model_registry: Optional[ModelRegistry] = None
server_manager: Optional[LlamaServerManager] = None
profile_manager: Optional[ProfileManager] = None
discovery_service: Optional[ModelDiscoveryService] = None
websocket_manager: Optional[WebSocketManager] = None
instance_manager: Optional[InstanceManager] = None

# Global CGRAG retriever (preloaded at startup)
_cgrag_retriever: Optional[object] = None


def get_cgrag_retriever() -> Optional[object]:
    """Get the preloaded CGRAG retriever.

    Returns:
        CGRAG retriever instance if preloaded, None otherwise
    """
    return _cgrag_retriever


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager with full model management.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    global model_registry, server_manager, profile_manager, discovery_service
    global websocket_manager, _cgrag_retriever, instance_manager

    # Startup
    logger = get_logger(__name__)
    logger.info("prx: S.Y.N.A.P.S.E. Core (PRAXIS) starting up...")

    model_manager = None

    try:
        # Load configuration
        config = load_config()
        logger.info(
            "prx: Configuration loaded successfully",
            extra={
                "environment": config.environment,
                "model_count": len(config.models),
            },
        )

        # Setup logging with loaded configuration and service tag
        setup_logging(config.logging, service_tag=ServiceTag.PRAXIS)
        logger.info("prx: Logging configured with PRAXIS service tag")

        # Get active profile from environment
        profile_name = os.getenv("PRAXIS_PROFILE", "development")
        logger.info(f"Using profile: {profile_name}")

        # Load runtime settings (creates defaults if missing)
        from app.services import runtime_settings as settings_service

        runtime_settings_obj = await settings_service.load_runtime_settings()
        logger.info(
            f"Runtime settings loaded: GPU layers={runtime_settings_obj.n_gpu_layers}, "
            f"ctx_size={runtime_settings_obj.ctx_size}, "
            f"embedding_model={runtime_settings_obj.embedding_model_name}"
        )

        # Discovery service only - NO server launching
        discovery_service = ModelDiscoveryService(
            scan_path=config.model_management.scan_path,
            port_range=config.model_management.port_range,
        )

        # Load or create registry (cached if exists)
        registry_path = Path("data/model_registry.json")
        if registry_path.exists():
            model_registry = discovery_service.load_registry(registry_path)
            logger.info(f"✓ Loaded {len(model_registry.models)} models from registry")
        else:
            logger.info("No registry found, discovering models...")
            model_registry = discovery_service.discover_models()
            discovery_service.save_registry(model_registry, registry_path)
            logger.info(f"✓ Discovered {len(model_registry.models)} models")

        # Initialize server manager (but don't start any servers yet)
        # Check for external server mode (Metal acceleration on macOS)
        use_external_servers_env = os.getenv("USE_EXTERNAL_SERVERS", "false")
        use_external_servers = use_external_servers_env.lower() == "true"
        logger.info(
            f" DEBUG: USE_EXTERNAL_SERVERS env var = '{use_external_servers_env}'"
        )
        logger.info(f" DEBUG: use_external_servers flag = {use_external_servers}")

        # Initialize WebSocket manager for log streaming
        websocket_manager = WebSocketManager(buffer_size=500)
        logger.info("WebSocket manager initialized")

        # Initialize event bus for system event streaming
        event_bus = init_event_bus(history_size=100, max_queue_size=1000)
        await event_bus.start()
        logger.info("Event bus initialized and started")

        # Initialize pipeline state manager for query processing visualization
        pipeline_manager = init_pipeline_state_manager(
            cleanup_interval=300, ttl_seconds=3600
        )
        await pipeline_manager.start()
        logger.info("Pipeline state manager initialized and started")

        # Initialize context state manager for context window allocation tracking
        context_manager = init_context_state_manager(
            cleanup_interval=300, ttl_seconds=3600
        )
        await context_manager.start()
        logger.info("Context state manager initialized and started")

        # Initialize metrics aggregator for time-series metrics storage
        metrics_aggregator = init_metrics_aggregator()
        await metrics_aggregator.start()
        logger.info("Metrics aggregator initialized and started")

        # Configure model name resolver for metrics aggregator
        # This allows the aggregator to resolve model IDs to display names
        from app.services.metrics_aggregator import set_model_name_resolver

        def resolve_model_display_name(model_id: str) -> str:
            """Resolve model ID to display name from registry."""
            if model_registry and model_id in model_registry.models:
                return model_registry.models[model_id].get_display_name()
            return model_id

        set_model_name_resolver(resolve_model_display_name)
        logger.info("Model name resolver configured for metrics aggregator")

        # Initialize topology manager for system architecture visualization
        topology_manager = init_topology_manager()
        await topology_manager.start()
        logger.info("Topology manager initialized and started")

        # Initialize cache metrics tracker for production monitoring
        init_cache_metrics()
        logger.info("Cache metrics tracker initialized")

        # Initialize health monitor for degraded status alerts
        health_monitor = init_health_monitor(check_interval=60)
        await health_monitor.start()
        logger.info("Health monitor initialized and started (check interval: 60s)")

        # Initialize log aggregator for system-wide log collection
        log_aggregator = init_log_aggregator(max_logs=1000)
        logger.info("Log aggregator initialized (max_logs=1000)")

        # Add custom logging handler to capture all logs
        root_logger = logging.getLogger()
        aggregator_handler = AggregatorHandler(log_aggregator)
        aggregator_handler.setLevel(logging.DEBUG)  # Capture all log levels
        root_logger.addHandler(aggregator_handler)
        logger.info("Log aggregation handler installed - capturing all system logs")

        server_manager = LlamaServerManager(
            llama_server_path=config.model_management.llama_server_path,
            max_startup_time=config.model_management.max_startup_time,
            readiness_check_interval=config.model_management.readiness_check_interval,
            use_external_servers=use_external_servers,
            websocket_manager=websocket_manager,
        )

        # Profile manager (still needed for future profile management)
        project_root = Path(__file__).parent.parent.parent
        profiles_dir = project_root / "config" / "profiles"
        profile_manager = ProfileManager(profiles_dir=profiles_dir)

        # Initialize instance manager for multi-instance support
        instance_registry_path = Path("data/instance_registry.json")
        instance_manager = init_instance_manager(
            registry_path=instance_registry_path,
            model_registry=model_registry,
            server_manager=server_manager,
        )
        logger.info(
            f"Instance manager initialized with {len(instance_manager.registry.instances)} instances"
        )

        # Expose services globally for routers
        from app.routers import models as models_router
        from app.routers import query as query_router
        from app.routers import proxy as proxy_router
        from app.routers import instances as instances_router
        from app.services.model_selector import ModelSelector

        models_router.model_registry = model_registry
        models_router.server_manager = server_manager
        models_router.profile_manager = profile_manager
        models_router.discovery_service = discovery_service

        # Expose instance manager to instances router
        instances_router.instance_manager = instance_manager

        # Expose model_registry to query router for council mode
        query_router.model_registry = model_registry

        # Initialize and expose model selector for query routing
        model_selector = ModelSelector(
            registry=model_registry, server_manager=server_manager
        )
        query_router.model_selector = model_selector
        app.state.model_selector = model_selector
        logger.info("ModelSelector initialized for query routing")

        # Expose server_manager to proxy router for reverse proxy
        proxy_router.server_manager = server_manager

        logger.info("✓ PRAXIS ready - NO models loaded (awaiting WebUI commands)")

        # Initialize ModelManager (for existing /status endpoint compatibility)
        from app.services.models import ModelManager

        model_manager = ModelManager(config.models)
        app.state.model_manager = model_manager

        # Start ModelManager (begins health checking for legacy models)
        await model_manager.start()
        logger.info("ModelManager started (legacy health checking)")

        # Preload CGRAG index (optional - improves first-query performance)
        try:
            project_root = Path(__file__).parent.parent.parent
            index_path = project_root / "data" / "faiss_indexes" / "docs.index"
            metadata_path = project_root / "data" / "faiss_indexes" / "docs.metadata"

            # Only preload if index exists
            if index_path.exists() and metadata_path.exists():
                logger.info("Preloading CGRAG index...")

                from app.services.cgrag import CGRAGIndexer, CGRAGRetriever

                # Load index in background to avoid blocking startup
                cgrag_indexer = CGRAGIndexer.load_index(
                    index_path=index_path, metadata_path=metadata_path
                )

                # Create retriever
                _cgrag_retriever = CGRAGRetriever(
                    indexer=cgrag_indexer,
                    min_relevance=config.cgrag.retrieval.min_relevance,
                )

                # Store in app state for router access
                app.state.cgrag_retriever = _cgrag_retriever

                logger.info(
                    f"CGRAG index preloaded successfully ({len(cgrag_indexer.chunks)} chunks)",
                    extra={"chunks": len(cgrag_indexer.chunks)},
                )
            else:
                logger.info(
                    "CGRAG index not found - skipping preload. Index will load on-demand.",
                    extra={"index_path": str(index_path)},
                )
        except Exception as e:
            logger.warning(
                f"Failed to preload CGRAG index: {e}. Index will load on-demand.",
                extra={"error": str(e)},
            )

        logger.info(
            f"S.Y.N.A.P.S.E. Core (PRAXIS) started successfully on {config.host}:{config.port}",
            extra={
                "app_name": config.app_name,
                "version": config.version,
                "environment": config.environment,
            },
        )

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise

    # Application is running
    yield

    # Shutdown
    logger.info("S.Y.N.A.P.S.E. Core (PRAXIS) shutting down...")

    # Stop health monitor
    try:
        health_monitor = get_health_monitor()
        await health_monitor.stop()
        logger.info("Health monitor stopped")
    except Exception as e:
        logger.warning(f"Error stopping health monitor: {e}")

    # Stop topology manager
    try:
        topology_manager = get_topology_manager()
        await topology_manager.stop()
        logger.info("Topology manager stopped")
    except Exception as e:
        logger.warning(f"Error stopping topology manager: {e}")

    # Stop metrics aggregator
    try:
        metrics_aggregator = get_metrics_aggregator()
        await metrics_aggregator.stop()
        logger.info("Metrics aggregator stopped")
    except Exception as e:
        logger.warning(f"Error stopping metrics aggregator: {e}")

    # Stop context state manager
    try:
        context_manager = get_context_state_manager()
        await context_manager.stop()
        logger.info("Context state manager stopped")
    except Exception as e:
        logger.warning(f"Error stopping context state manager: {e}")

    # Stop pipeline state manager
    try:
        pipeline_manager = get_pipeline_state_manager()
        await pipeline_manager.stop()
        logger.info("Pipeline state manager stopped")
    except Exception as e:
        logger.warning(f"Error stopping pipeline state manager: {e}")

    # Stop event bus
    try:
        event_bus = get_event_bus()
        await event_bus.stop()
        logger.info("Event bus stopped")
    except Exception as e:
        logger.warning(f"Error stopping event bus: {e}")

    # Shutdown PRAXIS model management - stop all running servers
    if server_manager:
        await server_manager.stop_all()
        logger.info("All model servers stopped")

    # Stop ModelManager (legacy)
    if model_manager:
        await model_manager.stop()
        logger.info("ModelManager stopped")

    uptime = time.time() - _app_start_time
    logger.info(
        f"S.Y.N.A.P.S.E. Core (PRAXIS) stopped after {uptime:.2f} seconds",
        extra={"uptime_seconds": uptime},
    )


# Create FastAPI application
app = FastAPI(
    title="S.Y.N.A.P.S.E. ENGINE Multi-Model Orchestration Backend",
    description="Backend API for orchestrating multiple LLM instances with intelligent routing",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    # Serialize all response models using camelCase aliases
    response_model_by_alias=True,
)

# Configure CORS middleware (will use default origins, updated in lifespan)
# Default to common development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:  # type: ignore
    """Add request ID to all requests for tracing.

    Args:
        request: Incoming request
        call_next: Next middleware/handler in chain

    Returns:
        Response with X-Request-ID header
    """
    # Get or generate request ID
    request_id = request.headers.get("X-Request-ID")
    request_id = set_request_id(request_id)

    try:
        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
    finally:
        # Clean up request context
        clear_request_id()


# Performance logging middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next) -> Response:  # type: ignore
    """Log request performance metrics.

    Args:
        request: Incoming request
        call_next: Next middleware/handler in chain

    Returns:
        Response
    """
    start_time = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate elapsed time
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Log performance
    logger = get_logger(__name__)
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed_ms, 2),
        },
    )

    # Add performance header
    response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

    return response


# Exception handlers
@app.exception_handler(SynapseException)
async def synapse_exception_handler(
    request: Request, exc: SynapseException
) -> JSONResponse:
    """Handle S.Y.N.A.P.S.E. CORE-specific exceptions.

    Args:
        request: Request that caused the exception
        exc: Synapse exception

    Returns:
        JSON error response
    """
    logger = get_logger(__name__)
    logger.error(
        f"prx: Synapse exception: {exc.message}",
        extra={
            "exception": exc.__class__.__name__,
            "details": exc.details,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: Request that caused the exception
        exc: Exception

    Returns:
        JSON error response
    """
    logger = get_logger(__name__)
    logger.error(
        f"Unexpected exception: {exc}",
        extra={"exception": exc.__class__.__name__},
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(models.router, tags=["models"])
app.include_router(query.router, tags=["queries"])
app.include_router(admin.router, tags=["admin"])
app.include_router(settings.router, tags=["settings"])
app.include_router(proxy.router, tags=["proxy"])
app.include_router(events.router, tags=["events"])
app.include_router(orchestrator.router, tags=["orchestrator"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(pipeline.router, tags=["pipeline"])
app.include_router(context.router, tags=["context"])
app.include_router(timeseries.router, tags=["timeseries"])
app.include_router(topology.router, tags=["topology"])
app.include_router(logs.router, tags=["logs"])
app.include_router(instances.router, tags=["instances"])
app.include_router(cgrag.router, tags=["cgrag"])


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        API information
    """
    return {
        "name": "S.Y.N.A.P.S.E. ENGINE Multi-Model Orchestration Backend",
        "version": "4.0.0",
        "docs": "/api/docs",
        "status": "operational",
    }


# WebSocket endpoint for real-time log streaming
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, model_id: Optional[str] = None) -> None:
    """WebSocket endpoint for real-time log streaming from llama-server processes.

    Streams stderr output from llama-server subprocesses to connected clients
    in real-time. Supports filtering by model_id. Sends buffered historical
    logs on connection, then streams new logs as they arrive.

    Query Parameters:
        model_id: Optional filter for specific model logs. If not provided,
            streams logs from all models.

    WebSocket Message Format:
        {
            "timestamp": "2025-11-05T09:30:00Z",
            "model_id": "deepseek_r1_8b_q4km",
            "port": 8080,
            "level": "INFO" | "WARN" | "ERROR",
            "message": "log line text"
        }

    Example Client Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/logs?model_id=deepseek_r1_8b_q4km');
        ws.onmessage = (event) => {
            const logEntry = JSON.parse(event.data);
            console.log(`[${logEntry.level}] ${logEntry.message}`);
        };

    Connection Lifecycle:
        1. Client connects via WebSocket handshake
        2. Server sends buffered historical logs (up to 500 lines per model)
        3. Server streams new logs in real-time as they arrive
        4. Connection stays open until client disconnects or error occurs

    Args:
        websocket: WebSocket connection instance
        model_id: Optional model ID filter for logs
    """
    logger = get_logger(__name__)

    if not websocket_manager:
        logger.error("WebSocket manager not initialized")
        await websocket.close(code=1011, reason="WebSocket manager not initialized")
        return

    # Accept connection
    await websocket_manager.connect(websocket)

    try:
        # Send buffered logs on connect
        buffered_logs = websocket_manager.get_logs(model_id)
        logger.info(
            f"Sending {len(buffered_logs)} buffered logs to new WebSocket client "
            f"(model_id filter: {model_id or 'none'})"
        )

        for log in buffered_logs:
            # Apply model_id filter if specified
            if model_id is None or log.get("model_id") == model_id:
                await websocket.send_json(log)

        # Keep connection alive and handle client messages (ping/pong, filter changes)
        while True:
            try:
                # Receive any client messages (with timeout to allow for broadcasts)
                # This keeps the connection alive and allows the server to detect disconnects
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client commands (currently just keep-alive, can extend later)
                # Future: could support commands like {"action": "filter", "model_id": "..."}
                logger.debug(f"Received WebSocket message: {data}")

            except asyncio.TimeoutError:
                # No message received - send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    # Connection lost
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        # Clean up connection
        await websocket_manager.disconnect(websocket)

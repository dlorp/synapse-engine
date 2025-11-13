"""Main FastAPI application for MAGI Multi-Model Orchestration Backend.

This module initializes the FastAPI application, configures middleware,
registers routers, and sets up application lifecycle events.
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import load_config, get_config
from app.core.exceptions import MAGIException
from app.core.logging import setup_logging, set_request_id, clear_request_id, get_logger
from app.routers import health, models, query

# Track application start time
_app_start_time = time.time()

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
    """Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger = get_logger(__name__)
    logger.info("MAGI Backend starting up...")

    model_manager = None

    try:
        # Load configuration
        config = load_config()
        logger.info(
            f"Configuration loaded successfully",
            extra={
                'environment': config.environment,
                'model_count': len(config.models)
            }
        )

        # Setup logging with loaded configuration
        setup_logging(config.logging)
        logger.info("Logging configured")

        # Initialize ModelManager
        from app.services.models import ModelManager

        model_manager = ModelManager(config.models)
        app.state.model_manager = model_manager

        # Start ModelManager (begins health checking)
        await model_manager.start()
        logger.info("ModelManager started and health checking initialized")

        # Preload CGRAG index (optional - improves first-query performance)
        global _cgrag_retriever
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
                    index_path=index_path,
                    metadata_path=metadata_path
                )

                # Create retriever
                _cgrag_retriever = CGRAGRetriever(
                    indexer=cgrag_indexer,
                    min_relevance=config.cgrag.retrieval.min_relevance
                )

                # Store in app state for router access
                app.state.cgrag_retriever = _cgrag_retriever

                logger.info(
                    f"CGRAG index preloaded successfully ({len(cgrag_indexer.chunks)} chunks)",
                    extra={'chunks': len(cgrag_indexer.chunks)}
                )
            else:
                logger.info(
                    "CGRAG index not found - skipping preload. Index will load on-demand.",
                    extra={'index_path': str(index_path)}
                )
        except Exception as e:
            logger.warning(
                f"Failed to preload CGRAG index: {e}. Index will load on-demand.",
                extra={'error': str(e)}
            )

        logger.info(
            f"MAGI Backend started successfully on {config.host}:{config.port}",
            extra={
                'app_name': config.app_name,
                'version': config.version,
                'environment': config.environment
            }
        )

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise

    # Application is running
    yield

    # Shutdown
    logger.info("MAGI Backend shutting down...")

    # Stop ModelManager
    if model_manager:
        await model_manager.stop()
        logger.info("ModelManager stopped")

    uptime = time.time() - _app_start_time
    logger.info(
        f"MAGI Backend stopped after {uptime:.2f} seconds",
        extra={'uptime_seconds': uptime}
    )


# Create FastAPI application
app = FastAPI(
    title="MAGI Multi-Model Orchestration Backend",
    description="Backend API for orchestrating multiple LLM instances with intelligent routing",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    # Serialize all response models using camelCase aliases
    response_model_by_alias=True
)

# Configure CORS middleware (will use default origins, updated in lifespan)
# Default to common development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
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
    request_id = request.headers.get('X-Request-ID')
    request_id = set_request_id(request_id)

    try:
        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id

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
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'elapsed_ms': round(elapsed_ms, 2)
        }
    )

    # Add performance header
    response.headers['X-Response-Time'] = f"{elapsed_ms:.2f}ms"

    return response


# Exception handlers
@app.exception_handler(MAGIException)
async def magi_exception_handler(request: Request, exc: MAGIException) -> JSONResponse:
    """Handle MAGI-specific exceptions.

    Args:
        request: Request that caused the exception
        exc: MAGI exception

    Returns:
        JSON error response
    """
    logger = get_logger(__name__)
    logger.error(
        f"MAGI exception: {exc.message}",
        extra={
            'exception': exc.__class__.__name__,
            'details': exc.details,
            'status_code': exc.status_code
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


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
        extra={'exception': exc.__class__.__name__},
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            'error': 'InternalServerError',
            'message': 'An unexpected error occurred',
            'details': {}
        }
    )


# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(models.router, tags=["models"])
app.include_router(query.router, tags=["queries"])


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        API information
    """
    return {
        'name': 'MAGI Multi-Model Orchestration Backend',
        'version': '0.1.0',
        'docs': '/api/docs',
        'status': 'operational'
    }

"""Reverse proxy endpoints for llama.cpp model servers.

Provides secure access to model servers by proxying requests through
the backend API. Model servers bind to localhost and are not directly
accessible from outside the Docker container.

Security Features:
- Model servers bound to 127.0.0.1 (localhost only)
- All external access goes through authenticated backend API
- Request/response validation and logging
- Centralized error handling and rate limiting (future)

Usage:
    POST /api/proxy/{model_id}/v1/chat/completions - Chat completions
    POST /api/proxy/{model_id}/v1/completions - Text completions
    GET /api/proxy/{model_id}/health - Health check

Author: Backend Architect
Phase: 5 - Security Hardening
"""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/proxy", tags=["proxy"])

# Global server manager (set by main.py)
from app.services.llama_server_manager import LlamaServerManager
server_manager: Optional[LlamaServerManager] = None


@router.post("/{model_id}/v1/chat/completions")
async def proxy_chat_completions(
    model_id: str,
    request: Request
) -> Response:
    """Proxy chat completion requests to the model server.

    Provides secure access to llama-server chat completions endpoint by
    proxying requests through the backend. Model servers are bound to
    localhost and not directly accessible from outside the container.

    Args:
        model_id: Model ID from registry (e.g., "deepseek_r1_8b_q4km")
        request: FastAPI request object containing JSON body

    Returns:
        Proxied response from llama-server with same format and status code

    Raises:
        HTTPException:
            - 503 if server manager not initialized or server not running
            - 404 if model_id not found in registry
            - 502 if connection to model server fails

    Example:
        POST /api/proxy/deepseek_r1_8b_q4km/v1/chat/completions
        {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
    """
    if not server_manager:
        logger.error("Proxy request failed - server manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server manager not initialized"
        )

    # Check if server is running
    if not server_manager.is_server_running(model_id):
        logger.warning(
            f"Proxy request failed - server not running for {model_id}",
            extra={"model_id": model_id}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model server {model_id} is not running. Start it first via /api/models/servers/{model_id}/start"
        )

    # Get server info
    server = server_manager.servers.get(model_id)
    if not server:
        logger.error(
            f"Proxy request failed - server not found: {model_id}",
            extra={"model_id": model_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {model_id} not found in registry"
        )

    port = server.port
    target_url = f"http://127.0.0.1:{port}/v1/chat/completions"

    logger.info(
        f"Proxying chat completions request to {model_id}",
        extra={
            "model_id": model_id,
            "port": port,
            "target_url": target_url
        }
    )

    # Get request body
    body = await request.body()

    # Proxy the request with extended timeout for LLM inference
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                target_url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            logger.info(
                f"Proxy response from {model_id}: {response.status_code}",
                extra={
                    "model_id": model_id,
                    "status_code": response.status_code,
                    "response_size": len(response.content)
                }
            )

            # Return proxied response with original status code and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )

        except httpx.RequestError as e:
            logger.error(
                f"Proxy request failed for {model_id}: {e}",
                extra={
                    "model_id": model_id,
                    "error": str(e),
                    "target_url": target_url
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to model server: {str(e)}"
            )


@router.post("/{model_id}/v1/completions")
async def proxy_completions(
    model_id: str,
    request: Request
) -> Response:
    """Proxy completion requests to the model server.

    Provides secure access to llama-server completions endpoint by
    proxying requests through the backend. Model servers are bound to
    localhost and not directly accessible from outside the container.

    Args:
        model_id: Model ID from registry (e.g., "deepseek_r1_8b_q4km")
        request: FastAPI request object containing JSON body

    Returns:
        Proxied response from llama-server with same format and status code

    Raises:
        HTTPException:
            - 503 if server manager not initialized or server not running
            - 404 if model_id not found in registry
            - 502 if connection to model server fails

    Example:
        POST /api/proxy/deepseek_r1_8b_q4km/v1/completions
        {
            "prompt": "Once upon a time",
            "temperature": 0.7,
            "max_tokens": 100
        }
    """
    if not server_manager:
        logger.error("Proxy request failed - server manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server manager not initialized"
        )

    if not server_manager.is_server_running(model_id):
        logger.warning(
            f"Proxy request failed - server not running for {model_id}",
            extra={"model_id": model_id}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model server {model_id} is not running. Start it first via /api/models/servers/{model_id}/start"
        )

    server = server_manager.servers.get(model_id)
    if not server:
        logger.error(
            f"Proxy request failed - server not found: {model_id}",
            extra={"model_id": model_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {model_id} not found in registry"
        )

    port = server.port
    target_url = f"http://127.0.0.1:{port}/v1/completions"

    logger.info(
        f"Proxying completions request to {model_id}",
        extra={
            "model_id": model_id,
            "port": port,
            "target_url": target_url
        }
    )

    body = await request.body()

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                target_url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            logger.info(
                f"Proxy response from {model_id}: {response.status_code}",
                extra={
                    "model_id": model_id,
                    "status_code": response.status_code,
                    "response_size": len(response.content)
                }
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )

        except httpx.RequestError as e:
            logger.error(
                f"Proxy request failed for {model_id}: {e}",
                extra={
                    "model_id": model_id,
                    "error": str(e),
                    "target_url": target_url
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to model server: {str(e)}"
            )


@router.get("/{model_id}/health")
async def proxy_health_check(model_id: str) -> Response:
    """Proxy health check to model server.

    Checks if a model server is running and healthy by proxying the
    health check request. Returns appropriate status codes based on
    server availability.

    Args:
        model_id: Model ID from registry

    Returns:
        Proxied health check response with status:
            - 200 if server is healthy
            - 503 if server is not running or unreachable
            - 404 if model_id not found in registry

    Example:
        GET /api/proxy/deepseek_r1_8b_q4km/health

        Response (healthy):
        {
            "status": "ok",
            "model_loaded": true,
            "slots_available": 1
        }

        Response (not running):
        {
            "status": "not_running"
        }
    """
    if not server_manager:
        logger.error("Proxy health check failed - server manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server manager not initialized"
        )

    # Check if server is tracked
    if not server_manager.is_server_running(model_id):
        logger.debug(
            f"Health check - server not running: {model_id}",
            extra={"model_id": model_id}
        )
        return Response(
            content='{"status": "not_running"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )

    server = server_manager.servers.get(model_id)
    if not server:
        logger.error(
            f"Health check failed - server not found: {model_id}",
            extra={"model_id": model_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {model_id} not found in registry"
        )

    port = server.port
    target_url = f"http://127.0.0.1:{port}/health"

    # Use shorter timeout for health checks
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(target_url)

            logger.debug(
                f"Health check response from {model_id}: {response.status_code}",
                extra={
                    "model_id": model_id,
                    "status_code": response.status_code
                }
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )

        except httpx.RequestError as e:
            logger.warning(
                f"Health check failed for {model_id}: {e}",
                extra={
                    "model_id": model_id,
                    "error": str(e),
                    "target_url": target_url
                }
            )
            return Response(
                content='{"status": "unreachable"}',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                media_type="application/json"
            )

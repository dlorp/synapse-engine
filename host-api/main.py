"""NODE:NEURAL - Host API for Metal Server Orchestration

Manages native Metal-accelerated llama-server processes on macOS host.
Executes SSH commands via secure wrapper to start/stop servers with
GPU acceleration. Provides health checks and process supervision.

Service: NODE:NEURAL
Log Tag: nrl:
Metrics: nrl_*
"""

import asyncio
import subprocess
import signal
import sys
import time
import logging
from fastapi import FastAPI, HTTPException
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="S.Y.N.A.P.S.E. NEURAL Orchestrator",
    description="Metal-accelerated model server management",
    version="4.0.0"
)

# Track application start time for uptime calculation
startup_time = time.time()

# Track if servers are running
servers_running = False


@app.get("/healthz")
async def liveness():
    """Liveness probe for NEURAL orchestrator.

    Fast health check (<50ms) to verify the service is alive and responding.
    Does not check external dependencies.

    Returns:
        Health status with uptime and component state
    """
    return {
        "status": "ok",
        "uptime": time.time() - startup_time,
        "components": {"neural": "alive"}
    }


@app.get("/ready")
async def readiness():
    """Readiness probe - checks SSH connectivity.

    Comprehensive health check that verifies:
    - SSH connection to mac-host
    - Ability to execute remote commands

    Returns:
        Health status with component readiness information
    """
    components = {}

    # Test SSH connection
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=2", "mac-host", "echo", "ready"],
            capture_output=True,
            timeout=3
        )
        components["ssh"] = "connected" if result.returncode == 0 else "disconnected"
    except Exception as e:
        logger.error(f"nrl: SSH health check failed: {e}")
        components["ssh"] = "error"

    status = "ok" if components["ssh"] == "connected" else "degraded"

    return {
        "status": status,
        "uptime": time.time() - startup_time,
        "components": components
    }


@app.get("/")
async def root():
    """Legacy root endpoint - redirects to liveness probe."""
    return await liveness()


@app.post("/api/servers/start")
async def start_servers():
    """
    Start Metal-accelerated llama-servers on Mac host.

    Executes the start-host-llama-servers.sh script which launches
    native macOS llama-server binaries with Metal GPU acceleration.
    """
    global servers_running

    logger.info("nrl: Received request to start Metal servers")

    try:
        # Execute the start script on Mac host via SSH
        result = subprocess.run(
            ["ssh", "mac-host", "start-metal-servers"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            servers_running = True
            logger.info("nrl: Metal servers started successfully")
            logger.info(f"nrl: Script output: {result.stdout}")
            return {
                "status": "started",
                "message": "Metal-accelerated llama-servers launched on host",
                "output": result.stdout
            }
        else:
            logger.error(f"nrl: Failed to start servers: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start servers: {result.stderr}"
            )

    except subprocess.TimeoutExpired:
        logger.error("nrl: Script execution timed out after 30s")
        raise HTTPException(
            status_code=500,
            detail="Script execution timed out"
        )
    except Exception as e:
        logger.error(f"nrl: Error starting servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/servers/stop")
async def stop_servers():
    """
    Stop Metal-accelerated llama-servers on Mac host.

    Executes the stop-host-llama-servers.sh script which gracefully
    shuts down all running llama-server processes.
    """
    global servers_running

    logger.info("nrl: Received request to stop Metal servers")

    try:
        result = subprocess.run(
            ["ssh", "mac-host", "stop-metal-servers"],
            capture_output=True,
            text=True,
            timeout=30
        )

        servers_running = False
        logger.info("nrl: Metal servers stopped successfully")
        logger.info(f"nrl: Script output: {result.stdout}")

        return {
            "status": "stopped",
            "message": "Metal-accelerated llama-servers shut down",
            "output": result.stdout
        }

    except subprocess.TimeoutExpired:
        logger.error("nrl: Script execution timed out after 30s")
        raise HTTPException(
            status_code=500,
            detail="Script execution timed out"
        )
    except Exception as e:
        logger.error(f"nrl: Error stopping servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/servers/status")
async def server_status():
    """
    Check if Metal servers are running.

    Returns the current running state as tracked by this service.
    Note: This is a simple state flag, not a health check of actual processes.
    """
    return {
        "running": servers_running,
        "message": "Servers running" if servers_running else "Servers stopped"
    }


def shutdown_handler(signum, frame):
    """
    Graceful shutdown handler.

    When Docker sends SIGTERM (during docker-compose down), this handler:
    1. Logs the shutdown event
    2. Calls stop-host-llama-servers.sh to shut down Metal servers
    3. Exits cleanly

    This ensures Metal servers are always stopped when S.Y.N.A.P.S.E. ENGINE shuts down.
    """
    logger.info("nrl: Host API received shutdown signal (SIGTERM)")
    logger.info("nrl: Stopping Metal servers before exit...")

    try:
        result = subprocess.run(
            ["ssh", "mac-host", "stop-metal-servers"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info("nrl: Metal servers stopped successfully")
            logger.info(f"nrl: Script output: {result.stdout}")
        else:
            logger.warning(f"nrl: Stop script exited with code {result.returncode}")
            logger.warning(f"nrl: stderr: {result.stderr}")

    except Exception as e:
        logger.error(f"nrl: Error stopping servers during shutdown: {e}")

    logger.info("nrl: Host API shutting down")
    sys.exit(0)


# Register shutdown handlers for graceful cleanup
signal.signal(signal.SIGTERM, shutdown_handler)  # Docker sends SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C sends SIGINT


if __name__ == "__main__":
    logger.info("nrl: S.Y.N.A.P.S.E. Host API (NEURAL) starting...")
    logger.info("nrl: Scripts directory mounted at: /scripts")
    logger.info("nrl: API accessible at: http://host-api:9090")
    logger.info("nrl: Health endpoints: /healthz (liveness), /ready (readiness)")

    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9090,
        log_level="info"
    )

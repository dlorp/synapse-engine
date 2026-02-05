"""
Llama.cpp Server Manager for S.Y.N.A.P.S.E. ENGINE Multi-Model Orchestration System.

This module manages the lifecycle of llama.cpp server processes, including:
- Selective server launching based on enabled models
- Concurrent startup with readiness detection
- Graceful shutdown with fallback to force-kill
- Process monitoring and status reporting
- Docker-compatible configuration

Author: Backend Architect
Phase: 4 - Selective Server Launcher
"""

import asyncio
import logging
import subprocess
import threading
import httpx
import os
from pathlib import Path
from typing import Dict, Optional, List, TYPE_CHECKING
from datetime import datetime

from app.models.discovered_model import DiscoveredModel
from app.core.exceptions import SynapseException
from app.services import runtime_settings as settings_service
from app.services.event_emitter import emit_model_state_event, emit_error_event

# Avoid circular import at runtime
if TYPE_CHECKING:
    from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class ServerProcess:
    """Wrapper for a llama.cpp server process.

    Encapsulates a running llama-server subprocess with metadata about
    the model it's serving, uptime tracking, and readiness status.

    Supports both managed subprocesses and external servers (for Metal).
    """

    def __init__(
        self,
        model: DiscoveredModel,
        process: Optional[subprocess.Popen] = None,
        is_external: bool = False,
    ):
        """Initialize server process wrapper.

        Args:
            model: The DiscoveredModel this server is running
            process: The subprocess.Popen instance (None for external servers)
            is_external: True if server is externally managed (not a subprocess)
        """
        self.model = model
        self.process = process
        self.port = model.port
        self.start_time = datetime.now()
        self.is_ready = False
        self.is_external = is_external
        self.pid = process.pid if process else None

    def is_running(self) -> bool:
        """Check if the underlying process is still alive.

        For external servers, always returns True (assumes host manages lifecycle).

        Returns:
            True if process is running, False if terminated
        """
        if self.is_external:
            return True  # External servers managed by host
        return self.process is not None and self.process.poll() is None

    def get_uptime_seconds(self) -> int:
        """Calculate server uptime in seconds.

        Returns:
            Integer seconds since server was started
        """
        return int((datetime.now() - self.start_time).total_seconds())

    def get_status(self) -> dict:
        """Get comprehensive status information for this server.

        Returns:
            Dictionary containing:
                - model_id: Unique model identifier
                - display_name: Human-readable model name
                - port: HTTP port server is listening on
                - pid: Process ID
                - is_ready: Whether server has completed initialization
                - is_running: Whether process is alive
                - uptime_seconds: Time since startup
                - tier: Model tier (fast, balanced, or powerful)
                - is_thinking: Whether this is a thinking-enabled model
        """
        return {
            "model_id": self.model.model_id,
            "display_name": self.model.get_display_name(),
            "port": self.port,
            "pid": self.pid,
            "is_ready": self.is_ready,
            "is_running": self.is_running(),
            "uptime_seconds": self.get_uptime_seconds(),
            "tier": str(self.model.get_effective_tier()),
            "is_thinking": self.model.is_effectively_thinking(),
        }


class LlamaServerManager:
    """Manager for llama.cpp server process lifecycle.

    Handles starting, monitoring, and stopping llama-server processes for
    discovered models. Supports concurrent startup, readiness detection,
    and graceful shutdown with fallback to force-kill.

    Docker-Compatible Features:
    - Binds to 127.0.0.1 for security (localhost only, access via reverse proxy)
    - Extended startup timeouts for large models
    - Assumes model paths are mounted volumes
    - Graceful handling of missing binary (for build stages)

    Metal Acceleration Mode (Apple Silicon):
    - When use_external_servers=True, connects to native Metal-accelerated
      llama-server processes running on macOS host
    - Servers started externally via scripts/start-host-llama-servers.sh
    - Backend connects via host.docker.internal for 2-3x faster inference
    - Requires manual server management but provides maximum GPU performance
    """

    def __init__(
        self,
        llama_server_path: Path = Path("/usr/local/bin/llama-server"),
        max_startup_time: int = 120,
        readiness_check_interval: int = 2,
        host: str = "127.0.0.1",
        use_external_servers: bool = False,
        websocket_manager: Optional["WebSocketManager"] = None,
    ):
        """Initialize the server manager.

        Args:
            llama_server_path: Path to llama-server binary executable
            max_startup_time: Maximum seconds to wait for server readiness
            readiness_check_interval: Seconds between readiness checks
            host: Host address to bind servers to (127.0.0.1 for security)
            use_external_servers: If True, connect to externally-managed servers
                instead of launching subprocesses (for Metal acceleration)
            websocket_manager: Optional WebSocket manager for log streaming
        """
        self.llama_server_path = Path(llama_server_path)
        self.max_startup_time = max_startup_time
        self.readiness_check_interval = readiness_check_interval
        self.host = host
        self.use_external_servers = use_external_servers
        self.websocket_manager = websocket_manager
        self.host_api_url = os.getenv("HOST_API_URL", "http://host-api:9090")

        logger.info(
            f" DEBUG: LlamaServerManager.__init__ received use_external_servers = {use_external_servers}"
        )

        # Validate llama-server binary exists (skip if using external servers)
        # Note: Skip validation in Docker build stages to allow image creation
        if not use_external_servers and not self.llama_server_path.exists():
            logger.warning(
                f"llama-server binary not found at {self.llama_server_path}. "
                "Server launches will fail. This is acceptable during Docker builds."
            )

        # Dictionary of running servers keyed by model_id
        self.servers: Dict[str, ServerProcess] = {}

        logger.info("Initialized llama.cpp server manager")
        if use_external_servers:
            logger.info("   EXTERNAL SERVER MODE (Metal Acceleration)")
            logger.info("  Connecting to native Metal-accelerated servers on host")
            logger.info("  Start servers with: ./scripts/start-host-llama-servers.sh")
        else:
            logger.info(f"  Binary path: {self.llama_server_path}")
            logger.info(f"  Bind host: {self.host}")
        logger.info(f"  Max startup time: {self.max_startup_time}s")
        logger.info(f"  Readiness check interval: {self.readiness_check_interval}s")
        if websocket_manager:
            logger.info("  Log streaming enabled (WebSocket)")

    async def start_server(self, model: DiscoveredModel) -> ServerProcess:
        """Start llama.cpp server process for a single model.

        Launches llama-server subprocess with optimized settings and waits
        for the server to become ready before returning.

        In external server mode (Metal acceleration), connects to externally-managed
        server via host.docker.internal instead of launching subprocess.

        Args:
            model: DiscoveredModel to start server for

        Returns:
            ServerProcess instance wrapping the launched process (or external server)

        Raises:
            SynapseException: If model has no port assigned, server fails to
                start, or readiness timeout is exceeded
        """
        # Validate model has port assignment
        if not model.port:
            raise SynapseException(
                f"Model {model.model_id} has no port assigned",
                details={"model_id": model.model_id},
            )

        # Check if server already running
        if model.model_id in self.servers:
            existing = self.servers[model.model_id]
            logger.warning(
                f"Server already running for {model.model_id} "
                f"(PID: {existing.pid}, port: {existing.port})"
            )
            return existing

        logger.info(f"Starting llama.cpp server for: {model.get_display_name()}")
        logger.info(f"  Model file: {model.file_path}")
        logger.info(f"  Port: {model.port}")
        logger.info(f"  Tier: {model.get_effective_tier()}")
        logger.info(f"  Thinking mode: {model.is_effectively_thinking()}")

        # External server mode (Metal acceleration on macOS host)
        logger.info(
            f" DEBUG: In start_server(), self.use_external_servers = {self.use_external_servers}"
        )
        if self.use_external_servers:
            logger.info(" DEBUG: Taking EXTERNAL SERVER path (Metal acceleration)")
            return await self._connect_to_external_server(model)
        else:
            logger.info(" DEBUG: Taking SUBPROCESS path (Docker Linux binary)")

        # Validate binary exists before launching
        if not self.llama_server_path.exists():
            raise SynapseException(
                f"llama-server binary not found at {self.llama_server_path}",
                details={
                    "model_id": model.model_id,
                    "binary_path": str(self.llama_server_path),
                },
            )

        # Load runtime settings for dynamic configuration
        settings = settings_service.get_runtime_settings()

        # Phase 2: Use per-model overrides if set, otherwise use global settings
        gpu_layers = (
            model.n_gpu_layers
            if model.n_gpu_layers is not None
            else settings.n_gpu_layers
        )
        ctx_size = model.ctx_size if model.ctx_size is not None else settings.ctx_size
        threads = model.n_threads if model.n_threads is not None else settings.threads
        batch_size = (
            model.batch_size if model.batch_size is not None else settings.batch_size
        )

        logger.info(
            f"Runtime settings for {model.model_id}: "
            f"GPU={gpu_layers} {'(override)' if model.n_gpu_layers is not None else '(global)'}, "
            f"ctx={ctx_size} {'(override)' if model.ctx_size is not None else '(global)'}, "
            f"threads={threads} {'(override)' if model.n_threads is not None else '(global)'}, "
            f"batch={batch_size} {'(override)' if model.batch_size is not None else '(global)'}"
        )

        # Build command with per-model or global settings
        cmd = [
            str(self.llama_server_path),
            "--model",
            str(model.file_path),
            "--host",
            self.host,
            "--port",
            str(model.port),
            "--ctx-size",
            str(ctx_size),
            "--n-gpu-layers",
            str(gpu_layers),
            "--threads",
            str(threads),
            "--batch-size",
            str(batch_size),
            "--ubatch-size",
            str(settings.ubatch_size),
        ]

        # Add optional flags based on settings
        if settings.flash_attn:
            cmd.append("--flash-attn")
        if settings.no_mmap:
            cmd.append("--no-mmap")

        # Log the full command for debugging (Phase 1 enhancement)
        cmd_str = " ".join(str(arg) for arg in cmd)
        logger.info(f"Executing command: {cmd_str}")

        # Launch subprocess
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line-buffered
                universal_newlines=True,
            )

            server = ServerProcess(model=model, process=process)
            self.servers[model.model_id] = server

            logger.info(
                f"Launched llama-server process: PID {process.pid} on port {model.port}"
            )

            # Emit model state event: loading -> active
            try:
                asyncio.create_task(
                    emit_model_state_event(
                        model_id=model.model_id,
                        previous_state="stopped",
                        current_state="loading",
                        reason=f"Server process started (PID: {process.pid})",
                        port=model.port,
                    )
                )
            except Exception as e:
                logger.debug(f"Failed to emit model state event: {e}")

            # Start log streaming thread (if WebSocket manager available)
            if self.websocket_manager:
                log_thread = threading.Thread(
                    target=self._stream_logs, args=(server,), daemon=True
                )
                log_thread.start()
                logger.debug(f"Started log streaming thread for {model.model_id}")

            # Wait for server to become ready
            await self._wait_for_readiness(server)

            return server

        except Exception as e:
            logger.error(
                f"Failed to start server for {model.model_id}: {e}", exc_info=True
            )

            # Emit error event
            try:
                asyncio.create_task(
                    emit_error_event(
                        error_type=type(e).__name__,
                        error_message=f"Failed to start server: {str(e)}",
                        component="LlamaServerManager",
                        recovery_action="Check model file path and llama-server binary",
                    )
                )
            except Exception as emit_err:
                logger.debug(f"Failed to emit error event: {emit_err}")

            raise SynapseException(
                f"Failed to launch llama.cpp server: {e}",
                details={
                    "model_id": model.model_id,
                    "port": model.port,
                    "binary": str(self.llama_server_path),
                },
            )

    async def _connect_to_external_server(
        self, model: DiscoveredModel
    ) -> ServerProcess:
        """Connect to externally-managed llama-server (Metal acceleration mode).

        Instead of launching a subprocess, this checks if a server is already
        running on the macOS host at the specified port. Used for Metal GPU
        acceleration where servers are started via start-host-llama-servers.sh.

        Args:
            model: DiscoveredModel to connect to

        Returns:
            ServerProcess instance tracking the external server

        Raises:
            SynapseException: If external server is not reachable
        """
        logger.info(
            f"🔌 Connecting to external Metal-accelerated server on port {model.port}..."
        )

        # Check health endpoint on host (via host.docker.internal)
        health_url = f"http://host.docker.internal:{model.port}/health"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=5.0)

                if response.status_code == 200:
                    logger.info(f"✓ External server ready at {health_url}")

                    # Create virtual ServerProcess for external server
                    server = ServerProcess(model=model, process=None, is_external=True)
                    server.is_ready = True
                    self.servers[model.model_id] = server

                    return server
                else:
                    raise SynapseException(
                        f"External server returned {response.status_code}",
                        details={"url": health_url, "status": response.status_code},
                    )

        except httpx.RequestError as e:
            logger.error(f"✗ Cannot connect to external server at {health_url}: {e}")
            raise SynapseException(
                f"External Metal-accelerated server not running on port {model.port}. "
                f"Start servers with: ./scripts/start-host-llama-servers.sh",
                details={"port": model.port, "health_url": health_url, "error": str(e)},
            )

    async def _ensure_metal_servers_started(self) -> None:
        """Start Metal servers via host API if not already running.

        This method checks if Metal servers are running on the host, and if not,
        triggers the host API to launch them. This enables automatic server startup
        when clicking "START ALL ENABLED" in the WebUI.

        Raises:
            SynapseException: If host API is unreachable or fails to start servers
        """
        if not self.use_external_servers:
            # Not in external server mode, nothing to do
            return

        logger.info(" Checking if Metal servers are already running...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check host API status
                status_response = await client.get(
                    f"{self.host_api_url}/api/servers/status"
                )
                status_data = status_response.json()

                if status_data.get("running"):
                    logger.info("✓ Metal servers already running on host")
                    return

                # Servers not running - start them via host API
                logger.info(" Starting Metal servers via host API...")
                logger.info("   This will take ~10-15 seconds for initialization")

                start_response = await client.post(
                    f"{self.host_api_url}/api/servers/start",
                    timeout=35.0,  # Allow time for script execution
                )

                if start_response.status_code == 200:
                    logger.info("✓ Metal servers start command successful")
                    logger.info(" Waiting 10 seconds for servers to initialize...")
                    await asyncio.sleep(10)  # Wait for servers to fully start
                    logger.info("✓ Metal servers should now be ready")
                else:
                    error_detail = start_response.json().get("detail", "Unknown error")
                    raise SynapseException(
                        f"Host API failed to start servers: {error_detail}",
                        details={"status_code": start_response.status_code},
                    )

        except httpx.RequestError as e:
            logger.error(f"✗ Cannot reach host API at {self.host_api_url}: {e}")
            raise SynapseException(
                f"Host API not available at {self.host_api_url}. "
                "Ensure docker-compose started all services correctly.",
                details={"host_api_url": self.host_api_url, "error": str(e)},
            )

    async def _wait_for_readiness(self, server: ServerProcess) -> None:
        """Wait for server to become ready by monitoring stderr output.

        Monitors the server's stderr stream for readiness indicators like
        "http server listening" or "server started". Falls back to timeout
        if no clear signal is detected.

        Args:
            server: ServerProcess to monitor for readiness

        Raises:
            SynapseException: If process dies during startup or critical
                error is detected in output
        """
        logger.info(f"Monitoring {server.model.model_id} for readiness signals...")

        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < self.max_startup_time:
            # Check if process has terminated unexpectedly
            if not server.is_running():
                # Read any final error output
                try:
                    if server.process is not None and server.process.stderr is not None:
                        stderr_output = server.process.stderr.read()
                        logger.error(f"Server stderr: {stderr_output}")
                except Exception:
                    pass

                raise SynapseException(
                    "Server process died during startup",
                    details={
                        "model_id": server.model.model_id,
                        "uptime": server.get_uptime_seconds(),
                    },
                )

            # Non-blocking read of stderr for readiness indicators
            try:
                import select

                if server.process is None or server.process.stderr is None:
                    await asyncio.sleep(0.5)
                    continue

                # Check if data available on stderr (Unix-like systems)
                ready_fds, _, _ = select.select(
                    [server.process.stderr],
                    [],
                    [],
                    0.1,  # 100ms timeout
                )

                if ready_fds:
                    line = server.process.stderr.readline()

                    if line:
                        line_lower = line.lower()

                        # Check for readiness keywords
                        readiness_indicators = [
                            "http server listening",
                            "server is listening",
                            "listening on",
                            "server started",
                            "ready to receive requests",
                        ]

                        if any(
                            indicator in line_lower
                            for indicator in readiness_indicators
                        ):
                            server.is_ready = True
                            elapsed = server.get_uptime_seconds()
                            logger.info(
                                f"✓ {server.model.model_id} is READY "
                                f"(startup took {elapsed}s)"
                            )

                            # Emit model state event: loading -> active
                            try:
                                asyncio.create_task(
                                    emit_model_state_event(
                                        model_id=server.model.model_id,
                                        previous_state="loading",
                                        current_state="active",
                                        reason=f"Server ready (startup took {elapsed}s)",
                                        port=server.port,
                                    )
                                )
                            except Exception as e:
                                logger.debug(f"Failed to emit model state event: {e}")
                            return

                        # Check for critical errors
                        error_indicators = [
                            "error loading model",
                            "failed to load",
                            "ggml_init_cublas: failed",
                            "cannot open model file",
                        ]

                        if any(error in line_lower for error in error_indicators):
                            logger.error(
                                f"Critical error during startup: {line.strip()}"
                            )
                            raise SynapseException(
                                f"Server startup failed with error: {line.strip()}",
                                details={"model_id": server.model.model_id},
                            )

                        # Log other output at debug level
                        if "error" in line_lower or "warn" in line_lower:
                            logger.debug(f"Server output: {line.strip()}")

            except Exception as e:
                logger.debug(f"Error reading server stderr: {e}")

            # Sleep before next check
            await asyncio.sleep(self.readiness_check_interval)

        # Timeout reached - mark as ready with warning
        # This is a fallback for servers that don't emit clear readiness signals
        logger.warning(
            f"  {server.model.model_id} reached {self.max_startup_time}s timeout "
            f"without clear readiness signal. Marking as ready (fallback behavior)."
        )
        server.is_ready = True

    def _stream_logs(self, server: ServerProcess) -> None:
        """Stream stderr from subprocess to WebSocket clients.

        Runs in a background thread to read stderr line by line from the
        llama-server process and broadcast log entries to connected WebSocket
        clients. Parses log levels from line content and formats entries for
        the frontend.

        This method runs until the subprocess terminates or an error occurs.
        The thread is daemon, so it will automatically terminate when the
        main process exits.

        Args:
            server: ServerProcess instance to stream logs from

        Thread Safety:
            Runs in a separate thread. Uses asyncio.run() to call the async
            websocket_manager.broadcast_log() method. This is safe because
            each call creates a new event loop for that thread.
        """
        if not self.websocket_manager:
            logger.warning("Cannot stream logs - WebSocket manager not available")
            return

        logger.info(f"Starting log stream for {server.model.model_id}")

        try:
            # Read stderr line by line until process terminates
            while server.is_running():
                if not server.process or not server.process.stderr:
                    break

                line = server.process.stderr.readline()

                if not line:
                    # Process ended or no more output
                    break

                # Parse log level from line content
                level = "INFO"
                line_lower = line.lower()

                if (
                    "error" in line_lower
                    or "failed" in line_lower
                    or "exception" in line_lower
                ):
                    level = "ERROR"
                elif "warn" in line_lower or "warning" in line_lower:
                    level = "WARN"

                # Create log entry
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "model_id": server.model.model_id,
                    "port": server.port,
                    "level": level,
                    "message": line.strip(),
                }

                # Broadcast to WebSocket clients
                # Run in new event loop (thread-safe pattern)
                try:
                    asyncio.run(self.websocket_manager.broadcast_log(log_entry))
                except Exception as e:
                    logger.debug(f"Failed to broadcast log: {e}")

        except Exception as e:
            logger.error(
                f"Log streaming error for {server.model.model_id}: {e}", exc_info=True
            )

        finally:
            logger.info(f"Log stream ended for {server.model.model_id}")

    async def start_all(
        self, models: List[DiscoveredModel]
    ) -> Dict[str, ServerProcess]:
        """Start servers for multiple models concurrently.

        Launches all model servers in parallel using asyncio.gather for
        maximum efficiency. Tolerates individual failures and reports
        aggregate results.

        Args:
            models: List of DiscoveredModels to start servers for

        Returns:
            Dictionary of successfully started servers keyed by model_id
        """
        if not models:
            logger.info("No models to start servers for")
            return {}

        # Ensure Metal servers are started via host API (if external mode)
        await self._ensure_metal_servers_started()

        logger.info(
            f"Starting llama.cpp servers for {len(models)} models concurrently..."
        )

        # Create startup tasks for all models
        tasks = [self.start_server(model) for model in models]

        # Execute concurrently, capturing exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful starts from failures
        started: Dict[str, ServerProcess] = {}
        failed: List[str] = []

        for model, result in zip(models, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to start server for {model.model_id}: {result}")
                failed.append(model.model_id)
            elif isinstance(result, ServerProcess):
                started[model.model_id] = result

        # Log summary
        logger.info(f"✓ Successfully started {len(started)}/{len(models)} servers")

        if failed:
            logger.warning(f"✗ Failed to start: {', '.join(failed)}")

        return started

    async def stop_server(self, model_id: str, timeout: int = 10) -> None:
        """Stop a specific server gracefully with fallback to force-kill.

        Attempts graceful shutdown via SIGTERM, waits for timeout, then
        force-kills with SIGKILL if necessary.

        For external servers (Metal mode), this only removes tracking.
        The actual server process must be stopped via stop-host-llama-servers.sh.

        Args:
            model_id: Model ID of the server to stop
            timeout: Seconds to wait for graceful shutdown before force-kill
        """
        server = self.servers.get(model_id)

        if not server:
            logger.warning(f"No running server found for {model_id}")
            return

        # External server mode - can't stop, only untrack
        if server.is_external:
            logger.warning(
                f"  Cannot stop external Metal-accelerated server for {model_id}. "
                f"Use ./scripts/stop-host-llama-servers.sh to stop all external servers."
            )
            # Remove from tracking dictionary
            del self.servers[model_id]
            return

        logger.info(
            f"Stopping server for {model_id} "
            f"(PID: {server.pid}, uptime: {server.get_uptime_seconds()}s)"
        )

        try:
            if server.process is None:
                logger.warning(f"Server {model_id} has no process to stop")
                return

            # Attempt graceful shutdown with SIGTERM
            server.process.terminate()

            try:
                # Wait for graceful exit
                server.process.wait(timeout=timeout)
                logger.info(f"✓ {model_id} stopped gracefully")

            except subprocess.TimeoutExpired:
                # Force-kill with SIGKILL
                logger.warning(
                    f"Server {model_id} did not stop within {timeout}s. "
                    f"Force-killing with SIGKILL..."
                )
                server.process.kill()
                server.process.wait(timeout=5)
                logger.info(f"✓ {model_id} force-stopped")

        except Exception as e:
            logger.error(f"Error stopping server {model_id}: {e}", exc_info=True)

        finally:
            # Emit model state event: active -> stopped
            try:
                asyncio.create_task(
                    emit_model_state_event(
                        model_id=model_id,
                        previous_state="active",
                        current_state="stopped",
                        reason="Server stopped by user request",
                        port=server.port,
                    )
                )
            except Exception as e:
                logger.debug(f"Failed to emit model state event: {e}")

            # Remove from tracking dictionary
            del self.servers[model_id]

    async def stop_all(self, timeout: int = 10) -> None:
        """Stop all running servers gracefully.

        Stops all servers concurrently using asyncio.gather for efficiency.
        In external server mode, calls host API to stop Metal servers.

        Args:
            timeout: Seconds to wait for each server to stop gracefully
        """
        # If using external Metal servers, stop them via host API
        if self.use_external_servers:
            logger.info("🛑 Stopping Metal servers via host API...")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    stop_response = await client.post(
                        f"{self.host_api_url}/api/servers/stop",
                        timeout=35.0,  # Allow time for graceful shutdown
                    )

                    if stop_response.status_code == 200:
                        logger.info(
                            "✓ Metal servers stopped successfully via host API"
                        )
                        # Clear internal server tracking
                        self.servers.clear()
                        return
                    else:
                        error_detail = stop_response.json().get(
                            "detail", "Unknown error"
                        )
                        logger.error(
                            f"✗ Host API failed to stop servers: {error_detail}"
                        )
                        raise SynapseException(
                            f"Host API failed to stop servers: {error_detail}",
                            details={"status_code": stop_response.status_code},
                        )

            except httpx.RequestError as e:
                logger.error(f"✗ Cannot reach host API at {self.host_api_url}: {e}")
                raise SynapseException(
                    f"Host API not available at {self.host_api_url}. "
                    "Servers may still be running on host.",
                    details={"host_api_url": self.host_api_url, "error": str(e)},
                )

        # Internal server mode - stop servers managed by this process
        if not self.servers:
            logger.info("No running servers to stop")
            return

        server_count = len(self.servers)
        logger.info(f"Stopping all {server_count} running servers...")

        # Create stop tasks for all servers
        # Use list() to snapshot keys since dict will be modified
        tasks = [
            self.stop_server(model_id, timeout=timeout)
            for model_id in list(self.servers.keys())
        ]

        # Execute concurrently, ignoring individual failures
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"✓ All {server_count} servers stopped")

    def get_status_summary(self) -> dict:
        """Get comprehensive status summary of all servers.

        Returns:
            Dictionary containing:
                - total_servers: Total number of tracked servers
                - ready_servers: Number of servers marked as ready
                - running_servers: Number of servers with live processes
                - servers: List of detailed status dicts for each server
        """
        servers_status = [s.get_status() for s in self.servers.values()]

        return {
            "total_servers": len(self.servers),
            "ready_servers": sum(1 for s in self.servers.values() if s.is_ready),
            "running_servers": sum(1 for s in self.servers.values() if s.is_running()),
            "servers": servers_status,
        }

    def get_server(self, model_id: str) -> Optional[ServerProcess]:
        """Get ServerProcess instance for a specific model.

        Args:
            model_id: Model identifier to lookup

        Returns:
            ServerProcess if found, None otherwise
        """
        return self.servers.get(model_id)

    def is_server_running(self, model_id: str) -> bool:
        """Check if a server is running for a specific model.

        Args:
            model_id: Model identifier to check

        Returns:
            True if server exists and process is alive
        """
        server = self.servers.get(model_id)
        return server is not None and server.is_running()

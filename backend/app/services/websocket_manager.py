"""
WebSocket Manager for Real-Time Log Streaming.

This module manages WebSocket connections for streaming llama-server process logs
to frontend clients. It provides:
- Connection lifecycle management (connect/disconnect)
- Broadcasting log messages to all connected clients
- Circular buffer for historical logs (500 lines per model)
- Thread-safe operations for concurrent access from subprocess threads
- Filtering by model_id

Author: Backend Architect
Phase: 3 - WebSocket Log Streaming
"""

import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional, Deque

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections and log broadcasting.

    Handles multiple concurrent WebSocket connections and broadcasts log
    messages from llama-server processes to all connected clients. Maintains
    a circular buffer of recent logs for each model to send to new clients
    upon connection.

    Thread Safety:
        All public methods use asyncio.Lock to ensure thread-safe access
        from both async request handlers and subprocess log threads.
    """

    def __init__(self, buffer_size: int = 500):
        """Initialize WebSocket manager.

        Args:
            buffer_size: Maximum number of log lines to buffer per model
        """
        self.active_connections: List[WebSocket] = []
        self.log_buffer: Dict[str, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        self.buffer_size = buffer_size
        self._lock = asyncio.Lock()

        logger.info(
            f"WebSocket manager initialized (buffer_size={buffer_size} lines/model)"
        )

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection.

        Accepts the WebSocket handshake and adds the connection to the
        active connections list for future broadcasts.

        Args:
            websocket: WebSocket connection to accept
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections.append(websocket)

        logger.info(
            f"WebSocket connected (total connections: {len(self.active_connections)})"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection.

        Removes the connection from the active connections list. Called when
        a client disconnects or a connection error occurs.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

        logger.info(
            f"WebSocket disconnected (remaining connections: {len(self.active_connections)})"
        )

    async def broadcast_log(self, log_entry: dict) -> None:
        """Broadcast log entry to all connected clients.

        Sends a log entry to all active WebSocket connections. Automatically
        handles disconnections by removing dead connections from the list.
        Also stores the log in the circular buffer for the model.

        Args:
            log_entry: Log entry dictionary with keys:
                - timestamp: ISO 8601 timestamp string
                - model_id: Model identifier
                - port: Server port number
                - level: Log level (INFO, WARN, ERROR)
                - message: Log message text

        Example:
            await websocket_manager.broadcast_log({
                "timestamp": "2025-11-05T09:30:00Z",
                "model_id": "deepseek_r1_8b_q4km",
                "port": 8080,
                "level": "INFO",
                "message": "Server started successfully"
            })
        """
        # Store in buffer first (no lock needed - defaultdict is thread-safe for reads)
        model_id = log_entry.get("model_id", "unknown")
        self.log_buffer[model_id].append(log_entry)

        # Broadcast to all connected clients
        async with self._lock:
            dead_connections = []

            for connection in self.active_connections:
                try:
                    await connection.send_json(log_entry)
                except Exception as e:
                    logger.debug(
                        f"Failed to send log to WebSocket (connection likely closed): {e}"
                    )
                    dead_connections.append(connection)

            # Remove dead connections
            for dead_conn in dead_connections:
                if dead_conn in self.active_connections:
                    self.active_connections.remove(dead_conn)

            if dead_connections:
                logger.info(
                    f"Removed {len(dead_connections)} dead WebSocket connections"
                )

    def get_logs(self, model_id: Optional[str] = None) -> List[dict]:
        """Get buffered logs for a model or all models.

        Retrieves historical logs from the circular buffer. If model_id is
        specified, returns only logs for that model. Otherwise, returns all
        buffered logs across all models, sorted by timestamp.

        Args:
            model_id: Optional model ID to filter logs. If None, returns all logs.

        Returns:
            List of log entry dictionaries, ordered by timestamp

        Example:
            # Get all logs
            all_logs = websocket_manager.get_logs()

            # Get logs for specific model
            model_logs = websocket_manager.get_logs("deepseek_r1_8b_q4km")
        """
        if model_id:
            # Return logs for specific model
            return list(self.log_buffer.get(model_id, []))
        else:
            # Return all logs, sorted by timestamp
            all_logs = []
            for model_id, logs in self.log_buffer.items():
                all_logs.extend(logs)

            # Sort by timestamp (ISO 8601 strings sort correctly)
            all_logs.sort(key=lambda x: x.get("timestamp", ""))

            return all_logs

    def clear_logs(self, model_id: Optional[str] = None) -> None:
        """Clear buffered logs for a model or all models.

        Clears the log buffer. If model_id is specified, clears only that
        model's logs. Otherwise, clears all logs.

        Args:
            model_id: Optional model ID to clear logs for. If None, clears all.
        """
        if model_id:
            if model_id in self.log_buffer:
                self.log_buffer[model_id].clear()
                logger.info(f"Cleared log buffer for model: {model_id}")
        else:
            self.log_buffer.clear()
            logger.info("Cleared all log buffers")

    def get_connection_count(self) -> int:
        """Get the number of active WebSocket connections.

        Returns:
            Number of active connections
        """
        return len(self.active_connections)

    def get_buffer_stats(self) -> dict:
        """Get statistics about buffered logs.

        Returns:
            Dictionary with keys:
                - total_models: Number of models with buffered logs
                - total_logs: Total number of buffered log entries
                - models: Dict mapping model_id to log count
        """
        models_stats = {
            model_id: len(logs)
            for model_id, logs in self.log_buffer.items()
        }

        return {
            "total_models": len(self.log_buffer),
            "total_logs": sum(models_stats.values()),
            "models": models_stats
        }

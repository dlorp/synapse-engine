"""Health Monitoring Service for Degraded Status Alerts.

This module provides background health monitoring that periodically checks
system health status and emits alerts when the system enters or recovers
from degraded state.

The health monitor integrates with:
- /api/health/ready endpoint for dependency checks
- EventBus for real-time alert broadcasting
- WebSocket /ws/events for frontend notifications

Author: Backend Architect
Phase: Production Metrics Implementation
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, List

import httpx

from app.core.logging import get_logger
from app.models.events import EventType, EventSeverity

logger = get_logger(__name__)


class HealthMonitor:
    """Background health monitoring service with degradation alerting.

    This service periodically polls the health check endpoint and emits
    alerts via EventBus when system health changes between "ok" and "degraded"
    states.

    Features:
        - Periodic health checks (configurable interval)
        - State transition detection (ok ↔ degraded)
        - Alert emission via EventBus
        - Degradation duration tracking
        - Automatic recovery detection

    Alert Types:
        - DEGRADED: System health degraded (error severity)
        - RECOVERED: System health restored (info severity)

    Example Alert Flow:
        1. System healthy → Redis fails → Health status: degraded
        2. Monitor detects: ok → degraded transition
        3. Emits ERROR alert: "System health degraded: memex"
        4. Frontend receives via WebSocket, shows red alert
        5. Redis recovers → Health status: ok
        6. Monitor detects: degraded → ok transition
        7. Emits INFO alert: "System health recovered"
        8. Frontend shows green success message

    Architecture:
        ┌──────────────────┐
        │  HealthMonitor   │
        │  (background)    │
        └────────┬─────────┘
                 │ poll every 60s
                 ▼
        ┌──────────────────┐
        │  /health/ready   │
        │  (check deps)    │
        └────────┬─────────┘
                 │ status change
                 ▼
        ┌──────────────────┐
        │    EventBus      │
        │  (broadcast)     │
        └────────┬─────────┘
                 │ WebSocket
                 ▼
        ┌──────────────────┐
        │  LiveEventFeed   │
        │  (frontend)      │
        └──────────────────┘

    Attributes:
        check_interval: Seconds between health checks (default: 60)
        last_status: Previous health status ("ok" or "degraded")
        degraded_since: Timestamp when degradation started
        running: Whether monitor loop is active
        _task: Background asyncio task
    """

    def __init__(
        self,
        check_interval: int = 60,
        health_endpoint: str = "http://localhost:8000/api/health/ready",
    ) -> None:
        """Initialize health monitor with configurable check interval.

        Args:
            check_interval: Seconds between health checks (default: 60)
            health_endpoint: Health check URL (default: internal endpoint)
        """
        self.check_interval = check_interval
        self.health_endpoint = health_endpoint
        self.last_status = "ok"
        self.degraded_since: Optional[datetime] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(
            f"HealthMonitor initialized (check_interval={check_interval}s, "
            f"endpoint={health_endpoint})"
        )

    async def start(self) -> None:
        """Start health monitoring background loop.

        Creates a background task that continuously monitors health status.
        Safe to call multiple times - ignores if already running.
        """
        if self.running:
            logger.warning("HealthMonitor already running, ignoring start request")
            return

        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("HealthMonitor started - background monitoring active")

    async def stop(self) -> None:
        """Stop health monitoring and clean up resources.

        Cancels the background task gracefully. Should be called during
        application shutdown.
        """
        if not self.running:
            return

        self.running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("HealthMonitor stopped")

    async def _monitor_loop(self) -> None:
        """Background monitoring loop - runs continuously until stopped.

        Polls health endpoint at configured interval, detects state transitions,
        and emits alerts via EventBus.
        """
        logger.info("Health monitoring loop started")

        # Wait a short period on startup to let services initialize
        await asyncio.sleep(10)

        while self.running:
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}", exc_info=True)

            # Sleep until next check
            await asyncio.sleep(self.check_interval)

        logger.info("Health monitoring loop stopped")

    async def _check_health(self) -> None:
        """Perform health check and emit alerts on status change.

        Queries the health endpoint, compares status with previous check,
        and emits appropriate alerts via EventBus if status changed.
        """
        try:
            # Query health endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(self.health_endpoint, timeout=5.0)

                if response.status_code != 200:
                    logger.warning(
                        f"Health endpoint returned {response.status_code}",
                        extra={"status_code": response.status_code},
                    )
                    return

                health_data = response.json()
                current_status = health_data.get("status", "unknown")
                components = health_data.get("components", {})

                # Detect status transitions
                if current_status == "degraded" and self.last_status == "ok":
                    # Transition: ok → degraded
                    await self._emit_degraded_alert(components)
                    self.degraded_since = datetime.utcnow()
                    logger.warning(
                        "System health DEGRADED", extra={"components": components}
                    )

                elif current_status == "ok" and self.last_status == "degraded":
                    # Transition: degraded → ok
                    await self._emit_recovery_alert()
                    degraded_duration = (
                        (datetime.utcnow() - self.degraded_since).total_seconds()
                        if self.degraded_since
                        else 0
                    )
                    self.degraded_since = None
                    logger.info(
                        f"System health RECOVERED after {degraded_duration:.0f}s",
                        extra={"degraded_duration_seconds": degraded_duration},
                    )

                # Update last status
                self.last_status = current_status

        except httpx.TimeoutException:
            logger.warning(
                f"Health endpoint timeout ({self.health_endpoint})",
                extra={"endpoint": self.health_endpoint},
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)

    async def _emit_degraded_alert(self, components: Dict[str, str]) -> None:
        """Emit system health degraded alert via EventBus.

        Creates an ERROR event with details of failed components and broadcasts
        to all WebSocket clients via EventBus.

        Args:
            components: Dictionary of component names to status strings
        """
        try:
            from app.services.event_bus import get_event_bus

            event_bus = get_event_bus()

            # Identify failed components
            failed_components = self._get_failed_components(components)

            # Build detailed message
            if len(failed_components) == 1:
                message = f"System health degraded: {failed_components[0]} unavailable"
            else:
                components_str = ", ".join(failed_components)
                message = f"System health degraded: {components_str} unavailable"

            # Emit error event
            await event_bus.publish(
                event_type=EventType.ERROR,
                message=message,
                severity=EventSeverity.ERROR,
                metadata={
                    "source": "health_monitor",
                    "failed_components": failed_components,
                    "all_components": components,
                    "degraded_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Emitted degraded alert: {message}")

        except Exception as e:
            logger.error(f"Failed to emit degraded alert: {e}", exc_info=True)

    async def _emit_recovery_alert(self) -> None:
        """Emit system health recovered alert via EventBus.

        Creates an INFO event indicating all components are operational and
        broadcasts to all WebSocket clients.
        """
        try:
            from app.services.event_bus import get_event_bus

            event_bus = get_event_bus()

            # Calculate degradation duration
            degraded_duration_seconds = (
                (datetime.utcnow() - self.degraded_since).total_seconds()
                if self.degraded_since
                else 0
            )

            # Build recovery message
            if degraded_duration_seconds > 0:
                duration_str = self._format_duration(degraded_duration_seconds)
                message = f"System health recovered after {duration_str}"
            else:
                message = "System health recovered - all components operational"

            # Emit success event (using QUERY_ROUTE type as generic success indicator)
            await event_bus.publish(
                event_type=EventType.QUERY_ROUTE,  # Generic info event
                message=message,
                severity=EventSeverity.INFO,
                metadata={
                    "source": "health_monitor",
                    "degraded_duration_seconds": round(degraded_duration_seconds, 2),
                    "recovered_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Emitted recovery alert: {message}")

        except Exception as e:
            logger.error(f"Failed to emit recovery alert: {e}", exc_info=True)

    def _get_failed_components(self, components: Dict[str, str]) -> List[str]:
        """Extract list of failed component names from health status.

        Args:
            components: Dictionary of component names to status strings

        Returns:
            List of component names with non-ready status
        """
        failed = []
        for name, status in components.items():
            # Consider "ready", "ok", "alive", and status with "_active" as healthy
            if status not in ["ready", "ok", "alive"] and "_active" not in status:
                failed.append(name)
        return failed

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "2m 30s", "45s", "1h 5m")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds / 3600)
            remaining_minutes = int((seconds % 3600) / 60)
            return f"{hours}h {remaining_minutes}m"

    def get_status(self) -> Dict[str, any]:
        """Get current health monitor status.

        Returns:
            Dictionary with keys:
                - running: Whether monitor is active
                - last_status: Last known health status
                - degraded_since: ISO timestamp if degraded, None otherwise
                - check_interval: Seconds between checks
        """
        return {
            "running": self.running,
            "last_status": self.last_status,
            "degraded_since": self.degraded_since.isoformat()
            if self.degraded_since
            else None,
            "check_interval": self.check_interval,
        }


# Global health monitor instance (initialized in main.py lifespan)
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance.

    Returns:
        Global HealthMonitor instance

    Raises:
        RuntimeError: If health monitor not initialized
    """
    if _health_monitor is None:
        raise RuntimeError(
            "HealthMonitor not initialized - call init_health_monitor() first"
        )
    return _health_monitor


def init_health_monitor(check_interval: int = 60) -> HealthMonitor:
    """Initialize the global health monitor instance.

    Should be called during application startup (in lifespan context).

    Args:
        check_interval: Seconds between health checks (default: 60)

    Returns:
        Initialized HealthMonitor instance
    """
    global _health_monitor
    _health_monitor = HealthMonitor(check_interval=check_interval)
    return _health_monitor

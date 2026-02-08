"""Orchestrator status tracking service.

This module provides a centralized service for tracking query routing decisions,
calculating tier utilization, and generating orchestrator status telemetry.

The service maintains an in-memory circular buffer of recent routing decisions
and computes real-time statistics for visualization in the frontend.
"""

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Deque, Optional
from uuid import uuid4

from app.core.logging import get_logger
from app.models.orchestrator import (
    ComplexityDistribution,
    ComplexityLevel,
    ModelTierLabel,
    OrchestratorStatusResponse,
    RoutingDecision,
    TierUtilization,
)

logger = get_logger(__name__)


class OrchestratorStatusService:
    """Service for tracking orchestrator routing decisions and telemetry.

    This service maintains a thread-safe circular buffer of routing decisions
    and provides real-time statistics for the orchestrator status endpoint.

    Attributes:
        max_decisions: Maximum number of decisions to keep in memory
        decisions: Circular buffer of routing decisions
        decision_times: Circular buffer of decision timestamps (for avg calculation)
        tier_stats: Running counters for tier utilization
        lock: Thread lock for safe concurrent access
    """

    def __init__(self, max_decisions: int = 100) -> None:
        """Initialize orchestrator status service.

        Args:
            max_decisions: Maximum number of decisions to keep in memory
        """
        self.max_decisions = max_decisions
        self.decisions: Deque[RoutingDecision] = deque(maxlen=max_decisions)
        self.decision_times: Deque[float] = deque(maxlen=max_decisions)  # ms
        self.tier_stats = {
            "Q2": {"total": 0, "active": 0},
            "Q3": {"total": 0, "active": 0},
            "Q4": {"total": 0, "active": 0},
        }
        self.lock = Lock()
        logger.info(f"OrchestratorStatusService initialized with buffer size {max_decisions}")

    def record_routing_decision(
        self,
        query: str,
        tier: str,
        complexity_score: float,
        decision_time_ms: float = 0.0,
    ) -> None:
        """Record a query routing decision.

        Thread-safe method to record routing decisions for telemetry.

        Args:
            query: Query text (will be truncated to 100 chars)
            tier: Selected tier ("fast", "balanced", or "powerful")
            complexity_score: Numerical complexity score
            decision_time_ms: Time taken to make routing decision (ms)
        """
        with self.lock:
            # Map tier names to labels
            tier_label = self._map_tier_to_label(tier)

            # Map complexity score to level
            complexity_level = self._map_score_to_complexity(complexity_score)

            # Truncate query for storage
            query_truncated = query[:100] if len(query) > 100 else query

            # Create decision record
            decision = RoutingDecision(
                id=f"dec-{uuid4().hex[:8]}",
                query=query_truncated,
                tier=tier_label,
                complexity=complexity_level,
                timestamp=datetime.now(timezone.utc).isoformat(),
                score=round(complexity_score, 2),
            )

            # Add to buffer
            self.decisions.append(decision)
            self.decision_times.append(decision_time_ms)

            # Update tier stats
            self.tier_stats[tier_label]["total"] += 1

            logger.debug(
                f"Recorded routing decision: {tier_label} for query "
                f"(complexity={complexity_score:.2f}, time={decision_time_ms:.2f}ms)"
            )

    def mark_request_active(self, tier: str) -> None:
        """Mark a request as active for a specific tier.

        Used to track concurrent requests per tier.

        Args:
            tier: Tier name ("fast", "balanced", or "powerful")
        """
        with self.lock:
            tier_label = self._map_tier_to_label(tier)
            self.tier_stats[tier_label]["active"] += 1

    def mark_request_complete(self, tier: str) -> None:
        """Mark a request as complete for a specific tier.

        Args:
            tier: Tier name ("fast", "balanced", or "powerful")
        """
        with self.lock:
            tier_label = self._map_tier_to_label(tier)
            self.tier_stats[tier_label]["active"] = max(
                0, self.tier_stats[tier_label]["active"] - 1
            )

    def get_status(self) -> OrchestratorStatusResponse:
        """Get current orchestrator status.

        Thread-safe method to generate complete status snapshot.

        Returns:
            OrchestratorStatusResponse with all telemetry data
        """
        with self.lock:
            # Get recent decisions (up to 10 most recent)
            recent_decisions = list(self.decisions)[-10:]
            recent_decisions.reverse()  # Newest first

            # Calculate tier utilization
            tier_utilization = self._calculate_tier_utilization()

            # Calculate complexity distribution
            complexity_distribution = self._calculate_complexity_distribution()

            # Calculate average decision time
            avg_decision_time = (
                sum(self.decision_times) / len(self.decision_times) if self.decision_times else 0.0
            )

            # Total decisions
            total_decisions = sum(stats["total"] for stats in self.tier_stats.values())

            return OrchestratorStatusResponse(
                tier_utilization=tier_utilization,
                recent_decisions=recent_decisions,
                complexity_distribution=complexity_distribution,
                total_decisions=total_decisions,
                avg_decision_time_ms=round(avg_decision_time, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def _calculate_tier_utilization(self) -> list[TierUtilization]:
        """Calculate tier utilization metrics.

        Returns:
            List of TierUtilization for Q2, Q3, Q4
        """
        utilization = []

        for tier_label in ["Q2", "Q3", "Q4"]:
            stats = self.tier_stats[tier_label]
            total = stats["total"]
            active = stats["active"]

            # Calculate utilization percentage based on recent activity
            # Use a sliding window of last 20 decisions
            recent_for_tier = sum(1 for d in list(self.decisions)[-20:] if d.tier == tier_label)
            utilization_percent = min(100, int((recent_for_tier / 20) * 100)) if total > 0 else 0

            utilization.append(
                TierUtilization(
                    tier=tier_label,  # type: ignore
                    utilization_percent=utilization_percent,
                    active_requests=active,
                    total_processed=total,
                )
            )

        return utilization

    def _calculate_complexity_distribution(self) -> ComplexityDistribution:
        """Calculate complexity distribution from recent decisions.

        Returns:
            ComplexityDistribution with percentages summing to 100%
        """
        if not self.decisions:
            # Default distribution when no data
            return ComplexityDistribution(simple=0, moderate=0, complex=0)

        # Count complexity levels
        counts = {"SIMPLE": 0, "MODERATE": 0, "COMPLEX": 0}
        for decision in self.decisions:
            counts[decision.complexity] += 1

        total = len(self.decisions)

        # Calculate percentages (rounded to integers)
        simple = int((counts["SIMPLE"] / total) * 100)
        moderate = int((counts["MODERATE"] / total) * 100)
        complex = int((counts["COMPLEX"] / total) * 100)

        # Ensure sum is exactly 100% (adjust largest category)
        diff = 100 - (simple + moderate + complex)
        if diff != 0:
            # Add difference to largest category
            max_count = max(counts.values())
            if counts["SIMPLE"] == max_count:
                simple += diff
            elif counts["MODERATE"] == max_count:
                moderate += diff
            else:
                complex += diff

        return ComplexityDistribution(simple=simple, moderate=moderate, complex=complex)

    @staticmethod
    def _map_tier_to_label(tier: str) -> ModelTierLabel:
        """Map tier name to tier label.

        Args:
            tier: Tier name ("fast", "balanced", "powerful")

        Returns:
            ModelTierLabel ("Q2", "Q3", "Q4")
        """
        tier_mapping = {"fast": "Q2", "balanced": "Q3", "powerful": "Q4"}
        return tier_mapping.get(tier.lower(), "Q2")  # type: ignore

    @staticmethod
    def _map_score_to_complexity(score: float) -> ComplexityLevel:
        """Map complexity score to complexity level.

        Args:
            score: Numerical complexity score

        Returns:
            ComplexityLevel ("SIMPLE", "MODERATE", "COMPLEX")
        """
        if score < 3.0:
            return "SIMPLE"
        elif score < 7.0:
            return "MODERATE"
        else:
            return "COMPLEX"


# Global singleton instance
_orchestrator_status_service: Optional[OrchestratorStatusService] = None


def get_orchestrator_status_service() -> OrchestratorStatusService:
    """Get or create the global orchestrator status service.

    Returns:
        OrchestratorStatusService singleton instance
    """
    global _orchestrator_status_service

    if _orchestrator_status_service is None:
        _orchestrator_status_service = OrchestratorStatusService(max_decisions=100)
        logger.info("Created global OrchestratorStatusService instance")

    return _orchestrator_status_service

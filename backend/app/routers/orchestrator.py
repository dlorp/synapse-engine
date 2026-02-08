"""Orchestrator status endpoints.

This module provides the API endpoint for retrieving real-time
orchestrator telemetry data including routing decisions, tier utilization,
and complexity distribution.
"""

from fastapi import APIRouter

from app.core.logging import get_logger
from app.models.orchestrator import OrchestratorStatusResponse
from app.services.orchestrator_status import get_orchestrator_status_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/orchestrator")


@router.get(
    "/status",
    response_model=OrchestratorStatusResponse,
    summary="Get orchestrator status",
    description="""
    Retrieve real-time orchestrator telemetry including:
    - Tier utilization metrics (Q2/Q3/Q4)
    - Recent routing decisions (up to 10)
    - Complexity distribution statistics
    - Average decision time
    - Total decisions processed

    This endpoint is designed for real-time visualization in the
    OrchestratorStatusPanel frontend component with 1-second polling.

    **Response Time Target:** <50ms
    """,
    responses={
        200: {
            "description": "Orchestrator status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "tierUtilization": [
                            {
                                "tier": "Q2",
                                "utilizationPercent": 75,
                                "activeRequests": 2,
                                "totalProcessed": 1250,
                            },
                            {
                                "tier": "Q3",
                                "utilizationPercent": 50,
                                "activeRequests": 1,
                                "totalProcessed": 680,
                            },
                            {
                                "tier": "Q4",
                                "utilizationPercent": 25,
                                "activeRequests": 0,
                                "totalProcessed": 320,
                            },
                        ],
                        "recentDecisions": [
                            {
                                "id": "dec-1234",
                                "query": "What is the current time?",
                                "tier": "Q2",
                                "complexity": "SIMPLE",
                                "timestamp": "2025-11-08T10:30:00Z",
                                "score": 1.2,
                            }
                        ],
                        "complexityDistribution": {
                            "simple": 45,
                            "moderate": 35,
                            "complex": 20,
                        },
                        "totalDecisions": 2250,
                        "avgDecisionTimeMs": 12.5,
                        "timestamp": "2025-11-08T10:35:00Z",
                    }
                }
            },
        }
    },
)
async def get_orchestrator_status() -> OrchestratorStatusResponse:
    """Get current orchestrator status.

    Returns real-time telemetry data from the orchestrator including
    routing decisions, tier utilization, and performance metrics.

    Returns:
        OrchestratorStatusResponse with complete telemetry data
    """
    service = get_orchestrator_status_service()
    status = service.get_status()

    logger.debug(
        "Orchestrator status retrieved",
        extra={
            "total_decisions": status.total_decisions,
            "avg_decision_time_ms": status.avg_decision_time_ms,
        },
    )

    return status

"""Context allocation endpoints for token budget visualization.

This module provides REST API endpoints for retrieving context window allocation
data for queries. Powers the Context Window Allocation Viewer feature in the
frontend.

The main endpoint returns detailed breakdown of token allocation across system
prompt, CGRAG context, user query, and response budget, along with CGRAG
artifact metadata.

Author: Backend Architect
Feature: Context Window Allocation Viewer
"""

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.context import ContextAllocation
from app.services.context_state import get_context_state_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get(
    "/allocation/{query_id}",
    response_model=ContextAllocation,
    summary="Get context allocation for a query",
    description="""
    Retrieve detailed context window allocation for a specific query.

    Returns token counts and percentages for each component:
    - System prompt (fixed instructions)
    - CGRAG context (retrieved artifacts)
    - User query (user's question)
    - Response budget (remaining tokens for generation)

    Also includes metadata about CGRAG artifacts with relevance scores
    and token contributions.
    """,
)
async def get_context_allocation(query_id: str) -> ContextAllocation:
    """Get context window allocation for a query.

    Args:
        query_id: Unique query identifier

    Returns:
        ContextAllocation with detailed token breakdown

    Raises:
        HTTPException(404): If query_id not found
        HTTPException(503): If context state manager not initialized

    Example Response:
        {
          "query_id": "550e8400-e29b-41d4-a716-446655440000",
          "model_id": "deepseek-r1:8b",
          "context_window_size": 8192,
          "total_tokens_used": 7200,
          "tokens_remaining": 992,
          "utilization_percentage": 87.9,
          "components": [
            {
              "component": "system_prompt",
              "tokens_used": 450,
              "tokens_allocated": 450,
              "percentage": 5.5,
              "content_preview": "You are a helpful AI assistant..."
            },
            {
              "component": "cgrag_context",
              "tokens_used": 6000,
              "tokens_allocated": 6000,
              "percentage": 73.2,
              "content_preview": "# Documentation..."
            },
            {
              "component": "user_query",
              "tokens_used": 250,
              "tokens_allocated": 250,
              "percentage": 3.1,
              "content_preview": "How does the CGRAG retrieval system work?"
            },
            {
              "component": "response_budget",
              "tokens_used": 0,
              "tokens_allocated": 1492,
              "percentage": 18.2,
              "content_preview": null
            }
          ],
          "cgrag_artifacts": [
            {
              "artifact_id": "doc_1",
              "source_file": "docs/architecture/cgrag.md",
              "relevance_score": 0.95,
              "token_count": 1500,
              "content_preview": "# CGRAG Architecture..."
            }
          ],
          "warning": "Context window >80% utilized - response may be truncated"
        }
    """
    try:
        # Get context state manager
        context_manager = get_context_state_manager()

        # Retrieve allocation
        allocation = await context_manager.get_allocation(query_id)

        if not allocation:
            logger.warning(
                f"Context allocation not found for query: {query_id}",
                extra={"query_id": query_id},
            )
            raise HTTPException(
                status_code=404,
                detail=f"Context allocation not found for query: {query_id}",
            )

        logger.info(
            f"Retrieved context allocation for query {query_id}",
            extra={
                "query_id": query_id,
                "model_id": allocation.model_id,
                "utilization": allocation.utilization_percentage,
            },
        )

        return allocation

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except RuntimeError as e:
        # Context state manager not initialized
        logger.error(f"Context state manager not initialized: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Context allocation service not available")

    except Exception as e:
        # Unexpected error
        logger.error(
            f"Error retrieving context allocation: {e}",
            extra={"query_id": query_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve context allocation: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Get context allocation statistics",
    description="""
    Retrieve statistics about context allocations across all queries.

    Provides aggregate metrics like total allocations tracked and
    average context window utilization.
    """,
)
async def get_context_stats() -> dict:
    """Get context allocation statistics.

    Returns aggregate statistics about all tracked context allocations.

    Returns:
        Dictionary with statistics:
        - total_allocations: Number of allocations currently tracked
        - avg_utilization_percentage: Average context window utilization

    Raises:
        HTTPException(503): If context state manager not initialized

    Example Response:
        {
          "total_allocations": 42,
          "avg_utilization_percentage": 68.5
        }
    """
    try:
        # Get context state manager
        context_manager = get_context_state_manager()

        # Get statistics
        stats = context_manager.get_stats()

        logger.debug(f"Retrieved context allocation stats: {stats}", extra=stats)

        return stats

    except RuntimeError as e:
        # Context state manager not initialized
        logger.error(f"Context state manager not initialized: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Context allocation service not available")

    except Exception as e:
        # Unexpected error
        logger.error(f"Error retrieving context stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context stats: {str(e)}")

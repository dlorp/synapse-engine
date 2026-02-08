"""Context allocation data models for token budget visualization.

This module defines Pydantic models for tracking and visualizing how context
window token budgets are allocated across different components (system prompt,
CGRAG context, user query, response budget).

These models power the Context Window Allocation Viewer feature in the frontend,
providing real-time visualization of token distribution and utilization.

Author: Backend Architect
Feature: Context Window Allocation Viewer
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ContextComponent(BaseModel):
    """Token allocation for a single context component.

    Represents how many tokens are used/allocated for one component of the
    context window (system prompt, CGRAG context, user query, or response budget).

    Attributes:
        component: Component identifier (system_prompt, cgrag_context, user_query, response_budget)
        tokens_used: Actual tokens used by this component
        tokens_allocated: Tokens allocated/reserved for this component
        percentage: Percentage of total context window (0-100)
        content_preview: Optional preview of component content (first 100 chars)

    Example:
        >>> component = ContextComponent(
        ...     component="system_prompt",
        ...     tokens_used=450,
        ...     tokens_allocated=450,
        ...     percentage=5.5,
        ...     content_preview="You are a helpful AI assistant..."
        ... )
    """

    component: str = Field(
        ...,
        description="Component identifier (system_prompt, cgrag_context, user_query, response_budget)",
    )
    tokens_used: int = Field(..., ge=0, description="Actual tokens used by this component")
    tokens_allocated: int = Field(
        ..., ge=0, description="Tokens allocated/reserved for this component"
    )
    percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of total context window (0-100)"
    )
    content_preview: Optional[str] = Field(
        None, description="Preview of component content (first 100 chars)"
    )


class CGRAGArtifact(BaseModel):
    """Information about a single CGRAG artifact in the context.

    Represents one retrieved document/chunk included in the context window,
    with metadata about its source, relevance, and token contribution.

    Attributes:
        artifact_id: Unique identifier for the artifact
        source_file: Original source file path
        relevance_score: Similarity score from FAISS retrieval (0.0-1.0)
        token_count: Number of tokens this artifact contributes
        content_preview: First 200 chars of artifact content

    Example:
        >>> artifact = CGRAGArtifact(
        ...     artifact_id="doc_1",
        ...     source_file="docs/architecture/cgrag.md",
        ...     relevance_score=0.95,
        ...     token_count=1500,
        ...     content_preview="# CGRAG Architecture\\n\\nThe Contextually-Guided..."
        ... )
    """

    artifact_id: str = Field(..., description="Unique identifier for the artifact")
    source_file: str = Field(..., description="Original source file path")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score from FAISS retrieval (0.0-1.0)",
    )
    token_count: int = Field(..., ge=0, description="Number of tokens this artifact contributes")
    content_preview: str = Field(..., description="First 200 chars of artifact content")


class ContextAllocation(BaseModel):
    """Complete context window allocation for a query.

    Aggregates all context components and CGRAG artifacts, providing a complete
    view of how the context window is utilized for a specific query. This is
    the main response model for the context allocation endpoint.

    Attributes:
        query_id: Unique identifier for the query
        model_id: Model identifier (e.g., deepseek-r1:8b)
        context_window_size: Model's maximum context window (e.g., 8192)
        total_tokens_used: Total tokens used across all components
        tokens_remaining: Tokens remaining for response generation
        utilization_percentage: Overall context window utilization (0-100)
        components: List of all context components with token allocations
        cgrag_artifacts: List of CGRAG artifacts included in context
        warning: Optional warning message (e.g., if >80% utilization)

    Example:
        >>> allocation = ContextAllocation(
        ...     query_id="550e8400-e29b-41d4-a716-446655440000",
        ...     model_id="deepseek-r1:8b",
        ...     context_window_size=8192,
        ...     total_tokens_used=7200,
        ...     tokens_remaining=992,
        ...     utilization_percentage=87.9,
        ...     components=[...],
        ...     cgrag_artifacts=[...],
        ...     warning="Context window >80% utilized - response may be truncated"
        ... )
    """

    query_id: str = Field(..., description="Unique identifier for the query")
    model_id: str = Field(..., description="Model identifier (e.g., deepseek-r1:8b)")
    context_window_size: int = Field(
        ..., gt=0, description="Model's maximum context window (e.g., 8192)"
    )
    total_tokens_used: int = Field(..., ge=0, description="Total tokens used across all components")
    tokens_remaining: int = Field(..., ge=0, description="Tokens remaining for response generation")
    utilization_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Overall context window utilization (0-100)"
    )
    components: List[ContextComponent] = Field(
        ..., description="List of all context components with token allocations"
    )
    cgrag_artifacts: List[CGRAGArtifact] = Field(
        default_factory=list, description="List of CGRAG artifacts included in context"
    )
    warning: Optional[str] = Field(
        None, description="Optional warning message (e.g., if >80% utilization)"
    )


class ContextAllocationRequest(BaseModel):
    """Request model for storing context allocation data.

    Used internally when query processing stores context allocation
    information for later retrieval. Not exposed as a public API endpoint.

    Attributes:
        query_id: Unique identifier for the query
        model_id: Model identifier
        system_prompt: System prompt text
        cgrag_context: Combined CGRAG context text
        user_query: User query text
        context_window_size: Model's maximum context window
        cgrag_artifacts: Optional list of CGRAG artifacts with metadata
    """

    query_id: str = Field(..., description="Unique identifier for the query")
    model_id: str = Field(..., description="Model identifier")
    system_prompt: str = Field(..., description="System prompt text")
    cgrag_context: str = Field(default="", description="Combined CGRAG context text")
    user_query: str = Field(..., description="User query text")
    context_window_size: int = Field(..., gt=0, description="Model's maximum context window")
    cgrag_artifacts: Optional[List[CGRAGArtifact]] = Field(
        None, description="Optional list of CGRAG artifacts with metadata"
    )

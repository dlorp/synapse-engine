"""Query request and response data models using Pydantic.

This module defines the data structures for query processing including
request validation, complexity assessment, and response formatting.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryMode(str, Enum):
    """Query processing modes for tier selection.

    Modes control how queries are routed to model tiers:
    - AUTO: Automatic complexity assessment determines tier
    - SIMPLE: Force routing to FAST tier (2B-7B models, fast extraction)
    - MODERATE: Force routing to BALANCED tier (8B-14B models, synthesis)
    - COMPLEX: Force routing to POWERFUL tier (>14B models, deep analysis)
    """
    AUTO = "auto"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryRequest(BaseModel):
    """Request model for POST /api/query endpoint.

    Attributes:
        query: User query text (1-10000 characters)
        mode: Processing mode (default: two-stage)
        use_context: Enable CGRAG context retrieval (default: True)
        use_web_search: Enable web search via SearXNG (default: False)
        max_tokens: Maximum tokens to generate (1-4096, default: 512)
        temperature: Sampling temperature (0.0-2.0, default: 0.7)
        council_adversarial: Use adversarial debate in council mode (default: False)
        benchmark_serial: Use serial execution in benchmark mode (default: False)

    Example:
        >>> request = QueryRequest(
        ...     query="What is Python?",
        ...     mode="two-stage",
        ...     max_tokens=256,
        ...     use_web_search=True
        ... )
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User query text"
    )
    mode: Literal["simple", "two-stage", "council", "benchmark"] = Field(
        default="two-stage",
        description="Query processing mode"
    )
    use_context: bool = Field(
        default=True,
        alias="useContext",
        description="Enable CGRAG context retrieval"
    )
    use_web_search: bool = Field(
        default=False,
        alias="useWebSearch",
        description="Enable web search via SearXNG"
    )
    max_tokens: int = Field(
        default=256,
        ge=1,
        le=4096,
        alias="maxTokens",
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation"
    )

    # Council mode configuration
    council_adversarial: bool = Field(
        default=False,
        alias="councilAdversarial",
        description="Use adversarial debate in council mode (vs consensus)"
    )

    council_profile: Optional[str] = Field(
        default=None,
        alias="councilProfile",
        description="Named profile for council model selection (e.g., 'fast-consensus', 'reasoning-debate')"
    )

    council_participants: Optional[List[str]] = Field(
        default=None,
        alias="councilParticipants",
        description="Explicit list of model IDs to use for council mode (overrides profile)"
    )

    # Multi-chat dialogue configuration
    council_max_turns: Optional[int] = Field(
        default=10,
        ge=2,
        le=20,
        alias="councilMaxTurns",
        description="Maximum dialogue turns (2-20). Default 10."
    )

    council_dynamic_termination: bool = Field(
        default=True,
        alias="councilDynamicTermination",
        description="End dialogue early if consensus/stalemate detected"
    )

    council_personas: Optional[Dict[str, str]] = Field(
        default=None,
        alias="councilPersonas",
        description="User-defined personas. Debate: {'pro': 'description', 'con': 'description'}. Consensus: {model_id: persona}"
    )

    council_persona_profile: Optional[str] = Field(
        default=None,
        alias="councilPersonaProfile",
        description="Named persona profile: 'classic', 'technical', 'business', 'scientific', 'ethical', 'political'"
    )

    council_moderator: bool = Field(
        default=False,
        alias="councilModerator",
        description="Enable moderator analysis after debate (post-debate analysis and summary)"
    )

    council_moderator_active: bool = Field(
        default=False,
        alias="councilModeratorActive",
        description="Enable active moderator interjections during debate (moderator can redirect if models go off-topic)"
    )

    council_moderator_model: Optional[str] = Field(
        default=None,
        alias="councilModeratorModel",
        description="Specific model ID for moderator analysis (optional, auto-selects most powerful model if not specified)"
    )

    council_moderator_check_frequency: int = Field(
        default=2,
        ge=1,
        le=10,
        alias="councilModeratorCheckFrequency",
        description="Number of turns between active moderator checks (default: 2). Only applies if councilModeratorActive=true."
    )

    # Debate mode model selection (adversarial only)
    council_pro_model: Optional[str] = Field(
        default=None,
        alias="councilProModel",
        description="Specific model ID for PRO position in debate mode (optional, requires councilConModel)"
    )

    council_con_model: Optional[str] = Field(
        default=None,
        alias="councilConModel",
        description="Specific model ID for CON position in debate mode (optional, requires councilProModel)"
    )

    # Benchmark mode configuration
    benchmark_serial: bool = Field(
        default=False,
        alias="benchmarkSerial",
        description="Execute models sequentially (vs parallel) to conserve VRAM"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "Explain async patterns in Python",
                "mode": "auto",
                "useContext": True,
                "maxTokens": 512,
                "temperature": 0.7
            }
        }
    )


class QueryComplexity(BaseModel):
    """Complexity assessment result from routing analysis.

    Contains the reasoning and scoring for query complexity
    assessment that determines model tier selection.

    Attributes:
        tier: Selected tier (fast, balanced, or powerful)
        score: Numerical complexity score
        reasoning: Human-readable explanation of tier selection
        indicators: Dictionary of detected complexity indicators

    Example:
        >>> complexity = QueryComplexity(
        ...     tier="balanced",
        ...     score=5.2,
        ...     reasoning="Moderate complexity - synthesis tier",
        ...     indicators={"has_comparison": True}
        ... )
    """
    tier: str = Field(
        ...,
        description="Selected tier: fast, balanced, or powerful"
    )
    score: float = Field(
        ...,
        description="Numerical complexity score"
    )
    reasoning: str = Field(
        ...,
        description="Human-readable explanation of tier selection"
    )
    indicators: dict = Field(
        default_factory=dict,
        description="Detected complexity indicators"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ArtifactInfo(BaseModel):
    """Information about a CGRAG artifact.

    Attributes:
        file_path: Path to source document
        relevance_score: Similarity score (0.0-1.0)
        chunk_index: Index of chunk within document
        token_count: Number of tokens in chunk
    """
    file_path: str = Field(..., alias="filePath", description="Source document path")
    relevance_score: float = Field(..., ge=0.0, le=1.0, alias="relevanceScore", description="Relevance score")
    chunk_index: int = Field(..., ge=0, alias="chunkIndex", description="Chunk index")
    token_count: int = Field(..., ge=0, alias="tokenCount", description="Token count")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class QueryMetadata(BaseModel):
    """Metadata about query processing and model invocation.

    Contains detailed information about how the query was processed,
    which model was used, and performance metrics.

    Attributes:
        model_tier: Tier used for processing (fast/balanced/powerful)
        model_id: Specific model instance identifier
        complexity: Complexity assessment (None if forced tier)
        tokens_used: Number of tokens generated
        processing_time_ms: Total processing time in milliseconds
        cgrag_artifacts: Number of CGRAG artifacts retrieved (future)
        cache_hit: Whether response was served from cache

    Example:
        >>> metadata = QueryMetadata(
        ...     model_tier="fast",
        ...     model_id="qwen_8b_fast",
        ...     tokens_used=128,
        ...     processing_time_ms=1850.2
        ... )
    """
    model_tier: str = Field(
        ...,
        alias="modelTier",
        description="Tier used for processing"
    )
    model_id: str = Field(
        ...,
        alias="modelId",
        description="Specific model instance identifier"
    )
    complexity: Optional[QueryComplexity] = Field(
        default=None,
        description="Complexity assessment result"
    )
    tokens_used: int = Field(
        default=0,
        alias="tokensUsed",
        description="Number of tokens generated"
    )
    processing_time_ms: float = Field(
        default=0.0,
        alias="processingTimeMs",
        description="Total processing time in milliseconds"
    )
    cgrag_artifacts: int = Field(
        default=0,
        alias="cgragArtifacts",
        description="Number of CGRAG artifacts retrieved"
    )
    cgrag_artifacts_info: List[ArtifactInfo] = Field(
        default_factory=list,
        alias="cgragArtifactsInfo",
        description="Detailed information about retrieved artifacts"
    )
    cache_hit: bool = Field(
        default=False,
        alias="cacheHit",
        description="Whether response was served from cache"
    )

    # Query mode
    query_mode: str = Field(
        default="simple",
        alias="queryMode",
        description="Query processing mode used"
    )

    # Two-stage workflow metadata
    stage1_response: Optional[str] = Field(
        default=None,
        alias="stage1Response",
        description="Stage 1 model response"
    )
    stage1_model_id: Optional[str] = Field(
        default=None,
        alias="stage1ModelId",
        description="Stage 1 model ID"
    )
    stage1_tier: Optional[str] = Field(
        default=None,
        alias="stage1Tier",
        description="Stage 1 tier"
    )
    stage1_processing_time: Optional[int] = Field(
        default=None,
        alias="stage1ProcessingTime",
        description="Stage 1 time (ms)"
    )
    stage1_tokens: Optional[int] = Field(
        default=None,
        alias="stage1Tokens",
        description="Stage 1 tokens generated"
    )
    stage2_model_id: Optional[str] = Field(
        default=None,
        alias="stage2ModelId",
        description="Stage 2 model ID"
    )
    stage2_tier: Optional[str] = Field(
        default=None,
        alias="stage2Tier",
        description="Stage 2 tier"
    )
    stage2_processing_time: Optional[int] = Field(
        default=None,
        alias="stage2ProcessingTime",
        description="Stage 2 time (ms)"
    )
    stage2_tokens: Optional[int] = Field(
        default=None,
        alias="stage2Tokens",
        description="Stage 2 tokens generated"
    )

    # Web search metadata
    web_search_results: Optional[List[dict]] = Field(
        default=None,
        alias="webSearchResults",
        description="Web search results from SearXNG"
    )
    web_search_time_ms: Optional[float] = Field(
        default=None,
        alias="webSearchTimeMs",
        description="Web search operation time (ms)"
    )
    web_search_count: int = Field(
        default=0,
        alias="webSearchCount",
        description="Number of web search results retrieved"
    )

    # Council mode metadata
    council_mode: Optional[Literal["consensus", "adversarial"]] = Field(
        default=None,
        alias="councilMode",
        description="Council mode type (consensus or adversarial)"
    )
    council_participants: Optional[List[str]] = Field(
        default=None,
        alias="councilParticipants",
        description="Model IDs participating in council"
    )
    council_rounds: Optional[int] = Field(
        default=None,
        alias="councilRounds",
        description="Number of deliberation rounds"
    )
    council_responses: Optional[List[dict]] = Field(
        default=None,
        alias="councilResponses",
        description="Per-model responses from council"
    )

    # Multi-chat dialogue metadata (true multi-chat mode)
    council_dialogue: Optional[bool] = Field(
        default=None,
        alias="councilDialogue",
        description="Flag indicating true multi-chat dialogue mode (vs parallel refinement)"
    )
    council_turns: Optional[List[dict]] = Field(
        default=None,
        alias="councilTurns",
        description="Sequential dialogue turns in multi-chat mode"
    )
    council_synthesis: Optional[str] = Field(
        default=None,
        alias="councilSynthesis",
        description="Final synthesis/summary of dialogue"
    )
    council_termination_reason: Optional[str] = Field(
        default=None,
        alias="councilTerminationReason",
        description="Reason dialogue ended (max_turns_reached, concession_detected, stalemate_repetition, etc.)"
    )
    council_total_turns: Optional[int] = Field(
        default=None,
        alias="councilTotalTurns",
        description="Total number of dialogue turns completed"
    )
    council_max_turns: Optional[int] = Field(
        default=None,
        alias="councilMaxTurns",
        description="Maximum turns configured for dialogue"
    )
    council_personas: Optional[Dict[str, str]] = Field(
        default=None,
        alias="councilPersonas",
        description="Persona assignments for dialogue participants"
    )

    # Moderator analysis metadata (council debate mode)
    council_moderator_analysis: Optional[str] = Field(
        default=None,
        alias="councilModeratorAnalysis",
        description="Comprehensive moderator analysis of debate (using LLM model)"
    )
    council_moderator_model: Optional[str] = Field(
        default=None,
        alias="councilModeratorModel",
        description="Model ID used for moderator analysis"
    )
    council_moderator_tokens: Optional[int] = Field(
        default=None,
        alias="councilModeratorTokens",
        description="Tokens used by moderator analysis"
    )
    council_moderator_thinking_steps: Optional[int] = Field(
        default=None,
        alias="councilModeratorThinkingSteps",
        description="Number of thinking steps used in moderator analysis (legacy, deprecated)"
    )
    council_moderator_breakdown: Optional[Dict] = Field(
        default=None,
        alias="councilModeratorBreakdown",
        description="Structured breakdown of moderator analysis (arguments, fallacies, etc.)"
    )
    council_moderator_interjections: Optional[int] = Field(
        default=None,
        alias="councilModeratorInterjections",
        description="Number of times moderator interjected during debate to redirect discussion"
    )

    # Benchmark mode metadata
    benchmark_results: Optional[List[dict]] = Field(
        default=None,
        alias="benchmarkResults",
        description="Results from benchmark comparison"
    )
    benchmark_execution_mode: Optional[Literal["parallel", "serial"]] = Field(
        default=None,
        alias="benchmarkExecutionMode",
        description="Benchmark execution mode (parallel or serial)"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class QueryResponse(BaseModel):
    """Response model for POST /api/query endpoint.

    Contains the query result, model output, and comprehensive
    metadata about the processing pipeline.

    Attributes:
        id: Unique query identifier (UUID)
        query: Original query text
        response: Model-generated response text
        metadata: Processing metadata and metrics
        timestamp: Response generation timestamp (UTC)

    Example:
        >>> response = QueryResponse(
        ...     id="550e8400-e29b-41d4-a716-446655440000",
        ...     query="What is Python?",
        ...     response="Python is a high-level programming language...",
        ...     metadata=metadata_object,
        ...     timestamp=datetime.utcnow()
        ... )
    """
    id: str = Field(
        ...,
        description="Unique query identifier (UUID)"
    )
    query: str = Field(
        ...,
        description="Original query text"
    )
    response: str = Field(
        ...,
        description="Model-generated response text"
    )
    metadata: QueryMetadata = Field(
        ...,
        description="Processing metadata and metrics"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response generation timestamp (UTC)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "What is Python?",
                "response": "Python is a high-level programming language...",
                "metadata": {
                    "modelTier": "fast",
                    "modelId": "qwen_8b_fast",
                    "complexity": {
                        "tier": "fast",
                        "score": 1.5,
                        "reasoning": "Simple query - fast extraction tier",
                        "indicators": {"token_count": 3}
                    },
                    "tokensUsed": 128,
                    "processingTimeMs": 1850.2,
                    "cgragArtifacts": 0,
                    "cacheHit": False
                },
                "timestamp": "2025-01-15T12:00:00Z"
            }
        }
    )

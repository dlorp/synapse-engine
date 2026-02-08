"""Query processing endpoints.

This module provides the main query endpoint that orchestrates the
complete query processing pipeline: complexity assessment, model
selection, and response generation.
"""

import asyncio
import json
import time
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.dependencies import (
    ConfigDependency,
    LoggerDependency,
    ModelManagerDependency,
)
from app.core.exceptions import (
    ModelNotFoundError,
    ModelUnavailableError,
    NoModelsAvailableError,
    QueryTimeoutError,
)
from app.models.context import (
    CGRAGArtifact as ContextCGRAGArtifact,
)
from app.models.context import (
    ContextAllocationRequest,
)
from app.models.discovered_model import ModelRegistry
from app.models.query import (
    ArtifactInfo,
    QueryComplexity,
    QueryMetadata,
    QueryRequest,
    QueryResponse,
)
from app.models.timeseries import MetricType
from app.services import runtime_settings as settings_service
from app.services.cgrag import CGRAGIndexer, CGRAGRetriever, get_cgrag_index_paths
from app.services.context_state import get_context_state_manager
from app.services.event_emitter import emit_cgrag_event, emit_query_route_event
from app.services.instance_manager import get_instance_manager
from app.services.llama_client import LlamaCppClient
from app.services.metrics_aggregator import get_metrics_aggregator
from app.services.model_selector import ModelSelector
from app.services.orchestrator_status import get_orchestrator_status_service
from app.services.pipeline_tracker import PipelineTracker
from app.services.routing import assess_complexity
from app.services.topology_manager import get_topology_manager
from app.services.websearch import get_searxng_client

router = APIRouter()

# Global service instances (initialized in main.py lifespan)
model_registry: Optional[ModelRegistry] = None
model_selector: Optional[ModelSelector] = None


async def store_context_allocation(
    query_id: str,
    model_id: str,
    system_prompt: str,
    cgrag_context: str,
    user_query: str,
    context_window_size: int,
    cgrag_artifacts: Optional[List] = None,
) -> None:
    """Store context allocation for a query.

    Helper function to store token allocation data for the Context Window
    Allocation Viewer. Can be called from any query processing mode.

    Args:
        query_id: Unique query identifier
        model_id: Model identifier used for generation
        system_prompt: System prompt text
        cgrag_context: Combined CGRAG context text
        user_query: User query text
        context_window_size: Model's maximum context window
        cgrag_artifacts: Optional list of CGRAG artifacts with metadata
    """
    try:
        # Get context state manager
        context_manager = get_context_state_manager()

        # Convert CGRAG artifacts to context format if provided
        context_artifacts = None
        if cgrag_artifacts:
            context_artifacts = [
                ContextCGRAGArtifact(
                    artifact_id=f"chunk_{artifact.chunk_index}",
                    source_file=artifact.file_path,
                    relevance_score=artifact.relevance_score,
                    token_count=artifact.token_count,
                    content_preview=artifact.content[:200] if hasattr(artifact, "content") else "",
                )
                for artifact in cgrag_artifacts
            ]

        # Create allocation request
        allocation_request = ContextAllocationRequest(
            query_id=query_id,
            model_id=model_id,
            system_prompt=system_prompt,
            cgrag_context=cgrag_context,
            user_query=user_query,
            context_window_size=context_window_size,
            cgrag_artifacts=context_artifacts,
        )

        # Store allocation
        await context_manager.store_allocation(allocation_request)

    except RuntimeError:
        # Context state manager not initialized - this is OK, just skip
        pass
    except Exception as e:
        # Log but don't fail the request
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.warning(
            f"Failed to store context allocation for query {query_id}: {e}",
            extra={"query_id": query_id, "error": str(e)},
        )


async def record_topology_flow(query_id: str, component_id: str) -> None:
    """Record query data flow through a system component.

    Helper function to record query traversal through system components
    for topology visualization. Silently fails if topology manager not available.

    Args:
        query_id: Unique query identifier
        component_id: Component identifier (orchestrator, cgrag_engine, model_id, etc.)
    """
    try:
        topology_manager = get_topology_manager()
        await topology_manager.record_data_flow(query_id, component_id)
    except RuntimeError:
        # Topology manager not initialized - this is OK, just skip
        pass
    except Exception as e:
        # Log but don't fail the request
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.debug(
            f"Failed to record topology flow for query {query_id}: {e}",
            extra={"query_id": query_id, "component_id": component_id},
        )


async def record_query_metrics(
    query_id: str,
    model_id: str,
    tier: str,
    query_mode: str,
    duration_ms: float,
    complexity_score: Optional[float] = None,
    tokens_generated: Optional[int] = None,
    cgrag_retrieval_time_ms: Optional[float] = None,
) -> None:
    """Record query metrics to the time-series aggregator.

    Helper function to record metrics after query completion for
    historical analysis and visualization.

    Args:
        query_id: Unique query identifier
        model_id: Model identifier used for generation
        tier: Tier (Q2, Q3, Q4)
        query_mode: Query mode (auto, simple, two-stage, council, etc.)
        duration_ms: Total query duration in milliseconds
        complexity_score: Optional complexity score
        tokens_generated: Optional token count
        cgrag_retrieval_time_ms: Optional CGRAG retrieval time
    """
    try:
        # Get metrics aggregator
        aggregator = get_metrics_aggregator()

        # Build metadata
        metadata = {
            "query_id": query_id,
            "model_id": model_id,
            "tier": tier,
            "query_mode": query_mode,
        }

        # Record response time
        await aggregator.record_metric(
            metric_name=MetricType.RESPONSE_TIME, value=duration_ms, metadata=metadata
        )

        # Record complexity score if available
        if complexity_score is not None:
            await aggregator.record_metric(
                metric_name=MetricType.COMPLEXITY_SCORE,
                value=complexity_score,
                metadata=metadata,
            )

        # Record tokens per second if available
        if tokens_generated is not None and duration_ms > 0:
            # Convert to tokens/sec
            tokens_per_sec = (tokens_generated / duration_ms) * 1000
            await aggregator.record_metric(
                metric_name=MetricType.TOKENS_PER_SECOND,
                value=tokens_per_sec,
                metadata=metadata,
            )

        # Record CGRAG retrieval time if available
        if cgrag_retrieval_time_ms is not None:
            await aggregator.record_metric(
                metric_name=MetricType.CGRAG_RETRIEVAL_TIME,
                value=cgrag_retrieval_time_ms,
                metadata=metadata,
            )

    except RuntimeError:
        # Metrics aggregator not initialized - this is OK, just skip
        pass
    except Exception as e:
        # Log but don't fail the request
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.warning(
            f"Failed to record metrics for query {query_id}: {e}",
            extra={"query_id": query_id, "error": str(e)},
        )


async def validate_models_available(model_ids: list[str], model_selector: ModelSelector) -> None:
    """Validate that specified models are available for debate.

    Args:
        model_ids: List of model IDs to validate
        model_selector: ModelSelector instance for checking availability

    Raises:
        HTTPException(404): If model not found in registry
        HTTPException(400): If model not enabled
        HTTPException(503): If model server not running
    """
    if not model_registry:
        raise HTTPException(status_code=503, detail="Model registry not available")

    for model_id in model_ids:
        # Check model exists in registry
        if model_id not in model_registry.models:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        model = model_registry.models[model_id]

        # Check model is enabled
        if not model.enabled:
            raise HTTPException(
                status_code=400,
                detail=f"Model not enabled: {model_id} ({model.display_name})",
            )

        # Check server is running
        server_manager = model_selector.server_manager
        if not server_manager.is_server_running(model_id):
            raise HTTPException(
                status_code=503,
                detail=f"Model server not running: {model_id} ({model.display_name})",
            )


async def auto_select_debate_participants(model_selector: ModelSelector) -> list[str]:
    """Auto-select 2 diverse models for debate.

    Prefers models from different tiers for more diverse perspectives.

    Args:
        model_selector: ModelSelector instance for selecting models

    Returns:
        List of 2 model IDs for PRO and CON positions

    Raises:
        HTTPException(400): If fewer than 2 models available
    """
    if not model_registry:
        raise HTTPException(status_code=503, detail="Model registry not available")

    # Get all enabled models
    enabled_models = [model for model in model_registry.models.values() if model.enabled]

    if len(enabled_models) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Debate mode requires at least 2 models, only {len(enabled_models)} available",
        )

    # Group models by tier
    tiers = defaultdict(list)
    for model in enabled_models:
        # Use tier_override if set, otherwise use assigned_tier
        tier = model.tier_override or model.assigned_tier
        tiers[tier.value if isinstance(tier, Enum) else tier].append(model.model_id)

    participants = []

    # Try to pick from different tiers for diversity
    if len(tiers) >= 2:
        tier_keys = list(tiers.keys())
        participants.append(tiers[tier_keys[0]][0])
        participants.append(tiers[tier_keys[1]][0])
    else:
        # Same tier, just pick first 2 enabled models
        participants = [m.model_id for m in enabled_models[:2]]

    return participants


async def _call_model_direct(
    model_id: str, prompt: str, max_tokens: int = 512, temperature: float = 0.7
) -> dict:
    """Call a model directly using LlamaCppClient.

    Args:
        model_id: Model identifier from registry
        prompt: Input prompt
        max_tokens: Max tokens to generate
        temperature: Sampling temperature

    Returns:
        Dict with 'content' key containing response text

    Raises:
        HTTPException: If model not found or call fails
    """
    if not model_registry:
        raise HTTPException(status_code=503, detail="Model registry not available")

    if model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    model = model_registry.models[model_id]

    # Create client for this model
    # Models are running on host machine
    # Docker on macOS: use host.docker.internal to reach host
    import platform

    if platform.system() == "Linux" and "microsoft" not in platform.release().lower():
        # Running in Docker on Linux (not WSL)
        host = "host.docker.internal"
    else:
        # Local development or WSL
        host = "host.docker.internal"

    base_url = f"http://{host}:{model.port}"
    client = LlamaCppClient(
        base_url=base_url,
        timeout=120,  # Longer timeout for generation
        max_retries=2,
    )

    try:
        result = await client.generate_completion(
            prompt=prompt, max_tokens=max_tokens, temperature=temperature
        )

        # Transform response to match expected format for dialogue_engine
        # dialogue_engine expects: {"content": str, "usage": {"total_tokens": int}}
        # LlamaCppClient returns: {"content": str, "tokens_predicted": int, "tokens_evaluated": int}
        return {
            "content": result.get("content", ""),
            "usage": {
                "total_tokens": result.get("tokens_predicted", 0)
                + result.get("tokens_evaluated", 0)
            },
        }
    finally:
        await client.close()


async def _process_consensus_mode(
    request: QueryRequest,
    model_manager,
    cgrag_context: str | None,
    complexity_score: float,
    query_id: str,
    config,
    logger,
) -> QueryResponse:
    """Process query using collaborative consensus approach.

    Workflow:
    1. Round 1: 3 models generate independent responses
    2. Round 2: Each model reviews others' responses and refines
    3. Synthesis: Most powerful model combines refined responses

    Args:
        request: Query request with parameters
        model_manager: Model manager instance
        cgrag_context: Retrieved context from CGRAG (computed here)
        complexity_score: Query complexity score (computed here)
        query_id: Unique query identifier
        config: Application configuration
        logger: Logger instance

    Returns:
        QueryResponse with consensus answer and metadata
    """
    time.time()

    # =================================================================
    # CGRAG & Web Search (reuse existing logic)
    # =================================================================
    # Build initial context with CGRAG and web search
    initial_prompt = request.query
    cgrag_artifacts = []
    web_search_results = []
    web_search_time_ms = 0.0

    # Web search (if enabled)
    if request.use_web_search:
        try:
            logger.info(f" Web search enabled for council query {query_id}")
            time.time()

            # Get SearXNG client
            import os

            searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
            max_results = int(os.getenv("WEBSEARCH_MAX_RESULTS", "5"))
            timeout = int(os.getenv("WEBSEARCH_TIMEOUT", "10"))

            searxng_client = get_searxng_client(
                base_url=searxng_url, timeout=timeout, max_results=max_results
            )

            # Execute search
            search_response = await searxng_client.search(request.query)
            web_search_results = search_response.results
            web_search_time_ms = search_response.search_time_ms

            logger.info(
                f"✓ Web search completed: {len(web_search_results)} results in {web_search_time_ms:.0f}ms",
                extra={"query_id": query_id, "results_count": len(web_search_results)},
            )

        except Exception as e:
            logger.warning(f" Web search failed for query {query_id}: {e}")

    # CGRAG retrieval
    cgrag_context_text = None
    if request.use_context:
        try:
            # Record topology flow - entering CGRAG engine
            await record_topology_flow(query_id, "cgrag_engine")

            # Determine path to FAISS index using runtime settings
            _, index_path, metadata_path = get_cgrag_index_paths("docs")

            # Check if index exists
            if index_path.exists() and metadata_path.exists():
                logger.debug(f"Loading CGRAG index for council query {query_id}")

                # Load CGRAG indexer
                cgrag_indexer = CGRAGIndexer.load_index(
                    index_path=index_path, metadata_path=metadata_path
                )

                # Validate embedding model consistency
                settings = settings_service.get_runtime_settings()
                is_valid, warning = cgrag_indexer.validate_embedding_model(
                    settings.embedding_model_name
                )
                if not is_valid:
                    logger.warning(warning, extra={"query_id": query_id})

                # Create retriever
                retriever = CGRAGRetriever(
                    indexer=cgrag_indexer,
                    min_relevance=config.cgrag.retrieval.min_relevance,
                )

                # Retrieve context
                cgrag_result = await retriever.retrieve(
                    query=request.query,
                    token_budget=config.cgrag.retrieval.token_budget,
                    max_artifacts=config.cgrag.retrieval.max_artifacts,
                )

                cgrag_artifacts = cgrag_result.artifacts

                logger.info(
                    f"Retrieved {len(cgrag_artifacts)} CGRAG artifacts for council query {query_id}",
                    extra={
                        "query_id": query_id,
                        "artifacts_count": len(cgrag_artifacts),
                    },
                )

                # Build context prompt
                if cgrag_artifacts:
                    context_sections = []
                    for chunk in cgrag_artifacts:
                        context_sections.append(
                            f"[Source: {chunk.file_path} (chunk {chunk.chunk_index})]\n{chunk.content}"
                        )
                    cgrag_context_text = "\n\n---\n\n".join(context_sections)

        except Exception as e:
            logger.warning(f"CGRAG retrieval failed for council query {query_id}: {e}")

    # Build context string for prompts
    context_string = ""
    if web_search_results:
        web_context = "\n\n".join(
            [
                f"[Web Result {i + 1}: {r.title}]\n{r.content}"
                for i, r in enumerate(web_search_results)
            ]
        )
        context_string += f"{web_context}\n\n---\n\n"

    if cgrag_context_text:
        context_string += f"{cgrag_context_text}\n\n---\n\n"

    context_string = context_string if context_string else ""

    # Build initial prompt with context
    if context_string:
        initial_prompt = f"{context_string}{request.query}"

    # =================================================================
    # SELECT 3 MODELS (prefer diverse tiers, but accept any 3)
    # =================================================================
    participants = []
    tried_tiers = []

    # Try to get models from different tiers (preferred)
    for tier in ["fast", "balanced", "powerful"]:
        try:
            if not model_selector:
                raise HTTPException(status_code=503, detail="Model selector not initialized")
            model = await model_selector.select_model(tier)
            participants.append(model.model_id)
            tried_tiers.append(tier)
            if len(participants) >= 3:
                break
        except Exception as e:
            logger.debug(f"No model available in {tier} tier: {e}")

    # If we don't have 3 models yet, get any additional enabled models from registry
    if len(participants) < 3:
        try:
            if model_registry:
                # Get all enabled models from registry
                for model_id, model in model_registry.models.items():
                    if model.enabled and model_id not in participants:
                        participants.append(model_id)
                        if len(participants) >= 3:
                            break
        except Exception as e:
            logger.warning(f"Failed to get additional models from registry: {e}")

    if len(participants) < 3:
        logger.error(f"Consensus mode requires 3 models, only found {len(participants)}")
        raise HTTPException(
            status_code=503,
            detail=f"Council consensus mode requires at least 3 enabled models (found {len(participants)})",
        )

    logger.info(f"Council participants: {participants}")

    # =================================================================
    # ROUND 1: Independent responses from all models
    # =================================================================
    logger.info(" Council Round 1: Initial independent responses")
    round1_start = time.time()

    round1_responses = {}
    round1_tasks = []

    for model_id in participants:
        task = _call_model_direct(
            model_id=model_id,
            prompt=initial_prompt,
            max_tokens=500,  # Limit Round 1 responses
            temperature=request.temperature,
        )
        round1_tasks.append((model_id, task))

    # Execute all Round 1 calls in parallel
    for model_id, task in round1_tasks:
        try:
            response = await task
            round1_responses[model_id] = response.get("content", "")
            logger.info(f"  ✓ {model_id}: {len(round1_responses[model_id])} chars")
        except Exception as e:
            logger.error(f"  ✗ {model_id} failed: {e}")
            # Continue with remaining models

    round1_time = int((time.time() - round1_start) * 1000)
    logger.info(
        f"Round 1 complete: {len(round1_responses)}/{len(participants)} models ({round1_time}ms)"
    )

    if len(round1_responses) < 2:
        raise HTTPException(
            status_code=500, detail="Consensus failed: Insufficient Round 1 responses"
        )

    # =================================================================
    # ROUND 2: Cross-review and refinement
    # =================================================================
    logger.info(" Council Round 2: Cross-review and refinement")
    round2_start = time.time()

    round2_responses = {}
    round2_tasks = []

    for model_id in round1_responses.keys():
        # Build cross-review prompt
        other_responses = "\n\n".join(
            [
                f"Model {other_id}'s response:\n{response}"
                for other_id, response in round1_responses.items()
                if other_id != model_id
            ]
        )

        refinement_prompt = f"""You are participating in a collaborative discussion to answer the following query:

Query: {request.query}

Your initial response:
{round1_responses[model_id]}

Other participants' responses:
{other_responses}

Review the other responses and refine your answer. You may:
- Incorporate good points from others
- Correct any errors you notice
- Add missing details
- Maintain your unique perspective while building consensus

Provide your refined response:"""

        task = _call_model_direct(
            model_id=model_id,
            prompt=refinement_prompt,
            max_tokens=700,  # Allow longer Round 2 responses
            temperature=request.temperature,
        )
        round2_tasks.append((model_id, task))

    # Execute Round 2 calls in parallel
    for model_id, task in round2_tasks:
        try:
            response = await task
            round2_responses[model_id] = response.get("content", "")
            logger.info(f"  ✓ {model_id} refined: {len(round2_responses[model_id])} chars")
        except Exception as e:
            logger.error(f"  ✗ {model_id} refinement failed: {e}")
            # Fallback to Round 1 response
            round2_responses[model_id] = round1_responses[model_id]

    round2_time = int((time.time() - round2_start) * 1000)
    logger.info(f"Round 2 complete: {len(round2_responses)} refinements ({round2_time}ms)")

    # =================================================================
    # SYNTHESIS: Combine refined responses into consensus
    # =================================================================
    logger.info("🎯 Synthesizing consensus answer")
    synthesis_start = time.time()

    # Use most powerful model for synthesis
    # Pick the last participant (likely most powerful) or first if all failed in Round 2
    synthesizer_model = participants[-1] if participants else list(round2_responses.keys())[0]

    all_refined = "\n\n".join(
        [
            f"Model {model_id}'s refined response:\n{response}"
            for model_id, response in round2_responses.items()
        ]
    )

    synthesis_prompt = f"""You are synthesizing multiple expert responses into a single consensus answer.

Original Query:
{request.query}

Expert Responses (after collaborative refinement):
{all_refined}

Your task:
1. Identify common themes and agreements across responses
2. Incorporate unique insights from each expert
3. Resolve any contradictions by favoring the most supported viewpoints
4. Provide a comprehensive, well-reasoned consensus answer
5. Maintain accuracy and completeness

Consensus Answer:"""

    try:
        consensus_result = await _call_model_direct(
            model_id=synthesizer_model,
            prompt=synthesis_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature * 0.8,  # Slightly lower temp for synthesis
        )
        consensus_answer = consensus_result.get("content", "")
        synthesis_time = int((time.time() - synthesis_start) * 1000)
        logger.info(f"✓ Consensus synthesized: {len(consensus_answer)} chars ({synthesis_time}ms)")
    except Exception as e:
        logger.error(f"Synthesis failed: {e}, falling back to best Round 2 response")
        # Fallback: Use longest/most detailed Round 2 response
        consensus_answer = max(round2_responses.values(), key=len)
        synthesis_time = 0

    total_time = round1_time + round2_time + synthesis_time

    # Build council metadata
    council_metadata = [
        {
            "model_id": model_id,
            "round1": round1_responses.get(model_id, ""),
            "round2": round2_responses.get(model_id, ""),
            "tokens": len(round2_responses.get(model_id, "").split()),
        }
        for model_id in participants
    ]

    # Build CGRAG artifact info
    cgrag_artifacts_info = []
    if cgrag_artifacts:
        cgrag_artifacts_info = [
            ArtifactInfo(
                file_path=chunk.file_path,
                relevance_score=chunk.relevance_score,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
            )
            for chunk in cgrag_artifacts
        ]

    # Build web search results metadata
    web_search_results_dict = None
    if web_search_results:
        web_search_results_dict = [
            {
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "engine": r.engine,
                "score": r.score,
                "published_date": r.published_date,
            }
            for r in web_search_results
        ]

    # Record metrics for time-series analysis
    await record_query_metrics(
        query_id=query_id,
        model_id=synthesizer_model,
        tier="council",
        query_mode="council",
        duration_ms=total_time,
        complexity_score=complexity_score,
    )

    return QueryResponse(
        id=query_id,
        query=request.query,
        response=consensus_answer,
        metadata=QueryMetadata(
            model_tier="council",
            model_id=synthesizer_model,  # Synthesis model
            processing_time_ms=total_time,
            complexity_score=complexity_score,
            cgrag_artifacts=len(cgrag_artifacts),
            cgrag_artifacts_info=cgrag_artifacts_info,
            query_mode="council",
            council_mode="consensus",
            council_participants=participants,
            council_rounds=2,
            council_responses=council_metadata,
            web_search_results=web_search_results_dict,
            web_search_time_ms=web_search_time_ms if web_search_time_ms > 0 else None,
            web_search_count=len(web_search_results),
            cache_hit=False,
            tokens_used=sum(len(r.split()) for r in round2_responses.values()),
        ),
    )


def get_participant_preset(
    role: str, default_preset_id: Optional[str], overrides: Optional[Dict[str, str]]
) -> Optional[str]:
    """Get effective preset for a council participant.

    Args:
        role: Participant role (pro, con, moderator)
        default_preset_id: Base preset from query request
        overrides: Per-participant override map

    Returns:
        Effective preset ID for this participant
    """
    if overrides and role in overrides:
        return overrides[role]
    return default_preset_id


def load_preset_system_prompt(preset_id: Optional[str]) -> str:
    """Load system prompt from preset configuration.

    Args:
        preset_id: Preset identifier

    Returns:
        System prompt string, or empty string if not found
    """
    if not preset_id:
        return ""

    try:
        presets_path = Path(__file__).parent.parent / "data" / "custom_presets.json"
        if presets_path.exists():
            with open(presets_path, "r") as f:
                presets = json.load(f)
            if preset_id in presets and "system_prompt" in presets[preset_id]:
                return presets[preset_id]["system_prompt"]
    except Exception as e:
        # Use module-level logger
        import logging

        logger_preset = logging.getLogger(__name__)
        logger_preset.warning(f"Failed to load preset {preset_id}: {e}")

    return ""


async def _process_debate_mode(
    request: QueryRequest,
    model_manager,
    cgrag_context: str | None,
    complexity_score: float,
    query_id: str,
    config,
    logger,
) -> QueryResponse:
    """Process query using adversarial debate with TRUE MULTI-CHAT dialogue.

    Uses DialogueEngine for sequential turn-based dialogue instead of
    parallel 2-round refinement.

    Workflow:
    1. Sequential turn-taking dialogue between two models
    2. Models directly address each other's points
    3. Dynamic termination on stalemate/concession or max turns
    4. Neutral model synthesizes final summary

    Args:
        request: Query request with parameters
        model_manager: Model manager instance
        cgrag_context: Retrieved context from CGRAG (computed here)
        complexity_score: Query complexity score (computed here)
        query_id: Unique query identifier
        config: Application configuration
        logger: Logger instance

    Returns:
        QueryResponse with debate dialogue and metadata
    """
    from app.services.dialogue_engine import dialogue_engine
    from app.services.persona_manager import persona_manager

    time.time()

    # =================================================================
    # CGRAG & Web Search (reuse existing logic - same as consensus)
    # =================================================================
    cgrag_artifacts = []
    web_search_results = []
    web_search_time_ms = 0.0

    # Web search (if enabled)
    if request.use_web_search:
        try:
            logger.info(f" Web search enabled for debate query {query_id}")
            time.time()

            # Get SearXNG client
            import os

            searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
            max_results = int(os.getenv("WEBSEARCH_MAX_RESULTS", "5"))
            timeout = int(os.getenv("WEBSEARCH_TIMEOUT", "10"))

            searxng_client = get_searxng_client(
                base_url=searxng_url, timeout=timeout, max_results=max_results
            )

            # Execute search
            search_response = await searxng_client.search(request.query)
            web_search_results = search_response.results
            web_search_time_ms = search_response.search_time_ms

            logger.info(
                f"✓ Web search completed: {len(web_search_results)} results in {web_search_time_ms:.0f}ms",
                extra={"query_id": query_id, "results_count": len(web_search_results)},
            )

        except Exception as e:
            logger.warning(f" Web search failed for debate query {query_id}: {e}")

    # CGRAG retrieval
    cgrag_context_text = None
    if request.use_context:
        try:
            # Determine path to FAISS index using runtime settings
            _, index_path, metadata_path = get_cgrag_index_paths("docs")

            # Check if index exists
            if index_path.exists() and metadata_path.exists():
                logger.debug(f"Loading CGRAG index for debate query {query_id}")

                # Load CGRAG indexer
                cgrag_indexer = CGRAGIndexer.load_index(
                    index_path=index_path, metadata_path=metadata_path
                )

                # Validate embedding model consistency
                settings = settings_service.get_runtime_settings()
                is_valid, warning = cgrag_indexer.validate_embedding_model(
                    settings.embedding_model_name
                )
                if not is_valid:
                    logger.warning(warning, extra={"query_id": query_id})

                # Create retriever
                retriever = CGRAGRetriever(
                    indexer=cgrag_indexer,
                    min_relevance=config.cgrag.retrieval.min_relevance,
                )

                # Retrieve context
                cgrag_result = await retriever.retrieve(
                    query=request.query,
                    token_budget=config.cgrag.retrieval.token_budget,
                    max_artifacts=config.cgrag.retrieval.max_artifacts,
                )

                cgrag_artifacts = cgrag_result.artifacts

                logger.info(
                    f"Retrieved {len(cgrag_artifacts)} CGRAG artifacts for debate query {query_id}",
                    extra={
                        "query_id": query_id,
                        "artifacts_count": len(cgrag_artifacts),
                    },
                )

                # Build context prompt
                if cgrag_artifacts:
                    context_sections = []
                    for chunk in cgrag_artifacts:
                        context_sections.append(
                            f"[Source: {chunk.file_path} (chunk {chunk.chunk_index})]\n{chunk.content}"
                        )
                    cgrag_context_text = "\n\n---\n\n".join(context_sections)

        except Exception as e:
            logger.warning(f"CGRAG retrieval failed for debate query {query_id}: {e}")

    # Build context string for prompts
    context_string = ""
    if web_search_results:
        web_context = "\n\n".join(
            [
                f"[Web Result {i + 1}: {r.title}]\n{r.content}"
                for i, r in enumerate(web_search_results)
            ]
        )
        context_string += f"{web_context}\n\n---\n\n"

    if cgrag_context_text:
        context_string += f"{cgrag_context_text}\n\n---\n\n"

    context_string = context_string if context_string else "No additional context"

    # =================================================================
    # SELECT 2 MODELS
    # =================================================================
    # Priority:
    # 1. User-specified pro/con models (council_pro_model + council_con_model)
    # 2. User-specified participants list (council_participants)
    # 3. Auto-select diverse models

    if request.council_pro_model and request.council_con_model:
        # User specified both PRO and CON models explicitly
        participants = [request.council_pro_model, request.council_con_model]
        logger.info(f"Using user-specified PRO/CON models: {participants}")

        # Validate both models are available
        if not model_selector:
            raise HTTPException(status_code=503, detail="Model selector not initialized")
        await validate_models_available(participants, model_selector)

    elif request.council_pro_model or request.council_con_model:
        # Error: Must specify both or neither
        raise HTTPException(
            status_code=400,
            detail="Must specify both councilProModel and councilConModel, or neither",
        )

    elif request.council_participants and len(request.council_participants) >= 2:
        # User specified participants list (legacy method)
        participants = request.council_participants[:2]
        logger.info(f"Using user-specified debate participants: {participants}")

    else:
        # Auto-select 2 diverse models
        if not model_selector:
            raise HTTPException(status_code=503, detail="Model selector not initialized")
        participants = await auto_select_debate_participants(model_selector)
        logger.info(f"Auto-selected debate participants: {participants}")

    logger.info(f" Debate participants: {participants[0]} (PRO) vs {participants[1]} (CON)")

    # =================================================================
    # GET PERSONAS
    # =================================================================
    personas = persona_manager.get_debate_personas(
        participants=participants,
        user_personas=request.council_personas,
        profile_name=request.council_persona_profile,
    )

    logger.info(f"Using personas: {personas}")

    # =================================================================
    # APPLY PRESET SYSTEM PROMPTS (if configured)
    # =================================================================
    # Get effective preset for PRO and CON participants
    pro_preset_id = get_participant_preset(
        "pro", request.preset_id, request.council_preset_overrides
    )
    con_preset_id = get_participant_preset(
        "con", request.preset_id, request.council_preset_overrides
    )

    # Load system prompts and prepend to personas
    if pro_preset_id:
        pro_system_prompt = load_preset_system_prompt(pro_preset_id)
        if pro_system_prompt and participants[0] in personas:
            personas[participants[0]] = f"{pro_system_prompt}\n\n{personas[participants[0]]}"
            logger.info(f"Applied preset {pro_preset_id} to PRO participant {participants[0]}")

    if con_preset_id:
        con_system_prompt = load_preset_system_prompt(con_preset_id)
        if con_system_prompt and participants[1] in personas:
            personas[participants[1]] = f"{con_system_prompt}\n\n{personas[participants[1]]}"
            logger.info(f"Applied preset {con_preset_id} to CON participant {participants[1]}")

    # =================================================================
    # DETERMINE MODERATOR MODEL (if active moderation enabled)
    # =================================================================
    moderator_model_for_interjections = None

    if request.council_moderator:
        # Use user-specified moderator model, or auto-select
        if request.council_moderator_model:
            moderator_model_for_interjections = request.council_moderator_model
            logger.info(
                f"Active moderator enabled with user-specified model: {moderator_model_for_interjections}"
            )
        else:
            # Auto-select moderator model (same logic as post-debate analysis)
            from app.services.moderator_analysis import _auto_select_moderator_model

            if model_selector:
                try:
                    moderator_model_for_interjections = _auto_select_moderator_model(model_selector)
                    logger.info(
                        f"Active moderator enabled with auto-selected model: {moderator_model_for_interjections}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to auto-select moderator model: {e} - disabling active moderation"
                    )
                    moderator_model_for_interjections = None

    # =================================================================
    # RUN DIALOGUE ENGINE
    # =================================================================
    logger.info(
        f"Starting debate dialogue: max {request.council_max_turns or 10} turns, dynamic_termination={request.council_dynamic_termination}"
    )
    dialogue_start = time.time()

    try:
        dialogue_result = await dialogue_engine.run_debate_dialogue(
            model_caller=_call_model_direct,
            participants=participants,
            query=request.query,
            personas=personas,
            context=context_string if context_string != "No additional context" else None,
            max_turns=request.council_max_turns or 10,
            dynamic_termination=request.council_dynamic_termination,
            temperature=request.temperature,
            max_tokens_per_turn=400,
            enable_active_moderator=request.council_moderator_active
            and moderator_model_for_interjections is not None,
            moderator_check_frequency=request.council_moderator_check_frequency,
            moderator_model=moderator_model_for_interjections,
            max_moderator_interjections=3,
        )
    except Exception as e:
        logger.error(f"Dialogue engine failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debate dialogue failed: {str(e)}")

    dialogue_time = int((time.time() - dialogue_start) * 1000)
    total_time = dialogue_time

    # Build CGRAG artifact info
    cgrag_artifacts_info = []
    if cgrag_artifacts:
        cgrag_artifacts_info = [
            ArtifactInfo(
                file_path=chunk.file_path,
                relevance_score=chunk.relevance_score,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
            )
            for chunk in cgrag_artifacts
        ]

    # Build web search results metadata
    web_search_results_dict = None
    if web_search_results:
        web_search_results_dict = [
            {
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "engine": r.engine,
                "score": r.score,
                "published_date": r.published_date,
            }
            for r in web_search_results
        ]

    logger.info(
        f"✓ Debate dialogue completed: {len(dialogue_result.turns)} turns, {dialogue_result.termination_reason}, {total_time}ms"
    )

    # =================================================================
    # MODERATOR ANALYSIS (if enabled)
    # =================================================================
    moderator_analysis_text = None
    moderator_model_id = None
    moderator_tokens_used = None
    moderator_breakdown = None

    if request.council_moderator:
        logger.info("🎓 Running moderator analysis with LLM model")
        moderator_start = time.time()

        try:
            from app.services.moderator_analysis import run_moderator_analysis

            # Validate moderator model if specified
            moderator_model_id_to_use = request.council_moderator_model

            if moderator_model_id_to_use:
                # Validate the specified moderator model
                if not model_selector:
                    raise HTTPException(status_code=503, detail="Model selector not initialized")
                await validate_models_available([moderator_model_id_to_use], model_selector)
                logger.info(f"Using user-specified moderator model: {moderator_model_id_to_use}")
            else:
                logger.info("Auto-selecting moderator model (prefers powerful tier)")

            # Run moderator analysis
            moderator_result = await run_moderator_analysis(
                dialogue_turns=dialogue_result.turns,
                query=request.query,
                synthesis=dialogue_result.synthesis,
                model_caller=_call_model_direct,
                model_selector=model_selector,
                model_id=moderator_model_id_to_use,
            )

            if moderator_result:
                moderator_analysis_text = moderator_result.analysis
                moderator_model_id = moderator_result.moderator_model
                moderator_tokens_used = moderator_result.tokens_used
                moderator_breakdown = moderator_result.breakdown

                moderator_time_ms = int((time.time() - moderator_start) * 1000)
                total_time += moderator_time_ms

                logger.info(
                    f"✓ Moderator analysis complete: {moderator_model_id} used {moderator_tokens_used} tokens in {moderator_time_ms}ms",
                    extra={
                        "query_id": query_id,
                        "moderator_model": moderator_model_id,
                        "tokens_used": moderator_tokens_used,
                        "analysis_time_ms": moderator_time_ms,
                    },
                )
            else:
                logger.warning("Moderator analysis returned no result")

        except Exception as e:
            logger.error(f"Moderator analysis failed: {e}", exc_info=True)
            # Continue without moderator analysis (graceful degradation)

    return QueryResponse(
        id=query_id,
        query=request.query,
        response=dialogue_result.synthesis,
        metadata=QueryMetadata(
            model_tier="council",
            model_id=f"{participants[0]} vs {participants[1]}",
            processing_time_ms=total_time,
            complexity_score=complexity_score,
            cgrag_artifacts=len(cgrag_artifacts),
            cgrag_artifacts_info=cgrag_artifacts_info,
            query_mode="council",
            council_mode="adversarial",
            council_participants=participants,
            # Multi-chat dialogue fields
            council_dialogue=True,
            council_turns=dialogue_result.to_dict()["turns"],
            council_synthesis=dialogue_result.synthesis,
            council_termination_reason=dialogue_result.termination_reason,
            council_total_turns=len(dialogue_result.turns),
            council_max_turns=request.council_max_turns or 10,
            council_personas=personas,
            # Moderator analysis fields
            council_moderator_analysis=moderator_analysis_text,
            council_moderator_model=moderator_model_id,
            council_moderator_tokens=moderator_tokens_used,
            council_moderator_thinking_steps=None,  # Legacy field, no longer used
            council_moderator_breakdown=moderator_breakdown,
            council_moderator_interjections=dialogue_result.moderator_interjection_count,
            # Legacy fields (for backwards compatibility)
            council_rounds=len(dialogue_result.turns),
            council_responses=None,  # Not used in dialogue mode
            web_search_results=web_search_results_dict,
            web_search_time_ms=web_search_time_ms if web_search_time_ms > 0 else None,
            web_search_count=len(web_search_results),
            cache_hit=False,
            tokens_used=dialogue_result.total_tokens,
        ),
    )


@router.post("/api/query", response_model=QueryResponse, response_model_by_alias=True)
async def process_query(
    request: QueryRequest,
    model_manager: ModelManagerDependency,
    config: ConfigDependency,
    logger: LoggerDependency,
) -> QueryResponse:
    """Process a user query through the model orchestration system.

    This endpoint implements mode-based query processing:

    TWO-STAGE MODE (default):
    1. Stage 1: FAST tier (b2-7) processes query with CGRAG context
    2. Stage 2: BALANCED (b8-14) or POWERFUL (>14B) refines Stage 1 response based on query complexity
    3. Returns refined response with both stages' metadata

    SIMPLE MODE:
    1. Single-model processing with FAST tier (b2-7) and optional CGRAG context
    2. Returns response from single tier

    Args:
        request: Query request with text and parameters
        model_manager: ModelManager instance (injected)
        config: Application configuration (injected)
        logger: Logger instance (injected)

    Returns:
        QueryResponse with model output and metadata

    Raises:
        HTTPException 503: No models available in selected tier
        HTTPException 504: Query processing timeout
        HTTPException 500: Internal server error

    Example:
        >>> # Two-stage query (default)
        >>> response = await client.post("/api/query", json={
        ...     "query": "What is Python?",
        ...     "mode": "two-stage"
        ... })
        >>> print(response.json()["metadata"]["query_mode"])
        'two-stage'

        >>> # Simple single-model query
        >>> response = await client.post("/api/query", json={
        ...     "query": "Explain async patterns",
        ...     "mode": "simple",
        ...     "max_tokens": 1024
        ... })
        >>> print(response.json()["metadata"]["query_mode"])
        'simple'
    """
    # 1. Generate unique query ID
    query_id = str(uuid4())
    start_time = time.time()

    logger.info(
        f"Processing query {query_id}",
        extra={
            "query_id": query_id,
            "mode": request.mode,
            "query_length": len(request.query),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        },
    )

    # Initialize pipeline tracker
    tracker = PipelineTracker(query_id)
    await tracker.create_pipeline()

    # Record topology flow - query entering orchestrator
    await record_topology_flow(query_id, "orchestrator")

    # ========================================================================
    # MULTI-INSTANCE SUPPORT: Lookup instance configuration if specified
    # ========================================================================
    instance_config = None
    instance_system_prompt = None
    if request.instance_id:
        try:
            instance_manager = get_instance_manager()
            instance_config = instance_manager.get_instance(request.instance_id)
            if instance_config:
                instance_system_prompt = instance_config.system_prompt
                logger.info(
                    f"Using instance {request.instance_id} for query {query_id}",
                    extra={
                        "query_id": query_id,
                        "instance_id": request.instance_id,
                        "has_system_prompt": bool(instance_system_prompt),
                        "instance_web_search": instance_config.web_search_enabled,
                    },
                )
            else:
                logger.warning(
                    f"Instance {request.instance_id} not found, continuing without instance config",
                    extra={"query_id": query_id, "instance_id": request.instance_id},
                )
        except Exception as e:
            logger.warning(
                f"Failed to lookup instance {request.instance_id}: {e}, continuing without instance config",
                extra={
                    "query_id": query_id,
                    "instance_id": request.instance_id,
                    "error": str(e),
                },
            )

    try:
        # ====================================================================
        # MODE-BASED QUERY ROUTING
        # ====================================================================

        query_mode = request.mode
        logger.info(f"Query mode: {query_mode}")

        if query_mode == "two-stage":
            # ================================================================
            # TWO-STAGE WORKFLOW
            # ================================================================
            logger.info(" Two-stage workflow selected")

            # STAGE 1: FAST tier (b2-7) with CGRAG context
            stage1_start = time.time()
            stage1_tier = "fast"

            try:
                if not model_selector:
                    raise HTTPException(status_code=503, detail="Model selector not initialized")
                stage1_model = await model_selector.select_model(stage1_tier)
                stage1_model_id = stage1_model.model_id
                logger.info(f"Stage 1 model selected: {stage1_model_id}")

                # Record topology flow - query routed to model
                await record_topology_flow(query_id, stage1_model_id)
            except Exception as e:
                logger.error(f"Failed to select Stage 1 model: {e}")
                raise HTTPException(
                    status_code=503, detail=f"No {stage1_tier} tier models available"
                )

            # Web search (if enabled)
            # Logic: Request overrides instance - if request enables, use it;
            # otherwise fall back to instance config if available
            web_search_results = []
            web_search_time_ms = 0.0
            effective_web_search = request.use_web_search or (
                instance_config is not None and instance_config.web_search_enabled
            )

            if effective_web_search:
                try:
                    logger.info(f" Web search enabled for query {query_id}")
                    time.time()

                    # Get SearXNG client
                    import os

                    searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
                    max_results = int(os.getenv("WEBSEARCH_MAX_RESULTS", "5"))
                    timeout = int(os.getenv("WEBSEARCH_TIMEOUT", "10"))

                    searxng_client = get_searxng_client(
                        base_url=searxng_url, timeout=timeout, max_results=max_results
                    )

                    # Execute search
                    search_response = await searxng_client.search(request.query)
                    web_search_results = search_response.results
                    web_search_time_ms = search_response.search_time_ms

                    logger.info(
                        f"✓ Web search completed: {len(web_search_results)} results in {web_search_time_ms:.0f}ms",
                        extra={
                            "query_id": query_id,
                            "results_count": len(web_search_results),
                            "search_time_ms": round(web_search_time_ms, 2),
                            "engines_used": search_response.engines_used,
                        },
                    )

                except Exception as e:
                    logger.warning(
                        f" Web search failed for query {query_id}: {e}, continuing without web results",
                        extra={
                            "query_id": query_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

            # CGRAG retrieval for Stage 1
            cgrag_artifacts = []
            cgrag_result = None
            cgrag_context_text = None  # Initialize to prevent unbound variable error
            # Default prompt (may be overwritten with context below)
            # Include instance system prompt if available
            if instance_system_prompt:
                stage1_full_prompt = f"{instance_system_prompt}\n\n{request.query}"
            else:
                stage1_full_prompt = request.query
            cgrag_start_time = time.time()

            if request.use_context:
                try:
                    # Determine path to FAISS index
                    project_root = Path(__file__).parent.parent.parent.parent
                    index_path = project_root / "data" / "faiss_indexes" / "docs.index"
                    metadata_path = project_root / "data" / "faiss_indexes" / "docs.metadata"

                    # Check if index exists
                    if index_path.exists() and metadata_path.exists():
                        logger.debug(f"Loading CGRAG index for query {query_id}")
                        index_load_start = time.time()

                        # Load CGRAG indexer
                        cgrag_indexer = CGRAGIndexer.load_index(
                            index_path=index_path, metadata_path=metadata_path
                        )

                        index_load_time_ms = (time.time() - index_load_start) * 1000
                        logger.info(
                            f"CGRAG index loaded in {index_load_time_ms:.1f}ms",
                            extra={
                                "query_id": query_id,
                                "load_time_ms": round(index_load_time_ms, 2),
                            },
                        )

                        # Validate embedding model consistency
                        settings = settings_service.get_runtime_settings()
                        is_valid, warning = cgrag_indexer.validate_embedding_model(
                            settings.embedding_model_name
                        )
                        if not is_valid:
                            logger.warning(warning, extra={"query_id": query_id})

                        # Create retriever
                        retriever = CGRAGRetriever(
                            indexer=cgrag_indexer,
                            min_relevance=config.cgrag.retrieval.min_relevance,
                        )

                        # Retrieve context
                        retrieval_start = time.time()
                        cgrag_result = await retriever.retrieve(
                            query=request.query,
                            token_budget=config.cgrag.retrieval.token_budget,
                            max_artifacts=config.cgrag.retrieval.max_artifacts,
                        )
                        retrieval_time_ms = (time.time() - retrieval_start) * 1000

                        cgrag_artifacts = cgrag_result.artifacts

                        logger.info(
                            f"Retrieved {len(cgrag_artifacts)} CGRAG artifacts for query {query_id}",
                            extra={
                                "query_id": query_id,
                                "artifacts_count": len(cgrag_artifacts),
                                "tokens_used": cgrag_result.tokens_used,
                                "retrieval_time_ms": round(retrieval_time_ms, 2),
                                "candidates_considered": cgrag_result.candidates_considered,
                                "total_cgrag_overhead_ms": round(
                                    (time.time() - cgrag_start_time) * 1000, 2
                                ),
                            },
                        )

                        # Emit CGRAG event for LiveEventFeed
                        await emit_cgrag_event(
                            query_id=query_id,
                            chunks_retrieved=len(cgrag_artifacts),
                            relevance_threshold=config.cgrag.retrieval.min_relevance,
                            retrieval_time_ms=int(retrieval_time_ms),
                            total_tokens=cgrag_result.tokens_used,
                            cache_hit=cgrag_result.cache_hit,
                        )

                        # Build context prompt (CGRAG artifacts)
                        if cgrag_artifacts:
                            context_sections = []
                            for chunk in cgrag_artifacts:
                                context_sections.append(
                                    f"[Source: {chunk.file_path} (chunk {chunk.chunk_index})]\n{chunk.content}"
                                )
                            cgrag_context_text = "\n\n---\n\n".join(context_sections)
                        else:
                            cgrag_context_text = None

                        logger.debug(
                            f"CGRAG context prepared for query {query_id}",
                            extra={
                                "query_id": query_id,
                                "cgrag_context_length": len(cgrag_context_text)
                                if cgrag_context_text
                                else 0,
                            },
                        )
                    else:
                        logger.warning(
                            f"CGRAG index not found for query {query_id}, continuing without context",
                            extra={
                                "query_id": query_id,
                                "index_path": str(index_path),
                                "metadata_path": str(metadata_path),
                            },
                        )

                except Exception as e:
                    logger.warning(
                        f"CGRAG retrieval failed for query {query_id}: {e}, continuing without context",
                        extra={
                            "query_id": query_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    cgrag_context_text = None

            # Build combined prompt with web search + CGRAG context
            context_parts = []

            # Add web search results first (most recent/relevant information)
            if web_search_results:
                web_search_sections = []
                for idx, result in enumerate(web_search_results, 1):
                    web_search_sections.append(
                        f"[Web Result {idx}: {result.title}]\nURL: {result.url}\n{result.content}"
                    )
                web_search_text = "\n\n---\n\n".join(web_search_sections)
                context_parts.append(f"Web Search Results:\n\n{web_search_text}")

            # Add CGRAG context second (local documentation)
            if cgrag_context_text:
                context_parts.append(f"Documentation Context:\n\n{cgrag_context_text}")

            # Build final prompt
            if context_parts:
                combined_context = "\n\n===\n\n".join(context_parts)
                # Include instance system prompt at the beginning if available
                system_prompt_section = ""
                if instance_system_prompt:
                    system_prompt_section = f"{instance_system_prompt}\n\n===\n\n"
                stage1_full_prompt = (
                    f"{system_prompt_section}"
                    f"{combined_context}\n\n"
                    f"===\n\n"
                    f"Question: {request.query}\n\n"
                    f"Answer the question based on the provided context. "
                    f"Use web search results for current/recent information and documentation for technical details. "
                    f"If the context doesn't contain relevant information, say so."
                )

                logger.info(
                    f"Built combined prompt for query {query_id}",
                    extra={
                        "query_id": query_id,
                        "has_web_results": len(web_search_results) > 0,
                        "has_cgrag": cgrag_context_text is not None,
                        "web_results_count": len(web_search_results),
                        "cgrag_artifacts_count": len(cgrag_artifacts),
                        "full_prompt_length": len(stage1_full_prompt),
                    },
                )
            else:
                # No context available, use query as-is
                logger.info(f"No context available for query {query_id}, using raw query")

            # Stage 1 model call
            try:
                logger.debug(f"Calling Stage 1 model {stage1_model_id}")
                stage1_result = await _call_model_direct(
                    model_id=stage1_model_id,
                    prompt=stage1_full_prompt,
                    max_tokens=500,  # Limited tokens for Stage 1
                    temperature=request.temperature,
                )
                stage1_time_ms = int((time.time() - stage1_start) * 1000)
                stage1_response = stage1_result.get("content", "")
                stage1_tokens = stage1_result.get("tokens_predicted", 0)

                logger.info(
                    f"✓ Stage 1 complete: {len(stage1_response)} chars in {stage1_time_ms}ms"
                )
            except Exception as e:
                logger.error(f"Stage 1 model call failed: {e}")
                raise HTTPException(status_code=500, detail=f"Stage 1 processing failed: {str(e)}")

            # STAGE 2: BALANCED or POWERFUL tier based on complexity
            stage2_start = time.time()

            # Assess query complexity to determine Stage 2 tier
            complexity_assessment_start = time.perf_counter()
            try:
                complexity = await assess_complexity(query=request.query, config=config.routing)
                # Select tier based on complexity (balanced for moderate, powerful for complex)
                if complexity.score >= config.routing.complexity_thresholds.get("powerful", 7.0):
                    stage2_tier = "powerful"
                else:
                    stage2_tier = "balanced"

                # Record routing decision for orchestrator telemetry
                decision_time_ms = (time.perf_counter() - complexity_assessment_start) * 1000
                orchestrator_service = get_orchestrator_status_service()
                orchestrator_service.record_routing_decision(
                    query=request.query,
                    tier=stage2_tier,
                    complexity_score=complexity.score,
                    decision_time_ms=decision_time_ms,
                )

                # Emit query routing event for LiveEventFeed
                tier_mapping = {"fast": "Q2", "balanced": "Q3", "powerful": "Q4"}
                estimated_latency_map = {
                    "fast": 2000,
                    "balanced": 5000,
                    "powerful": 15000,
                }
                await emit_query_route_event(
                    query_id=query_id,
                    complexity_score=complexity.score,
                    selected_tier=tier_mapping.get(stage2_tier, "Q3"),
                    estimated_latency_ms=estimated_latency_map.get(stage2_tier, 5000),
                    routing_reason=complexity.reasoning,
                )

                logger.info(
                    f"Stage 2 tier selected based on complexity: {stage2_tier} (score: {complexity.score:.2f})",
                    extra={
                        "query_id": query_id,
                        "complexity_score": complexity.score,
                        "stage2_tier": stage2_tier,
                    },
                )
            except Exception as e:
                logger.warning(f"Complexity assessment failed: {e}, defaulting to balanced tier")
                stage2_tier = "balanced"

            try:
                if not model_selector:
                    raise HTTPException(status_code=503, detail="Model selector not initialized")
                stage2_model = await model_selector.select_model(stage2_tier)
                stage2_model_id = stage2_model.model_id
                logger.info(f"Stage 2 model selected: {stage2_model_id}")

                # Record topology flow - query routed to stage 2 model
                await record_topology_flow(query_id, stage2_model_id)
            except Exception as e:
                logger.error(f"Failed to select Stage 2 model: {e}")
                raise HTTPException(
                    status_code=503, detail=f"No {stage2_tier} tier models available"
                )

            # Build Stage 2 refinement prompt
            stage2_prompt = f"""You are refining a response to improve its quality.

Original Query:
{request.query}

Initial Response (from Stage 1 model):
{stage1_response}

Instructions:
- Provide an improved, comprehensive response to the original query
- Expand on key points from the initial response
- Add depth, examples, and additional context
- Ensure accuracy and completeness
- Maintain a clear, professional tone

Refined Response:"""

            # Stage 2 model call
            try:
                logger.debug(f"Calling Stage 2 model {stage2_model_id}")
                stage2_result = await _call_model_direct(
                    model_id=stage2_model_id,
                    prompt=stage2_prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
                stage2_time_ms = int((time.time() - stage2_start) * 1000)
                stage2_response = stage2_result.get("content", "")
                stage2_tokens = stage2_result.get("tokens_predicted", 0)

                total_time_ms = stage1_time_ms + stage2_time_ms
                logger.info(
                    f"✓ Stage 2 complete: {len(stage2_response)} chars in {stage2_time_ms}ms "
                    f"(total: {total_time_ms}ms)"
                )
            except Exception as e:
                logger.error(f"Stage 2 model call failed: {e}")
                raise HTTPException(status_code=500, detail=f"Stage 2 processing failed: {str(e)}")

            # Build artifact info for metadata
            artifacts_info = []
            if cgrag_artifacts:
                for chunk in cgrag_artifacts:
                    # Count tokens for this chunk
                    token_count = int(len(chunk.content.split()) * 1.3)
                    artifacts_info.append(
                        ArtifactInfo(
                            file_path=chunk.file_path,
                            relevance_score=chunk.relevance_score,
                            chunk_index=chunk.chunk_index,
                            token_count=token_count,
                        )
                    )

            # Build response with two-stage metadata
            metadata = QueryMetadata(
                model_tier=stage2_tier,
                model_id=stage2_model_id,
                tokens_used=stage2_tokens,
                processing_time_ms=round(total_time_ms, 2),
                cgrag_artifacts=len(cgrag_artifacts),
                cgrag_artifacts_info=artifacts_info,
                cache_hit=cgrag_result.cache_hit if cgrag_result else False,
                query_mode="two-stage",
                stage1_response=stage1_response,
                stage1_model_id=stage1_model_id,
                stage1_tier=stage1_tier,
                stage1_processing_time=stage1_time_ms,
                stage1_tokens=stage1_tokens,
                stage2_model_id=stage2_model_id,
                stage2_tier=stage2_tier,
                stage2_processing_time=stage2_time_ms,
                stage2_tokens=stage2_tokens,
                # Web search metadata
                web_search_results=[
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.content,
                        "engine": r.engine,
                        "score": r.score,
                        "published_date": r.published_date,
                    }
                    for r in web_search_results
                ]
                if web_search_results
                else None,
                web_search_time_ms=web_search_time_ms if web_search_time_ms > 0 else None,
                web_search_count=len(web_search_results),
            )

            response = QueryResponse(
                id=query_id,
                query=request.query,
                response=stage2_response,
                metadata=metadata,
            )

            logger.info(
                f"Query {query_id} completed successfully (two-stage)",
                extra={
                    "query_id": query_id,
                    "stage1_model_id": stage1_model_id,
                    "stage2_model_id": stage2_model_id,
                    "total_tokens": stage1_tokens + stage2_tokens,
                    "processing_time_ms": total_time_ms,
                    "response_length": len(stage2_response),
                },
            )

            return response

        elif query_mode == "simple":
            # ================================================================
            # SIMPLE SINGLE-MODEL WORKFLOW (existing implementation)
            # ================================================================
            logger.info("🎯 Simple single-model workflow")

            # STAGE 1: INPUT
            async with tracker.stage("input") as metadata:
                metadata["query_length"] = len(request.query)
                metadata["mode"] = request.mode
                metadata["use_context"] = request.use_context
                metadata["use_web_search"] = request.use_web_search
                metadata["max_tokens"] = request.max_tokens

            # STAGE 2: COMPLEXITY ASSESSMENT
            async with tracker.stage("complexity") as metadata:
                # For simple mode, default to FAST tier (b2-7)
                tier = "fast"
                complexity = QueryComplexity(
                    tier=tier,
                    score=0.0,
                    reasoning="Simple mode - fast tier (2B-7B models)",
                    indicators={"forced": True, "mode": "simple"},
                )

                metadata["complexity_score"] = complexity.score
                metadata["tier"] = tier
                metadata["reasoning"] = complexity.reasoning

                # Record routing decision for orchestrator telemetry
                orchestrator_service = get_orchestrator_status_service()
                orchestrator_service.record_routing_decision(
                    query=request.query,
                    tier=tier,
                    complexity_score=complexity.score,
                    decision_time_ms=0.0,  # Simple mode has no complexity assessment overhead
                )

                # Emit query routing event for LiveEventFeed
                tier_mapping = {"fast": "Q2", "balanced": "Q3", "powerful": "Q4"}
                await emit_query_route_event(
                    query_id=query_id,
                    complexity_score=complexity.score,
                    selected_tier=tier_mapping.get(tier, "Q2"),
                    estimated_latency_ms=2000,  # Fast tier target
                    routing_reason=complexity.reasoning,
                )

                logger.info(
                    f"Query {query_id} using simple mode",
                    extra={"query_id": query_id, "tier": tier},
                )

            # STAGE 3: ROUTING (Model Selection)
            async with tracker.stage("routing") as metadata:
                # Select model from tier
                logger.debug(f"Selecting model for tier {tier}")
                if not model_selector:
                    raise HTTPException(status_code=503, detail="Model selector not initialized")
                model = await model_selector.select_model(tier)
                model_id = model.model_id

                # Record topology flow - query routed to model
                await record_topology_flow(query_id, model_id)

                metadata["model_selected"] = model_id
                metadata["model_port"] = model.port
                metadata["tier"] = tier

                logger.info(
                    f"Routing query {query_id} to {model_id}",
                    extra={"query_id": query_id, "model_id": model_id, "tier": tier},
                )

            # Web search (if enabled) - simple mode
            # Logic: Request overrides instance - if request enables, use it;
            # otherwise fall back to instance config if available
            web_search_results = []
            web_search_time_ms = 0.0
            effective_web_search = request.use_web_search or (
                instance_config is not None and instance_config.web_search_enabled
            )

            if effective_web_search:
                try:
                    logger.info(f" Web search enabled for query {query_id} (simple mode)")
                    time.time()

                    # Get SearXNG client
                    import os

                    searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
                    max_results = int(os.getenv("WEBSEARCH_MAX_RESULTS", "5"))
                    timeout = int(os.getenv("WEBSEARCH_TIMEOUT", "10"))

                    searxng_client = get_searxng_client(
                        base_url=searxng_url, timeout=timeout, max_results=max_results
                    )

                    # Execute search
                    search_response = await searxng_client.search(request.query)
                    web_search_results = search_response.results
                    web_search_time_ms = search_response.search_time_ms

                    logger.info(
                        f"✓ Web search completed: {len(web_search_results)} results in {web_search_time_ms:.0f}ms",
                        extra={
                            "query_id": query_id,
                            "results_count": len(web_search_results),
                            "search_time_ms": round(web_search_time_ms, 2),
                        },
                    )

                except Exception as e:
                    logger.warning(
                        f" Web search failed for query {query_id}: {e}",
                        extra={"query_id": query_id, "error": str(e)},
                    )

            # STAGE 4: CGRAG Retrieval (Context Gathering)
            cgrag_artifacts = []
            cgrag_result = None
            cgrag_context_text = None
            # Default prompt (may be overwritten with context below)
            # Include instance system prompt if available
            if instance_system_prompt:
                full_prompt = f"{instance_system_prompt}\n\n{request.query}"
            else:
                full_prompt = request.query
            cgrag_start_time = time.time()

            async with tracker.stage("cgrag") as cgrag_metadata:
                if not request.use_context:
                    cgrag_metadata["skipped"] = True
                    cgrag_metadata["reason"] = "use_context=False"
                elif request.use_context:
                    try:
                        # Determine path to FAISS index
                        project_root = Path(__file__).parent.parent.parent.parent
                        index_path = project_root / "data" / "faiss_indexes" / "docs.index"
                        metadata_path = project_root / "data" / "faiss_indexes" / "docs.metadata"

                        # Check if index exists
                        if index_path.exists() and metadata_path.exists():
                            logger.debug(f"Loading CGRAG index for query {query_id}")
                            index_load_start = time.time()

                            # Load CGRAG indexer
                            cgrag_indexer = CGRAGIndexer.load_index(
                                index_path=index_path, metadata_path=metadata_path
                            )

                            index_load_time_ms = (time.time() - index_load_start) * 1000
                            logger.info(
                                f"CGRAG index loaded in {index_load_time_ms:.1f}ms",
                                extra={
                                    "query_id": query_id,
                                    "load_time_ms": round(index_load_time_ms, 2),
                                },
                            )

                            # Validate embedding model consistency
                            settings = settings_service.get_runtime_settings()
                            is_valid, warning = cgrag_indexer.validate_embedding_model(
                                settings.embedding_model_name
                            )
                            if not is_valid:
                                logger.warning(warning, extra={"query_id": query_id})

                            # Create retriever
                            retriever = CGRAGRetriever(
                                indexer=cgrag_indexer,
                                min_relevance=config.cgrag.retrieval.min_relevance,
                            )

                            # Retrieve context
                            retrieval_start = time.time()
                            cgrag_result = await retriever.retrieve(
                                query=request.query,
                                token_budget=config.cgrag.retrieval.token_budget,
                                max_artifacts=config.cgrag.retrieval.max_artifacts,
                            )
                            retrieval_time_ms = (time.time() - retrieval_start) * 1000

                            cgrag_artifacts = cgrag_result.artifacts

                            # Populate pipeline metadata
                            cgrag_metadata["artifacts_retrieved"] = len(cgrag_artifacts)
                            cgrag_metadata["tokens_used"] = cgrag_result.tokens_used
                            cgrag_metadata["retrieval_time_ms"] = round(retrieval_time_ms, 2)
                            cgrag_metadata["cache_hit"] = cgrag_result.cache_hit

                            logger.info(
                                f"Retrieved {len(cgrag_artifacts)} CGRAG artifacts for query {query_id}",
                                extra={
                                    "query_id": query_id,
                                    "artifacts_count": len(cgrag_artifacts),
                                    "tokens_used": cgrag_result.tokens_used,
                                    "retrieval_time_ms": round(retrieval_time_ms, 2),
                                    "candidates_considered": cgrag_result.candidates_considered,
                                    "total_cgrag_overhead_ms": round(
                                        (time.time() - cgrag_start_time) * 1000, 2
                                    ),
                                },
                            )

                            # Emit CGRAG event for LiveEventFeed
                            await emit_cgrag_event(
                                query_id=query_id,
                                chunks_retrieved=len(cgrag_artifacts),
                                relevance_threshold=config.cgrag.retrieval.min_relevance,
                                retrieval_time_ms=int(retrieval_time_ms),
                                total_tokens=cgrag_result.tokens_used,
                                cache_hit=cgrag_result.cache_hit,
                            )

                            # Build context prompt (CGRAG artifacts)
                            if cgrag_artifacts:
                                context_sections = []
                                for chunk in cgrag_artifacts:
                                    context_sections.append(
                                        f"[Source: {chunk.file_path} (chunk {chunk.chunk_index})]\n{chunk.content}"
                                    )
                                cgrag_context_text = "\n\n---\n\n".join(context_sections)
                            else:
                                cgrag_context_text = None

                            logger.debug(
                                f"CGRAG context prepared for query {query_id} (simple mode)",
                                extra={
                                    "query_id": query_id,
                                    "cgrag_context_length": len(cgrag_context_text)
                                    if cgrag_context_text
                                    else 0,
                                },
                            )
                        else:
                            cgrag_metadata["skipped"] = True
                            cgrag_metadata["reason"] = "Index not found"
                            logger.warning(
                                f"CGRAG index not found for query {query_id}, continuing without context",
                                extra={
                                    "query_id": query_id,
                                    "index_path": str(index_path),
                                    "metadata_path": str(metadata_path),
                                },
                            )

                    except Exception as e:
                        cgrag_metadata["error"] = str(e)
                        logger.warning(
                            f"CGRAG retrieval failed for query {query_id}: {e}, continuing without context",
                            extra={
                                "query_id": query_id,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                        cgrag_context_text = None

            # Build combined prompt with web search + CGRAG context (simple mode)
            context_parts = []

            # Add web search results first
            if web_search_results:
                web_search_sections = []
                for idx, result in enumerate(web_search_results, 1):
                    web_search_sections.append(
                        f"[Web Result {idx}: {result.title}]\nURL: {result.url}\n{result.content}"
                    )
                web_search_text = "\n\n---\n\n".join(web_search_sections)
                context_parts.append(f"Web Search Results:\n\n{web_search_text}")

            # Add CGRAG context second
            if cgrag_context_text:
                context_parts.append(f"Documentation Context:\n\n{cgrag_context_text}")

            # Build final prompt
            if context_parts:
                combined_context = "\n\n===\n\n".join(context_parts)
                # Include instance system prompt at the beginning if available
                system_prompt_section = ""
                if instance_system_prompt:
                    system_prompt_section = f"{instance_system_prompt}\n\n===\n\n"
                full_prompt = (
                    f"{system_prompt_section}"
                    f"{combined_context}\n\n"
                    f"===\n\n"
                    f"Question: {request.query}\n\n"
                    f"Answer the question based on the provided context. "
                    f"Use web search results for current information and documentation for technical details. "
                    f"If the context doesn't contain relevant information, say so."
                )

                logger.info(
                    f"Built combined prompt for query {query_id} (simple mode)",
                    extra={
                        "query_id": query_id,
                        "has_web_results": len(web_search_results) > 0,
                        "has_cgrag": cgrag_context_text is not None,
                        "full_prompt_length": len(full_prompt),
                    },
                )
            else:
                # No context available, use query as-is
                logger.info(f"No context available for query {query_id}, using raw query")

            # STAGE 5: GENERATION (Model Inference)
            async with tracker.stage("generation") as gen_metadata:
                model_call_start = time.time()
                logger.debug(
                    f"Calling model {model_id} for query {query_id}",
                    extra={
                        "query_id": query_id,
                        "model_id": model_id,
                        "max_tokens": request.max_tokens,
                        "temperature": request.temperature,
                        "has_context": len(cgrag_artifacts) > 0,
                        "time_before_model_call_ms": round((time.time() - start_time) * 1000, 2),
                    },
                )

                result = await _call_model_direct(
                    model_id=model_id,
                    prompt=full_prompt,  # Use full_prompt with context
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

                # Calculate metrics
                model_call_time_ms = (time.time() - model_call_start) * 1000
                processing_time_ms = (time.time() - start_time) * 1000

                # Populate pipeline metadata
                gen_metadata["tokens_generated"] = result.get("tokens_predicted", 0)
                gen_metadata["response_length"] = len(result.get("content", ""))
                gen_metadata["model_call_time_ms"] = round(model_call_time_ms, 2)

                logger.info(
                    f"Query {query_id} timing breakdown",
                    extra={
                        "query_id": query_id,
                        "total_time_ms": round(processing_time_ms, 2),
                        "model_call_time_ms": round(model_call_time_ms, 2),
                        "overhead_ms": round(processing_time_ms - model_call_time_ms, 2),
                        "cgrag_enabled": request.use_context,
                        "tokens_generated": result.get("tokens_predicted", 0),
                    },
                )

            # STAGE 6: RESPONSE (Package Response)
            async with tracker.stage("response") as resp_metadata:
                # Build artifact info for metadata
                artifacts_info = []
                if cgrag_artifacts:
                    for chunk in cgrag_artifacts:
                        # Count tokens for this chunk
                        token_count = int(len(chunk.content.split()) * 1.3)
                        artifacts_info.append(
                            ArtifactInfo(
                                file_path=chunk.file_path,
                                relevance_score=chunk.relevance_score,
                                chunk_index=chunk.chunk_index,
                                token_count=token_count,
                            )
                        )

                # Build response with metadata
                metadata = QueryMetadata(
                    model_tier=tier,
                    model_id=model_id,
                    complexity=complexity,
                    tokens_used=result.get("tokens_predicted", 0),
                    processing_time_ms=round(processing_time_ms, 2),
                    cgrag_artifacts=len(cgrag_artifacts),
                    cgrag_artifacts_info=artifacts_info,
                    cache_hit=cgrag_result.cache_hit if cgrag_result else False,
                    query_mode="simple",
                    # Web search metadata
                    web_search_results=[
                        {
                            "title": r.title,
                            "url": r.url,
                            "content": r.content,
                            "engine": r.engine,
                            "score": r.score,
                            "published_date": r.published_date,
                        }
                        for r in web_search_results
                    ]
                    if web_search_results
                    else None,
                    web_search_time_ms=web_search_time_ms if web_search_time_ms > 0 else None,
                    web_search_count=len(web_search_results),
                )

                response = QueryResponse(
                    id=query_id,
                    query=request.query,
                    response=result.get("content", ""),
                    metadata=metadata,
                )

                resp_metadata["response_ready"] = True
                resp_metadata["total_tokens"] = metadata.tokens_used
                resp_metadata["processing_time_ms"] = metadata.processing_time_ms

                logger.info(
                    f"Query {query_id} completed successfully",
                    extra={
                        "query_id": query_id,
                        "model_id": model_id,
                        "tier": tier,
                        "tokens_generated": metadata.tokens_used,
                        "processing_time_ms": metadata.processing_time_ms,
                        "response_length": len(response.response),
                    },
                )

            # Mark pipeline as complete
            await tracker.complete_pipeline(
                model_selected=model_id,
                tier=tier,
                cgrag_artifacts_count=len(cgrag_artifacts),
            )

            return response

        elif query_mode == "council":
            # ================================================================
            # COUNCIL MODE: CONSENSUS OR ADVERSARIAL
            # ================================================================
            is_adversarial = request.council_adversarial
            logger.info(f" Council mode: {'Adversarial' if is_adversarial else 'Consensus'}")

            if is_adversarial:
                # Debate mode: 2 models, opposing arguments
                response = await _process_debate_mode(
                    request=request,
                    model_manager=model_manager,
                    cgrag_context=None,  # Will be computed inside
                    complexity_score=0.0,
                    query_id=query_id,
                    config=config,
                    logger=logger,
                )
            else:
                # Consensus mode: 3+ models, collaborative refinement
                response = await _process_consensus_mode(
                    request=request,
                    model_manager=model_manager,
                    cgrag_context=None,  # Will be computed inside
                    complexity_score=0.0,
                    query_id=query_id,
                    config=config,
                    logger=logger,
                )

            return response

        elif query_mode == "benchmark":
            # ================================================================
            # BENCHMARK MODE: SERIAL OR PARALLEL COMPARISON
            # ================================================================
            logger.info(
                f"🔬 Benchmark mode: {'serial' if request.benchmark_serial else 'parallel'}"
            )
            benchmark_start = time.time()

            # =================================================================
            # Phase A: Setup & Collect Models
            # =================================================================
            # Get runtime settings for VRAM estimation and defaults
            runtime_settings = settings_service.get_runtime_settings()

            # Collect all enabled models from registry
            if not model_registry:
                raise HTTPException(status_code=503, detail="Model registry not available")

            enabled_models = [
                model_id for model_id, model in model_registry.models.items() if model.enabled
            ]

            if not enabled_models:
                raise HTTPException(
                    status_code=503, detail="No enabled models available for benchmark"
                )

            logger.info(
                f" Benchmark: {len(enabled_models)} enabled models to test",
                extra={"query_id": query_id, "models": enabled_models},
            )

            # =================================================================
            # Phase B: Context & Prompt Building
            # =================================================================
            # Default prompt (may be overwritten with context below)
            # Include instance system prompt if available
            if instance_system_prompt:
                initial_prompt = f"{instance_system_prompt}\n\n{request.query}"
            else:
                initial_prompt = request.query
            cgrag_artifacts = []
            web_search_results = []

            # Web search (if enabled)
            # Logic: Request overrides instance
            effective_web_search = request.use_web_search or (
                instance_config is not None and instance_config.web_search_enabled
            )
            if effective_web_search:
                try:
                    logger.info(f" Web search enabled for benchmark query {query_id}")
                    time.time()

                    # Get SearXNG client
                    import os

                    searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
                    max_results = int(os.getenv("WEBSEARCH_MAX_RESULTS", "5"))
                    timeout = int(os.getenv("WEBSEARCH_TIMEOUT", "10"))

                    searxng_client = get_searxng_client(
                        base_url=searxng_url, timeout=timeout, max_results=max_results
                    )

                    # Execute search
                    search_response = await searxng_client.search(request.query)
                    web_search_results = search_response.results

                    logger.info(
                        f"✓ Web search completed: {len(web_search_results)} results",
                        extra={
                            "query_id": query_id,
                            "results_count": len(web_search_results),
                        },
                    )

                except Exception as e:
                    logger.warning(f" Web search failed for benchmark query {query_id}: {e}")

            # CGRAG retrieval (if enabled)
            cgrag_context_text = None
            if request.use_context:
                try:
                    # Determine path to FAISS index
                    project_root = Path(__file__).parent.parent.parent.parent
                    index_path = project_root / "data" / "faiss_indexes" / "docs.index"
                    metadata_path = project_root / "data" / "faiss_indexes" / "docs.metadata"

                    # Check if index exists
                    if index_path.exists() and metadata_path.exists():
                        logger.debug(f"Loading CGRAG index for benchmark query {query_id}")

                        # Load CGRAG indexer
                        cgrag_indexer = CGRAGIndexer.load_index(
                            index_path=index_path, metadata_path=metadata_path
                        )

                        # Validate embedding model consistency
                        settings = settings_service.get_runtime_settings()
                        is_valid, warning = cgrag_indexer.validate_embedding_model(
                            settings.embedding_model_name
                        )
                        if not is_valid:
                            logger.warning(warning, extra={"query_id": query_id})

                        # Create retriever
                        retriever = CGRAGRetriever(
                            indexer=cgrag_indexer,
                            min_relevance=config.cgrag.retrieval.min_relevance,
                        )

                        # Retrieve context
                        cgrag_result = await retriever.retrieve(
                            query=request.query,
                            token_budget=config.cgrag.retrieval.token_budget,
                            max_artifacts=config.cgrag.retrieval.max_artifacts,
                        )

                        cgrag_artifacts = cgrag_result.artifacts

                        logger.info(
                            f"Retrieved {len(cgrag_artifacts)} CGRAG artifacts for benchmark query {query_id}",
                            extra={
                                "query_id": query_id,
                                "artifacts_count": len(cgrag_artifacts),
                            },
                        )

                        # Build context prompt
                        if cgrag_artifacts:
                            context_sections = []
                            for chunk in cgrag_artifacts:
                                context_sections.append(
                                    f"[Source: {chunk.file_path} (chunk {chunk.chunk_index})]\n{chunk.content}"
                                )
                            cgrag_context_text = "\n\n---\n\n".join(context_sections)

                    else:
                        logger.warning(f"CGRAG index not found at {index_path}")

                except Exception as e:
                    logger.warning(f" CGRAG retrieval failed for benchmark query {query_id}: {e}")

            # Build final prompt with web search and CGRAG context
            # Build final prompt with context (include system prompt at beginning)
            system_prompt_section = ""
            if instance_system_prompt:
                system_prompt_section = f"{instance_system_prompt}\n\n===\n\n"

            if web_search_results:
                web_context = "\n\n".join(
                    [
                        f"[{i + 1}] {result.title}\n{result.snippet}\nSource: {result.url}"
                        for i, result in enumerate(web_search_results)
                    ]
                )
                initial_prompt = f"{system_prompt_section}Web Search Results:\n{web_context}\n\nQuestion: {request.query}"
            elif instance_system_prompt:
                # If only system prompt (no web results), still prepend it
                initial_prompt = f"{system_prompt_section}Question: {request.query}"

            if cgrag_context_text:
                # Prepend CGRAG context (after system prompt if present)
                if instance_system_prompt and not web_search_results:
                    initial_prompt = f"{system_prompt_section}Context:\n{cgrag_context_text}\n\nQuestion: {request.query}"
                else:
                    initial_prompt = f"Context:\n{cgrag_context_text}\n\n{initial_prompt}"

            # =================================================================
            # Phase C: Model Execution
            # =================================================================
            benchmark_results = []
            execution_mode = "serial" if request.benchmark_serial else "parallel"

            if request.benchmark_serial:
                # SERIAL MODE: Execute models one at a time (VRAM-safe)
                logger.info(" Benchmark: Serial execution mode (VRAM-safe)")

                for model_id in enabled_models:
                    model = model_registry.models[model_id]
                    model_start = time.time()

                    try:
                        # Call model
                        result = await _call_model_direct(
                            model_id=model_id,
                            prompt=initial_prompt,
                            max_tokens=runtime_settings.benchmark_default_max_tokens,
                            temperature=request.temperature,
                        )

                        response_text = result.get("content", "")
                        response_time_ms = int((time.time() - model_start) * 1000)

                        # Estimate VRAM usage (handle both string and enum quantization values)
                        if model.quantization:
                            quantization_str = (
                                model.quantization.upper()
                                if isinstance(model.quantization, str)
                                else model.quantization.value.upper()
                            )
                        else:
                            quantization_str = "Q4_K_M"
                        estimated_vram = runtime_settings.estimate_vram_per_model(
                            model_size_b=model.size_params or 8.0,
                            quantization=quantization_str,
                        )

                        # Extract metadata from result
                        token_count = result.get("tokens_generated", len(response_text.split()))
                        char_count = len(response_text)

                        benchmark_results.append(
                            {
                                "model_id": model_id,
                                "model_tier": model.tier or "unknown",
                                "response": response_text,
                                "response_time_ms": response_time_ms,
                                "token_count": token_count,
                                "char_count": char_count,
                                "success": True,
                                "error": None,
                                "estimated_vram_gb": estimated_vram,
                                "gpu_layers_used": runtime_settings.n_gpu_layers,
                                "context_window_used": runtime_settings.ctx_size,
                            }
                        )

                        logger.info(
                            f"✓ Benchmark: {model_id} completed in {response_time_ms}ms",
                            extra={
                                "query_id": query_id,
                                "model_id": model_id,
                                "time_ms": response_time_ms,
                            },
                        )

                    except Exception as e:
                        response_time_ms = int((time.time() - model_start) * 1000)
                        logger.error(
                            f"✗ Benchmark: {model_id} failed: {e}",
                            extra={"query_id": query_id, "model_id": model_id},
                        )

                        # Record failure
                        benchmark_results.append(
                            {
                                "model_id": model_id,
                                "model_tier": model.tier or "unknown",
                                "response": "",
                                "response_time_ms": response_time_ms,
                                "token_count": 0,
                                "char_count": 0,
                                "success": False,
                                "error": str(e),
                                "estimated_vram_gb": 0.0,
                                "gpu_layers_used": 0,
                                "context_window_used": 0,
                            }
                        )

            else:
                # PARALLEL MODE: Execute in batches (faster but VRAM-intensive)
                logger.info(" Benchmark: Parallel execution mode (fast)")
                batch_size = runtime_settings.benchmark_parallel_max_models

                # Process models in batches
                for i in range(0, len(enabled_models), batch_size):
                    batch = enabled_models[i : i + batch_size]
                    batch_start = time.time()

                    logger.info(
                        f" Benchmark batch {i // batch_size + 1}: {len(batch)} models",
                        extra={"query_id": query_id, "batch": batch},
                    )

                    # Create tasks for all models in batch
                    tasks = []
                    for model_id in batch:
                        task = _call_model_direct(
                            model_id=model_id,
                            prompt=initial_prompt,
                            max_tokens=runtime_settings.benchmark_default_max_tokens,
                            temperature=request.temperature,
                        )
                        tasks.append(task)

                    # Execute batch in parallel
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results
                    for model_id, result in zip(batch, results):
                        model = model_registry.models[model_id]

                        if isinstance(result, Exception):
                            # Model failed
                            logger.error(
                                f"✗ Benchmark: {model_id} failed: {result}",
                                extra={"query_id": query_id, "model_id": model_id},
                            )

                            benchmark_results.append(
                                {
                                    "model_id": model_id,
                                    "model_tier": model.tier or "unknown",
                                    "response": "",
                                    "response_time_ms": int((time.time() - batch_start) * 1000),
                                    "token_count": 0,
                                    "char_count": 0,
                                    "success": False,
                                    "error": str(result),
                                    "estimated_vram_gb": 0.0,
                                    "gpu_layers_used": 0,
                                    "context_window_used": 0,
                                }
                            )

                        else:
                            # Model succeeded
                            response_text = result.get("content", "")
                            token_count = result.get("tokens_generated", len(response_text.split()))
                            char_count = len(response_text)

                            # Estimate VRAM (handle both string and enum quantization values)
                            if model.quantization:
                                quantization_str = (
                                    model.quantization.upper()
                                    if isinstance(model.quantization, str)
                                    else model.quantization.value.upper()
                                )
                            else:
                                quantization_str = "Q4_K_M"
                            estimated_vram = runtime_settings.estimate_vram_per_model(
                                model_size_b=model.size_params or 8.0,
                                quantization=quantization_str,
                            )

                            # Note: In parallel mode, we don't have individual timing
                            # Use batch time as approximation
                            response_time_ms = int((time.time() - batch_start) * 1000)

                            benchmark_results.append(
                                {
                                    "model_id": model_id,
                                    "model_tier": model.tier or "unknown",
                                    "response": response_text,
                                    "response_time_ms": response_time_ms,
                                    "token_count": token_count,
                                    "char_count": char_count,
                                    "success": True,
                                    "error": None,
                                    "estimated_vram_gb": estimated_vram,
                                    "gpu_layers_used": runtime_settings.n_gpu_layers,
                                    "context_window_used": runtime_settings.ctx_size,
                                }
                            )

                            logger.info(
                                f"✓ Benchmark: {model_id} completed",
                                extra={"query_id": query_id, "model_id": model_id},
                            )

            # =================================================================
            # Phase D: Results Processing & Summary
            # =================================================================
            # Calculate metrics
            successful_results = [r for r in benchmark_results if r["success"]]
            failed_results = [r for r in benchmark_results if not r["success"]]

            if not successful_results:
                # All models failed
                raise HTTPException(
                    status_code=500,
                    detail=f"All {len(enabled_models)} models failed during benchmark",
                )

            # Timing metrics
            total_time_ms = int((time.time() - benchmark_start) * 1000)
            response_times = [r["response_time_ms"] for r in successful_results]
            fastest_time = min(response_times)
            slowest_time = max(response_times)
            avg_time = sum(response_times) // len(response_times)

            # Find fastest/slowest models
            fastest_result = min(successful_results, key=lambda r: r["response_time_ms"])
            slowest_result = max(successful_results, key=lambda r: r["response_time_ms"])

            # Token metrics
            total_tokens = sum(r["token_count"] for r in successful_results)

            # Build detailed comparison text
            comparison_sections = []

            for result in benchmark_results:
                status_emoji = "✓" if result["success"] else "✗"
                if result["success"]:
                    section = f"""
{status_emoji} {result["model_id"]} (Tier: {result["model_tier"]})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Response Time: {result["response_time_ms"]}ms
Tokens Generated: {result["token_count"]}
Characters: {result["char_count"]}
Estimated VRAM: {result["estimated_vram_gb"]} GB
GPU Layers: {result["gpu_layers_used"]}
Context Window: {result["context_window_used"]}

Response:
{result["response"]}
"""
                else:
                    section = f"""
{status_emoji} {result["model_id"]} (Tier: {result["model_tier"]})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERROR: {result["error"]}
Time to failure: {result["response_time_ms"]}ms
"""
                comparison_sections.append(section)

            detailed_comparison = "\n".join(comparison_sections)

            # Build summary text
            summary = f"""╔══════════════════════════════════════════════════════════════╗
║              BENCHMARK RESULTS - {execution_mode.upper()} MODE              ║
╚══════════════════════════════════════════════════════════════╝

EXECUTION SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Models Tested: {len(enabled_models)}
• Successful: {len(successful_results)}
• Failed: {len(failed_results)}
• Execution Mode: {"Parallel (fast, high VRAM)" if not request.benchmark_serial else "Serial (VRAM-safe, slower)"}
• Total Benchmark Time: {total_time_ms}ms ({total_time_ms / 1000:.2f}s)

PERFORMANCE METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Fastest: {fastest_result["model_id"]} ({fastest_time}ms)
🐌 Slowest: {slowest_result["model_id"]} ({slowest_time}ms)
 Average: {avg_time}ms
📝 Total Tokens: {total_tokens}

DETAILED COMPARISON:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{detailed_comparison}

╔══════════════════════════════════════════════════════════════╗
║                      END OF BENCHMARK                        ║
╚══════════════════════════════════════════════════════════════╝
"""

            # =================================================================
            # Phase E: Return QueryResponse
            # =================================================================
            # Convert CGRAG artifacts to ArtifactInfo
            cgrag_artifacts_info = [
                ArtifactInfo(
                    file_path=chunk.file_path,
                    chunk_index=chunk.chunk_index,
                    relevance_score=chunk.relevance_score,
                    token_count=chunk.token_count,
                )
                for chunk in cgrag_artifacts
            ]

            # Build metadata
            metadata = QueryMetadata(
                model_tier="benchmark",
                model_id=fastest_result["model_id"],  # Primary model is fastest
                complexity=None,
                tokens_used=total_tokens,
                processing_time_ms=total_time_ms,
                cgrag_artifacts=len(cgrag_artifacts),
                cgrag_artifacts_info=cgrag_artifacts_info,
                cache_hit=False,
                query_mode="benchmark",
                benchmark_results=benchmark_results,
                benchmark_execution_mode=execution_mode,
            )

            logger.info(
                f"✓ Benchmark completed: {len(successful_results)}/{len(enabled_models)} models succeeded in {total_time_ms}ms",
                extra={
                    "query_id": query_id,
                    "total_models": len(enabled_models),
                    "successful": len(successful_results),
                    "failed": len(failed_results),
                    "total_time_ms": total_time_ms,
                },
            )

            return QueryResponse(
                id=query_id, query=request.query, response=summary, metadata=metadata
            )

        else:
            # ================================================================
            # UNKNOWN MODE
            # ================================================================
            raise HTTPException(
                status_code=400,
                detail=f"Query mode '{query_mode}' not recognized. Available modes: simple, two-stage, council, benchmark",
            )

    except NoModelsAvailableError as e:
        # No healthy models in the requested tier
        tier_name = e.tier if hasattr(e, "tier") else "unknown"
        await tracker.fail_pipeline(f"No models available in {tier_name} tier")
        logger.error(
            f"No models available for query {query_id} in tier {tier_name}",
            extra={"query_id": query_id, "tier": tier_name, "error": str(e)},
        )

        raise HTTPException(
            status_code=503,
            detail={
                "error": "no_models_available",
                "message": f"No healthy models available in tier {tier_name}",
                "tier": tier_name,
                "available_tiers": e.details.get("available_tiers", []),
            },
        )

    except ModelNotFoundError as e:
        # Model ID doesn't exist (should not happen in normal flow)
        await tracker.fail_pipeline(f"Model not found: {e.model_id}")
        logger.error(
            f"Model not found for query {query_id}: {e}",
            extra={"query_id": query_id, "model_id": e.model_id, "error": str(e)},
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "model_not_found",
                "message": "Internal error: selected model not found",
                "model_id": e.model_id,
            },
        )

    except ModelUnavailableError as e:
        # Model exists but is unhealthy
        await tracker.fail_pipeline(f"Model unavailable: {e.reason}")
        logger.error(
            f"Model unavailable for query {query_id}: {e}",
            extra={
                "query_id": query_id,
                "model_id": e.model_id,
                "reason": e.reason,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=503,
            detail={
                "error": "model_unavailable",
                "message": f"Selected model is unavailable: {e.reason}",
                "model_id": e.model_id,
            },
        )

    except QueryTimeoutError as e:
        # Query processing exceeded timeout
        await tracker.fail_pipeline(f"Query timeout: {e.timeout_seconds}s")
        logger.error(
            f"Query {query_id} timed out",
            extra={
                "query_id": query_id,
                "model_id": e.model_id,
                "timeout_seconds": e.timeout_seconds,
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=504,
            detail={
                "error": "query_timeout",
                "message": f"Query processing timed out after {e.timeout_seconds}s",
                "timeout_seconds": e.timeout_seconds,
                "model_id": e.model_id,
            },
        )

    except Exception as e:
        # Unexpected error
        await tracker.fail_pipeline(f"Unexpected error: {str(e)}")
        logger.error(
            f"Unexpected error processing query {query_id}: {e}",
            extra={
                "query_id": query_id,
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while processing the query",
                "query_id": query_id,
            },
        )

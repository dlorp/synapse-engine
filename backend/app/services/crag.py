"""Corrective RAG (CRAG) Orchestrator - Self-correcting retrieval mechanism.

This module implements the main CRAG orchestration layer that combines:
- Relevance evaluation (fast heuristics)
- Query expansion (for PARTIAL relevance)
- Web search augmentation (for IRRELEVANT relevance)

Based on research from Russian Adaptive RAG and Korean AutoRAG frameworks.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.cgrag import CGRAGRetriever

logger = logging.getLogger(__name__)


class CRAGResult(BaseModel):
    """Result from CRAG retrieval with correction metadata.

    Attributes:
        artifacts: Final retrieved/corrected artifacts
        tokens_used: Total tokens in artifacts
        retrieval_time_ms: Total retrieval + correction time
        crag_decision: Relevance category (RELEVANT/PARTIAL/IRRELEVANT)
        crag_score: Aggregate relevance score (0.0-1.0)
        correction_applied: Whether correction strategy was used
        correction_strategy: Type of correction (query_expansion, web_search, none)
        original_artifacts_count: Number of artifacts before correction
        web_search_used: Whether web search was triggered
        cache_hit: Whether result was served from cache
        keyword_overlap: Keyword matching score
        semantic_coherence: Similarity score distribution quality
        length_adequacy: Content sufficiency score
        diversity: Source diversity score
    """

    artifacts: List  # List[DocumentChunk]
    tokens_used: int
    retrieval_time_ms: float
    crag_decision: str = Field(..., description="RELEVANT | PARTIAL | IRRELEVANT")
    crag_score: float = Field(..., ge=0.0, le=1.0)
    correction_applied: bool
    correction_strategy: str = Field(..., description="query_expansion | web_search | none")
    original_artifacts_count: int
    web_search_used: bool = False
    cache_hit: bool = False

    # Detailed evaluation metrics
    keyword_overlap: float = 0.0
    semantic_coherence: float = 0.0
    length_adequacy: float = 0.0
    diversity: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class CRAGOrchestrator:
    """Corrective RAG orchestrator integrating evaluation and correction.

    Implements the complete CRAG workflow:
    1. Initial retrieval via CGRAG
    2. Relevance evaluation using fast heuristics
    3. Decision routing:
       - RELEVANT (score > 0.75): Return as-is (fast path <70ms)
       - PARTIAL (0.50 < score <= 0.75): Query expansion + re-retrieval
       - IRRELEVANT (score <= 0.50): Web search augmentation
    4. Return corrected results with comprehensive metadata

    Expected Performance:
    - RELEVANT (fast path): <70ms (30% faster than current CGRAG)
    - PARTIAL (expansion): ~180ms (query expansion + merge)
    - IRRELEVANT (web search): ~450ms (web search overhead)

    Expected Accuracy Improvement:
    - Retrieval accuracy: ~70% -> 85-90% (+15-20%)
    - Hallucination rate: ~10% -> <5% (50% reduction)
    """

    def __init__(
        self,
        cgrag_retriever: "CGRAGRetriever",
        enable_web_search: bool = True,
        enable_query_expansion: bool = True,
    ):
        """Initialize CRAG orchestrator.

        Args:
            cgrag_retriever: CGRAG retriever instance
            enable_web_search: Enable web search fallback (default: True)
            enable_query_expansion: Enable query expansion (default: True)
        """
        # Import components here to avoid circular dependencies
        from app.services.crag_evaluator import CRAGEvaluator
        from app.services.query_expander import QueryExpander
        from app.services.web_augmenter import WebSearchAugmenter

        self.cgrag_retriever = cgrag_retriever
        self.evaluator = CRAGEvaluator()
        self.expander = QueryExpander() if enable_query_expansion else None
        self.augmenter = WebSearchAugmenter() if enable_web_search else None

        logger.info(
            f"[CRAG] Initialized: web_search={enable_web_search}, "
            f"query_expansion={enable_query_expansion}"
        )

    async def retrieve(
        self, query: str, token_budget: int = 8000, max_artifacts: int = 20
    ) -> CRAGResult:
        """Retrieve with corrective RAG workflow.

        Executes the full CRAG pipeline:
        - Initial CGRAG retrieval
        - Relevance evaluation
        - Correction strategy (if needed)
        - Final result packaging

        Args:
            query: Query text
            token_budget: Maximum tokens for artifacts
            max_artifacts: Maximum artifacts to retrieve

        Returns:
            CRAGResult with corrected artifacts and metadata

        Example:
            >>> orchestrator = CRAGOrchestrator(cgrag_retriever)
            >>> result = await orchestrator.retrieve("Python async patterns")
            >>> print(result.crag_decision)  # RELEVANT | PARTIAL | IRRELEVANT
            >>> print(result.correction_strategy)  # none | query_expansion | web_search
        """
        start_time = time.time()

        # Step 1: Initial CGRAG retrieval
        logger.info(f"[CRAG] Initial retrieval: query='{query[:50]}...'")
        cgrag_result = await self.cgrag_retriever.retrieve(
            query=query, token_budget=token_budget, max_artifacts=max_artifacts
        )

        logger.debug(
            f"[CRAG] Retrieved {len(cgrag_result.artifacts)} artifacts "
            f"({cgrag_result.tokens_used} tokens) in {cgrag_result.retrieval_time_ms:.1f}ms"
        )

        # Step 2: Relevance evaluation
        logger.info(f"[CRAG] Evaluating {len(cgrag_result.artifacts)} artifacts")
        relevance_eval = await self.evaluator.evaluate(
            query=query,
            artifacts=cgrag_result.artifacts,
            relevance_scores=cgrag_result.top_scores,
        )

        logger.info(
            f"[CRAG] Evaluation: {relevance_eval.category} (score={relevance_eval.score:.2f})"
        )
        logger.debug(
            f"[CRAG] Breakdown: keyword={relevance_eval.keyword_overlap:.2f}, "
            f"coherence={relevance_eval.semantic_coherence:.2f}, "
            f"length={relevance_eval.length_adequacy:.2f}, "
            f"diversity={relevance_eval.diversity:.2f}"
        )

        # Step 3: Decision routing
        final_artifacts = cgrag_result.artifacts
        correction_applied = False
        correction_strategy = "none"
        web_search_used = False

        if relevance_eval.category == "RELEVANT":
            # Fast path - use original artifacts
            logger.info("[CRAG] Fast path: Using original artifacts (high relevance)")
            correction_strategy = "none"

        elif relevance_eval.category == "PARTIAL" and self.expander:
            # Query expansion + re-retrieval
            logger.info("[CRAG] Applying query expansion (partial relevance)")
            expanded_query = self.expander.expand(query)
            logger.debug(f"[CRAG] Expanded query: '{expanded_query}'")

            # Re-retrieve with expanded query
            try:
                expanded_result = await self.cgrag_retriever.retrieve(
                    query=expanded_query,
                    token_budget=token_budget,
                    max_artifacts=max_artifacts,
                )

                # Merge original + expanded results
                final_artifacts = self._merge_artifacts(
                    cgrag_result.artifacts, expanded_result.artifacts, token_budget
                )

                correction_applied = True
                correction_strategy = "query_expansion"

                logger.info(
                    f"[CRAG] Merged {len(final_artifacts)} artifacts "
                    f"(original: {len(cgrag_result.artifacts)}, "
                    f"expanded: {len(expanded_result.artifacts)})"
                )

            except Exception as e:
                logger.error(f"[CRAG] Query expansion failed: {e}. Using original artifacts.")
                correction_strategy = "none"

        elif relevance_eval.category == "IRRELEVANT" and self.augmenter:
            # Web search augmentation
            logger.info("[CRAG] Fallback to web search (low relevance)")

            try:
                web_chunks = await self.augmenter.augment(query)

                if web_chunks:
                    final_artifacts = web_chunks
                    correction_applied = True
                    correction_strategy = "web_search"
                    web_search_used = True
                    logger.info(f"[CRAG] Retrieved {len(web_chunks)} web results")
                else:
                    logger.warning(
                        "[CRAG] Web search returned no results, using original artifacts"
                    )

            except Exception as e:
                logger.error(f"[CRAG] Web search failed: {e}. Using original artifacts.")

        else:
            # Correction disabled or failed - use original artifacts
            logger.info("[CRAG] No correction applied (disabled or unavailable)")

        # Calculate final token usage
        tokens_used = sum(self._estimate_tokens(chunk.content) for chunk in final_artifacts)

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"[CRAG] Complete in {elapsed_ms:.1f}ms: "
            f"{len(final_artifacts)} artifacts, {tokens_used} tokens, "
            f"correction={correction_strategy}"
        )

        # Log metrics for monitoring
        logger.info(
            f"[CRAG_METRICS] decision={relevance_eval.category} "
            f"score={relevance_eval.score:.2f} "
            f"correction={correction_strategy} "
            f"latency_ms={elapsed_ms:.1f} "
            f"artifacts={len(final_artifacts)} "
            f"tokens={tokens_used}"
        )

        return CRAGResult(
            artifacts=final_artifacts,
            tokens_used=tokens_used,
            retrieval_time_ms=elapsed_ms,
            crag_decision=relevance_eval.category,
            crag_score=relevance_eval.score,
            correction_applied=correction_applied,
            correction_strategy=correction_strategy,
            original_artifacts_count=len(cgrag_result.artifacts),
            web_search_used=web_search_used,
            cache_hit=cgrag_result.cache_hit,
            keyword_overlap=relevance_eval.keyword_overlap,
            semantic_coherence=relevance_eval.semantic_coherence,
            length_adequacy=relevance_eval.length_adequacy,
            diversity=relevance_eval.diversity,
        )

    def _merge_artifacts(
        self,
        original: List,  # List[DocumentChunk]
        expanded: List,  # List[DocumentChunk]
        token_budget: int,
    ) -> List:  # List[DocumentChunk]
        """Merge original and expanded artifacts using deduplication.

        Combines results from original and query-expanded retrieval while:
        - Avoiding duplicates (by chunk ID)
        - Respecting token budget
        - Prioritizing original artifacts (higher priority)

        Args:
            original: Original retrieval artifacts
            expanded: Query-expanded retrieval artifacts
            token_budget: Maximum tokens

        Returns:
            Merged artifact list

        Example:
            >>> merged = self._merge_artifacts(
            ...     original=[chunk1, chunk2],
            ...     expanded=[chunk2, chunk3, chunk4],
            ...     token_budget=5000
            ... )
            >>> # Returns: [chunk1, chunk2, chunk3, chunk4] (deduplicated, within budget)
        """
        # Deduplicate by chunk ID
        seen_ids = set()
        merged = []
        total_tokens = 0

        # Process original artifacts first (higher priority)
        for chunk in original:
            if chunk.id not in seen_ids:
                chunk_tokens = self._estimate_tokens(chunk.content)
                if total_tokens + chunk_tokens <= token_budget:
                    merged.append(chunk)
                    seen_ids.add(chunk.id)
                    total_tokens += chunk_tokens

        # Add new artifacts from expanded results
        for chunk in expanded:
            if chunk.id not in seen_ids:
                chunk_tokens = self._estimate_tokens(chunk.content)
                if total_tokens + chunk_tokens <= token_budget:
                    merged.append(chunk)
                    seen_ids.add(chunk.id)
                    total_tokens += chunk_tokens

        logger.debug(
            f"[CRAG] Merged artifacts: original={len(original)}, "
            f"expanded={len(expanded)}, merged={len(merged)}, "
            f"tokens={total_tokens}/{token_budget}"
        )

        return merged

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word-based heuristic.

        Uses the approximation: tokens ≈ words * 1.3

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        return int(len(text.split()) * 1.3)

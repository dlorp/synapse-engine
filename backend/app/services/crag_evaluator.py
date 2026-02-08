"""CRAG Relevance Evaluator - Fast heuristic-based retrieval quality assessment.

This module implements the core relevance evaluation component of Corrective RAG (CRAG).
Uses multi-criteria heuristics for fast, LLM-free quality assessment of retrieved artifacts.
"""

import logging
from dataclasses import dataclass
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Evaluation result from CRAG relevance assessment.

    Attributes:
        category: RELEVANT | PARTIAL | IRRELEVANT
        score: Aggregate relevance score (0.0-1.0)
        keyword_overlap: Keyword match ratio (0.0-1.0)
        semantic_coherence: Similarity score distribution quality (0.0-1.0)
        length_adequacy: Content sufficiency score (0.0-1.0)
        diversity: Source diversity score (0.0-1.0)
        reasoning: Human-readable explanation of classification
    """

    category: str
    score: float
    keyword_overlap: float
    semantic_coherence: float
    length_adequacy: float
    diversity: float
    reasoning: str


class CRAGEvaluator:
    """Evaluates retrieval quality using fast heuristics (LLM-free).

    Implements multi-criteria relevance assessment based on:
    - Keyword overlap between query and artifacts
    - Semantic coherence (similarity score distribution)
    - Content length adequacy
    - Source diversity

    Classification thresholds:
    - RELEVANT: score > 0.75 (high confidence, use as-is)
    - PARTIAL: 0.50 < score <= 0.75 (medium confidence, expand and retry)
    - IRRELEVANT: score <= 0.50 (low confidence, fallback to web search)
    """

    # Category thresholds
    RELEVANT_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.50

    # Criteria weights (must sum to 1.0)
    WEIGHTS = {
        "keyword_overlap": 0.30,
        "semantic_coherence": 0.40,
        "length_adequacy": 0.15,
        "diversity": 0.15,
    }

    # Simple stopwords list (English) - filter out common words
    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
        "what",
        "how",
        "which",
        "this",
        "these",
        "those",
        "there",
        "where",
        "when",
    }

    def __init__(self, min_keywords: int = 2, min_tokens_per_chunk: int = 100):
        """Initialize evaluator with configuration.

        Args:
            min_keywords: Minimum query keywords to consider for overlap
            min_tokens_per_chunk: Minimum tokens per chunk for adequacy check
        """
        self.min_keywords = min_keywords
        self.min_tokens_per_chunk = min_tokens_per_chunk
        logger.info(
            f"Initialized CRAGEvaluator: min_keywords={min_keywords}, "
            f"min_tokens_per_chunk={min_tokens_per_chunk}"
        )

    async def evaluate(
        self,
        query: str,
        artifacts: List,  # List[DocumentChunk]
        relevance_scores: List[float],
    ) -> RelevanceScore:
        """Evaluate retrieval quality using multi-criteria heuristics.

        Args:
            query: Original query text
            artifacts: Retrieved document chunks
            relevance_scores: FAISS similarity scores for artifacts

        Returns:
            RelevanceScore with category and detailed metrics
        """
        if not artifacts:
            # No artifacts retrieved - IRRELEVANT
            return RelevanceScore(
                category="IRRELEVANT",
                score=0.0,
                keyword_overlap=0.0,
                semantic_coherence=0.0,
                length_adequacy=0.0,
                diversity=0.0,
                reasoning="No artifacts retrieved from CGRAG index",
            )

        # Extract query keywords (simple tokenization)
        query_keywords = self._extract_keywords(query)

        # Criterion 1: Keyword Overlap (30%)
        keyword_score = self._compute_keyword_overlap(query_keywords, artifacts)

        # Criterion 2: Semantic Coherence (40%)
        coherence_score = self._compute_semantic_coherence(relevance_scores)

        # Criterion 3: Length Adequacy (15%)
        length_score = self._compute_length_adequacy(artifacts)

        # Criterion 4: Source Diversity (15%)
        diversity_score = self._compute_diversity(artifacts)

        # Weighted aggregate score
        aggregate_score = (
            self.WEIGHTS["keyword_overlap"] * keyword_score
            + self.WEIGHTS["semantic_coherence"] * coherence_score
            + self.WEIGHTS["length_adequacy"] * length_score
            + self.WEIGHTS["diversity"] * diversity_score
        )

        # Classify into category
        if aggregate_score > self.RELEVANT_THRESHOLD:
            category = "RELEVANT"
            reasoning = (
                f"High relevance (score={aggregate_score:.2f}). "
                f"Retrieved context is sufficient for generation."
            )
        elif aggregate_score > self.PARTIAL_THRESHOLD:
            category = "PARTIAL"
            reasoning = (
                f"Partial relevance (score={aggregate_score:.2f}). "
                f"Query expansion recommended to improve retrieval."
            )
        else:
            category = "IRRELEVANT"
            reasoning = (
                f"Low relevance (score={aggregate_score:.2f}). "
                f"Fallback to web search required for external knowledge."
            )

        logger.info(
            f"[CRAG_EVAL] category={category}, score={aggregate_score:.2f}, "
            f"keyword={keyword_score:.2f}, coherence={coherence_score:.2f}, "
            f"length={length_score:.2f}, diversity={diversity_score:.2f}"
        )

        return RelevanceScore(
            category=category,
            score=aggregate_score,
            keyword_overlap=keyword_score,
            semantic_coherence=coherence_score,
            length_adequacy=length_score,
            diversity=diversity_score,
            reasoning=reasoning,
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract query keywords using simple tokenization.

        Filters stopwords and short tokens to focus on meaningful terms.

        Args:
            query: Query text

        Returns:
            List of keyword strings
        """
        # Tokenize and lowercase
        tokens = query.lower().split()

        # Filter stopwords and short tokens
        keywords = [token for token in tokens if token not in self.STOPWORDS and len(token) > 2]

        return keywords

    def _compute_keyword_overlap(
        self,
        query_keywords: List[str],
        artifacts: List,  # List[DocumentChunk]
    ) -> float:
        """Compute keyword overlap ratio.

        Measures what fraction of query keywords appear in artifacts.

        Args:
            query_keywords: Query keywords
            artifacts: Retrieved chunks

        Returns:
            Overlap ratio (0.0-1.0)
        """
        if not query_keywords or not artifacts:
            return 0.0

        # Combine all artifact content
        combined_text = " ".join(chunk.content.lower() for chunk in artifacts)

        # Count how many query keywords appear
        found_keywords = sum(1 for keyword in query_keywords if keyword in combined_text)

        overlap_ratio = found_keywords / len(query_keywords)

        logger.debug(
            f"[CRAG_EVAL] Keyword overlap: {found_keywords}/{len(query_keywords)} "
            f"= {overlap_ratio:.2f}"
        )

        return overlap_ratio

    def _compute_semantic_coherence(self, relevance_scores: List[float]) -> float:
        """Compute semantic coherence from similarity score distribution.

        High coherence = high mean + low variance (all chunks relevant)
        Low coherence = low mean or high variance (some irrelevant chunks)

        Args:
            relevance_scores: FAISS similarity scores

        Returns:
            Coherence score (0.0-1.0)
        """
        if not relevance_scores:
            return 0.0

        scores = np.array(relevance_scores)
        mean_score = float(np.mean(scores))
        variance = float(np.var(scores))

        # Coherence = high mean, low variance
        # Penalize high variance (inconsistent relevance)
        coherence = mean_score * (1.0 - min(variance, 0.3))

        # Clip to [0.0, 1.0]
        coherence = float(np.clip(coherence, 0.0, 1.0))

        logger.debug(
            f"[CRAG_EVAL] Semantic coherence: mean={mean_score:.2f}, "
            f"var={variance:.2f}, coherence={coherence:.2f}"
        )

        return coherence

    def _compute_length_adequacy(self, artifacts: List) -> float:
        """Compute length adequacy score.

        Checks if artifacts have sufficient content to answer query.

        Args:
            artifacts: Retrieved chunks

        Returns:
            Adequacy score (0.0-1.0)
        """
        if not artifacts:
            return 0.0

        # Count tokens across all chunks
        total_tokens = sum(self._estimate_tokens(chunk.content) for chunk in artifacts)

        # Expect at least min_tokens_per_chunk * num_chunks
        expected_tokens = self.min_tokens_per_chunk * len(artifacts)

        if total_tokens >= expected_tokens:
            adequacy = 1.0
        else:
            adequacy = total_tokens / expected_tokens

        logger.debug(
            f"[CRAG_EVAL] Length adequacy: {total_tokens}/{expected_tokens} tokens = {adequacy:.2f}"
        )

        return adequacy

    def _compute_diversity(self, artifacts: List) -> float:
        """Compute source diversity score.

        Higher score = artifacts from multiple different files.

        Args:
            artifacts: Retrieved chunks

        Returns:
            Diversity score (0.0-1.0)
        """
        if not artifacts:
            return 0.0

        # Count unique file paths
        unique_files = len(set(chunk.file_path for chunk in artifacts))

        # Diversity = unique_files / total_chunks (capped at 1.0)
        diversity = unique_files / len(artifacts)

        logger.debug(
            f"[CRAG_EVAL] Source diversity: {unique_files}/{len(artifacts)} files = {diversity:.2f}"
        )

        return min(diversity, 1.0)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word-based heuristic.

        Uses the approximation: tokens ≈ words * 1.3
        This is reasonable for English text.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * 1.3)

"""Unit tests for CRAG (Corrective RAG) components.

Tests cover:
- CRAGEvaluator: Relevance assessment with multi-criteria heuristics
- QueryExpander: Synonym-based query expansion
- WebSearchAugmenter: Web search fallback
- CRAGOrchestrator: End-to-end CRAG workflow
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.crag_evaluator import CRAGEvaluator, RelevanceScore
from app.services.query_expander import QueryExpander
from app.services.web_augmenter import WebSearchAugmenter
from app.services.crag import CRAGOrchestrator, CRAGResult
from app.services.cgrag import DocumentChunk, CGRAGResult


# Test fixtures
@pytest.fixture
def mock_document_chunks():
    """Create mock document chunks for testing."""
    return [
        DocumentChunk(
            id="chunk1",
            file_path="docs/async.md",
            content="Async patterns in Python use asyncio library for concurrent execution. "
            "The async/await syntax provides clean abstraction over event loops.",
            chunk_index=0,
            start_pos=0,
            end_pos=150,
            relevance_score=0.92,
        ),
        DocumentChunk(
            id="chunk2",
            file_path="docs/async.md",
            content="Asynchronous programming allows non-blocking I/O operations, improving "
            "performance for I/O-bound tasks. Python's asyncio module is the standard library.",
            chunk_index=1,
            start_pos=150,
            end_pos=300,
            relevance_score=0.88,
        ),
        DocumentChunk(
            id="chunk3",
            file_path="docs/python.md",
            content="Python is a high-level interpreted programming language with dynamic typing.",
            chunk_index=0,
            start_pos=0,
            end_pos=80,
            relevance_score=0.65,
        ),
    ]


@pytest.fixture
def irrelevant_chunks():
    """Create irrelevant document chunks (low relevance)."""
    return [
        DocumentChunk(
            id="chunk4",
            file_path="docs/frontend.md",
            content="React components use hooks for state management in modern applications.",
            chunk_index=0,
            start_pos=0,
            end_pos=80,
            relevance_score=0.35,
        ),
        DocumentChunk(
            id="chunk5",
            file_path="docs/css.md",
            content="CSS Grid provides two-dimensional layout capabilities for web design.",
            chunk_index=0,
            start_pos=0,
            end_pos=70,
            relevance_score=0.28,
        ),
    ]


# CRAGEvaluator Tests
class TestCRAGEvaluator:
    """Tests for relevance evaluation component."""

    @pytest.mark.asyncio
    async def test_evaluator_relevant_category(self, mock_document_chunks):
        """Test evaluator classifies high-quality retrieval as RELEVANT."""
        evaluator = CRAGEvaluator()

        query = "Python async patterns concurrent execution"
        relevance_scores = [chunk.relevance_score for chunk in mock_document_chunks]

        result = await evaluator.evaluate(query, mock_document_chunks, relevance_scores)

        assert isinstance(result, RelevanceScore)
        assert result.category == "RELEVANT"
        assert result.score > 0.75
        assert result.keyword_overlap > 0.5  # Most keywords should match
        assert result.semantic_coherence > 0.7  # High similarity scores
        assert "sufficient" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_evaluator_irrelevant_category(self, irrelevant_chunks):
        """Test evaluator classifies poor retrieval as IRRELEVANT."""
        evaluator = CRAGEvaluator()

        query = "Kubernetes deployment strategies for microservices"
        relevance_scores = [chunk.relevance_score for chunk in irrelevant_chunks]

        result = await evaluator.evaluate(query, irrelevant_chunks, relevance_scores)

        assert result.category == "IRRELEVANT"
        assert result.score < 0.50
        assert result.keyword_overlap < 0.3  # Few keywords match
        assert "web search" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_evaluator_partial_category(self, mock_document_chunks):
        """Test evaluator classifies medium-quality retrieval as PARTIAL."""
        evaluator = CRAGEvaluator()

        # Query with only partial keyword overlap
        query = "Python async error handling debugging strategies"
        relevance_scores = [0.72, 0.68, 0.55]  # Medium scores

        result = await evaluator.evaluate(query, mock_document_chunks, relevance_scores)

        # Should be PARTIAL or RELEVANT depending on criteria
        assert result.category in ["PARTIAL", "RELEVANT"]
        if result.category == "PARTIAL":
            assert 0.50 < result.score <= 0.75
            assert "expansion" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_evaluator_empty_artifacts(self):
        """Test evaluator handles empty artifact list."""
        evaluator = CRAGEvaluator()

        result = await evaluator.evaluate("test query", [], [])

        assert result.category == "IRRELEVANT"
        assert result.score == 0.0
        assert result.keyword_overlap == 0.0
        assert "no artifacts" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_keyword_overlap_calculation(self, mock_document_chunks):
        """Test keyword overlap scoring."""
        evaluator = CRAGEvaluator()

        # Query with all keywords present in artifacts
        query = "async python concurrent"
        keywords = evaluator._extract_keywords(query)
        overlap = evaluator._compute_keyword_overlap(keywords, mock_document_chunks)

        assert overlap > 0.8  # All keywords should be found

        # Query with no keywords present
        query = "kubernetes docker container"
        keywords = evaluator._extract_keywords(query)
        overlap = evaluator._compute_keyword_overlap(keywords, mock_document_chunks)

        assert overlap < 0.2  # Few/no keywords found

    def test_semantic_coherence_calculation(self):
        """Test semantic coherence scoring."""
        evaluator = CRAGEvaluator()

        # High coherence - all scores high and similar
        high_scores = [0.92, 0.90, 0.88, 0.91]
        coherence = evaluator._compute_semantic_coherence(high_scores)
        assert coherence > 0.8

        # Low coherence - mixed scores
        mixed_scores = [0.85, 0.45, 0.92, 0.38]
        coherence = evaluator._compute_semantic_coherence(mixed_scores)
        assert coherence < 0.7  # Penalized for high variance

    def test_length_adequacy_calculation(self, mock_document_chunks):
        """Test length adequacy scoring."""
        evaluator = CRAGEvaluator(min_tokens_per_chunk=50)

        adequacy = evaluator._compute_length_adequacy(mock_document_chunks)

        # Chunks have ~20-25 words each = ~26-32 tokens
        # Total ~78-96 tokens for 3 chunks
        # Expected: 3 * 50 = 150 tokens
        # Adequacy should be ~0.5-0.65
        assert 0.4 < adequacy < 0.8

    def test_diversity_calculation(self, mock_document_chunks):
        """Test source diversity scoring."""
        evaluator = CRAGEvaluator()

        diversity = evaluator._compute_diversity(mock_document_chunks)

        # 3 chunks from 2 different files (async.md, python.md)
        # Diversity = 2 / 3 = 0.67
        assert 0.6 < diversity < 0.7


# QueryExpander Tests
class TestQueryExpander:
    """Tests for query expansion component."""

    def test_basic_expansion(self):
        """Test basic query expansion with synonyms."""
        expander = QueryExpander(max_synonyms_per_term=2)

        query = "explain async function"
        expanded = expander.expand(query)

        # Should contain original terms
        assert "explain" in expanded
        assert "async" in expanded
        assert "function" in expanded

        # Should contain synonyms
        assert any(syn in expanded for syn in ["describe", "clarify", "illustrate"])
        assert any(syn in expanded for syn in ["asynchronous", "concurrent"])
        assert any(syn in expanded for syn in ["method", "procedure", "routine"])

    def test_expansion_preserves_originals(self):
        """Test that expanded query includes all original terms."""
        expander = QueryExpander()

        query = "optimize performance"
        expanded = expander.expand(query)

        assert "optimize" in expanded
        assert "performance" in expanded

    def test_expansion_with_unknown_terms(self):
        """Test expansion handles terms without synonyms."""
        expander = QueryExpander()

        query = "xyzabc unknown terms"
        expanded = expander.expand(query)

        # Should still include original terms
        assert "xyzabc" in expanded
        assert "unknown" in expanded
        assert "terms" in expanded

    def test_max_synonyms_limit(self):
        """Test max_synonyms_per_term limit is respected."""
        expander = QueryExpander(max_synonyms_per_term=1)

        query = "function"
        expanded = expander.expand(query)

        # Should have original + 1 synonym = 2 terms
        terms = expanded.split()
        assert len(terms) == 2
        assert "function" in terms

    def test_add_synonym_runtime(self):
        """Test adding synonyms at runtime."""
        expander = QueryExpander()

        expander.add_synonym("fastapi", ["framework", "api", "backend"])

        query = "fastapi development"
        expanded = expander.expand(query)

        assert "fastapi" in expanded
        assert any(syn in expanded for syn in ["framework", "api", "backend"])


# WebSearchAugmenter Tests
class TestWebSearchAugmenter:
    """Tests for web search augmentation component."""

    @pytest.mark.asyncio
    async def test_augment_converts_web_results_to_chunks(self):
        """Test web search results are converted to DocumentChunk format."""
        # Mock SearXNG client
        with patch("app.services.web_augmenter.get_searxng_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_search_response = Mock()
            mock_search_response.results = [
                Mock(
                    title="Python Async Guide",
                    url="https://example.com/async",
                    content="Comprehensive guide to async programming in Python",
                    score=1.0,
                ),
                Mock(
                    title="Asyncio Tutorial",
                    url="https://example.com/asyncio",
                    content="Learn asyncio for concurrent Python programming",
                    score=0.9,
                ),
            ]
            mock_search_response.search_time_ms = 250.0

            mock_client.search = AsyncMock(return_value=mock_search_response)
            mock_get_client.return_value = mock_client

            augmenter = WebSearchAugmenter(max_results=5)

            # Execute augmentation
            chunks = await augmenter.augment("Python async patterns")

            # Verify results
            assert len(chunks) == 2
            assert all(chunk.language == "web" for chunk in chunks)
            assert chunks[0].file_path == "https://example.com/async"
            assert "Python Async Guide" in chunks[0].content
            assert chunks[0].relevance_score == 1.0

    @pytest.mark.asyncio
    async def test_augment_handles_empty_results(self):
        """Test augmenter handles empty search results gracefully."""
        with patch("app.services.web_augmenter.get_searxng_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_search_response = Mock()
            mock_search_response.results = []
            mock_search_response.search_time_ms = 100.0

            mock_client.search = AsyncMock(return_value=mock_search_response)
            mock_get_client.return_value = mock_client

            augmenter = WebSearchAugmenter()
            chunks = await augmenter.augment("test query")

            assert chunks == []

    @pytest.mark.asyncio
    async def test_augment_handles_search_failure(self):
        """Test augmenter handles search failures gracefully."""
        with patch("app.services.web_augmenter.get_searxng_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(side_effect=Exception("Search failed"))
            mock_get_client.return_value = mock_client

            augmenter = WebSearchAugmenter()
            chunks = await augmenter.augment("test query")

            # Should return empty list on failure (graceful degradation)
            assert chunks == []


# CRAGOrchestrator Tests
class TestCRAGOrchestrator:
    """Tests for CRAG orchestration workflow."""

    @pytest.mark.asyncio
    async def test_orchestrator_fast_path_relevant(self, mock_document_chunks):
        """Test CRAG fast path (RELEVANT category, no correction)."""
        # Mock CGRAG retriever
        mock_retriever = AsyncMock()
        mock_cgrag_result = CGRAGResult(
            artifacts=mock_document_chunks,
            tokens_used=200,
            candidates_considered=20,
            retrieval_time_ms=85.0,
            cache_hit=False,
            top_scores=[0.92, 0.88, 0.65],
        )
        mock_retriever.retrieve = AsyncMock(return_value=mock_cgrag_result)

        orchestrator = CRAGOrchestrator(
            cgrag_retriever=mock_retriever,
            enable_web_search=False,
            enable_query_expansion=False,
        )

        # Execute CRAG workflow
        result = await orchestrator.retrieve(
            query="Python async patterns concurrent execution", token_budget=5000
        )

        # Verify fast path
        assert isinstance(result, CRAGResult)
        assert result.crag_decision == "RELEVANT"
        assert result.correction_applied is False
        assert result.correction_strategy == "none"
        assert result.crag_score > 0.75
        assert len(result.artifacts) == 3  # Original artifacts
        assert result.web_search_used is False

    @pytest.mark.asyncio
    async def test_orchestrator_query_expansion_partial(self, mock_document_chunks):
        """Test CRAG query expansion (PARTIAL category)."""
        # Mock CGRAG retriever
        mock_retriever = AsyncMock()

        # Initial retrieval (medium relevance)
        initial_result = CGRAGResult(
            artifacts=mock_document_chunks[:2],  # Only 2 chunks
            tokens_used=150,
            candidates_considered=10,
            retrieval_time_ms=80.0,
            cache_hit=False,
            top_scores=[0.68, 0.62],
        )

        # Expanded retrieval (better results)
        expanded_chunk = DocumentChunk(
            id="chunk_expanded",
            file_path="docs/concurrency.md",
            content="Concurrent programming with async/await in Python using asyncio.",
            chunk_index=0,
            start_pos=0,
            end_pos=70,
            relevance_score=0.85,
        )
        expanded_result = CGRAGResult(
            artifacts=[expanded_chunk] + mock_document_chunks[:1],
            tokens_used=180,
            candidates_considered=15,
            retrieval_time_ms=90.0,
            cache_hit=False,
            top_scores=[0.85, 0.68],
        )

        # Configure mock to return different results
        mock_retriever.retrieve = AsyncMock(
            side_effect=[initial_result, expanded_result]
        )

        orchestrator = CRAGOrchestrator(
            cgrag_retriever=mock_retriever,
            enable_web_search=False,
            enable_query_expansion=True,
        )

        # Execute with PARTIAL-triggering query
        result = await orchestrator.retrieve(
            query="async error handling",  # Partial keyword overlap
            token_budget=5000,
        )

        # Verify query expansion was applied
        assert result.correction_applied is True
        assert result.correction_strategy == "query_expansion"
        assert len(result.artifacts) >= 2  # Merged results
        assert result.web_search_used is False

    @pytest.mark.asyncio
    async def test_orchestrator_web_search_fallback(self, irrelevant_chunks):
        """Test CRAG web search fallback (IRRELEVANT category)."""
        # Mock CGRAG retriever (returns irrelevant results)
        mock_retriever = AsyncMock()
        mock_cgrag_result = CGRAGResult(
            artifacts=irrelevant_chunks,
            tokens_used=80,
            candidates_considered=5,
            retrieval_time_ms=70.0,
            cache_hit=False,
            top_scores=[0.35, 0.28],
        )
        mock_retriever.retrieve = AsyncMock(return_value=mock_cgrag_result)

        # Mock web augmenter
        web_chunk = DocumentChunk(
            id="web1",
            file_path="https://example.com/kubernetes",
            content="Kubernetes Deployment Strategies for Microservices",
            chunk_index=0,
            start_pos=0,
            end_pos=50,
            language="web",
            relevance_score=0.95,
        )

        with patch("app.services.crag.WebSearchAugmenter") as MockAugmenter:
            mock_augmenter_instance = AsyncMock()
            mock_augmenter_instance.augment = AsyncMock(return_value=[web_chunk])
            MockAugmenter.return_value = mock_augmenter_instance

            orchestrator = CRAGOrchestrator(
                cgrag_retriever=mock_retriever,
                enable_web_search=True,
                enable_query_expansion=False,
            )

            # Execute with irrelevant-triggering query
            result = await orchestrator.retrieve(
                query="Kubernetes deployment strategies microservices",
                token_budget=5000,
            )

            # Verify web search fallback
            assert result.crag_decision == "IRRELEVANT"
            assert result.correction_applied is True
            assert result.correction_strategy == "web_search"
            assert result.web_search_used is True
            assert len(result.artifacts) == 1
            assert result.artifacts[0].language == "web"

    @pytest.mark.asyncio
    async def test_orchestrator_merge_deduplication(self):
        """Test artifact merging deduplicates by chunk ID."""
        mock_retriever = AsyncMock()

        # Create chunks with duplicate IDs
        chunk1 = DocumentChunk(
            id="chunk1",
            file_path="docs/test.md",
            content="Content 1",
            chunk_index=0,
            start_pos=0,
            end_pos=10,
        )
        chunk2 = DocumentChunk(
            id="chunk2",
            file_path="docs/test.md",
            content="Content 2",
            chunk_index=1,
            start_pos=10,
            end_pos=20,
        )
        chunk1_duplicate = DocumentChunk(
            id="chunk1",  # Same ID as chunk1
            file_path="docs/test.md",
            content="Content 1",
            chunk_index=0,
            start_pos=0,
            end_pos=10,
        )

        orchestrator = CRAGOrchestrator(
            cgrag_retriever=mock_retriever,
            enable_web_search=False,
            enable_query_expansion=False,
        )

        # Test merge with duplicates
        merged = orchestrator._merge_artifacts(
            original=[chunk1, chunk2],
            expanded=[chunk1_duplicate, chunk2],  # Duplicates
            token_budget=10000,
        )

        # Should only have 2 unique chunks
        assert len(merged) == 2
        assert set(c.id for c in merged) == {"chunk1", "chunk2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

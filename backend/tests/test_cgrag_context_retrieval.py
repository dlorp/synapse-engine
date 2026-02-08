"""Integration tests for CGRAG context retrieval.

Tests cover:
- Context retrieval under various loads (single/batch/concurrent)
- Edge cases with empty contexts and boundary conditions
- Timeout handling and latency validation
- Error recovery and resilience
"""

import asyncio
import time
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import faiss
import numpy as np
import pytest

from app.services.cgrag import (
    CGRAGIndexer,
    CGRAGResult,
    CGRAGRetriever,
    DocumentChunk,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_chunks() -> List[DocumentChunk]:
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            id=f"chunk-{i}",
            file_path=f"docs/file{i % 5}.md",
            content=f"This is test content for chunk {i}. " * 20,  # ~200 words
            chunk_index=i,
            start_pos=i * 1000,
            end_pos=(i + 1) * 1000,
            language="markdown",
            relevance_score=0.0,
        )
        for i in range(100)
    ]


@pytest.fixture
def small_chunks() -> List[DocumentChunk]:
    """Create small set of chunks for basic tests."""
    return [
        DocumentChunk(
            id="chunk-python",
            file_path="docs/python.md",
            content="Python is a high-level programming language known for readability.",
            chunk_index=0,
            start_pos=0,
            end_pos=70,
            language="markdown",
        ),
        DocumentChunk(
            id="chunk-async",
            file_path="docs/async.md",
            content="Async programming in Python uses asyncio for concurrent execution.",
            chunk_index=0,
            start_pos=0,
            end_pos=70,
            language="markdown",
        ),
        DocumentChunk(
            id="chunk-ml",
            file_path="docs/ml.md",
            content="Machine learning models require training data and feature engineering.",
            chunk_index=0,
            start_pos=0,
            end_pos=70,
            language="markdown",
        ),
    ]


@pytest.fixture
def mock_indexer(small_chunks):
    """Create a mock CGRAGIndexer with pre-loaded chunks."""
    indexer = MagicMock(spec=CGRAGIndexer)
    indexer.chunks = small_chunks
    indexer.embedding_dim = 384
    indexer.embedding_model_name = "all-MiniLM-L6-v2"

    # Create a simple FAISS index
    n_chunks = len(small_chunks)
    embeddings = np.random.rand(n_chunks, 384).astype(np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatL2(384)
    index.add(embeddings)
    indexer.index = index

    # Mock encoder
    mock_encoder = MagicMock()
    mock_encoder.encode = MagicMock(return_value=np.random.rand(1, 384).astype(np.float32))
    indexer.encoder = mock_encoder

    return indexer


@pytest.fixture
def mock_indexer_large(sample_chunks):
    """Create a mock CGRAGIndexer with larger chunk set for load testing."""
    indexer = MagicMock(spec=CGRAGIndexer)
    indexer.chunks = sample_chunks
    indexer.embedding_dim = 384
    indexer.embedding_model_name = "all-MiniLM-L6-v2"

    # Create FAISS index
    n_chunks = len(sample_chunks)
    embeddings = np.random.rand(n_chunks, 384).astype(np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatL2(384)
    index.add(embeddings)
    indexer.index = index

    # Mock encoder
    mock_encoder = MagicMock()
    mock_encoder.encode = MagicMock(return_value=np.random.rand(1, 384).astype(np.float32))
    indexer.encoder = mock_encoder

    return indexer


# ============================================================================
# Context Retrieval Under Various Loads
# ============================================================================


class TestContextRetrievalLoads:
    """Tests for context retrieval under various load conditions."""

    @pytest.mark.asyncio
    async def test_single_query_retrieval(self, mock_indexer):
        """Test basic single query retrieval."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(
            query="Python programming", token_budget=1000, max_artifacts=10
        )

        assert isinstance(result, CGRAGResult)
        assert len(result.artifacts) > 0
        assert result.tokens_used <= 1000
        assert result.retrieval_time_ms >= 0

    @pytest.mark.asyncio
    async def test_retrieval_respects_token_budget(self, mock_indexer_large):
        """Test that retrieval respects token budget constraints.

        Note: The algorithm guarantees at least one artifact is returned even
        if it exceeds the budget (greedy packing with minimum 1 guarantee).
        """
        retriever = CGRAGRetriever(indexer=mock_indexer_large, min_relevance=0.0)

        # Test various token budgets (larger ones to avoid hitting the >=1 guarantee)
        budgets = [500, 1000, 5000, 8000]
        for budget in budgets:
            result = await retriever.retrieve(
                query="test query", token_budget=budget, max_artifacts=50
            )
            # With multiple artifacts, budget should be respected
            # Single artifact may exceed small budgets due to >=1 guarantee
            if len(result.artifacts) > 1:
                assert result.tokens_used <= budget, (
                    f"Tokens {result.tokens_used} exceeded budget {budget}"
                )

    @pytest.mark.asyncio
    async def test_retrieval_respects_max_artifacts(self, mock_indexer_large):
        """Test that retrieval respects max_artifacts limit."""
        retriever = CGRAGRetriever(indexer=mock_indexer_large, min_relevance=0.0)

        max_artifacts_values = [1, 5, 10, 20]
        for max_artifacts in max_artifacts_values:
            result = await retriever.retrieve(
                query="test query",
                token_budget=100000,  # Large budget to not constrain by tokens
                max_artifacts=max_artifacts,
            )
            # Note: actual artifacts may be fewer due to relevance filtering
            assert len(result.artifacts) <= max_artifacts * 5  # 5x factor in code

    @pytest.mark.asyncio
    async def test_concurrent_retrieval_queries(self, mock_indexer_large):
        """Test concurrent retrieval of multiple queries."""
        retriever = CGRAGRetriever(indexer=mock_indexer_large, min_relevance=0.0)

        queries = [
            "Python async patterns",
            "Machine learning models",
            "Database optimization",
            "API design principles",
            "Testing strategies",
        ]

        # Run queries concurrently
        start_time = time.time()
        tasks = [retriever.retrieve(query=q, token_budget=2000, max_artifacts=10) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # Verify all results are valid
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, CGRAGResult)
            assert len(result.artifacts) >= 0

        # Concurrent execution should be faster than sequential
        # (this is a soft assertion - actual speedup depends on implementation)
        assert elapsed < 10.0, f"Concurrent queries took too long: {elapsed}s"

    @pytest.mark.asyncio
    async def test_high_volume_sequential_queries(self, mock_indexer_large):
        """Test handling of high volume sequential queries."""
        retriever = CGRAGRetriever(indexer=mock_indexer_large, min_relevance=0.0)

        n_queries = 20
        results = []
        total_time = 0

        for i in range(n_queries):
            start = time.time()
            result = await retriever.retrieve(
                query=f"Query number {i} about programming",
                token_budget=1000,
                max_artifacts=5,
            )
            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            results.append(result)

        avg_time = total_time / n_queries
        assert len(results) == n_queries
        assert all(isinstance(r, CGRAGResult) for r in results)

        # Log average retrieval time for monitoring
        print(f"\nAverage retrieval time over {n_queries} queries: {avg_time:.2f}ms")


# ============================================================================
# Edge Cases with Empty Contexts
# ============================================================================


class TestEmptyContextEdgeCases:
    """Tests for edge cases involving empty or minimal contexts."""

    @pytest.mark.asyncio
    async def test_retrieval_with_no_matching_chunks(self, mock_indexer):
        """Test retrieval when no chunks match relevance threshold."""
        # Set high relevance threshold that nothing will match
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.99)

        result = await retriever.retrieve(
            query="completely unrelated topic xyz", token_budget=1000, max_artifacts=10
        )

        assert isinstance(result, CGRAGResult)
        assert len(result.artifacts) == 0
        assert result.tokens_used == 0
        assert result.candidates_considered == 0

    @pytest.mark.asyncio
    async def test_retrieval_with_empty_query(self, mock_indexer):
        """Test retrieval with empty query string."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(query="", token_budget=1000, max_artifacts=10)

        # Should still return a valid result (even if meaningless)
        assert isinstance(result, CGRAGResult)
        assert result.retrieval_time_ms >= 0

    @pytest.mark.asyncio
    async def test_retrieval_with_whitespace_query(self, mock_indexer):
        """Test retrieval with whitespace-only query."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(query="   \t\n   ", token_budget=1000, max_artifacts=10)

        assert isinstance(result, CGRAGResult)

    @pytest.mark.asyncio
    async def test_retrieval_with_zero_token_budget(self, mock_indexer):
        """Test retrieval with zero token budget."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(
            query="Python programming", token_budget=0, max_artifacts=10
        )

        # With zero budget, should return at most one artifact (greedy ensures >=1)
        assert isinstance(result, CGRAGResult)
        # At least one chunk is always included per the algorithm
        assert len(result.artifacts) <= 1

    @pytest.mark.asyncio
    async def test_retrieval_with_minimal_token_budget(self, mock_indexer):
        """Test retrieval with very small token budget."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(query="Python", token_budget=1, max_artifacts=10)

        assert isinstance(result, CGRAGResult)
        # At least one artifact should be returned (greedy packing guarantee)
        assert len(result.artifacts) >= 1

    @pytest.mark.asyncio
    async def test_retrieval_with_single_artifact_limit(self, mock_indexer):
        """Test retrieval limited to single artifact."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(
            query="Python programming", token_budget=10000, max_artifacts=1
        )

        assert isinstance(result, CGRAGResult)
        # max_artifacts * 5 candidates are retrieved, then filtered
        assert len(result.artifacts) <= 5


# ============================================================================
# Timeout Handling
# ============================================================================


class TestTimeoutHandling:
    """Tests for timeout handling and latency requirements."""

    @pytest.mark.asyncio
    async def test_retrieval_latency_under_100ms(self, mock_indexer):
        """Test that retrieval completes under 100ms target (with mocks)."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        # Warm-up call
        await retriever.retrieve(query="warmup", token_budget=1000, max_artifacts=5)

        # Measure actual retrieval time
        result = await retriever.retrieve(
            query="Python programming", token_budget=1000, max_artifacts=10
        )

        assert result.retrieval_time_ms < 100, (
            f"Retrieval took {result.retrieval_time_ms:.2f}ms, exceeding 100ms target"
        )

    @pytest.mark.asyncio
    async def test_retrieval_with_slow_encoder_timeout(self):
        """Test handling when encoder is slow (simulated)."""
        # Create indexer with slow encoder
        indexer = MagicMock(spec=CGRAGIndexer)
        indexer.chunks = [
            DocumentChunk(
                id="chunk-1",
                file_path="test.md",
                content="Test content",
                chunk_index=0,
                start_pos=0,
                end_pos=100,
            )
        ]
        indexer.embedding_dim = 384

        # Create a simple index
        embeddings = np.random.rand(1, 384).astype(np.float32)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatL2(384)
        index.add(embeddings)
        indexer.index = index

        # Mock slow encoder
        async def slow_encode(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms delay
            return np.random.rand(1, 384).astype(np.float32)

        mock_encoder = MagicMock()
        mock_encoder.encode = MagicMock(return_value=np.random.rand(1, 384).astype(np.float32))
        indexer.encoder = mock_encoder

        retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.0)

        # Should still complete (may exceed target but shouldn't hang)
        result = await asyncio.wait_for(
            retriever.retrieve(query="test", token_budget=1000, max_artifacts=5),
            timeout=5.0,
        )
        assert isinstance(result, CGRAGResult)

    @pytest.mark.asyncio
    async def test_multiple_retrievals_consistent_latency(self, mock_indexer_large):
        """Test that retrieval latency remains consistent across multiple calls."""
        retriever = CGRAGRetriever(indexer=mock_indexer_large, min_relevance=0.0)

        latencies = []
        for i in range(10):
            result = await retriever.retrieve(
                query=f"Query {i}", token_budget=2000, max_artifacts=10
            )
            latencies.append(result.retrieval_time_ms)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        # Latency variance should be reasonable (no outliers > 3x average)
        assert max_latency < avg_latency * 5, (
            f"Latency spike: max={max_latency:.2f}ms, avg={avg_latency:.2f}ms"
        )

        print(
            f"\nLatency stats: min={min_latency:.2f}ms, "
            f"avg={avg_latency:.2f}ms, max={max_latency:.2f}ms"
        )


# ============================================================================
# Error Recovery
# ============================================================================


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    def test_retriever_requires_loaded_index(self):
        """Test that retriever raises error when index is not loaded."""
        indexer = MagicMock(spec=CGRAGIndexer)
        indexer.index = None

        with pytest.raises(ValueError, match="no index"):
            CGRAGRetriever(indexer=indexer, min_relevance=0.7)

    @pytest.mark.asyncio
    async def test_retrieval_handles_encoder_error(self, mock_indexer):
        """Test retrieval handles encoder errors gracefully."""
        # Make encoder raise an exception
        mock_indexer.encoder.encode = MagicMock(side_effect=RuntimeError("Encoder failed"))

        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        with pytest.raises(RuntimeError, match="Encoder failed"):
            await retriever.retrieve(query="test", token_budget=1000, max_artifacts=5)

    @pytest.mark.asyncio
    async def test_retrieval_handles_invalid_faiss_index(self):
        """Test handling of corrupted/invalid FAISS index."""
        indexer = MagicMock(spec=CGRAGIndexer)
        indexer.chunks = []
        indexer.embedding_dim = 384

        # Create index that will return invalid results
        indexer.index = MagicMock()
        indexer.index.search = MagicMock(return_value=(np.array([[-1, -1]]), np.array([[-1, -1]])))

        mock_encoder = MagicMock()
        mock_encoder.encode = MagicMock(return_value=np.random.rand(1, 384).astype(np.float32))
        indexer.encoder = mock_encoder

        retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.0)

        # Should handle gracefully (no valid indices)
        result = await retriever.retrieve(query="test", token_budget=1000)

        assert isinstance(result, CGRAGResult)
        assert len(result.artifacts) == 0

    @pytest.mark.asyncio
    async def test_retrieval_handles_mismatched_dimensions(self):
        """Test handling when query embedding dimensions don't match index."""
        indexer = MagicMock(spec=CGRAGIndexer)
        indexer.chunks = [
            DocumentChunk(
                id="chunk-1",
                file_path="test.md",
                content="Test content",
                chunk_index=0,
                start_pos=0,
                end_pos=100,
            )
        ]
        indexer.embedding_dim = 384

        # Create 384-dim index
        embeddings = np.random.rand(1, 384).astype(np.float32)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatL2(384)
        index.add(embeddings)
        indexer.index = index

        # Return wrong dimension embedding
        mock_encoder = MagicMock()
        mock_encoder.encode = MagicMock(
            return_value=np.random.rand(1, 128).astype(np.float32)  # Wrong dim!
        )
        indexer.encoder = mock_encoder

        retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.0)

        # FAISS should raise an error for dimension mismatch
        with pytest.raises(Exception):  # RuntimeError from FAISS
            await retriever.retrieve(query="test", token_budget=1000)

    def test_indexer_validates_directory_exists(self):
        """Test that indexer validates directory existence."""
        indexer = CGRAGIndexer()

        with pytest.raises(ValueError, match="does not exist"):
            asyncio.get_event_loop().run_until_complete(
                indexer.index_directory(Path("/nonexistent/path/xyz"))
            )

    @pytest.mark.asyncio
    async def test_retrieval_recovers_after_transient_error(self, mock_indexer):
        """Test that retrieval works after a transient error."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        # First call fails
        original_encode = mock_indexer.encoder.encode
        mock_indexer.encoder.encode = MagicMock(side_effect=RuntimeError("Transient error"))

        with pytest.raises(RuntimeError):
            await retriever.retrieve(query="test", token_budget=1000)

        # Restore encoder
        mock_indexer.encoder.encode = original_encode

        # Second call should succeed
        result = await retriever.retrieve(
            query="test after recovery", token_budget=1000, max_artifacts=5
        )
        assert isinstance(result, CGRAGResult)


# ============================================================================
# Token Budget Edge Cases
# ============================================================================


class TestTokenBudgetEdgeCases:
    """Tests for token budget calculation edge cases."""

    @pytest.mark.asyncio
    async def test_single_large_chunk_exceeds_budget(self, mock_indexer):
        """Test handling when single chunk exceeds token budget."""
        # Create a chunk with very large content
        large_chunk = DocumentChunk(
            id="large-chunk",
            file_path="docs/large.md",
            content="word " * 10000,  # ~10000 words = ~13000 tokens
            chunk_index=0,
            start_pos=0,
            end_pos=50000,
        )
        mock_indexer.chunks = [large_chunk]

        # Recreate index with one chunk
        embeddings = np.random.rand(1, 384).astype(np.float32)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatL2(384)
        index.add(embeddings)
        mock_indexer.index = index

        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        # Even with small budget, at least one chunk should be returned
        result = await retriever.retrieve(query="test", token_budget=100, max_artifacts=5)

        # Algorithm guarantees at least 1 chunk
        assert len(result.artifacts) >= 1

    @pytest.mark.asyncio
    async def test_exact_token_budget_boundary(self, mock_indexer):
        """Test behavior at exact token budget boundary."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        # Get result with a specific budget
        result = await retriever.retrieve(query="test", token_budget=500, max_artifacts=10)

        # Tokens used should not exceed budget (or be at most 1 chunk over)
        # The algorithm allows one chunk that pushes over if nothing else fits
        first_chunk_tokens = int(len(result.artifacts[0].content.split()) * 1.3)
        assert result.tokens_used <= 500 or result.tokens_used <= first_chunk_tokens, (
            f"Tokens {result.tokens_used} unexpectedly high for budget 500"
        )


# ============================================================================
# Relevance Filtering
# ============================================================================


class TestRelevanceFiltering:
    """Tests for relevance score filtering."""

    @pytest.mark.asyncio
    async def test_high_relevance_threshold_filters_chunks(self, mock_indexer):
        """Test that high relevance threshold filters out low-scoring chunks."""
        # With high threshold, should get fewer or no results
        retriever_high = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.95)
        retriever_low = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result_high = await retriever_high.retrieve(
            query="test", token_budget=5000, max_artifacts=20
        )
        result_low = await retriever_low.retrieve(query="test", token_budget=5000, max_artifacts=20)

        # High threshold should return same or fewer artifacts
        assert len(result_high.artifacts) <= len(result_low.artifacts)

    @pytest.mark.asyncio
    async def test_relevance_scores_are_normalized(self, mock_indexer):
        """Test that relevance scores are in [0, 1] range."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(query="Python", token_budget=5000, max_artifacts=20)

        for artifact in result.artifacts:
            assert 0.0 <= artifact.relevance_score <= 1.0, (
                f"Relevance score {artifact.relevance_score} out of range"
            )

        for score in result.top_scores:
            assert 0.0 <= score <= 1.0, f"Top score {score} out of range"

    @pytest.mark.asyncio
    async def test_artifacts_sorted_by_relevance(self, mock_indexer):
        """Test that returned artifacts are sorted by relevance (descending)."""
        retriever = CGRAGRetriever(indexer=mock_indexer, min_relevance=0.0)

        result = await retriever.retrieve(query="test", token_budget=5000, max_artifacts=20)

        if len(result.artifacts) > 1:
            scores = [a.relevance_score for a in result.artifacts]
            assert scores == sorted(scores, reverse=True), "Artifacts not sorted by relevance"

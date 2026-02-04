"""Tests for the routing module - Query complexity assessment.

Tests the assess_complexity function and related helper functions
for determining query complexity and appropriate model tier selection.
"""

import pytest

from app.services.routing import (
    assess_complexity,
    _detect_pattern_type,
    _calculate_score,
    _map_score_to_tier,
    _build_reasoning,
    SIMPLE_PATTERNS,
    MODERATE_PATTERNS,
    COMPLEX_PATTERNS,
)
from app.models.config import RoutingConfig
from app.models.query import QueryComplexity


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def default_routing_config():
    """Create a default routing configuration for testing."""
    return RoutingConfig(
        complexity_thresholds={"fast": 3.0, "balanced": 7.0},
        model_tiers={"fast": [], "balanced": [], "powerful": []},
    )


@pytest.fixture
def strict_routing_config():
    """Create a stricter routing configuration with lower thresholds."""
    return RoutingConfig(
        complexity_thresholds={"fast": 2.0, "balanced": 5.0},
        model_tiers={"fast": [], "balanced": [], "powerful": []},
    )


# ============================================================================
# Pattern Detection Tests
# ============================================================================


class TestPatternDetection:
    """Tests for _detect_pattern_type function."""

    def test_detect_simple_patterns(self):
        """Should detect simple query patterns correctly."""
        simple_queries = [
            "what is python",
            "who is alan turing",
            "when was linux created",
            "where is google headquarters",
            "list all programming languages",
            "define machine learning",
        ]
        for query in simple_queries:
            assert _detect_pattern_type(query) == "simple", (
                f"Expected 'simple' for: {query}"
            )

    def test_detect_moderate_patterns(self):
        """Should detect moderate complexity patterns correctly."""
        moderate_queries = [
            "explain how neural networks work",
            "compare python and javascript",
            "summarize the article about AI",
            "why does this code fail",
            "difference between lists and tuples",
        ]
        for query in moderate_queries:
            assert _detect_pattern_type(query) == "moderate", (
                f"Expected 'moderate' for: {query}"
            )

    def test_detect_complex_patterns(self):
        """Should detect complex query patterns correctly."""
        complex_queries = [
            "analyze the performance implications of this algorithm",
            "evaluate the security risks of this approach",
            "design a microservices architecture",
            "architect a scalable database solution",
            "synthesize information from multiple sources",
            "critique this implementation strategy",
            "propose a solution for the latency problem",
        ]
        for query in complex_queries:
            assert _detect_pattern_type(query) == "complex", (
                f"Expected 'complex' for: {query}"
            )

    def test_no_pattern_detected(self):
        """Should return 'none' when no clear pattern is detected."""
        ambiguous_queries = [
            "hello world",
            "python programming tips",
            "best practices for coding",
            "quick question about syntax",
        ]
        for query in ambiguous_queries:
            assert _detect_pattern_type(query) == "none", (
                f"Expected 'none' for: {query}"
            )

    def test_pattern_priority_complex_over_moderate(self):
        """Complex patterns should take priority over moderate patterns."""
        # This query contains both 'analyze' (complex) and 'explain' (moderate)
        query = "analyze and explain the system architecture"
        assert _detect_pattern_type(query) == "complex"

    def test_pattern_priority_moderate_over_simple(self):
        """Moderate patterns should take priority over simple patterns."""
        # This query contains both 'compare' (moderate) and 'what is' (simple)
        query = "compare what is python vs what is javascript"
        assert _detect_pattern_type(query) == "moderate"

    def test_case_insensitivity(self):
        """Pattern detection should be case-insensitive when query is lowercased first."""
        # Note: _detect_pattern_type expects pre-lowercased input
        assert _detect_pattern_type("what is python") == "simple"
        assert _detect_pattern_type("explain machine learning") == "moderate"
        assert _detect_pattern_type("analyze this data") == "complex"


# ============================================================================
# Score Calculation Tests
# ============================================================================


class TestScoreCalculation:
    """Tests for _calculate_score function."""

    def test_base_score_from_token_count(self):
        """Base score should increase with token count."""
        # With no patterns or structural indicators, score should be token_count * 0.05 + 1.0 (none pattern)
        score_5_tokens = _calculate_score(
            token_count=5,
            pattern_type="none",
            has_multiple_parts=False,
            has_multiple_questions=False,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
        )
        score_20_tokens = _calculate_score(
            token_count=20,
            pattern_type="none",
            has_multiple_parts=False,
            has_multiple_questions=False,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
        )
        assert score_5_tokens < score_20_tokens
        assert score_5_tokens == pytest.approx(5 * 0.05 + 1.0)
        assert score_20_tokens == pytest.approx(20 * 0.05 + 1.0)

    def test_pattern_type_bonus(self):
        """Different pattern types should add different bonuses."""
        base_args = dict(
            token_count=10,
            has_multiple_parts=False,
            has_multiple_questions=False,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
        )

        score_simple = _calculate_score(pattern_type="simple", **base_args)
        score_moderate = _calculate_score(pattern_type="moderate", **base_args)
        score_complex = _calculate_score(pattern_type="complex", **base_args)
        score_none = _calculate_score(pattern_type="none", **base_args)

        # Verify relative ordering
        assert score_simple < score_moderate < score_complex
        # Verify specific bonuses (base = 10 * 0.05 = 0.5)
        assert score_simple == pytest.approx(0.5 + 0.5)  # simple adds 0.5
        assert score_moderate == pytest.approx(0.5 + 2.0)  # moderate adds 2.0
        assert score_complex == pytest.approx(0.5 + 5.0)  # complex adds 5.0
        assert score_none == pytest.approx(0.5 + 1.0)  # none adds 1.0

    def test_structural_complexity_bonuses(self):
        """Structural indicators should add complexity bonuses."""
        base_args = dict(token_count=10, pattern_type="none")

        score_minimal = _calculate_score(
            has_multiple_parts=False,
            has_multiple_questions=False,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
            **base_args,
        )

        score_with_multiple_parts = _calculate_score(
            has_multiple_parts=True,
            has_multiple_questions=False,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
            **base_args,
        )

        score_with_multiple_questions = _calculate_score(
            has_multiple_parts=False,
            has_multiple_questions=True,
            has_conditionals=False,
            has_reasoning_indicators=False,
            has_enumeration=False,
            **base_args,
        )

        score_with_conditionals = _calculate_score(
            has_multiple_parts=False,
            has_multiple_questions=False,
            has_conditionals=True,
            has_reasoning_indicators=False,
            has_enumeration=False,
            **base_args,
        )

        # Verify bonuses are added
        assert score_with_multiple_parts == score_minimal + 2.0
        assert score_with_multiple_questions == score_minimal + 1.5
        assert score_with_conditionals == score_minimal + 1.0

    def test_cumulative_bonuses(self):
        """Multiple structural indicators should stack."""
        base_args = dict(token_count=10, pattern_type="none")

        score_all_bonuses = _calculate_score(
            has_multiple_parts=True,
            has_multiple_questions=True,
            has_conditionals=True,
            has_reasoning_indicators=True,
            has_enumeration=True,
            **base_args,
        )

        # Expected: 0.5 (tokens) + 1.0 (none) + 2.0 + 1.5 + 1.0 + 1.5 + 1.0 = 8.5
        expected = 0.5 + 1.0 + 2.0 + 1.5 + 1.0 + 1.5 + 1.0
        assert score_all_bonuses == pytest.approx(expected)


# ============================================================================
# Tier Mapping Tests
# ============================================================================


class TestTierMapping:
    """Tests for _map_score_to_tier function."""

    def test_fast_tier_mapping(self, default_routing_config):
        """Scores below fast threshold should map to fast tier."""
        assert _map_score_to_tier(0.5, default_routing_config) == "fast"
        assert _map_score_to_tier(2.0, default_routing_config) == "fast"
        assert _map_score_to_tier(2.9, default_routing_config) == "fast"

    def test_balanced_tier_mapping(self, default_routing_config):
        """Scores between fast and balanced thresholds should map to balanced."""
        assert _map_score_to_tier(3.0, default_routing_config) == "balanced"
        assert _map_score_to_tier(5.0, default_routing_config) == "balanced"
        assert _map_score_to_tier(6.9, default_routing_config) == "balanced"

    def test_powerful_tier_mapping(self, default_routing_config):
        """Scores at or above balanced threshold should map to powerful."""
        assert _map_score_to_tier(7.0, default_routing_config) == "powerful"
        assert _map_score_to_tier(10.0, default_routing_config) == "powerful"
        assert _map_score_to_tier(15.0, default_routing_config) == "powerful"

    def test_boundary_conditions(self, default_routing_config):
        """Test exact boundary values."""
        # Just below fast threshold -> fast
        assert _map_score_to_tier(2.999, default_routing_config) == "fast"
        # At fast threshold -> balanced
        assert _map_score_to_tier(3.0, default_routing_config) == "balanced"
        # Just below balanced threshold -> balanced
        assert _map_score_to_tier(6.999, default_routing_config) == "balanced"
        # At balanced threshold -> powerful
        assert _map_score_to_tier(7.0, default_routing_config) == "powerful"

    def test_custom_thresholds(self, strict_routing_config):
        """Custom thresholds should be respected."""
        # With thresholds fast=2.0, balanced=5.0
        assert _map_score_to_tier(1.9, strict_routing_config) == "fast"
        assert _map_score_to_tier(2.0, strict_routing_config) == "balanced"
        assert _map_score_to_tier(4.9, strict_routing_config) == "balanced"
        assert _map_score_to_tier(5.0, strict_routing_config) == "powerful"


# ============================================================================
# Reasoning Builder Tests
# ============================================================================


class TestReasoningBuilder:
    """Tests for _build_reasoning function."""

    def test_fast_tier_reasoning(self):
        """Fast tier should have appropriate reasoning text."""
        reasoning = _build_reasoning(
            tier="fast", score=1.5, pattern_type="simple", token_count=10
        )
        assert "Score: 1.50" in reasoning
        assert "FAST tier" in reasoning
        assert "2B-7B models" in reasoning
        assert "<2s" in reasoning
        assert "simple query pattern" in reasoning

    def test_balanced_tier_reasoning(self):
        """Balanced tier should have appropriate reasoning text."""
        reasoning = _build_reasoning(
            tier="balanced", score=5.0, pattern_type="moderate", token_count=20
        )
        assert "Score: 5.00" in reasoning
        assert "BALANCED tier" in reasoning
        assert "8B-14B models" in reasoning
        assert "<5s" in reasoning
        assert "moderate" in reasoning

    def test_powerful_tier_reasoning(self):
        """Powerful tier should have appropriate reasoning text."""
        reasoning = _build_reasoning(
            tier="powerful", score=9.5, pattern_type="complex", token_count=80
        )
        assert "Score: 9.50" in reasoning
        assert "POWERFUL tier" in reasoning
        assert ">14B models" in reasoning
        assert "<15s" in reasoning
        assert "complex" in reasoning
        # Long query should mention token count
        assert "80 tokens" in reasoning

    def test_no_pattern_omitted(self):
        """When pattern type is 'none', pattern info should be omitted."""
        reasoning = _build_reasoning(
            tier="fast", score=1.5, pattern_type="none", token_count=10
        )
        assert "query pattern" not in reasoning


# ============================================================================
# Integration Tests - Full Complexity Assessment
# ============================================================================


class TestAssessComplexity:
    """Integration tests for the full assess_complexity function."""

    @pytest.mark.asyncio
    async def test_simple_query_routes_to_fast(self, default_routing_config):
        """Simple queries should route to fast tier."""
        result = await assess_complexity("What is Python?", default_routing_config)

        assert isinstance(result, QueryComplexity)
        assert result.tier == "fast"
        assert result.score < 3.0
        assert "FAST" in result.reasoning

    @pytest.mark.asyncio
    async def test_moderate_query_routes_to_balanced(self, default_routing_config):
        """Moderate queries should route to balanced tier."""
        result = await assess_complexity(
            "Explain how machine learning works and compare it with traditional programming",
            default_routing_config,
        )

        assert result.tier == "balanced"
        assert 3.0 <= result.score < 7.0

    @pytest.mark.asyncio
    async def test_complex_query_routes_to_powerful(self, default_routing_config):
        """Complex queries should route to powerful tier."""
        result = await assess_complexity(
            "Analyze the architectural implications of using microservices, "
            "evaluate the trade-offs between monolithic and distributed systems, "
            "and propose a migration strategy if the current system has high latency. "
            "First, assess the current bottlenecks, then design a solution.",
            default_routing_config,
        )

        assert result.tier == "powerful"
        assert result.score >= 7.0

    @pytest.mark.asyncio
    async def test_indicators_included(self, default_routing_config):
        """Result should include all complexity indicators."""
        result = await assess_complexity(
            "If the system fails, then explain why and also describe recovery steps?",
            default_routing_config,
        )

        assert "indicators" in result.model_dump()
        indicators = result.indicators
        assert "token_count" in indicators
        assert "pattern_type" in indicators
        assert "has_multiple_parts" in indicators
        assert "has_conditionals" in indicators
        assert "has_multiple_questions" in indicators

    @pytest.mark.asyncio
    async def test_multiple_questions_detected(self, default_routing_config):
        """Multiple question marks should be detected."""
        result = await assess_complexity(
            "What is Python? How does it compare to Java? Why would I choose one?",
            default_routing_config,
        )

        assert result.indicators["has_multiple_questions"] is True
        # Multiple questions add complexity
        assert result.score > 1.0

    @pytest.mark.asyncio
    async def test_conditional_detected(self, default_routing_config):
        """Conditional statements should be detected."""
        result = await assess_complexity(
            "If the database connection fails, what should the system do?",
            default_routing_config,
        )

        assert result.indicators["has_conditionals"] is True

    @pytest.mark.asyncio
    async def test_enumeration_detected(self, default_routing_config):
        """Enumeration keywords should be detected."""
        result = await assess_complexity(
            "Explain the process step by step, first showing the initial setup",
            default_routing_config,
        )

        assert result.indicators["has_enumeration"] is True

    @pytest.mark.asyncio
    async def test_reasoning_indicators_detected(self, default_routing_config):
        """Reasoning keywords should be detected."""
        result = await assess_complexity(
            "The cache failed because the memory was full, therefore we need a solution",
            default_routing_config,
        )

        assert result.indicators["has_reasoning_indicators"] is True

    @pytest.mark.asyncio
    async def test_score_rounded_to_two_decimals(self, default_routing_config):
        """Complexity score should be rounded to 2 decimal places."""
        result = await assess_complexity(
            "What is the meaning of life?", default_routing_config
        )

        # Score should be a float with at most 2 decimal places
        score_str = str(result.score)
        if "." in score_str:
            decimal_places = len(score_str.split(".")[1])
            assert decimal_places <= 2


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_query(self, default_routing_config):
        """Empty query should still return a valid result."""
        result = await assess_complexity("", default_routing_config)

        assert isinstance(result, QueryComplexity)
        assert result.tier == "fast"  # Minimal query -> fast tier
        assert result.score >= 0

    @pytest.mark.asyncio
    async def test_very_long_query(self, default_routing_config):
        """Very long queries should route to powerful tier."""
        long_query = " ".join(["word"] * 200)  # 200 words
        result = await assess_complexity(long_query, default_routing_config)

        # Long queries (200 tokens * 0.05 = 10.0 base) should go to powerful
        assert result.tier == "powerful"

    @pytest.mark.asyncio
    async def test_special_characters(self, default_routing_config):
        """Query with special characters should be handled."""
        result = await assess_complexity(
            "What is @#$%^&*()? How do symbols work?", default_routing_config
        )

        assert isinstance(result, QueryComplexity)
        assert result.tier in ["fast", "balanced", "powerful"]

    @pytest.mark.asyncio
    async def test_unicode_query(self, default_routing_config):
        """Unicode queries should be handled."""
        result = await assess_complexity(
            "What is the meaning of 日本語? Explain 中文 encoding.",
            default_routing_config,
        )

        assert isinstance(result, QueryComplexity)

    @pytest.mark.asyncio
    async def test_mixed_case_patterns(self, default_routing_config):
        """Patterns should be detected regardless of case."""
        result_lower = await assess_complexity(
            "analyze this code", default_routing_config
        )
        result_upper = await assess_complexity(
            "ANALYZE this code", default_routing_config
        )
        result_mixed = await assess_complexity(
            "AnAlYzE this code", default_routing_config
        )

        assert result_lower.indicators["pattern_type"] == "complex"
        assert result_upper.indicators["pattern_type"] == "complex"
        assert result_mixed.indicators["pattern_type"] == "complex"


# ============================================================================
# Pattern List Validation
# ============================================================================


class TestPatternLists:
    """Tests to ensure pattern lists are properly defined."""

    def test_simple_patterns_not_empty(self):
        """Simple patterns list should have entries."""
        assert len(SIMPLE_PATTERNS) > 0

    def test_moderate_patterns_not_empty(self):
        """Moderate patterns list should have entries."""
        assert len(MODERATE_PATTERNS) > 0

    def test_complex_patterns_not_empty(self):
        """Complex patterns list should have entries."""
        assert len(COMPLEX_PATTERNS) > 0

    def test_no_pattern_overlap(self):
        """Pattern lists should not have overlapping patterns."""
        simple_set = set(SIMPLE_PATTERNS)
        moderate_set = set(MODERATE_PATTERNS)
        complex_set = set(COMPLEX_PATTERNS)

        assert simple_set.isdisjoint(moderate_set), (
            "Simple and moderate patterns overlap"
        )
        assert simple_set.isdisjoint(complex_set), "Simple and complex patterns overlap"
        assert moderate_set.isdisjoint(complex_set), (
            "Moderate and complex patterns overlap"
        )

    def test_patterns_are_lowercase(self):
        """All patterns should be lowercase for consistent matching."""
        for pattern in SIMPLE_PATTERNS + MODERATE_PATTERNS + COMPLEX_PATTERNS:
            assert pattern == pattern.lower(), f"Pattern not lowercase: {pattern}"

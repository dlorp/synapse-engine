"""Tests for orchestrator status models.

Tests validation, serialization, and model behavior for
orchestrator telemetry data models.
"""

import pytest
from pydantic import ValidationError

from app.models.orchestrator import (
    RoutingDecision,
    TierUtilization,
    ComplexityDistribution,
    OrchestratorStatusResponse,
)


class TestRoutingDecision:
    """Tests for RoutingDecision model."""

    def test_valid_simple_decision(self):
        """Test creating a valid simple routing decision."""
        decision = RoutingDecision(
            id="dec-001",
            query="What time is it?",
            tier="Q2",
            complexity="SIMPLE",
            timestamp="2025-01-30T10:00:00Z",
            score=1.5,
        )
        assert decision.id == "dec-001"
        assert decision.tier == "Q2"
        assert decision.complexity == "SIMPLE"
        assert decision.score == 1.5

    def test_valid_moderate_decision(self):
        """Test creating moderate complexity decision."""
        decision = RoutingDecision(
            id="dec-002",
            query="Explain how photosynthesis works",
            tier="Q3",
            complexity="MODERATE",
            timestamp="2025-01-30T10:00:00Z",
            score=5.0,
        )
        assert decision.tier == "Q3"
        assert decision.complexity == "MODERATE"

    def test_valid_complex_decision(self):
        """Test creating complex routing decision."""
        decision = RoutingDecision(
            id="dec-003",
            query="Analyze the economic implications...",
            tier="Q4",
            complexity="COMPLEX",
            timestamp="2025-01-30T10:00:00Z",
            score=9.5,
        )
        assert decision.tier == "Q4"
        assert decision.complexity == "COMPLEX"

    def test_query_max_length(self):
        """Test query at maximum length is valid."""
        # Note: Pydantic max_length on str doesn't raise by default,
        # it depends on the config. Testing with valid max length.
        decision = RoutingDecision(
            id="dec-004",
            query="x" * 100,
            tier="Q2",
            complexity="SIMPLE",
            timestamp="2025-01-30T10:00:00Z",
            score=1.0,
        )
        assert len(decision.query) == 100

    def test_score_minimum(self):
        """Test score minimum validation."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                id="dec-005",
                query="Test",
                tier="Q2",
                complexity="SIMPLE",
                timestamp="2025-01-30T10:00:00Z",
                score=-0.1,
            )

    def test_score_maximum(self):
        """Test score maximum validation (15.0)."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                id="dec-006",
                query="Test",
                tier="Q2",
                complexity="SIMPLE",
                timestamp="2025-01-30T10:00:00Z",
                score=15.1,
            )

    def test_score_at_maximum(self):
        """Test score at maximum value."""
        decision = RoutingDecision(
            id="dec-007",
            query="Test",
            tier="Q4",
            complexity="COMPLEX",
            timestamp="2025-01-30T10:00:00Z",
            score=15.0,
        )
        assert decision.score == 15.0

    def test_invalid_tier_rejected(self):
        """Test invalid tier values are rejected."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                id="dec-008",
                query="Test",
                tier="Q5",  # Invalid
                complexity="SIMPLE",
                timestamp="2025-01-30T10:00:00Z",
                score=1.0,
            )

    def test_invalid_complexity_rejected(self):
        """Test invalid complexity values are rejected."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                id="dec-009",
                query="Test",
                tier="Q2",
                complexity="EASY",  # Invalid
                timestamp="2025-01-30T10:00:00Z",
                score=1.0,
            )


class TestTierUtilization:
    """Tests for TierUtilization model."""

    def test_valid_tier_utilization(self):
        """Test creating valid tier utilization."""
        util = TierUtilization(
            tier="Q2",
            utilization_percent=75,
            active_requests=3,
            total_processed=1500,
        )
        assert util.tier == "Q2"
        assert util.utilization_percent == 75
        assert util.active_requests == 3
        assert util.total_processed == 1500

    def test_zero_utilization(self):
        """Test zero utilization is valid."""
        util = TierUtilization(
            tier="Q4",
            utilization_percent=0,
            active_requests=0,
            total_processed=0,
        )
        assert util.utilization_percent == 0

    def test_max_utilization(self):
        """Test 100% utilization is valid."""
        util = TierUtilization(
            tier="Q3",
            utilization_percent=100,
            active_requests=10,
            total_processed=5000,
        )
        assert util.utilization_percent == 100

    def test_utilization_over_100_rejected(self):
        """Test utilization over 100% is rejected."""
        with pytest.raises(ValidationError):
            TierUtilization(
                tier="Q2",
                utilization_percent=101,
                active_requests=0,
                total_processed=0,
            )

    def test_negative_utilization_rejected(self):
        """Test negative utilization is rejected."""
        with pytest.raises(ValidationError):
            TierUtilization(
                tier="Q2",
                utilization_percent=-1,
                active_requests=0,
                total_processed=0,
            )

    def test_negative_active_requests_rejected(self):
        """Test negative active requests is rejected."""
        with pytest.raises(ValidationError):
            TierUtilization(
                tier="Q2",
                utilization_percent=50,
                active_requests=-1,
                total_processed=0,
            )

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases."""
        util = TierUtilization(
            tier="Q2",
            utilization_percent=50,
            active_requests=2,
            total_processed=100,
        )
        data = util.model_dump(by_alias=True)
        assert "utilizationPercent" in data
        assert "activeRequests" in data
        assert "totalProcessed" in data


class TestComplexityDistribution:
    """Tests for ComplexityDistribution model."""

    def test_valid_distribution(self):
        """Test valid complexity distribution."""
        dist = ComplexityDistribution(
            simple=45,
            moderate=35,
            complex=20,
        )
        assert dist.simple == 45
        assert dist.moderate == 35
        assert dist.complex == 20

    def test_distribution_sums_to_100(self):
        """Test that distribution can sum to 100%."""
        dist = ComplexityDistribution(
            simple=50,
            moderate=30,
            complex=20,
        )
        total = dist.simple + dist.moderate + dist.complex
        assert total == 100

    def test_all_zero_valid(self):
        """Test all zeros is valid (no queries yet)."""
        dist = ComplexityDistribution(
            simple=0,
            moderate=0,
            complex=0,
        )
        assert dist.simple == 0

    def test_all_simple(self):
        """Test 100% simple queries."""
        dist = ComplexityDistribution(
            simple=100,
            moderate=0,
            complex=0,
        )
        assert dist.simple == 100

    def test_negative_percentage_rejected(self):
        """Test negative percentages are rejected."""
        with pytest.raises(ValidationError):
            ComplexityDistribution(
                simple=-10,
                moderate=60,
                complex=50,
            )

    def test_over_100_percentage_rejected(self):
        """Test percentages over 100 are rejected."""
        with pytest.raises(ValidationError):
            ComplexityDistribution(
                simple=101,
                moderate=0,
                complex=0,
            )


class TestOrchestratorStatusResponse:
    """Tests for OrchestratorStatusResponse model."""

    def test_valid_response(self):
        """Test creating valid status response."""
        tier_util = TierUtilization(
            tier="Q2",
            utilization_percent=60,
            active_requests=2,
            total_processed=500,
        )
        decision = RoutingDecision(
            id="dec-001",
            query="Test query",
            tier="Q2",
            complexity="SIMPLE",
            timestamp="2025-01-30T10:00:00Z",
            score=2.0,
        )
        distribution = ComplexityDistribution(
            simple=50,
            moderate=35,
            complex=15,
        )
        response = OrchestratorStatusResponse(
            tier_utilization=[tier_util],
            recent_decisions=[decision],
            complexity_distribution=distribution,
            total_decisions=1000,
            avg_decision_time_ms=12.5,
            timestamp="2025-01-30T10:30:00Z",
        )
        assert response.total_decisions == 1000
        assert response.avg_decision_time_ms == 12.5
        assert len(response.tier_utilization) == 1
        assert len(response.recent_decisions) == 1

    def test_multiple_tiers(self):
        """Test response with all three tiers."""
        tiers = [
            TierUtilization(
                tier="Q2",
                utilization_percent=75,
                active_requests=2,
                total_processed=1250,
            ),
            TierUtilization(
                tier="Q3",
                utilization_percent=50,
                active_requests=1,
                total_processed=680,
            ),
            TierUtilization(
                tier="Q4",
                utilization_percent=25,
                active_requests=0,
                total_processed=320,
            ),
        ]
        distribution = ComplexityDistribution(simple=45, moderate=35, complex=20)
        response = OrchestratorStatusResponse(
            tier_utilization=tiers,
            recent_decisions=[],
            complexity_distribution=distribution,
            total_decisions=2250,
            avg_decision_time_ms=10.0,
            timestamp="2025-01-30T10:30:00Z",
        )
        assert len(response.tier_utilization) == 3

    def test_empty_decisions(self):
        """Test response with no recent decisions."""
        distribution = ComplexityDistribution(simple=0, moderate=0, complex=0)
        response = OrchestratorStatusResponse(
            tier_utilization=[],
            recent_decisions=[],
            complexity_distribution=distribution,
            total_decisions=0,
            avg_decision_time_ms=0.0,
            timestamp="2025-01-30T10:00:00Z",
        )
        assert response.total_decisions == 0
        assert len(response.recent_decisions) == 0

    def test_negative_total_decisions_rejected(self):
        """Test negative total decisions is rejected."""
        distribution = ComplexityDistribution(simple=0, moderate=0, complex=0)
        with pytest.raises(ValidationError):
            OrchestratorStatusResponse(
                tier_utilization=[],
                recent_decisions=[],
                complexity_distribution=distribution,
                total_decisions=-1,
                avg_decision_time_ms=0.0,
                timestamp="2025-01-30T10:00:00Z",
            )

    def test_negative_avg_time_rejected(self):
        """Test negative average decision time is rejected."""
        distribution = ComplexityDistribution(simple=0, moderate=0, complex=0)
        with pytest.raises(ValidationError):
            OrchestratorStatusResponse(
                tier_utilization=[],
                recent_decisions=[],
                complexity_distribution=distribution,
                total_decisions=0,
                avg_decision_time_ms=-1.0,
                timestamp="2025-01-30T10:00:00Z",
            )

    def test_serialization_aliases(self):
        """Test camelCase serialization aliases in response."""
        distribution = ComplexityDistribution(simple=50, moderate=30, complex=20)
        response = OrchestratorStatusResponse(
            tier_utilization=[],
            recent_decisions=[],
            complexity_distribution=distribution,
            total_decisions=100,
            avg_decision_time_ms=5.0,
            timestamp="2025-01-30T10:00:00Z",
        )
        data = response.model_dump(by_alias=True)
        assert "tierUtilization" in data
        assert "recentDecisions" in data
        assert "complexityDistribution" in data
        assert "totalDecisions" in data
        assert "avgDecisionTimeMs" in data

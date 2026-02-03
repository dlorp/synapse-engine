"""Tests for context allocation models.

Tests validation and model behavior for context window
allocation and CGRAG artifact tracking.
"""

import pytest
from pydantic import ValidationError

from app.models.context import (
    ContextComponent,
    CGRAGArtifact,
    ContextAllocation,
    ContextAllocationRequest,
)


class TestContextComponent:
    """Tests for ContextComponent model."""

    def test_valid_system_prompt_component(self):
        """Test creating a valid system prompt component."""
        component = ContextComponent(
            component="system_prompt",
            tokens_used=450,
            tokens_allocated=450,
            percentage=5.5,
            content_preview="You are a helpful AI assistant...",
        )
        assert component.component == "system_prompt"
        assert component.tokens_used == 450
        assert component.percentage == 5.5

    def test_valid_cgrag_context_component(self):
        """Test creating a valid CGRAG context component."""
        component = ContextComponent(
            component="cgrag_context",
            tokens_used=3500,
            tokens_allocated=4000,
            percentage=42.7,
            content_preview="# Architecture Overview...",
        )
        assert component.component == "cgrag_context"
        assert component.tokens_used < component.tokens_allocated

    def test_valid_user_query_component(self):
        """Test creating a valid user query component."""
        component = ContextComponent(
            component="user_query",
            tokens_used=150,
            tokens_allocated=150,
            percentage=1.8,
            content_preview="What is the architecture of...",
        )
        assert component.component == "user_query"

    def test_valid_response_budget_component(self):
        """Test creating a valid response budget component."""
        component = ContextComponent(
            component="response_budget",
            tokens_used=0,
            tokens_allocated=4000,
            percentage=48.8,
        )
        assert component.tokens_used == 0
        assert component.tokens_allocated == 4000
        assert component.content_preview is None

    def test_component_without_preview(self):
        """Test component creation without content preview."""
        component = ContextComponent(
            component="system_prompt",
            tokens_used=100,
            tokens_allocated=100,
            percentage=2.0,
        )
        assert component.content_preview is None

    def test_negative_tokens_rejected(self):
        """Test negative token counts are rejected."""
        with pytest.raises(ValidationError):
            ContextComponent(
                component="test",
                tokens_used=-1,
                tokens_allocated=100,
                percentage=1.0,
            )
        with pytest.raises(ValidationError):
            ContextComponent(
                component="test",
                tokens_used=100,
                tokens_allocated=-1,
                percentage=1.0,
            )

    def test_percentage_minimum(self):
        """Test percentage minimum is 0."""
        component = ContextComponent(
            component="test",
            tokens_used=0,
            tokens_allocated=0,
            percentage=0.0,
        )
        assert component.percentage == 0.0

    def test_percentage_maximum(self):
        """Test percentage maximum is 100."""
        component = ContextComponent(
            component="test",
            tokens_used=8192,
            tokens_allocated=8192,
            percentage=100.0,
        )
        assert component.percentage == 100.0

    def test_percentage_over_100_rejected(self):
        """Test percentage over 100 is rejected."""
        with pytest.raises(ValidationError):
            ContextComponent(
                component="test",
                tokens_used=100,
                tokens_allocated=100,
                percentage=100.1,
            )

    def test_percentage_negative_rejected(self):
        """Test negative percentage is rejected."""
        with pytest.raises(ValidationError):
            ContextComponent(
                component="test",
                tokens_used=100,
                tokens_allocated=100,
                percentage=-0.1,
            )


class TestCGRAGArtifact:
    """Tests for CGRAGArtifact model."""

    def test_valid_artifact(self):
        """Test creating a valid CGRAG artifact."""
        artifact = CGRAGArtifact(
            artifact_id="doc_1",
            source_file="docs/architecture/cgrag.md",
            relevance_score=0.95,
            token_count=1500,
            content_preview="# CGRAG Architecture\n\nThe Contextually-Guided...",
        )
        assert artifact.artifact_id == "doc_1"
        assert artifact.relevance_score == 0.95
        assert artifact.token_count == 1500

    def test_artifact_with_high_relevance(self):
        """Test artifact with perfect relevance score."""
        artifact = CGRAGArtifact(
            artifact_id="doc_exact",
            source_file="exact_match.md",
            relevance_score=1.0,
            token_count=500,
            content_preview="Exact match content",
        )
        assert artifact.relevance_score == 1.0

    def test_artifact_with_low_relevance(self):
        """Test artifact with zero relevance score."""
        artifact = CGRAGArtifact(
            artifact_id="doc_low",
            source_file="low_relevance.md",
            relevance_score=0.0,
            token_count=200,
            content_preview="Low relevance content",
        )
        assert artifact.relevance_score == 0.0

    def test_relevance_score_over_1_rejected(self):
        """Test relevance score over 1.0 is rejected."""
        with pytest.raises(ValidationError):
            CGRAGArtifact(
                artifact_id="doc_invalid",
                source_file="test.md",
                relevance_score=1.1,
                token_count=100,
                content_preview="Test",
            )

    def test_relevance_score_negative_rejected(self):
        """Test negative relevance score is rejected."""
        with pytest.raises(ValidationError):
            CGRAGArtifact(
                artifact_id="doc_invalid",
                source_file="test.md",
                relevance_score=-0.1,
                token_count=100,
                content_preview="Test",
            )

    def test_negative_token_count_rejected(self):
        """Test negative token count is rejected."""
        with pytest.raises(ValidationError):
            CGRAGArtifact(
                artifact_id="doc_invalid",
                source_file="test.md",
                relevance_score=0.5,
                token_count=-1,
                content_preview="Test",
            )

    def test_zero_token_count_valid(self):
        """Test zero token count is valid (empty artifact)."""
        artifact = CGRAGArtifact(
            artifact_id="empty",
            source_file="empty.md",
            relevance_score=0.5,
            token_count=0,
            content_preview="",
        )
        assert artifact.token_count == 0


class TestContextAllocation:
    """Tests for ContextAllocation model."""

    def test_valid_allocation(self):
        """Test creating a valid context allocation."""
        components = [
            ContextComponent(
                component="system_prompt",
                tokens_used=450,
                tokens_allocated=450,
                percentage=5.5,
            ),
            ContextComponent(
                component="user_query",
                tokens_used=150,
                tokens_allocated=150,
                percentage=1.8,
            ),
            ContextComponent(
                component="response_budget",
                tokens_used=0,
                tokens_allocated=4000,
                percentage=48.8,
            ),
        ]
        allocation = ContextAllocation(
            query_id="550e8400-e29b-41d4-a716-446655440000",
            model_id="deepseek-r1:8b",
            context_window_size=8192,
            total_tokens_used=600,
            tokens_remaining=7592,
            utilization_percentage=7.3,
            components=components,
        )
        assert allocation.query_id == "550e8400-e29b-41d4-a716-446655440000"
        assert allocation.context_window_size == 8192
        assert len(allocation.components) == 3
        assert len(allocation.cgrag_artifacts) == 0

    def test_allocation_with_artifacts(self):
        """Test allocation with CGRAG artifacts."""
        artifact = CGRAGArtifact(
            artifact_id="doc_1",
            source_file="test.md",
            relevance_score=0.9,
            token_count=1000,
            content_preview="Test content",
        )
        allocation = ContextAllocation(
            query_id="test-query",
            model_id="test-model",
            context_window_size=8192,
            total_tokens_used=1600,
            tokens_remaining=6592,
            utilization_percentage=19.5,
            components=[],
            cgrag_artifacts=[artifact],
        )
        assert len(allocation.cgrag_artifacts) == 1
        assert allocation.cgrag_artifacts[0].artifact_id == "doc_1"

    def test_allocation_with_warning(self):
        """Test allocation with high utilization warning."""
        allocation = ContextAllocation(
            query_id="test-query",
            model_id="test-model",
            context_window_size=8192,
            total_tokens_used=7200,
            tokens_remaining=992,
            utilization_percentage=87.9,
            components=[],
            warning="Context window >80% utilized - response may be truncated",
        )
        assert allocation.warning is not None
        assert ">80%" in allocation.warning

    def test_zero_context_window_rejected(self):
        """Test zero context window size is rejected."""
        with pytest.raises(ValidationError):
            ContextAllocation(
                query_id="test",
                model_id="test",
                context_window_size=0,
                total_tokens_used=0,
                tokens_remaining=0,
                utilization_percentage=0.0,
                components=[],
            )

    def test_negative_tokens_rejected(self):
        """Test negative token counts are rejected."""
        with pytest.raises(ValidationError):
            ContextAllocation(
                query_id="test",
                model_id="test",
                context_window_size=8192,
                total_tokens_used=-1,
                tokens_remaining=8192,
                utilization_percentage=0.0,
                components=[],
            )
        with pytest.raises(ValidationError):
            ContextAllocation(
                query_id="test",
                model_id="test",
                context_window_size=8192,
                total_tokens_used=0,
                tokens_remaining=-1,
                utilization_percentage=0.0,
                components=[],
            )

    def test_utilization_bounds(self):
        """Test utilization percentage bounds."""
        # Valid at 0%
        allocation = ContextAllocation(
            query_id="test",
            model_id="test",
            context_window_size=8192,
            total_tokens_used=0,
            tokens_remaining=8192,
            utilization_percentage=0.0,
            components=[],
        )
        assert allocation.utilization_percentage == 0.0

        # Valid at 100%
        allocation = ContextAllocation(
            query_id="test",
            model_id="test",
            context_window_size=8192,
            total_tokens_used=8192,
            tokens_remaining=0,
            utilization_percentage=100.0,
            components=[],
        )
        assert allocation.utilization_percentage == 100.0

    def test_utilization_over_100_rejected(self):
        """Test utilization over 100% is rejected."""
        with pytest.raises(ValidationError):
            ContextAllocation(
                query_id="test",
                model_id="test",
                context_window_size=8192,
                total_tokens_used=8192,
                tokens_remaining=0,
                utilization_percentage=100.1,
                components=[],
            )


class TestContextAllocationRequest:
    """Tests for ContextAllocationRequest model."""

    def test_minimal_request(self):
        """Test creating request with minimal fields."""
        req = ContextAllocationRequest(
            query_id="test-query",
            model_id="test-model",
            system_prompt="You are helpful",
            user_query="What is AI?",
            context_window_size=8192,
        )
        assert req.query_id == "test-query"
        assert req.cgrag_context == ""
        assert req.cgrag_artifacts is None

    def test_full_request(self):
        """Test creating request with all fields."""
        artifact = CGRAGArtifact(
            artifact_id="doc_1",
            source_file="test.md",
            relevance_score=0.9,
            token_count=500,
            content_preview="Preview",
        )
        req = ContextAllocationRequest(
            query_id="test-query",
            model_id="test-model",
            system_prompt="System prompt here",
            cgrag_context="Retrieved context goes here",
            user_query="User question",
            context_window_size=32768,
            cgrag_artifacts=[artifact],
        )
        assert req.cgrag_context == "Retrieved context goes here"
        assert len(req.cgrag_artifacts) == 1

    def test_zero_context_window_rejected(self):
        """Test zero context window size is rejected."""
        with pytest.raises(ValidationError):
            ContextAllocationRequest(
                query_id="test",
                model_id="test",
                system_prompt="Test",
                user_query="Test",
                context_window_size=0,
            )

    def test_empty_system_prompt_allowed(self):
        """Test empty system prompt is allowed."""
        req = ContextAllocationRequest(
            query_id="test",
            model_id="test",
            system_prompt="",
            user_query="Query",
            context_window_size=8192,
        )
        assert req.system_prompt == ""

    def test_empty_user_query_allowed(self):
        """Test empty user query is allowed (edge case)."""
        req = ContextAllocationRequest(
            query_id="test",
            model_id="test",
            system_prompt="System",
            user_query="",
            context_window_size=8192,
        )
        assert req.user_query == ""

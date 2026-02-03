"""Unit tests for pipeline and events Pydantic models.

Tests model validation, serialization, and edge cases for the
PipelineStage, PipelineStatus, SystemEvent, and related event models.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.models.pipeline import PipelineStage, PipelineStatus
from app.models.events import (
    EventType,
    EventSeverity,
    SystemEvent,
    QueryRouteEvent,
    ModelStateEvent,
    CGRAGEvent,
    CacheEvent,
    ErrorEvent,
    PerformanceEvent,
    PipelineEvent,
)


class TestPipelineStage:
    """Tests for PipelineStage model."""

    def test_valid_pipeline_stage(self):
        """Test creating a valid pipeline stage."""
        stage = PipelineStage(
            stage_name="complexity",
            status="completed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_ms=42,
            metadata={"complexity_score": 6.5},
        )

        assert stage.stage_name == "complexity"
        assert stage.status == "completed"
        assert stage.duration_ms == 42

    def test_all_valid_stage_names(self):
        """Test all valid stage name literals."""
        valid_names = [
            "input",
            "complexity",
            "cgrag",
            "routing",
            "generation",
            "response",
        ]

        for name in valid_names:
            stage = PipelineStage(stage_name=name, status="pending")
            assert stage.stage_name == name

    def test_invalid_stage_name_raises_error(self):
        """Test that invalid stage name raises validation error."""
        with pytest.raises(PydanticValidationError):
            PipelineStage(stage_name="invalid_stage", status="pending")

    def test_all_valid_status_values(self):
        """Test all valid status literals."""
        valid_statuses = ["pending", "active", "completed", "failed"]

        for status in valid_statuses:
            stage = PipelineStage(stage_name="input", status=status)
            assert stage.status == status

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(PydanticValidationError):
            PipelineStage(stage_name="input", status="invalid_status")

    def test_optional_fields_default_to_none(self):
        """Test that optional fields default to None or empty dict."""
        stage = PipelineStage(stage_name="input", status="pending")

        assert stage.start_time is None
        assert stage.end_time is None
        assert stage.duration_ms is None
        assert stage.metadata == {}

    def test_metadata_can_be_complex(self):
        """Test that metadata can contain complex nested data."""
        complex_metadata = {
            "artifacts": [{"id": 1, "name": "test"}],
            "scores": {"accuracy": 0.95, "speed": 0.8},
            "nested": {"deep": {"value": True}},
        }

        stage = PipelineStage(
            stage_name="cgrag",
            status="completed",
            metadata=complex_metadata,
        )

        assert stage.metadata["artifacts"][0]["id"] == 1
        assert stage.metadata["scores"]["accuracy"] == 0.95

    def test_duration_ms_can_be_zero(self):
        """Test that duration_ms can be zero for instant operations."""
        stage = PipelineStage(
            stage_name="input",
            status="completed",
            duration_ms=0,
        )

        assert stage.duration_ms == 0

    def test_negative_duration_allowed(self):
        """Test that negative duration is technically allowed by the model."""
        # Note: This may be a design decision - negative might be invalid semantically
        # but Pydantic doesn't restrict it unless we add a validator
        stage = PipelineStage(
            stage_name="input",
            status="completed",
            duration_ms=-1,  # Edge case
        )

        assert stage.duration_ms == -1


class TestPipelineStatus:
    """Tests for PipelineStatus model."""

    def test_valid_pipeline_status(self):
        """Test creating a valid pipeline status."""
        stages = [
            PipelineStage(stage_name="input", status="completed"),
            PipelineStage(stage_name="complexity", status="active"),
        ]

        status = PipelineStatus(
            query_id="test-query-123",
            current_stage="complexity",
            stages=stages,
            overall_status="processing",
        )

        assert status.query_id == "test-query-123"
        assert status.current_stage == "complexity"
        assert len(status.stages) == 2
        assert status.overall_status == "processing"

    def test_all_valid_overall_statuses(self):
        """Test all valid overall_status values."""
        for overall in ["processing", "completed", "failed"]:
            status = PipelineStatus(
                query_id="id",
                current_stage="input",
                stages=[],
                overall_status=overall,
            )
            assert status.overall_status == overall

    def test_invalid_overall_status_raises_error(self):
        """Test invalid overall_status raises validation error."""
        with pytest.raises(PydanticValidationError):
            PipelineStatus(
                query_id="id",
                current_stage="input",
                stages=[],
                overall_status="unknown",
            )

    def test_optional_fields_default(self):
        """Test optional fields have correct defaults."""
        status = PipelineStatus(
            query_id="id",
            current_stage="input",
            stages=[],
            overall_status="processing",
        )

        assert status.total_duration_ms is None
        assert status.model_selected is None
        assert status.tier is None
        assert status.cgrag_artifacts_count is None

    def test_complete_pipeline_status(self):
        """Test pipeline status with all fields populated."""
        status = PipelineStatus(
            query_id="complete-query",
            current_stage="response",
            stages=[],
            overall_status="completed",
            total_duration_ms=5000,
            model_selected="deepseek-r1:8b",
            tier="Q3",
            cgrag_artifacts_count=8,
        )

        assert status.total_duration_ms == 5000
        assert status.model_selected == "deepseek-r1:8b"
        assert status.tier == "Q3"
        assert status.cgrag_artifacts_count == 8

    def test_empty_stages_list_allowed(self):
        """Test that empty stages list is valid."""
        status = PipelineStatus(
            query_id="id",
            current_stage="input",
            stages=[],
            overall_status="processing",
        )

        assert status.stages == []


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_have_values(self):
        """Test all event types are accessible."""
        event_types = [
            EventType.QUERY_ROUTE,
            EventType.MODEL_STATE,
            EventType.CGRAG,
            EventType.CACHE,
            EventType.ERROR,
            EventType.PERFORMANCE,
            EventType.PIPELINE_STAGE_START,
            EventType.PIPELINE_STAGE_COMPLETE,
            EventType.PIPELINE_STAGE_FAILED,
            EventType.PIPELINE_COMPLETE,
            EventType.PIPELINE_FAILED,
            EventType.TOPOLOGY_HEALTH_UPDATE,
            EventType.TOPOLOGY_DATAFLOW_UPDATE,
            EventType.LOG,
        ]

        assert len(event_types) == 14

    def test_event_type_values_are_strings(self):
        """Test event type values are snake_case strings."""
        assert EventType.QUERY_ROUTE.value == "query_route"
        assert EventType.MODEL_STATE.value == "model_state"
        assert EventType.PIPELINE_STAGE_START.value == "pipeline_stage_start"


class TestEventSeverity:
    """Tests for EventSeverity enum."""

    def test_all_severity_levels(self):
        """Test all severity levels."""
        assert EventSeverity.INFO.value == "info"
        assert EventSeverity.WARNING.value == "warning"
        assert EventSeverity.ERROR.value == "error"


class TestSystemEvent:
    """Tests for SystemEvent model."""

    def test_valid_system_event(self):
        """Test creating a valid system event."""
        event = SystemEvent(
            timestamp=1699468800.123,
            type=EventType.QUERY_ROUTE,
            message="Query routed to Q4 tier",
            severity=EventSeverity.INFO,
            metadata={"query_id": "abc123"},
        )

        assert event.timestamp == 1699468800.123
        assert event.type == EventType.QUERY_ROUTE
        assert event.message == "Query routed to Q4 tier"

    def test_severity_defaults_to_info(self):
        """Test that severity defaults to INFO."""
        event = SystemEvent(
            timestamp=1234567890.0,
            type=EventType.CACHE,
            message="Cache hit",
        )

        assert event.severity == EventSeverity.INFO

    def test_metadata_defaults_to_empty_dict(self):
        """Test metadata defaults to empty dict."""
        event = SystemEvent(
            timestamp=1234567890.0,
            type=EventType.LOG,
            message="Log entry",
        )

        assert event.metadata == {}

    def test_message_min_length_validation(self):
        """Test that empty message raises validation error."""
        with pytest.raises(PydanticValidationError):
            SystemEvent(
                timestamp=1234567890.0,
                type=EventType.ERROR,
                message="",  # Empty message
            )

    def test_message_max_length_validation(self):
        """Test that very long message raises validation error."""
        with pytest.raises(PydanticValidationError):
            SystemEvent(
                timestamp=1234567890.0,
                type=EventType.ERROR,
                message="x" * 1001,  # Exceeds 1000 char limit
            )

    def test_message_at_max_length(self):
        """Test message at exactly max length is valid."""
        event = SystemEvent(
            timestamp=1234567890.0,
            type=EventType.LOG,
            message="x" * 1000,  # Exactly at limit
        )

        assert len(event.message) == 1000

    def test_model_dump_json_serialization(self):
        """Test that event can be serialized to JSON."""
        event = SystemEvent(
            timestamp=1699468800.0,
            type=EventType.ERROR,
            message="Test error",
            severity=EventSeverity.ERROR,
        )

        json_str = event.model_dump_json()

        # Check key content (JSON format may vary with/without spaces)
        assert "timestamp" in json_str
        assert "1699468800.0" in json_str
        assert '"type":"error"' in json_str or '"type": "error"' in json_str


class TestQueryRouteEvent:
    """Tests for QueryRouteEvent model."""

    def test_valid_query_route_event(self):
        """Test creating a valid query route event."""
        event = QueryRouteEvent(
            query_id="query-123",
            complexity_score=7.5,
            selected_tier="Q3",
            estimated_latency_ms=5000,
            routing_reason="Multi-part query",
        )

        assert event.query_id == "query-123"
        assert event.complexity_score == 7.5
        assert event.selected_tier == "Q3"

    def test_valid_tier_values(self):
        """Test all valid tier values."""
        for tier in ["Q2", "Q3", "Q4"]:
            event = QueryRouteEvent(
                query_id="id",
                complexity_score=5.0,
                selected_tier=tier,
                estimated_latency_ms=1000,
                routing_reason="Test",
            )
            assert event.selected_tier == tier

    def test_invalid_tier_raises_error(self):
        """Test invalid tier raises validation error."""
        with pytest.raises(PydanticValidationError):
            QueryRouteEvent(
                query_id="id",
                complexity_score=5.0,
                selected_tier="Q5",  # Invalid
                estimated_latency_ms=1000,
                routing_reason="Test",
            )


class TestCacheEvent:
    """Tests for CacheEvent model."""

    def test_valid_cache_event(self):
        """Test creating a valid cache event."""
        event = CacheEvent(
            operation="hit",
            key="query:abc:response",
            hit=True,
            latency_ms=2,
            size_bytes=4096,
        )

        assert event.operation == "hit"
        assert event.hit is True
        assert event.size_bytes == 4096

    def test_valid_operation_values(self):
        """Test all valid operation values."""
        for op in ["hit", "miss", "set", "evict"]:
            event = CacheEvent(
                operation=op,
                key="test-key",
                hit=(op == "hit"),
                latency_ms=1,
            )
            assert event.operation == op

    def test_invalid_operation_raises_error(self):
        """Test invalid operation raises validation error."""
        with pytest.raises(PydanticValidationError):
            CacheEvent(
                operation="delete",  # Invalid
                key="key",
                hit=False,
                latency_ms=1,
            )

    def test_size_bytes_optional(self):
        """Test size_bytes is optional."""
        event = CacheEvent(
            operation="miss",
            key="key",
            hit=False,
            latency_ms=1,
        )

        assert event.size_bytes is None


class TestErrorEvent:
    """Tests for ErrorEvent model."""

    def test_valid_error_event(self):
        """Test creating a valid error event."""
        event = ErrorEvent(
            error_type="ModelUnavailableError",
            error_message="Q4 model not responding",
            component="ModelManager",
            stack_trace="Traceback...",
            recovery_action="Retry with Q3 tier",
        )

        assert event.error_type == "ModelUnavailableError"
        assert event.component == "ModelManager"

    def test_optional_fields(self):
        """Test stack_trace and recovery_action are optional."""
        event = ErrorEvent(
            error_type="Error",
            error_message="Something went wrong",
            component="Unknown",
        )

        assert event.stack_trace is None
        assert event.recovery_action is None


class TestPerformanceEvent:
    """Tests for PerformanceEvent model."""

    def test_valid_performance_event(self):
        """Test creating a valid performance event."""
        event = PerformanceEvent(
            metric_name="query_latency_ms",
            current_value=18000,
            threshold_value=15000,
            component="Q4_POWERFUL_1",
            action_required=False,
        )

        assert event.metric_name == "query_latency_ms"
        assert event.current_value == 18000
        assert event.threshold_value == 15000

    def test_action_required_defaults_false(self):
        """Test action_required defaults to False."""
        event = PerformanceEvent(
            metric_name="memory_usage",
            current_value=90.0,
            threshold_value=80.0,
            component="System",
        )

        assert event.action_required is False


class TestPipelineEvent:
    """Tests for PipelineEvent model."""

    def test_valid_pipeline_event(self):
        """Test creating a valid pipeline event."""
        event = PipelineEvent(
            query_id="query-uuid",
            stage="cgrag",
            metadata={"artifacts_retrieved": 8},
        )

        assert event.query_id == "query-uuid"
        assert event.stage == "cgrag"

    def test_all_valid_stages(self):
        """Test all valid stage literals."""
        valid_stages = [
            "input",
            "complexity",
            "cgrag",
            "routing",
            "generation",
            "response",
        ]

        for stage in valid_stages:
            event = PipelineEvent(query_id="id", stage=stage)
            assert event.stage == stage

    def test_invalid_stage_raises_error(self):
        """Test invalid stage raises validation error."""
        with pytest.raises(PydanticValidationError):
            PipelineEvent(query_id="id", stage="invalid")

    def test_metadata_defaults_empty(self):
        """Test metadata defaults to empty dict."""
        event = PipelineEvent(query_id="id", stage="input")

        assert event.metadata == {}


class TestModelStateEvent:
    """Tests for ModelStateEvent model."""

    def test_valid_model_state_event(self):
        """Test creating a valid model state event."""
        event = ModelStateEvent(
            model_id="deepseek_r1_8b",
            previous_state="idle",
            current_state="processing",
            reason="Query dispatched",
            port=8080,
        )

        assert event.model_id == "deepseek_r1_8b"
        assert event.previous_state == "idle"
        assert event.current_state == "processing"
        assert event.port == 8080

    def test_port_optional(self):
        """Test port is optional."""
        event = ModelStateEvent(
            model_id="model",
            previous_state="idle",
            current_state="error",
            reason="Health check failed",
        )

        assert event.port is None


class TestCGRAGEvent:
    """Tests for CGRAGEvent model."""

    def test_valid_cgrag_event(self):
        """Test creating a valid CGRAG event."""
        event = CGRAGEvent(
            query_id="query-123",
            chunks_retrieved=5,
            relevance_threshold=0.7,
            retrieval_time_ms=45,
            total_tokens=1500,
            cache_hit=True,
        )

        assert event.chunks_retrieved == 5
        assert event.relevance_threshold == 0.7
        assert event.cache_hit is True

    def test_all_fields_required(self):
        """Test all fields are required for CGRAGEvent."""
        with pytest.raises(PydanticValidationError):
            CGRAGEvent(
                query_id="id",
                chunks_retrieved=5,
                # Missing other required fields
            )

"""Unit tests for the exceptions module.

Tests all custom exception classes to ensure proper initialization,
serialization to dict, and correct HTTP status codes.
"""

import pytest
from app.core.exceptions import (
    SynapseException,
    ConfigurationError,
    ModelNotFoundError,
    ModelUnavailableError,
    NoModelsAvailableError,
    QueryTimeoutError,
    ValidationError,
)


class TestSynapseException:
    """Tests for the base SynapseException class."""

    def test_basic_initialization(self):
        """Test basic exception initialization with required message."""
        exc = SynapseException("Test error message")

        assert exc.message == "Test error message"
        assert exc.details == {}
        assert exc.status_code == 500
        assert str(exc) == "Test error message"

    def test_initialization_with_details(self):
        """Test exception with custom details dict."""
        details = {"key": "value", "count": 42}
        exc = SynapseException("Error with details", details=details)

        assert exc.details == {"key": "value", "count": 42}

    def test_initialization_with_custom_status_code(self):
        """Test exception with custom HTTP status code."""
        exc = SynapseException("Custom status", status_code=418)

        assert exc.status_code == 418

    def test_to_dict_basic(self):
        """Test to_dict() returns correct structure."""
        exc = SynapseException("Test error")
        result = exc.to_dict()

        assert result == {
            "error": "SynapseException",
            "message": "Test error",
            "details": {},
        }

    def test_to_dict_with_details(self):
        """Test to_dict() includes custom details."""
        exc = SynapseException(
            "Error with metadata",
            details={"request_id": "abc123", "timestamp": 1234567890},
        )
        result = exc.to_dict()

        assert result["details"] == {"request_id": "abc123", "timestamp": 1234567890}

    def test_exception_is_catchable(self):
        """Test that exception can be caught and handled."""
        with pytest.raises(SynapseException) as exc_info:
            raise SynapseException("Raised exception", status_code=503)

        assert exc_info.value.status_code == 503

    def test_none_details_converted_to_empty_dict(self):
        """Test that None details becomes empty dict."""
        exc = SynapseException("Test", details=None)
        assert exc.details == {}


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_default_status_code(self):
        """Test that default status code is 500."""
        exc = ConfigurationError("Config missing")

        assert exc.status_code == 500

    def test_message_inheritance(self):
        """Test message is properly inherited."""
        exc = ConfigurationError("Invalid database config", details={"field": "host"})

        assert exc.message == "Invalid database config"
        assert exc.details == {"field": "host"}

    def test_to_dict_includes_class_name(self):
        """Test to_dict uses ConfigurationError class name."""
        exc = ConfigurationError("Test")
        result = exc.to_dict()

        assert result["error"] == "ConfigurationError"


class TestModelNotFoundError:
    """Tests for ModelNotFoundError exception."""

    def test_model_id_in_message(self):
        """Test that model_id appears in error message."""
        exc = ModelNotFoundError("gpt-4-turbo")

        assert "gpt-4-turbo" in exc.message
        assert exc.message == "Model not found: gpt-4-turbo"

    def test_status_code_is_404(self):
        """Test that status code is 404 (Not Found)."""
        exc = ModelNotFoundError("missing-model")

        assert exc.status_code == 404

    def test_model_id_in_details(self):
        """Test that model_id is included in details."""
        exc = ModelNotFoundError("deepseek-r1")

        assert exc.details["model_id"] == "deepseek-r1"

    def test_additional_details_merged(self):
        """Test that additional details are merged with model_id."""
        exc = ModelNotFoundError(
            "test-model",
            details={"searched_registries": ["local", "remote"]},
        )

        assert exc.details["model_id"] == "test-model"
        assert exc.details["searched_registries"] == ["local", "remote"]

    def test_to_dict_structure(self):
        """Test complete to_dict structure."""
        exc = ModelNotFoundError("my-model")
        result = exc.to_dict()

        assert result["error"] == "ModelNotFoundError"
        assert result["message"] == "Model not found: my-model"
        assert result["details"]["model_id"] == "my-model"


class TestModelUnavailableError:
    """Tests for ModelUnavailableError exception."""

    def test_model_id_and_reason_in_message(self):
        """Test that model_id and reason appear in message."""
        exc = ModelUnavailableError("llama-70b", "Server not responding")

        assert "llama-70b" in exc.message
        assert "Server not responding" in exc.message
        assert exc.message == "Model unavailable: llama-70b - Server not responding"

    def test_status_code_is_503(self):
        """Test that status code is 503 (Service Unavailable)."""
        exc = ModelUnavailableError("model", "reason")

        assert exc.status_code == 503

    def test_details_contain_model_and_reason(self):
        """Test that details include both model_id and reason."""
        exc = ModelUnavailableError("test-model", "High load")

        assert exc.details["model_id"] == "test-model"
        assert exc.details["reason"] == "High load"

    def test_additional_details_merged(self):
        """Test that additional details are preserved."""
        exc = ModelUnavailableError(
            "model",
            "Timeout",
            details={"last_successful_ping": 1234567890},
        )

        assert exc.details["last_successful_ping"] == 1234567890
        assert exc.details["model_id"] == "model"


class TestNoModelsAvailableError:
    """Tests for NoModelsAvailableError exception."""

    def test_tier_in_message(self):
        """Test that tier appears in message."""
        exc = NoModelsAvailableError("Q4")

        assert "Q4" in exc.message
        assert exc.message == "No models available in tier: Q4"

    def test_status_code_is_503(self):
        """Test that status code is 503."""
        exc = NoModelsAvailableError("Q3")

        assert exc.status_code == 503

    def test_tier_in_details(self):
        """Test that tier is in details."""
        exc = NoModelsAvailableError("Q2")

        assert exc.details["tier"] == "Q2"


class TestQueryTimeoutError:
    """Tests for QueryTimeoutError exception."""

    def test_model_id_and_timeout_in_message(self):
        """Test that model_id and timeout appear in message."""
        exc = QueryTimeoutError("claude-3", 30)

        assert "claude-3" in exc.message
        assert "30" in exc.message
        assert exc.message == "Query to claude-3 exceeded timeout of 30s"

    def test_status_code_is_504(self):
        """Test that status code is 504 (Gateway Timeout)."""
        exc = QueryTimeoutError("model", 60)

        assert exc.status_code == 504

    def test_details_contain_model_and_timeout(self):
        """Test that details include both values."""
        exc = QueryTimeoutError("slow-model", 120)

        assert exc.details["model_id"] == "slow-model"
        assert exc.details["timeout_seconds"] == 120

    def test_timeout_zero(self):
        """Test edge case with zero timeout."""
        exc = QueryTimeoutError("instant-model", 0)

        assert exc.details["timeout_seconds"] == 0
        assert "0s" in exc.message


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_custom_message(self):
        """Test that custom message is used."""
        exc = ValidationError("Invalid query format")

        assert exc.message == "Invalid query format"

    def test_status_code_is_422(self):
        """Test that status code is 422 (Unprocessable Entity)."""
        exc = ValidationError("Bad input")

        assert exc.status_code == 422

    def test_validation_details(self):
        """Test that validation details are preserved."""
        exc = ValidationError(
            "Field validation failed",
            details={
                "field": "email",
                "constraint": "must be valid email",
                "received": "not-an-email",
            },
        )

        assert exc.details["field"] == "email"
        assert exc.details["constraint"] == "must be valid email"

    def test_to_dict_structure(self):
        """Test complete to_dict structure for validation errors."""
        exc = ValidationError("Test", details={"fields": ["a", "b"]})
        result = exc.to_dict()

        assert result["error"] == "ValidationError"
        assert result["message"] == "Test"
        assert result["details"]["fields"] == ["a", "b"]


class TestExceptionHierarchy:
    """Tests for the exception class hierarchy."""

    def test_all_exceptions_inherit_from_synapse_exception(self):
        """Test that all custom exceptions inherit from SynapseException."""
        exceptions = [
            ConfigurationError("test"),
            ModelNotFoundError("test"),
            ModelUnavailableError("test", "reason"),
            NoModelsAvailableError("Q3"),
            QueryTimeoutError("test", 30),
            ValidationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, SynapseException)
            assert isinstance(exc, Exception)

    def test_exceptions_can_be_caught_by_base_class(self):
        """Test that all exceptions can be caught by SynapseException."""
        try:
            raise ModelNotFoundError("test")
        except SynapseException as e:
            assert e.status_code == 404

        try:
            raise QueryTimeoutError("test", 30)
        except SynapseException as e:
            assert e.status_code == 504

    def test_exception_chaining(self):
        """Test that exceptions can be chained with __cause__."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as ve:
                raise ConfigurationError("Config failed") from ve
        except ConfigurationError as ce:
            assert ce.__cause__ is not None
            assert isinstance(ce.__cause__, ValueError)

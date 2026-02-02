"""Custom exception hierarchy for S.Y.N.A.P.S.E. CORE (PRAXIS).

All application-specific exceptions inherit from SynapseException to enable
centralized error handling and logging.
"""

from typing import Any, Dict, Optional


class SynapseException(Exception):
    """Base exception for all S.Y.N.A.P.S.E. CORE (PRAXIS) errors.

    Attributes:
        message: Human-readable error message
        details: Additional error context
        status_code: HTTP status code for API responses
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ) -> None:
        """Initialize Synapse exception.

        Args:
            message: Error message
            details: Additional error context
            status_code: HTTP status code for API responses
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Returns:
            Dictionary containing error message and details
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(SynapseException):
    """Raised when configuration is invalid or missing.

    This exception indicates a problem with the application configuration
    that prevents proper initialization or operation.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            details: Additional error context
        """
        super().__init__(
            message=message,
            details=details,
            status_code=500,  # Internal server error
        )


class ModelNotFoundError(SynapseException):
    """Raised when a requested model does not exist.

    This exception indicates that a model with the specified identifier
    is not configured in the system.
    """

    def __init__(self, model_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize model not found error.

        Args:
            model_id: The requested model identifier
            details: Additional error context
        """
        error_details = details or {}
        error_details["model_id"] = model_id

        super().__init__(
            message=f"Model not found: {model_id}",
            details=error_details,
            status_code=404,  # Not found
        )


class ModelUnavailableError(SynapseException):
    """Raised when a model exists but is currently unavailable.

    This exception indicates that a model is configured but cannot
    currently service requests due to health issues, high load, or
    other operational problems.
    """

    def __init__(
        self, model_id: str, reason: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize model unavailable error.

        Args:
            model_id: The unavailable model identifier
            reason: Reason for unavailability
            details: Additional error context
        """
        error_details = details or {}
        error_details["model_id"] = model_id
        error_details["reason"] = reason

        super().__init__(
            message=f"Model unavailable: {model_id} - {reason}",
            details=error_details,
            status_code=503,  # Service unavailable
        )


class NoModelsAvailableError(SynapseException):
    """Raised when no models in a tier are available to service requests.

    This exception indicates a critical situation where all models
    in a requested tier (or all tiers if fallback fails) are unavailable.
    """

    def __init__(self, tier: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize no models available error.

        Args:
            tier: The requested tier
            details: Additional error context
        """
        error_details = details or {}
        error_details["tier"] = tier

        super().__init__(
            message=f"No models available in tier: {tier}",
            details=error_details,
            status_code=503,  # Service unavailable
        )


class QueryTimeoutError(SynapseException):
    """Raised when a model query exceeds the timeout threshold.

    This exception indicates that a request to a model server took
    too long and was cancelled to prevent resource exhaustion.
    """

    def __init__(
        self,
        model_id: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize query timeout error.

        Args:
            model_id: The model that timed out
            timeout_seconds: The timeout threshold that was exceeded
            details: Additional error context
        """
        error_details = details or {}
        error_details["model_id"] = model_id
        error_details["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=f"Query to {model_id} exceeded timeout of {timeout_seconds}s",
            details=error_details,
            status_code=504,  # Gateway timeout
        )


class ValidationError(SynapseException):
    """Raised when request validation fails.

    This exception indicates that the client provided invalid data
    that failed validation checks.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            details: Additional error context
        """
        super().__init__(
            message=message,
            details=details,
            status_code=422,  # Unprocessable entity
        )

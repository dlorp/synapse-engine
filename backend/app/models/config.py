"""Configuration data models using Pydantic for validation."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for a single model instance.

    Attributes:
        name: Model identifier (e.g., qwen_8b_fast)
        tier: Model tier based on parameter size (fast, balanced, powerful)
        url: Base URL for model server
        port: Port number for model server
        max_context_tokens: Maximum context window size
        timeout_seconds: Request timeout in seconds
        max_retries: Maximum retry attempts for failed requests
        retry_delay_seconds: Delay in seconds between retry attempts (linear backoff)
        health_check_interval: Seconds between health checks
    """

    name: str = Field(..., description="Model identifier")
    tier: str = Field(..., description="Model tier (fast, balanced, powerful)")
    url: str = Field(..., description="Model server base URL")
    port: int = Field(..., ge=1, le=65535, description="Model server port")
    max_context_tokens: int = Field(..., gt=0, description="Maximum context window")
    timeout_seconds: int = Field(..., gt=0, description="Request timeout")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(
        default=2, gt=0, description="Linear delay in seconds between retries"
    )
    health_check_interval: int = Field(
        default=10, gt=0, description="Health check interval in seconds"
    )

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Validate tier is one of fast, balanced, powerful."""
        if v not in ["fast", "balanced", "powerful"]:
            raise ValueError(f"Invalid tier: {v}. Must be fast, balanced, or powerful")
        return v


class RoutingConfig(BaseModel):
    """Query routing configuration.

    Attributes:
        complexity_thresholds: Score thresholds for tier selection
        default_tier: Fallback tier when routing fails
        enable_load_balancing: Enable load balancing across FAST tier instances
        prefer_cached: Prefer cached responses when available
    """

    complexity_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"fast": 3.0, "balanced": 7.0, "powerful": 15.0},
        description="Complexity score thresholds for each tier",
    )
    default_tier: str = Field(default="balanced", description="Default tier for routing")
    enable_load_balancing: bool = Field(
        default=True, description="Enable load balancing for FAST tier models"
    )
    prefer_cached: bool = Field(default=True, description="Prefer cached responses")


class RedisConfig(BaseModel):
    """Redis cache configuration.

    Attributes:
        host: Redis server host
        port: Redis server port
        db: Redis database number
        password: Optional Redis password
        default_ttl: Default TTL for cached entries in seconds
        max_connections: Maximum connection pool size
    """

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    db: int = Field(default=0, ge=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    default_ttl: int = Field(default=3600, gt=0, description="Default TTL in seconds")
    max_connections: int = Field(default=10, gt=0, description="Maximum connection pool size")


class LoggingConfig(BaseModel):
    """Logging configuration.

    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (json or text)
        log_file: Optional log file path
        enable_request_logging: Log all HTTP requests
        enable_performance_logging: Log performance metrics
    """

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_request_logging: bool = Field(default=True, description="Enable request logging")
    enable_performance_logging: bool = Field(
        default=True, description="Enable performance metrics logging"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate log format."""
        if v not in ["json", "text"]:
            raise ValueError(f"Invalid log format: {v}. Must be 'json' or 'text'")
        return v


class CGRAGIndexingConfig(BaseModel):
    """CGRAG indexing configuration.

    Attributes:
        chunk_size: Target chunk size in words
        chunk_overlap: Overlap between chunks in words
        embedding_model: Sentence-transformers model name
        embedding_dimension: Dimension of embedding vectors
    """

    chunk_size: int = Field(default=512, gt=0, description="Chunk size in words")
    chunk_overlap: int = Field(default=50, ge=0, description="Chunk overlap in words")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence-transformers model name"
    )
    embedding_dimension: int = Field(default=384, gt=0, description="Embedding vector dimension")


class CGRAGRetrievalConfig(BaseModel):
    """CGRAG retrieval configuration.

    Attributes:
        token_budget: Maximum tokens to retrieve
        min_relevance: Minimum relevance threshold (0.0-1.0)
        max_artifacts: Maximum number of artifacts to consider
        cache_ttl: Cache TTL in seconds
    """

    token_budget: int = Field(default=8000, gt=0, description="Token budget for retrieval")
    min_relevance: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum relevance threshold"
    )
    max_artifacts: int = Field(default=10, gt=0, description="Maximum artifacts to retrieve")
    cache_ttl: int = Field(default=3600, gt=0, description="Cache TTL in seconds")


class CGRAGFAISSConfig(BaseModel):
    """FAISS index configuration.

    Attributes:
        index_type: Index type (Flat or IVF)
        nlist: Number of clusters for IVF index
        nprobe: Number of clusters to search in IVF index
    """

    index_type: str = Field(default="IVF", description="Index type (Flat or IVF)")
    nlist: int = Field(default=100, gt=0, description="Number of IVF clusters")
    nprobe: int = Field(default=10, gt=0, description="Number of clusters to search")

    @field_validator("index_type")
    @classmethod
    def validate_index_type(cls, v: str) -> str:
        """Validate index type."""
        if v not in ["Flat", "IVF"]:
            raise ValueError(f"Invalid index type: {v}. Must be 'Flat' or 'IVF'")
        return v


class CGRAGConfig(BaseModel):
    """CGRAG (Contextually-Guided RAG) configuration.

    Attributes:
        indexing: Indexing configuration
        retrieval: Retrieval configuration
        faiss: FAISS index configuration
    """

    indexing: CGRAGIndexingConfig = Field(
        default_factory=CGRAGIndexingConfig, description="Indexing configuration"
    )
    retrieval: CGRAGRetrievalConfig = Field(
        default_factory=CGRAGRetrievalConfig, description="Retrieval configuration"
    )
    faiss: CGRAGFAISSConfig = Field(
        default_factory=CGRAGFAISSConfig, description="FAISS index configuration"
    )


class ModelManagementConfig(BaseModel):
    """Model management configuration.

    Attributes:
        scan_path: Directory to scan for GGUF models
        registry_path: Path to model registry JSON file
        llama_server_path: Path to llama-server binary
        port_range: Port range for model servers (start, end)
        max_startup_time: Maximum seconds to wait for server startup
        readiness_check_interval: Seconds between readiness checks
        concurrent_starts: Start servers concurrently (faster but higher resource spike)
    """

    scan_path: Path = Field(
        default=Path("/models"), description="Directory to scan for GGUF models"
    )

    registry_path: Path = Field(
        default=Path("data/model_registry.json"),
        description="Path to model registry JSON file",
    )

    llama_server_path: Path = Field(
        default=Path("/usr/local/bin/llama-server"),
        description="Path to llama-server binary",
    )

    port_range: Tuple[int, int] = Field(
        default=(8080, 8099), description="Port range for model servers"
    )

    max_startup_time: int = Field(
        default=120, description="Maximum seconds to wait for server startup"
    )

    readiness_check_interval: int = Field(default=2, description="Seconds between readiness checks")

    concurrent_starts: bool = Field(
        default=True,
        description="Start servers concurrently (faster but higher resource spike)",
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AppConfig(BaseModel):
    """Main application configuration.

    Attributes:
        app_name: Application name
        version: Application version
        environment: Environment (development, staging, production)
        host: Server host
        port: Server port
        debug: Enable debug mode
        cors_origins: List of allowed CORS origins
        models: Dictionary of model configurations
        routing: Routing configuration
        redis: Redis configuration
        logging: Logging configuration
    """

    app_name: str = Field(default="S.Y.N.A.P.S.E. Core (PRAXIS)", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Nested configurations
    models: Dict[str, ModelConfig] = Field(default_factory=dict, description="Model configurations")
    routing: RoutingConfig = Field(
        default_factory=RoutingConfig, description="Routing configuration"
    )
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis configuration")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    cgrag: CGRAGConfig = Field(default_factory=CGRAGConfig, description="CGRAG configuration")
    model_management: ModelManagementConfig = Field(
        default_factory=ModelManagementConfig,
        description="Model management configuration",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v

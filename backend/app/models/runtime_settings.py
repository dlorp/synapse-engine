"""Runtime settings that can be modified via WebUI.

These settings are persisted to data/runtime_settings.json and can be
updated through the /api/settings endpoint without requiring system
reconfiguration or container rebuilds.
"""

from typing import Optional

from pydantic import BaseModel, Field


class RuntimeSettings(BaseModel):
    """WebUI-configurable runtime settings.

    These settings control:
    - GPU/VRAM allocation for llama-server instances
    - HuggingFace embedding model configuration
    - CGRAG retrieval parameters
    - Benchmark mode defaults

    Changes to GPU/VRAM settings require server restart to take effect.
    """

    # ========================================================================
    # GPU/VRAM Configuration (requires server restart)
    # ========================================================================

    n_gpu_layers: int = Field(
        default=99,
        ge=0,
        le=999,
        description="Number of layers to offload to GPU (0=CPU only, 99=max offload)",
    )

    ctx_size: int = Field(
        default=32768,
        ge=512,
        le=131072,
        description="Context window size in tokens (2K, 4K, 8K, 16K, 32K, 64K, 128K)",
    )

    threads: int = Field(default=8, ge=1, le=64, description="Number of CPU threads for processing")

    batch_size: int = Field(
        default=512, ge=32, le=2048, description="Batch size for prompt processing"
    )

    ubatch_size: int = Field(
        default=256, ge=32, le=1024, description="Micro-batch size for generation"
    )

    flash_attn: bool = Field(
        default=True,
        description="Enable Flash Attention for faster inference (GPU only)",
    )

    no_mmap: bool = Field(default=True, description="Disable memory mapping (use for Metal/GPU)")

    # ========================================================================
    # HuggingFace/Embeddings Configuration
    # ========================================================================

    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="HuggingFace sentence-transformers model name",
    )

    embedding_model_cache_path: Optional[str] = Field(
        default=None,
        description="Custom cache path for HuggingFace models (None = use default ~/.cache/huggingface)",
    )

    embedding_dimension: int = Field(
        default=384,
        ge=128,
        le=1536,
        description="Embedding vector dimension (must match model output)",
    )

    # ========================================================================
    # CGRAG Configuration
    # ========================================================================

    cgrag_token_budget: int = Field(
        default=8000,
        ge=1000,
        le=32000,
        description="Maximum tokens to use for CGRAG context",
    )

    cgrag_min_relevance: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score for including artifacts (0.0-1.0)",
    )

    cgrag_chunk_size: int = Field(
        default=512,
        ge=128,
        le=2048,
        description="Text chunk size for CGRAG indexing (tokens)",
    )

    cgrag_chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=512,
        description="Overlap between chunks to preserve context (tokens)",
    )

    cgrag_max_results: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of artifacts to retrieve from FAISS",
    )

    cgrag_index_directory: str = Field(
        default="data/faiss_indexes",
        description="Directory containing CGRAG FAISS indexes (relative to project root)",
    )

    # ========================================================================
    # Benchmark Mode Defaults
    # ========================================================================

    benchmark_default_max_tokens: int = Field(
        default=1024,
        ge=128,
        le=4096,
        description="Default max_tokens per model in benchmark mode",
    )

    benchmark_parallel_max_models: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of models to run in parallel (VRAM constraint)",
    )

    # ========================================================================
    # Web Search Configuration
    # ========================================================================

    websearch_max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of web search results to include",
    )

    websearch_timeout_seconds: int = Field(
        default=10, ge=5, le=30, description="Timeout for web search requests"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "n_gpu_layers": 99,
                "ctx_size": 32768,
                "threads": 8,
                "batch_size": 512,
                "ubatch_size": 256,
                "flash_attn": True,
                "no_mmap": True,
                "embedding_model_name": "all-MiniLM-L6-v2",
                "embedding_model_cache_path": None,
                "embedding_dimension": 384,
                "cgrag_token_budget": 8000,
                "cgrag_min_relevance": 0.7,
                "cgrag_chunk_size": 512,
                "cgrag_chunk_overlap": 50,
                "cgrag_max_results": 20,
                "benchmark_default_max_tokens": 1024,
                "benchmark_parallel_max_models": 5,
                "websearch_max_results": 5,
                "websearch_timeout_seconds": 10,
            }
        }

    def requires_server_restart(self, other: "RuntimeSettings") -> bool:
        """Check if changes between self and other require server restart.

        Args:
            other: Other RuntimeSettings to compare against

        Returns:
            True if any GPU/VRAM/performance settings changed
        """
        restart_fields = {
            "n_gpu_layers",
            "ctx_size",
            "threads",
            "batch_size",
            "ubatch_size",
            "flash_attn",
            "no_mmap",
        }

        for field in restart_fields:
            if getattr(self, field) != getattr(other, field):
                return True

        return False

    def estimate_vram_per_model(
        self, model_size_b: float = 8.0, quantization: str = "Q4_K_M"
    ) -> float:
        """Estimate VRAM usage per model instance.

        Args:
            model_size_b: Model size in billions of parameters
            quantization: Quantization type (Q2_K, Q3_K_M, Q4_K_M, Q8_0)

        Returns:
            Estimated VRAM in GB
        """
        # Quantization multipliers (bytes per parameter)
        QUANT_MULTIPLIERS = {
            "Q2_K": 0.25,
            "Q3_K_S": 0.31,
            "Q3_K_M": 0.35,
            "Q3_K_L": 0.38,
            "Q4_K_S": 0.43,
            "Q4_K_M": 0.50,
            "Q5_K_S": 0.56,
            "Q5_K_M": 0.62,
            "Q6_K": 0.75,
            "Q8_0": 1.0,
            "F16": 2.0,
            "F32": 4.0,
        }

        if self.n_gpu_layers == 0:
            return 0.0  # CPU only

        # Model weights
        multiplier = QUANT_MULTIPLIERS.get(quantization, 0.50)  # Default to Q4_K_M
        model_size_gb = model_size_b * multiplier

        # Context buffer (KV cache)
        # Formula: ctx_size * layers * hidden_dim * 2 (K+V) * 2 bytes (FP16)
        # Simplified: ~2 bytes per token for 8B models
        context_size_gb = (self.ctx_size * 2) / (1024**3)

        # GPU kernel overhead
        overhead_gb = 0.5

        total_vram = model_size_gb + context_size_gb + overhead_gb

        return round(total_vram, 2)

"""Tests for the model selection service.

Tests registry-based model selection, tier filtering, availability checking,
and round-robin load balancing functionality.
"""

import pytest
from unittest.mock import MagicMock

from app.services.model_selector import ModelSelector
from app.models.discovered_model import (
    ModelRegistry,
    ModelTier,
    DiscoveredModel,
)
from app.core.exceptions import NoModelsAvailableError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_server_manager():
    """Create a mock LlamaServerManager."""
    manager = MagicMock()
    manager.is_server_running = MagicMock(return_value=True)
    return manager


@pytest.fixture
def sample_models():
    """Create sample discovered models for testing."""
    from app.models.discovered_model import QuantizationLevel

    return [
        DiscoveredModel(
            model_id="fast_model_1",
            filename="fast1.gguf",
            file_path="/models/fast1.gguf",
            family="llama",
            size_params=2.0,
            quantization=QuantizationLevel.Q4_K_M,
            assigned_tier=ModelTier.FAST,
            enabled=True,
        ),
        DiscoveredModel(
            model_id="fast_model_2",
            filename="fast2.gguf",
            file_path="/models/fast2.gguf",
            family="llama",
            size_params=3.0,
            quantization=QuantizationLevel.Q4_K_M,
            assigned_tier=ModelTier.FAST,
            enabled=True,
        ),
        DiscoveredModel(
            model_id="balanced_model_1",
            filename="balanced1.gguf",
            file_path="/models/balanced1.gguf",
            family="qwen",
            size_params=8.0,
            quantization=QuantizationLevel.Q5_K_M,
            assigned_tier=ModelTier.BALANCED,
            enabled=True,
        ),
        DiscoveredModel(
            model_id="powerful_model_1",
            filename="powerful1.gguf",
            file_path="/models/powerful1.gguf",
            family="deepseek",
            size_params=20.0,
            quantization=QuantizationLevel.Q6_K,
            assigned_tier=ModelTier.POWERFUL,
            enabled=True,
        ),
        DiscoveredModel(
            model_id="disabled_model",
            filename="disabled.gguf",
            file_path="/models/disabled.gguf",
            family="llama",
            size_params=2.0,
            quantization=QuantizationLevel.Q4_0,
            assigned_tier=ModelTier.FAST,
            enabled=False,
        ),
    ]


@pytest.fixture
def model_registry(sample_models):
    """Create a model registry with sample models."""
    from datetime import datetime

    registry = ModelRegistry(
        scan_path="/models",
        last_scan=datetime.utcnow().isoformat(),
    )
    for model in sample_models:
        registry.add_model(model)
    return registry


@pytest.fixture
def model_selector(model_registry, mock_server_manager):
    """Create a model selector with sample data."""
    return ModelSelector(registry=model_registry, server_manager=mock_server_manager)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for ModelSelector initialization."""

    def test_creates_with_registry_and_manager(
        self, model_registry, mock_server_manager
    ):
        """Selector should be created with registry and server manager."""
        selector = ModelSelector(
            registry=model_registry, server_manager=mock_server_manager
        )

        assert selector.registry is model_registry
        assert selector.server_manager is mock_server_manager

    def test_request_counts_initialized_empty(
        self, model_registry, mock_server_manager
    ):
        """Request counts should be initialized as empty."""
        selector = ModelSelector(
            registry=model_registry, server_manager=mock_server_manager
        )

        # Should be a defaultdict that returns 0 for new keys
        assert selector._request_counts["nonexistent"] == 0


# ============================================================================
# Availability Check Tests
# ============================================================================


class TestIsModelAvailable:
    """Tests for is_model_available method."""

    def test_available_when_enabled_and_running(
        self, model_selector, sample_models, mock_server_manager
    ):
        """Model should be available when enabled and server running."""
        model = sample_models[0]  # fast_model_1, enabled
        mock_server_manager.is_server_running.return_value = True

        assert model_selector.is_model_available(model) is True

    def test_unavailable_when_disabled(
        self, model_selector, sample_models, mock_server_manager
    ):
        """Model should be unavailable when disabled."""
        disabled_model = sample_models[4]  # disabled_model
        mock_server_manager.is_server_running.return_value = True

        assert model_selector.is_model_available(disabled_model) is False

    def test_unavailable_when_server_not_running(
        self, model_selector, sample_models, mock_server_manager
    ):
        """Model should be unavailable when server not running."""
        model = sample_models[0]  # fast_model_1, enabled
        mock_server_manager.is_server_running.return_value = False

        assert model_selector.is_model_available(model) is False

    def test_server_running_check_uses_model_id(
        self, model_selector, sample_models, mock_server_manager
    ):
        """is_model_available should pass model_id to server_manager."""
        model = sample_models[0]  # fast_model_1

        model_selector.is_model_available(model)

        mock_server_manager.is_server_running.assert_called_with("fast_model_1")


# ============================================================================
# Model Selection Tests
# ============================================================================


class TestSelectModel:
    """Tests for select_model method."""

    @pytest.mark.asyncio
    async def test_selects_model_from_requested_tier(self, model_selector):
        """Should select a model from the requested tier."""
        model = await model_selector.select_model("fast")

        assert model.get_effective_tier() == ModelTier.FAST
        assert model.model_id in ["fast_model_1", "fast_model_2"]

    @pytest.mark.asyncio
    async def test_selects_only_available_models(
        self, model_selector, mock_server_manager
    ):
        """Should only select from available models."""

        # Make fast_model_1 unavailable
        def is_running(model_id):
            return model_id != "fast_model_1"

        mock_server_manager.is_server_running = MagicMock(side_effect=is_running)

        model = await model_selector.select_model("fast")

        assert model.model_id == "fast_model_2"

    @pytest.mark.asyncio
    async def test_raises_for_invalid_tier(self, model_selector):
        """Should raise NoModelsAvailableError for invalid tier."""
        with pytest.raises(NoModelsAvailableError) as exc_info:
            await model_selector.select_model("invalid_tier")

        assert "invalid_tier" in str(exc_info.value.details)
        assert "valid_tiers" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_raises_when_no_models_available(
        self, model_selector, mock_server_manager
    ):
        """Should raise NoModelsAvailableError when no models available."""
        mock_server_manager.is_server_running.return_value = False

        with pytest.raises(NoModelsAvailableError) as exc_info:
            await model_selector.select_model("fast")

        # tier is stored in details
        assert "fast" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_tier_has_no_models(self, mock_server_manager):
        """Should raise NoModelsAvailableError for empty tier."""
        from datetime import datetime

        empty_registry = ModelRegistry(
            scan_path="/models",
            last_scan=datetime.utcnow().isoformat(),
        )
        selector = ModelSelector(
            registry=empty_registry, server_manager=mock_server_manager
        )

        with pytest.raises(NoModelsAvailableError):
            await selector.select_model("fast")

    @pytest.mark.asyncio
    async def test_increments_request_count(self, model_selector):
        """Should increment request count for selected model."""
        model = await model_selector.select_model("balanced")

        assert model_selector._request_counts[model.model_id] == 1

        # Select again
        await model_selector.select_model("balanced")

        assert model_selector._request_counts[model.model_id] == 2


# ============================================================================
# Round-Robin Load Balancing Tests
# ============================================================================


class TestRoundRobinLoadBalancing:
    """Tests for round-robin load balancing across models."""

    @pytest.mark.asyncio
    async def test_distributes_across_multiple_models(self, model_selector):
        """Should distribute requests across all available models in tier."""
        # Select from fast tier multiple times
        selected_models = []
        for _ in range(4):
            model = await model_selector.select_model("fast")
            selected_models.append(model.model_id)

        # Both fast models should be selected
        assert "fast_model_1" in selected_models
        assert "fast_model_2" in selected_models

        # Distribution should be even
        assert selected_models.count("fast_model_1") == 2
        assert selected_models.count("fast_model_2") == 2

    @pytest.mark.asyncio
    async def test_selects_least_used_model(self, model_selector):
        """Should select model with lowest request count."""
        # Pre-set request counts
        model_selector._request_counts["fast_model_1"] = 10
        model_selector._request_counts["fast_model_2"] = 5

        model = await model_selector.select_model("fast")

        # Should select the less-used model
        assert model.model_id == "fast_model_2"

    @pytest.mark.asyncio
    async def test_single_model_always_selected(
        self, model_registry, mock_server_manager
    ):
        """Single available model should always be selected."""
        from datetime import datetime
        from app.models.discovered_model import QuantizationLevel

        # Create registry with only one model in tier
        registry = ModelRegistry(
            scan_path="/models",
            last_scan=datetime.utcnow().isoformat(),
        )
        registry.add_model(
            DiscoveredModel(
                model_id="only_model",
                filename="only.gguf",
                file_path="/models/only.gguf",
                family="llama",
                size_params=8.0,
                quantization=QuantizationLevel.Q5_K_M,
                assigned_tier=ModelTier.BALANCED,
                enabled=True,
            )
        )

        selector = ModelSelector(registry=registry, server_manager=mock_server_manager)

        # Select multiple times
        for _ in range(5):
            model = await selector.select_model("balanced")
            assert model.model_id == "only_model"


# ============================================================================
# Get Available Models Tests
# ============================================================================


class TestGetAvailableModels:
    """Tests for get_available_models method."""

    def test_returns_only_available_models(self, model_selector, mock_server_manager):
        """Should return only models that are enabled and running."""
        # All enabled models have servers running by default
        available = model_selector.get_available_models()

        # Should exclude disabled model
        model_ids = [m.model_id for m in available]
        assert "disabled_model" not in model_ids
        assert len(available) == 4  # All enabled models

    def test_returns_empty_when_none_available(
        self, model_selector, mock_server_manager
    ):
        """Should return empty list when no models available."""
        mock_server_manager.is_server_running.return_value = False

        available = model_selector.get_available_models()

        assert available == []


# ============================================================================
# Get Available Count Tests
# ============================================================================


class TestGetAvailableCount:
    """Tests for get_available_count method."""

    def test_count_all_available(self, model_selector):
        """Should count all available models when no tier specified."""
        count = model_selector.get_available_count()

        assert count == 4  # All enabled models

    def test_count_by_tier(self, model_selector):
        """Should count available models in specific tier."""
        fast_count = model_selector.get_available_count("fast")
        balanced_count = model_selector.get_available_count("balanced")
        powerful_count = model_selector.get_available_count("powerful")

        assert fast_count == 2
        assert balanced_count == 1
        assert powerful_count == 1

    def test_count_invalid_tier(self, model_selector):
        """Should return 0 for invalid tier."""
        count = model_selector.get_available_count("invalid")

        assert count == 0

    def test_count_excludes_unavailable(self, model_selector, mock_server_manager):
        """Should exclude unavailable models from count."""

        # Make half the fast models unavailable
        def is_running(model_id):
            return model_id != "fast_model_1"

        mock_server_manager.is_server_running = MagicMock(side_effect=is_running)

        count = model_selector.get_available_count("fast")

        assert count == 1


# ============================================================================
# Tier Conversion Tests
# ============================================================================


class TestTierConversion:
    """Tests for tier string to enum conversion."""

    @pytest.mark.asyncio
    async def test_accepts_lowercase_tiers(self, model_selector):
        """Should accept lowercase tier strings."""
        model = await model_selector.select_model("fast")
        assert model.get_effective_tier() == ModelTier.FAST

        model = await model_selector.select_model("balanced")
        assert model.get_effective_tier() == ModelTier.BALANCED

        model = await model_selector.select_model("powerful")
        assert model.get_effective_tier() == ModelTier.POWERFUL


# ============================================================================
# Error Details Tests
# ============================================================================


class TestErrorDetails:
    """Tests for error details in exceptions."""

    @pytest.mark.asyncio
    async def test_error_includes_available_tiers(
        self, model_selector, mock_server_manager
    ):
        """NoModelsAvailableError should include which tiers have models."""

        # Make only fast tier unavailable
        def is_running(model_id):
            return "fast" not in model_id

        mock_server_manager.is_server_running = MagicMock(side_effect=is_running)

        with pytest.raises(NoModelsAvailableError) as exc_info:
            await model_selector.select_model("fast")

        # Error should list tiers that DO have available models
        assert "available_tiers" in exc_info.value.details
        available_tiers = exc_info.value.details["available_tiers"]
        assert "balanced" in available_tiers
        assert "powerful" in available_tiers

    @pytest.mark.asyncio
    async def test_error_includes_model_counts(
        self, model_selector, mock_server_manager
    ):
        """NoModelsAvailableError should include model counts."""
        mock_server_manager.is_server_running.return_value = False

        with pytest.raises(NoModelsAvailableError) as exc_info:
            await model_selector.select_model("fast")

        assert "tier_total_models" in exc_info.value.details
        assert "tier_enabled_models" in exc_info.value.details


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for model selection workflow."""

    @pytest.mark.asyncio
    async def test_complete_selection_workflow(
        self, model_registry, mock_server_manager
    ):
        """Test complete workflow of selecting models across tiers."""
        selector = ModelSelector(
            registry=model_registry, server_manager=mock_server_manager
        )

        # Select from each tier
        fast = await selector.select_model("fast")
        balanced = await selector.select_model("balanced")
        powerful = await selector.select_model("powerful")

        assert fast.get_effective_tier() == ModelTier.FAST
        assert balanced.get_effective_tier() == ModelTier.BALANCED
        assert powerful.get_effective_tier() == ModelTier.POWERFUL

        # Verify request counts
        assert selector._request_counts[fast.model_id] == 1
        assert selector._request_counts[balanced.model_id] == 1
        assert selector._request_counts[powerful.model_id] == 1

    @pytest.mark.asyncio
    async def test_handles_dynamic_availability_changes(
        self, model_selector, mock_server_manager
    ):
        """Selector should handle models becoming unavailable."""
        # Initially all available
        model1 = await model_selector.select_model("fast")
        assert model1.model_id in ["fast_model_1", "fast_model_2"]

        # Make fast_model_1 unavailable
        def is_running(model_id):
            return model_id != "fast_model_1"

        mock_server_manager.is_server_running = MagicMock(side_effect=is_running)

        # Next selection should only pick fast_model_2
        for _ in range(3):
            model = await model_selector.select_model("fast")
            assert model.model_id == "fast_model_2"

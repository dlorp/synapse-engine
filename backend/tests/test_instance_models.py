"""Tests for model instance configuration models.

Tests validation logic, methods, and registry behavior for
multi-instance model management.
"""

import pytest
from pydantic import ValidationError

from app.models.instance import (
    CreateInstanceRequest,
    InstanceConfig,
    InstanceListResponse,
    InstanceRegistry,
    InstanceResponse,
    InstanceStatus,
    SystemPromptPreset,
    SystemPromptPresetsResponse,
    UpdateInstanceRequest,
)


class TestInstanceStatus:
    """Tests for InstanceStatus enum."""

    def test_all_statuses_exist(self):
        """Test all expected statuses are defined."""
        assert InstanceStatus.STOPPED.value == "stopped"
        assert InstanceStatus.STARTING.value == "starting"
        assert InstanceStatus.ACTIVE.value == "active"
        assert InstanceStatus.STOPPING.value == "stopping"
        assert InstanceStatus.ERROR.value == "error"

    def test_status_count(self):
        """Test expected number of statuses."""
        assert len(InstanceStatus) == 5


class TestInstanceConfig:
    """Tests for InstanceConfig model."""

    def test_minimal_valid_config(self):
        """Test creating config with required fields only."""
        config = InstanceConfig(
            instance_id="test_model:01",
            model_id="test_model",
            instance_number=1,
            display_name="Test Instance",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert config.instance_id == "test_model:01"
        assert config.status == InstanceStatus.STOPPED
        assert config.system_prompt is None
        assert config.web_search_enabled is False

    def test_full_config(self):
        """Test creating config with all fields."""
        config = InstanceConfig(
            instance_id="model:05",
            model_id="model",
            instance_number=5,
            display_name="Full Config",
            system_prompt="You are a helpful assistant.",
            web_search_enabled=True,
            port=8105,
            status=InstanceStatus.ACTIVE,
            created_at="2025-01-30T10:00:00Z",
            updated_at="2025-01-30T11:00:00Z",
        )
        assert config.web_search_enabled is True
        assert config.system_prompt == "You are a helpful assistant."
        assert config.status == InstanceStatus.ACTIVE

    def test_invalid_instance_id_format(self):
        """Test that invalid instance_id format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InstanceConfig(
                instance_id="invalid_format",  # Missing :NN
                model_id="test",
                instance_number=1,
                display_name="Test",
                port=8100,
                created_at="2025-01-30T10:00:00Z",
            )
        assert "Instance ID must be in format" in str(exc_info.value)

    def test_instance_id_must_have_two_digits(self):
        """Test instance_id requires two digit suffix."""
        with pytest.raises(ValidationError):
            InstanceConfig(
                instance_id="model:1",  # Only one digit
                model_id="model",
                instance_number=1,
                display_name="Test",
                port=8100,
                created_at="2025-01-30T10:00:00Z",
            )

    def test_instance_number_range(self):
        """Test instance number must be 1-99."""
        with pytest.raises(ValidationError):
            InstanceConfig(
                instance_id="model:00",
                model_id="model",
                instance_number=0,  # Below minimum
                display_name="Test",
                port=8100,
                created_at="2025-01-30T10:00:00Z",
            )
        with pytest.raises(ValidationError):
            InstanceConfig(
                instance_id="model:100",
                model_id="model",
                instance_number=100,  # Above maximum
                display_name="Test",
                port=8100,
                created_at="2025-01-30T10:00:00Z",
            )

    def test_display_name_empty_rejected(self):
        """Test empty display name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InstanceConfig(
                instance_id="model:01",
                model_id="model",
                instance_number=1,
                display_name="   ",  # Whitespace only
                port=8100,
                created_at="2025-01-30T10:00:00Z",
            )
        assert "Display name cannot be empty" in str(exc_info.value)

    def test_display_name_html_stripped(self):
        """Test HTML tags are removed from display name."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="<script>alert('xss')</script>Safe Name",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert "<script>" not in config.display_name
        assert "Safe Name" in config.display_name

    def test_system_prompt_null_bytes_removed(self):
        """Test null bytes are removed from system prompt."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            system_prompt="Hello\x00World",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert "\x00" not in config.system_prompt
        assert config.system_prompt == "HelloWorld"

    def test_system_prompt_control_chars_removed(self):
        """Test control characters are removed from system prompt."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            system_prompt="Hello\x07World",  # Bell character
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert "\x07" not in config.system_prompt

    def test_system_prompt_newlines_preserved(self):
        """Test newlines and tabs are preserved in system prompt."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            system_prompt="Line1\nLine2\tTabbed",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert "\n" in config.system_prompt
        assert "\t" in config.system_prompt

    def test_system_prompt_whitespace_only_becomes_none(self):
        """Test whitespace-only system prompt becomes None."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            system_prompt="   \n\t  ",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        assert config.system_prompt is None

    def test_port_validation(self):
        """Test port range validation."""
        with pytest.raises(ValidationError):
            InstanceConfig(
                instance_id="model:01",
                model_id="model",
                instance_number=1,
                display_name="Test",
                port=80,  # Below 1024
                created_at="2025-01-30T10:00:00Z",
            )
        with pytest.raises(ValidationError):
            InstanceConfig(
                instance_id="model:01",
                model_id="model",
                instance_number=1,
                display_name="Test",
                port=70000,  # Above 65535
                created_at="2025-01-30T10:00:00Z",
            )

    def test_get_full_name(self):
        """Test get_full_name method."""
        config = InstanceConfig(
            instance_id="mymodel:03",
            model_id="mymodel",
            instance_number=3,
            display_name="My Custom Instance",
            port=8103,
            created_at="2025-01-30T10:00:00Z",
        )
        assert config.get_full_name() == "My Custom Instance [mymodel:03]"

    def test_serialization_aliases(self):
        """Test JSON serialization uses camelCase aliases."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            web_search_enabled=True,
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        data = config.model_dump(by_alias=True)
        assert "instanceId" in data
        assert "modelId" in data
        assert "instanceNumber" in data
        assert "displayName" in data
        assert "webSearchEnabled" in data
        assert "createdAt" in data


class TestInstanceRegistry:
    """Tests for InstanceRegistry model."""

    def test_empty_registry(self):
        """Test creating empty registry."""
        registry = InstanceRegistry()
        assert len(registry.instances) == 0
        assert registry.port_range == (8100, 8199)

    def test_add_instance(self):
        """Test adding instance to registry."""
        registry = InstanceRegistry()
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config)
        assert "model:01" in registry.instances
        assert registry.instances["model:01"].display_name == "Test"

    def test_remove_instance(self):
        """Test removing instance from registry."""
        registry = InstanceRegistry()
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config)
        result = registry.remove_instance("model:01")
        assert result is True
        assert "model:01" not in registry.instances

    def test_remove_nonexistent_instance(self):
        """Test removing instance that doesn't exist."""
        registry = InstanceRegistry()
        result = registry.remove_instance("nonexistent:01")
        assert result is False

    def test_get_instances_for_model(self):
        """Test getting all instances for a specific model."""
        registry = InstanceRegistry()
        config1 = InstanceConfig(
            instance_id="model_a:01",
            model_id="model_a",
            instance_number=1,
            display_name="A1",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        config2 = InstanceConfig(
            instance_id="model_a:02",
            model_id="model_a",
            instance_number=2,
            display_name="A2",
            port=8101,
            created_at="2025-01-30T10:00:00Z",
        )
        config3 = InstanceConfig(
            instance_id="model_b:01",
            model_id="model_b",
            instance_number=1,
            display_name="B1",
            port=8102,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config1)
        registry.add_instance(config2)
        registry.add_instance(config3)

        model_a_instances = registry.get_instances_for_model("model_a")
        assert len(model_a_instances) == 2
        assert all(inst.model_id == "model_a" for inst in model_a_instances)

    def test_get_next_instance_number_empty(self):
        """Test getting next instance number for model with no instances."""
        registry = InstanceRegistry()
        assert registry.get_next_instance_number("new_model") == 1

    def test_get_next_instance_number_existing(self):
        """Test getting next instance number with existing instances."""
        registry = InstanceRegistry()
        config = InstanceConfig(
            instance_id="model:03",
            model_id="model",
            instance_number=3,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config)
        assert registry.get_next_instance_number("model") == 4

    def test_get_next_instance_number_capped_at_99(self):
        """Test instance number doesn't exceed 99."""
        registry = InstanceRegistry()
        config = InstanceConfig(
            instance_id="model:99",
            model_id="model",
            instance_number=99,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config)
        assert registry.get_next_instance_number("model") == 99

    def test_get_available_port_empty(self):
        """Test getting available port with no instances."""
        registry = InstanceRegistry()
        assert registry.get_available_port() == 8100

    def test_get_available_port_with_instances(self):
        """Test getting available port skips used ports."""
        registry = InstanceRegistry()
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(config)
        assert registry.get_available_port() == 8101

    def test_get_available_port_all_used(self):
        """Test returns None when all ports in range are used."""
        registry = InstanceRegistry(port_range=(8100, 8101))
        for i, port in enumerate([8100, 8101]):
            config = InstanceConfig(
                instance_id=f"model:{i + 1:02d}",
                model_id="model",
                instance_number=i + 1,
                display_name=f"Test {i}",
                port=port,
                created_at="2025-01-30T10:00:00Z",
            )
            registry.add_instance(config)
        assert registry.get_available_port() is None

    def test_get_active_instances(self):
        """Test getting only active instances."""
        registry = InstanceRegistry()
        active = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Active",
            port=8100,
            status=InstanceStatus.ACTIVE,
            created_at="2025-01-30T10:00:00Z",
        )
        stopped = InstanceConfig(
            instance_id="model:02",
            model_id="model",
            instance_number=2,
            display_name="Stopped",
            port=8101,
            status=InstanceStatus.STOPPED,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(active)
        registry.add_instance(stopped)

        active_list = registry.get_active_instances()
        assert len(active_list) == 1
        assert active_list[0].instance_id == "model:01"

    def test_get_instances_by_status(self):
        """Test filtering instances by status."""
        registry = InstanceRegistry()
        starting = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Starting",
            port=8100,
            status=InstanceStatus.STARTING,
            created_at="2025-01-30T10:00:00Z",
        )
        registry.add_instance(starting)

        result = registry.get_instances_by_status(InstanceStatus.STARTING)
        assert len(result) == 1
        assert result[0].status == InstanceStatus.STARTING


class TestCreateInstanceRequest:
    """Tests for CreateInstanceRequest model."""

    def test_minimal_request(self):
        """Test creating request with required fields."""
        req = CreateInstanceRequest(
            model_id="my_model",
            display_name="My Instance",
        )
        assert req.model_id == "my_model"
        assert req.system_prompt is None
        assert req.web_search_enabled is False

    def test_full_request(self):
        """Test creating request with all fields."""
        req = CreateInstanceRequest(
            model_id="my_model",
            display_name="Full Instance",
            system_prompt="Be helpful",
            web_search_enabled=True,
        )
        assert req.system_prompt == "Be helpful"
        assert req.web_search_enabled is True


class TestUpdateInstanceRequest:
    """Tests for UpdateInstanceRequest model."""

    def test_empty_update(self):
        """Test update with no fields (all optional)."""
        req = UpdateInstanceRequest()
        assert req.display_name is None
        assert req.system_prompt is None
        assert req.web_search_enabled is None

    def test_partial_update(self):
        """Test partial field update."""
        req = UpdateInstanceRequest(display_name="New Name")
        assert req.display_name == "New Name"
        assert req.system_prompt is None


class TestInstanceResponse:
    """Tests for InstanceResponse model."""

    def test_response_creation(self):
        """Test creating instance response."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        resp = InstanceResponse(
            instance=config,
            model_display_name="Base Model Name",
            model_tier="powerful",
        )
        assert resp.model_display_name == "Base Model Name"
        assert resp.model_tier == "powerful"


class TestInstanceListResponse:
    """Tests for InstanceListResponse model."""

    def test_list_response(self):
        """Test creating list response."""
        config = InstanceConfig(
            instance_id="model:01",
            model_id="model",
            instance_number=1,
            display_name="Test",
            port=8100,
            created_at="2025-01-30T10:00:00Z",
        )
        resp = InstanceListResponse(
            instances=[config],
            total=1,
            by_model={"model": 1},
        )
        assert resp.total == 1
        assert resp.by_model["model"] == 1


class TestSystemPromptPreset:
    """Tests for SystemPromptPreset model."""

    def test_preset_creation(self):
        """Test creating system prompt preset."""
        preset = SystemPromptPreset(
            id="coding",
            name="Coding Assistant",
            prompt="You are an expert programmer.",
            description="For code-related questions",
            category="development",
        )
        assert preset.id == "coding"
        assert preset.category == "development"

    def test_preset_default_category(self):
        """Test default category is 'general'."""
        preset = SystemPromptPreset(
            id="test",
            name="Test",
            prompt="Test prompt",
            description="Test description",
        )
        assert preset.category == "general"


class TestSystemPromptPresetsResponse:
    """Tests for SystemPromptPresetsResponse model."""

    def test_presets_response(self):
        """Test creating presets list response."""
        preset = SystemPromptPreset(
            id="test",
            name="Test",
            prompt="Prompt",
            description="Desc",
        )
        resp = SystemPromptPresetsResponse(presets=[preset])
        assert len(resp.presets) == 1

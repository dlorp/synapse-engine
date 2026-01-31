"""Test suite for Code Chat API router endpoints.

Tests for the FastAPI router that exposes Code Chat functionality
via REST API and SSE streaming.

Phase: Code Chat Implementation (Session 5)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.code_chat import (
    CodeChatRequest,
    WorkspaceListResponse,
    WorkspaceValidation,
    DirectoryInfo,
    PRESETS,
)


# =============================================================================
# Model Tests (these run without server)
# =============================================================================

class TestCodeChatRequestModel:
    """Tests for CodeChatRequest validation."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = CodeChatRequest(
            query="Read the main.py file",
            workspace_path="/workspace/project"
        )
        assert request.query == "Read the main.py file"
        assert request.workspace_path == "/workspace/project"

    def test_request_defaults(self):
        """Test default values are applied."""
        request = CodeChatRequest(
            query="test",
            workspace_path="/workspace"
        )
        assert request.use_cgrag is True
        assert request.use_web_search is True
        assert request.max_iterations == 15
        assert request.preset == "balanced"

    def test_request_with_all_options(self):
        """Test request with all options specified."""
        request = CodeChatRequest(
            query="analyze code",
            workspace_path="/workspace",
            session_id="session-123",
            context_name="my_context",
            use_cgrag=False,
            use_web_search=False,
            max_iterations=10,
            preset="quality"
        )
        assert request.session_id == "session-123"
        assert request.context_name == "my_context"
        assert request.use_cgrag is False
        assert request.max_iterations == 10

    def test_request_validation_max_iterations(self):
        """Test max_iterations validation bounds."""
        # Valid within bounds
        request = CodeChatRequest(
            query="test",
            workspace_path="/workspace",
            max_iterations=1
        )
        assert request.max_iterations == 1

        request = CodeChatRequest(
            query="test",
            workspace_path="/workspace",
            max_iterations=50
        )
        assert request.max_iterations == 50


class TestWorkspaceModels:
    """Tests for workspace-related models."""

    def test_directory_info(self):
        """Test DirectoryInfo model."""
        dir_info = DirectoryInfo(
            name="my-project",
            path="/home/user/my-project",
            is_directory=True,
            is_git_repo=True,
            project_type="python"
        )
        assert dir_info.name == "my-project"
        assert dir_info.is_git_repo is True
        assert dir_info.project_type == "python"

    def test_workspace_list_response(self):
        """Test WorkspaceListResponse model."""
        response = WorkspaceListResponse(
            current_path="/home/user",
            directories=[
                DirectoryInfo(name="project", path="/home/user/project")
            ],
            parent_path="/home",
            is_git_repo=False,
            project_type=None
        )
        assert response.current_path == "/home/user"
        assert len(response.directories) == 1
        assert response.parent_path == "/home"

    def test_workspace_validation_valid(self):
        """Test valid WorkspaceValidation."""
        validation = WorkspaceValidation(
            valid=True,
            is_git_repo=True,
            file_count=150,
            has_cgrag_index=True
        )
        assert validation.valid is True
        assert validation.error is None

    def test_workspace_validation_invalid(self):
        """Test invalid WorkspaceValidation."""
        validation = WorkspaceValidation(
            valid=False,
            error="Path does not exist"
        )
        assert validation.valid is False
        assert validation.error is not None


class TestPresetModels:
    """Tests for preset models."""

    def test_builtin_presets_exist(self):
        """Test that built-in presets are defined."""
        assert "speed" in PRESETS
        assert "balanced" in PRESETS
        assert "quality" in PRESETS
        assert "coding" in PRESETS
        assert "research" in PRESETS

    def test_preset_structure(self):
        """Test preset has required fields."""
        preset = PRESETS["balanced"]
        assert preset.name == "balanced"
        assert preset.description is not None
        assert preset.planning_tier in ["fast", "balanced", "powerful"]
        assert isinstance(preset.tool_configs, dict)

    def test_preset_tool_configs(self):
        """Test preset tool configurations."""
        preset = PRESETS["quality"]
        assert preset.planning_tier == "powerful"
        # Check that some tools are configured
        assert len(preset.tool_configs) > 0


# =============================================================================
# Router Integration Tests (require server mock)
# =============================================================================

class TestWorkspacesEndpoint:
    """Tests for /api/code-chat/workspaces endpoint."""

    @pytest.fixture
    def mock_services(self):
        """Mock workspace services."""
        with patch('app.routers.code_chat.validate_path') as mock_validate, \
             patch('app.routers.code_chat.list_directories') as mock_list, \
             patch('app.routers.code_chat.get_parent_path') as mock_parent, \
             patch('app.routers.code_chat.check_git_repo') as mock_git, \
             patch('app.routers.code_chat.detect_project_type') as mock_type:

            mock_validate.return_value = (True, None)
            mock_list.return_value = [
                DirectoryInfo(name="project", path="/workspace/project")
            ]
            mock_parent.return_value = "/"
            mock_git.return_value = False
            mock_type.return_value = None

            yield {
                'validate_path': mock_validate,
                'list_directories': mock_list,
                'get_parent_path': mock_parent,
                'check_git_repo': mock_git,
                'detect_project_type': mock_type
            }

    @pytest.mark.asyncio
    async def test_list_workspaces_calls_services(self, mock_services):
        """Test that list_workspaces calls required services."""
        from app.routers.code_chat import list_workspaces

        result = await list_workspaces(path="/workspace")

        mock_services['validate_path'].assert_called_once_with("/workspace")
        mock_services['list_directories'].assert_called_once()


class TestContextsEndpoint:
    """Tests for /api/code-chat/contexts endpoint."""

    @pytest.fixture
    def mock_context_services(self):
        """Mock context services."""
        with patch('app.routers.code_chat.list_cgrag_indexes') as mock_list:
            mock_list.return_value = []
            yield {'list_cgrag_indexes': mock_list}

    @pytest.mark.asyncio
    async def test_list_contexts_empty(self, mock_context_services):
        """Test listing contexts when none exist."""
        from app.routers.code_chat import list_contexts

        result = await list_contexts()

        assert result == []
        mock_context_services['list_cgrag_indexes'].assert_called_once()


class TestPresetsEndpoint:
    """Tests for /api/code-chat/presets endpoint."""

    @pytest.mark.asyncio
    async def test_get_presets_returns_all(self):
        """Test that get_presets returns all presets."""
        from app.routers.code_chat import get_presets

        result = await get_presets()

        assert len(result) == len(PRESETS)
        preset_names = [p.name for p in result]
        assert "balanced" in preset_names
        assert "quality" in preset_names

    @pytest.mark.asyncio
    async def test_get_preset_by_name(self):
        """Test getting a specific preset."""
        from app.routers.code_chat import get_preset

        result = await get_preset("balanced")

        assert result.name == "balanced"

    @pytest.mark.asyncio
    async def test_get_preset_not_found(self):
        """Test getting non-existent preset raises 404."""
        from fastapi import HTTPException
        from app.routers.code_chat import get_preset

        with pytest.raises(HTTPException) as exc_info:
            await get_preset("nonexistent")

        assert exc_info.value.status_code == 404


# =============================================================================
# Query Endpoint Tests
# =============================================================================

class TestQueryEndpoint:
    """Tests for /api/code-chat/query endpoint."""

    @pytest.mark.asyncio
    async def test_query_validates_workspace(self):
        """Test that query validates workspace path."""
        from fastapi import HTTPException
        from app.routers.code_chat import query

        # Create mock request
        mock_request = MagicMock()

        with patch('app.routers.code_chat.validate_path') as mock_validate:
            mock_validate.return_value = (False, "Path not allowed")

            request_obj = CodeChatRequest(
                query="test query",
                workspace_path="../../../etc"
            )

            with pytest.raises(HTTPException) as exc_info:
                await query(request_obj, mock_request)

            assert exc_info.value.status_code == 400


# =============================================================================
# Cancel Endpoint Tests
# =============================================================================

class TestCancelEndpoint:
    """Tests for /api/code-chat/cancel endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_session(self):
        """Test cancelling a session."""
        from app.routers.code_chat import cancel_session

        mock_request = MagicMock()
        mock_agent = MagicMock()
        mock_agent.cancel.return_value = True

        with patch('app.routers.code_chat.get_agent', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_agent

            result = await cancel_session("session-123", mock_request)

            assert result["success"] is True
            assert result["session_id"] == "session-123"
            mock_agent.cancel.assert_called_once_with("session-123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

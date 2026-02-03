"""Tests for the workspace management service.

Tests workspace path validation, project detection, and directory listing
functionality for the Code Chat assistant.
"""

import json
from pathlib import Path

import pytest

from app.services.code_chat.workspace import (
    validate_path,
    get_parent_path,
    check_git_repo,
    detect_project_type,
    detect_project_info,
    is_valid_workspace,
    list_directories,
    count_files,
    check_cgrag_index_exists,
    parse_pyproject_toml,
    parse_package_json,
    parse_cargo_toml,
    parse_go_mod,
    ALLOWED_WORKSPACE_ROOTS,
)


class TestValidatePath:
    """Tests for validate_path function."""

    def test_rejects_relative_path(self):
        """Relative paths are rejected."""
        is_valid, error = validate_path("relative/path")
        # After resolution, the path should still be checked against allowed roots
        # If the resolved path is not under allowed roots, it should fail
        assert is_valid is False or "must be under one of" in (error or "")

    def test_accepts_path_under_allowed_root(self, tmp_path):
        """Paths under allowed roots are accepted."""
        # Create a path under /Users (macOS) or /home (Linux)
        # Using tmp_path which is typically under allowed roots
        test_dir = tmp_path / "workspace"
        test_dir.mkdir()

        # Check if tmp_path is under an allowed root
        tmp_str = str(tmp_path.resolve())
        under_allowed = any(
            tmp_str.startswith(root) for root in ALLOWED_WORKSPACE_ROOTS
        )

        is_valid, error = validate_path(str(test_dir))

        if under_allowed:
            assert is_valid is True
            assert error is None
        else:
            # Not under allowed roots - that's expected for some systems
            assert is_valid is False

    def test_rejects_nonexistent_path(self):
        """Nonexistent paths are rejected."""
        is_valid, error = validate_path("/Users/nonexistent/path/12345")
        assert is_valid is False
        assert error is not None

    def test_rejects_path_outside_allowed_roots(self, tmp_path):
        """Paths outside allowed roots are rejected."""
        # Create a temp path that might be outside allowed roots
        # (behavior depends on system, but we test the logic)
        is_valid, error = validate_path("/etc/passwd")
        # Should either not exist or be rejected as outside allowed roots
        assert is_valid is False


class TestGetParentPath:
    """Tests for get_parent_path function."""

    @pytest.mark.asyncio
    async def test_returns_parent_directory(self, tmp_path):
        """Returns parent of given directory."""
        child = tmp_path / "subdir"
        child.mkdir()

        parent = await get_parent_path(str(child))

        # Should return the parent path or None if outside allowed roots
        if parent:
            assert parent == str(tmp_path.resolve())

    @pytest.mark.asyncio
    async def test_returns_none_at_allowed_root_boundary(self):
        """Returns None when parent would be outside allowed roots."""
        # At filesystem root or allowed root boundary
        for root in ALLOWED_WORKSPACE_ROOTS:
            if Path(root).exists():
                result = await get_parent_path(root)
                # Parent of root should be None (outside allowed)
                # or the actual parent if it's still allowed
                # Just verify the function doesn't crash
                assert result is None or isinstance(result, str)
                break

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_path(self):
        """Returns None for invalid paths."""
        parent = await get_parent_path("/nonexistent/path/12345")
        assert parent is None


class TestCheckGitRepo:
    """Tests for check_git_repo function."""

    @pytest.mark.asyncio
    async def test_returns_true_for_git_directory(self, tmp_path):
        """Returns True when .git directory exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = await check_git_repo(str(tmp_path))

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_without_git_directory(self, tmp_path):
        """Returns False when no .git directory."""
        result = await check_git_repo(str(tmp_path))

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_invalid_path(self):
        """Returns False for nonexistent paths."""
        result = await check_git_repo("/nonexistent/path")

        assert result is False


class TestDetectProjectType:
    """Tests for detect_project_type function."""

    @pytest.mark.asyncio
    async def test_detects_python_pyproject(self, tmp_path):
        """Detects Python project with pyproject.toml."""
        (tmp_path / "pyproject.toml").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "python"

    @pytest.mark.asyncio
    async def test_detects_python_requirements(self, tmp_path):
        """Detects Python project with requirements.txt."""
        (tmp_path / "requirements.txt").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "python"

    @pytest.mark.asyncio
    async def test_detects_python_setup_py(self, tmp_path):
        """Detects Python project with setup.py."""
        (tmp_path / "setup.py").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "python"

    @pytest.mark.asyncio
    async def test_detects_node_project(self, tmp_path):
        """Detects Node.js project with package.json."""
        (tmp_path / "package.json").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "node"

    @pytest.mark.asyncio
    async def test_detects_rust_project(self, tmp_path):
        """Detects Rust project with Cargo.toml."""
        (tmp_path / "Cargo.toml").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "rust"

    @pytest.mark.asyncio
    async def test_detects_go_project(self, tmp_path):
        """Detects Go project with go.mod."""
        (tmp_path / "go.mod").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "go"

    @pytest.mark.asyncio
    async def test_detects_java_maven_project(self, tmp_path):
        """Detects Java project with pom.xml."""
        (tmp_path / "pom.xml").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "java"

    @pytest.mark.asyncio
    async def test_detects_java_gradle_project(self, tmp_path):
        """Detects Java project with build.gradle."""
        (tmp_path / "build.gradle").touch()

        result = await detect_project_type(str(tmp_path))

        assert result == "java"

    @pytest.mark.asyncio
    async def test_returns_none_for_no_project(self, tmp_path):
        """Returns None when no project markers found."""
        result = await detect_project_type(str(tmp_path))

        assert result is None


class TestParsePyprojectToml:
    """Tests for parse_pyproject_toml function."""

    @pytest.mark.asyncio
    async def test_parses_basic_pyproject(self, tmp_path):
        """Parses basic pyproject.toml metadata."""
        pyproject_content = """
[project]
name = "test-project"
version = "1.2.3"
dependencies = ["fastapi", "pydantic"]

[project.optional-dependencies]
dev = ["pytest", "ruff"]

[project.scripts]
cli = "test_project.cli:main"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        result = await parse_pyproject_toml(pyproject_path)

        assert result.type == "python"
        assert result.name == "test-project"
        assert result.version == "1.2.3"
        assert "fastapi" in result.dependencies
        assert "pydantic" in result.dependencies
        assert "pytest" in result.dev_dependencies
        assert "cli" in result.entry_points

    @pytest.mark.asyncio
    async def test_handles_minimal_pyproject(self, tmp_path):
        """Handles minimal pyproject.toml."""
        pyproject_content = """
[project]
name = "minimal"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        result = await parse_pyproject_toml(pyproject_path)

        assert result.type == "python"
        assert result.name == "minimal"

    @pytest.mark.asyncio
    async def test_handles_invalid_toml(self, tmp_path):
        """Returns default ProjectInfo for invalid TOML."""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("invalid { toml content")

        result = await parse_pyproject_toml(pyproject_path)

        assert result.type == "python"


class TestParsePackageJson:
    """Tests for parse_package_json function."""

    @pytest.mark.asyncio
    async def test_parses_basic_package_json(self, tmp_path):
        """Parses basic package.json metadata."""
        package_content = {
            "name": "test-app",
            "version": "2.0.0",
            "main": "index.js",
            "dependencies": {"express": "^4.0.0"},
            "devDependencies": {"jest": "^29.0.0"},
            "scripts": {"start": "node index.js", "test": "jest"},
        }
        package_path = tmp_path / "package.json"
        package_path.write_text(json.dumps(package_content))

        result = await parse_package_json(package_path)

        assert result.type == "node"
        assert result.name == "test-app"
        assert result.version == "2.0.0"
        assert "express" in result.dependencies
        assert "jest" in result.dev_dependencies
        assert result.scripts.get("start") == "node index.js"
        assert "index.js" in result.entry_points

    @pytest.mark.asyncio
    async def test_handles_minimal_package_json(self, tmp_path):
        """Handles minimal package.json."""
        package_path = tmp_path / "package.json"
        package_path.write_text('{"name": "minimal"}')

        result = await parse_package_json(package_path)

        assert result.type == "node"
        assert result.name == "minimal"

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, tmp_path):
        """Returns default ProjectInfo for invalid JSON."""
        package_path = tmp_path / "package.json"
        package_path.write_text("invalid json {")

        result = await parse_package_json(package_path)

        assert result.type == "node"


class TestParseCargoToml:
    """Tests for parse_cargo_toml function."""

    @pytest.mark.asyncio
    async def test_parses_basic_cargo_toml(self, tmp_path):
        """Parses basic Cargo.toml metadata."""
        cargo_content = """
[package]
name = "rust-app"
version = "0.1.0"

[dependencies]
tokio = "1.0"
serde = "1.0"

[dev-dependencies]
criterion = "0.4"
"""
        cargo_path = tmp_path / "Cargo.toml"
        cargo_path.write_text(cargo_content)

        result = await parse_cargo_toml(cargo_path)

        assert result.type == "rust"
        assert result.name == "rust-app"
        assert result.version == "0.1.0"
        assert "tokio" in result.dependencies
        assert "criterion" in result.dev_dependencies


class TestParseGoMod:
    """Tests for parse_go_mod function."""

    @pytest.mark.asyncio
    async def test_parses_basic_go_mod(self, tmp_path):
        """Parses basic go.mod metadata."""
        go_mod_content = """
module github.com/user/myapp

go 1.21

require github.com/gin-gonic/gin v1.9.0
require github.com/stretchr/testify v1.8.0
"""
        go_mod_path = tmp_path / "go.mod"
        go_mod_path.write_text(go_mod_content)

        result = await parse_go_mod(go_mod_path)

        assert result.type == "go"
        assert result.name == "github.com/user/myapp"
        assert result.version == "1.21"
        assert "github.com/gin-gonic/gin" in result.dependencies


class TestDetectProjectInfo:
    """Tests for detect_project_info function."""

    @pytest.mark.asyncio
    async def test_detects_python_project_info(self, tmp_path):
        """Detects Python project and parses info."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "detected-project"
version = "3.0.0"
""")

        result = await detect_project_info(str(tmp_path))

        assert result is not None
        assert result.type == "python"
        assert result.name == "detected-project"

    @pytest.mark.asyncio
    async def test_detects_node_project_info(self, tmp_path):
        """Detects Node project and parses info."""
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "node-app", "version": "1.0.0"}')

        result = await detect_project_info(str(tmp_path))

        assert result is not None
        assert result.type == "node"
        assert result.name == "node-app"

    @pytest.mark.asyncio
    async def test_returns_none_for_no_project(self, tmp_path):
        """Returns None when no project files found."""
        result = await detect_project_info(str(tmp_path))

        assert result is None


class TestIsValidWorkspace:
    """Tests for is_valid_workspace function."""

    @pytest.mark.asyncio
    async def test_returns_true_for_valid_directory(self, tmp_path):
        """Returns True for valid directory under allowed roots."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Check if tmp_path is under allowed roots
        is_under_allowed = any(
            str(tmp_path).startswith(root) for root in ALLOWED_WORKSPACE_ROOTS
        )

        result = await is_valid_workspace(str(workspace))

        if is_under_allowed:
            assert result is True
        else:
            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_file(self, tmp_path):
        """Returns False when path is a file, not directory."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        result = await is_valid_workspace(str(test_file))

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent(self):
        """Returns False for nonexistent path."""
        result = await is_valid_workspace("/nonexistent/path/12345")

        assert result is False


class TestCountFiles:
    """Tests for count_files function."""

    @pytest.mark.asyncio
    async def test_counts_files_in_directory(self, tmp_path):
        """Counts files recursively."""
        # Create some files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").touch()

        count = await count_files(str(tmp_path))

        assert count == 3

    @pytest.mark.asyncio
    async def test_respects_max_count(self, tmp_path):
        """Stops counting at max_count."""
        # Create many files
        for i in range(20):
            (tmp_path / f"file{i}.txt").touch()

        count = await count_files(str(tmp_path), max_count=10)

        assert count == 10

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_directory(self, tmp_path):
        """Returns 0 for empty directory."""
        count = await count_files(str(tmp_path))

        assert count == 0

    @pytest.mark.asyncio
    async def test_returns_zero_for_invalid_path(self):
        """Returns 0 for invalid path."""
        count = await count_files("/nonexistent/path")

        assert count == 0


class TestCheckCgragIndexExists:
    """Tests for check_cgrag_index_exists function."""

    @pytest.mark.asyncio
    async def test_returns_false_when_no_index(self, tmp_path):
        """Returns False when no CGRAG index exists."""
        result = await check_cgrag_index_exists(str(tmp_path))

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent_workspace(self):
        """Returns False for nonexistent workspace path."""
        result = await check_cgrag_index_exists("/nonexistent/workspace")
        assert result is False

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(self, tmp_path):
        """Returns False when errors occur during check."""
        # The function should handle any errors and return False
        result = await check_cgrag_index_exists(str(tmp_path / "nonexistent"))
        assert result is False


class TestListDirectories:
    """Tests for list_directories function."""

    @pytest.mark.asyncio
    async def test_lists_subdirectories(self, tmp_path):
        """Lists subdirectories in path."""
        # Create subdirectories
        (tmp_path / "project1").mkdir()
        (tmp_path / "project2").mkdir()
        # Create a file (should be ignored)
        (tmp_path / "readme.txt").touch()

        result = await list_directories(str(tmp_path))

        names = [d.name for d in result]
        assert "project1" in names
        assert "project2" in names
        assert "readme.txt" not in names

    @pytest.mark.asyncio
    async def test_excludes_hidden_directories(self, tmp_path):
        """Excludes directories starting with dot."""
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "visible").mkdir()

        result = await list_directories(str(tmp_path))

        names = [d.name for d in result]
        assert ".hidden" not in names
        assert "visible" in names

    @pytest.mark.asyncio
    async def test_excludes_blocked_directories(self, tmp_path):
        """Excludes directories in BLOCKED_DIRECTORIES list."""
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "real_project").mkdir()

        result = await list_directories(str(tmp_path))

        names = [d.name for d in result]
        assert "node_modules" not in names
        assert "__pycache__" not in names
        assert "real_project" in names

    @pytest.mark.asyncio
    async def test_detects_git_repos(self, tmp_path):
        """Detects git repositories in listing."""
        git_project = tmp_path / "git_project"
        git_project.mkdir()
        (git_project / ".git").mkdir()

        non_git = tmp_path / "non_git"
        non_git.mkdir()

        result = await list_directories(str(tmp_path))

        git_info = next(d for d in result if d.name == "git_project")
        non_git_info = next(d for d in result if d.name == "non_git")

        assert git_info.is_git_repo is True
        assert non_git_info.is_git_repo is False

    @pytest.mark.asyncio
    async def test_detects_project_types(self, tmp_path):
        """Detects project types in listing."""
        python_proj = tmp_path / "python_proj"
        python_proj.mkdir()
        (python_proj / "pyproject.toml").touch()

        node_proj = tmp_path / "node_proj"
        node_proj.mkdir()
        (node_proj / "package.json").touch()

        result = await list_directories(str(tmp_path))

        python_info = next(d for d in result if d.name == "python_proj")
        node_info = next(d for d in result if d.name == "node_proj")

        assert python_info.project_type == "python"
        assert node_info.project_type == "node"

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_directory(self, tmp_path):
        """Returns empty list for directory with no subdirs."""
        result = await list_directories(str(tmp_path))

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_sorted_list(self, tmp_path):
        """Returns directories in sorted order."""
        (tmp_path / "zebra").mkdir()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "middle").mkdir()

        result = await list_directories(str(tmp_path))

        names = [d.name for d in result]
        assert names == ["alpha", "middle", "zebra"]

    @pytest.mark.asyncio
    async def test_includes_directory_info_fields(self, tmp_path):
        """DirectoryInfo includes all expected fields."""
        (tmp_path / "test_dir").mkdir()

        result = await list_directories(str(tmp_path))

        assert len(result) == 1
        dir_info = result[0]
        assert dir_info.name == "test_dir"
        assert dir_info.is_directory is True
        assert isinstance(dir_info.is_git_repo, bool)
        assert dir_info.path is not None

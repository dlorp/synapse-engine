"""Workspace management service for Code Chat mode.

This module provides workspace selection, validation, and project detection
functionality for the Code Chat agentic coding assistant.

Implements:
- Directory browsing with git repo detection
- Project type detection (Python, Node, Rust, Go, Java)
- Project info parsing from manifest files
- Security validation for workspace paths
- CGRAG index detection

Author: Backend Architect
Phase: Code Chat Implementation (Phase 1.1)
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import aiofiles

from app.models.code_chat import DirectoryInfo, ProjectInfo

logger = logging.getLogger(__name__)

# Security: Allowed base paths for workspaces
ALLOWED_WORKSPACE_ROOTS = [
    "/workspace",  # Docker volume mount
    "/projects",  # Alternative mount
    "/home",  # User directories (Linux)
    "/Users",  # macOS user directories
]

# Directories to exclude from workspace listings
BLOCKED_DIRECTORIES = {
    "node_modules",
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "venv",
    ".venv",
    "env",
    ".tox",
    "dist",
    "build",
    "target",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    ".idea",
    ".vscode",
    ".DS_Store",
}

# Project detection file patterns
PROJECT_MARKERS = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
    "node": ["package.json"],
    "rust": ["Cargo.toml"],
    "go": ["go.mod"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
}


def validate_path(path: str) -> Tuple[bool, Optional[str]]:
    """Validate path is safe and allowed.

    Args:
        path: Path to validate

    Returns:
        (is_valid, error_message)

    Checks:
        - Path must be absolute
        - Path must resolve to be under allowed roots
        - No path traversal attacks (.. resolution)
        - Path must exist
    """
    try:
        # Convert to Path object and resolve
        path_obj = Path(path).resolve()

        # Check if absolute
        if not path_obj.is_absolute():
            return False, "Path must be absolute"

        # Check if under allowed roots
        is_allowed = any(
            str(path_obj).startswith(root) for root in ALLOWED_WORKSPACE_ROOTS
        )
        if not is_allowed:
            return (
                False,
                f"Path must be under one of: {', '.join(ALLOWED_WORKSPACE_ROOTS)}",
            )

        # Check if exists
        if not path_obj.exists():
            return False, "Path does not exist"

        return True, None

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False, f"Invalid path: {str(e)}"


async def get_parent_path(path: str) -> Optional[str]:
    """Get the parent directory path, or None if at root.

    Args:
        path: Current directory path

    Returns:
        Parent directory path, or None if at filesystem root
    """
    try:
        path_obj = Path(path).resolve()
        parent = path_obj.parent

        # Check if we're at root (parent == self)
        if parent == path_obj:
            return None

        # Validate parent is still allowed
        is_valid, _ = validate_path(str(parent))
        if not is_valid:
            return None

        return str(parent)

    except Exception as e:
        logger.error(f"Error getting parent path: {e}")
        return None


async def check_git_repo(path: str) -> bool:
    """Check if path is inside a git repository.

    Args:
        path: Directory path to check

    Returns:
        True if .git directory exists
    """
    try:
        path_obj = Path(path)
        git_dir = path_obj / ".git"
        return git_dir.exists() and git_dir.is_dir()
    except Exception as e:
        logger.error(f"Error checking git repo: {e}")
        return False


async def detect_project_type(path: str) -> Optional[str]:
    """Detect project type from config files.

    Args:
        path: Directory path to check

    Returns:
        "python", "node", "rust", "go", "java", or None

    Detection rules:
        - Python: pyproject.toml, requirements.txt, setup.py
        - Node: package.json
        - Rust: Cargo.toml
        - Go: go.mod
        - Java: pom.xml, build.gradle
    """
    try:
        path_obj = Path(path)

        for project_type, markers in PROJECT_MARKERS.items():
            for marker in markers:
                if (path_obj / marker).exists():
                    return project_type

        return None

    except Exception as e:
        logger.error(f"Error detecting project type: {e}")
        return None


async def parse_pyproject_toml(path: Path) -> ProjectInfo:
    """Parse Python pyproject.toml for project info.

    Args:
        path: Path to pyproject.toml file

    Returns:
        ProjectInfo with extracted metadata
    """
    try:
        # Use tomllib (Python 3.11+) or tomli for Python 3.10
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        async with aiofiles.open(path, "rb") as f:
            content = await f.read()
            data = tomllib.loads(content.decode("utf-8"))

        # Extract project metadata
        project = data.get("project", {})
        name = project.get("name")
        version = project.get("version")

        # Dependencies
        dependencies = project.get("dependencies", [])
        dev_dependencies = []

        # Optional dependencies
        optional_deps = project.get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            dev_dependencies.extend(deps)

        # Scripts
        scripts = project.get("scripts", {})

        # Entry points
        entry_points = []
        if "scripts" in project:
            entry_points = list(project["scripts"].keys())

        return ProjectInfo(
            type="python",
            name=name,
            version=version,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=scripts,
            entry_points=entry_points,
        )

    except Exception as e:
        logger.error(f"Error parsing pyproject.toml: {e}")
        return ProjectInfo(type="python")


async def parse_package_json(path: Path) -> ProjectInfo:
    """Parse Node.js package.json for project info.

    Args:
        path: Path to package.json file

    Returns:
        ProjectInfo with extracted metadata
    """
    try:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            data = json.loads(content)

        name = data.get("name")
        version = data.get("version")
        dependencies = list(data.get("dependencies", {}).keys())
        dev_dependencies = list(data.get("devDependencies", {}).keys())
        scripts = data.get("scripts", {})

        # Entry points
        entry_points = []
        if "main" in data:
            entry_points.append(data["main"])
        if "module" in data:
            entry_points.append(data["module"])

        return ProjectInfo(
            type="node",
            name=name,
            version=version,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=scripts,
            entry_points=entry_points,
        )

    except Exception as e:
        logger.error(f"Error parsing package.json: {e}")
        return ProjectInfo(type="node")


async def parse_cargo_toml(path: Path) -> ProjectInfo:
    """Parse Rust Cargo.toml for project info.

    Args:
        path: Path to Cargo.toml file

    Returns:
        ProjectInfo with extracted metadata
    """
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        async with aiofiles.open(path, "rb") as f:
            content = await f.read()
            data = tomllib.loads(content.decode("utf-8"))

        package = data.get("package", {})
        name = package.get("name")
        version = package.get("version")

        dependencies = list(data.get("dependencies", {}).keys())
        dev_dependencies = list(data.get("dev-dependencies", {}).keys())

        # Scripts (from Cargo.toml aliases if present)
        scripts = {}

        # Entry points
        entry_points = []
        if "bin" in data:
            for bin_entry in data["bin"]:
                if "path" in bin_entry:
                    entry_points.append(bin_entry["path"])

        return ProjectInfo(
            type="rust",
            name=name,
            version=version,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            scripts=scripts,
            entry_points=entry_points,
        )

    except Exception as e:
        logger.error(f"Error parsing Cargo.toml: {e}")
        return ProjectInfo(type="rust")


async def parse_go_mod(path: Path) -> ProjectInfo:
    """Parse Go go.mod for project info.

    Args:
        path: Path to go.mod file

    Returns:
        ProjectInfo with extracted metadata
    """
    try:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()

        name = None
        version = None
        dependencies = []

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("module "):
                name = line.replace("module ", "").strip()

            if line.startswith("go "):
                version = line.replace("go ", "").strip()

            # Dependencies from require blocks
            if line.startswith("require "):
                # Single line require
                dep = line.replace("require ", "").strip()
                dependencies.append(dep.split()[0])

        return ProjectInfo(
            type="go",
            name=name,
            version=version,
            dependencies=dependencies,
            dev_dependencies=[],
            scripts={},
            entry_points=[],
        )

    except Exception as e:
        logger.error(f"Error parsing go.mod: {e}")
        return ProjectInfo(type="go")


async def detect_project_info(path: str) -> Optional[ProjectInfo]:
    """Detect detailed project information.

    Args:
        path: Directory path to analyze

    Returns:
        ProjectInfo with extracted metadata, or None if not a project

    Parses project config files to extract:
        - Project name and version
        - Dependencies and dev dependencies
        - Scripts (npm scripts, Makefile targets, etc.)
        - Entry points (main files)
    """
    try:
        path_obj = Path(path)

        # Python projects
        if (path_obj / "pyproject.toml").exists():
            return await parse_pyproject_toml(path_obj / "pyproject.toml")

        # Node projects
        if (path_obj / "package.json").exists():
            return await parse_package_json(path_obj / "package.json")

        # Rust projects
        if (path_obj / "Cargo.toml").exists():
            return await parse_cargo_toml(path_obj / "Cargo.toml")

        # Go projects
        if (path_obj / "go.mod").exists():
            return await parse_go_mod(path_obj / "go.mod")

        return None

    except Exception as e:
        logger.error(f"Error detecting project info: {e}")
        return None


async def is_valid_workspace(path: str) -> bool:
    """Check if a path is a valid workspace.

    Args:
        path: Path to validate

    Returns:
        True if valid workspace

    Valid if:
        - Path exists and is a directory
        - Path is not a system directory
        - Path is readable
    """
    is_valid, _ = validate_path(path)
    if not is_valid:
        return False

    try:
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_dir()
    except Exception:
        return False


async def count_files(path: str, max_count: int = 10000) -> int:
    """Count files in directory (recursively with limit).

    Args:
        path: Directory path
        max_count: Maximum files to count before stopping

    Returns:
        Number of files found (capped at max_count)
    """
    try:
        path_obj = Path(path)
        count = 0

        for item in path_obj.rglob("*"):
            if item.is_file():
                count += 1
                if count >= max_count:
                    break

        return count

    except Exception as e:
        logger.error(f"Error counting files: {e}")
        return 0


async def check_cgrag_index_exists(path: str) -> bool:
    """Check if a CGRAG index exists for this workspace.

    Args:
        path: Workspace path

    Returns:
        True if index exists

    Check in data/faiss_indexes/ for an index matching the workspace name.
    """
    try:
        # Get workspace name from path
        workspace_name = Path(path).name

        # Check for index files
        index_dir = Path(__file__).parents[3] / "data" / "faiss_indexes"
        index_path = index_dir / workspace_name

        # Check if index directory exists and has required files
        if not index_path.exists():
            return False

        # FAISS index should have .index file
        index_file = index_path / "index.faiss"
        metadata_file = index_path / "metadata.json"

        return index_file.exists() and metadata_file.exists()

    except Exception as e:
        logger.error(f"Error checking CGRAG index: {e}")
        return False


async def list_directories(path: str) -> List[DirectoryInfo]:
    """List directories available for workspace selection.

    Args:
        path: Current directory path to list

    Returns:
        List of DirectoryInfo objects for subdirectories

    - Returns directories (not files) at the given path
    - Detects if each directory is a git repo
    - Detects project type for each directory
    - Filters out hidden directories (starting with .)
    - Filters out common non-workspace directories
    """
    directories = []

    try:
        path_obj = Path(path)

        # List all entries
        for entry in sorted(path_obj.iterdir()):
            # Skip files
            if not entry.is_dir():
                continue

            # Skip hidden directories
            if entry.name.startswith("."):
                continue

            # Skip blocked directories
            if entry.name in BLOCKED_DIRECTORIES:
                continue

            # Check git repo status
            is_git = await check_git_repo(str(entry))

            # Detect project type
            project_type = await detect_project_type(str(entry))

            # Create DirectoryInfo
            dir_info = DirectoryInfo(
                name=entry.name,
                path=str(entry.resolve()),
                is_directory=True,
                is_git_repo=is_git,
                project_type=project_type,
            )

            directories.append(dir_info)

    except PermissionError:
        logger.warning(f"Permission denied listing directory: {path}")
    except Exception as e:
        logger.error(f"Error listing directories: {e}")

    return directories

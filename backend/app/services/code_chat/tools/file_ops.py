"""File operation tools for Code Chat mode.

Provides secure file operations within workspace boundary:
- read_file: Read file contents with size limits
- write_file: Create/overwrite files with diff preview
- list_directory: List directory contents
- delete_file: Remove files with confirmation

All operations enforce strict security boundaries:
- Path traversal prevention via path resolution
- Symlink target validation
- File size limits (10MB)
- Comprehensive audit logging

Author: Backend Architect
Phase: Code Chat Implementation (Session 2.2)
"""

import aiofiles
import logging
import difflib
from pathlib import Path
from typing import List, Optional

from app.models.code_chat import ToolName, ToolResult, DiffLine, DiffPreview
from app.services.code_chat.tools.base import BaseTool, SecurityError

logger = logging.getLogger(__name__)

# Limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_READ_LINES = 50000
MAX_DIRECTORY_ENTRIES = 1000

# Blocked patterns
BLOCKED_DIRECTORIES = {'node_modules', '__pycache__', '.git', '.venv', 'venv', '.tox'}


class ReadFileTool(BaseTool):
    """Read file contents with security validation.

    Reads text files from the workspace with strict size limits and
    path validation. Handles various encodings and provides detailed
    error messages.

    Security features:
    - Path traversal prevention
    - Symlink target validation
    - File size enforcement (10MB max)
    - Audit logging

    Attributes:
        name: ToolName.READ_FILE
        description: Read file contents
        parameter_schema: JSON schema for path and encoding
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.READ_FILE
    description = "Read file contents from workspace"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative or absolute path to file"
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8"
            }
        },
        "required": ["path"]
    }

    def __init__(self, workspace_root: str):
        """Initialize read file tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _validate_and_resolve(self, path: str) -> Path:
        """Validate and resolve path within workspace.

        Args:
            path: Relative or absolute path

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If path escapes workspace or is invalid
        """
        # Resolve path (handles relative paths)
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_root / path).resolve()

        # Check if within workspace root
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Path traversal attempt: {path} resolves outside workspace"
            )

        # Validate symlink targets
        if resolved.is_symlink():
            target = resolved.readlink()
            if target.is_absolute():
                target_resolved = target.resolve()
            else:
                target_resolved = (resolved.parent / target).resolve()

            # Check symlink target is within workspace
            try:
                target_resolved.relative_to(self.workspace_root)
            except ValueError:
                raise SecurityError(
                    f"Symlink escape attempt: {path} -> {target} outside workspace"
                )

        return resolved

    async def execute(self, path: str, encoding: str = "utf-8") -> ToolResult:
        """Read file contents.

        Args:
            path: Relative or absolute path to file
            encoding: File encoding (default: utf-8)

        Returns:
            ToolResult with file contents or error
        """
        try:
            # Validate and resolve path
            resolved_path = self._validate_and_resolve(path)

            # Check file exists
            if not resolved_path.exists():
                logger.warning(f"File not found: {path}")
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}"
                )

            # Check is regular file
            if not resolved_path.is_file():
                logger.warning(f"Not a regular file: {path}")
                return ToolResult(
                    success=False,
                    error=f"Not a regular file: {path}"
                )

            # Check file size
            file_size = resolved_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                logger.warning(
                    f"File too large: {path} ({file_size} bytes > {MAX_FILE_SIZE} bytes)"
                )
                return ToolResult(
                    success=False,
                    error=f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)"
                )

            # Read file
            async with aiofiles.open(resolved_path, 'r', encoding=encoding) as f:
                content = await f.read()

            # Audit log
            logger.info(
                f"READ_FILE: {path} ({file_size} bytes, {len(content.splitlines())} lines)"
            )

            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "path": str(resolved_path),
                    "size_bytes": file_size,
                    "line_count": len(content.splitlines()),
                    "encoding": encoding
                }
            )

        except SecurityError as e:
            # Security violations logged at warning level
            logger.warning(f"Security violation in read_file: {e}")
            return ToolResult(success=False, error=str(e))

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {path}: {e}")
            return ToolResult(
                success=False,
                error=f"Encoding error: file may be binary or use different encoding than {encoding}"
            )

        except Exception as e:
            logger.error(f"Error reading file {path}: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Error reading file: {str(e)}")


class WriteFileTool(BaseTool):
    """Write file contents with diff preview.

    Creates or overwrites files in the workspace with automatic diff
    generation for existing files. Enforces size limits and creates
    parent directories as needed.

    Security features:
    - Path traversal prevention
    - Content size enforcement (10MB max)
    - Parent directory creation (sandboxed)
    - Audit logging with diff preview

    Attributes:
        name: ToolName.WRITE_FILE
        description: Write file contents
        parameter_schema: JSON schema for path, content, create_dirs
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.WRITE_FILE
    description = "Write file contents to workspace"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative or absolute path to file"
            },
            "content": {
                "type": "string",
                "description": "File content to write"
            },
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories if needed (default: True)",
                "default": True
            }
        },
        "required": ["path", "content"]
    }

    def __init__(self, workspace_root: str):
        """Initialize write file tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _validate_and_resolve(self, path: str) -> Path:
        """Validate and resolve path within workspace.

        Args:
            path: Relative or absolute path

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If path escapes workspace
        """
        # Resolve path
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_root / path).resolve()

        # Check if within workspace root
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Path traversal attempt: {path} resolves outside workspace"
            )

        return resolved

    def _create_diff_preview(
        self,
        path: Path,
        original: Optional[str],
        new: str,
        change_type: str
    ) -> DiffPreview:
        """Create diff preview for file changes.

        Args:
            path: File path
            original: Original content (None for new files)
            new: New content
            change_type: "create" or "modify"

        Returns:
            DiffPreview with unified diff
        """
        diff_lines = []

        if original is not None:
            # Generate unified diff
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{path.name}",
                tofile=f"b/{path.name}",
                lineterm=""
            )

            # Parse diff lines
            line_num = 0
            for line in diff:
                # Skip diff headers
                if line.startswith("---") or line.startswith("+++"):
                    continue
                if line.startswith("@@"):
                    continue

                line_num += 1
                if line.startswith("+"):
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="add",
                        content=line[1:]
                    ))
                elif line.startswith("-"):
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="remove",
                        content=line[1:]
                    ))
                else:
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="context",
                        content=line[1:] if line.startswith(" ") else line
                    ))

        return DiffPreview(
            file_path=str(path),
            original_content=original,
            new_content=new,
            diff_lines=diff_lines,
            change_type=change_type
        )

    async def execute(
        self,
        path: str,
        content: str,
        create_dirs: bool = True
    ) -> ToolResult:
        """Write file contents.

        Args:
            path: Relative or absolute path to file
            content: File content to write
            create_dirs: Create parent directories if needed

        Returns:
            ToolResult with success message and diff preview
        """
        try:
            # Validate content size
            content_size = len(content.encode('utf-8'))
            if content_size > MAX_FILE_SIZE:
                logger.warning(
                    f"Content too large: {content_size} bytes > {MAX_FILE_SIZE} bytes"
                )
                return ToolResult(
                    success=False,
                    error=f"Content too large: {content_size} bytes (max: {MAX_FILE_SIZE} bytes)"
                )

            # Validate and resolve path
            resolved_path = self._validate_and_resolve(path)

            # Check if file exists (for diff preview)
            original_content = None
            change_type = "create"

            if resolved_path.exists():
                if resolved_path.is_file():
                    # Read original content for diff
                    async with aiofiles.open(resolved_path, 'r', encoding='utf-8') as f:
                        original_content = await f.read()
                    change_type = "modify"
                else:
                    return ToolResult(
                        success=False,
                        error=f"Path exists but is not a file: {path}"
                    )

            # Create parent directories if needed
            if create_dirs:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            async with aiofiles.open(resolved_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            # Generate diff preview
            diff_preview = self._create_diff_preview(
                resolved_path,
                original_content,
                content,
                change_type
            )

            # Audit log
            logger.info(
                f"WRITE_FILE: {path} ({change_type}, {content_size} bytes, "
                f"{len(content.splitlines())} lines)"
            )

            return ToolResult(
                success=True,
                output=f"{'Created' if change_type == 'create' else 'Modified'} file: {path}",
                data={
                    "diff_preview": diff_preview.model_dump(),
                    "change_type": change_type,
                    "size_bytes": content_size,
                    "line_count": len(content.splitlines())
                },
                metadata={
                    "path": str(resolved_path),
                    "change_type": change_type
                }
            )

        except SecurityError as e:
            logger.warning(f"Security violation in write_file: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error writing file {path}: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Error writing file: {str(e)}")


class ListDirectoryTool(BaseTool):
    """List directory contents with metadata.

    Lists files and directories within the workspace with type detection,
    size information, and optional recursive scanning.

    Security features:
    - Path traversal prevention
    - Entry count limits (max 1000)
    - Depth limits for recursive listings
    - Blocked directory filtering

    Attributes:
        name: ToolName.LIST_DIRECTORY
        description: List directory contents
        parameter_schema: JSON schema for path, recursive, max_depth
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.LIST_DIRECTORY
    description = "List directory contents"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative or absolute directory path (default: workspace root)",
                "default": "."
            },
            "recursive": {
                "type": "boolean",
                "description": "List recursively (default: False)",
                "default": False
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum recursion depth (default: 2)",
                "default": 2,
                "minimum": 1,
                "maximum": 10
            }
        },
        "required": []
    }

    def __init__(self, workspace_root: str):
        """Initialize list directory tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _validate_and_resolve(self, path: str) -> Path:
        """Validate and resolve path within workspace.

        Args:
            path: Relative or absolute path

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If path escapes workspace
        """
        # Resolve path
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_root / path).resolve()

        # Check if within workspace root
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Path traversal attempt: {path} resolves outside workspace"
            )

        return resolved

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _list_entries(
        self,
        path: Path,
        recursive: bool,
        max_depth: int,
        current_depth: int = 0
    ) -> List[str]:
        """Recursively list directory entries.

        Args:
            path: Directory path
            recursive: Whether to recurse
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth

        Returns:
            List of formatted entry strings
        """
        entries = []
        count = 0

        try:
            for entry in sorted(path.iterdir()):
                # Check entry limit
                if count >= MAX_DIRECTORY_ENTRIES:
                    entries.append(
                        f"\n... (truncated, max {MAX_DIRECTORY_ENTRIES} entries)"
                    )
                    break

                # Skip hidden files (except .gitignore, .env, etc.)
                if entry.name.startswith('.') and entry.name not in {
                    '.gitignore', '.env', '.env.example', '.dockerignore'
                }:
                    continue

                # Skip blocked directories
                if entry.is_dir() and entry.name in BLOCKED_DIRECTORIES:
                    continue

                # Format entry
                indent = "  " * current_depth
                if entry.is_dir():
                    entries.append(f"{indent}{entry.name}/")

                    # Recurse if enabled and within depth limit
                    if recursive and current_depth < max_depth:
                        sub_entries = self._list_entries(
                            entry,
                            recursive,
                            max_depth,
                            current_depth + 1
                        )
                        entries.extend(sub_entries)
                else:
                    # File with size
                    size = entry.stat().st_size
                    size_str = self._format_size(size)
                    entries.append(f"{indent}{entry.name} ({size_str})")

                count += 1

        except PermissionError:
            entries.append(f"{path.name}: Permission denied")

        return entries

    async def execute(
        self,
        path: str = ".",
        recursive: bool = False,
        max_depth: int = 2
    ) -> ToolResult:
        """List directory contents.

        Args:
            path: Relative or absolute directory path
            recursive: List recursively
            max_depth: Maximum recursion depth

        Returns:
            ToolResult with formatted directory listing
        """
        try:
            # Validate and resolve path
            resolved_path = self._validate_and_resolve(path)

            # Check directory exists
            if not resolved_path.exists():
                logger.warning(f"Directory not found: {path}")
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {path}"
                )

            # Check is directory
            if not resolved_path.is_dir():
                logger.warning(f"Not a directory: {path}")
                return ToolResult(
                    success=False,
                    error=f"Not a directory: {path}"
                )

            # List entries
            entries = self._list_entries(resolved_path, recursive, max_depth)

            # Format output
            output = f"Directory: {resolved_path}\n\n"
            output += "\n".join(entries)

            # Audit log
            logger.info(
                f"LIST_DIRECTORY: {path} (recursive={recursive}, "
                f"{len(entries)} entries)"
            )

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "path": str(resolved_path),
                    "entry_count": len(entries),
                    "recursive": recursive
                }
            )

        except SecurityError as e:
            logger.warning(f"Security violation in list_directory: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Error listing directory: {str(e)}")


class DeleteFileTool(BaseTool):
    """Delete file with confirmation requirement.

    Removes files from the workspace after user confirmation.
    Always requires confirmation to prevent accidental deletions.

    Security features:
    - Path traversal prevention
    - Confirmation requirement (never auto-deletes)
    - Audit logging
    - Directory deletion prevention (files only)

    Attributes:
        name: ToolName.DELETE_FILE
        description: Delete file
        parameter_schema: JSON schema for path
        workspace_root: Absolute path to workspace directory
        requires_confirmation: Always True
    """

    name = ToolName.DELETE_FILE
    description = "Delete file from workspace (requires confirmation)"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative or absolute path to file"
            }
        },
        "required": ["path"]
    }
    requires_confirmation = True

    def __init__(self, workspace_root: str):
        """Initialize delete file tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _validate_and_resolve(self, path: str) -> Path:
        """Validate and resolve path within workspace.

        Args:
            path: Relative or absolute path

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If path escapes workspace
        """
        # Resolve path
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_root / path).resolve()

        # Check if within workspace root
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Path traversal attempt: {path} resolves outside workspace"
            )

        return resolved

    async def execute(self, path: str) -> ToolResult:
        """Delete file (returns confirmation request).

        This tool ALWAYS requires confirmation and will NOT delete files
        immediately. Instead, it returns a confirmation request.

        Args:
            path: Relative or absolute path to file

        Returns:
            ToolResult with confirmation request
        """
        try:
            # Validate and resolve path
            resolved_path = self._validate_and_resolve(path)

            # Check file exists
            if not resolved_path.exists():
                logger.warning(f"File not found: {path}")
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}"
                )

            # Check is regular file (not directory)
            if not resolved_path.is_file():
                logger.warning(f"Not a regular file: {path}")
                return ToolResult(
                    success=False,
                    error=f"Not a regular file (use dedicated directory deletion tool): {path}"
                )

            # Get file info
            file_size = resolved_path.stat().st_size

            # Audit log
            logger.info(
                f"DELETE_FILE requested: {path} ({file_size} bytes)"
            )

            # Return confirmation request
            return ToolResult(
                success=True,
                output=f"Confirm deletion of: {path} ({file_size} bytes)",
                requires_confirmation=True,
                confirmation_type="file_delete",
                metadata={
                    "path": str(resolved_path),
                    "size_bytes": file_size
                }
            )

        except SecurityError as e:
            logger.warning(f"Security violation in delete_file: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Error deleting file: {str(e)}")

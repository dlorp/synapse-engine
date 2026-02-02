"""Git tools for Code Chat mode.

Provides safe git operations within workspace boundary:
- git_status: Get working tree status
- git_diff: View file diffs (staged or unstaged)
- git_log: View commit history
- git_commit: Create commits (requires confirmation)
- git_branch: List branches and get current branch

All operations enforce strict security boundaries:
- Git repository validation
- Operations limited to workspace root only
- No destructive operations (force push, hard reset, etc.)
- Commit operations require user confirmation
- Comprehensive audit logging

Author: Backend Architect
Phase: Code Chat Implementation (Git Tools)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

from app.models.code_chat import ToolName, ToolResult
from app.services.code_chat.tools.base import BaseTool, SecurityError

logger = logging.getLogger(__name__)


class GitStatusTool(BaseTool):
    """Get git status showing modified, staged, and untracked files.

    Returns structured output with:
    - Modified files (staged and unstaged)
    - Untracked files
    - Deleted files
    - Current branch information

    Security features:
    - Validates workspace is a git repository
    - All operations limited to workspace root
    - Read-only operation (no modifications)

    Attributes:
        name: ToolName.GIT_STATUS
        description: Get current git status
        parameter_schema: JSON schema (no parameters required)
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GIT_STATUS
    description = (
        "Get the current git status showing modified, staged, and untracked files"
    )
    parameter_schema = {"type": "object", "properties": {}, "required": []}

    def __init__(self, workspace_root: str):
        """Initialize git status tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if .git directory exists, False otherwise
        """
        return (self.workspace_root / ".git").exists()

    async def execute(self, **kwargs) -> ToolResult:
        """Get git status.

        Returns:
            ToolResult with formatted git status or error
        """
        try:
            # Validate workspace is git repo
            if not self._is_git_repo():
                logger.warning(f"Not a git repository: {self.workspace_root}")
                return ToolResult(
                    success=False, error=f"Not a git repository: {self.workspace_root}"
                )

            # Run git status --porcelain for machine-readable output
            proc = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                "--branch",
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"git status failed: {error_msg}")
                return ToolResult(
                    success=False, error=f"git status failed: {error_msg}"
                )

            # Parse output
            output = stdout.decode()
            lines = output.strip().split("\n")

            # Extract branch info (first line with ##)
            branch_info = ""
            file_lines = []
            for line in lines:
                if line.startswith("##"):
                    branch_info = line[3:].strip()
                elif line.strip():
                    file_lines.append(line)

            # Format output
            formatted_output = f"Branch: {branch_info}\n\n"

            if file_lines:
                formatted_output += "Changes:\n"
                for line in file_lines:
                    # Parse status codes (first 2 chars)
                    status = line[:2]
                    filepath = line[3:].strip()

                    # Map status codes to readable format
                    if status == "M ":
                        formatted_output += f"  Modified (staged):   {filepath}\n"
                    elif status == " M":
                        formatted_output += f"  Modified (unstaged): {filepath}\n"
                    elif status == "MM":
                        formatted_output += f"  Modified (both):     {filepath}\n"
                    elif status == "A ":
                        formatted_output += f"  Added (staged):      {filepath}\n"
                    elif status == "D ":
                        formatted_output += f"  Deleted (staged):    {filepath}\n"
                    elif status == " D":
                        formatted_output += f"  Deleted (unstaged):  {filepath}\n"
                    elif status == "??":
                        formatted_output += f"  Untracked:           {filepath}\n"
                    elif status == "R ":
                        formatted_output += f"  Renamed:             {filepath}\n"
                    else:
                        formatted_output += f"  {status}: {filepath}\n"
            else:
                formatted_output += "Working tree clean\n"

            # Audit log
            logger.info(
                f"GIT_STATUS: {self.workspace_root} ({len(file_lines)} changes)"
            )

            return ToolResult(
                success=True,
                output=formatted_output,
                metadata={
                    "branch": branch_info,
                    "change_count": len(file_lines),
                    "has_changes": len(file_lines) > 0,
                },
            )

        except Exception as e:
            logger.error(f"Error executing git status: {e}", exc_info=True)
            return ToolResult(
                success=False, error=f"Error executing git status: {str(e)}"
            )


class GitDiffTool(BaseTool):
    """Get git diff for modified files.

    Shows unified diff for:
    - Unstaged changes (default)
    - Staged changes (with staged=true)
    - Specific file (with file parameter)

    Security features:
    - Validates workspace is a git repository
    - All operations limited to workspace root
    - Read-only operation (no modifications)

    Attributes:
        name: ToolName.GIT_DIFF
        description: Get diff for modified files
        parameter_schema: JSON schema for file and staged parameters
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GIT_DIFF
    description = "Get the diff for modified files, optionally for a specific file or staged changes"
    parameter_schema = {
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "Specific file to diff (optional)",
            },
            "staged": {
                "type": "boolean",
                "description": "Show staged changes instead of unstaged (default: false)",
                "default": False,
            },
        },
        "required": [],
    }

    def __init__(self, workspace_root: str):
        """Initialize git diff tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if .git directory exists, False otherwise
        """
        return (self.workspace_root / ".git").exists()

    async def execute(
        self, file: Optional[str] = None, staged: bool = False, **kwargs
    ) -> ToolResult:
        """Get git diff.

        Args:
            file: Specific file to diff (optional)
            staged: Show staged changes instead of unstaged

        Returns:
            ToolResult with diff output or error
        """
        try:
            # Validate workspace is git repo
            if not self._is_git_repo():
                logger.warning(f"Not a git repository: {self.workspace_root}")
                return ToolResult(
                    success=False, error=f"Not a git repository: {self.workspace_root}"
                )

            # Build git diff command
            cmd = ["git", "diff"]

            if staged:
                cmd.append("--staged")

            if file:
                # Validate file is within workspace (security check)
                file_path = Path(file)
                if file_path.is_absolute():
                    try:
                        file_path.relative_to(self.workspace_root)
                    except ValueError:
                        raise SecurityError(f"File path outside workspace: {file}")
                cmd.append("--")
                cmd.append(file)

            # Run git diff
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"git diff failed: {error_msg}")
                return ToolResult(success=False, error=f"git diff failed: {error_msg}")

            diff_output = stdout.decode()

            # Track whether there are actual changes
            has_changes = bool(diff_output.strip())

            # Format output message
            if not has_changes:
                output_msg = "No changes"
                if staged:
                    output_msg += " in staging area"
                if file:
                    output_msg += f" for {file}"
                diff_output = output_msg

            # Audit log
            logger.info(
                f"GIT_DIFF: {self.workspace_root} "
                f"(staged={staged}, file={file or 'all'})"
            )

            return ToolResult(
                success=True,
                output=diff_output,
                metadata={"staged": staged, "file": file, "has_changes": has_changes},
            )

        except SecurityError as e:
            logger.warning(f"Security violation in git_diff: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error executing git diff: {e}", exc_info=True)
            return ToolResult(
                success=False, error=f"Error executing git diff: {str(e)}"
            )


class GitLogTool(BaseTool):
    """Get recent commit history.

    Shows commit log with:
    - Commit hash (short)
    - Author and date
    - Commit message
    - Optional file-specific history

    Security features:
    - Validates workspace is a git repository
    - All operations limited to workspace root
    - Read-only operation (no modifications)

    Attributes:
        name: ToolName.GIT_LOG
        description: Get recent commit history
        parameter_schema: JSON schema for count and file parameters
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GIT_LOG
    description = "Get recent commit history with messages and authors"
    parameter_schema = {
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "Number of commits to show (default: 10)",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "file": {
                "type": "string",
                "description": "Show history for specific file (optional)",
            },
        },
        "required": [],
    }

    def __init__(self, workspace_root: str):
        """Initialize git log tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if .git directory exists, False otherwise
        """
        return (self.workspace_root / ".git").exists()

    async def execute(
        self, count: int = 10, file: Optional[str] = None, **kwargs
    ) -> ToolResult:
        """Get commit history.

        Args:
            count: Number of commits to show
            file: Show history for specific file (optional)

        Returns:
            ToolResult with formatted commit log or error
        """
        try:
            # Validate workspace is git repo
            if not self._is_git_repo():
                logger.warning(f"Not a git repository: {self.workspace_root}")
                return ToolResult(
                    success=False, error=f"Not a git repository: {self.workspace_root}"
                )

            # Build git log command with pretty format
            cmd = [
                "git",
                "log",
                f"-n{count}",
                "--pretty=format:%h|%an|%ar|%s",
                "--decorate=short",
            ]

            if file:
                # Validate file is within workspace (security check)
                file_path = Path(file)
                if file_path.is_absolute():
                    try:
                        file_path.relative_to(self.workspace_root)
                    except ValueError:
                        raise SecurityError(f"File path outside workspace: {file}")
                cmd.append("--")
                cmd.append(file)

            # Run git log
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"git log failed: {error_msg}")
                return ToolResult(success=False, error=f"git log failed: {error_msg}")

            # Parse and format output
            log_output = stdout.decode()
            if not log_output.strip():
                return ToolResult(
                    success=True,
                    output="No commits found",
                    metadata={"commit_count": 0},
                )

            lines = log_output.strip().split("\n")
            formatted_output = f"Recent commits (last {len(lines)}):\n\n"

            for line in lines:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commit_hash, author, date, message = parts
                    formatted_output += f"{commit_hash}  {message}\n"
                    formatted_output += f"         by {author}, {date}\n\n"

            # Audit log
            logger.info(
                f"GIT_LOG: {self.workspace_root} (count={count}, file={file or 'all'})"
            )

            return ToolResult(
                success=True,
                output=formatted_output,
                metadata={"commit_count": len(lines), "file": file},
            )

        except SecurityError as e:
            logger.warning(f"Security violation in git_log: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error executing git log: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Error executing git log: {str(e)}")


class GitCommitTool(BaseTool):
    """Create a git commit with user confirmation.

    Stages and commits changes with a message. ALWAYS requires user
    confirmation before executing.

    Best practice: Agent should show diff first using GitDiffTool
    before attempting commit.

    Security features:
    - Validates workspace is a git repository
    - Requires user confirmation (never auto-commits)
    - All operations limited to workspace root
    - No force operations or destructive changes
    - Comprehensive audit logging

    Attributes:
        name: ToolName.GIT_COMMIT
        description: Create a commit
        parameter_schema: JSON schema for message and files
        workspace_root: Absolute path to workspace directory
        requires_confirmation: Always True
    """

    name = ToolName.GIT_COMMIT
    description = (
        "Stage and commit changes with a message. "
        "IMPORTANT: Always show diff first using git_diff tool."
    )
    parameter_schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Commit message",
                "minLength": 1,
                "maxLength": 1000,
            },
            "files": {
                "type": "array",
                "description": "Specific files to stage (optional, default: all changes)",
                "items": {"type": "string"},
            },
        },
        "required": ["message"],
    }
    requires_confirmation = True

    def __init__(self, workspace_root: str):
        """Initialize git commit tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if .git directory exists, False otherwise
        """
        return (self.workspace_root / ".git").exists()

    async def execute(
        self, message: str, files: Optional[List[str]] = None, **kwargs
    ) -> ToolResult:
        """Create commit (returns confirmation request).

        This tool ALWAYS requires confirmation and will NOT commit
        immediately. Instead, it returns a confirmation request.

        Args:
            message: Commit message
            files: Specific files to stage (optional)

        Returns:
            ToolResult with confirmation request
        """
        try:
            # Validate workspace is git repo
            if not self._is_git_repo():
                logger.warning(f"Not a git repository: {self.workspace_root}")
                return ToolResult(
                    success=False, error=f"Not a git repository: {self.workspace_root}"
                )

            # Validate files if specified
            if files:
                for file in files:
                    file_path = Path(file)
                    if file_path.is_absolute():
                        try:
                            file_path.relative_to(self.workspace_root)
                        except ValueError:
                            raise SecurityError(f"File path outside workspace: {file}")

            # Check if there are changes to commit
            status_proc = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            status_stdout, _ = await status_proc.communicate()

            if not status_stdout.decode().strip():
                return ToolResult(success=False, error="No changes to commit")

            # Format confirmation message
            confirmation_msg = f"Commit message: {message}\n\n"
            if files:
                confirmation_msg += f"Files to stage: {', '.join(files)}\n"
            else:
                confirmation_msg += "Files to stage: all changes\n"

            # Audit log
            logger.info(
                f"GIT_COMMIT requested: {self.workspace_root} "
                f"(message='{message[:50]}...', files={files or 'all'})"
            )

            # Return confirmation request
            return ToolResult(
                success=True,
                output=confirmation_msg,
                requires_confirmation=True,
                confirmation_type="git_commit",
                data={"message": message, "files": files},
                metadata={"message": message, "files": files or []},
            )

        except SecurityError as e:
            logger.warning(f"Security violation in git_commit: {e}")
            return ToolResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Error executing git commit: {e}", exc_info=True)
            return ToolResult(
                success=False, error=f"Error executing git commit: {str(e)}"
            )


class GitBranchTool(BaseTool):
    """List branches and get current branch.

    Shows:
    - Current branch name
    - All local branches
    - Remote tracking branches (if available)

    Security features:
    - Validates workspace is a git repository
    - All operations limited to workspace root
    - Read-only operation (no modifications)

    Attributes:
        name: ToolName.GIT_BRANCH
        description: List branches
        parameter_schema: JSON schema (no parameters required)
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GIT_BRANCH
    description = "List branches or get current branch name"
    parameter_schema = {"type": "object", "properties": {}, "required": []}

    def __init__(self, workspace_root: str):
        """Initialize git branch tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if .git directory exists, False otherwise
        """
        return (self.workspace_root / ".git").exists()

    async def execute(self, **kwargs) -> ToolResult:
        """List branches and show current.

        Returns:
            ToolResult with branch information or error
        """
        try:
            # Validate workspace is git repo
            if not self._is_git_repo():
                logger.warning(f"Not a git repository: {self.workspace_root}")
                return ToolResult(
                    success=False, error=f"Not a git repository: {self.workspace_root}"
                )

            # Get current branch
            current_proc = await asyncio.create_subprocess_exec(
                "git",
                "branch",
                "--show-current",
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            current_stdout, current_stderr = await current_proc.communicate()

            if current_proc.returncode != 0:
                error_msg = current_stderr.decode().strip()
                logger.error(f"git branch --show-current failed: {error_msg}")
                return ToolResult(
                    success=False, error=f"git branch failed: {error_msg}"
                )

            current_branch = current_stdout.decode().strip()

            # Get all branches
            all_proc = await asyncio.create_subprocess_exec(
                "git",
                "branch",
                "-a",
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            all_stdout, all_stderr = await all_proc.communicate()

            if all_proc.returncode != 0:
                error_msg = all_stderr.decode().strip()
                logger.error(f"git branch -a failed: {error_msg}")
                # Don't fail entirely, just return current branch
                return ToolResult(
                    success=True,
                    output=f"Current branch: {current_branch}\n(Could not list other branches)",
                    metadata={"current_branch": current_branch},
                )

            # Parse and format output
            branches = all_stdout.decode().strip().split("\n")
            formatted_output = f"Current branch: {current_branch}\n\n"
            formatted_output += "All branches:\n"

            local_branches = []
            remote_branches = []

            for branch in branches:
                branch = branch.strip()
                if branch.startswith("* "):
                    # Current branch
                    branch_name = branch[2:].strip()
                    local_branches.append(f"  * {branch_name} (current)")
                elif branch.startswith("remotes/"):
                    # Remote branch
                    remote_branches.append(f"  {branch}")
                else:
                    # Other local branch
                    local_branches.append(f"    {branch}")

            if local_branches:
                formatted_output += "\n".join(local_branches) + "\n"

            if remote_branches:
                formatted_output += "\nRemote branches:\n"
                formatted_output += "\n".join(remote_branches) + "\n"

            # Audit log
            logger.info(f"GIT_BRANCH: {self.workspace_root} (current={current_branch})")

            return ToolResult(
                success=True,
                output=formatted_output,
                metadata={
                    "current_branch": current_branch,
                    "branch_count": len(branches),
                },
            )

        except Exception as e:
            logger.error(f"Error executing git branch: {e}", exc_info=True)
            return ToolResult(
                success=False, error=f"Error executing git branch: {str(e)}"
            )

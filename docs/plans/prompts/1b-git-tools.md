# Task: Implement Git MCP Tools for Code Chat

You are implementing Git tools that the ReAct agent can use during code chat sessions. These follow the existing tool pattern in `backend/app/services/code_chat/tools/`.

## Context

- Tool types defined in: `frontend/src/types/codeChat.ts` (git_status, git_diff, git_log, git_commit, git_branch)
- Tool base class: `backend/app/services/code_chat/tools/base.py`
- Existing tools example: `backend/app/services/code_chat/tools/file_ops.py`
- Router: `backend/app/routers/code_chat.py`
- Read SESSION_NOTES.md for recent context

## Requirements

### git.py (~350 lines) - Create 5 tool classes

#### 1. GitStatusTool

```python
class GitStatusTool(BaseTool):
    """Shows working tree status."""
    name = "git_status"
    description = "Show the working tree status including modified, staged, and untracked files."

    async def execute(self, **params) -> ToolResult:
        # Run git status --porcelain
        # Parse output into structured format
        # Return formatted status
```

- Parameters: None (operates on current workspace)
- Returns: Formatted status with modified/staged/untracked files

#### 2. GitDiffTool

```python
class GitDiffTool(BaseTool):
    """Shows diff for specific file or all changes."""
    name = "git_diff"
    description = "Show changes between commits, working tree, etc."

    async def execute(self, file_path: str = None, staged: bool = False) -> ToolResult:
        # Run git diff (--staged if staged=True)
        # Optionally filter by file_path
        # Return unified diff format
```

- Parameters: `file_path` (optional), `staged` (bool, default False)
- Returns: Unified diff format

#### 3. GitLogTool

```python
class GitLogTool(BaseTool):
    """Shows commit history."""
    name = "git_log"
    description = "Show commit logs."

    async def execute(self, limit: int = 10, file_path: str = None) -> ToolResult:
        # Run git log --oneline -n {limit}
        # Optionally filter by file_path
        # Format entries
```

- Parameters: `limit` (int, default 10), `file_path` (optional)
- Returns: Formatted log entries (hash, author, date, message)

#### 4. GitCommitTool (SECURITY CRITICAL)

```python
class GitCommitTool(BaseTool):
    """Creates a commit with message. REQUIRES USER CONFIRMATION."""
    name = "git_commit"
    description = "Create a new commit. Returns confirmation request - agent MUST ask user before executing."

    async def execute(self, message: str, files: List[str] = None) -> ToolResult:
        # DO NOT auto-commit
        # Return a CONFIRMATION REQUEST that agent must present to user
        # Only after user confirms should actual commit happen
```

- Parameters: `message` (str), `files` (list of paths, optional - default all staged)
- **CRITICAL:** MUST return confirmation request, NOT auto-commit
- Agent should relay confirmation to user before actual execution

#### 5. GitBranchTool

```python
class GitBranchTool(BaseTool):
    """List, create, or switch branches."""
    name = "git_branch"
    description = "Manage git branches."

    async def execute(self, action: str = "list", name: str = None) -> ToolResult:
        # action: "list" | "create" | "switch"
        # name: branch name (required for create/switch)
```

- Parameters: `action` (list|create|switch), `name` (optional)
- Returns: Branch list or operation result

## Security Considerations

1. **All git operations MUST run within workspace boundary**
   ```python
   # Validate workspace
   workspace = Path(self.workspace).resolve()
   if not Path(target).resolve().is_relative_to(workspace):
       raise SecurityError("Path outside workspace")
   ```

2. **git_commit MUST require user confirmation**
   - Return result with `requires_confirmation: True`
   - Include proposed changes summary
   - Agent must present to user and wait for approval

3. **Never expose credentials**
   - Sanitize git remote URLs
   - Don't log or return .git/config contents

4. **Validate all file paths**
   - Use `validate_path()` from context.py

## Implementation Pattern

```python
from .base import BaseTool, ToolResult
import subprocess
import shlex
from pathlib import Path
from typing import Optional, List

class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Show the working tree status including modified, staged, and untracked files."

    async def execute(self, **params) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Git error: {result.stderr}"
                )

            # Parse porcelain output
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            modified = []
            staged = []
            untracked = []

            for line in lines:
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]
                if status[0] == '?':
                    untracked.append(filename)
                elif status[0] != ' ':
                    staged.append(filename)
                if status[1] != ' ' and status[1] != '?':
                    modified.append(filename)

            return ToolResult(
                success=True,
                output={
                    "modified": modified,
                    "staged": staged,
                    "untracked": untracked,
                    "clean": len(lines) == 0
                }
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Git command timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

## Registration

### backend/app/services/code_chat/tools/__init__.py

```python
from .git import (
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitCommitTool,
    GitBranchTool,
)

__all__ = [
    # ... existing exports ...
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
    "GitCommitTool",
    "GitBranchTool",
]
```

### backend/app/routers/code_chat.py

Add imports and register with tool registry (follow existing pattern for file_ops tools).

## Acceptance Criteria

- [ ] git_status returns current repo state (modified/staged/untracked)
- [ ] git_diff shows file changes in unified format
- [ ] git_log shows commit history with hash/author/date/message
- [ ] git_commit returns confirmation request (does NOT auto-commit)
- [ ] git_branch lists/creates/switches branches
- [ ] All operations validate workspace boundary
- [ ] Proper error handling for non-git directories
- [ ] Timeout handling for slow operations

## Files

- **CREATE:** `backend/app/services/code_chat/tools/git.py`
- **MODIFY:** `backend/app/services/code_chat/tools/__init__.py`
- **MODIFY:** `backend/app/routers/code_chat.py`

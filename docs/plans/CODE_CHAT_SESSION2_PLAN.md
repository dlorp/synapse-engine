# Code Chat Session 2: Tool Infrastructure & ReAct Agent Core

**Date:** 2025-11-29
**Status:** Ready for Implementation
**Estimated Time:** 6-8 hours
**Session:** 2 of 8-12

---

## Related Documentation

- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Master implementation plan
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Recent development context
- [CLAUDE.md](../../CLAUDE.md) - Project standards and conventions

---

## Executive Summary

Session 2 implements the tool infrastructure and ReAct agent core for Code Chat mode. This builds on Session 1's models and services to create the execution engine that powers the agentic coding assistant.

**Key Deliverables:**
1. **Tool Base Infrastructure** - ToolResult, BaseTool, ToolRegistry classes
2. **File Operations Tools** - read_file, write_file, list_directory, delete_file with security
3. **Search Tools** - search_code (CGRAG), web_search (SearXNG), grep_files
4. **ReAct Agent Engine** - State machine with PLANNING/EXECUTING/OBSERVING loop
5. **Conversation Memory** - Session-based memory management

---

## Session 1 Recap (Dependencies)

The following were implemented in Session 1 and are available for use:

| File | Status | Key Exports |
|------|--------|-------------|
| [backend/app/models/code_chat.py](../../backend/app/models/code_chat.py) | Complete | AgentState, ToolName, ToolCall, ToolResult, ReActStep, CodeChatRequest, CodeChatStreamEvent, PRESETS |
| [backend/app/services/code_chat/__init__.py](../../backend/app/services/code_chat/__init__.py) | Complete | Package exports for workspace and context functions |
| [backend/app/services/code_chat/workspace.py](../../backend/app/services/code_chat/workspace.py) | Complete | validate_path(), list_directories(), detect_project_type(), check_git_repo() |
| [backend/app/services/code_chat/context.py](../../backend/app/services/code_chat/context.py) | Complete | list_cgrag_indexes(), create_cgrag_index(), get_retriever_for_context() |

**Security Patterns Established:**
- Path validation via `validate_path()` in workspace.py
- Allowed workspace roots: `/workspace`, `/projects`, `/home`, `/Users`
- Blocked directories: node_modules, __pycache__, .git, etc.

---

## Task Breakdown

### Task 1: Tool Base Infrastructure
**File:** `backend/app/services/code_chat/tools/base.py`
**Agent:** @backend-architect
**Estimated Time:** 45 minutes
**Priority:** 1 (blocking)

**Description:**
Create base classes for the tool system that all tools inherit from.

**Code Structure:**
```python
"""Base tool infrastructure for Code Chat mode.

Provides:
- BaseTool: Abstract base class for all tools
- ToolRegistry: Central registry for tool discovery and invocation
- Security decorators: Path validation, rate limiting
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import asyncio
import logging
from functools import wraps

from app.models.code_chat import ToolName, ToolResult, ToolCall

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for all Code Chat tools.

    All tools must:
    1. Define a unique name matching ToolName enum
    2. Implement execute() method
    3. Define parameter schema for validation
    4. Handle errors gracefully and return ToolResult

    Attributes:
        name: Tool identifier from ToolName enum
        description: Human-readable description
        parameter_schema: JSON schema for parameters
        requires_confirmation: Whether tool needs user approval
    """

    name: ToolName
    description: str
    parameter_schema: Dict[str, Any]
    requires_confirmation: bool = False

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success/failure and output
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters against schema.

        Args:
            params: Parameters to validate

        Returns:
            Error message if validation fails, None if valid
        """
        # Default implementation - subclasses can override
        required = self.parameter_schema.get("required", [])
        for param in required:
            if param not in params:
                return f"Missing required parameter: {param}"
        return None


class ToolRegistry:
    """Central registry for all Code Chat tools.

    Manages tool registration, discovery, and invocation.
    Provides thread-safe access to tools with logging.

    Usage:
        registry = ToolRegistry()
        registry.register(ReadFileTool(workspace_root="/workspace"))
        result = await registry.execute("read_file", path="src/main.py")
    """

    def __init__(self):
        self._tools: Dict[ToolName, BaseTool] = {}
        self._lock = asyncio.Lock()

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name.value}")

    def get(self, name: ToolName) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata."""
        return [
            {
                "name": tool.name.value,
                "description": tool.description,
                "parameters": tool.parameter_schema,
                "requires_confirmation": tool.requires_confirmation
            }
            for tool in self._tools.values()
        ]

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool from a ToolCall.

        Args:
            tool_call: ToolCall with tool name and arguments

        Returns:
            ToolResult from tool execution
        """
        tool = self.get(tool_call.tool)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_call.tool}"
            )

        # Validate parameters
        error = tool.validate_params(tool_call.args)
        if error:
            return ToolResult(success=False, error=error)

        # Execute with error handling
        try:
            return await tool.execute(**tool_call.args)
        except Exception as e:
            logger.error(f"Tool {tool_call.tool} failed: {e}")
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
```

**Acceptance Criteria:**
- [ ] BaseTool ABC with execute(), validate_params() methods
- [ ] ToolRegistry with register(), get(), list_tools(), execute()
- [ ] Proper error handling returning ToolResult
- [ ] Logging at key points
- [ ] Type hints throughout

---

### Task 2: File Operations Tools
**File:** `backend/app/services/code_chat/tools/file_ops.py`
**Agents:** @backend-architect (implementation), @security-specialist (review)
**Estimated Time:** 90 minutes
**Priority:** 2 (depends on Task 1)

**Description:**
Implement file operation tools with comprehensive security checks.

**Security Requirements (from @security-specialist):**
1. **Path Traversal Prevention:**
   - All paths resolved and validated against workspace root
   - Symlink targets verified within workspace
   - No `..` after resolution

2. **File Size Limits:**
   - Read: Max 10MB per file
   - Write: Max 10MB per file
   - Rate limit: 100 operations/minute

3. **Audit Logging:**
   - Log all file operations with timestamp, path, operation type
   - Log security violations with client context

**Code Structure:**
```python
"""File operation tools for Code Chat mode.

Provides secure file operations within workspace boundary:
- read_file: Read file contents with size limits
- write_file: Create/overwrite files with diff preview
- list_directory: List directory contents
- delete_file: Remove files with confirmation

All operations are sandboxed to the workspace root.
"""

import aiofiles
import logging
from pathlib import Path
from typing import Optional
import difflib

from app.models.code_chat import ToolName, ToolResult, DiffLine, DiffPreview
from app.services.code_chat.tools.base import BaseTool
from app.services.code_chat.workspace import validate_path

logger = logging.getLogger(__name__)

# Limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_READ_LINES = 50000


class ReadFileTool(BaseTool):
    """Read file contents within workspace.

    Parameters:
        path: Relative or absolute path to file
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string, or error if file too large/not found
    """

    name = ToolName.READ_FILE
    description = "Read the contents of a file in the workspace"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "encoding": {"type": "string", "default": "utf-8"}
        },
        "required": ["path"]
    }

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, path: str, encoding: str = "utf-8") -> ToolResult:
        """Read file with security validation."""
        # Validate path
        try:
            full_path = self._validate_and_resolve(path)
        except SecurityError as e:
            logger.warning(f"Security violation in read_file: {e}")
            return ToolResult(success=False, error=str(e))

        # Check file exists
        if not full_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not full_path.is_file():
            return ToolResult(success=False, error=f"Not a file: {path}")

        # Check file size
        size = full_path.stat().st_size
        if size > MAX_FILE_SIZE:
            return ToolResult(
                success=False,
                error=f"File too large: {size} bytes (max {MAX_FILE_SIZE})"
            )

        # Read file
        try:
            async with aiofiles.open(full_path, 'r', encoding=encoding) as f:
                content = await f.read()

            logger.info(f"Read file: {path} ({len(content)} chars)")
            return ToolResult(
                success=True,
                output=content,
                metadata={"path": str(full_path), "size": size}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Read failed: {e}")

    def _validate_and_resolve(self, path: str) -> Path:
        """Validate and resolve path within workspace."""
        # Handle relative paths
        if not Path(path).is_absolute():
            full_path = (self.workspace_root / path).resolve()
        else:
            full_path = Path(path).resolve()

        # Ensure within workspace
        try:
            full_path.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(f"Path escapes workspace: {path}")

        # Check symlinks
        if full_path.is_symlink():
            target = full_path.resolve()
            try:
                target.relative_to(self.workspace_root)
            except ValueError:
                raise SecurityError(f"Symlink escapes workspace: {path}")

        return full_path


class WriteFileTool(BaseTool):
    """Write content to a file in the workspace.

    Parameters:
        path: Target file path
        content: Content to write
        create_dirs: Create parent directories if needed (default: True)

    Returns:
        Success message with diff preview for existing files
    """

    name = ToolName.WRITE_FILE
    description = "Write content to a file (creates parent directories)"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path"},
            "content": {"type": "string", "description": "Content to write"},
            "create_dirs": {"type": "boolean", "default": True}
        },
        "required": ["path", "content"]
    }
    requires_confirmation = False  # Diff preview shown before execution

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(
        self,
        path: str,
        content: str,
        create_dirs: bool = True
    ) -> ToolResult:
        """Write file with diff preview."""
        # Validate path
        try:
            full_path = self._validate_and_resolve(path)
        except SecurityError as e:
            logger.warning(f"Security violation in write_file: {e}")
            return ToolResult(success=False, error=str(e))

        # Check content size
        if len(content.encode('utf-8')) > MAX_FILE_SIZE:
            return ToolResult(
                success=False,
                error=f"Content too large (max {MAX_FILE_SIZE} bytes)"
            )

        # Create diff preview
        original_content = None
        change_type = "create"
        if full_path.exists():
            try:
                async with aiofiles.open(full_path, 'r') as f:
                    original_content = await f.read()
                change_type = "modify"
            except Exception:
                pass

        diff_preview = self._create_diff_preview(
            path, original_content, content, change_type
        )

        # Create parent directories if needed
        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            logger.info(f"Wrote file: {path} ({len(content)} chars)")
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to {path}",
                data={"diff_preview": diff_preview.model_dump()},
                metadata={"path": str(full_path), "change_type": change_type}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Write failed: {e}")

    def _validate_and_resolve(self, path: str) -> Path:
        """Same validation as ReadFileTool."""
        if not Path(path).is_absolute():
            full_path = (self.workspace_root / path).resolve()
        else:
            full_path = Path(path).resolve()

        try:
            full_path.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(f"Path escapes workspace: {path}")

        return full_path

    def _create_diff_preview(
        self,
        path: str,
        original: Optional[str],
        new: str,
        change_type: str
    ) -> DiffPreview:
        """Create unified diff preview."""
        diff_lines = []

        if original:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}"
            )

            line_num = 0
            for line in diff:
                if line.startswith('+') and not line.startswith('+++'):
                    line_num += 1
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="add",
                        content=line[1:].rstrip('\n')
                    ))
                elif line.startswith('-') and not line.startswith('---'):
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="remove",
                        content=line[1:].rstrip('\n')
                    ))
                elif line.startswith(' '):
                    line_num += 1
                    diff_lines.append(DiffLine(
                        line_number=line_num,
                        type="context",
                        content=line[1:].rstrip('\n')
                    ))
        else:
            # New file - all lines are additions
            for i, line in enumerate(new.splitlines(), 1):
                diff_lines.append(DiffLine(
                    line_number=i,
                    type="add",
                    content=line
                ))

        return DiffPreview(
            file_path=path,
            original_content=original,
            new_content=new,
            diff_lines=diff_lines,
            change_type=change_type
        )


class ListDirectoryTool(BaseTool):
    """List contents of a directory in the workspace."""

    name = ToolName.LIST_DIRECTORY
    description = "List files and directories in a path"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."},
            "recursive": {"type": "boolean", "default": False},
            "max_depth": {"type": "integer", "default": 2}
        },
        "required": []
    }

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(
        self,
        path: str = ".",
        recursive: bool = False,
        max_depth: int = 2
    ) -> ToolResult:
        """List directory contents."""
        # Implementation details...
        pass


class DeleteFileTool(BaseTool):
    """Delete a file from the workspace."""

    name = ToolName.DELETE_FILE
    description = "Delete a file (requires confirmation)"
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    }
    requires_confirmation = True

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, path: str) -> ToolResult:
        """Delete file with confirmation."""
        # Implementation details...
        pass


class SecurityError(Exception):
    """Raised when a security check fails."""
    pass
```

**Acceptance Criteria:**
- [ ] ReadFileTool with size limits, encoding support
- [ ] WriteFileTool with diff preview generation
- [ ] ListDirectoryTool with recursive option
- [ ] DeleteFileTool with confirmation requirement
- [ ] All tools validate paths via workspace root
- [ ] SecurityError raised on path traversal attempts
- [ ] Comprehensive logging of all operations

---

### Task 3: Search Tools
**File:** `backend/app/services/code_chat/tools/search.py`
**Agents:** @cgrag-specialist (search_code), @backend-architect (web_search, grep_files)
**Estimated Time:** 60 minutes
**Priority:** 3 (depends on Task 1)

**Description:**
Implement search tools that integrate with existing CGRAG and SearXNG services.

**Integration Points:**
- CGRAG: Use `get_retriever_for_context()` from [context.py](../../backend/app/services/code_chat/context.py)
- SearXNG: Use `SearXNGClient` from [websearch.py](../../backend/app/services/websearch.py)

**Code Structure:**
```python
"""Search tools for Code Chat mode.

Provides:
- search_code: CGRAG-based semantic code search
- web_search: SearXNG-based web search
- grep_files: Regex pattern matching in files

Integrates with existing services for retrieval.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional

from app.models.code_chat import ToolName, ToolResult
from app.services.code_chat.tools.base import BaseTool
from app.services.code_chat.context import get_retriever_for_context
from app.services.websearch import SearXNGClient

logger = logging.getLogger(__name__)


class SearchCodeTool(BaseTool):
    """Semantic code search using CGRAG.

    Parameters:
        query: Search query (natural language)
        context_name: CGRAG index to search (optional, uses default if not specified)
        max_results: Maximum chunks to return (default: 10)
        min_relevance: Minimum relevance score (default: 0.7)

    Returns:
        Relevant code chunks with file paths and relevance scores
    """

    name = ToolName.SEARCH_CODE
    description = "Search the codebase for relevant code using semantic search"
    parameter_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "context_name": {"type": "string", "description": "CGRAG index name"},
            "max_results": {"type": "integer", "default": 10},
            "min_relevance": {"type": "number", "default": 0.7}
        },
        "required": ["query"]
    }

    def __init__(self, default_context: Optional[str] = None):
        """Initialize with optional default context name."""
        self.default_context = default_context

    async def execute(
        self,
        query: str,
        context_name: Optional[str] = None,
        max_results: int = 10,
        min_relevance: float = 0.7
    ) -> ToolResult:
        """Execute semantic code search."""
        context = context_name or self.default_context

        if not context:
            return ToolResult(
                success=False,
                error="No CGRAG context specified. Select a context or provide context_name."
            )

        # Get retriever for the context
        retriever = await get_retriever_for_context(context)
        if not retriever:
            return ToolResult(
                success=False,
                error=f"Context '{context}' not found or not indexed"
            )

        try:
            # Execute retrieval
            result = await retriever.retrieve(
                query=query,
                token_budget=8000,  # Default token budget
                min_relevance=min_relevance
            )

            # Format output
            chunks_output = []
            for artifact in result.artifacts[:max_results]:
                chunks_output.append(
                    f"=== {artifact.file_path} (relevance: {artifact.relevance_score:.2f}) ===\n"
                    f"{artifact.content}\n"
                )

            output = "\n".join(chunks_output) if chunks_output else "No relevant results found."

            logger.info(f"Search '{query}' in {context}: {len(result.artifacts)} results")
            return ToolResult(
                success=True,
                output=output,
                data={
                    "result_count": len(result.artifacts),
                    "tokens_used": result.tokens_used,
                    "top_scores": [a.relevance_score for a in result.artifacts[:5]]
                },
                metadata={"context": context, "query": query}
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ToolResult(success=False, error=f"Search failed: {e}")


class WebSearchTool(BaseTool):
    """Web search using SearXNG metasearch engine.

    Parameters:
        query: Search query
        max_results: Maximum results to return (default: 5)

    Returns:
        Web search results with titles, URLs, and snippets
    """

    name = ToolName.WEB_SEARCH
    description = "Search the web for documentation, tutorials, or solutions"
    parameter_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }

    def __init__(self, searxng_url: str = "http://localhost:8888"):
        """Initialize with SearXNG instance URL."""
        self.client = SearXNGClient(base_url=searxng_url)

    async def execute(
        self,
        query: str,
        max_results: int = 5
    ) -> ToolResult:
        """Execute web search."""
        try:
            response = await self.client.search(query, max_results=max_results)

            # Format output
            results_output = []
            for result in response.results:
                results_output.append(
                    f"**{result.title}**\n"
                    f"URL: {result.url}\n"
                    f"{result.content}\n"
                )

            output = "\n---\n".join(results_output) if results_output else "No results found."

            logger.info(f"Web search '{query}': {len(response.results)} results")
            return ToolResult(
                success=True,
                output=output,
                data={
                    "result_count": len(response.results),
                    "search_time_ms": response.search_time_ms,
                    "engines_used": response.engines_used
                },
                metadata={"query": query}
            )
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(success=False, error=f"Web search failed: {e}")


class GrepFilesTool(BaseTool):
    """Regex pattern search in workspace files.

    Parameters:
        pattern: Regex pattern to search for
        path: Directory to search in (default: workspace root)
        file_pattern: Glob pattern for files (default: *)
        case_sensitive: Case-sensitive search (default: True)
        max_results: Maximum matches to return (default: 100)

    Returns:
        Matching lines with file paths and line numbers
    """

    name = ToolName.GREP_FILES
    description = "Search for regex patterns in files"
    parameter_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "path": {"type": "string", "default": "."},
            "file_pattern": {"type": "string", "default": "*"},
            "case_sensitive": {"type": "boolean", "default": True},
            "max_results": {"type": "integer", "default": 100}
        },
        "required": ["pattern"]
    }

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        case_sensitive: bool = True,
        max_results: int = 100
    ) -> ToolResult:
        """Execute regex search in files."""
        # Implementation with proper path validation
        # Compile regex with case sensitivity
        # Walk directory and search files
        # Return formatted results
        pass
```

**Acceptance Criteria:**
- [ ] SearchCodeTool integrates with existing CGRAGRetriever
- [ ] WebSearchTool integrates with existing SearXNGClient
- [ ] GrepFilesTool with regex pattern matching
- [ ] All tools return formatted, readable output
- [ ] Error handling for missing contexts/services
- [ ] Logging of search operations

---

### Task 4: Conversation Memory
**File:** `backend/app/services/code_chat/memory.py`
**Agent:** @backend-architect
**Estimated Time:** 45 minutes
**Priority:** 4 (can run parallel with Task 3)

**Description:**
Implement conversation memory management for maintaining context across queries.

**Code Structure:**
```python
"""Conversation memory management for Code Chat mode.

Provides:
- ConversationMemory: Per-session memory with turn history
- MemoryManager: Singleton for managing multiple sessions
- Context building for LLM prompts
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import uuid

from app.models.code_chat import ConversationTurn, ProjectInfo

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Maintains conversation context within a Code Chat session.

    Tracks:
    - Recent conversation turns (query + response + tools used)
    - Recently accessed files (for context)
    - Project information (detected from workspace)
    - Workspace and context configuration

    Attributes:
        session_id: Unique session identifier
        max_turns: Maximum turns to keep in memory
        turns: Deque of conversation turns (FIFO)
        file_context: Recently accessed file contents
        project_context: Detected project information
        workspace_path: Current workspace path
        context_name: Current CGRAG context
    """

    def __init__(
        self,
        session_id: str,
        max_turns: int = 20,
        max_file_context: int = 5
    ):
        self.session_id = session_id
        self.max_turns = max_turns
        self.max_file_context = max_file_context

        self.turns: deque[ConversationTurn] = deque(maxlen=max_turns)
        self.file_context: Dict[str, str] = {}  # path -> content preview
        self.project_context: Optional[ProjectInfo] = None
        self.workspace_path: Optional[str] = None
        self.context_name: Optional[str] = None

        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def add_turn(
        self,
        query: str,
        response: str,
        tools_used: List[str]
    ) -> None:
        """Add a conversation turn to memory.

        Args:
            query: User's query
            response: Agent's response
            tools_used: List of tool names used in this turn
        """
        turn = ConversationTurn(
            query=query,
            response=response,
            tools_used=tools_used,
            timestamp=datetime.now()
        )
        self.turns.append(turn)
        self.last_activity = datetime.now()

        logger.debug(f"Session {self.session_id}: Added turn, {len(self.turns)} turns total")

    def add_file_context(self, path: str, content: str, max_preview: int = 500) -> None:
        """Add recently accessed file to context.

        Args:
            path: File path
            content: File content
            max_preview: Maximum characters to store as preview
        """
        # Limit file context size
        if len(self.file_context) >= self.max_file_context:
            # Remove oldest entry
            oldest_key = next(iter(self.file_context))
            del self.file_context[oldest_key]

        self.file_context[path] = content[:max_preview]

    def set_project_context(self, project_info: ProjectInfo) -> None:
        """Set project context from workspace detection."""
        self.project_context = project_info

    def get_context_for_prompt(self, include_file_context: bool = True) -> str:
        """Build context string for LLM prompt.

        Constructs a formatted context including:
        - Workspace information
        - Recent conversation history
        - Project information
        - Recently accessed files (optional)

        Args:
            include_file_context: Whether to include recent file contents

        Returns:
            Formatted context string for LLM prompt
        """
        context_parts = []

        # Workspace info
        if self.workspace_path:
            context_parts.append(f"## Workspace\n{self.workspace_path}")

        # Project context
        if self.project_context:
            context_parts.append(
                f"## Project\n"
                f"Type: {self.project_context.type}\n"
                f"Name: {self.project_context.name or 'Unknown'}\n"
                f"Dependencies: {', '.join(self.project_context.dependencies[:10])}"
            )

        # Recent conversation
        if self.turns:
            context_parts.append("## Recent Conversation")
            for turn in list(self.turns)[-5:]:  # Last 5 turns
                context_parts.append(
                    f"User: {turn.query[:200]}{'...' if len(turn.query) > 200 else ''}\n"
                    f"Assistant: {turn.response[:200]}{'...' if len(turn.response) > 200 else ''}\n"
                    f"Tools: {', '.join(turn.tools_used) if turn.tools_used else 'none'}"
                )

        # File context
        if include_file_context and self.file_context:
            context_parts.append("## Recently Accessed Files")
            for path, preview in self.file_context.items():
                context_parts.append(f"### {path}\n```\n{preview}\n```")

        return "\n\n".join(context_parts)

    def clear(self) -> None:
        """Clear all conversation memory."""
        self.turns.clear()
        self.file_context.clear()
        self.project_context = None
        logger.info(f"Session {self.session_id}: Memory cleared")


class MemoryManager:
    """Singleton manager for conversation memories.

    Manages multiple session memories with cleanup of stale sessions.
    Thread-safe for concurrent access.
    """

    _instance: Optional["MemoryManager"] = None
    _lock = asyncio.Lock()

    def __init__(self, session_timeout_hours: int = 24):
        self._memories: Dict[str, ConversationMemory] = {}
        self.session_timeout_hours = session_timeout_hours

    @classmethod
    async def get_instance(cls) -> "MemoryManager":
        """Get or create singleton instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = MemoryManager()
            return cls._instance

    def get_or_create(
        self,
        session_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
        context_name: Optional[str] = None
    ) -> ConversationMemory:
        """Get existing memory or create new one.

        Args:
            session_id: Session ID (generates new if None)
            workspace_path: Workspace path to set
            context_name: CGRAG context to set

        Returns:
            ConversationMemory instance
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id not in self._memories:
            memory = ConversationMemory(session_id)
            self._memories[session_id] = memory
            logger.info(f"Created new memory for session {session_id}")

        memory = self._memories[session_id]

        # Update configuration if provided
        if workspace_path:
            memory.workspace_path = workspace_path
        if context_name:
            memory.context_name = context_name

        return memory

    def get(self, session_id: str) -> Optional[ConversationMemory]:
        """Get memory by session ID."""
        return self._memories.get(session_id)

    def remove(self, session_id: str) -> bool:
        """Remove a session's memory."""
        if session_id in self._memories:
            del self._memories[session_id]
            logger.info(f"Removed memory for session {session_id}")
            return True
        return False

    async def cleanup_stale_sessions(self) -> int:
        """Remove sessions inactive for longer than timeout.

        Returns:
            Number of sessions removed
        """
        now = datetime.now()
        stale_sessions = []

        for session_id, memory in self._memories.items():
            hours_inactive = (now - memory.last_activity).total_seconds() / 3600
            if hours_inactive > self.session_timeout_hours:
                stale_sessions.append(session_id)

        for session_id in stale_sessions:
            del self._memories[session_id]

        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")

        return len(stale_sessions)
```

**Acceptance Criteria:**
- [ ] ConversationMemory with turn tracking and file context
- [ ] MemoryManager singleton for session management
- [ ] Context building for LLM prompts
- [ ] Session cleanup for stale sessions
- [ ] FIFO queue for turns (max 20)
- [ ] File context limiting (max 5 files)

---

### Task 5: ReAct Agent Core
**File:** `backend/app/services/code_chat/agent.py`
**Agent:** @backend-architect
**Estimated Time:** 120 minutes
**Priority:** 5 (depends on Tasks 1-4)

**Description:**
Implement the ReAct agent state machine that orchestrates the planning-executing-observing loop.

**Code Structure:**
```python
"""ReAct Agent implementation for Code Chat mode.

Implements a state machine that follows the ReAct pattern:
1. PLANNING: LLM generates thought about what to do
2. EXECUTING: Run selected tool
3. OBSERVING: Process tool result
4. Loop until COMPLETED or max iterations

Supports:
- Model tier routing per tool
- Streaming events via SSE
- Cancellation handling
- Comprehensive error recovery
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from app.models.code_chat import (
    AgentState, CodeChatRequest, CodeChatStreamEvent,
    ReActStep, ToolCall, ToolName, PRESETS
)
from app.services.code_chat.tools.base import ToolRegistry
from app.services.code_chat.memory import ConversationMemory, MemoryManager

logger = logging.getLogger(__name__)


class ReActAgent:
    """LangGraph-inspired ReAct agent with state machine.

    Executes queries through a planning-execution-observation loop
    with configurable model tiers per tool via presets.

    Attributes:
        model_selector: Service for selecting LLM instances
        tool_registry: Registry of available tools
        memory_manager: Manager for conversation memories
        searxng_client: Client for web search
    """

    SYSTEM_PROMPT = '''You are an expert coding assistant with access to tools.

Available tools:
{tools_description}

IMPORTANT: Respond in EXACTLY this format:

For taking an action:
Thought: [Your reasoning about what to do next]
Action: tool_name(arg1="value1", arg2="value2")

For providing final answer:
Thought: [Summary of what was done]
Answer: [Complete response to the user]

Rules:
1. Always start with a Thought
2. Use tools to gather information before answering
3. File paths should be relative to the workspace
4. Read files before modifying them
5. When done, provide a clear Answer
'''

    def __init__(
        self,
        model_selector,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager
    ):
        self.model_selector = model_selector
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self._active_sessions: Dict[str, bool] = {}  # session_id -> is_active

    async def run(
        self,
        request: CodeChatRequest
    ) -> AsyncIterator[CodeChatStreamEvent]:
        """Execute ReAct loop with streaming events.

        Args:
            request: Code Chat request with query and configuration

        Yields:
            CodeChatStreamEvent for each step in the loop
        """
        # Get or create session memory
        memory = self.memory_manager.get_or_create(
            session_id=request.session_id,
            workspace_path=request.workspace_path,
            context_name=request.context_name
        )

        # Track active session for cancellation
        session_id = memory.session_id
        self._active_sessions[session_id] = True

        # Get preset configuration
        preset = PRESETS.get(request.preset, PRESETS["balanced"])

        state = AgentState.PLANNING
        steps: List[ReActStep] = []
        tools_used: List[str] = []
        step_number = 0

        try:
            # Initial context retrieval if CGRAG enabled
            if request.use_cgrag and request.context_name:
                yield CodeChatStreamEvent(
                    type="state",
                    state=AgentState.PLANNING,
                    content="Retrieving code context..."
                )
                context = await self._get_cgrag_context(
                    request.query, request.context_name
                )
                if context:
                    yield CodeChatStreamEvent(
                        type="context",
                        content=context
                    )

            # Main ReAct loop
            for iteration in range(request.max_iterations):
                # Check for cancellation
                if not self._active_sessions.get(session_id, False):
                    yield CodeChatStreamEvent(
                        type="cancelled",
                        content="Session cancelled by user"
                    )
                    return

                step_number = iteration + 1

                # PLANNING: Generate thought and action
                state = AgentState.PLANNING
                yield CodeChatStreamEvent(
                    type="state",
                    state=state,
                    tier=preset.planning_tier,
                    step_number=step_number
                )

                # Build prompt with context
                prompt = self._build_prompt(request.query, steps, memory)

                # Call LLM for planning
                response = await self._call_llm(
                    prompt=prompt,
                    tier=preset.planning_tier,
                    temperature=0.7
                )

                # Parse response
                thought, action_or_answer = self._parse_response(response)

                # Emit thought
                yield CodeChatStreamEvent(
                    type="thought",
                    content=thought,
                    tier=preset.planning_tier,
                    step_number=step_number
                )

                # Check if final answer
                if action_or_answer.get("type") == "answer":
                    state = AgentState.COMPLETED
                    yield CodeChatStreamEvent(
                        type="answer",
                        content=action_or_answer["content"],
                        state=state,
                        step_number=step_number
                    )

                    # Save to memory
                    memory.add_turn(
                        query=request.query,
                        response=action_or_answer["content"],
                        tools_used=tools_used
                    )
                    return

                # EXECUTING: Run the tool
                tool_call = action_or_answer.get("tool_call")
                if not tool_call:
                    yield CodeChatStreamEvent(
                        type="error",
                        content="Failed to parse tool call from response"
                    )
                    continue

                state = AgentState.EXECUTING
                yield CodeChatStreamEvent(
                    type="action",
                    tool=tool_call,
                    state=state,
                    step_number=step_number
                )

                # Execute tool
                result = await self.tool_registry.execute(tool_call)
                tools_used.append(tool_call.tool.value)

                # OBSERVING: Process result
                state = AgentState.OBSERVING
                observation = result.output if result.success else f"Error: {result.error}"

                yield CodeChatStreamEvent(
                    type="observation",
                    content=observation,
                    state=state,
                    step_number=step_number
                )

                # Handle confirmation requests
                if result.requires_confirmation:
                    yield CodeChatStreamEvent(
                        type="diff_preview",
                        content=str(result.data),
                        step_number=step_number
                    )

                # Record step
                steps.append(ReActStep(
                    step_number=step_number,
                    thought=thought,
                    action=tool_call,
                    observation=observation,
                    state=state,
                    model_tier=preset.planning_tier,
                    timestamp=datetime.now()
                ))

            # Max iterations reached
            yield CodeChatStreamEvent(
                type="error",
                content=f"Reached maximum iterations ({request.max_iterations})"
            )

        except asyncio.CancelledError:
            yield CodeChatStreamEvent(
                type="cancelled",
                content="Session cancelled"
            )
        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            yield CodeChatStreamEvent(
                type="error",
                content=f"Agent error: {str(e)}"
            )
        finally:
            # Cleanup
            self._active_sessions.pop(session_id, None)

    def cancel(self, session_id: str) -> bool:
        """Cancel an active session.

        Args:
            session_id: Session to cancel

        Returns:
            True if session was active and cancelled
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id] = False
            logger.info(f"Cancelled session {session_id}")
            return True
        return False

    def _build_prompt(
        self,
        query: str,
        steps: List[ReActStep],
        memory: ConversationMemory
    ) -> str:
        """Build the LLM prompt with context and history."""
        # Get tool descriptions
        tools_desc = self._format_tools_description()

        # Format system prompt
        system = self.SYSTEM_PROMPT.format(tools_description=tools_desc)

        # Add conversation context
        context = memory.get_context_for_prompt()

        # Add previous steps
        history = ""
        for step in steps:
            history += f"\nThought: {step.thought}"
            if step.action:
                history += f"\nAction: {step.action.tool.value}({self._format_args(step.action.args)})"
            if step.observation:
                history += f"\nObservation: {step.observation[:500]}"

        # Combine into prompt
        prompt = f"{system}\n\n{context}\n\nQuery: {query}{history}\n"

        return prompt

    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response into thought and action/answer.

        Returns:
            (thought, {"type": "answer"|"action", ...})
        """
        thought = ""
        result = {}

        # Extract thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Answer:|$)', response, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Check for answer
        answer_match = re.search(r'Answer:\s*(.+?)$', response, re.DOTALL)
        if answer_match:
            return thought, {"type": "answer", "content": answer_match.group(1).strip()}

        # Check for action
        action_match = re.search(r'Action:\s*(\w+)\((.*?)\)', response, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1)
            args_str = action_match.group(2)

            # Parse arguments
            args = self._parse_args(args_str)

            try:
                tool_call = ToolCall(
                    tool=ToolName(tool_name),
                    args=args
                )
                return thought, {"type": "action", "tool_call": tool_call}
            except ValueError:
                return thought, {"type": "error", "message": f"Unknown tool: {tool_name}"}

        return thought, {"type": "error", "message": "Could not parse response"}

    def _parse_args(self, args_str: str) -> Dict:
        """Parse argument string into dictionary."""
        args = {}
        # Match key="value" or key='value' patterns
        pattern = r'(\w+)\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(pattern, args_str):
            args[match.group(1)] = match.group(2)
        return args

    def _format_args(self, args: Dict) -> str:
        """Format arguments dictionary as string."""
        return ", ".join(f'{k}="{v}"' for k, v in args.items())

    def _format_tools_description(self) -> str:
        """Format tool descriptions for system prompt."""
        tools = self.tool_registry.list_tools()
        lines = []
        for tool in tools:
            params = ", ".join(
                f"{k}: {v.get('type', 'any')}"
                for k, v in tool["parameters"].get("properties", {}).items()
            )
            lines.append(f"- {tool['name']}({params}): {tool['description']}")
        return "\n".join(lines)

    async def _call_llm(self, prompt: str, tier: str, temperature: float) -> str:
        """Call LLM with specified tier."""
        # Use model_selector to route to appropriate model
        model = await self.model_selector.select_model(tier)
        response = await model.generate(prompt, temperature=temperature)
        return response

    async def _get_cgrag_context(self, query: str, context_name: str) -> Optional[str]:
        """Retrieve CGRAG context for query."""
        from app.services.code_chat.context import get_retriever_for_context

        retriever = await get_retriever_for_context(context_name)
        if not retriever:
            return None

        result = await retriever.retrieve(query=query, token_budget=4000)
        if result.artifacts:
            return "\n\n".join(
                f"=== {a.file_path} ===\n{a.content}"
                for a in result.artifacts[:5]
            )
        return None
```

**Acceptance Criteria:**
- [ ] State machine with PLANNING -> EXECUTING -> OBSERVING loop
- [ ] SSE streaming via AsyncIterator[CodeChatStreamEvent]
- [ ] Response parsing for Thought/Action/Answer format
- [ ] Tool execution via ToolRegistry
- [ ] Memory integration for context building
- [ ] Cancellation support
- [ ] Error handling and recovery
- [ ] Max iterations limit

---

## Implementation Order

The tasks must be implemented in this order due to dependencies:

```
Task 1: base.py (Tool Base Infrastructure)
    |
    +---> Task 2: file_ops.py (File Operations)
    |         |
    |         +---> [Security Review by @security-specialist]
    |
    +---> Task 3: search.py (Search Tools) [can parallel with Task 4]
    |
    +---> Task 4: memory.py (Conversation Memory) [can parallel with Task 3]
              |
              +---> Task 5: agent.py (ReAct Agent Core)
```

---

## Agent Assignments Summary

| Task | Primary Agent | Supporting Agent | Est. Time |
|------|---------------|------------------|-----------|
| Task 1: Tool Base Infrastructure | @backend-architect | - | 45 min |
| Task 2: File Operations | @backend-architect | @security-specialist | 90 min |
| Task 3: Search Tools | @cgrag-specialist | @backend-architect | 60 min |
| Task 4: Conversation Memory | @backend-architect | - | 45 min |
| Task 5: ReAct Agent Core | @backend-architect | - | 120 min |

**Total Estimated Time:** 6 hours (360 min)

---

## Security Review Checklist (for @security-specialist)

After Task 2 is implemented, @security-specialist should review:

- [ ] Path traversal prevention via resolve() and relative_to()
- [ ] Symlink target validation
- [ ] File size limits enforced (10MB)
- [ ] No shell command injection vectors
- [ ] Audit logging of all file operations
- [ ] SecurityError raised on violations
- [ ] No path information leakage in error messages

---

## Integration Points

### Existing Services to Use

| Service | File | Usage |
|---------|------|-------|
| CGRAGRetriever | [backend/app/services/cgrag.py](../../backend/app/services/cgrag.py) | search_code tool |
| SearXNGClient | [backend/app/services/websearch.py](../../backend/app/services/websearch.py) | web_search tool |
| validate_path | [backend/app/services/code_chat/workspace.py](../../backend/app/services/code_chat/workspace.py) | File operation security |
| get_retriever_for_context | [backend/app/services/code_chat/context.py](../../backend/app/services/code_chat/context.py) | CGRAG integration |
| EventBus | [backend/app/services/event_bus.py](../../backend/app/services/event_bus.py) | Progress events |

### Models from Session 1

All models are defined in [backend/app/models/code_chat.py](../../backend/app/models/code_chat.py):
- AgentState, ToolName - Enums
- ToolCall, ToolResult, ReActStep - Execution models
- CodeChatRequest, CodeChatStreamEvent - API models
- PRESETS - Built-in model configurations

---

## Testing Checklist

After implementation, verify:

**Tool Base (Task 1):**
- [ ] BaseTool subclass can be created
- [ ] ToolRegistry registers and retrieves tools
- [ ] execute() handles errors gracefully

**File Operations (Task 2):**
- [ ] read_file reads files within workspace
- [ ] read_file rejects paths outside workspace
- [ ] read_file enforces size limits
- [ ] write_file creates new files with directories
- [ ] write_file generates correct diff preview
- [ ] delete_file requires confirmation

**Search Tools (Task 3):**
- [ ] search_code returns relevant chunks
- [ ] search_code handles missing context gracefully
- [ ] web_search returns formatted results
- [ ] grep_files matches patterns correctly

**Memory (Task 4):**
- [ ] ConversationMemory tracks turns
- [ ] MemoryManager creates/retrieves sessions
- [ ] get_context_for_prompt formats correctly
- [ ] Stale session cleanup works

**ReAct Agent (Task 5):**
- [ ] State machine progresses correctly
- [ ] Events stream in order
- [ ] Tool calls are parsed correctly
- [ ] Final answer terminates loop
- [ ] Cancellation stops execution

---

## Files to Create

| File | Lines (Est.) | Description |
|------|--------------|-------------|
| `backend/app/services/code_chat/tools/__init__.py` | 20 | Package exports |
| `backend/app/services/code_chat/tools/base.py` | 150 | Base tool classes |
| `backend/app/services/code_chat/tools/file_ops.py` | 350 | File operation tools |
| `backend/app/services/code_chat/tools/search.py` | 250 | Search tools |
| `backend/app/services/code_chat/memory.py` | 200 | Conversation memory |
| `backend/app/services/code_chat/agent.py` | 400 | ReAct agent core |

**Total:** ~1,370 lines

---

## Next Session Preview (Session 3)

Session 3 will implement:
1. API Router - FastAPI endpoints for /api/code-chat/*
2. SSE Streaming - Server-Sent Events for real-time updates
3. Session management - Cancel, list, cleanup endpoints
4. Frontend hooks - useCodeChat, useWorkspaces, useContexts

---

## Commands for Implementation

Each agent should run these commands before starting:

```bash
# Verify Session 1 files exist
ls -la ${PROJECT_DIR}/backend/app/models/code_chat.py
ls -la ${PROJECT_DIR}/backend/app/services/code_chat/

# Create tools directory
mkdir -p ${PROJECT_DIR}/backend/app/services/code_chat/tools

# Verify syntax after each file
python -m py_compile ${PROJECT_DIR}/backend/app/services/code_chat/tools/base.py
```

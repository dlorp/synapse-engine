# Code Chat Mode - Execution Plan

**Date:** 2025-11-29
**Status:** Ready for Execution
**Reference:** [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md)

---

## Executive Summary

This document provides the execution strategy for implementing Code Chat Mode. The implementation follows a **Foundation-First** approach, building core data structures before services, and services before UI components.

**Total Estimated Time:** 40-60 hours (8-12 development sessions)
**Session 1 Target:** Backend Foundation (Phase 1.1 + 1.2) - 4-6 hours

---

## Session 1: Backend Foundation

**Goal:** Establish all Pydantic models and workspace/context management services that define the data structures for the entire Code Chat feature.

**Rationale:** Backend models define the contracts between all components. Starting here ensures:
1. Frontend types can be generated from backend schemas
2. API contracts are established before endpoint implementation
3. Tool interfaces are well-defined before ReAct agent development

### Task Breakdown

#### Task 1.1: Backend Models (`backend/app/models/code_chat.py`)
**Agent:** `@backend-architect`
**Priority:** CRITICAL - All other tasks depend on this
**Estimated Time:** 2-3 hours
**Dependencies:** None

**Deliverables:**
```
backend/app/models/code_chat.py (NEW - ~400 lines)
```

**Required Components:**

1. **Enums:**
   ```python
   class AgentState(str, Enum):
       IDLE = "idle"
       PLANNING = "planning"
       EXECUTING = "executing"
       OBSERVING = "observing"
       COMPLETED = "completed"
       ERROR = "error"
       CANCELLED = "cancelled"

   class ToolName(str, Enum):
       # File Operations
       READ_FILE = "read_file"
       WRITE_FILE = "write_file"
       LIST_DIRECTORY = "list_directory"
       DELETE_FILE = "delete_file"
       # Search
       SEARCH_CODE = "search_code"
       WEB_SEARCH = "web_search"
       GREP_FILES = "grep_files"
       # Execution
       RUN_PYTHON = "run_python"
       RUN_SHELL = "run_shell"
       # Git (MCP)
       GIT_STATUS = "git_status"
       GIT_DIFF = "git_diff"
       GIT_LOG = "git_log"
       GIT_COMMIT = "git_commit"
       GIT_BRANCH = "git_branch"
       # LSP (MCP)
       GET_DIAGNOSTICS = "get_diagnostics"
       GET_DEFINITIONS = "get_definitions"
       GET_REFERENCES = "get_references"
       # Project
       GET_PROJECT_INFO = "get_project_info"
   ```

2. **Configuration Models:**
   ```python
   class ToolModelConfig(BaseModel):
       tier: Literal["fast", "balanced", "powerful"]
       temperature: float = 0.7
       max_tokens: int = 2048

   class ModelPreset(BaseModel):
       name: str
       description: str
       planning_tier: Literal["fast", "balanced", "powerful"]
       tool_configs: Dict[ToolName, ToolModelConfig]
   ```

3. **Request/Response Models:**
   ```python
   class CodeChatRequest(BaseModel):
       query: str
       session_id: Optional[str] = None
       workspace_path: str
       context_name: Optional[str] = None
       use_cgrag: bool = True
       use_web_search: bool = True
       max_iterations: int = 15
       preset: str = "balanced"
       tool_overrides: Optional[Dict[str, ToolModelConfig]] = None

   class ToolCall(BaseModel):
       tool: ToolName
       args: Dict[str, Any]

   class ToolResult(BaseModel):
       success: bool
       output: str
       error: Optional[str] = None
       metadata: Dict[str, Any] = Field(default_factory=dict)
       requires_confirmation: bool = False
       confirmation_type: Optional[str] = None
       data: Optional[Dict[str, Any]] = None

   class ReActStep(BaseModel):
       step_number: int
       thought: str
       action: Optional[ToolCall] = None
       observation: Optional[str] = None
       state: AgentState
       model_tier: str
       timestamp: datetime

   class CodeChatStreamEvent(BaseModel):
       type: Literal["state", "thought", "action", "observation",
                     "answer", "error", "cancelled", "context", "diff_preview"]
       content: Optional[str] = None
       state: Optional[AgentState] = None
       tier: Optional[str] = None
       tool: Optional[ToolCall] = None
       diff: Optional["DiffPreview"] = None
   ```

4. **Workspace/Context Models:**
   ```python
   class DirectoryInfo(BaseModel):
       name: str
       path: str
       is_directory: bool
       is_git_repo: bool
       project_type: Optional[str] = None

   class WorkspaceListResponse(BaseModel):
       current_path: str
       directories: List[DirectoryInfo]
       parent_path: Optional[str]
       is_git_repo: bool
       project_type: Optional[str]

   class WorkspaceValidation(BaseModel):
       valid: bool
       is_git_repo: bool
       project_info: Optional["ProjectInfo"] = None
       file_count: int
       has_cgrag_index: bool

   class ProjectInfo(BaseModel):
       type: str  # python, node, rust, go
       name: Optional[str]
       version: Optional[str]
       dependencies: List[str]
       dev_dependencies: List[str] = Field(default_factory=list)
       scripts: Dict[str, str] = Field(default_factory=dict)
       entry_points: List[str] = Field(default_factory=list)

   class ContextInfo(BaseModel):
       name: str
       path: str
       chunk_count: int
       last_indexed: datetime
       source_path: str
       embedding_model: str

   class CreateContextRequest(BaseModel):
       name: str
       source_path: str
       embedding_model: str = "all-MiniLM-L6-v2"
   ```

5. **Diff Preview Models:**
   ```python
   class DiffLine(BaseModel):
       line_number: int
       type: Literal["add", "remove", "context"]
       content: str

   class DiffPreview(BaseModel):
       file_path: str
       original_content: Optional[str]
       new_content: str
       diff_lines: List[DiffLine]
       change_type: Literal["create", "modify", "delete"]
   ```

6. **Conversation Memory Models:**
   ```python
   class ConversationTurn(BaseModel):
       query: str
       response: str
       tools_used: List[str]
       timestamp: datetime
   ```

7. **Built-in Presets Dictionary:**
   ```python
   PRESETS: Dict[str, ModelPreset] = {
       "speed": ModelPreset(...),
       "balanced": ModelPreset(...),
       "quality": ModelPreset(...),
       "coding": ModelPreset(...),
       "research": ModelPreset(...),
   }
   ```

**Acceptance Criteria:**
- [ ] All models have proper type hints and Field definitions
- [ ] All models follow existing patterns (see [events.py](../../backend/app/models/events.py))
- [ ] Models use `model_config = ConfigDict(populate_by_name=True)` for camelCase aliases
- [ ] All enums extend `str, Enum` for JSON serialization
- [ ] All models have docstrings with examples
- [ ] File passes `python -m py_compile backend/app/models/code_chat.py`

---

#### Task 1.2: Workspace Service (`backend/app/services/code_chat/workspace.py`)
**Agent:** `@backend-architect`
**Priority:** HIGH - Required for workspace selection UI
**Estimated Time:** 1.5-2 hours
**Dependencies:** Task 1.1 (models)

**Deliverables:**
```
backend/app/services/code_chat/__init__.py (NEW)
backend/app/services/code_chat/workspace.py (NEW - ~200 lines)
```

**Required Functions:**

```python
# workspace.py
from pathlib import Path
from typing import List, Optional
from app.models.code_chat import (
    DirectoryInfo, WorkspaceListResponse, WorkspaceValidation, ProjectInfo
)

# Security: Define allowed root paths (configurable via env)
ALLOWED_WORKSPACE_ROOTS = ["/workspace", "/projects", "/home"]

def validate_path_security(path: str) -> bool:
    """Validate path is within allowed roots and no traversal attacks."""
    ...

def list_directories(path: str) -> List[DirectoryInfo]:
    """List directories at given path with metadata."""
    ...

def get_parent_path(path: str) -> Optional[str]:
    """Get parent directory path, respecting allowed roots."""
    ...

def check_git_repo(path: str) -> bool:
    """Check if path is a git repository."""
    ...

def detect_project_type(path: str) -> Optional[str]:
    """Detect project type from config files."""
    ...

def detect_project_info(path: str) -> Optional[ProjectInfo]:
    """Extract detailed project info from config files."""
    ...

def is_valid_workspace(path: str) -> bool:
    """Validate workspace path exists and is accessible."""
    ...

def count_files(path: str, max_depth: int = 5) -> int:
    """Count files in workspace (limited depth for performance)."""
    ...

async def list_workspaces(path: str = "/") -> WorkspaceListResponse:
    """Main function for GET /api/code-chat/workspaces endpoint."""
    ...

async def validate_workspace(path: str) -> WorkspaceValidation:
    """Main function for POST /api/code-chat/workspaces/validate endpoint."""
    ...
```

**Project Detection Logic:**
```python
def detect_project_type(path: str) -> Optional[str]:
    workspace = Path(path)
    if (workspace / "pyproject.toml").exists():
        return "python"
    if (workspace / "requirements.txt").exists():
        return "python"
    if (workspace / "setup.py").exists():
        return "python"
    if (workspace / "package.json").exists():
        return "node"
    if (workspace / "Cargo.toml").exists():
        return "rust"
    if (workspace / "go.mod").exists():
        return "go"
    if (workspace / "pom.xml").exists():
        return "java"
    if (workspace / "build.gradle").exists():
        return "java"
    return None
```

**Acceptance Criteria:**
- [ ] Path validation prevents directory traversal attacks
- [ ] Allowed workspace roots are configurable via environment variable
- [ ] Project type detection works for Python, Node, Rust, Go, Java
- [ ] Git repository detection is accurate
- [ ] File counting is limited to prevent hangs on large directories
- [ ] All functions have proper error handling
- [ ] File passes syntax check

---

#### Task 1.3: Context Management (`backend/app/services/code_chat/context.py`)
**Agent:** `@cgrag-specialist`
**Priority:** HIGH - Required for CGRAG index selection
**Estimated Time:** 1-1.5 hours
**Dependencies:** Task 1.1 (models), existing CGRAG service

**Deliverables:**
```
backend/app/services/code_chat/context.py (NEW - ~150 lines)
```

**Required Functions:**

```python
# context.py
from typing import List, Optional
from pathlib import Path
from app.models.code_chat import ContextInfo, CreateContextRequest

# CGRAG index storage location
CGRAG_INDEX_DIR = Path("/app/data/faiss_indexes")

def list_cgrag_indexes() -> List[ContextInfo]:
    """List all available CGRAG indexes with metadata."""
    ...

def check_cgrag_index_exists(workspace_path: str) -> bool:
    """Check if a CGRAG index exists for a workspace."""
    ...

def get_context_info(name: str) -> Optional[ContextInfo]:
    """Get info about a specific CGRAG context."""
    ...

async def create_cgrag_index(
    name: str,
    source_path: str,
    embedding_model: str = "all-MiniLM-L6-v2"
) -> ContextInfo:
    """Create a new CGRAG index from source directory.

    Integrates with existing cgrag.py service.
    """
    ...

async def refresh_cgrag_index(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context."""
    ...

async def delete_cgrag_index(name: str) -> bool:
    """Delete a CGRAG index (admin operation)."""
    ...
```

**Integration with Existing CGRAG:**
- Must integrate with existing `backend/app/services/cgrag.py`
- Use existing `CGRAGRetriever` class for retrieval operations
- Index metadata should be stored in JSON alongside FAISS index

**Acceptance Criteria:**
- [ ] Correctly integrates with existing CGRAG service
- [ ] Index metadata persisted to disk (JSON file)
- [ ] Index creation is async and doesn't block
- [ ] Proper error handling for missing indexes
- [ ] File passes syntax check

---

### Session 1 Parallel Work Opportunities

**Parallelizable after Task 1.1 completes:**

```
Task 1.1 (Models) - MUST complete first
    |
    +-----> Task 1.2 (Workspace Service) - @backend-architect
    |
    +-----> Task 1.3 (Context Management) - @cgrag-specialist
```

**Recommended Workflow:**
1. Start with Task 1.1 (Models) - single developer focus
2. Once models are complete, split into parallel tracks:
   - @backend-architect continues with Task 1.2 (Workspace)
   - @cgrag-specialist starts Task 1.3 (Context)
3. Both parallel tasks can be reviewed and merged independently

---

## Session 2: Backend Tools and ReAct Agent (Future)

**Goal:** Implement tool infrastructure and ReAct agent core

### Planned Tasks

#### Task 2.1: Base Tool Classes
**Agent:** `@backend-architect`
**Files:**
```
backend/app/services/code_chat/tools/__init__.py
backend/app/services/code_chat/tools/base.py
```

#### Task 2.2: File Operations Tools
**Agent:** `@backend-architect` + `@security-specialist`
**Files:**
```
backend/app/services/code_chat/tools/file_ops.py
```

#### Task 2.3: Search Tools
**Agent:** `@backend-architect` + `@cgrag-specialist`
**Files:**
```
backend/app/services/code_chat/tools/search.py
```

#### Task 2.4: ReAct Agent Core
**Agent:** `@backend-architect`
**Files:**
```
backend/app/services/code_chat/agent.py
backend/app/services/code_chat/memory.py
backend/app/services/code_chat/presets.py
```

---

## Session 3: Python Sandbox (Future)

**Goal:** Create isolated Python execution environment

### Planned Tasks

#### Task 3.1: Sandbox Dockerfile
**Agent:** `@devops-engineer` + `@security-specialist`
**Files:**
```
sandbox/Dockerfile
sandbox/server.py
```

#### Task 3.2: Docker Compose Integration
**Agent:** `@devops-engineer`
**Files:**
```
docker-compose.yml (modify - add synapse_sandbox service)
```

---

## Session 4: API Router (Future)

**Goal:** Expose Code Chat functionality via REST API

### Planned Tasks

#### Task 4.1: Code Chat Router
**Agent:** `@backend-architect` + `@websocket-realtime-specialist`
**Files:**
```
backend/app/routers/code_chat.py
```

---

## Session 5-6: Frontend Implementation (Future)

**Goal:** Build Code Chat UI with terminal aesthetics

### Planned Tasks

#### Task 5.1: TypeScript Types
**Agent:** `@frontend-engineer`
**Files:**
```
frontend/src/types/codeChat.ts
```

#### Task 5.2: React Hooks
**Agent:** `@frontend-engineer`
**Files:**
```
frontend/src/hooks/useCodeChat.ts
frontend/src/hooks/useWorkspaces.ts
frontend/src/hooks/useContexts.ts
frontend/src/hooks/usePresets.ts
```

#### Task 5.3: Selector Components
**Agent:** `@frontend-engineer` + `@terminal-ui-specialist`
**Files:**
```
frontend/src/pages/CodeChatPage/WorkspaceSelector.tsx
frontend/src/pages/CodeChatPage/ContextSelector.tsx
frontend/src/pages/CodeChatPage/PresetSelector.tsx
frontend/src/pages/CodeChatPage/DiffPreview.tsx
```

#### Task 5.4: Main Page Component
**Agent:** `@frontend-engineer` + `@terminal-ui-specialist`
**Files:**
```
frontend/src/pages/CodeChatPage/CodeChatPage.tsx
frontend/src/pages/CodeChatPage/CodeChatPage.module.css
frontend/src/pages/CodeChatPage/index.ts
```

---

## Session 7: MCP Tools (Future)

**Goal:** Implement Git and LSP tools

### Planned Tasks

#### Task 7.1: Git Tools
**Agent:** `@backend-architect`
**Files:**
```
backend/app/services/code_chat/tools/git.py
```

#### Task 7.2: LSP Tools
**Agent:** `@backend-architect`
**Files:**
```
backend/app/services/code_chat/tools/lsp.py
```

---

## Session 8: Integration and Testing (Future)

**Goal:** Wire everything together and test

### Planned Tasks

#### Task 8.1: Main.py Integration
**Agent:** `@backend-architect`
**Files:**
```
backend/app/main.py (modify)
backend/app/models/events.py (modify - add CODE_CHAT event types)
```

#### Task 8.2: Route Integration
**Agent:** `@frontend-engineer`
**Files:**
```
frontend/src/router/routes.tsx (modify)
frontend/src/components/modes/ModeSelector.tsx (modify)
```

#### Task 8.3: Testing
**Agent:** `@testing-specialist`
**Tests:**
- Unit tests for all tools
- Integration tests for ReAct loop
- E2E tests for full workflow

---

## Agent Assignments Summary

| Agent | Session 1 Tasks | Estimated Hours |
|-------|-----------------|-----------------|
| @backend-architect | 1.1 Models, 1.2 Workspace | 3.5-5 hours |
| @cgrag-specialist | 1.3 Context Management | 1-1.5 hours |

### Agent Invocation Order for Session 1

1. **First:** Invoke `@backend-architect` with Task 1.1 (Models)
   - This is the critical path - all other work depends on it
   - Estimated completion: 2-3 hours

2. **After Task 1.1 completes:** Invoke in parallel:
   - `@backend-architect` with Task 1.2 (Workspace)
   - `@cgrag-specialist` with Task 1.3 (Context)

3. **End of Session:** Review and merge all PRs

---

## Success Criteria for Session 1

### Must Complete
- [x] `backend/app/models/code_chat.py` - All models defined ✅ (972 lines)
- [x] `backend/app/services/code_chat/__init__.py` - Package initialized ✅ (52 lines)
- [x] `backend/app/services/code_chat/workspace.py` - Workspace functions ✅ (556 lines)
- [x] `backend/app/services/code_chat/context.py` - Context functions ✅ (534 lines)

### Quality Gates
- [x] All Python files pass `python -m py_compile` ✅
- [x] All models have docstrings with examples ✅
- [x] Path security validation implemented ✅
- [x] Integration with existing CGRAG verified ✅

### Session 1 Deliverables Checklist
```
backend/app/models/code_chat.py           [✅] 972 lines (exceeded estimate)
backend/app/services/code_chat/__init__.py [✅] 52 lines
backend/app/services/code_chat/workspace.py [✅] 556 lines (exceeded estimate)
backend/app/services/code_chat/context.py   [✅] 534 lines (exceeded estimate)
```

**Total new code for Session 1:** 2,114 lines (nearly 3x estimate - comprehensive implementation)

---

## Risk Assessment

### High Risk Items
1. **CGRAG Integration** - May require understanding existing cgrag.py internals
   - Mitigation: Assign @cgrag-specialist who knows the codebase

2. **Path Security** - Directory traversal vulnerabilities
   - Mitigation: @security-specialist review before merge

3. **Model Complexity** - Many interconnected models
   - Mitigation: Thorough review, follow existing patterns

### Medium Risk Items
1. **Project Detection** - May not cover all project types
   - Mitigation: Start with common types, extensible design

2. **Index Metadata** - New persistence requirement
   - Mitigation: Simple JSON storage initially

---

## Related Documentation

- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Full implementation plan
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history
- [events.py](../../backend/app/models/events.py) - Model patterns to follow
- [query.py](../../backend/app/models/query.py) - Request/response patterns
- [cgrag.py](../../backend/app/services/cgrag.py) - Existing CGRAG service
- [backend-architect.md](../../.claude/agents/backend-architect.md) - Agent capabilities
- [cgrag-specialist.md](../../.claude/agents/cgrag-specialist.md) - Agent capabilities

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-29 | 1.0 | Initial execution plan created |

# S.Y.N.A.P.S.E. ENGINE - Code Chat Mode Implementation Plan

**Date:** 2025-11-29
**Status:** Ready for Implementation
**Estimated Time:** 40-60 hours (8-12 development sessions)

---

## Executive Summary

Add a "Code Chat" mode - an agentic coding assistant with a custom ReAct loop inspired by LangGraph patterns. The agent will use powerful models (Q4) for planning, and appropriate tiers for execution, with full file access and sandboxed Python execution.

### Key Features
- **Custom ReAct Loop** - State machine with explicit states (PLANNING, EXECUTING, OBSERVING, COMPLETED, ERROR)
- **Configurable Models per Tool** - Each tool can use a different model tier with preset support
- **Workspace Selection** - User selects working directory through TUI file browser
- **Context Selection** - User selects which CGRAG index/project context to use
- **Full File Access** - Read, write, create, delete in selected workspace
- **Sandboxed Python** - Isolated container for code execution
- **Web Search** - Existing SearXNG integration
- **CGRAG** - Existing code context retrieval (selectable index)
- **Real-time Streaming** - SSE events for each ReAct step
- **MCP Tools** - Git operations, LSP diagnostics, shell commands
- **Conversation Memory** - Maintain context across multiple queries in a session
- **Diff Preview** - Show file diffs before applying changes
- **Project Context** - Auto-detect project type (package.json, requirements.txt, etc.)

---

## Architecture Overview

```
+---------------------------------------------------------------------+
|                    CODE CHAT MODE                                    |
+---------------------------------------------------------------------+
|  React Frontend                                                      |
|  +-- CodeChatPage (terminal-style UI)                               |
|  +-- WorkspaceSelector (folder browser for workspace selection)     |
|  +-- ContextSelector (CGRAG index / project context selection)      |
|  +-- useCodeChat hook (SSE streaming)                               |
|  +-- ReAct step visualization                                       |
+---------------------------------------------------------------------+
|  FastAPI Backend (synapse_core)                                     |
|  +-- GET /api/code-chat/workspaces (list available directories)     |
|  +-- GET /api/code-chat/contexts (list CGRAG indexes)               |
|  +-- POST /api/code-chat/query (SSE streaming)                      |
|  +-- ReActAgent (state machine)                                     |
|  |   +-- State: PLANNING -> EXECUTING -> OBSERVING -> loop          |
|  |   +-- Model routing: Q4 planning, Q3 tools, Q2 quick             |
|  |   +-- Tools: file ops, CGRAG, web search, Python                 |
|  +-- Integrates with existing services                              |
+---------------------------------------------------------------------+
|  Python Sandbox (synapse_sandbox)                                   |
|  +-- Isolated container (512MB RAM, 30s timeout)                    |
|  +-- Restricted imports (no os, subprocess, socket)                 |
|  +-- Non-root user, read-only filesystem                            |
+---------------------------------------------------------------------+
|  Existing Infrastructure                                            |
|  +-- llama.cpp servers (Q2/Q3/Q4)                                   |
|  +-- CGRAG (code context retrieval - multiple indexes)              |
|  +-- SearXNG (web search)                                           |
|  +-- Configurable workspace volumes                                 |
+---------------------------------------------------------------------+
```

---

## Workspace & Context Selection

### Workspace Selection (TUI File Browser)

Users can select which folder to use as the workspace through a terminal-style file browser:

```
+---------------------------------------------+
| WORKSPACE SELECTION                         |
+---------------------------------------------+
| Current: /projects/my-app                   |
|                                             |
| +-- /                                       |
|   +-- projects/                             |
|     +-- my-app/          <-- [SELECTED]     |
|     +-- another-project/                    |
|     +-- experiments/                        |
|   +-- documents/                            |
|   +-- downloads/                            |
|                                             |
| [SELECT] [REFRESH] [NEW FOLDER]             |
+---------------------------------------------+
```

**Backend API:**

```python
@router.get("/workspaces")
async def list_workspaces(path: str = "/") -> WorkspaceListResponse:
    """List directories available for workspace selection."""
    return WorkspaceListResponse(
        current_path=path,
        directories=list_directories(path),
        parent_path=get_parent_path(path),
        is_git_repo=check_git_repo(path),
        project_type=detect_project_type(path)
    )

@router.post("/workspaces/validate")
async def validate_workspace(path: str) -> WorkspaceValidation:
    """Validate a workspace path and return metadata."""
    return WorkspaceValidation(
        valid=is_valid_workspace(path),
        is_git_repo=check_git_repo(path),
        project_info=detect_project_info(path),
        file_count=count_files(path),
        has_cgrag_index=check_cgrag_index_exists(path)
    )
```

**Frontend Component:**

```typescript
interface WorkspaceInfo {
  path: string;
  name: string;
  isGitRepo: boolean;
  projectType: string | null;  // 'python', 'node', 'rust', etc.
  fileCount: number;
  hasCgragIndex: boolean;
}

export const WorkspaceSelector: React.FC<{
  currentWorkspace: string;
  onSelect: (path: string) => void;
}> = ({ currentWorkspace, onSelect }) => {
  const [browsePath, setBrowsePath] = useState('/');
  const { data: directories } = useWorkspaces(browsePath);

  return (
    <AsciiPanel title="WORKSPACE SELECTION">
      <div className={styles.currentPath}>
        Current: {currentWorkspace || 'None selected'}
      </div>
      <div className={styles.directoryTree}>
        {directories?.map(dir => (
          <DirectoryItem
            key={dir.path}
            directory={dir}
            onNavigate={setBrowsePath}
            onSelect={onSelect}
          />
        ))}
      </div>
      <div className={styles.actions}>
        <Button onClick={() => onSelect(browsePath)}>SELECT</Button>
        <Button onClick={() => setBrowsePath('/')}>HOME</Button>
      </div>
    </AsciiPanel>
  );
};
```

### Context Selection (CGRAG Index Selector)

Users can select which CGRAG index to use for code context retrieval:

```
+---------------------------------------------+
| CONTEXT SELECTION                           |
+---------------------------------------------+
| Available Indexes:                          |
|                                             |
| (*) synapse-engine     [42,156 chunks]      |
|     Indexed: 2025-11-29 10:30               |
|                                             |
| ( ) my-app             [8,234 chunks]       |
|     Indexed: 2025-11-28 15:00               |
|                                             |
| ( ) documentation      [3,891 chunks]       |
|     Indexed: 2025-11-27 09:15               |
|                                             |
| ( ) None (no context)                       |
|                                             |
| [CREATE NEW INDEX] [REFRESH INDEX]          |
+---------------------------------------------+
```

**Backend API:**

```python
@router.get("/contexts")
async def list_contexts() -> List[ContextInfo]:
    """List available CGRAG indexes for context selection."""
    indexes = list_cgrag_indexes()
    return [
        ContextInfo(
            name=idx.name,
            path=idx.path,
            chunk_count=idx.chunk_count,
            last_indexed=idx.last_indexed,
            source_path=idx.source_path,
            embedding_model=idx.embedding_model
        )
        for idx in indexes
    ]

@router.post("/contexts/create")
async def create_context(request: CreateContextRequest) -> ContextInfo:
    """Create a new CGRAG index from a directory."""
    # Index the specified directory
    index = await create_cgrag_index(
        name=request.name,
        source_path=request.source_path,
        embedding_model=request.embedding_model
    )
    return ContextInfo(...)

@router.post("/contexts/{name}/refresh")
async def refresh_context(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context."""
    index = await refresh_cgrag_index(name)
    return ContextInfo(...)
```

**Frontend Component:**

```typescript
interface ContextInfo {
  name: string;
  path: string;
  chunkCount: number;
  lastIndexed: string;
  sourcePath: string;
  embeddingModel: string;
}

export const ContextSelector: React.FC<{
  selectedContext: string | null;
  onSelect: (contextName: string | null) => void;
}> = ({ selectedContext, onSelect }) => {
  const { data: contexts } = useContexts();
  const [isCreating, setIsCreating] = useState(false);

  return (
    <AsciiPanel title="CONTEXT SELECTION">
      <div className={styles.contextList}>
        {contexts?.map(ctx => (
          <div
            key={ctx.name}
            className={cx(styles.contextItem, {
              [styles.selected]: ctx.name === selectedContext
            })}
            onClick={() => onSelect(ctx.name)}
          >
            <span className={styles.radio}>
              {ctx.name === selectedContext ? '(*)' : '( )'}
            </span>
            <span className={styles.name}>{ctx.name}</span>
            <span className={styles.chunks}>[{ctx.chunkCount.toLocaleString()} chunks]</span>
            <span className={styles.date}>Indexed: {formatDate(ctx.lastIndexed)}</span>
          </div>
        ))}
        <div
          className={cx(styles.contextItem, {
            [styles.selected]: selectedContext === null
          })}
          onClick={() => onSelect(null)}
        >
          <span className={styles.radio}>
            {selectedContext === null ? '(*)' : '( )'}
          </span>
          <span className={styles.name}>None (no context)</span>
        </div>
      </div>
      <div className={styles.actions}>
        <Button onClick={() => setIsCreating(true)}>CREATE NEW INDEX</Button>
        {selectedContext && (
          <Button onClick={() => refreshContext(selectedContext)}>REFRESH INDEX</Button>
        )}
      </div>
      {isCreating && <CreateContextModal onClose={() => setIsCreating(false)} />}
    </AsciiPanel>
  );
};
```

### Updated Request Model

```python
class CodeChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    # Workspace & Context Selection
    workspace_path: str  # User-selected workspace directory
    context_name: Optional[str] = None  # Selected CGRAG index (None = no context)

    # Feature toggles
    use_cgrag: bool = True  # Only applies if context_name is set
    use_web_search: bool = True
    max_iterations: int = 15

    # Model configuration
    preset: str = "balanced"
    tool_overrides: Optional[Dict[str, ToolModelConfig]] = None
```

### Frontend Configuration Panel

The Code Chat page will have a configuration panel for workspace and context:

```
+------------------------------------------------------------------+
| CODE CHAT CONFIGURATION                                           |
+------------------------------------------------------------------+
|                                                                   |
| WORKSPACE: /projects/synapse-engine              [CHANGE]         |
|   Type: Python (pyproject.toml)                                   |
|   Files: 1,234 | Git: main branch                                 |
|                                                                   |
| CONTEXT: synapse-engine                          [CHANGE]         |
|   Chunks: 42,156 | Last indexed: 2025-11-29 10:30                |
|                                                                   |
| PRESET: [balanced v]                                              |
|                                                                   |
| [ ] Enable web search                                             |
| [x] Enable CGRAG context                                          |
|                                                                   |
+------------------------------------------------------------------+
```

---

## Configurable Model Tiers & Presets

### Per-Tool Model Configuration

Each tool can be configured to use a specific model tier. This allows fine-grained control over quality vs. speed tradeoffs.

```python
class ToolModelConfig(BaseModel):
    """Model configuration for a specific tool."""
    tool: ToolName
    tier: Literal["fast", "balanced", "powerful"]
    temperature: float = 0.7
    max_tokens: int = 2048

class ModelPreset(BaseModel):
    """A preset is a named collection of tool configurations."""
    name: str
    description: str
    planning_tier: str  # Model for ReAct reasoning
    tool_configs: Dict[ToolName, ToolModelConfig]
```

### Built-in Presets

| Preset | Planning | read_file | write_file | search_code | web_search | run_python | Use Case |
|--------|----------|-----------|------------|-------------|------------|------------|----------|
| **speed** | balanced | fast | fast | fast | fast | balanced | Quick tasks, simple queries |
| **balanced** | powerful | balanced | balanced | balanced | balanced | balanced | Default, good quality |
| **quality** | powerful | powerful | powerful | powerful | powerful | powerful | Complex tasks, code review |
| **coding** | powerful | fast | powerful | balanced | fast | powerful | Code generation focus |
| **research** | powerful | fast | fast | powerful | powerful | fast | Web research, exploration |

### Custom Presets

Users can define custom presets in the UI or via API:

```json
{
  "name": "my-preset",
  "description": "Custom preset for my workflow",
  "planning_tier": "powerful",
  "tool_configs": {
    "read_file": { "tier": "fast", "max_tokens": 1024 },
    "write_file": { "tier": "powerful", "temperature": 0.3 },
    "search_code": { "tier": "balanced" },
    "web_search": { "tier": "balanced" },
    "run_python": { "tier": "powerful", "max_tokens": 4096 }
  }
}
```

### Frontend Configuration UI

The Code Chat page will include a settings panel where users can:
1. Select a preset from dropdown
2. Override individual tool tiers
3. Save custom presets
4. View current configuration

```
+-------------------------------------+
| MODEL CONFIGURATION                 |
+-------------------------------------+
| Preset: [balanced v]                |
|                                     |
| Planning:     [powerful v]          |
| read_file:    [fast v]              |
| write_file:   [powerful v]          |
| search_code:  [balanced v]          |
| web_search:   [balanced v]          |
| run_python:   [powerful v]          |
|                                     |
| [Save as Preset] [Reset to Default] |
+-------------------------------------+
```

---

## MCP Tools & Advanced Features

### Extended Tool Set

Beyond basic file operations, Code Chat will include MCP-inspired tools:

```python
class ToolName(str, Enum):
    # File Operations (Core)
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_DIRECTORY = "list_directory"
    DELETE_FILE = "delete_file"

    # Search & Context
    SEARCH_CODE = "search_code"      # CGRAG integration
    WEB_SEARCH = "web_search"        # SearXNG integration
    GREP_FILES = "grep_files"        # Regex search in files

    # Code Execution
    RUN_PYTHON = "run_python"        # Sandboxed Python
    RUN_SHELL = "run_shell"          # Sandboxed shell (limited)

    # Git Operations (MCP)
    GIT_STATUS = "git_status"        # Show working tree status
    GIT_DIFF = "git_diff"            # Show changes
    GIT_LOG = "git_log"              # Show commit history
    GIT_COMMIT = "git_commit"        # Commit changes (with confirmation)
    GIT_BRANCH = "git_branch"        # List/create branches

    # LSP Operations (MCP)
    GET_DIAGNOSTICS = "get_diagnostics"    # Lint errors, type errors
    GET_DEFINITIONS = "get_definitions"    # Go to definition
    GET_REFERENCES = "get_references"      # Find all references

    # Project Context
    GET_PROJECT_INFO = "get_project_info"  # Detect project type, deps
```

### MCP Tool Implementations

**Git Tools (`backend/app/services/code_chat/mcp_tools/git.py`):**

```python
async def git_status(workspace: str) -> ToolResult:
    """Get git status for workspace."""
    result = await run_git_command(workspace, ["status", "--porcelain", "-b"])
    return ToolResult(
        success=True,
        output=parse_git_status(result),
        metadata={"branch": extract_branch(result)}
    )

async def git_diff(workspace: str, file: Optional[str] = None) -> ToolResult:
    """Get diff for staged/unstaged changes."""
    cmd = ["diff", "--color=never"]
    if file:
        cmd.append(file)
    result = await run_git_command(workspace, cmd)
    return ToolResult(success=True, output=result)

async def git_commit(workspace: str, message: str, files: List[str]) -> ToolResult:
    """Commit changes (requires user confirmation in UI)."""
    # This tool returns a confirmation request, not direct execution
    return ToolResult(
        success=True,
        requires_confirmation=True,
        confirmation_type="git_commit",
        data={"message": message, "files": files}
    )
```

**LSP Tools (`backend/app/services/code_chat/mcp_tools/lsp.py`):**

```python
async def get_diagnostics(workspace: str, file: str) -> ToolResult:
    """Get lint/type errors for a file using pyright/eslint."""
    # Use subprocess to run type checker
    if file.endswith('.py'):
        result = await run_command(["pyright", "--outputjson", file])
        diagnostics = parse_pyright_output(result)
    elif file.endswith(('.ts', '.tsx', '.js', '.jsx')):
        result = await run_command(["eslint", "--format=json", file])
        diagnostics = parse_eslint_output(result)
    else:
        diagnostics = []

    return ToolResult(
        success=True,
        output=format_diagnostics(diagnostics),
        metadata={"count": len(diagnostics), "file": file}
    )
```

### Conversation Memory

Sessions maintain context across multiple queries:

```python
class ConversationMemory:
    """Maintain context within a Code Chat session."""

    def __init__(self, session_id: str, max_turns: int = 20):
        self.session_id = session_id
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []
        self.file_context: Dict[str, str] = {}  # Recently accessed files
        self.project_context: Optional[ProjectInfo] = None
        self.workspace_path: Optional[str] = None
        self.context_name: Optional[str] = None

    def add_turn(self, query: str, response: str, tools_used: List[str]):
        """Add a conversation turn."""
        self.turns.append(ConversationTurn(
            query=query,
            response=response,
            tools_used=tools_used,
            timestamp=datetime.now()
        ))
        # Trim to max turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def get_context_for_prompt(self) -> str:
        """Build context string for LLM prompt."""
        context_parts = []

        # Workspace info
        if self.workspace_path:
            context_parts.append(f"## Workspace: {self.workspace_path}")

        # Recent conversation
        if self.turns:
            context_parts.append("## Recent Conversation")
            for turn in self.turns[-5:]:  # Last 5 turns
                context_parts.append(f"User: {turn.query[:200]}...")
                context_parts.append(f"Assistant: {turn.response[:200]}...")

        # Project context
        if self.project_context:
            context_parts.append(f"## Project: {self.project_context.type}")
            context_parts.append(f"Dependencies: {self.project_context.deps[:500]}")

        return "\n\n".join(context_parts)
```

### Diff Preview System

Before applying file changes, show a diff preview:

```python
class DiffPreview(BaseModel):
    """Preview of file changes before applying."""
    file_path: str
    original_content: Optional[str]
    new_content: str
    diff_lines: List[DiffLine]
    change_type: Literal["create", "modify", "delete"]

class DiffLine(BaseModel):
    line_number: int
    type: Literal["add", "remove", "context"]
    content: str

async def create_diff_preview(
    workspace: str,
    file_path: str,
    new_content: str
) -> DiffPreview:
    """Create a diff preview for file changes."""
    full_path = Path(workspace) / file_path

    if full_path.exists():
        original = full_path.read_text()
        change_type = "modify"
    else:
        original = None
        change_type = "create"

    diff_lines = compute_diff(original, new_content)

    return DiffPreview(
        file_path=file_path,
        original_content=original,
        new_content=new_content,
        diff_lines=diff_lines,
        change_type=change_type
    )
```

### Project Context Detection

Auto-detect project type and dependencies:

```python
class ProjectInfo(BaseModel):
    """Detected project information."""
    type: str  # "python", "node", "rust", "go", etc.
    name: Optional[str]
    version: Optional[str]
    dependencies: List[str]
    dev_dependencies: List[str]
    scripts: Dict[str, str]
    entry_points: List[str]

async def detect_project_info(workspace: str) -> Optional[ProjectInfo]:
    """Detect project type from config files."""
    workspace_path = Path(workspace)

    # Check for Python project
    if (workspace_path / "pyproject.toml").exists():
        return parse_pyproject_toml(workspace_path / "pyproject.toml")
    if (workspace_path / "requirements.txt").exists():
        return parse_requirements_txt(workspace_path)
    if (workspace_path / "setup.py").exists():
        return parse_setup_py(workspace_path / "setup.py")

    # Check for Node.js project
    if (workspace_path / "package.json").exists():
        return parse_package_json(workspace_path / "package.json")

    # Check for Rust project
    if (workspace_path / "Cargo.toml").exists():
        return parse_cargo_toml(workspace_path / "Cargo.toml")

    # Check for Go project
    if (workspace_path / "go.mod").exists():
        return parse_go_mod(workspace_path / "go.mod")

    return None
```

### Updated Preset Table with MCP Tools

| Preset | Planning | File Ops | Git Ops | LSP | Python | Web |
|--------|----------|----------|---------|-----|--------|-----|
| **speed** | balanced | fast | fast | fast | balanced | fast |
| **balanced** | powerful | fast | balanced | balanced | balanced | balanced |
| **quality** | powerful | balanced | powerful | powerful | powerful | powerful |
| **coding** | powerful | fast | powerful | powerful | powerful | fast |
| **debug** | powerful | fast | powerful | powerful | powerful | powerful |

---

## Phase 1: Backend Core - ReAct Agent Engine

**Estimated Time:** 12-16 hours

### 1.1 Models (`backend/app/models/code_chat.py`)

```python
# Key models to create:
class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"      # Q4 model reasoning
    EXECUTING = "executing"    # Running tool
    OBSERVING = "observing"    # Processing result
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class ToolName(str, Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_DIRECTORY = "list_directory"
    DELETE_FILE = "delete_file"
    SEARCH_CODE = "search_code"
    WEB_SEARCH = "web_search"
    RUN_PYTHON = "run_python"
    # MCP Tools
    GIT_STATUS = "git_status"
    GIT_DIFF = "git_diff"
    GIT_LOG = "git_log"
    GIT_COMMIT = "git_commit"
    GET_DIAGNOSTICS = "get_diagnostics"

class ReActStep(BaseModel):
    step_number: int
    thought: str
    action: Optional[ToolCall]
    observation: Optional[str]
    state: AgentState
    model_tier: str
    timestamp: datetime

class CodeChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

    # Workspace & Context Selection (USER SELECTABLE IN TUI)
    workspace_path: str  # Selected via WorkspaceSelector
    context_name: Optional[str] = None  # Selected via ContextSelector

    # Feature toggles
    use_cgrag: bool = True
    use_web_search: bool = True
    max_iterations: int = 15

    # Model configuration
    preset: str = "balanced"  # speed, balanced, quality, coding, research
    tool_overrides: Optional[Dict[str, ToolModelConfig]] = None

# Built-in presets
PRESETS: Dict[str, ModelPreset] = {
    "speed": ModelPreset(
        name="speed",
        description="Fast responses, lower quality",
        planning_tier="balanced",
        tool_configs={
            ToolName.READ_FILE: ToolModelConfig(tier="fast"),
            ToolName.WRITE_FILE: ToolModelConfig(tier="fast"),
            ToolName.SEARCH_CODE: ToolModelConfig(tier="fast"),
            ToolName.WEB_SEARCH: ToolModelConfig(tier="fast"),
            ToolName.RUN_PYTHON: ToolModelConfig(tier="balanced"),
        }
    ),
    "balanced": ModelPreset(
        name="balanced",
        description="Default - good quality and speed",
        planning_tier="powerful",
        tool_configs={
            ToolName.READ_FILE: ToolModelConfig(tier="fast"),
            ToolName.WRITE_FILE: ToolModelConfig(tier="balanced"),
            ToolName.SEARCH_CODE: ToolModelConfig(tier="balanced"),
            ToolName.WEB_SEARCH: ToolModelConfig(tier="balanced"),
            ToolName.RUN_PYTHON: ToolModelConfig(tier="balanced"),
        }
    ),
    "quality": ModelPreset(
        name="quality",
        description="Best quality, slower responses",
        planning_tier="powerful",
        tool_configs={
            ToolName.READ_FILE: ToolModelConfig(tier="balanced"),
            ToolName.WRITE_FILE: ToolModelConfig(tier="powerful"),
            ToolName.SEARCH_CODE: ToolModelConfig(tier="powerful"),
            ToolName.WEB_SEARCH: ToolModelConfig(tier="powerful"),
            ToolName.RUN_PYTHON: ToolModelConfig(tier="powerful"),
        }
    ),
    "coding": ModelPreset(
        name="coding",
        description="Optimized for code generation",
        planning_tier="powerful",
        tool_configs={
            ToolName.READ_FILE: ToolModelConfig(tier="fast"),
            ToolName.WRITE_FILE: ToolModelConfig(tier="powerful", temperature=0.3),
            ToolName.SEARCH_CODE: ToolModelConfig(tier="balanced"),
            ToolName.WEB_SEARCH: ToolModelConfig(tier="fast"),
            ToolName.RUN_PYTHON: ToolModelConfig(tier="powerful"),
        }
    ),
}
```

### 1.2 Tools (`backend/app/services/code_chat/tools.py`)

```python
# Tool implementations with security
class CodeChatTools:
    def __init__(self, workspace_root: str, cgrag: CGRAGRetriever, searxng: SearXNGClient):
        self.workspace_root = Path(workspace_root).resolve()
        self.cgrag = cgrag
        self.searxng = searxng

    def _validate_path(self, path: str) -> Path:
        """Prevent path traversal attacks."""
        full_path = (self.workspace_root / path).resolve()
        if not str(full_path).startswith(str(self.workspace_root)):
            raise SecurityError(f"Path traversal blocked: {path}")
        return full_path

    async def read_file(self, path: str) -> ToolResult: ...
    async def write_file(self, path: str, content: str) -> ToolResult: ...
    async def list_directory(self, path: str = ".") -> ToolResult: ...
    async def delete_file(self, path: str) -> ToolResult: ...
    async def search_code(self, query: str) -> ToolResult: ...
    async def web_search(self, query: str) -> ToolResult: ...
    async def run_python(self, code: str) -> ToolResult: ...
```

### 1.3 ReAct Agent (`backend/app/services/code_chat/agent.py`)

```python
class ReActAgent:
    """LangGraph-inspired ReAct agent with state machine."""

    SYSTEM_PROMPT = """You are an expert coding assistant with access to tools.

Available tools:
- read_file(path): Read file contents from workspace
- write_file(path, content): Create or overwrite a file
- list_directory(path): List directory contents
- delete_file(path): Delete a file
- search_code(query): Search codebase via CGRAG
- web_search(query): Search the web for documentation
- run_python(code): Execute Python code in sandbox
- git_status(): Show working tree status
- git_diff(file?): Show changes
- get_diagnostics(file): Get lint/type errors

Response format (MUST follow exactly):
Thought: [Your reasoning about what to do next]
Action: tool_name(arg1="value1", arg2="value2")

OR when you have the final answer:
Thought: [Summary of what was done]
Answer: [Complete response to the user]
"""

    async def run(self, request: CodeChatRequest) -> AsyncIterator[CodeChatStreamEvent]:
        """Execute ReAct loop with streaming events."""
        state = AgentState.PLANNING
        steps: List[ReActStep] = []

        # Initialize tools with user-selected workspace
        self.tools = CodeChatTools(
            workspace_root=request.workspace_path,
            cgrag=self._get_cgrag_for_context(request.context_name),
            searxng=self.searxng
        )

        # Initial context from CGRAG (if context selected)
        if request.use_cgrag and request.context_name:
            context = await self.tools.search_code(request.query)
            yield CodeChatStreamEvent(type="context", data=context)

        for iteration in range(request.max_iterations):
            # Select model tier based on state
            tier = self._select_tier(state, iteration)

            # Get LLM response
            yield CodeChatStreamEvent(type="state", state=state, tier=tier)
            response = await self._call_llm(request.query, steps, tier)

            # Parse ReAct format
            thought, action_or_answer = self._parse_response(response)
            yield CodeChatStreamEvent(type="thought", content=thought)

            if action_or_answer.is_answer:
                yield CodeChatStreamEvent(type="answer", content=action_or_answer.content)
                return

            # Execute tool
            state = AgentState.EXECUTING
            yield CodeChatStreamEvent(type="action", tool=action_or_answer.tool)

            result = await self._execute_tool(action_or_answer)
            state = AgentState.OBSERVING
            yield CodeChatStreamEvent(type="observation", content=result)

            steps.append(ReActStep(...))
            state = AgentState.PLANNING

    def _get_tier_for_tool(self, tool: ToolName) -> str:
        """Get model tier for a specific tool from preset + overrides."""
        # Check for override first
        if self.tool_overrides and tool in self.tool_overrides:
            return self.tool_overrides[tool].tier
        # Fall back to preset
        return self.preset.tool_configs[tool].tier

    def _get_planning_tier(self) -> str:
        """Get model tier for ReAct planning/reasoning."""
        return self.preset.planning_tier
```

### 1.4 Router (`backend/app/routers/code_chat.py`)

```python
router = APIRouter(prefix="/api/code-chat", tags=["code-chat"])

# ========== WORKSPACE SELECTION ==========

@router.get("/workspaces")
async def list_workspaces(path: str = "/") -> WorkspaceListResponse:
    """List directories available for workspace selection."""
    return WorkspaceListResponse(
        current_path=path,
        directories=list_directories(path),
        parent_path=get_parent_path(path),
        is_git_repo=check_git_repo(path),
        project_type=detect_project_type(path)
    )

@router.post("/workspaces/validate")
async def validate_workspace(path: str) -> WorkspaceValidation:
    """Validate a workspace path and return metadata."""
    return WorkspaceValidation(
        valid=is_valid_workspace(path),
        is_git_repo=check_git_repo(path),
        project_info=detect_project_info(path),
        file_count=count_files(path),
        has_cgrag_index=check_cgrag_index_exists(path)
    )

# ========== CONTEXT SELECTION ==========

@router.get("/contexts")
async def list_contexts() -> List[ContextInfo]:
    """List available CGRAG indexes for context selection."""
    indexes = list_cgrag_indexes()
    return [
        ContextInfo(
            name=idx.name,
            path=idx.path,
            chunk_count=idx.chunk_count,
            last_indexed=idx.last_indexed,
            source_path=idx.source_path
        )
        for idx in indexes
    ]

@router.post("/contexts/create")
async def create_context(request: CreateContextRequest) -> ContextInfo:
    """Create a new CGRAG index from a directory."""
    index = await create_cgrag_index(
        name=request.name,
        source_path=request.source_path
    )
    return ContextInfo(...)

@router.post("/contexts/{name}/refresh")
async def refresh_context(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context."""
    index = await refresh_cgrag_index(name)
    return ContextInfo(...)

# ========== PRESETS ==========

@router.get("/presets")
async def get_presets() -> List[ModelPreset]:
    """Get all available presets (built-in + custom)."""
    return list(PRESETS.values())

@router.get("/presets/{name}")
async def get_preset(name: str) -> ModelPreset:
    """Get a specific preset by name."""
    if name not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return PRESETS[name]

@router.post("/presets")
async def create_preset(preset: ModelPreset) -> ModelPreset:
    """Create a custom preset (saved to user storage)."""
    custom_presets[preset.name] = preset
    return preset

# ========== QUERY ==========

@router.post("/query")
async def query(request: CodeChatRequest) -> StreamingResponse:
    """SSE streaming endpoint for Code Chat."""
    agent = get_agent()

    async def event_stream():
        try:
            async for event in agent.run(request):
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Session-ID": request.session_id or str(uuid4())}
    )

@router.post("/cancel/{session_id}")
async def cancel(session_id: str):
    """Cancel an active session."""
    # Cancel via session registry
```

---

## Phase 2: Python Sandbox Container

**Estimated Time:** 6-8 hours

### 2.1 Dockerfile (`sandbox/Dockerfile`)

```dockerfile
FROM python:3.11-slim

# Non-root user for security
RUN useradd -m -u 1000 sandbox
WORKDIR /app

# Install safe packages only
RUN pip install --no-cache-dir numpy pandas matplotlib

COPY server.py /app/
RUN chown -R sandbox:sandbox /app

USER sandbox
EXPOSE 8001
CMD ["python", "server.py"]
```

### 2.2 Execution Server (`sandbox/server.py`)

```python
from fastapi import FastAPI
import ast
import sys
from io import StringIO
import resource

app = FastAPI()

SAFE_BUILTINS = {
    'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
    'set', 'tuple', 'bool', 'sum', 'min', 'max', 'sorted', 'enumerate',
    'zip', 'map', 'filter', 'abs', 'round', 'pow', 'divmod'
}

ALLOWED_IMPORTS = {'math', 'datetime', 'json', 're', 'collections', 'itertools'}

@app.post("/execute")
async def execute(code: str, timeout: int = 30):
    """Execute Python code with restrictions."""
    # Set resource limits
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

    # Validate AST for dangerous operations
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] not in ALLOWED_IMPORTS:
                        return {"error": f"Import not allowed: {alias.name}"}
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    # Execute with captured output
    stdout = StringIO()
    sys.stdout = stdout
    try:
        exec(code, {"__builtins__": {k: __builtins__[k] for k in SAFE_BUILTINS}})
        return {"output": stdout.getvalue(), "error": None}
    except Exception as e:
        return {"output": stdout.getvalue(), "error": str(e)}
    finally:
        sys.stdout = sys.__stdout__
```

### 2.3 Docker Compose Addition

```yaml
# Add to docker-compose.yml
synapse_sandbox:
  build: ./sandbox
  container_name: synapse_sandbox
  networks:
    - synapse_net
  volumes:
    - ./workspace:/workspace:ro  # Read-only workspace access
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 512M
  security_opt:
    - no-new-privileges:true
  read_only: true
  tmpfs:
    - /tmp:size=64M
```

---

## Phase 3: Frontend Implementation

**Estimated Time:** 12-16 hours

### 3.1 Types (`frontend/src/types/codeChat.ts`)

```typescript
export type AgentState = 'idle' | 'planning' | 'executing' | 'observing' | 'completed' | 'error';
export type ModelTier = 'fast' | 'balanced' | 'powerful';
export type ToolName = 'read_file' | 'write_file' | 'list_directory' | 'delete_file' | 'search_code' | 'web_search' | 'run_python' | 'git_status' | 'git_diff' | 'get_diagnostics';

export interface ToolModelConfig {
  tier: ModelTier;
  temperature?: number;
  maxTokens?: number;
}

export interface ModelPreset {
  name: string;
  description: string;
  planningTier: ModelTier;
  toolConfigs: Record<ToolName, ToolModelConfig>;
}

// Workspace Selection Types
export interface DirectoryInfo {
  name: string;
  path: string;
  isDirectory: boolean;
  isGitRepo: boolean;
  projectType: string | null;
}

export interface WorkspaceInfo {
  path: string;
  isGitRepo: boolean;
  projectType: string | null;
  projectInfo: ProjectInfo | null;
  fileCount: number;
  hasCgragIndex: boolean;
}

export interface ProjectInfo {
  type: string;
  name: string | null;
  version: string | null;
  dependencies: string[];
}

// Context Selection Types
export interface ContextInfo {
  name: string;
  path: string;
  chunkCount: number;
  lastIndexed: string;
  sourcePath: string;
  embeddingModel: string;
}

// ReAct Types
export interface ReActStep {
  stepNumber: number;
  thought: string;
  action?: { tool: ToolName; args: Record<string, string> };
  observation?: string;
  state: AgentState;
  modelTier: ModelTier;
  timestamp: string;
}

export interface CodeChatStreamEvent {
  type: 'state' | 'thought' | 'action' | 'observation' | 'answer' | 'error' | 'cancelled';
  content?: string;
  state?: AgentState;
  tier?: ModelTier;
  tool?: { name: ToolName; args: Record<string, string> };
}

export interface CodeChatRequest {
  query: string;
  sessionId?: string;
  // Workspace & Context Selection
  workspacePath: string;
  contextName?: string | null;
  // Feature toggles
  useCgrag?: boolean;
  useWebSearch?: boolean;
  maxIterations?: number;
  // Model configuration
  preset?: string;
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
}

export const BUILT_IN_PRESETS: string[] = ['speed', 'balanced', 'quality', 'coding', 'research'];
```

### 3.2 Hooks

**`frontend/src/hooks/useWorkspaces.ts`:**

```typescript
export function useWorkspaces(path: string) {
  return useQuery({
    queryKey: ['workspaces', path],
    queryFn: () => fetch(`/api/code-chat/workspaces?path=${encodeURIComponent(path)}`)
      .then(res => res.json()),
  });
}

export function useWorkspaceValidation(path: string) {
  return useQuery({
    queryKey: ['workspace-validation', path],
    queryFn: () => fetch(`/api/code-chat/workspaces/validate?path=${encodeURIComponent(path)}`)
      .then(res => res.json()),
    enabled: !!path,
  });
}
```

**`frontend/src/hooks/useContexts.ts`:**

```typescript
export function useContexts() {
  return useQuery({
    queryKey: ['contexts'],
    queryFn: () => fetch('/api/code-chat/contexts').then(res => res.json()),
  });
}

export function useCreateContext() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateContextRequest) =>
      fetch('/api/code-chat/contexts/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      }).then(res => res.json()),
    onSuccess: () => queryClient.invalidateQueries(['contexts']),
  });
}
```

**`frontend/src/hooks/useCodeChat.ts`:**

```typescript
export function useCodeChat() {
  const [steps, setSteps] = useState<ReActStep[]>([]);
  const [currentState, setCurrentState] = useState<AgentState>('idle');
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const submit = useCallback(async (request: CodeChatRequest) => {
    setSteps([]);
    setAnswer(null);
    setError(null);
    setCurrentState('planning');

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/code-chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const events = text.split('\n\n').filter(Boolean);

        for (const eventStr of events) {
          if (eventStr.startsWith('data: ')) {
            const event: CodeChatStreamEvent = JSON.parse(eventStr.slice(6));
            handleEvent(event);
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
        setCurrentState('error');
      }
    }
  }, []);

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setCurrentState('idle');
  }, []);

  return { steps, currentState, answer, error, submit, cancel };
}
```

### 3.3 Page Component (`frontend/src/pages/CodeChatPage/CodeChatPage.tsx`)

```tsx
export const CodeChatPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [workspacePath, setWorkspacePath] = useState<string>('');
  const [contextName, setContextName] = useState<string | null>(null);
  const [preset, setPreset] = useState('balanced');
  const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);
  const [showContextSelector, setShowContextSelector] = useState(false);

  const { steps, currentState, answer, error, submit, cancel } = useCodeChat();
  const { data: workspaceInfo } = useWorkspaceValidation(workspacePath);

  const handleSubmit = () => {
    if (!workspacePath) {
      toast.error('Please select a workspace first');
      return;
    }
    submit({
      query,
      workspacePath,
      contextName,
      preset,
      useCgrag: !!contextName,
      useWebSearch: true,
    });
  };

  return (
    <div className={styles.container}>
      {/* Configuration Panel */}
      <AsciiPanel title="CODE CHAT CONFIGURATION" className={styles.configPanel}>
        <div className={styles.configRow}>
          <span className={styles.label}>WORKSPACE:</span>
          <span className={styles.value}>
            {workspacePath || 'None selected'}
          </span>
          <Button onClick={() => setShowWorkspaceSelector(true)}>CHANGE</Button>
        </div>
        {workspaceInfo && (
          <div className={styles.workspaceInfo}>
            Type: {workspaceInfo.projectType || 'Unknown'} |
            Files: {workspaceInfo.fileCount} |
            Git: {workspaceInfo.isGitRepo ? 'Yes' : 'No'}
          </div>
        )}

        <div className={styles.configRow}>
          <span className={styles.label}>CONTEXT:</span>
          <span className={styles.value}>
            {contextName || 'None (no CGRAG)'}
          </span>
          <Button onClick={() => setShowContextSelector(true)}>CHANGE</Button>
        </div>

        <div className={styles.configRow}>
          <span className={styles.label}>PRESET:</span>
          <select value={preset} onChange={e => setPreset(e.target.value)}>
            {BUILT_IN_PRESETS.map(p => (
              <option key={p} value={p}>{p.toUpperCase()}</option>
            ))}
          </select>
        </div>
      </AsciiPanel>

      {/* Main Chat Panel */}
      <AsciiPanel title="CODE CHAT" className={styles.mainPanel}>
        {/* State indicator */}
        <div className={styles.stateBar}>
          <span className={styles[`state-${currentState}`]}>
            [{currentState.toUpperCase()}]
          </span>
          {currentState !== 'idle' && currentState !== 'completed' && (
            <Button onClick={cancel} variant="danger">CANCEL</Button>
          )}
        </div>

        {/* Query input */}
        <div className={styles.inputSection}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your coding task..."
            disabled={currentState !== 'idle' && currentState !== 'completed'}
          />
          <Button
            onClick={handleSubmit}
            disabled={!query.trim() || !workspacePath || (currentState !== 'idle' && currentState !== 'completed')}
          >
            EXECUTE
          </Button>
        </div>

        {/* ReAct steps */}
        <div className={styles.stepsContainer}>
          {steps.map((step, i) => (
            <div key={i} className={styles.step}>
              <div className={styles.stepHeader}>
                Step {step.stepNumber} [{step.modelTier}]
              </div>
              <div className={styles.thought}>
                <span className={styles.label}>THOUGHT:</span> {step.thought}
              </div>
              {step.action && (
                <div className={styles.action}>
                  <span className={styles.label}>ACTION:</span>
                  {step.action.tool}({JSON.stringify(step.action.args)})
                </div>
              )}
              {step.observation && (
                <div className={styles.observation}>
                  <span className={styles.label}>OBSERVATION:</span>
                  <pre>{step.observation}</pre>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Final answer */}
        {answer && (
          <div className={styles.answer}>
            <div className={styles.answerHeader}>ANSWER</div>
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        )}

        {error && <div className={styles.error}>ERROR: {error}</div>}
      </AsciiPanel>

      {/* Modals */}
      {showWorkspaceSelector && (
        <WorkspaceSelector
          currentWorkspace={workspacePath}
          onSelect={(path) => {
            setWorkspacePath(path);
            setShowWorkspaceSelector(false);
          }}
          onClose={() => setShowWorkspaceSelector(false)}
        />
      )}

      {showContextSelector && (
        <ContextSelector
          selectedContext={contextName}
          onSelect={(name) => {
            setContextName(name);
            setShowContextSelector(false);
          }}
          onClose={() => setShowContextSelector(false)}
        />
      )}
    </div>
  );
};
```

---

## Phase 4: Integration

**Estimated Time:** 6-8 hours

### 4.1 Backend Integration

**Modify `backend/app/main.py`:**
```python
from app.routers import code_chat
from app.services.code_chat.agent import init_react_agent

# In lifespan function, after model_selector init:
react_agent = init_react_agent(model_selector, cgrag_retriever, searxng_client)

# Add router:
app.include_router(code_chat.router)
```

**Modify `backend/app/models/events.py`:**
```python
class EventType(str, Enum):
    # ... existing types ...
    CODE_CHAT_STEP = "code_chat_step"
    CODE_CHAT_COMPLETE = "code_chat_complete"
    CODE_CHAT_ERROR = "code_chat_error"
```

### 4.2 Frontend Integration

**Modify `frontend/src/components/modes/ModeSelector.tsx`:**
```typescript
export type QueryMode = 'two-stage' | 'simple' | 'council' | 'benchmark' | 'code-chat';

const MODES: ModeDefinition[] = [
  // ... existing modes ...
  {
    id: 'code-chat',
    label: 'CODE CHAT',
    description: 'Agentic assistant with file ops & code execution',
    available: true,
  },
];
```

**Modify `frontend/src/router/routes.tsx`:**
```typescript
import { CodeChatPage } from '../pages/CodeChatPage/CodeChatPage';

// Add route:
{ path: 'code-chat', element: <CodeChatPage /> }
```

---

## Phase 5: Testing & Security

**Estimated Time:** 4-6 hours

### Security Checklist

- [ ] Path traversal prevention (all file paths validated)
- [ ] Workspace path validation (must be within allowed directories)
- [ ] Sandbox container isolation (non-root, read-only, memory limits)
- [ ] Python execution restrictions (no dangerous imports)
- [ ] Session timeout and cleanup
- [ ] Rate limiting on endpoints
- [ ] Input sanitization

### Testing Checklist

**Backend:**
- [ ] ReAct response parsing (Thought/Action/Answer formats)
- [ ] Tool execution (each tool individually)
- [ ] State machine transitions
- [ ] Streaming events format
- [ ] Error handling and recovery
- [ ] Cancellation mid-execution
- [ ] Workspace listing and validation
- [ ] Context listing and creation

**Frontend:**
- [ ] SSE event parsing
- [ ] Step visualization updates
- [ ] Cancel functionality
- [ ] Error display
- [ ] Workspace selector navigation
- [ ] Context selector display

**Integration:**
- [ ] Multi-step ReAct loop (5+ iterations)
- [ ] File read -> modify -> write workflow
- [ ] CGRAG + web search combination
- [ ] Python execution with output capture
- [ ] Workspace switching mid-session
- [ ] Context switching mid-session

---

## Files Summary

### New Files (26)

| File | Purpose |
|------|---------|
| **Backend Models & Core** | |
| `backend/app/models/code_chat.py` | Pydantic models + presets |
| `backend/app/services/code_chat/__init__.py` | Package init |
| `backend/app/services/code_chat/agent.py` | ReAct agent engine |
| `backend/app/services/code_chat/memory.py` | Conversation memory management |
| `backend/app/services/code_chat/presets.py` | Preset definitions + storage |
| `backend/app/services/code_chat/workspace.py` | Workspace listing/validation |
| `backend/app/services/code_chat/context.py` | CGRAG context management |
| **Backend Tools** | |
| `backend/app/services/code_chat/tools/base.py` | Base tool classes |
| `backend/app/services/code_chat/tools/file_ops.py` | File read/write/delete/list |
| `backend/app/services/code_chat/tools/search.py` | CGRAG + web search + grep |
| `backend/app/services/code_chat/tools/execution.py` | Python + shell sandbox |
| `backend/app/services/code_chat/tools/git.py` | Git operations (MCP) |
| `backend/app/services/code_chat/tools/lsp.py` | LSP diagnostics (MCP) |
| `backend/app/services/code_chat/tools/project.py` | Project detection |
| **Backend Router** | |
| `backend/app/routers/code_chat.py` | API endpoints (query + presets + workspaces + contexts) |
| **Sandbox** | |
| `sandbox/Dockerfile` | Sandbox container |
| `sandbox/server.py` | Execution server |
| **Frontend** | |
| `frontend/src/types/codeChat.ts` | TypeScript types |
| `frontend/src/hooks/useCodeChat.ts` | React hook for chat |
| `frontend/src/hooks/usePresets.ts` | React hook for preset management |
| `frontend/src/hooks/useWorkspaces.ts` | React hook for workspace browsing |
| `frontend/src/hooks/useContexts.ts` | React hook for context selection |
| `frontend/src/pages/CodeChatPage/CodeChatPage.tsx` | Main page component |
| `frontend/src/pages/CodeChatPage/CodeChatPage.module.css` | Styles |
| `frontend/src/pages/CodeChatPage/WorkspaceSelector.tsx` | Workspace file browser |
| `frontend/src/pages/CodeChatPage/ContextSelector.tsx` | CGRAG context selector |
| `frontend/src/pages/CodeChatPage/PresetSelector.tsx` | Preset dropdown + overrides |
| `frontend/src/pages/CodeChatPage/DiffPreview.tsx` | Diff visualization component |
| `frontend/src/pages/CodeChatPage/index.ts` | Export |
| **Workspace** | |
| `workspace/.gitkeep` | Default workspace directory |

### Files to Modify (5)

| File | Changes |
|------|---------|
| `docker-compose.yml` | Add sandbox service, workspace volume |
| `backend/app/main.py` | Initialize agent, add router |
| `backend/app/models/events.py` | Add Code Chat event types |
| `frontend/src/router/routes.tsx` | Add route |
| `frontend/src/components/modes/ModeSelector.tsx` | Add mode |

---

## Implementation Order & Agent Assignments

Each phase should be handled by the appropriate specialized agent:

### Phase 1: Backend Core (12-16 hours)
**Lead Agent:** `@backend-architect`

| Task | Agent | Description |
|------|-------|-------------|
| 1.1 Models | @backend-architect | Pydantic models, presets, state machine |
| 1.2 Workspace/Context | @backend-architect | Workspace listing, context management |
| 1.3 Tools | @backend-architect + @cgrag-specialist | Tool implementations, CGRAG integration |
| 1.4 Agent | @backend-architect | ReAct engine, model routing |
| 1.5 Router | @backend-architect | API endpoints, SSE streaming |

### Phase 2: Sandbox Container (6-8 hours)
**Lead Agent:** `@devops-engineer`

| Task | Agent | Description |
|------|-------|-------------|
| 2.1 Dockerfile | @devops-engineer | Container config, security |
| 2.2 Server | @devops-engineer + @security-specialist | Execution server, restrictions |
| 2.3 Compose | @devops-engineer | Docker integration |

### Phase 3: Frontend (12-16 hours)
**Lead Agent:** `@frontend-engineer`

| Task | Agent | Description |
|------|-------|-------------|
| 3.1 Types | @frontend-engineer | TypeScript interfaces |
| 3.2 Hooks | @frontend-engineer | useCodeChat, usePresets, useWorkspaces, useContexts |
| 3.3 Selectors | @frontend-engineer + @terminal-ui-specialist | WorkspaceSelector, ContextSelector |
| 3.4 Page | @frontend-engineer + @terminal-ui-specialist | CodeChatPage, PresetSelector |
| 3.5 Styling | @terminal-ui-specialist | Terminal aesthetic CSS |

### Phase 4: Integration (6-8 hours)
**Lead Agent:** `@backend-architect`

| Task | Agent | Description |
|------|-------|-------------|
| 4.1 Main.py | @backend-architect | Router registration, init |
| 4.2 Events | @websocket-realtime-specialist | Event types, streaming |
| 4.3 Routes | @frontend-engineer | Route integration |

### Phase 5: Testing & Security (4-6 hours)
**Lead Agents:** `@testing-specialist` + `@security-specialist`

| Task | Agent | Description |
|------|-------|-------------|
| 5.1 Security | @security-specialist | Path validation, sandbox hardening |
| 5.2 Unit Tests | @testing-specialist | Backend + frontend tests |
| 5.3 E2E Tests | @testing-specialist | Full integration tests |

Start with Phase 1.1 (models) as it defines the data structures everything else depends on.

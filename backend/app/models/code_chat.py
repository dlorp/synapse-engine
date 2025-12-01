"""Code Chat mode data models using Pydantic.

This module defines the data structures for the Code Chat agentic coding
assistant including ReAct loop states, tool configurations, workspace
management, and streaming event models.

Author: Backend Architect
Phase: Code Chat Implementation (Phase 1.1)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Enums
# ============================================================================


class AgentState(str, Enum):
    """Agent state machine states for the ReAct loop.

    States define the current phase of agent execution:
    - IDLE: Awaiting next query
    - PLANNING: Q4 model reasoning about next action
    - EXECUTING: Running selected tool
    - OBSERVING: Processing tool result and deciding next step
    - COMPLETED: Task successfully finished
    - ERROR: Encountered unrecoverable error
    - CANCELLED: User or system cancelled execution
    """
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ToolName(str, Enum):
    """Available tools for the Code Chat agent.

    Tools are grouped by category:
    - File Operations: read_file, write_file, list_directory, delete_file
    - Code Search: search_code, grep_files
    - Web Search: web_search
    - Execution: run_python, run_shell
    - MCP Tools: git_*, get_diagnostics, get_definitions, get_references, get_project_info
    """
    # File operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_DIRECTORY = "list_directory"
    DELETE_FILE = "delete_file"

    # Code search
    SEARCH_CODE = "search_code"
    GREP_FILES = "grep_files"

    # Web search
    WEB_SEARCH = "web_search"

    # Execution
    RUN_PYTHON = "run_python"
    RUN_SHELL = "run_shell"

    # MCP Tools - Git
    GIT_STATUS = "git_status"
    GIT_DIFF = "git_diff"
    GIT_LOG = "git_log"
    GIT_COMMIT = "git_commit"
    GIT_BRANCH = "git_branch"

    # MCP Tools - LSP
    GET_DIAGNOSTICS = "get_diagnostics"
    GET_DEFINITIONS = "get_definitions"
    GET_REFERENCES = "get_references"
    GET_PROJECT_INFO = "get_project_info"


# ============================================================================
# Tool Configuration Models
# ============================================================================


class ToolModelConfig(BaseModel):
    """Model configuration for a specific tool.

    Attributes:
        tier: Model tier to use for this tool (fast/balanced/powerful)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate (1-4096)

    Example:
        >>> config = ToolModelConfig(
        ...     tier="powerful",
        ...     temperature=0.3,
        ...     max_tokens=2048
        ... )
    """
    tier: Literal["fast", "balanced", "powerful"] = Field(
        default="balanced",
        description="Model tier for this tool"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=4096,
        description="Maximum tokens to generate"
    )

    model_config = ConfigDict(from_attributes=True)


class ModelPreset(BaseModel):
    """Named collection of tool configurations for quick switching.

    Presets provide optimized configurations for different workflows:
    - SYNAPSE_DEFAULT: Foundational baseline for general-purpose assistance
    - SYNAPSE_ANALYST: Deep analytical substrate for decomposition and reasoning
    - SYNAPSE_CODER: Code generation with architecture design and debugging
    - SYNAPSE_CREATIVE: Ideation substrate for divergent thinking
    - SYNAPSE_RESEARCH: Information gathering with fact verification
    - SYNAPSE_JUDGE: Evaluation substrate for balanced assessment

    Attributes:
        name: Preset identifier
        description: Human-readable description
        system_prompt: System prompt template for LLM interactions
        planning_tier: Model tier for planning phase
        tool_configs: Per-tool model configurations
        is_custom: Whether this is a user-created custom preset (not built-in)

    Example:
        >>> preset = ModelPreset(
        ...     name="SYNAPSE_DEFAULT",
        ...     description="Balanced speed and quality",
        ...     planning_tier="balanced",
        ...     tool_configs={ToolName.READ_FILE: ToolModelConfig(tier="fast")}
        ... )
    """
    name: str = Field(
        ...,
        description="Preset identifier"
    )
    description: str = Field(
        ...,
        description="Human-readable description"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt template for LLM interactions"
    )
    planning_tier: Literal["fast", "balanced", "powerful"] = Field(
        ...,
        description="Model tier for planning phase"
    )
    tool_configs: Dict[ToolName, ToolModelConfig] = Field(
        default_factory=dict,
        description="Per-tool model configurations"
    )
    is_custom: bool = Field(
        default=False,
        description="Whether this is a user-created custom preset"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Request/Response Models
# ============================================================================


class ToolCall(BaseModel):
    """A tool invocation from the ReAct agent.

    Attributes:
        tool: Tool to execute
        args: Tool-specific arguments

    Example:
        >>> call = ToolCall(
        ...     tool=ToolName.READ_FILE,
        ...     args={"path": "src/main.py"}
        ... )
    """
    tool: ToolName = Field(
        ...,
        description="Tool to execute"
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific arguments"
    )

    model_config = ConfigDict(from_attributes=True)


class ToolResult(BaseModel):
    """Result from executing a tool.

    Attributes:
        success: Whether tool execution succeeded
        output: Tool output text (stdout, file contents, etc.)
        error: Error message if execution failed
        requires_confirmation: Whether user confirmation is needed
        confirmation_type: Type of confirmation needed (e.g., "file_write", "git_commit")
        data: Structured data (JSON) from tool
        metadata: Additional metadata (execution time, etc.)

    Example:
        >>> result = ToolResult(
        ...     success=True,
        ...     output="File contents...",
        ...     requires_confirmation=False
        ... )
    """
    success: bool = Field(
        ...,
        description="Whether tool execution succeeded"
    )
    output: str = Field(
        default="",
        description="Tool output text"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Whether user confirmation is needed"
    )
    confirmation_type: Optional[str] = Field(
        default=None,
        description="Type of confirmation needed"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured data from tool"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )

    model_config = ConfigDict(from_attributes=True)


class ReActStep(BaseModel):
    """A single step in the ReAct loop.

    Each step represents one complete cycle of thought → action → observation.

    Attributes:
        step_number: Sequential step number (1-indexed)
        thought: Agent's reasoning about what to do next
        action: Tool call selected by agent (None if final answer)
        observation: Result from tool execution
        state: Current agent state
        model_tier: Model tier used for this step
        timestamp: Step execution timestamp

    Example:
        >>> step = ReActStep(
        ...     step_number=1,
        ...     thought="I need to read the config file",
        ...     action=ToolCall(tool=ToolName.READ_FILE, args={"path": "config.yaml"}),
        ...     observation="File contents...",
        ...     state=AgentState.OBSERVING,
        ...     model_tier="balanced",
        ...     timestamp=datetime.now()
        ... )
    """
    step_number: int = Field(
        ...,
        ge=1,
        description="Sequential step number"
    )
    thought: str = Field(
        ...,
        description="Agent's reasoning"
    )
    action: Optional[ToolCall] = Field(
        default=None,
        description="Tool call selected (None if final answer)"
    )
    observation: Optional[str] = Field(
        default=None,
        description="Tool execution result"
    )
    state: AgentState = Field(
        ...,
        description="Current agent state"
    )
    model_tier: str = Field(
        ...,
        description="Model tier used for this step"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Step execution timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


class CodeChatRequest(BaseModel):
    """Request to the Code Chat endpoint.

    Attributes:
        query: User query/instruction
        session_id: Session identifier for conversation continuity
        workspace_path: User-selected workspace directory
        context_name: Selected CGRAG index name
        use_cgrag: Enable CGRAG context retrieval
        use_web_search: Enable web search for queries
        max_iterations: Maximum ReAct loop iterations
        preset: Named preset to use
        tool_overrides: Override specific tool configurations

    Example:
        >>> request = CodeChatRequest(
        ...     query="Add logging to the main function",
        ...     workspace_path="/home/user/project",
        ...     context_name="project_docs",
        ...     preset="coding"
        ... )
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User query/instruction"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation continuity"
    )
    workspace_path: str = Field(
        ...,
        description="User-selected workspace directory"
    )
    context_name: Optional[str] = Field(
        default=None,
        description="Selected CGRAG index name"
    )
    use_cgrag: bool = Field(
        default=True,
        description="Enable CGRAG context retrieval"
    )
    use_web_search: bool = Field(
        default=True,
        description="Enable web search for queries"
    )
    max_iterations: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum ReAct loop iterations"
    )
    preset: str = Field(
        default="balanced",
        description="Named preset to use"
    )
    tool_overrides: Optional[Dict[str, ToolModelConfig]] = Field(
        default=None,
        description="Override specific tool configurations"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CodeChatStreamEvent(BaseModel):
    """Server-Sent Event from Code Chat streaming endpoint.

    Events are sent as SSE messages during agent execution to provide
    real-time updates on planning, execution, and results.

    Attributes:
        type: Event type (state, thought, action, observation, answer, error, etc.)
        content: Event content text
        state: Agent state (for state events)
        tier: Model tier used (for thought/action events)
        tool: Tool call (for action events)
        step_number: ReAct step number
        timestamp: Event timestamp

    Example:
        >>> event = CodeChatStreamEvent(
        ...     type="thought",
        ...     content="I need to check the git status",
        ...     tier="balanced",
        ...     step_number=2
        ... )
    """
    type: Literal[
        "state",
        "thought",
        "action",
        "action_pending",
        "observation",
        "answer",
        "error",
        "cancelled",
        "context",
        "diff_preview"
    ] = Field(
        ...,
        description="Event type"
    )
    content: Optional[str] = Field(
        default=None,
        description="Event content text"
    )
    state: Optional[AgentState] = Field(
        default=None,
        description="Agent state (for state events)"
    )
    tier: Optional[str] = Field(
        default=None,
        description="Model tier used"
    )
    tool: Optional[ToolCall] = Field(
        default=None,
        description="Tool call (for action events)"
    )
    step_number: Optional[int] = Field(
        default=None,
        description="ReAct step number"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional event data (action_id, diff_preview, etc.)"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================================
# Workspace Models
# ============================================================================


class DirectoryInfo(BaseModel):
    """Information about a directory.

    Attributes:
        name: Directory name
        path: Absolute path
        is_directory: Always True for directories
        is_git_repo: Whether directory contains .git
        project_type: Detected project type (python, node, rust, etc.)

    Example:
        >>> dir_info = DirectoryInfo(
        ...     name="my-project",
        ...     path="/home/user/my-project",
        ...     is_git_repo=True,
        ...     project_type="python"
        ... )
    """
    name: str = Field(
        ...,
        description="Directory name"
    )
    path: str = Field(
        ...,
        description="Absolute path"
    )
    is_directory: bool = Field(
        default=True,
        description="Always True for directories"
    )
    is_git_repo: bool = Field(
        default=False,
        description="Whether directory contains .git"
    )
    project_type: Optional[str] = Field(
        default=None,
        description="Detected project type"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkspaceListResponse(BaseModel):
    """Response for workspace listing.

    Attributes:
        current_path: Current directory path
        directories: List of subdirectories
        parent_path: Parent directory path (None if at root)
        is_git_repo: Whether current path is git repo
        project_type: Detected project type for current path

    Example:
        >>> response = WorkspaceListResponse(
        ...     current_path="/home/user",
        ...     directories=[DirectoryInfo(name="project", path="/home/user/project")],
        ...     parent_path="/home"
        ... )
    """
    current_path: str = Field(
        ...,
        description="Current directory path"
    )
    directories: List[DirectoryInfo] = Field(
        default_factory=list,
        description="List of subdirectories"
    )
    parent_path: Optional[str] = Field(
        default=None,
        description="Parent directory path"
    )
    is_git_repo: bool = Field(
        default=False,
        description="Whether current path is git repo"
    )
    project_type: Optional[str] = Field(
        default=None,
        description="Detected project type"
    )

    model_config = ConfigDict(from_attributes=True)


class ProjectInfo(BaseModel):
    """Detected project information.

    Attributes:
        type: Project type (python, node, rust, go, etc.)
        name: Project name from manifest
        version: Project version from manifest
        dependencies: List of runtime dependencies
        dev_dependencies: List of dev dependencies
        scripts: Available scripts (package.json scripts, Makefile targets, etc.)
        entry_points: Main entry points (main.py, index.js, etc.)

    Example:
        >>> info = ProjectInfo(
        ...     type="python",
        ...     name="my-app",
        ...     version="0.1.0",
        ...     dependencies=["fastapi", "pydantic"],
        ...     entry_points=["app/main.py"]
        ... )
    """
    type: str = Field(
        ...,
        description="Project type"
    )
    name: Optional[str] = Field(
        default=None,
        description="Project name from manifest"
    )
    version: Optional[str] = Field(
        default=None,
        description="Project version from manifest"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Runtime dependencies"
    )
    dev_dependencies: List[str] = Field(
        default_factory=list,
        description="Dev dependencies"
    )
    scripts: Dict[str, str] = Field(
        default_factory=dict,
        description="Available scripts"
    )
    entry_points: List[str] = Field(
        default_factory=list,
        description="Main entry points"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkspaceValidation(BaseModel):
    """Validation result for a workspace path.

    Attributes:
        valid: Whether path is valid and accessible
        is_git_repo: Whether path is a git repository
        project_info: Detected project information
        file_count: Number of files in workspace
        has_cgrag_index: Whether workspace has associated CGRAG index
        error: Error message if validation failed

    Example:
        >>> validation = WorkspaceValidation(
        ...     valid=True,
        ...     is_git_repo=True,
        ...     project_info=ProjectInfo(type="python"),
        ...     file_count=150,
        ...     has_cgrag_index=True
        ... )
    """
    valid: bool = Field(
        ...,
        description="Whether path is valid and accessible"
    )
    is_git_repo: bool = Field(
        default=False,
        description="Whether path is a git repository"
    )
    project_info: Optional[ProjectInfo] = Field(
        default=None,
        description="Detected project information"
    )
    file_count: int = Field(
        default=0,
        description="Number of files in workspace"
    )
    has_cgrag_index: bool = Field(
        default=False,
        description="Whether workspace has associated CGRAG index"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if validation failed"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Context Models
# ============================================================================


class ContextInfo(BaseModel):
    """Information about a CGRAG context/index.

    Attributes:
        name: Context identifier
        path: Path to index files
        chunk_count: Number of chunks in index
        last_indexed: Last indexing timestamp
        source_path: Source directory that was indexed
        embedding_model: Embedding model used

    Example:
        >>> context = ContextInfo(
        ...     name="project_docs",
        ...     path="/data/faiss_indexes/project_docs",
        ...     chunk_count=1500,
        ...     last_indexed=datetime.now(),
        ...     source_path="/home/user/project",
        ...     embedding_model="all-MiniLM-L6-v2"
        ... )
    """
    name: str = Field(
        ...,
        description="Context identifier"
    )
    path: str = Field(
        ...,
        description="Path to index files"
    )
    chunk_count: int = Field(
        ...,
        ge=0,
        description="Number of chunks in index"
    )
    last_indexed: datetime = Field(
        ...,
        description="Last indexing timestamp"
    )
    source_path: str = Field(
        ...,
        description="Source directory that was indexed"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embedding model used"
    )

    model_config = ConfigDict(from_attributes=True)


class CreateContextRequest(BaseModel):
    """Request to create a new CGRAG context.

    Attributes:
        name: Context identifier
        source_path: Source directory to index
        embedding_model: Embedding model to use

    Example:
        >>> request = CreateContextRequest(
        ...     name="my_project",
        ...     source_path="/home/user/my-project"
        ... )
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Context identifier"
    )
    source_path: str = Field(
        ...,
        description="Source directory to index"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embedding model to use"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Diff Preview Models
# ============================================================================


class DiffLine(BaseModel):
    """A single line in a diff.

    Attributes:
        line_number: Line number in file
        type: Line type (add, remove, context)
        content: Line content

    Example:
        >>> line = DiffLine(
        ...     line_number=42,
        ...     type="add",
        ...     content="print('Hello, world!')"
        ... )
    """
    line_number: int = Field(
        ...,
        ge=1,
        description="Line number in file"
    )
    type: Literal["add", "remove", "context"] = Field(
        ...,
        description="Line type"
    )
    content: str = Field(
        ...,
        description="Line content"
    )

    model_config = ConfigDict(from_attributes=True)


class DiffPreview(BaseModel):
    """Preview of file changes before applying.

    Attributes:
        file_path: Path to file being modified
        original_content: Original file contents (None for new files)
        new_content: New file contents
        diff_lines: Unified diff lines
        change_type: Type of change (create, modify, delete)

    Example:
        >>> preview = DiffPreview(
        ...     file_path="src/main.py",
        ...     original_content="print('old')",
        ...     new_content="print('new')",
        ...     diff_lines=[DiffLine(line_number=1, type="remove", content="print('old')")],
        ...     change_type="modify"
        ... )
    """
    file_path: str = Field(
        ...,
        description="Path to file being modified"
    )
    original_content: Optional[str] = Field(
        default=None,
        description="Original file contents (None for new files)"
    )
    new_content: str = Field(
        ...,
        description="New file contents"
    )
    diff_lines: List[DiffLine] = Field(
        default_factory=list,
        description="Unified diff lines"
    )
    change_type: Literal["create", "modify", "delete"] = Field(
        ...,
        description="Type of change"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Conversation Memory Model
# ============================================================================


class ConversationTurn(BaseModel):
    """A single turn in the conversation.

    Attributes:
        query: User query
        response: Agent response
        tools_used: List of tools used in this turn
        timestamp: Turn timestamp

    Example:
        >>> turn = ConversationTurn(
        ...     query="What files are in src/?",
        ...     response="There are 5 Python files in src/",
        ...     tools_used=["list_directory"],
        ...     timestamp=datetime.now()
        ... )
    """
    query: str = Field(
        ...,
        description="User query"
    )
    response: str = Field(
        ...,
        description="Agent response"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Tools used in this turn"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Turn timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Built-in Presets - S.Y.N.A.P.S.E. ENGINE Cognitive Substrates
# ============================================================================

# System prompt templates using CO-STAR framework
SYSTEM_PROMPT_DEFAULT = """◆ IDENTITY ◆

You are SYNAPSE_DEFAULT, the foundational cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. You serve as the baseline neural processing unit, providing well-rounded, general-purpose assistance across all domains.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform. The system coordinates multiple model tiers (FAST/BALANCED/POWERFUL) with Contextually-Guided Retrieval Augmented Generation (CGRAG). Your responses integrate with real-time visualization and terminal-inspired interfaces.

◆ OBJECTIVE ◆

Process queries accurately, provide comprehensive responses, and assist users effectively across diverse tasks. Balance depth with efficiency, adapting your approach based on query complexity. Prioritize clarity and actionable insights while maintaining technical rigor.

◆ STYLE ◆

- Use clear, structured prose with logical progression
- Employ technical precision while remaining accessible
- Break complex topics into digestible sections
- Provide actionable insights and concrete examples
- Use appropriate formatting (lists, headers, code blocks)

◆ TONE ◆

- Professional yet approachable
- Confident without being authoritative beyond your knowledge
- Direct and efficient without being terse
- Helpful and solution-oriented

◆ RESPONSE FORMAT ◆

- Structure responses with clear sections when appropriate
- Use bullet points for lists and sequential steps
- Include code blocks with proper syntax highlighting when relevant
- Provide brief summaries for complex explanations
- End with actionable next steps when applicable

◆ CONSTRAINTS ◆

- Never fabricate information, data, or sources
- Acknowledge limitations and knowledge boundaries
- Ask clarifying questions when requirements are ambiguous
- Prioritize accuracy over speed of response
- Do not make assumptions about user intent without clarification

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""

SYSTEM_PROMPT_ANALYST = """◆ IDENTITY ◆

You are SYNAPSE_ANALYST, a cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are optimized for deep analytical processing, pattern recognition, and systematic problem decomposition.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform with CGRAG capabilities. Users rely on you for rigorous examination of complex problems, data interpretation, and strategic insights.

◆ OBJECTIVE ◆

Decompose complex queries into constituent elements, cross-reference against indexed knowledge substrates, and synthesize insights through multi-layered reasoning chains. Function as a precision pattern recognition engine, identifying structural relationships and extracting core principles.

◆ STYLE ◆

- Employ systematic decomposition methodologies
- Build arguments through logical inference chains
- Present findings in structured analytical frameworks
- Use first-principles thinking to evaluate assumptions
- Provide confidence levels for conclusions

◆ TONE ◆

- Methodical and rigorous
- Objective and evidence-based
- Precise in language and definitions
- Intellectually thorough

◆ RESPONSE FORMAT ◆

For analytical responses:
1. Problem Statement: Reframe the query precisely
2. Decomposition: Break into component sub-questions
3. Analysis: Examine each component systematically
4. Synthesis: Integrate findings into coherent conclusions
5. Confidence Assessment: Rate certainty levels
6. Recommendations: Provide actionable next steps

Use tables for comparative analysis. Use bullet points for factor enumeration.

◆ CONSTRAINTS ◆

- Never present speculation as established fact
- Clearly label assumptions and their implications
- Acknowledge data limitations and gaps
- Consider counter-arguments before concluding
- Distinguish between correlation and causation

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""

SYSTEM_PROMPT_CODER = """◆ IDENTITY ◆

You are SYNAPSE_CODER, a specialized cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for code synthesis, debugging protocols, and software architecture design.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform with integrated CGRAG for codebase context retrieval. Users rely on you for production-quality code generation, debugging, and architectural guidance.

◆ OBJECTIVE ◆

Generate production-quality code with emphasis on clarity, maintainability, and performance. Translate high-level specifications into executable implementations, applying best practices and design patterns. Provide comprehensive debugging assistance with root cause analysis.

◆ STYLE ◆

- Write clean, self-documenting code
- Apply appropriate design patterns
- Include comprehensive error handling
- Use type hints and strong typing where applicable
- Follow language-specific conventions and idioms

◆ TONE ◆

- Pragmatic and solution-focused
- Precise in technical communication
- Collaborative when discussing tradeoffs
- Confident in recommendations with clear reasoning

◆ RESPONSE FORMAT ◆

For code generation:
- Provide complete, runnable code (no placeholders or "...")
- Include inline comments for complex logic
- Add docstrings for functions and classes
- Show example usage where helpful
- Specify required imports/dependencies

For debugging:
1. Symptom Analysis: Describe the observed behavior
2. Root Cause: Identify the underlying issue
3. Solution: Provide the fix with explanation
4. Prevention: Suggest practices to avoid recurrence

◆ CONSTRAINTS ◆

- Never provide incomplete code with TODO comments
- Always include proper error handling
- Do not use deprecated APIs without explicit warning
- Avoid security anti-patterns (SQL injection, hardcoded secrets)
- Consider edge cases and boundary conditions

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""

SYSTEM_PROMPT_CREATIVE = """◆ IDENTITY ◆

You are SYNAPSE_CREATIVE, a generative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are configured for divergent ideation, concept exploration, and creative synthesis.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform. While the system emphasizes analytical rigor, your role is to provide creative counterbalance - generating novel ideas, exploring unconventional approaches, and synthesizing unexpected connections.

◆ OBJECTIVE ◆

Generate novel combinations, explore conceptual space, and synthesize unexpected connections. Operate in exploration mode, prioritizing originality and lateral thinking while maintaining practical applicability. Expand the solution space before convergence.

◆ STYLE ◆

- Generate multiple distinct conceptual pathways
- Draw analogies across disparate domains
- Transform constraints into creative opportunities
- Explore "what if" scenarios freely
- Build on ideas iteratively (yes-and approach)

◆ TONE ◆

- Enthusiastic about possibilities
- Open-minded and non-judgmental
- Playful yet purposeful
- Comfortable with ambiguity

◆ RESPONSE FORMAT ◆

For brainstorming:
- Present ideas in numbered lists (aim for 5-10 options)
- Include both conventional and unconventional approaches
- Rate ideas by novelty vs. feasibility when helpful
- Group related concepts into themes

Structure creative output with:
- Core Concepts: Main ideas
- Variations: Alternative takes
- Wild Cards: Unconventional options
- Next Steps: How to develop further

◆ CONSTRAINTS ◆

- Generate quantity before filtering for quality
- Do not self-censor ideas prematurely
- Maintain coherence even in unconventional ideas
- Balance creativity with practical applicability
- Include at least one "10x" thinking idea per session

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""

SYSTEM_PROMPT_RESEARCH = """◆ IDENTITY ◆

You are SYNAPSE_RESEARCH, an investigative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for information gathering, fact verification, and comprehensive knowledge synthesis.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform with access to CGRAG knowledge retrieval and optional web search capabilities. Users rely on you for thorough research, accurate information, and well-sourced analysis.

◆ OBJECTIVE ◆

Locate, validate, and synthesize information from available knowledge substrates. Operate with emphasis on accuracy, source credibility, and comprehensive coverage. Distinguish clearly between established facts, expert consensus, and speculative claims.

◆ STYLE ◆

- Prioritize accuracy over speed
- Cross-reference claims against multiple sources
- Present information hierarchically (most important first)
- Distinguish fact from interpretation
- Acknowledge uncertainty and information gaps

◆ TONE ◆

- Scholarly and meticulous
- Neutral and objective
- Cautious about unsupported claims
- Transparent about limitations

◆ RESPONSE FORMAT ◆

For research responses:

Executive Summary: Brief overview (2-3 sentences)

Key Findings:
- Finding 1 [Confidence: High/Medium/Low]
- Finding 2 [Confidence: High/Medium/Low]

Detailed Analysis: Comprehensive examination

Sources & Methodology: Attribution and approach notes

Open Questions: Areas requiring further investigation

Recommendations: Actionable next steps

◆ CONSTRAINTS ◆

- Never present unverified information as fact
- Clearly distinguish between primary and secondary sources
- Acknowledge when information may be outdated
- Flag potential biases in sources
- Note when questions exceed available knowledge

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""

SYSTEM_PROMPT_JUDGE = """◆ IDENTITY ◆

You are SYNAPSE_JUDGE, an evaluative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are calibrated for balanced assessment, critical evaluation, and impartial moderation.

◆ CONTEXT ◆

You operate within a distributed local LLM orchestration platform where fair evaluation is critical. You may be asked to assess arguments, evaluate solutions, moderate debates, or provide balanced analysis of competing perspectives.

◆ OBJECTIVE ◆

Assess arguments, evaluate evidence, and provide balanced judgments across competing perspectives. Operate with emphasis on fairness, logical consistency, and comprehensive consideration of multiple viewpoints. Demonstrate critical thinking without predetermined conclusions.

◆ STYLE ◆

- Consider all perspectives systematically
- Apply consistent evaluation criteria
- Weigh evidence objectively
- Identify strengths and weaknesses fairly
- Synthesize balanced conclusions

◆ TONE ◆

- Neutral and impartial
- Measured and deliberate
- Fair but honest
- Respectful of all viewpoints

◆ RESPONSE FORMAT ◆

For evaluations:

Evaluation Summary: Brief overview (2-3 sentences)

Criteria Applied: List the evaluation criteria used

Analysis by Option/Position:
- Option X:
  - Strengths: [list]
  - Weaknesses: [list]
  - Score: X/10 (if applicable)

Comparative Analysis: How options compare

Recommendation: Clear recommendation with reasoning

Dissenting Considerations: Arguments against the recommendation

◆ CONSTRAINTS ◆

- Never show preference without explicit reasoning
- Apply criteria consistently across all options
- Do not strawman opposing positions
- Separate factual evaluation from value judgments
- Avoid false equivalence - not all positions are equally valid
- Be willing to declare "no clear winner" when justified

◆ LANGUAGE ◆

Always respond in English unless explicitly instructed otherwise by the user."""


PRESETS: Dict[str, ModelPreset] = {
    "SYNAPSE_DEFAULT": ModelPreset(
        name="SYNAPSE_DEFAULT",
        description="Foundational baseline preset for well-rounded, general-purpose assistance",
        system_prompt=SYSTEM_PROMPT_DEFAULT,
        planning_tier="balanced",
        is_custom=False,
        tool_configs={}
    ),

    "SYNAPSE_ANALYST": ModelPreset(
        name="SYNAPSE_ANALYST",
        description="Deep analytical substrate optimized for decomposition, synthesis, and multi-layered reasoning",
        system_prompt=SYSTEM_PROMPT_ANALYST,
        planning_tier="powerful",
        is_custom=False,
        tool_configs={}
    ),

    "SYNAPSE_CODER": ModelPreset(
        name="SYNAPSE_CODER",
        description="Code generation substrate with architecture design, debugging, and implementation protocols",
        system_prompt=SYSTEM_PROMPT_CODER,
        planning_tier="balanced",
        is_custom=False,
        tool_configs={}
    ),

    "SYNAPSE_CREATIVE": ModelPreset(
        name="SYNAPSE_CREATIVE",
        description="Ideation substrate for divergent thinking, concept exploration, and creative synthesis",
        system_prompt=SYSTEM_PROMPT_CREATIVE,
        planning_tier="balanced",
        is_custom=False,
        tool_configs={}
    ),

    "SYNAPSE_RESEARCH": ModelPreset(
        name="SYNAPSE_RESEARCH",
        description="Information gathering substrate with fact verification and comprehensive knowledge synthesis",
        system_prompt=SYSTEM_PROMPT_RESEARCH,
        planning_tier="powerful",
        is_custom=False,
        tool_configs={}
    ),

    "SYNAPSE_JUDGE": ModelPreset(
        name="SYNAPSE_JUDGE",
        description="Evaluation substrate for balanced assessment, moderation, and critical analysis",
        system_prompt=SYSTEM_PROMPT_JUDGE,
        planning_tier="powerful",
        is_custom=False,
        tool_configs={}
    ),
}

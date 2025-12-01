/**
 * TypeScript types for Code Chat mode.
 *
 * Mirrors Pydantic models from backend/app/models/code_chat.py
 * Provides type safety for the Code Chat agentic coding assistant including
 * ReAct loop states, tool configurations, workspace management, and streaming events.
 */

// ============================================================================
// Enums and Union Types
// ============================================================================

/**
 * Agent state machine states for the ReAct loop.
 *
 * States define the current phase of agent execution:
 * - idle: Awaiting next query
 * - planning: Reasoning about next action
 * - executing: Running selected tool
 * - observing: Processing tool result and deciding next step
 * - completed: Task successfully finished
 * - error: Encountered unrecoverable error
 * - cancelled: User or system cancelled execution
 */
export type AgentState =
  | 'idle'
  | 'planning'
  | 'executing'
  | 'observing'
  | 'completed'
  | 'error'
  | 'cancelled';

/**
 * Model tier for query routing.
 */
export type ModelTier = 'fast' | 'balanced' | 'powerful';

/**
 * Available tools for the Code Chat agent.
 *
 * Tools are grouped by category:
 * - File Operations: read_file, write_file, list_directory, delete_file
 * - Code Search: search_code, grep_files
 * - Web Search: web_search
 * - Execution: run_python, run_shell
 * - Git: git_status, git_diff, git_log, git_commit, git_branch
 * - LSP: get_diagnostics, get_definitions, get_references, get_project_info
 */
export type ToolName =
  | 'read_file'
  | 'write_file'
  | 'list_directory'
  | 'delete_file'
  | 'search_code'
  | 'grep_files'
  | 'web_search'
  | 'run_python'
  | 'run_shell'
  | 'git_status'
  | 'git_diff'
  | 'git_log'
  | 'git_commit'
  | 'git_branch'
  | 'get_diagnostics'
  | 'get_definitions'
  | 'get_references'
  | 'get_project_info';

// ============================================================================
// Tool Configuration Models
// ============================================================================

/**
 * Model configuration for a specific tool.
 *
 * Defines which model tier to use and generation parameters
 * for executing a particular tool.
 */
export interface ToolModelConfig {
  /** Model tier to use for this tool */
  tier: ModelTier;
  /** Sampling temperature (0.0-2.0) */
  temperature?: number;
  /** Maximum tokens to generate (1-4096) */
  maxTokens?: number;
}

/**
 * Named collection of tool configurations for quick switching.
 *
 * Presets provide optimized configurations for different workflows:
 * - speed: Prioritize response time (all fast tier)
 * - balanced: Mix of fast/balanced tiers
 * - quality: Prioritize output quality (more powerful tier usage)
 * - coding: Optimized for code editing tasks
 * - research: Optimized for exploration and analysis
 */
export interface ModelPreset {
  /** Preset identifier */
  name: string;
  /** Human-readable description */
  description: string;
  /** System prompt template for LLM interactions (null if not defined) */
  systemPrompt?: string | null;
  /** Model tier for planning phase */
  planningTier: ModelTier;
  /** Per-tool model configurations */
  toolConfigs: Record<ToolName, ToolModelConfig>;
  /** Whether this is a user-created custom preset (not built-in) */
  isCustom: boolean;
}

// ============================================================================
// Workspace Models
// ============================================================================

/**
 * Information about a directory.
 */
export interface DirectoryInfo {
  /** Directory name */
  name: string;
  /** Absolute path */
  path: string;
  /** Always true for directories */
  isDirectory: boolean;
  /** Whether directory contains .git */
  isGitRepo: boolean;
  /** Detected project type (python, node, rust, etc.) */
  projectType: string | null;
}

/**
 * Response for workspace listing.
 */
export interface WorkspaceListResponse {
  /** Current directory path */
  currentPath: string;
  /** List of subdirectories */
  directories: DirectoryInfo[];
  /** Parent directory path (null if at root) */
  parentPath: string | null;
  /** Whether current path is git repo */
  isGitRepo: boolean;
  /** Detected project type for current path */
  projectType: string | null;
}

/**
 * Detected project information.
 */
export interface ProjectInfo {
  /** Project type (python, node, rust, go, etc.) */
  type: string;
  /** Project name from manifest */
  name: string | null;
  /** Project version from manifest */
  version: string | null;
  /** List of runtime dependencies */
  dependencies: string[];
  /** List of dev dependencies */
  devDependencies: string[];
  /** Available scripts (package.json scripts, Makefile targets, etc.) */
  scripts: Record<string, string>;
  /** Main entry points (main.py, index.js, etc.) */
  entryPoints: string[];
}

/**
 * Validation result for a workspace path.
 */
export interface WorkspaceValidation {
  /** Whether path is valid and accessible */
  valid: boolean;
  /** Whether path is a git repository */
  isGitRepo: boolean;
  /** Detected project information */
  projectInfo: ProjectInfo | null;
  /** Number of files in workspace */
  fileCount: number;
  /** Whether workspace has associated CGRAG index */
  hasCgragIndex: boolean;
  /** Error message if validation failed */
  error?: string;
}

// ============================================================================
// Context Models
// ============================================================================

/**
 * Information about a CGRAG context/index.
 */
export interface ContextInfo {
  /** Context identifier */
  name: string;
  /** Path to index files */
  path: string;
  /** Number of chunks in index */
  chunkCount: number;
  /** Last indexing timestamp */
  lastIndexed: string;
  /** Source directory that was indexed */
  sourcePath: string;
  /** Embedding model used */
  embeddingModel: string;
}

/**
 * Request to create a new CGRAG context.
 */
export interface CreateContextRequest {
  /** Context identifier */
  name: string;
  /** Source directory to index */
  sourcePath: string;
  /** Embedding model to use */
  embeddingModel?: string;
}

// ============================================================================
// Tool & Step Models
// ============================================================================

/**
 * A tool invocation from the ReAct agent.
 */
export interface ToolCall {
  /** Tool to execute */
  tool: ToolName;
  /** Tool-specific arguments */
  args: Record<string, unknown>;
}

/**
 * Result from executing a tool.
 */
export interface ToolResult {
  /** Whether tool execution succeeded */
  success: boolean;
  /** Tool output text (stdout, file contents, etc.) */
  output?: string;
  /** Error message if execution failed */
  error?: string;
  /** Structured data (JSON) from tool */
  data?: Record<string, unknown>;
  /** Additional metadata (execution time, etc.) */
  metadata?: Record<string, unknown>;
}

/**
 * A single step in the ReAct loop.
 *
 * Each step represents one complete cycle of thought → action → observation.
 */
export interface ReActStep {
  /** Sequential step number (1-indexed) */
  stepNumber: number;
  /** Agent's reasoning about what to do next */
  thought: string;
  /** Tool call selected by agent (undefined if final answer) */
  action?: ToolCall;
  /** Result from tool execution */
  observation?: string;
  /** Current agent state */
  state: AgentState;
  /** Model tier used for this step */
  modelTier: ModelTier;
  /** Step execution timestamp */
  timestamp: string;
}

// ============================================================================
// Request/Response Models
// ============================================================================

/**
 * Request to the Code Chat endpoint.
 */
export interface CodeChatRequest {
  /** User query/instruction */
  query: string;
  /** Session identifier for conversation continuity */
  sessionId?: string;
  /** User-selected workspace directory */
  workspacePath: string;
  /** Selected CGRAG index name */
  contextName?: string | null;
  /** Enable CGRAG context retrieval */
  useCgrag?: boolean;
  /** Enable web search for queries */
  useWebSearch?: boolean;
  /** Maximum ReAct loop iterations */
  maxIterations?: number;
  /** Named preset to use */
  preset?: string;
  /** Override specific tool configurations */
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
}

/**
 * Server-Sent Event from Code Chat streaming endpoint.
 *
 * Events are sent as SSE messages during agent execution to provide
 * real-time updates on planning, execution, and results.
 */
export interface CodeChatStreamEvent {
  /** Event type */
  type:
    | 'state'
    | 'thought'
    | 'action'
    | 'action_pending'
    | 'observation'
    | 'answer'
    | 'error'
    | 'cancelled'
    | 'context'
    | 'diff_preview';
  /** Event content text */
  content?: string;
  /** Agent state (for state events) */
  state?: AgentState;
  /** Model tier used (for thought/action events) */
  tier?: ModelTier;
  /** Tool call (for action events) */
  tool?: ToolCall;
  /** ReAct step number */
  stepNumber?: number;
  /** Event timestamp */
  timestamp: string;
  /** Additional event data (action_id, diff_preview, etc.) */
  data?: Record<string, unknown>;
}

// ============================================================================
// Conversation Models
// ============================================================================

/**
 * A single turn in the conversation.
 */
export interface ConversationTurn {
  /** User query */
  query: string;
  /** Agent response */
  response: string;
  /** List of tools used in this turn */
  toolsUsed: string[];
  /** Turn timestamp */
  timestamp: string;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Built-in preset names.
 */
export const BUILT_IN_PRESETS = ['speed', 'balanced', 'quality', 'coding', 'research'] as const;

/**
 * Built-in preset type.
 */
export type BuiltInPreset = typeof BUILT_IN_PRESETS[number];

/**
 * Default preset to use.
 */
export const DEFAULT_PRESET: BuiltInPreset = 'balanced';

/**
 * Default maximum iterations for ReAct loop.
 */
export const DEFAULT_MAX_ITERATIONS = 10;

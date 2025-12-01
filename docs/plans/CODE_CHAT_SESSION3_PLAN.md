# Code Chat Session 3 - API Router & Frontend Hooks

**Date:** 2025-11-29
**Status:** Execution Plan
**Estimated Time:** 4-6 hours (1 session)
**Related Documentation:**
- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Master implementation plan
- [CODE_CHAT_SESSION2_PLAN.md](./CODE_CHAT_SESSION2_PLAN.md) - Previous session plan
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history

---

## Executive Summary

Session 3 connects the Session 1 & 2 backend implementation to the frontend by creating:
1. **FastAPI Router** (`code_chat.py`) - 9 endpoints with SSE streaming for the query endpoint
2. **React Hooks** (4 hooks) - useCodeChat, useWorkspaces, useContexts, usePresets
3. **TypeScript Types** - Complete type definitions matching Pydantic models
4. **API Integration** - Endpoints and client updates

This session bridges the gap between the fully-implemented ReAct agent backend and the (future) frontend UI components.

---

## Completed Work (Sessions 1 & 2)

### Session 1 Files (2,114 lines)
| File | Lines | Purpose |
|------|-------|---------|
| [`backend/app/models/code_chat.py`](../../backend/app/models/code_chat.py) | 972 | All Pydantic models, 5 presets |
| [`backend/app/services/code_chat/__init__.py`](../../backend/app/services/code_chat/__init__.py) | 52 | Package exports |
| [`backend/app/services/code_chat/workspace.py`](../../backend/app/services/code_chat/workspace.py) | 556 | Workspace browsing/validation |
| [`backend/app/services/code_chat/context.py`](../../backend/app/services/code_chat/context.py) | 534 | CGRAG context management |

### Session 2 Files (2,983 lines)
| File | Lines | Purpose |
|------|-------|---------|
| [`backend/app/services/code_chat/tools/base.py`](../../backend/app/services/code_chat/tools/base.py) | 309 | BaseTool, ToolRegistry |
| [`backend/app/services/code_chat/tools/file_ops.py`](../../backend/app/services/code_chat/tools/file_ops.py) | 805 | Read/Write/List/Delete tools |
| [`backend/app/services/code_chat/tools/search.py`](../../backend/app/services/code_chat/tools/search.py) | 640 | CGRAG, WebSearch, Grep tools |
| [`backend/app/services/code_chat/tools/__init__.py`](../../backend/app/services/code_chat/tools/__init__.py) | 40 | Tool exports |
| [`backend/app/services/code_chat/memory.py`](../../backend/app/services/code_chat/memory.py) | 497 | ConversationMemory, MemoryManager |
| [`backend/app/services/code_chat/agent.py`](../../backend/app/services/code_chat/agent.py) | 732 | ReActAgent state machine |

---

## Session 3 Implementation Plan

### Phase 1: Backend Router (Estimated: 350-400 lines)

**File:** `backend/app/routers/code_chat.py`

**Agent Assignment:** @backend-architect

**Dependencies:**
- Models from [`app.models.code_chat`](../../backend/app/models/code_chat.py)
- Services from [`app.services.code_chat`](../../backend/app/services/code_chat/__init__.py)
- Existing patterns from [`app.routers.events`](../../backend/app/routers/events.py) (SSE)

**Endpoints to Implement:**

```
GET  /api/code-chat/workspaces            - List directories for workspace selection
POST /api/code-chat/workspaces/validate   - Validate workspace path
GET  /api/code-chat/contexts              - List CGRAG indexes
POST /api/code-chat/contexts/create       - Create new CGRAG index
POST /api/code-chat/contexts/{name}/refresh - Refresh existing index
GET  /api/code-chat/presets               - List available presets
GET  /api/code-chat/presets/{name}        - Get specific preset details
POST /api/code-chat/query                 - SSE streaming query endpoint
POST /api/code-chat/cancel/{session_id}   - Cancel active session
```

**Code Structure:**

```python
"""Code Chat API router with SSE streaming.

Provides endpoints for:
- Workspace browsing and validation
- CGRAG context management
- Preset management
- Query execution with SSE streaming
- Session cancellation

Author: Backend Architect
Phase: Code Chat Implementation (Session 3)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
import json

from app.models.code_chat import (
    WorkspaceListResponse, WorkspaceValidation, DirectoryInfo,
    ContextInfo, CreateContextRequest,
    ModelPreset, PRESETS,
    CodeChatRequest, CodeChatStreamEvent
)
from app.services.code_chat import (
    list_directories, get_parent_path, check_git_repo,
    detect_project_type, detect_project_info, is_valid_workspace,
    count_files, check_cgrag_index_exists,
    list_cgrag_indexes, get_context_info, create_cgrag_index,
    refresh_cgrag_index, delete_cgrag_index,
    ReActAgent
)
from app.services.code_chat.memory import MemoryManager
from app.services.code_chat.tools import ToolRegistry, ReadFileTool, WriteFileTool, ...

router = APIRouter(prefix="/api/code-chat", tags=["code-chat"])

# Global agent instance (initialized on first use)
_agent: Optional[ReActAgent] = None
_memory_manager: Optional[MemoryManager] = None
_tool_registry: Optional[ToolRegistry] = None

async def get_agent() -> ReActAgent:
    """Get or create the ReAct agent singleton."""
    global _agent, _memory_manager, _tool_registry
    # Lazy initialization pattern
    ...

# ============================================================================
# WORKSPACE ENDPOINTS
# ============================================================================

@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces(
    path: str = Query("/", description="Directory path to list")
) -> WorkspaceListResponse:
    """List directories available for workspace selection.

    Returns subdirectories of the given path, along with metadata
    about each (git repo status, project type, etc.).

    Args:
        path: Directory path to list (default: root)

    Returns:
        WorkspaceListResponse with directories and metadata
    """
    ...

@router.post("/workspaces/validate", response_model=WorkspaceValidation)
async def validate_workspace(
    path: str = Query(..., description="Workspace path to validate")
) -> WorkspaceValidation:
    """Validate a workspace path and return metadata.

    Checks if path is a valid workspace and returns:
    - Git repository status
    - Project info (type, name, dependencies)
    - File count
    - CGRAG index availability

    Args:
        path: Workspace path to validate

    Returns:
        WorkspaceValidation with all metadata
    """
    ...

# ============================================================================
# CONTEXT ENDPOINTS
# ============================================================================

@router.get("/contexts", response_model=List[ContextInfo])
async def list_contexts() -> List[ContextInfo]:
    """List available CGRAG indexes.

    Returns all CGRAG indexes with metadata including:
    - Chunk count
    - Last indexed timestamp
    - Source path
    - Embedding model used
    """
    ...

@router.post("/contexts/create", response_model=ContextInfo)
async def create_context(request: CreateContextRequest) -> ContextInfo:
    """Create a new CGRAG index from a directory.

    Indexes all code files in the source directory using
    the specified embedding model. Returns info about the
    created index.

    Args:
        request: CreateContextRequest with name, sourcePath, embeddingModel

    Returns:
        ContextInfo for the newly created index
    """
    ...

@router.post("/contexts/{name}/refresh", response_model=ContextInfo)
async def refresh_context(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context.

    Re-scans the source directory and updates the index
    with any new or modified files.

    Args:
        name: Context name to refresh

    Returns:
        Updated ContextInfo
    """
    ...

# ============================================================================
# PRESET ENDPOINTS
# ============================================================================

@router.get("/presets", response_model=List[ModelPreset])
async def get_presets() -> List[ModelPreset]:
    """Get all available presets.

    Returns both built-in presets (speed, balanced, quality,
    coding, research) and any custom presets.
    """
    return list(PRESETS.values())

@router.get("/presets/{name}", response_model=ModelPreset)
async def get_preset(name: str) -> ModelPreset:
    """Get a specific preset by name.

    Args:
        name: Preset name

    Returns:
        ModelPreset configuration

    Raises:
        404: Preset not found
    """
    if name not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return PRESETS[name]

# ============================================================================
# QUERY ENDPOINT (SSE STREAMING)
# ============================================================================

@router.post("/query")
async def query(request: CodeChatRequest) -> StreamingResponse:
    """Execute Code Chat query with SSE streaming.

    Returns Server-Sent Events for real-time updates:
    - state: Agent state changes (planning, executing, observing)
    - thought: Agent reasoning
    - action: Tool execution
    - observation: Tool result
    - answer: Final response
    - error: Error occurred
    - cancelled: Session cancelled
    - context: CGRAG context retrieved
    - diff_preview: File diff for write operations

    The SSE format is:
    ```
    data: {"type": "thought", "content": "...", "stepNumber": 1}

    data: {"type": "action", "tool": {...}, "stepNumber": 1}

    data: {"type": "observation", "content": "...", "stepNumber": 1}

    data: {"type": "answer", "content": "...", "state": "completed"}
    ```

    Args:
        request: CodeChatRequest with query and configuration

    Returns:
        StreamingResponse with SSE events
    """
    agent = await get_agent()

    async def event_stream():
        try:
            async for event in agent.run(request):
                # Format as SSE
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-ID": request.session_id or "new"
        }
    )

@router.post("/cancel/{session_id}")
async def cancel_session(session_id: str) -> dict:
    """Cancel an active Code Chat session.

    Sets the cancellation flag for the session, which will be
    checked on the next iteration of the ReAct loop.

    Args:
        session_id: Session ID to cancel

    Returns:
        {"success": bool, "session_id": str}
    """
    agent = await get_agent()
    cancelled = agent.cancel(session_id)
    return {"success": cancelled, "session_id": session_id}
```

**Integration Points:**
1. Add router import to [`backend/app/main.py`](../../backend/app/main.py)
2. Register router with `app.include_router(code_chat.router, tags=["code-chat"])`
3. Initialize MemoryManager in lifespan (or lazy init)
4. Pass ModelSelector to agent for LLM calls

---

### Phase 2: TypeScript Types (Estimated: 150-180 lines)

**File:** `frontend/src/types/codeChat.ts`

**Agent Assignment:** @frontend-engineer

**Type Definitions:**

```typescript
/**
 * TypeScript types for Code Chat mode.
 *
 * Mirrors Pydantic models from backend/app/models/code_chat.py
 */

// ============================================================================
// Enums
// ============================================================================

export type AgentState =
  | 'idle'
  | 'planning'
  | 'executing'
  | 'observing'
  | 'completed'
  | 'error'
  | 'cancelled';

export type ModelTier = 'fast' | 'balanced' | 'powerful';

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
// Tool Configuration
// ============================================================================

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

// ============================================================================
// Workspace Types
// ============================================================================

export interface DirectoryInfo {
  name: string;
  path: string;
  isDirectory: boolean;
  isGitRepo: boolean;
  projectType: string | null;
}

export interface WorkspaceListResponse {
  currentPath: string;
  directories: DirectoryInfo[];
  parentPath: string | null;
  isGitRepo: boolean;
  projectType: string | null;
}

export interface ProjectInfo {
  type: string;
  name: string | null;
  version: string | null;
  dependencies: string[];
  devDependencies: string[];
  scripts: Record<string, string>;
  entryPoints: string[];
}

export interface WorkspaceValidation {
  valid: boolean;
  isGitRepo: boolean;
  projectInfo: ProjectInfo | null;
  fileCount: number;
  hasCgragIndex: boolean;
  error?: string;
}

// ============================================================================
// Context Types
// ============================================================================

export interface ContextInfo {
  name: string;
  path: string;
  chunkCount: number;
  lastIndexed: string;
  sourcePath: string;
  embeddingModel: string;
}

export interface CreateContextRequest {
  name: string;
  sourcePath: string;
  embeddingModel?: string;
}

// ============================================================================
// Tool & Step Types
// ============================================================================

export interface ToolCall {
  tool: ToolName;
  args: Record<string, unknown>;
}

export interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
  data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface ReActStep {
  stepNumber: number;
  thought: string;
  action?: ToolCall;
  observation?: string;
  state: AgentState;
  modelTier: ModelTier;
  timestamp: string;
}

// ============================================================================
// Request/Response Types
// ============================================================================

export interface CodeChatRequest {
  query: string;
  sessionId?: string;
  workspacePath: string;
  contextName?: string | null;
  useCgrag?: boolean;
  useWebSearch?: boolean;
  maxIterations?: number;
  preset?: string;
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
}

export interface CodeChatStreamEvent {
  type: 'state' | 'thought' | 'action' | 'observation' | 'answer' | 'error' | 'cancelled' | 'context' | 'diff_preview';
  content?: string;
  state?: AgentState;
  tier?: ModelTier;
  tool?: ToolCall;
  stepNumber?: number;
  timestamp: string;
}

// ============================================================================
// Conversation Types
// ============================================================================

export interface ConversationTurn {
  query: string;
  response: string;
  toolsUsed: string[];
  timestamp: string;
}

// ============================================================================
// Constants
// ============================================================================

export const BUILT_IN_PRESETS = ['speed', 'balanced', 'quality', 'coding', 'research'] as const;
export type BuiltInPreset = typeof BUILT_IN_PRESETS[number];

export const DEFAULT_PRESET: BuiltInPreset = 'balanced';
export const DEFAULT_MAX_ITERATIONS = 10;
```

---

### Phase 3: React Hooks (Estimated: 250-300 lines)

**Files:**
1. `frontend/src/hooks/useCodeChat.ts` (~120 lines)
2. `frontend/src/hooks/useWorkspaces.ts` (~50 lines)
3. `frontend/src/hooks/useContexts.ts` (~60 lines)
4. `frontend/src/hooks/usePresets.ts` (~30 lines)

**Agent Assignment:** @frontend-engineer

#### useCodeChat.ts (SSE Streaming Hook)

```typescript
/**
 * React hook for Code Chat SSE streaming.
 *
 * Handles:
 * - SSE connection to /api/code-chat/query
 * - Event parsing and state updates
 * - Step accumulation
 * - Cancellation support
 * - Error handling
 */

import { useState, useCallback, useRef } from 'react';
import {
  CodeChatRequest,
  CodeChatStreamEvent,
  ReActStep,
  AgentState,
} from '../types/codeChat';

interface UseCodeChatResult {
  /** Accumulated ReAct steps */
  steps: ReActStep[];
  /** Current agent state */
  currentState: AgentState;
  /** Final answer (when completed) */
  answer: string | null;
  /** Error message (when error state) */
  error: string | null;
  /** Whether query is in progress */
  isLoading: boolean;
  /** CGRAG context retrieved */
  context: string | null;
  /** Submit a new query */
  submit: (request: CodeChatRequest) => Promise<void>;
  /** Cancel current query */
  cancel: () => void;
  /** Reset state for new query */
  reset: () => void;
}

export function useCodeChat(): UseCodeChatResult {
  const [steps, setSteps] = useState<ReActStep[]>([]);
  const [currentState, setCurrentState] = useState<AgentState>('idle');
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const currentStepRef = useRef<Partial<ReActStep>>({});

  const handleEvent = useCallback((event: CodeChatStreamEvent) => {
    switch (event.type) {
      case 'state':
        if (event.state) {
          setCurrentState(event.state);
        }
        break;

      case 'thought':
        // Start new step
        currentStepRef.current = {
          stepNumber: event.stepNumber || steps.length + 1,
          thought: event.content || '',
          state: 'planning',
          modelTier: event.tier || 'balanced',
          timestamp: event.timestamp
        };
        break;

      case 'action':
        // Add action to current step
        if (event.tool) {
          currentStepRef.current.action = event.tool;
        }
        break;

      case 'observation':
        // Complete step and add to list
        const completedStep: ReActStep = {
          ...(currentStepRef.current as ReActStep),
          observation: event.content,
          state: 'observing'
        };
        setSteps(prev => [...prev, completedStep]);
        currentStepRef.current = {};
        break;

      case 'context':
        setContext(event.content || null);
        break;

      case 'answer':
        setAnswer(event.content || null);
        setCurrentState('completed');
        setIsLoading(false);
        break;

      case 'error':
        setError(event.content || 'Unknown error');
        setCurrentState('error');
        setIsLoading(false);
        break;

      case 'cancelled':
        setCurrentState('cancelled');
        setIsLoading(false);
        break;
    }
  }, [steps.length]);

  const submit = useCallback(async (request: CodeChatRequest) => {
    // Reset state
    setSteps([]);
    setAnswer(null);
    setError(null);
    setContext(null);
    setCurrentState('planning');
    setIsLoading(true);
    currentStepRef.current = {};

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/code-chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Get session ID from header
      sessionIdRef.current = response.headers.get('X-Session-ID');

      // Read SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: CodeChatStreamEvent = JSON.parse(line.slice(6));
              handleEvent(event);
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setCurrentState('cancelled');
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setCurrentState('error');
      }
    } finally {
      setIsLoading(false);
    }
  }, [handleEvent]);

  const cancel = useCallback(() => {
    // Abort fetch
    abortControllerRef.current?.abort();

    // Also call cancel endpoint if we have a session
    if (sessionIdRef.current) {
      fetch(`/api/code-chat/cancel/${sessionIdRef.current}`, { method: 'POST' })
        .catch(console.error);
    }

    setCurrentState('cancelled');
    setIsLoading(false);
  }, []);

  const reset = useCallback(() => {
    setSteps([]);
    setAnswer(null);
    setError(null);
    setContext(null);
    setCurrentState('idle');
    setIsLoading(false);
    currentStepRef.current = {};
  }, []);

  return {
    steps,
    currentState,
    answer,
    error,
    context,
    isLoading,
    submit,
    cancel,
    reset
  };
}
```

#### useWorkspaces.ts

```typescript
/**
 * React hooks for workspace browsing and validation.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import {
  WorkspaceListResponse,
  WorkspaceValidation
} from '../types/codeChat';

/**
 * Hook for fetching directory listing.
 *
 * @param path - Directory path to list (default: '/')
 * @returns Query result with directory listing
 */
export function useWorkspaces(path: string = '/'): UseQueryResult<WorkspaceListResponse> {
  return useQuery({
    queryKey: ['workspaces', path],
    queryFn: async (): Promise<WorkspaceListResponse> => {
      const response = await apiClient.get('/code-chat/workspaces', {
        params: { path }
      });
      return response.data;
    },
    staleTime: 30000, // Cache for 30 seconds
  });
}

/**
 * Hook for validating a workspace path.
 *
 * @param path - Workspace path to validate
 * @returns Query result with validation details
 */
export function useWorkspaceValidation(
  path: string
): UseQueryResult<WorkspaceValidation> {
  return useQuery({
    queryKey: ['workspace-validation', path],
    queryFn: async (): Promise<WorkspaceValidation> => {
      const response = await apiClient.post('/code-chat/workspaces/validate', null, {
        params: { path }
      });
      return response.data;
    },
    enabled: !!path && path.length > 0,
    staleTime: 60000, // Cache for 1 minute
  });
}
```

#### useContexts.ts

```typescript
/**
 * React hooks for CGRAG context management.
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { ContextInfo, CreateContextRequest } from '../types/codeChat';

/**
 * Hook for fetching available CGRAG contexts.
 *
 * @returns Query result with list of contexts
 */
export function useContexts(): UseQueryResult<ContextInfo[]> {
  return useQuery({
    queryKey: ['contexts'],
    queryFn: async (): Promise<ContextInfo[]> => {
      const response = await apiClient.get('/code-chat/contexts');
      return response.data;
    },
    staleTime: 60000, // Cache for 1 minute
  });
}

/**
 * Hook for creating a new CGRAG context.
 *
 * @returns Mutation for creating context
 */
export function useCreateContext(): UseMutationResult<ContextInfo, Error, CreateContextRequest> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateContextRequest): Promise<ContextInfo> => {
      const response = await apiClient.post('/code-chat/contexts/create', request);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    }
  });
}

/**
 * Hook for refreshing an existing CGRAG context.
 *
 * @returns Mutation for refreshing context
 */
export function useRefreshContext(): UseMutationResult<ContextInfo, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (name: string): Promise<ContextInfo> => {
      const response = await apiClient.post(`/code-chat/contexts/${name}/refresh`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    }
  });
}
```

#### usePresets.ts

```typescript
/**
 * React hook for preset management.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { ModelPreset } from '../types/codeChat';

/**
 * Hook for fetching all available presets.
 *
 * @returns Query result with list of presets
 */
export function usePresets(): UseQueryResult<ModelPreset[]> {
  return useQuery({
    queryKey: ['presets'],
    queryFn: async (): Promise<ModelPreset[]> => {
      const response = await apiClient.get('/code-chat/presets');
      return response.data;
    },
    staleTime: 300000, // Cache for 5 minutes (presets rarely change)
  });
}

/**
 * Hook for fetching a specific preset.
 *
 * @param name - Preset name to fetch
 * @returns Query result with preset configuration
 */
export function usePreset(name: string): UseQueryResult<ModelPreset> {
  return useQuery({
    queryKey: ['presets', name],
    queryFn: async (): Promise<ModelPreset> => {
      const response = await apiClient.get(`/code-chat/presets/${name}`);
      return response.data;
    },
    enabled: !!name,
    staleTime: 300000, // Cache for 5 minutes
  });
}
```

---

### Phase 4: API Endpoint Updates (Estimated: 15 lines)

**File:** [`frontend/src/api/endpoints.ts`](../../frontend/src/api/endpoints.ts)

**Add to existing endpoints object:**

```typescript
codeChat: {
  workspaces: 'code-chat/workspaces',
  validateWorkspace: 'code-chat/workspaces/validate',
  contexts: 'code-chat/contexts',
  createContext: 'code-chat/contexts/create',
  refreshContext: (name: string) => `code-chat/contexts/${name}/refresh`,
  presets: 'code-chat/presets',
  preset: (name: string) => `code-chat/presets/${name}`,
  query: 'code-chat/query',
  cancel: (sessionId: string) => `code-chat/cancel/${sessionId}`,
},
```

---

### Phase 5: Backend Integration (Estimated: 10 lines)

**File:** [`backend/app/main.py`](../../backend/app/main.py)

**Changes:**

1. Add import (line ~31):
```python
from app.routers import health, models, query, admin, settings, proxy, events, orchestrator, metrics, pipeline, context, timeseries, topology, logs, code_chat
```

2. Register router (after line ~532):
```python
app.include_router(code_chat.router, tags=["code-chat"])
```

---

## Implementation Order

| Order | Task | File | Lines | Agent |
|-------|------|------|-------|-------|
| 1 | TypeScript types | `frontend/src/types/codeChat.ts` | ~180 | @frontend-engineer |
| 2 | API endpoints | `frontend/src/api/endpoints.ts` | ~15 | @frontend-engineer |
| 3 | Backend router | `backend/app/routers/code_chat.py` | ~400 | @backend-architect |
| 4 | useWorkspaces hook | `frontend/src/hooks/useWorkspaces.ts` | ~50 | @frontend-engineer |
| 5 | useContexts hook | `frontend/src/hooks/useContexts.ts` | ~70 | @frontend-engineer |
| 6 | usePresets hook | `frontend/src/hooks/usePresets.ts` | ~40 | @frontend-engineer |
| 7 | useCodeChat hook | `frontend/src/hooks/useCodeChat.ts` | ~140 | @frontend-engineer |
| 8 | Backend integration | `backend/app/main.py` | ~5 | @backend-architect |

**Total Estimated Lines:** ~900

---

## Testing Checklist

### Backend Tests
- [ ] GET /api/code-chat/workspaces returns directory listing
- [ ] GET /api/code-chat/workspaces with path param navigates correctly
- [ ] POST /api/code-chat/workspaces/validate returns workspace info
- [ ] POST /api/code-chat/workspaces/validate handles invalid paths
- [ ] GET /api/code-chat/contexts returns CGRAG indexes (empty initially)
- [ ] POST /api/code-chat/contexts/create creates new index
- [ ] POST /api/code-chat/contexts/create handles missing source path
- [ ] POST /api/code-chat/contexts/{name}/refresh refreshes index
- [ ] POST /api/code-chat/contexts/{name}/refresh handles unknown index
- [ ] GET /api/code-chat/presets returns all 5 presets
- [ ] GET /api/code-chat/presets/{name} returns specific preset
- [ ] GET /api/code-chat/presets/{name} returns 404 for unknown
- [ ] POST /api/code-chat/query streams SSE events
- [ ] POST /api/code-chat/query handles missing workspace
- [ ] POST /api/code-chat/cancel/{session_id} cancels session
- [ ] POST /api/code-chat/cancel/{session_id} handles unknown session

### Frontend Tests
- [ ] useWorkspaces fetches and caches directory data
- [ ] useWorkspaces refetches on path change
- [ ] useWorkspaceValidation skips fetch when path empty
- [ ] useContexts fetches and caches context data
- [ ] useCreateContext invalidates cache on success
- [ ] useRefreshContext invalidates cache on success
- [ ] usePresets fetches and caches preset data
- [ ] useCodeChat parses SSE events correctly
- [ ] useCodeChat accumulates steps correctly
- [ ] useCodeChat handles thought -> action -> observation flow
- [ ] useCodeChat sets answer on completion
- [ ] useCodeChat handles errors gracefully
- [ ] useCodeChat.cancel aborts fetch and calls API
- [ ] useCodeChat.reset clears all state

### Integration Tests
- [ ] Full query flow from submit to answer
- [ ] Cancellation mid-execution
- [ ] Error handling in ReAct loop
- [ ] Workspace change during session
- [ ] Context creation and immediate use
- [ ] Preset change between queries

---

## Key Design Decisions

### 1. SSE vs WebSocket
**Decision:** Use SSE (Server-Sent Events)
**Rationale:**
- Simpler implementation (no bidirectional needed)
- Standard HTTP POST with streaming response
- Better for one-way server-to-client updates
- Consistent with existing patterns in the codebase
- Native browser support via EventSource (though we use fetch for POST)

### 2. Lazy Agent Initialization
**Decision:** Initialize agent on first request
**Rationale:**
- Avoids blocking startup
- Memory manager and tool registry created on demand
- Reduces startup time when Code Chat not used
- Allows workspace-specific tool initialization

### 3. Step Accumulation
**Decision:** Build steps incrementally from events
**Rationale:**
- thought event starts new step
- action event adds action to current step
- observation event completes step
- Matches ReAct loop structure from agent.py

### 4. Session Cancellation
**Decision:** Dual approach (abort + API call)
**Rationale:**
- AbortController cancels fetch immediately
- API call ensures backend cleanup
- Handles both client and server state
- Prevents orphaned sessions

### 5. Query vs Mutation for Hooks
**Decision:** Use Query for reads, Mutation for writes
**Rationale:**
- Follows TanStack Query best practices
- Automatic cache invalidation on mutations
- Proper loading/error states
- Consistent with existing hook patterns

---

## Files Summary

### New Files (6)
| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/routers/code_chat.py` | ~400 | API router with 9 endpoints |
| `frontend/src/types/codeChat.ts` | ~180 | TypeScript type definitions |
| `frontend/src/hooks/useCodeChat.ts` | ~140 | SSE streaming hook |
| `frontend/src/hooks/useWorkspaces.ts` | ~50 | Workspace browsing hooks |
| `frontend/src/hooks/useContexts.ts` | ~70 | Context management hooks |
| `frontend/src/hooks/usePresets.ts` | ~40 | Preset fetching hook |

### Modified Files (2)
| File | Changes |
|------|---------|
| [`backend/app/main.py`](../../backend/app/main.py) | Add router import and registration |
| [`frontend/src/api/endpoints.ts`](../../frontend/src/api/endpoints.ts) | Add code-chat endpoints |

---

## Dependencies & Prerequisites

### Backend
- Session 1 & 2 code must be complete and error-free
- Model selector must be available (currently NotImplementedError in agent.py)
- CGRAG service must be functional

### Frontend
- TanStack Query configured (already present)
- Axios client configured (already present)
- TypeScript strict mode enabled (already present)

### Known Issues to Address
1. `agent.py:669` - `_call_llm` raises `NotImplementedError`
   - Needs ModelSelector integration
   - Can stub for initial testing with mock responses

2. Tool registry initialization
   - Need to create tools with workspace_root
   - Workspace changes require re-initialization or workspace-aware tools

---

## Next Session (Session 4)

After Session 3, the remaining work will be:

1. **Frontend UI Components** (Session 4)
   - CodeChatPage component
   - WorkspaceSelector component
   - ContextSelector component
   - ReActStepVisualization component
   - DiffPreview component
   - Terminal-styled output display

2. **LLM Integration** (Session 4 or 5)
   - Implement _call_llm with ModelSelector
   - Add streaming token output (if desired)
   - Test with actual models

3. **Testing & Polish** (Session 5)
   - Unit tests for backend endpoints
   - Unit tests for frontend hooks
   - E2E tests with Playwright
   - Error handling improvements
   - Performance optimization

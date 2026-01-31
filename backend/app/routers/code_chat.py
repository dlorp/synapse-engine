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

import asyncio
import logging
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.models.code_chat import (
    WorkspaceListResponse,
    WorkspaceValidation,
    ContextInfo,
    CreateContextRequest,
    ModelPreset,
    CodeChatRequest,
    CodeChatStreamEvent,
)
from app.services.code_chat import (
    list_directories,
    get_parent_path,
    check_git_repo,
    detect_project_type,
    detect_project_info,
    is_valid_workspace,
    count_files,
    check_cgrag_index_exists,
    validate_path,
    list_cgrag_indexes,
    get_context_info,
    create_cgrag_index,
    refresh_cgrag_index,
    ReActAgent,
)
from app.services.code_chat.memory import MemoryManager
from app.services.code_chat.tools.base import ToolRegistry

# Import all tools for registration
from app.services.code_chat.tools.file_ops import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from app.services.code_chat.tools.search import (
    SearchCodeTool,
    GrepFilesTool,
    WebSearchTool,
)
from app.services.code_chat.tools.git import (
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitCommitTool,
    GitBranchTool,
)
from app.services.code_chat.tools.lsp import (
    GetDiagnosticsTool,
    GetDefinitionsTool,
    GetReferencesTool,
    GetProjectInfoTool,
)
from app.services.code_chat.preset_store import preset_store

router = APIRouter(prefix="/api/code-chat", tags=["code-chat"])
logger = logging.getLogger(__name__)

# Global instances (initialized on first use - lazy loading)
_agent: Optional[ReActAgent] = None
_memory_manager: Optional[MemoryManager] = None
_tool_registry: Optional[ToolRegistry] = None


async def get_agent(request: Request) -> ReActAgent:
    """Get or create the ReAct agent singleton.

    Lazy initialization pattern - agent is created on first request.
    Requires model_selector from app.state.

    Args:
        request: FastAPI request for accessing app.state

    Returns:
        ReActAgent instance

    Raises:
        RuntimeError: If model_selector not found in app.state
    """
    global _agent, _memory_manager, _tool_registry

    if _agent is not None:
        return _agent

    logger.info("Initializing Code Chat agent (lazy load)...")

    # Get model_selector from app.state
    model_selector = getattr(request.app.state, "model_selector", None)
    if model_selector is None:
        raise RuntimeError(
            "model_selector not found in app.state - ensure it's initialized in lifespan"
        )

    # Initialize memory manager
    _memory_manager = MemoryManager()
    logger.info("MemoryManager initialized")

    # Initialize tool registry
    _tool_registry = ToolRegistry()

    # Register tools
    # File operations
    _tool_registry.register(ReadFileTool(workspace_root="/workspace"))
    _tool_registry.register(WriteFileTool(workspace_root="/workspace"))
    _tool_registry.register(ListDirectoryTool(workspace_root="/workspace"))
    _tool_registry.register(DeleteFileTool(workspace_root="/workspace"))

    # Search tools
    _tool_registry.register(SearchCodeTool(workspace_root="/workspace"))
    _tool_registry.register(GrepFilesTool(workspace_root="/workspace"))
    _tool_registry.register(WebSearchTool())

    # Git tools
    _tool_registry.register(GitStatusTool(workspace_root="/workspace"))
    _tool_registry.register(GitDiffTool(workspace_root="/workspace"))
    _tool_registry.register(GitLogTool(workspace_root="/workspace"))
    _tool_registry.register(GitCommitTool(workspace_root="/workspace"))
    _tool_registry.register(GitBranchTool(workspace_root="/workspace"))

    # LSP/IDE tools
    _tool_registry.register(GetDiagnosticsTool(workspace_root="/workspace"))
    _tool_registry.register(GetDefinitionsTool(workspace_root="/workspace"))
    _tool_registry.register(GetReferencesTool(workspace_root="/workspace"))
    _tool_registry.register(GetProjectInfoTool(workspace_root="/workspace"))

    logger.info(f"ToolRegistry initialized with {len(_tool_registry.list_tools())} tools")

    # Initialize agent
    _agent = ReActAgent(
        model_selector=model_selector,
        tool_registry=_tool_registry,
        memory_manager=_memory_manager,
    )

    logger.info("ReActAgent initialized successfully")

    return _agent


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

    Raises:
        HTTPException: 400 if path is invalid or not allowed
        HTTPException: 500 if listing fails
    """
    logger.info(f"Listing workspaces at path: {path}")

    # Validate path
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        logger.warning(f"Invalid workspace path: {path} - {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # List directories
        directories = await list_directories(path)

        # Get parent path
        parent = await get_parent_path(path)

        # Check if current path is git repo
        is_git = await check_git_repo(path)

        # Detect project type
        project_type = await detect_project_type(path)

        return WorkspaceListResponse(
            current_path=path,
            directories=directories,
            parent_path=parent,
            is_git_repo=is_git,
            project_type=project_type,
        )

    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to list directories: {str(e)}"
        )


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
    logger.info(f"Validating workspace: {path}")

    # Validate path security
    is_valid_path, error_msg = validate_path(path)
    if not is_valid_path:
        logger.warning(f"Invalid workspace path: {path} - {error_msg}")
        return WorkspaceValidation(valid=False, error=error_msg)

    try:
        # Check if valid workspace
        is_valid = await is_valid_workspace(path)
        if not is_valid:
            return WorkspaceValidation(
                valid=False, error="Path is not a valid workspace directory"
            )

        # Gather metadata
        is_git = await check_git_repo(path)
        project_info = await detect_project_info(path)
        file_count = await count_files(path)
        has_index = await check_cgrag_index_exists(path)

        return WorkspaceValidation(
            valid=True,
            is_git_repo=is_git,
            project_info=project_info,
            file_count=file_count,
            has_cgrag_index=has_index,
        )

    except Exception as e:
        logger.error(f"Workspace validation failed: {e}", exc_info=True)
        return WorkspaceValidation(
            valid=False, error=f"Validation error: {str(e)}"
        )


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

    Returns:
        List of ContextInfo objects

    Raises:
        HTTPException: 500 if listing fails
    """
    logger.info("Listing CGRAG contexts")

    try:
        contexts = await list_cgrag_indexes()
        logger.info(f"Found {len(contexts)} CGRAG contexts")
        return contexts

    except Exception as e:
        logger.error(f"Failed to list contexts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to list contexts: {str(e)}"
        )


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

    Raises:
        HTTPException: 400 if source path invalid
        HTTPException: 409 if context already exists
        HTTPException: 500 if indexing fails
    """
    logger.info(f"Creating CGRAG context: {request.name} from {request.source_path}")

    # Validate source path
    is_valid, error_msg = validate_path(request.source_path)
    if not is_valid:
        logger.warning(f"Invalid source path: {request.source_path} - {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # Check if context already exists
        existing = await get_context_info(request.name)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Context '{request.name}' already exists",
            )

        # Create index
        context_info = await create_cgrag_index(
            name=request.name,
            source_path=request.source_path,
            embedding_model=request.embedding_model,
        )

        logger.info(
            f"Created CGRAG context '{request.name}' with {context_info.chunk_count} chunks"
        )

        return context_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to create context: {str(e)}"
        )


@router.post("/contexts/{name}/refresh", response_model=ContextInfo)
async def refresh_context(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context.

    Re-scans the source directory and updates the index
    with any new or modified files.

    Args:
        name: Context name to refresh

    Returns:
        Updated ContextInfo

    Raises:
        HTTPException: 404 if context not found
        HTTPException: 500 if refresh fails
    """
    logger.info(f"Refreshing CGRAG context: {name}")

    try:
        # Check if context exists
        existing = await get_context_info(name)
        if existing is None:
            raise HTTPException(
                status_code=404, detail=f"Context '{name}' not found"
            )

        # Refresh index
        context_info = await refresh_cgrag_index(name)

        logger.info(
            f"Refreshed CGRAG context '{name}' - {context_info.chunk_count} chunks"
        )

        return context_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh context: {str(e)}"
        )


# ============================================================================
# PRESET ENDPOINTS
# ============================================================================


@router.get("/presets", response_model=List[ModelPreset])
async def get_presets() -> List[ModelPreset]:
    """Get all available presets.

    Returns both built-in presets (speed, balanced, quality,
    coding, research) and any custom presets.

    Returns:
        List of ModelPreset objects
    """
    logger.info("Listing Code Chat presets")
    return preset_store.get_all()


@router.get("/presets/{name}", response_model=ModelPreset)
async def get_preset(name: str) -> ModelPreset:
    """Get a specific preset by name.

    Args:
        name: Preset name

    Returns:
        ModelPreset configuration

    Raises:
        HTTPException: 404 if preset not found
    """
    logger.info(f"Fetching preset: {name}")

    preset = preset_store.get(name)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")

    return preset


@router.post("/presets", response_model=ModelPreset)
async def create_preset(preset: ModelPreset) -> ModelPreset:
    """Create a new custom preset.

    Args:
        preset: Preset configuration to create

    Returns:
        Created ModelPreset with isCustom=True

    Raises:
        HTTPException: 400 if name conflicts with built-in or existing custom
        HTTPException: 500 if creation fails
    """
    logger.info(f"Creating custom preset: {preset.name}")

    try:
        created = preset_store.create(preset)
        logger.info(f"Successfully created custom preset: {preset.name}")
        return created

    except ValueError as e:
        logger.warning(f"Failed to create preset '{preset.name}': {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error creating preset '{preset.name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create preset: {str(e)}"
        )


@router.put("/presets/{name}", response_model=ModelPreset)
async def update_preset(name: str, preset: ModelPreset) -> ModelPreset:
    """Update an existing custom preset.

    Args:
        name: Name of preset to update
        preset: Updated preset configuration

    Returns:
        Updated ModelPreset

    Raises:
        HTTPException: 400 if trying to update built-in preset or validation fails
        HTTPException: 404 if preset not found
        HTTPException: 500 if update fails
    """
    logger.info(f"Updating custom preset: {name}")

    try:
        updated = preset_store.update(name, preset)
        logger.info(f"Successfully updated custom preset: {name} -> {updated.name}")
        return updated

    except ValueError as e:
        error_msg = str(e)

        # Check if it's a "not found" error
        if "not found" in error_msg.lower():
            logger.warning(f"Preset '{name}' not found for update")
            raise HTTPException(status_code=404, detail=error_msg)

        # Otherwise it's a validation error
        logger.warning(f"Failed to update preset '{name}': {e}")
        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        logger.error(f"Unexpected error updating preset '{name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preset: {str(e)}"
        )


@router.delete("/presets/{name}")
async def delete_preset(name: str) -> dict:
    """Delete a custom preset.

    Args:
        name: Name of preset to delete

    Returns:
        {"success": bool, "name": str}

    Raises:
        HTTPException: 400 if trying to delete built-in preset
        HTTPException: 404 if preset not found
        HTTPException: 500 if deletion fails
    """
    logger.info(f"Deleting custom preset: {name}")

    try:
        deleted = preset_store.delete(name)

        if deleted:
            logger.info(f"Successfully deleted custom preset: {name}")
            return {"success": True, "name": name}
        else:
            logger.warning(f"Preset '{name}' not found for deletion")
            raise HTTPException(
                status_code=404,
                detail=f"Custom preset '{name}' not found"
            )

    except ValueError as e:
        # Trying to delete built-in preset
        logger.warning(f"Attempted to delete built-in preset '{name}'")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error deleting preset '{name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete preset: {str(e)}"
        )


# ============================================================================
# QUERY ENDPOINT (SSE STREAMING)
# ============================================================================


@router.post("/query")
async def query(request_obj: CodeChatRequest, req: Request) -> StreamingResponse:
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
        request_obj: CodeChatRequest with query and configuration
        req: FastAPI request for accessing app state

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: 400 if workspace path invalid
        HTTPException: 500 if agent initialization fails
    """
    # Validate workspace path
    is_valid, error_msg = validate_path(request_obj.workspace_path)
    if not is_valid:
        logger.warning(
            f"Invalid workspace path in query: {request_obj.workspace_path} - {error_msg}"
        )
        raise HTTPException(status_code=400, detail=error_msg)

    # Generate session ID if not provided
    session_id = request_obj.session_id or str(uuid4())

    logger.info(
        f"Starting Code Chat query (session: {session_id}, "
        f"workspace: {request_obj.workspace_path}, "
        f"preset: {request_obj.preset})"
    )

    try:
        # Get agent instance
        agent = await get_agent(req)

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize agent: {str(e)}"
        )

    async def event_stream():
        """SSE event stream generator."""
        try:
            # Stream events from agent
            async for event in agent.run(request_obj):
                # Format as SSE
                event_json = event.model_dump_json()
                yield f"data: {event_json}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Query stream cancelled for session {session_id}")
            cancel_event = CodeChatStreamEvent(
                type="cancelled", content="Query execution was cancelled"
            )
            yield f"data: {cancel_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(
                f"Error in query stream for session {session_id}: {e}",
                exc_info=True,
            )
            error_event = CodeChatStreamEvent(
                type="error", content=f"Error: {str(e)}"
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-ID": session_id,
        },
    )


@router.post("/cancel/{session_id}")
async def cancel_session(session_id: str, req: Request) -> dict:
    """Cancel an active Code Chat session.

    Sets the cancellation flag for the session, which will be
    checked on the next iteration of the ReAct loop.

    Args:
        session_id: Session ID to cancel
        req: FastAPI request for accessing agent

    Returns:
        {"success": bool, "session_id": str}

    Raises:
        HTTPException: 500 if agent not initialized
    """
    logger.info(f"Cancelling Code Chat session: {session_id}")

    try:
        # Get agent instance
        agent = await get_agent(req)

        # Cancel session
        cancelled = agent.cancel(session_id)

        if cancelled:
            logger.info(f"Session {session_id} cancelled successfully")
        else:
            logger.warning(f"Session {session_id} not found or already completed")

        return {"success": cancelled, "session_id": session_id}

    except Exception as e:
        logger.error(f"Failed to cancel session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel session: {str(e)}"
        )


@router.post("/confirm-action")
async def confirm_action(
    action_id: str = Query(..., description="Action ID to confirm"),
    approved: bool = Query(..., description="Whether to approve the action"),
    req: Request = None
) -> dict:
    """Confirm or reject a pending file operation.

    Called by the frontend when the user approves or rejects a file
    write/delete operation. The agent is waiting for this confirmation
    before proceeding with execution.

    Args:
        action_id: Action identifier (format: session_id_iteration)
        approved: True to approve, False to reject
        req: FastAPI request for accessing agent

    Returns:
        {"success": bool, "action_id": str, "approved": bool}

    Raises:
        HTTPException: 400 if action_id not found
        HTTPException: 500 if agent not initialized

    Example:
        POST /api/code-chat/confirm-action?action_id=abc123_1&approved=true
    """
    logger.info(f"Confirming action {action_id} (approved={approved})")

    try:
        # Get agent instance
        agent = await get_agent(req)

        # Confirm action
        confirmed = agent.confirm_action(action_id, approved)

        if confirmed:
            logger.info(f"Action {action_id} {'approved' if approved else 'rejected'}")
            return {"success": True, "action_id": action_id, "approved": approved}
        else:
            logger.warning(f"Action {action_id} not found")
            raise HTTPException(
                status_code=400,
                detail=f"Action '{action_id}' not found or already processed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm action: {str(e)}"
        )

"""
Code Chat Services Package

This package provides the core services for the Code Chat mode feature:
- ReAct agent with state machine
- Workspace management and browsing
- CGRAG context management
- Tool implementations (file ops, search, execution, MCP)
- Conversation memory
- Preset management

Session 1: Models, workspace, context
Session 2: Tools, memory, agent
"""

from app.services.code_chat.workspace import (
    list_directories,
    get_parent_path,
    check_git_repo,
    detect_project_type,
    detect_project_info,
    is_valid_workspace,
    count_files,
    check_cgrag_index_exists,
    validate_path,
)

from app.services.code_chat.context import (
    list_cgrag_indexes,
    get_context_info,
    create_cgrag_index,
    refresh_cgrag_index,
    delete_cgrag_index,
    get_retriever_for_context,
)

from app.services.code_chat.memory import (
    ConversationMemory,
    MemoryManager,
)

from app.services.code_chat.agent import ReActAgent

__all__ = [
    # Workspace functions
    "list_directories",
    "get_parent_path",
    "check_git_repo",
    "detect_project_type",
    "detect_project_info",
    "is_valid_workspace",
    "count_files",
    "check_cgrag_index_exists",
    "validate_path",
    # Context functions
    "list_cgrag_indexes",
    "get_context_info",
    "create_cgrag_index",
    "refresh_cgrag_index",
    "delete_cgrag_index",
    "get_retriever_for_context",
    # Memory
    "ConversationMemory",
    "MemoryManager",
    # Agent
    "ReActAgent",
]

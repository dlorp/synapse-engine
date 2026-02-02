"""Conversation memory management for Code Chat mode.

Provides:
- ConversationMemory: Per-session memory with turn history
- MemoryManager: Singleton for managing multiple sessions
- Context building for LLM prompts

This module maintains conversation context across multiple queries within a
Code Chat session, tracking recent turns, accessed files, and project information
to build rich context for LLM prompts.

Author: Backend Architect
Phase: Code Chat Implementation (Phase 1.4)
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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
        max_turns: Maximum conversation turns to keep (FIFO)
        max_file_context: Maximum files to track in context
        turns: Deque of recent conversation turns
        file_context: Dict of recently accessed file previews
        project_context: Detected project information
        workspace_path: Current workspace directory
        context_name: Current CGRAG context name
        created_at: Session creation timestamp
        last_activity: Last activity timestamp

    Example:
        >>> memory = ConversationMemory(
        ...     session_id="abc123",
        ...     workspace_path="/home/user/project",
        ...     context_name="my_project"
        ... )
        >>> memory.add_turn(
        ...     query="What files are in src/?",
        ...     response="There are 5 Python files in src/",
        ...     tools_used=["list_directory"]
        ... )
        >>> context = memory.get_context_for_prompt()
    """

    def __init__(
        self,
        session_id: str,
        workspace_path: str,
        context_name: Optional[str] = None,
        max_turns: int = 20,
        max_file_context: int = 5,
    ):
        """Initialize conversation memory.

        Args:
            session_id: Unique session identifier
            workspace_path: Current workspace directory
            context_name: Current CGRAG context name
            max_turns: Maximum conversation turns to keep (default: 20)
            max_file_context: Maximum files to track (default: 5)
        """
        self.session_id = session_id
        self.workspace_path = workspace_path
        self.context_name = context_name
        self.max_turns = max_turns
        self.max_file_context = max_file_context

        # Conversation history (FIFO queue)
        self.turns: deque[ConversationTurn] = deque(maxlen=max_turns)

        # Recently accessed files (path -> preview content)
        # Limited to max_file_context most recent files
        self.file_context: Dict[str, str] = {}

        # Project information
        self.project_context: Optional[ProjectInfo] = None

        # Timestamps
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        logger.info(
            f"Created ConversationMemory for session {session_id} "
            f"(workspace: {workspace_path}, context: {context_name})"
        )

    def add_turn(
        self, query: str, response: str, tools_used: Optional[List[str]] = None
    ) -> None:
        """Add a conversation turn to memory.

        Creates a ConversationTurn and adds to the turns deque. If the deque
        is at max capacity, the oldest turn is automatically removed (FIFO).

        Args:
            query: User query text
            response: Agent response text
            tools_used: List of tool names used in this turn
        """
        if tools_used is None:
            tools_used = []

        turn = ConversationTurn(
            query=query,
            response=response,
            tools_used=tools_used,
            timestamp=datetime.now(),
        )

        self.turns.append(turn)
        self.last_activity = datetime.now()

        logger.debug(
            f"Added turn to session {self.session_id} "
            f"(tools: {', '.join(tools_used) if tools_used else 'none'}, "
            f"total turns: {len(self.turns)})"
        )

    def add_file_context(self, path: str, content: str, max_preview: int = 500) -> None:
        """Track a recently accessed file for context.

        Adds file preview to file_context dict. If max_file_context is exceeded,
        removes the oldest file (FIFO based on insertion order in Python 3.7+).

        Args:
            path: File path (relative or absolute)
            content: File content
            max_preview: Maximum characters to keep in preview (default: 500)
        """
        # Truncate content to max_preview
        preview = content[:max_preview]
        if len(content) > max_preview:
            preview += "\n... (truncated)"

        # Remove oldest file if at capacity
        if len(self.file_context) >= self.max_file_context:
            # Pop first item (oldest in dict)
            oldest_path = next(iter(self.file_context))
            del self.file_context[oldest_path]
            logger.debug(
                f"Removed oldest file context: {oldest_path} "
                f"(session: {self.session_id})"
            )

        # Add new file context
        self.file_context[path] = preview
        self.last_activity = datetime.now()

        logger.debug(
            f"Added file context: {path} ({len(preview)} chars) "
            f"(session: {self.session_id})"
        )

    def set_project_context(self, project_info: ProjectInfo) -> None:
        """Set project information for this session.

        Args:
            project_info: Detected project information
        """
        self.project_context = project_info
        self.last_activity = datetime.now()

        logger.info(
            f"Set project context for session {self.session_id}: "
            f"{project_info.type} project '{project_info.name or 'unnamed'}'"
        )

    def get_context_for_prompt(self, include_file_context: bool = True) -> str:
        """Build context string for LLM prompt.

        Formats conversation history, project info, and file context into a
        structured markdown prompt that provides relevant context to the LLM.

        Args:
            include_file_context: Whether to include recently accessed files

        Returns:
            Formatted context string for LLM prompt

        Example:
            >>> context = memory.get_context_for_prompt()
            >>> # Returns:
            >>> # ## Workspace
            >>> # /home/user/project
            >>> #
            >>> # ## Project
            >>> # Type: python
            >>> # Name: my-app
            >>> # ...
        """
        parts = []

        # Workspace info
        parts.append("## Workspace")
        parts.append(self.workspace_path)
        if self.context_name:
            parts.append(f"CGRAG Context: {self.context_name}")
        parts.append("")

        # Project info
        if self.project_context:
            parts.append("## Project")
            parts.append(f"Type: {self.project_context.type}")
            if self.project_context.name:
                parts.append(f"Name: {self.project_context.name}")
            if self.project_context.version:
                parts.append(f"Version: {self.project_context.version}")

            if self.project_context.dependencies:
                deps_str = ", ".join(self.project_context.dependencies[:10])
                if len(self.project_context.dependencies) > 10:
                    deps_str += f" ... ({len(self.project_context.dependencies)} total)"
                parts.append(f"Dependencies: {deps_str}")

            if self.project_context.entry_points:
                parts.append(
                    f"Entry Points: {', '.join(self.project_context.entry_points)}"
                )

            parts.append("")

        # Recent conversation
        if self.turns:
            parts.append("## Recent Conversation")
            for turn in self.turns:
                # Truncate long queries/responses for context
                query_preview = turn.query[:200]
                if len(turn.query) > 200:
                    query_preview += "..."

                response_preview = turn.response[:300]
                if len(turn.response) > 300:
                    response_preview += "..."

                parts.append(f"User: {query_preview}")
                parts.append(f"Assistant: {response_preview}")

                if turn.tools_used:
                    parts.append(f"Tools: {', '.join(turn.tools_used)}")

                parts.append("")

        # Recently accessed files
        if include_file_context and self.file_context:
            parts.append("## Recently Accessed Files")
            for path, preview in self.file_context.items():
                parts.append(f"### {path}")
                parts.append("```")
                parts.append(preview)
                parts.append("```")
                parts.append("")

        return "\n".join(parts)

    def clear(self) -> None:
        """Clear all memory for this session.

        Resets conversation turns, file context, and project context.
        Does not reset workspace_path or context_name configuration.
        """
        self.turns.clear()
        self.file_context.clear()
        self.project_context = None
        self.last_activity = datetime.now()

        logger.info(f"Cleared memory for session {self.session_id}")


class MemoryManager:
    """Singleton manager for multiple session memories.

    Manages ConversationMemory instances across multiple concurrent sessions
    with thread-safe operations and automatic cleanup of stale sessions.

    Attributes:
        _instance: Singleton instance
        _lock: Asyncio lock for thread safety
        _sessions: Dict of session_id -> ConversationMemory

    Example:
        >>> manager = await MemoryManager.get_instance()
        >>> memory = await manager.get_or_create(
        ...     session_id="abc123",
        ...     workspace_path="/home/user/project",
        ...     context_name="my_project"
        ... )
        >>> await manager.cleanup_stale_sessions()
    """

    _instance: Optional["MemoryManager"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self):
        """Initialize memory manager.

        Note: Use get_instance() instead of direct instantiation to ensure
        singleton behavior.
        """
        self._sessions: Dict[str, ConversationMemory] = {}
        self._manager_lock = asyncio.Lock()
        logger.info("MemoryManager initialized")

    @classmethod
    async def get_instance(cls) -> "MemoryManager":
        """Get or create the singleton MemoryManager instance.

        Thread-safe singleton access using asyncio lock.

        Returns:
            MemoryManager singleton instance
        """
        if cls._instance is None:
            async with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_or_create(
        self,
        session_id: str,
        workspace_path: str,
        context_name: Optional[str] = None,
        max_turns: int = 20,
        max_file_context: int = 5,
    ) -> ConversationMemory:
        """Get existing memory or create new one for session.

        Args:
            session_id: Unique session identifier
            workspace_path: Current workspace directory
            context_name: Current CGRAG context name
            max_turns: Maximum conversation turns to keep
            max_file_context: Maximum files to track

        Returns:
            ConversationMemory for the session
        """
        async with self._manager_lock:
            if session_id not in self._sessions:
                memory = ConversationMemory(
                    session_id=session_id,
                    workspace_path=workspace_path,
                    context_name=context_name,
                    max_turns=max_turns,
                    max_file_context=max_file_context,
                )
                self._sessions[session_id] = memory
                logger.info(
                    f"Created new session memory: {session_id} "
                    f"(total sessions: {len(self._sessions)})"
                )
            else:
                memory = self._sessions[session_id]
                # Update last activity
                memory.last_activity = datetime.now()
                logger.debug(f"Retrieved existing session memory: {session_id}")

            return memory

    async def get(self, session_id: str) -> Optional[ConversationMemory]:
        """Get existing memory for session.

        Args:
            session_id: Session identifier

        Returns:
            ConversationMemory if exists, None otherwise
        """
        async with self._manager_lock:
            memory = self._sessions.get(session_id)
            if memory:
                # Update last activity
                memory.last_activity = datetime.now()
            return memory

    async def remove(self, session_id: str) -> bool:
        """Remove session memory.

        Args:
            session_id: Session identifier

        Returns:
            True if session was removed, False if not found
        """
        async with self._manager_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(
                    f"Removed session memory: {session_id} "
                    f"(remaining sessions: {len(self._sessions)})"
                )
                return True
            return False

    async def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """Remove inactive sessions older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 24)

        Returns:
            Number of sessions removed
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0

        async with self._manager_lock:
            stale_sessions = [
                session_id
                for session_id, memory in self._sessions.items()
                if memory.last_activity < cutoff_time
            ]

            for session_id in stale_sessions:
                del self._sessions[session_id]
                removed_count += 1
                logger.info(
                    f"Cleaned up stale session: {session_id} "
                    f"(last activity: {self._sessions[session_id].last_activity})"
                )

        if removed_count > 0:
            logger.info(
                f"Cleanup complete: removed {removed_count} stale sessions "
                f"(cutoff: {cutoff_time}, remaining: {len(self._sessions)})"
            )

        return removed_count

    async def get_active_session_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active sessions
        """
        async with self._manager_lock:
            return len(self._sessions)

    async def get_session_stats(self) -> Dict[str, any]:
        """Get statistics about active sessions.

        Returns:
            Dict with session statistics including:
                - total_sessions: Total active sessions
                - avg_turns: Average turns per session
                - oldest_session: Age of oldest session in hours
                - newest_session: Age of newest session in hours
        """
        async with self._manager_lock:
            if not self._sessions:
                return {
                    "total_sessions": 0,
                    "avg_turns": 0,
                    "oldest_session_hours": 0,
                    "newest_session_hours": 0,
                }

            now = datetime.now()
            turn_counts = [len(m.turns) for m in self._sessions.values()]
            ages = [
                (now - m.created_at).total_seconds() / 3600
                for m in self._sessions.values()
            ]

            return {
                "total_sessions": len(self._sessions),
                "avg_turns": sum(turn_counts) / len(turn_counts) if turn_counts else 0,
                "oldest_session_hours": max(ages) if ages else 0,
                "newest_session_hours": min(ages) if ages else 0,
            }

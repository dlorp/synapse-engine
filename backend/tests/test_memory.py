"""Tests for the conversation memory management module.

Tests ConversationMemory and MemoryManager classes that provide
conversation context persistence within Code Chat sessions.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.models.code_chat import ProjectInfo
from app.services.code_chat.memory import ConversationMemory, MemoryManager


class TestConversationMemory:
    """Tests for ConversationMemory class."""

    def test_init_creates_empty_memory(self):
        """Memory initializes with empty turns and file context."""
        memory = ConversationMemory(
            session_id="test-session",
            workspace_path="/home/user/project",
            context_name="test-context",
        )

        assert memory.session_id == "test-session"
        assert memory.workspace_path == "/home/user/project"
        assert memory.context_name == "test-context"
        assert len(memory.turns) == 0
        assert len(memory.file_context) == 0
        assert memory.project_context is None
        assert memory.max_turns == 20  # default
        assert memory.max_file_context == 5  # default

    def test_init_with_custom_limits(self):
        """Memory respects custom max_turns and max_file_context."""
        memory = ConversationMemory(
            session_id="test",
            workspace_path="/tmp",
            max_turns=5,
            max_file_context=3,
        )

        assert memory.max_turns == 5
        assert memory.max_file_context == 3

    def test_add_turn_stores_conversation_turn(self):
        """add_turn() creates and stores a ConversationTurn."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        memory.add_turn(
            query="What files are here?",
            response="There are 3 Python files.",
            tools_used=["list_directory"],
        )

        assert len(memory.turns) == 1
        turn = memory.turns[0]
        assert turn.query == "What files are here?"
        assert turn.response == "There are 3 Python files."
        assert turn.tools_used == ["list_directory"]
        assert isinstance(turn.timestamp, datetime)

    def test_add_turn_without_tools_uses_empty_list(self):
        """add_turn() with no tools_used defaults to empty list."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        memory.add_turn(query="Hello", response="Hi there!")

        assert memory.turns[0].tools_used == []

    def test_add_turn_respects_max_turns_fifo(self):
        """add_turn() removes oldest turn when max_turns exceeded (FIFO)."""
        memory = ConversationMemory(
            session_id="test", workspace_path="/tmp", max_turns=3
        )

        # Add 4 turns
        for i in range(4):
            memory.add_turn(query=f"Query {i}", response=f"Response {i}")

        # Should only keep last 3
        assert len(memory.turns) == 3
        assert memory.turns[0].query == "Query 1"  # Oldest remaining
        assert memory.turns[2].query == "Query 3"  # Newest

    def test_add_turn_updates_last_activity(self):
        """add_turn() updates last_activity timestamp."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        initial_activity = memory.last_activity

        # Small delay to ensure timestamp changes
        import time

        time.sleep(0.01)

        memory.add_turn(query="Test", response="Response")

        assert memory.last_activity > initial_activity

    def test_add_file_context_stores_preview(self):
        """add_file_context() stores file content preview."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        memory.add_file_context(
            path="src/main.py",
            content="def main():\n    print('hello')",
        )

        assert "src/main.py" in memory.file_context
        assert "def main()" in memory.file_context["src/main.py"]

    def test_add_file_context_truncates_long_content(self):
        """add_file_context() truncates content beyond max_preview."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        long_content = "x" * 1000
        memory.add_file_context(path="big.txt", content=long_content, max_preview=100)

        preview = memory.file_context["big.txt"]
        assert len(preview) < len(long_content)
        assert "... (truncated)" in preview

    def test_add_file_context_respects_max_file_context_fifo(self):
        """add_file_context() removes oldest file when max exceeded (FIFO)."""
        memory = ConversationMemory(
            session_id="test", workspace_path="/tmp", max_file_context=2
        )

        # Add 3 files
        memory.add_file_context("file1.py", "content1")
        memory.add_file_context("file2.py", "content2")
        memory.add_file_context("file3.py", "content3")

        # Should only keep last 2
        assert len(memory.file_context) == 2
        assert "file1.py" not in memory.file_context
        assert "file2.py" in memory.file_context
        assert "file3.py" in memory.file_context

    def test_set_project_context_stores_info(self):
        """set_project_context() stores ProjectInfo."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        project = ProjectInfo(
            type="python",
            name="my-app",
            version="1.0.0",
            dependencies=["fastapi", "pydantic"],
            entry_points=["main.py"],
        )
        memory.set_project_context(project)

        assert memory.project_context is not None
        assert memory.project_context.type == "python"
        assert memory.project_context.name == "my-app"
        assert memory.project_context.version == "1.0.0"

    def test_get_context_for_prompt_builds_markdown(self):
        """get_context_for_prompt() builds formatted markdown context."""
        memory = ConversationMemory(
            session_id="test",
            workspace_path="/home/user/project",
            context_name="my_context",
        )

        context = memory.get_context_for_prompt()

        assert "## Workspace" in context
        assert "/home/user/project" in context
        assert "my_context" in context

    def test_get_context_for_prompt_includes_project_info(self):
        """get_context_for_prompt() includes project information."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.set_project_context(
            ProjectInfo(
                type="python",
                name="test-project",
                version="2.0.0",
                dependencies=["numpy", "pandas"],
                entry_points=["app.py"],
            )
        )

        context = memory.get_context_for_prompt()

        assert "## Project" in context
        assert "Type: python" in context
        assert "Name: test-project" in context
        assert "Version: 2.0.0" in context
        assert "numpy" in context
        assert "Entry Points: app.py" in context

    def test_get_context_for_prompt_includes_conversation_history(self):
        """get_context_for_prompt() includes recent conversation turns."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.add_turn(
            query="List files",
            response="Found 5 files",
            tools_used=["list_directory"],
        )

        context = memory.get_context_for_prompt()

        assert "## Recent Conversation" in context
        assert "User: List files" in context
        assert "Assistant: Found 5 files" in context
        assert "Tools: list_directory" in context

    def test_get_context_for_prompt_includes_file_context(self):
        """get_context_for_prompt() includes recently accessed files."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.add_file_context("main.py", "print('hello')")

        context = memory.get_context_for_prompt()

        assert "## Recently Accessed Files" in context
        assert "### main.py" in context
        assert "print('hello')" in context

    def test_get_context_for_prompt_excludes_file_context_when_disabled(self):
        """get_context_for_prompt(include_file_context=False) excludes files."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.add_file_context("main.py", "print('hello')")

        context = memory.get_context_for_prompt(include_file_context=False)

        assert "## Recently Accessed Files" not in context
        assert "main.py" not in context

    def test_get_context_for_prompt_truncates_long_queries_and_responses(self):
        """get_context_for_prompt() truncates long queries/responses."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")

        long_query = "x" * 300
        long_response = "y" * 400
        memory.add_turn(query=long_query, response=long_response)

        context = memory.get_context_for_prompt()

        # Query should be truncated at 200 chars
        assert "..." in context
        assert long_query not in context  # Full query shouldn't appear

    def test_get_context_for_prompt_handles_many_dependencies(self):
        """get_context_for_prompt() truncates long dependency lists."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.set_project_context(
            ProjectInfo(
                type="python",
                name="big-project",
                dependencies=[f"dep{i}" for i in range(20)],  # 20 deps
            )
        )

        context = memory.get_context_for_prompt()

        # Should show first 10 and indicate more
        assert "dep0" in context
        assert "dep9" in context
        assert "20 total" in context

    def test_clear_resets_memory(self):
        """clear() resets all memory state."""
        memory = ConversationMemory(session_id="test", workspace_path="/tmp")
        memory.add_turn(query="Q", response="R")
        memory.add_file_context("test.py", "content")
        memory.set_project_context(ProjectInfo(type="python"))

        memory.clear()

        assert len(memory.turns) == 0
        assert len(memory.file_context) == 0
        assert memory.project_context is None
        # Config should remain
        assert memory.workspace_path == "/tmp"
        assert memory.session_id == "test"


class TestMemoryManager:
    """Tests for MemoryManager singleton class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        MemoryManager._instance = None
        yield
        MemoryManager._instance = None

    @pytest.mark.asyncio
    async def test_get_instance_returns_singleton(self):
        """get_instance() returns the same instance each time."""
        instance1 = await MemoryManager.get_instance()
        instance2 = await MemoryManager.get_instance()

        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new_session(self):
        """get_or_create() creates new memory for unknown session."""
        manager = await MemoryManager.get_instance()

        memory = await manager.get_or_create(
            session_id="new-session",
            workspace_path="/home/user/project",
            context_name="my-context",
        )

        assert memory.session_id == "new-session"
        assert memory.workspace_path == "/home/user/project"
        assert memory.context_name == "my-context"

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_session(self):
        """get_or_create() returns existing memory for known session."""
        manager = await MemoryManager.get_instance()

        # Create session
        memory1 = await manager.get_or_create(
            session_id="existing",
            workspace_path="/tmp",
        )
        memory1.add_turn(query="Test", response="Response")

        # Get same session
        memory2 = await manager.get_or_create(
            session_id="existing",
            workspace_path="/tmp",
        )

        assert memory1 is memory2
        assert len(memory2.turns) == 1

    @pytest.mark.asyncio
    async def test_get_or_create_respects_custom_limits(self):
        """get_or_create() passes custom limits to new sessions."""
        manager = await MemoryManager.get_instance()

        memory = await manager.get_or_create(
            session_id="custom",
            workspace_path="/tmp",
            max_turns=10,
            max_file_context=3,
        )

        assert memory.max_turns == 10
        assert memory.max_file_context == 3

    @pytest.mark.asyncio
    async def test_get_returns_existing_session(self):
        """get() returns existing session memory."""
        manager = await MemoryManager.get_instance()

        # Create first
        await manager.get_or_create(session_id="exists", workspace_path="/tmp")

        # Get should work
        memory = await manager.get("exists")

        assert memory is not None
        assert memory.session_id == "exists"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_unknown_session(self):
        """get() returns None for unknown session."""
        manager = await MemoryManager.get_instance()

        memory = await manager.get("nonexistent")

        assert memory is None

    @pytest.mark.asyncio
    async def test_get_updates_last_activity(self):
        """get() updates last_activity on the session."""
        manager = await MemoryManager.get_instance()
        memory = await manager.get_or_create(session_id="test", workspace_path="/tmp")
        initial_activity = memory.last_activity

        # Small delay
        import time

        time.sleep(0.01)

        # Get session
        await manager.get("test")

        assert memory.last_activity > initial_activity

    @pytest.mark.asyncio
    async def test_remove_deletes_session(self):
        """remove() deletes session and returns True."""
        manager = await MemoryManager.get_instance()
        await manager.get_or_create(session_id="to-remove", workspace_path="/tmp")

        result = await manager.remove("to-remove")

        assert result is True
        assert await manager.get("to-remove") is None

    @pytest.mark.asyncio
    async def test_remove_returns_false_for_unknown(self):
        """remove() returns False for unknown session."""
        manager = await MemoryManager.get_instance()

        result = await manager.remove("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_active_session_count(self):
        """get_active_session_count() returns correct count."""
        manager = await MemoryManager.get_instance()

        # Initially zero
        assert await manager.get_active_session_count() == 0

        # Add sessions
        await manager.get_or_create(session_id="s1", workspace_path="/tmp")
        await manager.get_or_create(session_id="s2", workspace_path="/tmp")

        assert await manager.get_active_session_count() == 2

    @pytest.mark.asyncio
    async def test_get_session_stats_empty(self):
        """get_session_stats() returns zeros for empty manager."""
        manager = await MemoryManager.get_instance()

        stats = await manager.get_session_stats()

        assert stats["total_sessions"] == 0
        assert stats["avg_turns"] == 0
        assert stats["oldest_session_hours"] == 0
        assert stats["newest_session_hours"] == 0

    @pytest.mark.asyncio
    async def test_get_session_stats_with_sessions(self):
        """get_session_stats() returns correct statistics."""
        manager = await MemoryManager.get_instance()

        # Create sessions with turns
        m1 = await manager.get_or_create(session_id="s1", workspace_path="/tmp")
        m1.add_turn(query="Q1", response="R1")
        m1.add_turn(query="Q2", response="R2")

        m2 = await manager.get_or_create(session_id="s2", workspace_path="/tmp")
        m2.add_turn(query="Q1", response="R1")

        stats = await manager.get_session_stats()

        assert stats["total_sessions"] == 2
        assert stats["avg_turns"] == 1.5  # (2 + 1) / 2
        assert stats["oldest_session_hours"] >= 0
        assert stats["newest_session_hours"] >= 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_sessions_removes_old(self):
        """cleanup_stale_sessions() removes sessions older than max_age."""
        manager = await MemoryManager.get_instance()

        # Create a session
        memory = await manager.get_or_create(session_id="stale", workspace_path="/tmp")

        # Manually backdate last_activity to 25 hours ago
        memory.last_activity = datetime.now() - timedelta(hours=25)

        # Cleanup with 24 hour max
        removed = await manager.cleanup_stale_sessions(max_age_hours=24)

        # Verify the session was removed
        assert removed == 1
        assert await manager.get("stale") is None

    @pytest.mark.asyncio
    async def test_cleanup_stale_sessions_keeps_recent(self):
        """cleanup_stale_sessions() keeps recent sessions."""
        manager = await MemoryManager.get_instance()

        # Create a fresh session
        await manager.get_or_create(session_id="fresh", workspace_path="/tmp")

        # Cleanup with 24 hour max
        await manager.cleanup_stale_sessions(max_age_hours=24)

        # Session should still exist
        assert await manager.get("fresh") is not None

    @pytest.mark.asyncio
    async def test_concurrent_access_is_thread_safe(self):
        """Manager handles concurrent access safely."""
        manager = await MemoryManager.get_instance()

        async def create_session(i: int):
            return await manager.get_or_create(
                session_id=f"session-{i}",
                workspace_path="/tmp",
            )

        # Create 10 sessions concurrently
        tasks = [create_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert await manager.get_active_session_count() == 10

        # All session IDs should be unique
        session_ids = {m.session_id for m in results}
        assert len(session_ids) == 10

"""Search tools for Code Chat mode.

Provides:
- search_code: CGRAG-based semantic code search
- web_search: SearXNG-based web search
- grep_files: Regex pattern matching in files

Integrates with existing services for retrieval.

Author: CGRAG Specialist
Phase: Code Chat Implementation (Session 2.2 - Task 3)
"""

import logging
import re
import aiofiles
from pathlib import Path
from typing import List, Optional

from app.models.code_chat import ToolName, ToolResult
from app.services.code_chat.tools.base import BaseTool, SecurityError

logger = logging.getLogger(__name__)

# Limits
MAX_GREP_RESULTS = 500
MAX_LINE_LENGTH = 500  # Truncate long lines in grep output
MAX_SEARCH_CODE_RESULTS = 10
MAX_WEB_SEARCH_RESULTS = 5

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size for grep

# Blocked directories for security
BLOCKED_DIRECTORIES = {
    '__pycache__',
    'node_modules',
    '.git',
    '.venv',
    'venv',
    '.env',
    'dist',
    'build',
    '.cache',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'coverage',
    'htmlcov'
}

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.o', '.a', '.lib', '.dll', '.exe',
    '.bin', '.dat', '.db', '.sqlite', '.pkl', '.pickle',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.wav',
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
}


class SearchCodeTool(BaseTool):
    """CGRAG-based semantic code search.

    Uses FAISS vector search to find relevant code chunks based on
    semantic similarity to the query. Requires a CGRAG context to be
    selected (context_name parameter).

    Attributes:
        name: ToolName.SEARCH_CODE
        description: Search codebase semantically using CGRAG
        parameter_schema: JSON schema for validation
        workspace_root: Workspace root directory
    """

    name = ToolName.SEARCH_CODE
    description = "Search codebase semantically using CGRAG vector search"
    parameter_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (semantic search, not keyword)"
            },
            "context_name": {
                "type": "string",
                "description": "CGRAG context/index name (optional if only one exists)"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": MAX_SEARCH_CODE_RESULTS,
                "minimum": 1,
                "maximum": 50
            },
            "min_relevance": {
                "type": "number",
                "description": "Minimum relevance score (0.0-1.0)",
                "default": 0.7,
                "minimum": 0.0,
                "maximum": 1.0
            }
        },
        "required": ["query"]
    }
    requires_confirmation = False

    def __init__(self, workspace_root: str):
        """Initialize SearchCodeTool.

        Args:
            workspace_root: Workspace root directory
        """
        self.workspace_root = Path(workspace_root)

    async def execute(
        self,
        query: str,
        context_name: Optional[str] = None,
        max_results: int = MAX_SEARCH_CODE_RESULTS,
        min_relevance: float = 0.7
    ) -> ToolResult:
        """Execute semantic code search.

        Args:
            query: Search query
            context_name: CGRAG context name (optional)
            max_results: Maximum results to return
            min_relevance: Minimum relevance threshold

        Returns:
            ToolResult with formatted search results
        """
        try:
            from app.services.code_chat.context import get_retriever_for_context

            logger.info(
                f"Executing search_code: query='{query}', context='{context_name}', "
                f"max_results={max_results}, min_relevance={min_relevance}"
            )

            # Get retriever for context
            retriever = await get_retriever_for_context(context_name)

            if retriever is None:
                error_msg = (
                    f"CGRAG context '{context_name}' not found or unavailable. "
                    f"Please select a valid context or create one first."
                )
                logger.warning(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg
                )

            # Update minimum relevance threshold
            retriever.min_relevance = min_relevance

            # Execute retrieval
            result = await retriever.retrieve(
                query=query,
                token_budget=8000,  # Standard token budget
                max_artifacts=max_results
            )

            if not result.artifacts:
                return ToolResult(
                    success=True,
                    output=f"No results found for query: '{query}' (min_relevance={min_relevance})"
                )

            # Format results
            output_lines = [
                f"Found {len(result.artifacts)} relevant code chunks:",
                f"Search time: {result.retrieval_time_ms:.1f}ms",
                f"Tokens used: {result.tokens_used}",
                ""
            ]

            for i, artifact in enumerate(result.artifacts, 1):
                # Extract relative path from workspace root
                try:
                    file_path = Path(artifact.file_path)
                    if file_path.is_absolute() and file_path.is_relative_to(self.workspace_root):
                        relative_path = file_path.relative_to(self.workspace_root)
                    else:
                        relative_path = file_path
                except (ValueError, OSError):
                    relative_path = artifact.file_path

                output_lines.append(
                    f"=== {i}. {relative_path} (relevance: {artifact.relevance_score:.3f}) ==="
                )
                output_lines.append(artifact.content)
                output_lines.append("")  # Blank line separator

            output = "\n".join(output_lines)

            logger.info(
                f"search_code completed: {len(result.artifacts)} results, "
                f"{result.tokens_used} tokens, {result.retrieval_time_ms:.1f}ms"
            )

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "result_count": len(result.artifacts),
                    "tokens_used": result.tokens_used,
                    "retrieval_time_ms": result.retrieval_time_ms,
                    "top_score": result.top_scores[0] if result.top_scores else 0.0
                }
            )

        except Exception as e:
            logger.error(f"search_code failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )


class WebSearchTool(BaseTool):
    """SearXNG-based web search.

    Executes web searches using SearXNG metasearch engine and returns
    formatted results with titles, URLs, and snippets.

    Attributes:
        name: ToolName.WEB_SEARCH
        description: Search the web using SearXNG
        parameter_schema: JSON schema for validation
    """

    name = ToolName.WEB_SEARCH
    description = "Search the web using SearXNG metasearch engine"
    parameter_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": MAX_WEB_SEARCH_RESULTS,
                "minimum": 1,
                "maximum": 20
            }
        },
        "required": ["query"]
    }
    requires_confirmation = False

    async def execute(
        self,
        query: str,
        max_results: int = MAX_WEB_SEARCH_RESULTS
    ) -> ToolResult:
        """Execute web search.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            ToolResult with formatted search results
        """
        try:
            from app.services.websearch import get_searxng_client

            logger.info(f"Executing web_search: query='{query}', max_results={max_results}")

            # Get SearXNG client
            client = get_searxng_client()

            # Update max_results on client
            original_max = client.max_results
            client.max_results = max_results

            try:
                # Execute search
                response = await client.search(query=query)

                if not response.results:
                    return ToolResult(
                        success=True,
                        output=f"No web search results found for query: '{query}'"
                    )

                # Format results
                output_lines = [
                    f"Web search results for: '{query}'",
                    f"Found {response.total_results} results (showing {len(response.results)})",
                    f"Search time: {response.search_time_ms}ms",
                    f"Engines: {', '.join(response.engines_used)}",
                    ""
                ]

                for i, result in enumerate(response.results, 1):
                    output_lines.append(f"{i}. {result.title}")
                    output_lines.append(f"   URL: {result.url}")
                    if result.content:
                        # Truncate long snippets
                        snippet = result.content[:300] + "..." if len(result.content) > 300 else result.content
                        output_lines.append(f"   {snippet}")
                    if result.published_date:
                        output_lines.append(f"   Published: {result.published_date}")
                    output_lines.append("")  # Blank line separator

                output = "\n".join(output_lines)

                logger.info(
                    f"web_search completed: {len(response.results)} results, "
                    f"{response.search_time_ms}ms"
                )

                return ToolResult(
                    success=True,
                    output=output,
                    metadata={
                        "result_count": len(response.results),
                        "total_results": response.total_results,
                        "search_time_ms": response.search_time_ms,
                        "engines_used": response.engines_used
                    }
                )

            finally:
                # Restore original max_results
                client.max_results = original_max

        except Exception as e:
            logger.error(f"web_search failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Web search failed: {str(e)}"
            )


class GrepFilesTool(BaseTool):
    """Regex pattern search in files.

    Recursively searches files for regex pattern matches, similar to
    grep -r. Supports case sensitivity control, file pattern filtering,
    and result limiting.

    Attributes:
        name: ToolName.GREP_FILES
        description: Search files with regex patterns
        parameter_schema: JSON schema for validation
        workspace_root: Workspace root directory
    """

    name = ToolName.GREP_FILES
    description = "Search files using regex patterns (like grep -r)"
    parameter_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regex pattern to search for"
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search (relative to workspace, default: '.')",
                "default": "."
            },
            "file_pattern": {
                "type": "string",
                "description": "File glob pattern (e.g., '*.py', '*.ts')",
                "default": "*"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether search is case sensitive",
                "default": True
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of matches to return",
                "default": 100,
                "minimum": 1,
                "maximum": MAX_GREP_RESULTS
            }
        },
        "required": ["pattern"]
    }
    requires_confirmation = False

    def __init__(self, workspace_root: str):
        """Initialize GrepFilesTool.

        Args:
            workspace_root: Workspace root directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        case_sensitive: bool = True,
        max_results: int = 100
    ) -> ToolResult:
        """Execute regex pattern search.

        Args:
            pattern: Regex pattern to search for
            path: Directory or file to search
            file_pattern: File glob pattern
            case_sensitive: Whether search is case sensitive
            max_results: Maximum matches to return

        Returns:
            ToolResult with formatted matches
        """
        try:
            logger.info(
                f"Executing grep_files: pattern='{pattern}', path='{path}', "
                f"file_pattern='{file_pattern}', case_sensitive={case_sensitive}, "
                f"max_results={max_results}"
            )

            # Resolve and validate path
            search_path = self._resolve_and_validate_path(path)

            # Compile regex pattern
            try:
                regex_flags = 0 if case_sensitive else re.IGNORECASE
                compiled_pattern = re.compile(pattern, regex_flags)
            except re.error as e:
                return ToolResult(
                    success=False,
                    error=f"Invalid regex pattern: {e}"
                )

            # Collect files to search
            files_to_search = self._collect_files(search_path, file_pattern)

            if not files_to_search:
                return ToolResult(
                    success=True,
                    output=f"No files matched pattern '{file_pattern}' in '{path}'"
                )

            # Search files for pattern matches
            matches = await self._search_files(
                files_to_search,
                compiled_pattern,
                max_results
            )

            if not matches:
                return ToolResult(
                    success=True,
                    output=f"No matches found for pattern '{pattern}' in {len(files_to_search)} files"
                )

            # Format output
            output_lines = [
                f"Found {len(matches)} matches for pattern '{pattern}':",
                f"Searched {len(files_to_search)} files",
                ""
            ]

            for file_path, line_num, line_content in matches:
                # Get relative path from workspace
                try:
                    relative_path = file_path.relative_to(self.workspace_root)
                except ValueError:
                    relative_path = file_path

                # Truncate long lines
                if len(line_content) > MAX_LINE_LENGTH:
                    line_content = line_content[:MAX_LINE_LENGTH] + "..."

                output_lines.append(f"{relative_path}:{line_num}: {line_content}")

            if len(matches) >= max_results:
                output_lines.append("")
                output_lines.append(f"(showing first {max_results} matches)")

            output = "\n".join(output_lines)

            logger.info(
                f"grep_files completed: {len(matches)} matches in {len(files_to_search)} files"
            )

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "match_count": len(matches),
                    "files_searched": len(files_to_search),
                    "pattern": pattern,
                    "case_sensitive": case_sensitive
                }
            )

        except SecurityError as e:
            logger.error(f"Security violation in grep_files: {e}")
            return ToolResult(
                success=False,
                error=f"Security violation: {str(e)}"
            )
        except Exception as e:
            logger.error(f"grep_files failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Pattern search failed: {str(e)}"
            )

    def _resolve_and_validate_path(self, path: str) -> Path:
        """Resolve and validate search path within workspace.

        Args:
            path: Path to validate (relative to workspace)

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If path is outside workspace
        """
        # Resolve path relative to workspace
        if Path(path).is_absolute():
            target_path = Path(path).resolve()
        else:
            target_path = (self.workspace_root / path).resolve()

        # Validate path is within workspace
        try:
            target_path.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Path '{path}' is outside workspace root '{self.workspace_root}'"
            )

        # Check path exists
        if not target_path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        return target_path

    def _collect_files(self, search_path: Path, file_pattern: str) -> List[Path]:
        """Collect files matching pattern.

        Args:
            search_path: Directory or file to search
            file_pattern: File glob pattern

        Returns:
            List of file paths to search
        """
        files = []

        if search_path.is_file():
            # Single file
            files.append(search_path)
        else:
            # Directory - walk and collect matching files
            for path in search_path.rglob(file_pattern):
                # Skip directories
                if not path.is_file():
                    continue

                # Skip blocked directories
                if any(blocked in path.parts for blocked in BLOCKED_DIRECTORIES):
                    continue

                # Skip binary files
                if path.suffix in BINARY_EXTENSIONS:
                    continue

                # Skip hidden files
                if any(part.startswith('.') for part in path.parts[len(self.workspace_root.parts):]):
                    continue

                # Check file size
                try:
                    if path.stat().st_size > MAX_FILE_SIZE:
                        logger.debug(f"Skipping large file: {path}")
                        continue
                except OSError:
                    continue

                files.append(path)

        return sorted(files)

    async def _search_files(
        self,
        files: List[Path],
        pattern: re.Pattern,
        max_results: int
    ) -> List[tuple[Path, int, str]]:
        """Search files for pattern matches.

        Args:
            files: Files to search
            pattern: Compiled regex pattern
            max_results: Maximum matches to return

        Returns:
            List of (file_path, line_number, line_content) tuples
        """
        matches = []

        for file_path in files:
            if len(matches) >= max_results:
                break

            try:
                # Read file asynchronously
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    line_num = 0
                    async for line in f:
                        line_num += 1

                        # Search for pattern
                        if pattern.search(line):
                            matches.append((
                                file_path,
                                line_num,
                                line.rstrip('\n\r')
                            ))

                            if len(matches) >= max_results:
                                break

            except Exception as e:
                logger.debug(f"Failed to search file {file_path}: {e}")
                continue

        return matches

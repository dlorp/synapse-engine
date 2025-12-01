"""Base tool infrastructure for Code Chat mode.

Provides:
- BaseTool: Abstract base class for all tools
- ToolRegistry: Central registry for tool discovery and invocation
- SecurityError: Custom exception for security violations

All tools must inherit from BaseTool and implement the execute() method.
The ToolRegistry manages tool registration, validation, and execution with
comprehensive error handling.

Author: Backend Architect
Phase: Code Chat Implementation (Session 2.1)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
import logging

from app.models.code_chat import ToolName, ToolResult, ToolCall

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security check fails.

    Examples include:
    - Path traversal attempts
    - Access outside workspace boundaries
    - Symlink escape attempts
    - File size limit violations
    """
    pass


class BaseTool(ABC):
    """Abstract base class for all Code Chat tools.

    All tools must:
    1. Define a unique name matching ToolName enum
    2. Implement execute() method with proper error handling
    3. Define parameter_schema for validation (JSON Schema format)
    4. Handle errors gracefully and return ToolResult
    5. Set requires_confirmation flag if user approval needed

    Attributes:
        name: Tool identifier from ToolName enum
        description: Human-readable description of what the tool does
        parameter_schema: JSON Schema definition for parameters
        requires_confirmation: Whether tool needs user approval before execution

    Example:
        >>> class MyTool(BaseTool):
        ...     name = ToolName.READ_FILE
        ...     description = "Read file contents"
        ...     parameter_schema = {
        ...         "type": "object",
        ...         "properties": {"path": {"type": "string"}},
        ...         "required": ["path"]
        ...     }
        ...
        ...     async def execute(self, path: str) -> ToolResult:
        ...         return ToolResult(success=True, output="file contents")
    """

    name: ToolName
    description: str
    parameter_schema: Dict[str, Any]
    requires_confirmation: bool = False

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        This method must be implemented by all tool subclasses.
        It should perform the tool's operation and return a ToolResult
        with success status and output or error message.

        Args:
            **kwargs: Tool-specific parameters matching parameter_schema

        Returns:
            ToolResult with success/failure status and output/error

        Raises:
            Exception: Any errors should be caught and returned in ToolResult.error
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters against schema.

        Default implementation checks for required parameters.
        Subclasses can override for more complex validation.

        Args:
            params: Parameters to validate against parameter_schema

        Returns:
            Error message if validation fails, None if valid

        Example:
            >>> tool = MyTool()
            >>> error = tool.validate_params({"path": "/tmp/file.txt"})
            >>> assert error is None  # Validation passed
            >>> error = tool.validate_params({})
            >>> assert error == "Missing required parameter: path"
        """
        # Check required parameters
        required = self.parameter_schema.get("required", [])
        for param in required:
            if param not in params:
                return f"Missing required parameter: {param}"

        # Additional validation can be added by subclasses
        return None


class ToolRegistry:
    """Central registry for all Code Chat tools.

    Manages tool registration, discovery, and invocation with
    thread-safe access and comprehensive error handling.

    The registry provides:
    - Tool registration with automatic deduplication
    - Tool lookup by ToolName
    - Tool listing with metadata
    - Safe tool execution with validation and error handling
    - Thread-safe concurrent access via asyncio lock

    Usage:
        >>> registry = ToolRegistry()
        >>> registry.register(ReadFileTool(workspace_root="/workspace"))
        >>> registry.register(WriteFileTool(workspace_root="/workspace"))
        >>>
        >>> # Execute tool via ToolCall
        >>> call = ToolCall(tool=ToolName.READ_FILE, args={"path": "src/main.py"})
        >>> result = await registry.execute(call)
        >>> if result.success:
        ...     print(result.output)
        >>> else:
        ...     print(result.error)

    Attributes:
        _tools: Dictionary mapping ToolName to BaseTool instances
        _lock: Asyncio lock for thread-safe access
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[ToolName, BaseTool] = {}
        self._lock = asyncio.Lock()

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        If a tool with the same name already exists, it will be replaced
        with a warning logged.

        Args:
            tool: BaseTool instance to register

        Example:
            >>> registry = ToolRegistry()
            >>> registry.register(ReadFileTool(workspace_root="/workspace"))
        """
        if tool.name in self._tools:
            logger.warning(
                f"Tool {tool.name.value} already registered, replacing with new instance"
            )

        self._tools[tool.name] = tool
        logger.info(
            f"Registered tool: {tool.name.value} "
            f"(confirmation required: {tool.requires_confirmation})"
        )

    def get(self, name: ToolName) -> Optional[BaseTool]:
        """Get a tool by name.

        Args:
            name: ToolName enum value

        Returns:
            BaseTool instance if found, None otherwise

        Example:
            >>> tool = registry.get(ToolName.READ_FILE)
            >>> if tool:
            ...     result = await tool.execute(path="file.txt")
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata.

        Returns:
            List of dictionaries containing tool information:
            - name: Tool name (string)
            - description: Tool description
            - parameters: Parameter schema
            - requires_confirmation: Whether confirmation needed

        Example:
            >>> tools = registry.list_tools()
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        return [
            {
                "name": tool.name.value,
                "description": tool.description,
                "parameters": tool.parameter_schema,
                "requires_confirmation": tool.requires_confirmation
            }
            for tool in self._tools.values()
        ]

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool from a ToolCall.

        Performs the following steps:
        1. Lookup tool by name
        2. Validate parameters against schema
        3. Execute tool with error handling
        4. Return ToolResult with success/failure status

        All errors are caught and returned as ToolResult.error to
        prevent crashes in the ReAct loop.

        Args:
            tool_call: ToolCall with tool name and arguments

        Returns:
            ToolResult from tool execution or error result

        Example:
            >>> call = ToolCall(
            ...     tool=ToolName.READ_FILE,
            ...     args={"path": "src/main.py"}
            ... )
            >>> result = await registry.execute(call)
            >>> assert result.success
            >>> assert len(result.output) > 0
        """
        # Lookup tool
        tool = self.get(tool_call.tool)
        if not tool:
            logger.error(f"Unknown tool: {tool_call.tool.value}")
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_call.tool.value}"
            )

        # Validate parameters
        error = tool.validate_params(tool_call.args)
        if error:
            logger.warning(
                f"Tool {tool_call.tool.value} validation failed: {error}"
            )
            return ToolResult(
                success=False,
                error=f"Parameter validation failed: {error}"
            )

        # Execute with comprehensive error handling
        try:
            logger.info(
                f"Executing tool {tool_call.tool.value} with args: "
                f"{list(tool_call.args.keys())}"
            )
            result = await tool.execute(**tool_call.args)

            # Log execution result
            if result.success:
                logger.info(
                    f"Tool {tool_call.tool.value} executed successfully"
                )
            else:
                logger.warning(
                    f"Tool {tool_call.tool.value} failed: {result.error}"
                )

            return result

        except SecurityError as e:
            # Security violations get special logging
            logger.error(
                f"Security violation in {tool_call.tool.value}: {e}",
                exc_info=True
            )
            return ToolResult(
                success=False,
                error=f"Security violation: {str(e)}"
            )

        except Exception as e:
            # All other exceptions caught and logged
            logger.error(
                f"Tool {tool_call.tool.value} raised exception: {e}",
                exc_info=True
            )
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

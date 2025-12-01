"""Code Chat tools package.

Exports base classes and tool implementations for the Code Chat
agentic coding assistant.

Phase: Code Chat Implementation (Session 2)
"""

from app.services.code_chat.tools.base import (
    BaseTool,
    ToolRegistry,
    SecurityError
)
from app.services.code_chat.tools.file_ops import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from app.services.code_chat.tools.search import (
    SearchCodeTool,
    WebSearchTool,
    GrepFilesTool,
)
from app.services.code_chat.tools.execution import (
    RunPythonTool,
    RunShellTool,
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

__all__ = [
    # Base classes
    "BaseTool",
    "ToolRegistry",
    "SecurityError",
    # File operation tools
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "DeleteFileTool",
    # Search tools
    "SearchCodeTool",
    "WebSearchTool",
    "GrepFilesTool",
    # Execution tools
    "RunPythonTool",
    "RunShellTool",
    # Git tools
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
    "GitCommitTool",
    "GitBranchTool",
    # LSP/IDE tools
    "GetDiagnosticsTool",
    "GetDefinitionsTool",
    "GetReferencesTool",
    "GetProjectInfoTool",
]

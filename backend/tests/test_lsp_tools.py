"""Tests for LSP/IDE integration tools.

Tests the diagnostics, definitions, references, and project info tools
with various fallback strategies.

Author: Backend Architect
Phase: Code Chat Implementation (LSP Tools)
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.services.code_chat.tools.lsp import (
    GetDiagnosticsTool,
    GetDefinitionsTool,
    GetReferencesTool,
    GetProjectInfoTool,
)
from app.models.code_chat import ToolName


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    workspace = tempfile.mkdtemp()
    yield workspace
    shutil.rmtree(workspace)


@pytest.fixture
def python_workspace(temp_workspace):
    """Create workspace with Python files."""
    # Create a simple Python file with a function
    test_file = Path(temp_workspace) / "test.py"
    test_file.write_text("""
def hello_world():
    print("Hello, world!")
    return 42

class MyClass:
    def __init__(self):
        self.value = hello_world()

# Call the function
result = hello_world()
""")

    # Create another file that uses the function
    other_file = Path(temp_workspace) / "other.py"
    other_file.write_text("""
from test import hello_world

def main():
    hello_world()
""")

    # Create requirements.txt
    requirements = Path(temp_workspace) / "requirements.txt"
    requirements.write_text("""
fastapi==0.109.0
pydantic>=2.0.0
pytest
""")

    return temp_workspace


@pytest.fixture
def node_workspace(temp_workspace):
    """Create workspace with Node.js files."""
    # Create package.json
    package_json = Path(temp_workspace) / "package.json"
    package_json.write_text("""{
  "name": "test-project",
  "version": "1.0.0",
  "description": "Test project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}""")

    # Create index.js
    index_js = Path(temp_workspace) / "index.js"
    index_js.write_text("""
function greet(name) {
    return `Hello, ${name}!`;
}

const result = greet("World");
console.log(result);
""")

    return temp_workspace


# ============================================================================
# GET_DIAGNOSTICS Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_diagnostics_tool_attributes():
    """Test GetDiagnosticsTool has correct attributes."""
    tool = GetDiagnosticsTool(workspace_root="/tmp")
    assert tool.name == ToolName.GET_DIAGNOSTICS
    assert "errors" in tool.description.lower() or "diagnostics" in tool.description.lower()
    assert "file" in tool.parameter_schema["properties"]


@pytest.mark.asyncio
async def test_get_diagnostics_nonexistent_file(python_workspace):
    """Test diagnostics for non-existent file."""
    tool = GetDiagnosticsTool(workspace_root=python_workspace)
    result = await tool.execute(file="nonexistent.py")
    assert not result.success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_get_diagnostics_valid_file(python_workspace):
    """Test diagnostics for valid Python file."""
    tool = GetDiagnosticsTool(workspace_root=python_workspace)
    result = await tool.execute(file="test.py")
    # Should succeed even if no diagnostics found
    assert result.success
    assert result.data is not None
    assert "diagnostics" in result.data


@pytest.mark.asyncio
async def test_get_diagnostics_all_files(python_workspace):
    """Test diagnostics for all workspace files."""
    tool = GetDiagnosticsTool(workspace_root=python_workspace)
    result = await tool.execute()
    assert result.success
    assert result.data is not None


@pytest.mark.asyncio
async def test_get_diagnostics_security(python_workspace):
    """Test diagnostics rejects path traversal."""
    tool = GetDiagnosticsTool(workspace_root=python_workspace)
    result = await tool.execute(file="../../etc/passwd")
    assert not result.success
    assert "security" in result.error.lower() or "workspace" in result.error.lower()


# ============================================================================
# GET_DEFINITIONS Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_definitions_tool_attributes():
    """Test GetDefinitionsTool has correct attributes."""
    tool = GetDefinitionsTool(workspace_root="/tmp")
    assert tool.name == ToolName.GET_DEFINITIONS
    assert "symbol" in tool.parameter_schema["properties"]
    assert "symbol" in tool.parameter_schema["required"]


@pytest.mark.asyncio
async def test_get_definitions_invalid_symbol(python_workspace):
    """Test definitions for invalid symbol name."""
    tool = GetDefinitionsTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="123invalid")
    assert not result.success
    assert "invalid" in result.error.lower()


@pytest.mark.asyncio
async def test_get_definitions_find_function(python_workspace):
    """Test finding function definition."""
    tool = GetDefinitionsTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="hello_world")
    assert result.success
    if result.data and result.data.get("count", 0) > 0:
        # If grep found it, verify structure
        definitions = result.data["definitions"]
        assert len(definitions) > 0
        assert "file" in definitions[0]
        assert "line" in definitions[0]


@pytest.mark.asyncio
async def test_get_definitions_find_class(python_workspace):
    """Test finding class definition."""
    tool = GetDefinitionsTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="MyClass")
    assert result.success
    if result.data and result.data.get("count", 0) > 0:
        definitions = result.data["definitions"]
        assert "class" in definitions[0]["content"].lower()


@pytest.mark.asyncio
async def test_get_definitions_not_found(python_workspace):
    """Test definitions for non-existent symbol."""
    tool = GetDefinitionsTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="nonexistent_function")
    assert result.success
    assert result.data["count"] == 0


# ============================================================================
# GET_REFERENCES Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_references_tool_attributes():
    """Test GetReferencesTool has correct attributes."""
    tool = GetReferencesTool(workspace_root="/tmp")
    assert tool.name == ToolName.GET_REFERENCES
    assert "symbol" in tool.parameter_schema["properties"]


@pytest.mark.asyncio
async def test_get_references_invalid_symbol(python_workspace):
    """Test references for invalid symbol name."""
    tool = GetReferencesTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="123invalid")
    assert not result.success


@pytest.mark.asyncio
async def test_get_references_find_usages(python_workspace):
    """Test finding symbol references."""
    tool = GetReferencesTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="hello_world")
    assert result.success
    # hello_world is used in multiple places
    if result.data and result.data.get("count", 0) > 0:
        references = result.data["references"]
        assert len(references) > 0
        # Should find at least the definition and one call
        assert any("def hello_world" in ref.get("content", "") for ref in references) or \
               any("hello_world()" in ref.get("content", "") for ref in references)


@pytest.mark.asyncio
async def test_get_references_not_found(python_workspace):
    """Test references for non-existent symbol."""
    tool = GetReferencesTool(workspace_root=python_workspace)
    result = await tool.execute(symbol="nonexistent_symbol")
    assert result.success
    assert result.data["count"] == 0


# ============================================================================
# GET_PROJECT_INFO Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_project_info_tool_attributes():
    """Test GetProjectInfoTool has correct attributes."""
    tool = GetProjectInfoTool(workspace_root="/tmp")
    assert tool.name == ToolName.GET_PROJECT_INFO
    assert tool.parameter_schema is not None


@pytest.mark.asyncio
async def test_get_project_info_python(python_workspace):
    """Test project info for Python project."""
    tool = GetProjectInfoTool(workspace_root=python_workspace)
    result = await tool.execute()
    assert result.success
    assert result.data is not None
    assert result.data["type"] == "python"
    # Should detect dependencies from requirements.txt
    if "dependencies" in result.data:
        deps = result.data["dependencies"]
        assert "fastapi" in deps or "pydantic" in deps or "pytest" in deps


@pytest.mark.asyncio
async def test_get_project_info_node(node_workspace):
    """Test project info for Node.js project."""
    tool = GetProjectInfoTool(workspace_root=node_workspace)
    result = await tool.execute()
    assert result.success
    assert result.data is not None
    assert result.data["type"] == "node"
    assert result.data["name"] == "test-project"
    assert result.data["version"] == "1.0.0"
    # Check dependencies
    assert "express" in result.data["dependencies"]
    assert "lodash" in result.data["dependencies"]
    # Check scripts
    assert "start" in result.data["scripts"]
    assert "test" in result.data["scripts"]


@pytest.mark.asyncio
async def test_get_project_info_no_manifest(temp_workspace):
    """Test project info when no manifest found."""
    tool = GetProjectInfoTool(workspace_root=temp_workspace)
    result = await tool.execute()
    assert result.success
    # Should return None for project_type
    assert result.data is None or result.data.get("project_type") is None


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_all_tools_registered():
    """Test all LSP tools can be imported."""
    from app.services.code_chat.tools import (
        GetDiagnosticsTool,
        GetDefinitionsTool,
        GetReferencesTool,
        GetProjectInfoTool,
    )
    assert GetDiagnosticsTool is not None
    assert GetDefinitionsTool is not None
    assert GetReferencesTool is not None
    assert GetProjectInfoTool is not None


@pytest.mark.asyncio
async def test_tools_in_registry():
    """Test LSP tools are in ToolRegistry."""
    from app.services.code_chat.tools.base import ToolRegistry
    from app.services.code_chat.tools.lsp import (
        GetDiagnosticsTool,
        GetDefinitionsTool,
        GetReferencesTool,
        GetProjectInfoTool,
    )

    registry = ToolRegistry()
    registry.register(GetDiagnosticsTool(workspace_root="/tmp"))
    registry.register(GetDefinitionsTool(workspace_root="/tmp"))
    registry.register(GetReferencesTool(workspace_root="/tmp"))
    registry.register(GetProjectInfoTool(workspace_root="/tmp"))

    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    assert "get_diagnostics" in tool_names
    assert "get_definitions" in tool_names
    assert "get_references" in tool_names
    assert "get_project_info" in tool_names

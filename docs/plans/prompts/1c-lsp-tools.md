# Task: Implement LSP MCP Tools for Code Chat

You are implementing Language Server Protocol tools that provide code diagnostics, definitions, and references to the ReAct agent.

## Context

- Tool types defined in: `frontend/src/types/codeChat.ts` (get_diagnostics, get_definitions, get_references, get_project_info)
- Sandbox container: `sandbox/Dockerfile`
- Tool base: `backend/app/services/code_chat/tools/base.py`
- Read SESSION_NOTES.md for recent context

## Requirements

### Part 1: Docker Setup

**sandbox/Dockerfile additions:**

```dockerfile
# Add after existing pip install
RUN pip install pyright

# Or for npm-based pyright:
# RUN npm install -g pyright
```

### Part 2: lsp.py (~280 lines) - Create 4 tool classes

#### 1. GetDiagnosticsTool

```python
class GetDiagnosticsTool(BaseTool):
    """Runs static analysis and returns diagnostics."""
    name = "get_diagnostics"
    description = "Get type errors, lint issues, and other diagnostics for a file."

    async def execute(self, file_path: str) -> ToolResult:
        # Determine language from extension
        # Run appropriate analyzer:
        #   - Python: pyright --outputjson
        #   - JS/TS: eslint (if available)
        # Parse JSON output
        # Return list of diagnostics
```

- Parameters: `file_path` (str)
- Returns: List of `{line, column, severity, message, code}`

**Implementation for Python:**
```python
import subprocess
import json

result = subprocess.run(
    ["pyright", "--outputjson", file_path],
    capture_output=True,
    text=True,
    timeout=60,
    cwd=self.workspace
)

# Parse pyright JSON output
data = json.loads(result.stdout)
diagnostics = []
for diag in data.get("generalDiagnostics", []):
    diagnostics.append({
        "line": diag.get("range", {}).get("start", {}).get("line", 0),
        "column": diag.get("range", {}).get("start", {}).get("character", 0),
        "severity": diag.get("severity", "error"),
        "message": diag.get("message", ""),
        "code": diag.get("rule", "")
    })
```

#### 2. GetDefinitionsTool

```python
class GetDefinitionsTool(BaseTool):
    """Finds definition location for symbol at position."""
    name = "get_definitions"
    description = "Find where a symbol is defined."

    async def execute(self, file_path: str, line: int, column: int) -> ToolResult:
        # Use AST parsing for Python
        # Or language server if available
        # Return definition location
```

- Parameters: `file_path` (str), `line` (int), `column` (int)
- Returns: `{file, line, column}` or null if not found

**Note:** This is complex without a running language server. For MVP, use Python's AST module for Python files:
- Parse file into AST
- Find symbol at position
- Trace imports and class definitions
- Return location

#### 3. GetReferencesTool

```python
class GetReferencesTool(BaseTool):
    """Finds all references to symbol."""
    name = "get_references"
    description = "Find all usages of a symbol across the codebase."

    async def execute(self, file_path: str, line: int, column: int) -> ToolResult:
        # Extract symbol name at position
        # Use grep/ripgrep to find references
        # Filter to actual references (not just string matches)
        # Return list of locations
```

- Parameters: `file_path` (str), `line` (int), `column` (int)
- Returns: List of `{file, line, column}`

**MVP Implementation:**
```python
# Extract symbol at position
with open(file_path) as f:
    lines = f.readlines()
    line_content = lines[line - 1]
    # Extract word at column position

# Use ripgrep for speed
result = subprocess.run(
    ["rg", "-n", "--json", symbol_name, self.workspace],
    capture_output=True,
    text=True
)
# Parse JSON output
```

#### 4. GetProjectInfoTool

```python
class GetProjectInfoTool(BaseTool):
    """Analyzes project structure."""
    name = "get_project_info"
    description = "Detect project language, framework, and structure."

    async def execute(self) -> ToolResult:
        # Check for package.json -> Node.js
        # Check for pyproject.toml/setup.py -> Python
        # Check for Cargo.toml -> Rust
        # Detect framework from dependencies
        # Find entry points
```

- Parameters: None
- Returns: `{language, framework, package_manager, entry_points, dependencies}`

**Detection logic:**
```python
from pathlib import Path
import json
import tomllib

workspace = Path(self.workspace)
info = {
    "language": "unknown",
    "framework": None,
    "package_manager": None,
    "entry_points": [],
    "dependencies": []
}

# Python detection
if (workspace / "pyproject.toml").exists():
    info["language"] = "python"
    info["package_manager"] = "poetry" or "pip"
    # Parse pyproject.toml for framework detection

# Node.js detection
if (workspace / "package.json").exists():
    info["language"] = "javascript"
    with open(workspace / "package.json") as f:
        pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "react" in deps:
            info["framework"] = "react"
        elif "vue" in deps:
            info["framework"] = "vue"
```

## Graceful Degradation

If pyright or other tools aren't available, return helpful message:

```python
async def execute(self, file_path: str) -> ToolResult:
    try:
        # Check if pyright is available
        subprocess.run(["pyright", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ToolResult(
            success=False,
            error="pyright not installed. Python diagnostics unavailable."
        )
```

## Acceptance Criteria

- [ ] get_diagnostics returns type errors for Python files
- [ ] get_diagnostics handles files without errors (returns empty list)
- [ ] get_definitions finds symbol definitions (at least for Python imports)
- [ ] get_references finds all usages (using ripgrep fallback)
- [ ] get_project_info detects Python/Node.js projects
- [ ] get_project_info detects common frameworks (React, FastAPI, etc.)
- [ ] Graceful error when pyright unavailable
- [ ] Proper timeout handling (60s for diagnostics)

## Files

- **MODIFY:** `sandbox/Dockerfile` (add pyright)
- **CREATE:** `backend/app/services/code_chat/tools/lsp.py`
- **MODIFY:** `backend/app/services/code_chat/tools/__init__.py`
- **MODIFY:** `backend/app/routers/code_chat.py`

## Priority Note

If time is limited, implement in this order:
1. GetDiagnosticsTool (most valuable)
2. GetProjectInfoTool (useful for context)
3. GetReferencesTool (grep-based is acceptable)
4. GetDefinitionsTool (complex, can be simplified)

# Task: Implement run_shell Tool for Code Chat

You are implementing a sandboxed shell execution tool for the ReAct agent. **Security is CRITICAL.**

## Context

- Existing RunPythonTool in: `backend/app/services/code_chat/tools/execution.py`
- Sandbox server: `sandbox/server.py`
- Tool type defined in: `frontend/src/types/codeChat.ts` (run_shell)
- Read SESSION_NOTES.md for recent context

## Security Requirements (CRITICAL)

### Allowed Commands (Whitelist)

**Read-only/Safe commands:**
```python
ALLOWED_COMMANDS = {
    # File inspection
    "ls", "cat", "head", "tail", "less", "file", "stat",
    # Search
    "find", "grep", "rg", "awk", "sed",
    # Text processing
    "wc", "sort", "uniq", "cut", "tr", "diff",
    # Info
    "pwd", "which", "whoami", "date", "env",
}
```

**BLOCKED commands (never allow):**
```python
BLOCKED_COMMANDS = {
    # Destructive
    "rm", "rmdir", "mv", "cp", "mkdir", "touch",
    # System modification
    "chmod", "chown", "chgrp", "kill", "pkill",
    # Network
    "wget", "curl", "nc", "ssh", "scp", "rsync",
    # Execution
    "python", "python3", "node", "bash", "sh", "exec",
    # Package managers
    "pip", "npm", "apt", "brew", "yum",
}
```

### Argument Validation

Block shell metacharacters that could enable injection:
```python
DANGEROUS_CHARS = {';', '|', '&&', '||', '$', '`', '$(', '>', '<', '>>'}

def validate_command(command: str) -> bool:
    for char in DANGEROUS_CHARS:
        if char in command:
            return False
    return True
```

### Working Directory Restriction

All commands must run within workspace:
```python
cwd = Path(workspace).resolve()
# Commands like 'cd' should be blocked or workspace-relative
```

## Requirements

### execution.py additions (~100 lines)

```python
import shlex
from typing import Set

class RunShellTool(BaseTool):
    """Run whitelisted shell commands in sandbox."""
    name = "run_shell"
    description = "Run read-only shell commands like ls, cat, grep, find."

    ALLOWED_COMMANDS: Set[str] = {
        "ls", "cat", "head", "tail", "less", "file", "stat",
        "find", "grep", "rg", "awk", "sed",
        "wc", "sort", "uniq", "cut", "tr", "diff",
        "pwd", "which", "whoami", "date", "env",
    }

    DANGEROUS_CHARS = {';', '|', '&&', '||', '$', '`', '$(', '${', '>', '<', '>>'}

    def validate_command(self, command: str) -> tuple[bool, str]:
        """Validate command is safe to execute.

        Returns:
            (is_valid, error_message)
        """
        # Check for dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in command:
                return False, f"Blocked: shell metacharacter '{char}' not allowed"

        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

        if not parts:
            return False, "Empty command"

        # Check command is in whitelist
        cmd = parts[0]
        if cmd not in self.ALLOWED_COMMANDS:
            return False, f"Command '{cmd}' not in whitelist. Allowed: {', '.join(sorted(self.ALLOWED_COMMANDS))}"

        return True, ""

    async def execute(self, command: str) -> ToolResult:
        # Validate command
        is_valid, error = self.validate_command(command)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Security: {error}"
            )

        # Call sandbox /shell endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.sandbox_url}/shell",
                    json={
                        "command": command,
                        "workspace": str(self.workspace),
                        "timeout": 30
                    },
                    timeout=35
                )
                result = response.json()
                return ToolResult(
                    success=result.get("success", False),
                    output=result.get("stdout", ""),
                    error=result.get("stderr") if not result.get("success") else None
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### sandbox/server.py additions

```python
from fastapi import FastAPI
import subprocess
import shlex

app = FastAPI()

# Re-use same whitelist
ALLOWED_COMMANDS = {...}
DANGEROUS_CHARS = {...}

class ShellRequest(BaseModel):
    command: str
    workspace: str
    timeout: int = 30

@app.post("/shell")
async def execute_shell(request: ShellRequest):
    """Execute whitelisted shell command."""

    # Double-check validation (defense in depth)
    for char in DANGEROUS_CHARS:
        if char in request.command:
            return {"success": False, "stderr": f"Blocked: '{char}' not allowed"}

    parts = shlex.split(request.command)
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        return {"success": False, "stderr": f"Command not allowed"}

    # Validate workspace exists
    workspace = Path(request.workspace)
    if not workspace.exists():
        return {"success": False, "stderr": "Workspace not found"}

    try:
        result = subprocess.run(
            parts,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=request.timeout
        )

        # Log for audit
        logger.info(f"Shell command: {request.command} in {workspace}")

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": "Command timed out"}
    except Exception as e:
        return {"success": False, "stderr": str(e)}
```

## Testing

### Security Tests

```python
@pytest.mark.asyncio
async def test_shell_blocks_rm():
    tool = RunShellTool(workspace="/workspace")
    result = await tool.execute("rm -rf /")
    assert not result.success
    assert "not in whitelist" in result.error

@pytest.mark.asyncio
async def test_shell_blocks_pipe():
    tool = RunShellTool(workspace="/workspace")
    result = await tool.execute("ls | cat")
    assert not result.success
    assert "metacharacter" in result.error

@pytest.mark.asyncio
async def test_shell_blocks_command_substitution():
    tool = RunShellTool(workspace="/workspace")
    result = await tool.execute("echo $(cat /etc/passwd)")
    assert not result.success

@pytest.mark.asyncio
async def test_shell_allows_ls():
    tool = RunShellTool(workspace="/tmp")
    result = await tool.execute("ls -la")
    assert result.success

@pytest.mark.asyncio
async def test_shell_allows_grep():
    tool = RunShellTool(workspace="/workspace")
    result = await tool.execute("grep -r TODO .")
    assert result.success
```

## Acceptance Criteria

- [ ] Whitelisted commands execute successfully (ls, cat, grep, find, etc.)
- [ ] Blocked commands return clear error with whitelist
- [ ] Shell metacharacters (;, |, &&, $, etc.) are blocked
- [ ] Commands only run in workspace directory
- [ ] 30 second timeout works correctly
- [ ] All commands logged for audit
- [ ] Defense in depth: validation in both tool AND sandbox

## Files

- **MODIFY:** `backend/app/services/code_chat/tools/execution.py`
- **MODIFY:** `sandbox/server.py`
- **MODIFY:** `backend/app/services/code_chat/tools/__init__.py`
- **MODIFY:** `backend/app/routers/code_chat.py`

## Security Checklist

- [ ] Command whitelist is restrictive (read-only commands only)
- [ ] Shell metacharacters blocked
- [ ] No path traversal possible
- [ ] Timeout prevents hanging
- [ ] All commands logged
- [ ] Validation happens in BOTH tool and sandbox
- [ ] Error messages don't leak system info

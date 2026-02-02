"""
S.Y.N.A.P.S.E. ENGINE - Sandboxed Python Execution Server

Provides isolated Python code execution with security restrictions:
- Blocked dangerous imports (os, subprocess, socket, etc.)
- Limited builtins (no exec, eval, compile)
- Memory limit: 512MB
- CPU timeout: configurable (max 30s)
- Output capture
"""

import ast
import time
import signal
import resource
import traceback
from io import StringIO
from typing import Optional, Set
from contextlib import redirect_stdout, redirect_stderr

from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

# =============================================================================
# Configuration
# =============================================================================

app = FastAPI(
    title="Synapse Sandbox",
    description="Isolated Python execution environment",
    version="1.0.0",
)

# Safe builtins that don't provide system access
SAFE_BUILTINS: Set[str] = {
    # Basic types
    "True",
    "False",
    "None",
    "int",
    "float",
    "str",
    "bool",
    "bytes",
    "bytearray",
    "list",
    "tuple",
    "dict",
    "set",
    "frozenset",
    "complex",
    "memoryview",
    # Type operations
    "type",
    "isinstance",
    "issubclass",
    "callable",
    "hasattr",
    "getattr",
    "setattr",
    "delattr",
    # Iteration
    "range",
    "enumerate",
    "zip",
    "map",
    "filter",
    "iter",
    "next",
    "reversed",
    "sorted",
    # Math
    "abs",
    "round",
    "pow",
    "divmod",
    "sum",
    "min",
    "max",
    "bin",
    "hex",
    "oct",
    "ord",
    "chr",
    # String/repr
    "repr",
    "ascii",
    "format",
    "print",
    "input",
    # Collections
    "len",
    "slice",
    "all",
    "any",
    # Object
    "object",
    "super",
    "property",
    "staticmethod",
    "classmethod",
    # ID/hash
    "id",
    "hash",
    # Exceptions (read-only)
    "Exception",
    "BaseException",
    "TypeError",
    "ValueError",
    "AttributeError",
    "KeyError",
    "IndexError",
    "RuntimeError",
    "StopIteration",
    "GeneratorExit",
    "ZeroDivisionError",
    "OverflowError",
    "FloatingPointError",
    "AssertionError",
    "ImportError",
    "ModuleNotFoundError",
    "NameError",
    "UnboundLocalError",
    "NotImplementedError",
    "RecursionError",
}

# Allowed imports (safe modules only)
ALLOWED_IMPORTS: Set[str] = {
    # Standard library (safe)
    "math",
    "cmath",
    "datetime",
    "calendar",
    "json",
    "re",
    "collections",
    "collections.abc",
    "itertools",
    "functools",
    "operator",
    "string",
    "textwrap",
    "random",
    "statistics",
    "decimal",
    "fractions",
    "numbers",
    "copy",
    "pprint",
    "typing",
    "typing_extensions",
    "dataclasses",
    "enum",
    "abc",
    "contextlib",
    "heapq",
    "bisect",
    "array",
    "struct",
    "hashlib",  # Read-only hashing
    "base64",
    "binascii",
    "unicodedata",
    "difflib",
    # Data science
    "numpy",
    "np",
    "pandas",
    "pd",
    "matplotlib",
    "matplotlib.pyplot",
    "plt",
    "sympy",
    "scipy",
    "scipy.stats",
    "scipy.optimize",
    "scipy.integrate",
}

# Forbidden imports (security critical)
FORBIDDEN_IMPORTS: Set[str] = {
    # System access
    "os",
    "sys",
    "platform",
    "sysconfig",
    "subprocess",
    "shlex",
    "multiprocessing",
    "threading",
    "concurrent",
    "asyncio",
    "async_generator",
    # Network
    "socket",
    "ssl",
    "urllib",
    "urllib.request",
    "urllib.parse",
    "http",
    "http.client",
    "http.server",
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "nntplib",
    "email",
    "mailbox",
    "requests",
    "httpx",
    "aiohttp",
    # File system
    "pathlib",
    "shutil",
    "tempfile",
    "glob",
    "fnmatch",
    "fileinput",
    "filecmp",
    "io",  # Can be used for file-like operations
    # Code execution
    "importlib",
    "pkgutil",
    "modulefinder",
    "runpy",
    "compileall",
    "ast",
    "dis",
    "code",
    "codeop",
    "compile",
    "exec",
    "eval",
    # Serialization (can execute code)
    "pickle",
    "shelve",
    "marshal",
    "copyreg",
    "dbm",
    "sqlite3",
    # Introspection
    "inspect",
    "traceback",
    "linecache",
    "gc",
    "weakref",
    # C interface
    "ctypes",
    "cffi",
    "ffi",
    # Process/signals
    "signal",
    "resource",
    "pty",
    "tty",
    "termios",
    # Debugging
    "pdb",
    "bdb",
    "profile",
    "pstats",
    "timeit",
    "trace",
    # Web/HTML
    "html",
    "xml",
    "webbrowser",
    "cgi",
    "cgitb",
    # Other dangerous
    "builtins",
    "__builtins__",
    "warnings",  # Can suppress errors
    "logging",  # Can access files
    "configparser",
    "atexit",
}


# =============================================================================
# Models
# =============================================================================


class ExecuteRequest(BaseModel):
    """Request to execute Python code."""

    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(
        default=30, ge=1, le=30, description="Timeout in seconds (max 30)"
    )


class ExecuteResponse(BaseModel):
    """Response from code execution."""

    output: str = Field(..., description="Captured stdout/stderr")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


# =============================================================================
# Security Validation
# =============================================================================


def validate_code(code: str) -> Optional[str]:
    """
    Validate code for dangerous operations.
    Returns error message if validation fails, None if code is safe.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"

    for node in ast.walk(tree):
        # Check import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in FORBIDDEN_IMPORTS:
                    return f"Import blocked (security): {alias.name}"
                if module not in ALLOWED_IMPORTS and alias.name not in ALLOWED_IMPORTS:
                    return f"Import not allowed: {alias.name}"

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if module in FORBIDDEN_IMPORTS or node.module in FORBIDDEN_IMPORTS:
                    return f"Import blocked (security): from {node.module}"
                if module not in ALLOWED_IMPORTS and node.module not in ALLOWED_IMPORTS:
                    return f"Import not allowed: from {node.module}"

        # Block dangerous function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ("exec", "eval", "compile", "__import__", "open"):
                    return f"Function blocked (security): {node.func.id}()"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in (
                    "system",
                    "popen",
                    "spawn",
                    "fork",
                    "execv",
                    "execve",
                    "execvp",
                    "spawnl",
                    "spawnle",
                ):
                    return f"Method blocked (security): .{node.func.attr}()"

        # Block attribute access to dangerous objects
        if isinstance(node, ast.Attribute):
            if node.attr in (
                "__class__",
                "__bases__",
                "__subclasses__",
                "__mro__",
                "__globals__",
                "__code__",
                "__builtins__",
                "__dict__",
            ):
                return f"Attribute access blocked (security): .{node.attr}"

    return None


class TimeoutError(Exception):
    """Raised when code execution times out."""

    pass


def timeout_handler(signum, frame):
    """Signal handler for execution timeout."""
    raise TimeoutError("Execution timed out")


# =============================================================================
# Safe Import Function
# =============================================================================


def create_safe_import():
    """
    Create a restricted __import__ function that only allows safe modules.
    This enables 'import' statements for whitelisted modules only.
    """
    original_import = (
        __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
    )

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        """Import function that only allows whitelisted modules."""
        # Get the base module name
        base_module = name.split(".")[0]

        # Check if module is explicitly forbidden
        if base_module in FORBIDDEN_IMPORTS or name in FORBIDDEN_IMPORTS:
            raise ImportError(f"Import blocked (security): {name}")

        # Check if module is allowed
        if base_module not in ALLOWED_IMPORTS and name not in ALLOWED_IMPORTS:
            raise ImportError(f"Import not allowed: {name}")

        # Allow the import
        return original_import(name, globals, locals, fromlist, level)

    return safe_import


# =============================================================================
# Execution
# =============================================================================


def execute_code(code: str, timeout: int = 30) -> ExecuteResponse:
    """
    Execute Python code in a restricted environment.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        ExecuteResponse with output, error, and timing
    """
    # Validate code first
    error = validate_code(code)
    if error:
        return ExecuteResponse(output="", error=error, execution_time_ms=0)

    # Set CPU time limit (Docker handles memory limits)
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
    except Exception:
        pass  # May fail in some environments

    # Set signal-based timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    # Capture output
    output_buffer = StringIO()
    error_msg = None
    start_time = time.time()

    try:
        # Build restricted builtins
        import builtins

        restricted_builtins = {}
        for name in SAFE_BUILTINS:
            if hasattr(builtins, name):
                restricted_builtins[name] = getattr(builtins, name)

        # Add safe __import__ to allow whitelisted modules
        restricted_builtins["__import__"] = create_safe_import()

        # Create restricted globals
        restricted_globals = {
            "__builtins__": restricted_builtins,
            "__name__": "__main__",
            "__doc__": None,
        }

        # Execute with captured output
        with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
            exec(code, restricted_globals)

    except TimeoutError:
        error_msg = "Execution timed out (exceeded time limit)"
    except MemoryError:
        error_msg = "Memory limit exceeded (container limit)"
    except RecursionError:
        error_msg = "Maximum recursion depth exceeded"
    except Exception:
        # Format error with traceback (but sanitize paths)
        tb = traceback.format_exc()
        # Remove file paths for security
        tb_lines = []
        for line in tb.split("\n"):
            if 'File "' in line:
                line = line.replace("/app/", "").replace("/home/", "")
            tb_lines.append(line)
        error_msg = "\n".join(tb_lines)
    finally:
        # Restore signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    execution_time = (time.time() - start_time) * 1000

    return ExecuteResponse(
        output=output_buffer.getvalue(),
        error=error_msg,
        execution_time_ms=round(execution_time, 2),
    )


# =============================================================================
# API Endpoints
# =============================================================================


@app.post("/execute", response_model=ExecuteResponse)
async def execute_endpoint(request: ExecuteRequest) -> ExecuteResponse:
    """
    Execute Python code in sandbox.

    Security features:
    - Blocked dangerous imports (os, subprocess, socket, etc.)
    - Limited builtins (no exec, eval, compile)
    - Memory limit: 512MB
    - CPU timeout: configurable (max 30s)
    """
    return execute_code(request.code, request.timeout)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "synapse_sandbox", "version": "1.0.0"}


@app.get("/allowed-imports")
async def allowed_imports():
    """List allowed imports for user reference."""
    return {
        "allowed": sorted(ALLOWED_IMPORTS),
        "note": "Only these modules can be imported. System, network, and file access is blocked.",
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

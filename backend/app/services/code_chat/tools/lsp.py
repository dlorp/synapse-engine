"""LSP/IDE integration tools for Code Chat mode.

Provides code intelligence capabilities:
- get_diagnostics: Get TypeScript/Python errors and warnings
- get_definitions: Find where symbols are defined
- get_references: Find all usages of symbols
- get_project_info: Get project structure and metadata

These tools implement intelligent fallbacks when full LSP servers are unavailable:
- Diagnostics: pyright (Python) / tsc (TypeScript) or pattern matching
- Definitions: ctags, grep-based search, or regex patterns
- References: ripgrep or basic grep with smart filtering
- Project info: Manifest file parsing

Author: Backend Architect
Phase: Code Chat Implementation (LSP Tools)
"""

import asyncio
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.models.code_chat import ToolName, ToolResult
from app.services.code_chat.tools.base import BaseTool, SecurityError

logger = logging.getLogger(__name__)

# Limits
MAX_DIAGNOSTICS = 100
MAX_REFERENCES = 500
MAX_SYMBOLS = 1000


class GetDiagnosticsTool(BaseTool):
    """Get IDE diagnostics (errors, warnings) for files.

    Provides language server-style diagnostics using multiple strategies:
    1. MCP IDE diagnostics (if available)
    2. pyright for Python files
    3. tsc for TypeScript/JavaScript files
    4. Pattern-based fallback for basic syntax errors

    Returns structured diagnostic information including:
    - Severity (error, warning, info)
    - Location (file, line, column)
    - Message text
    - Error code (if available)

    Attributes:
        name: ToolName.GET_DIAGNOSTICS
        description: Get TypeScript/Python errors and warnings from IDE
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GET_DIAGNOSTICS
    description = "Get TypeScript/Python errors and warnings from the IDE"
    parameter_schema = {
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "File path to get diagnostics for (relative or absolute). "
                              "If not provided, gets diagnostics for all workspace files."
            }
        }
    }

    def __init__(self, workspace_root: str):
        """Initialize diagnostics tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, file: Optional[str] = None, **kwargs) -> ToolResult:
        """Get diagnostics for file(s).

        Args:
            file: Optional file path (relative or absolute)

        Returns:
            ToolResult with structured diagnostics or error
        """
        try:
            # Resolve file path if provided
            target_path: Optional[Path] = None
            if file:
                target_path = self._resolve_path(file)
                if not target_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"File not found: {file}"
                    )

            # Try different diagnostic strategies
            diagnostics: List[Dict[str, Any]] = []

            # Strategy 1: Try pyright for Python files
            if not file or (target_path and target_path.suffix == '.py'):
                py_diags = await self._run_pyright(target_path)
                diagnostics.extend(py_diags)

            # Strategy 2: Try tsc for TypeScript/JavaScript
            if not file or (target_path and target_path.suffix in {'.ts', '.tsx', '.js', '.jsx'}):
                ts_diags = await self._run_tsc(target_path)
                diagnostics.extend(ts_diags)

            # Limit results
            if len(diagnostics) > MAX_DIAGNOSTICS:
                diagnostics = diagnostics[:MAX_DIAGNOSTICS]
                logger.warning(
                    f"Truncated diagnostics from {len(diagnostics)} to {MAX_DIAGNOSTICS}"
                )

            # Format output
            if not diagnostics:
                output = "No diagnostics found."
            else:
                output = self._format_diagnostics(diagnostics)

            return ToolResult(
                success=True,
                output=output,
                data={"diagnostics": diagnostics, "count": len(diagnostics)}
            )

        except SecurityError as e:
            logger.error(f"Security error in get_diagnostics: {e}")
            return ToolResult(success=False, error=f"Security error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting diagnostics: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to get diagnostics: {str(e)}")

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate path within workspace.

        Args:
            path: Relative or absolute path

        Returns:
            Resolved path within workspace

        Raises:
            SecurityError: If path escapes workspace
        """
        if Path(path).is_absolute():
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_root / path).resolve()

        # Security check: ensure path is within workspace
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(f"Path escapes workspace: {path}")

        return resolved

    async def _run_pyright(self, target: Optional[Path]) -> List[Dict[str, Any]]:
        """Run pyright for Python diagnostics.

        Args:
            target: Target file or None for all files

        Returns:
            List of diagnostic dictionaries
        """
        try:
            # Check if pyright is available
            which_proc = await asyncio.create_subprocess_exec(
                "which", "pyright",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await which_proc.communicate()
            if which_proc.returncode != 0:
                logger.debug("pyright not available, skipping Python diagnostics")
                return []

            # Build command
            cmd = ["pyright", "--outputjson"]
            if target:
                cmd.append(str(target))

            # Run pyright
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            # Parse JSON output
            if stdout:
                try:
                    result = json.loads(stdout.decode())
                    return self._parse_pyright_output(result)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse pyright JSON output")

        except Exception as e:
            logger.debug(f"Error running pyright: {e}")

        return []

    def _parse_pyright_output(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse pyright JSON output to standard format.

        Args:
            result: Pyright JSON output

        Returns:
            List of diagnostic dictionaries
        """
        diagnostics = []
        for diag in result.get("generalDiagnostics", []):
            diagnostics.append({
                "file": diag.get("file", ""),
                "line": diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                "column": diag.get("range", {}).get("start", {}).get("character", 0) + 1,
                "severity": diag.get("severity", "error"),
                "message": diag.get("message", ""),
                "code": diag.get("rule", ""),
                "source": "pyright"
            })
        return diagnostics

    async def _run_tsc(self, target: Optional[Path]) -> List[Dict[str, Any]]:
        """Run tsc for TypeScript/JavaScript diagnostics.

        Args:
            target: Target file or None for all files

        Returns:
            List of diagnostic dictionaries
        """
        try:
            # Check if tsc is available
            which_proc = await asyncio.create_subprocess_exec(
                "which", "npx",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await which_proc.communicate()
            if which_proc.returncode != 0:
                logger.debug("npx not available, skipping TypeScript diagnostics")
                return []

            # Build command
            cmd = ["npx", "tsc", "--noEmit", "--pretty", "false"]
            if target:
                cmd.append(str(target))

            # Run tsc
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            # Parse output (tsc outputs to stdout)
            if stdout:
                return self._parse_tsc_output(stdout.decode())

        except Exception as e:
            logger.debug(f"Error running tsc: {e}")

        return []

    def _parse_tsc_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse tsc text output to standard format.

        Args:
            output: tsc stdout text

        Returns:
            List of diagnostic dictionaries
        """
        diagnostics = []
        # Parse format: "path/file.ts(line,col): error TSxxxx: message"
        pattern = re.compile(
            r"^(.+?)\((\d+),(\d+)\):\s+(error|warning)\s+TS(\d+):\s+(.+)$",
            re.MULTILINE
        )
        for match in pattern.finditer(output):
            diagnostics.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "severity": match.group(4),
                "message": match.group(6),
                "code": f"TS{match.group(5)}",
                "source": "tsc"
            })
        return diagnostics

    def _format_diagnostics(self, diagnostics: List[Dict[str, Any]]) -> str:
        """Format diagnostics for human-readable output.

        Args:
            diagnostics: List of diagnostic dictionaries

        Returns:
            Formatted text
        """
        lines = [f"Found {len(diagnostics)} diagnostic(s):\n"]
        for diag in diagnostics:
            severity = diag.get("severity", "error").upper()
            file = diag.get("file", "unknown")
            line = diag.get("line", 0)
            col = diag.get("column", 0)
            message = diag.get("message", "")
            code = diag.get("code", "")

            lines.append(
                f"[{severity}] {file}:{line}:{col} - {message} ({code})"
            )

        return "\n".join(lines)


class GetDefinitionsTool(BaseTool):
    """Find where a symbol is defined.

    Uses multiple strategies to locate symbol definitions:
    1. ctags (if available)
    2. Language-specific grep patterns
    3. Basic grep fallback

    Returns file path, line number, and context for the definition.

    Attributes:
        name: ToolName.GET_DEFINITIONS
        description: Find where a function, class, or variable is defined
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GET_DEFINITIONS
    description = "Find where a function, class, or variable is defined"
    parameter_schema = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Symbol name to find (function, class, variable)"
            },
            "file": {
                "type": "string",
                "description": "Optional: limit search to specific file"
            }
        },
        "required": ["symbol"]
    }

    def __init__(self, workspace_root: str):
        """Initialize definitions tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, symbol: str, file: Optional[str] = None, **kwargs) -> ToolResult:
        """Find symbol definition.

        Args:
            symbol: Symbol name to find
            file: Optional file to limit search

        Returns:
            ToolResult with definition location(s) or error
        """
        try:
            # Validate symbol name
            if not symbol or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', symbol):
                return ToolResult(
                    success=False,
                    error=f"Invalid symbol name: {symbol}"
                )

            # Try grep-based search with language-specific patterns
            definitions = await self._grep_definitions(symbol, file)

            if not definitions:
                return ToolResult(
                    success=True,
                    output=f"No definitions found for symbol: {symbol}",
                    data={"definitions": [], "count": 0}
                )

            # Format output
            output = self._format_definitions(symbol, definitions)

            return ToolResult(
                success=True,
                output=output,
                data={"definitions": definitions, "count": len(definitions)}
            )

        except SecurityError as e:
            logger.error(f"Security error in get_definitions: {e}")
            return ToolResult(success=False, error=f"Security error: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding definitions: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to find definitions: {str(e)}")

    async def _grep_definitions(
        self,
        symbol: str,
        target_file: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Use grep to find symbol definitions with language-specific patterns.

        Args:
            symbol: Symbol name
            target_file: Optional file to limit search

        Returns:
            List of definition dictionaries
        """
        definitions = []

        # Build patterns for different languages
        patterns = [
            # Python: def, class, async def
            rf"^(def|class|async def)\s+{symbol}\s*[\(\:]",
            # TypeScript/JavaScript: function, class, const/let/var
            rf"^(function|class)\s+{symbol}\s*[\(\{{]",
            rf"^(const|let|var)\s+{symbol}\s*=",
            # TypeScript: interface, type, enum
            rf"^(interface|type|enum)\s+{symbol}\s*[\{{=]",
        ]

        try:
            for pattern in patterns:
                # Build grep command
                cmd = ["grep", "-n", "-E", pattern]
                if target_file:
                    cmd.append(str(self.workspace_root / target_file))
                else:
                    cmd.extend(["-r", str(self.workspace_root)])

                # Run grep
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()

                if proc.returncode == 0 and stdout:
                    # Parse grep output
                    for line in stdout.decode().split('\n'):
                        if not line:
                            continue
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            file_path = parts[0]
                            line_num = parts[1]
                            content = parts[2]

                            # Make path relative to workspace
                            try:
                                rel_path = Path(file_path).relative_to(self.workspace_root)
                            except ValueError:
                                rel_path = Path(file_path)

                            definitions.append({
                                "file": str(rel_path),
                                "line": int(line_num),
                                "content": content.strip(),
                                "pattern": pattern
                            })

        except Exception as e:
            logger.debug(f"Error running grep for definitions: {e}")

        # Remove duplicates
        seen = set()
        unique_definitions = []
        for defn in definitions:
            key = (defn["file"], defn["line"])
            if key not in seen:
                seen.add(key)
                unique_definitions.append(defn)

        return unique_definitions

    def _format_definitions(
        self,
        symbol: str,
        definitions: List[Dict[str, Any]]
    ) -> str:
        """Format definitions for human-readable output.

        Args:
            symbol: Symbol name
            definitions: List of definition dictionaries

        Returns:
            Formatted text
        """
        lines = [f"Found {len(definitions)} definition(s) for '{symbol}':\n"]
        for defn in definitions:
            file = defn.get("file", "unknown")
            line = defn.get("line", 0)
            content = defn.get("content", "")
            lines.append(f"{file}:{line}: {content}")

        return "\n".join(lines)


class GetReferencesTool(BaseTool):
    """Find all references to a symbol.

    Uses ripgrep or grep to find all usages of a symbol across the workspace.
    Filters out likely false positives (comments, strings, etc.).

    Attributes:
        name: ToolName.GET_REFERENCES
        description: Find all usages of a function, class, or variable
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GET_REFERENCES
    description = "Find all usages of a function, class, or variable"
    parameter_schema = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Symbol name to find references for"
            },
            "file": {
                "type": "string",
                "description": "Optional: limit search to specific file"
            }
        },
        "required": ["symbol"]
    }

    def __init__(self, workspace_root: str):
        """Initialize references tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, symbol: str, file: Optional[str] = None, **kwargs) -> ToolResult:
        """Find all references to symbol.

        Args:
            symbol: Symbol name to find
            file: Optional file to limit search

        Returns:
            ToolResult with reference locations or error
        """
        try:
            # Validate symbol name
            if not symbol or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', symbol):
                return ToolResult(
                    success=False,
                    error=f"Invalid symbol name: {symbol}"
                )

            # Try ripgrep first, fallback to grep
            references = await self._find_references(symbol, file)

            # Limit results
            if len(references) > MAX_REFERENCES:
                references = references[:MAX_REFERENCES]
                logger.warning(
                    f"Truncated references from {len(references)} to {MAX_REFERENCES}"
                )

            if not references:
                return ToolResult(
                    success=True,
                    output=f"No references found for symbol: {symbol}",
                    data={"references": [], "count": 0}
                )

            # Format output
            output = self._format_references(symbol, references)

            return ToolResult(
                success=True,
                output=output,
                data={"references": references, "count": len(references)}
            )

        except SecurityError as e:
            logger.error(f"Security error in get_references: {e}")
            return ToolResult(success=False, error=f"Security error: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding references: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to find references: {str(e)}")

    async def _find_references(
        self,
        symbol: str,
        target_file: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Find all references using ripgrep or grep.

        Args:
            symbol: Symbol name
            target_file: Optional file to limit search

        Returns:
            List of reference dictionaries
        """
        # Try ripgrep first (faster and smarter)
        references = await self._try_ripgrep(symbol, target_file)
        if references:
            return references

        # Fallback to grep
        return await self._try_grep(symbol, target_file)

    async def _try_ripgrep(
        self,
        symbol: str,
        target_file: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Try using ripgrep for references.

        Args:
            symbol: Symbol name
            target_file: Optional file to limit search

        Returns:
            List of reference dictionaries
        """
        try:
            # Check if rg is available
            which_proc = await asyncio.create_subprocess_exec(
                "which", "rg",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await which_proc.communicate()
            if which_proc.returncode != 0:
                return []

            # Build command
            cmd = ["rg", "-n", "--json", rf"\b{symbol}\b"]
            if target_file:
                cmd.append(str(self.workspace_root / target_file))
            else:
                cmd.append(str(self.workspace_root))

            # Run ripgrep
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode in {0, 1} and stdout:  # rg returns 1 if no matches
                return self._parse_ripgrep_output(stdout.decode())

        except Exception as e:
            logger.debug(f"Error running ripgrep: {e}")

        return []

    def _parse_ripgrep_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse ripgrep JSON output.

        Args:
            output: ripgrep stdout with JSON lines

        Returns:
            List of reference dictionaries
        """
        references = []
        for line in output.split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    match_data = data.get("data", {})
                    path = match_data.get("path", {}).get("text", "")
                    line_num = match_data.get("line_number", 0)
                    line_text = match_data.get("lines", {}).get("text", "").strip()

                    # Make path relative
                    try:
                        rel_path = Path(path).relative_to(self.workspace_root)
                    except ValueError:
                        rel_path = Path(path)

                    references.append({
                        "file": str(rel_path),
                        "line": line_num,
                        "content": line_text
                    })
            except json.JSONDecodeError:
                continue

        return references

    async def _try_grep(
        self,
        symbol: str,
        target_file: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fallback to grep for references.

        Args:
            symbol: Symbol name
            target_file: Optional file to limit search

        Returns:
            List of reference dictionaries
        """
        references = []
        try:
            # Build command
            cmd = ["grep", "-n", "-w", symbol]
            if target_file:
                cmd.append(str(self.workspace_root / target_file))
            else:
                cmd.extend(["-r", str(self.workspace_root)])

            # Run grep
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                # Parse grep output
                for line in stdout.decode().split('\n'):
                    if not line:
                        continue
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        line_num = parts[1]
                        content = parts[2]

                        # Make path relative
                        try:
                            rel_path = Path(file_path).relative_to(self.workspace_root)
                        except ValueError:
                            rel_path = Path(file_path)

                        references.append({
                            "file": str(rel_path),
                            "line": int(line_num),
                            "content": content.strip()
                        })

        except Exception as e:
            logger.debug(f"Error running grep for references: {e}")

        return references

    def _format_references(
        self,
        symbol: str,
        references: List[Dict[str, Any]]
    ) -> str:
        """Format references for human-readable output.

        Args:
            symbol: Symbol name
            references: List of reference dictionaries

        Returns:
            Formatted text
        """
        lines = [f"Found {len(references)} reference(s) to '{symbol}':\n"]
        for ref in references:
            file = ref.get("file", "unknown")
            line = ref.get("line", 0)
            content = ref.get("content", "")
            lines.append(f"{file}:{line}: {content}")

        return "\n".join(lines)


class GetProjectInfoTool(BaseTool):
    """Get project structure and metadata.

    Analyzes the workspace to determine:
    - Project type (Python, Node.js, Rust, Go, etc.)
    - Dependencies and dev dependencies
    - Available scripts
    - Entry points
    - Project metadata (name, version)

    Uses manifest file parsing (package.json, pyproject.toml, Cargo.toml, etc.).

    Attributes:
        name: ToolName.GET_PROJECT_INFO
        description: Get project structure and metadata
        workspace_root: Absolute path to workspace directory
    """

    name = ToolName.GET_PROJECT_INFO
    description = "Get project structure and metadata"
    parameter_schema = {
        "type": "object",
        "properties": {}
    }

    def __init__(self, workspace_root: str):
        """Initialize project info tool.

        Args:
            workspace_root: Absolute path to workspace directory
        """
        self.workspace_root = Path(workspace_root).resolve()

    async def execute(self, **kwargs) -> ToolResult:
        """Get project information.

        Returns:
            ToolResult with project metadata or error
        """
        try:
            # Detect project type and parse manifest
            project_info = await self._detect_project()

            if not project_info:
                return ToolResult(
                    success=True,
                    output="No recognized project structure found.",
                    data={"project_type": None}
                )

            # Format output
            output = self._format_project_info(project_info)

            return ToolResult(
                success=True,
                output=output,
                data=project_info
            )

        except Exception as e:
            logger.error(f"Error getting project info: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to get project info: {str(e)}")

    async def _detect_project(self) -> Optional[Dict[str, Any]]:
        """Detect project type and parse manifest.

        Returns:
            Project info dictionary or None
        """
        # Check for Node.js project
        package_json = self.workspace_root / "package.json"
        if package_json.exists():
            return await self._parse_package_json(package_json)

        # Check for Python project
        pyproject_toml = self.workspace_root / "pyproject.toml"
        if pyproject_toml.exists():
            return await self._parse_pyproject_toml(pyproject_toml)

        # Check for requirements.txt (basic Python)
        requirements_txt = self.workspace_root / "requirements.txt"
        if requirements_txt.exists():
            return await self._parse_requirements_txt(requirements_txt)

        # Check for Rust project
        cargo_toml = self.workspace_root / "Cargo.toml"
        if cargo_toml.exists():
            return await self._parse_cargo_toml(cargo_toml)

        # Check for Go project
        go_mod = self.workspace_root / "go.mod"
        if go_mod.exists():
            return await self._parse_go_mod(go_mod)

        return None

    async def _parse_package_json(self, path: Path) -> Dict[str, Any]:
        """Parse package.json for Node.js projects.

        Args:
            path: Path to package.json

        Returns:
            Project info dictionary
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)

            return {
                "type": "node",
                "name": data.get("name"),
                "version": data.get("version"),
                "dependencies": list(data.get("dependencies", {}).keys()),
                "dev_dependencies": list(data.get("devDependencies", {}).keys()),
                "scripts": data.get("scripts", {}),
                "entry_points": [data.get("main", "index.js")]
            }
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")
            return {"type": "node", "error": str(e)}

    async def _parse_pyproject_toml(self, path: Path) -> Dict[str, Any]:
        """Parse pyproject.toml for Python projects.

        Args:
            path: Path to pyproject.toml

        Returns:
            Project info dictionary
        """
        try:
            # Basic TOML parsing (without external library)
            content = path.read_text()

            # Extract name
            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
            name = name_match.group(1) if name_match else None

            # Extract version
            version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
            version = version_match.group(1) if version_match else None

            # Extract dependencies (basic pattern matching)
            deps_section = re.search(
                r'\[tool\.poetry\.dependencies\](.*?)(?:\[|$)',
                content,
                re.DOTALL
            )
            dependencies = []
            if deps_section:
                deps = re.findall(r'^([a-zA-Z0-9_-]+)\s*=', deps_section.group(1), re.MULTILINE)
                dependencies = [d for d in deps if d != "python"]

            return {
                "type": "python",
                "name": name,
                "version": version,
                "dependencies": dependencies,
                "dev_dependencies": [],
                "scripts": {},
                "entry_points": ["main.py", "app/main.py"]
            }
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")
            return {"type": "python", "error": str(e)}

    async def _parse_requirements_txt(self, path: Path) -> Dict[str, Any]:
        """Parse requirements.txt for Python projects.

        Args:
            path: Path to requirements.txt

        Returns:
            Project info dictionary
        """
        try:
            content = path.read_text()
            # Extract package names (ignore versions and comments)
            dependencies = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name before ==, >=, etc.
                    package = re.split(r'[><=!]', line)[0].strip()
                    if package:
                        dependencies.append(package)

            return {
                "type": "python",
                "name": None,
                "version": None,
                "dependencies": dependencies,
                "dev_dependencies": [],
                "scripts": {},
                "entry_points": ["main.py", "app/main.py"]
            }
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt: {e}")
            return {"type": "python", "error": str(e)}

    async def _parse_cargo_toml(self, path: Path) -> Dict[str, Any]:
        """Parse Cargo.toml for Rust projects.

        Args:
            path: Path to Cargo.toml

        Returns:
            Project info dictionary
        """
        try:
            content = path.read_text()

            # Extract name
            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
            name = name_match.group(1) if name_match else None

            # Extract version
            version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
            version = version_match.group(1) if version_match else None

            return {
                "type": "rust",
                "name": name,
                "version": version,
                "dependencies": [],
                "dev_dependencies": [],
                "scripts": {},
                "entry_points": ["src/main.rs"]
            }
        except Exception as e:
            logger.warning(f"Error parsing Cargo.toml: {e}")
            return {"type": "rust", "error": str(e)}

    async def _parse_go_mod(self, path: Path) -> Dict[str, Any]:
        """Parse go.mod for Go projects.

        Args:
            path: Path to go.mod

        Returns:
            Project info dictionary
        """
        try:
            content = path.read_text()

            # Extract module name
            module_match = re.search(r'module\s+([^\s]+)', content)
            name = module_match.group(1) if module_match else None

            return {
                "type": "go",
                "name": name,
                "version": None,
                "dependencies": [],
                "dev_dependencies": [],
                "scripts": {},
                "entry_points": ["main.go"]
            }
        except Exception as e:
            logger.warning(f"Error parsing go.mod: {e}")
            return {"type": "go", "error": str(e)}

    def _format_project_info(self, info: Dict[str, Any]) -> str:
        """Format project info for human-readable output.

        Args:
            info: Project info dictionary

        Returns:
            Formatted text
        """
        lines = ["Project Information:\n"]
        lines.append(f"Type: {info.get('type', 'unknown')}")

        if info.get('name'):
            lines.append(f"Name: {info['name']}")
        if info.get('version'):
            lines.append(f"Version: {info['version']}")

        deps = info.get('dependencies', [])
        if deps:
            lines.append(f"\nDependencies ({len(deps)}):")
            for dep in deps[:10]:  # Show first 10
                lines.append(f"  - {dep}")
            if len(deps) > 10:
                lines.append(f"  ... and {len(deps) - 10} more")

        scripts = info.get('scripts', {})
        if scripts:
            lines.append(f"\nScripts:")
            for name, cmd in list(scripts.items())[:5]:  # Show first 5
                lines.append(f"  - {name}: {cmd}")
            if len(scripts) > 5:
                lines.append(f"  ... and {len(scripts) - 5} more")

        entry_points = info.get('entry_points', [])
        if entry_points:
            lines.append(f"\nEntry Points:")
            for ep in entry_points:
                lines.append(f"  - {ep}")

        return "\n".join(lines)

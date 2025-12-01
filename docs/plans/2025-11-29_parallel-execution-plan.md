# Code Chat Completion - Parallel Execution Plan

**Date:** 2025-11-29
**Status:** Ready for Execution
**Estimated Total Time:** 4-5 hours (parallel) vs 16-18 hours (sequential)
**Time Savings:** ~70% reduction via parallelization

---

## Executive Summary

This plan orchestrates 4 agents across 3 waves of parallel execution to complete all 6 incomplete Code Chat features. By identifying zero-dependency tasks that can run simultaneously, we reduce total implementation time from ~16 hours to ~4-5 hours.

**Related Documentation:**
- [2025-11-29_code-chat-completion.md](./2025-11-29_code-chat-completion.md) - Original analysis
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history
- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Original spec

---

## Dependency Analysis

```
[Wave 1 - No Dependencies]
├── CreateContextModal (frontend-only, no backend changes)
├── Git MCP Tools (backend-only, no frontend changes yet)
├── LSP MCP Tools (backend-only, no frontend changes yet)
└── run_shell Tool (backend-only, small addition)

[Wave 2 - Depends on Wave 1]
├── DiffPreview Integration (depends on frontend working state)
└── Preset CRUD (depends on backend router stability)

[Wave 3 - Integration]
└── End-to-end testing & documentation
```

---

## Wave 1: Zero-Dependency Parallel Tasks (2-3 hours)

### Task 1A: CreateContextModal (CRITICAL BLOCKER)

**Agent:** `@frontend-engineer`
**Priority:** P0 (Blocking)
**Estimated Time:** 2 hours
**Dependencies:** None (backend already complete)

**Files to Create:**
- `frontend/src/pages/CodeChatPage/CreateContextModal.tsx` (~180 lines)
- `frontend/src/pages/CodeChatPage/CreateContextModal.module.css` (~150 lines)

**Files to Modify:**
- `frontend/src/pages/CodeChatPage/ContextSelector.tsx` (line 100-102: replace alert)
- `frontend/src/pages/CodeChatPage/index.ts` (add export)

---

### Task 1B: Git MCP Tools

**Agent:** `@backend-architect`
**Priority:** P1 (High)
**Estimated Time:** 3 hours
**Dependencies:** None (independent backend work)

**Files to Create:**
- `backend/app/services/code_chat/tools/git.py` (~350 lines)

**Files to Modify:**
- `backend/app/services/code_chat/tools/__init__.py`
- `backend/app/routers/code_chat.py` (tool registration)

---

### Task 1C: LSP MCP Tools

**Agent:** `@devops-engineer` (for language server setup) + `@backend-architect` (for tool implementation)
**Priority:** P2 (Medium)
**Estimated Time:** 3 hours
**Dependencies:** None (independent backend work)

**Files to Create:**
- `backend/app/services/code_chat/tools/lsp.py` (~280 lines)

**Files to Modify:**
- `backend/app/services/code_chat/tools/__init__.py`
- `backend/app/routers/code_chat.py`
- `sandbox/Dockerfile` (add pyright)

---

### Task 1D: run_shell Tool

**Agent:** `@security-specialist` (review) + `@backend-architect` (implementation)
**Priority:** P3 (Low)
**Estimated Time:** 1.5 hours
**Dependencies:** None (builds on existing execution.py)

**Files to Modify:**
- `backend/app/services/code_chat/tools/execution.py` (~100 lines)
- `sandbox/server.py` (add shell endpoint)

---

## Wave 2: Integration Tasks (1-2 hours)

### Task 2A: DiffPreview Integration

**Agent:** `@frontend-engineer`
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours
**Dependencies:** Wave 1 completion (stable frontend state)

**Files to Modify:**
- `frontend/src/pages/CodeChatPage/CodeChatPage.tsx` (import DiffPreview, add state)
- `frontend/src/pages/CodeChatPage/ReActStepViewer.tsx` (show diff for write actions)
- `frontend/src/hooks/useCodeChat.ts` (handle diff_preview events)

---

### Task 2B: Preset CRUD

**Agent:** `@backend-architect` + `@frontend-engineer`
**Priority:** P3 (Low)
**Estimated Time:** 2 hours
**Dependencies:** Wave 1 completion (router stability)

**Files to Create:**
- `backend/app/services/code_chat/presets.py` (~150 lines)
- `frontend/src/pages/CodeChatPage/SavePresetModal.tsx` (~100 lines)
- `frontend/src/pages/CodeChatPage/SavePresetModal.module.css` (~80 lines)

**Files to Modify:**
- `backend/app/routers/code_chat.py` (add CRUD endpoints)
- `frontend/src/pages/CodeChatPage/PresetSelector.tsx` (add save button)
- `frontend/src/hooks/usePresets.ts` (add mutations)

---

## Wave 3: Testing & Documentation (0.5 hours)

### Task 3A: Integration Testing

**Agent:** `@testing-specialist` (if available) or `@backend-architect`
**Priority:** P1
**Estimated Time:** 30 minutes

**Activities:**
- Run full test suite
- Manual E2E testing of new features
- Update SESSION_NOTES.md

---

## Parallel Execution Timeline

```
Time    | Agent 1 (Frontend)     | Agent 2 (Backend)      | Agent 3 (DevOps/Security)
--------|------------------------|------------------------|---------------------------
0:00    | CreateContextModal     | Git MCP Tools          | LSP Docker setup
0:30    | ...                    | ...                    | ...
1:00    | ...                    | ...                    | run_shell security review
1:30    | ...                    | ...                    | ...
2:00    | CreateContextModal     | Git MCP Tools          | LSP tool implementation
2:30    | DiffPreview Integration| LSP Tools (continue)   | ...
3:00    | ...                    | Preset CRUD (backend)  | ...
3:30    | ...                    | ...                    | Integration testing
4:00    | Preset CRUD (frontend) | ...                    | ...
4:30    | Testing & Docs         | Testing & Docs         | Testing & Docs
```

---

## Agent Prompts (Copy/Paste Ready)

### PROMPT 1A: CreateContextModal (@frontend-engineer)

```
## Task: Implement CreateContextModal Component

You are implementing the CreateContextModal component to replace the placeholder alert in ContextSelector.tsx. The backend is FULLY COMPLETE - you only need frontend work.

### Context
- Current placeholder at: frontend/src/pages/CodeChatPage/ContextSelector.tsx line 100-102
- Hook already exists: useCreateContext in frontend/src/hooks/useContexts.ts
- Backend endpoint: POST /api/code-chat/contexts/create (fully implemented)
- Type exists: CreateContextRequest in frontend/src/types/codeChat.ts

### Requirements

**CreateContextModal.tsx** (~180 lines):
1. Modal overlay with terminal aesthetic (match ContextSelector modal)
2. Form fields:
   - Name input (required, alphanumeric + hyphens)
   - Source path input with browse button (reuse WorkspaceSelector as subcomponent)
   - Embedding model dropdown (default: all-MiniLM-L6-v2, options: paraphrase-MiniLM-L6-v2)
3. Submit button with loading state during indexing
4. Cancel button
5. Error display for validation/server errors
6. Progress display (optional - can use simple loading spinner initially)

**CreateContextModal.module.css** (~150 lines):
- Match terminal aesthetic from ContextSelector.module.css
- Form layout with labels and inputs
- Loading spinner
- Error message styling

**ContextSelector.tsx modifications**:
- Add useState for showCreateModal
- Replace alert() with setShowCreateModal(true)
- Render CreateContextModal when showCreateModal is true
- Handle onSuccess to close modal and refresh list

**index.ts**:
- Add CreateContextModal export

### Acceptance Criteria
- [ ] User can click "CREATE NEW INDEX" and see modal
- [ ] User can enter name (validated: alphanumeric + hyphens)
- [ ] User can browse/enter source path
- [ ] User can select embedding model
- [ ] Create button shows loading state during indexing
- [ ] Success closes modal and shows new index in list
- [ ] Errors display clearly in modal

### Files
- CREATE: frontend/src/pages/CodeChatPage/CreateContextModal.tsx
- CREATE: frontend/src/pages/CodeChatPage/CreateContextModal.module.css
- MODIFY: frontend/src/pages/CodeChatPage/ContextSelector.tsx
- MODIFY: frontend/src/pages/CodeChatPage/index.ts

### Reference
- Read useContexts.ts for hook interface
- Read ContextSelector.tsx for modal pattern
- Read codeChat.ts for CreateContextRequest type
```

---

### PROMPT 1B: Git MCP Tools (@backend-architect)

```
## Task: Implement Git MCP Tools for Code Chat

You are implementing Git tools that the ReAct agent can use during code chat sessions. These follow the existing tool pattern in backend/app/services/code_chat/tools/.

### Context
- Tool types defined in: frontend/src/types/codeChat.ts (git_status, git_diff, git_log, git_commit, git_branch)
- Tool base class: backend/app/services/code_chat/tools/base.py
- Existing tools example: backend/app/services/code_chat/tools/file_ops.py
- Router: backend/app/routers/code_chat.py

### Requirements

**git.py** (~350 lines) - Create 5 tool classes:

1. **GitStatusTool**
   - Shows working tree status
   - Returns formatted status with modified/staged/untracked files
   - Parameters: None (operates on workspace)

2. **GitDiffTool**
   - Shows diff for specific file or all changes
   - Parameters: file_path (optional), staged (bool, default False)
   - Returns unified diff format

3. **GitLogTool**
   - Shows commit history
   - Parameters: limit (int, default 10), file_path (optional)
   - Returns formatted log entries

4. **GitCommitTool** (SECURITY CRITICAL)
   - Creates a commit with message
   - Parameters: message (str), files (list of paths, optional - default all staged)
   - MUST return a confirmation request before executing
   - Agent should ASK USER before actually committing

5. **GitBranchTool**
   - List/create/switch branches
   - Parameters: action (list|create|switch), name (optional)

### Security Considerations
- All git operations MUST run within workspace boundary
- git_commit MUST require user confirmation (via tool result asking for confirm)
- Never expose credentials or sensitive git config
- Validate all file paths against workspace root

### Implementation Pattern
```python
from .base import BaseTool, ToolResult
import subprocess
from pathlib import Path

class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Show the working tree status..."

    async def execute(self, **params) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Format and return
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### Registration
- Add to backend/app/services/code_chat/tools/__init__.py
- Import in backend/app/routers/code_chat.py
- Register with tool registry

### Acceptance Criteria
- [ ] git_status returns current repo state
- [ ] git_diff shows file changes
- [ ] git_log shows commit history
- [ ] git_commit returns confirmation request (doesn't auto-commit)
- [ ] git_branch lists/creates/switches branches
- [ ] All operations validate workspace boundary
- [ ] Proper error handling for non-git directories

### Files
- CREATE: backend/app/services/code_chat/tools/git.py
- MODIFY: backend/app/services/code_chat/tools/__init__.py
- MODIFY: backend/app/routers/code_chat.py
```

---

### PROMPT 1C: LSP MCP Tools (@devops-engineer + @backend-architect)

```
## Task: Implement LSP MCP Tools for Code Chat

You are implementing Language Server Protocol tools that provide code diagnostics, definitions, and references to the ReAct agent.

### Context
- Tool types defined in: frontend/src/types/codeChat.ts (get_diagnostics, get_definitions, get_references, get_project_info)
- Sandbox container: sandbox/Dockerfile
- Tool base: backend/app/services/code_chat/tools/base.py

### Requirements

**Part 1: Docker Setup (@devops-engineer)**
- Add pyright to sandbox/Dockerfile (for Python diagnostics)
- Optionally: typescript-language-server for JS/TS

**Part 2: lsp.py (~280 lines) - Create 4 tool classes (@backend-architect)**

1. **GetDiagnosticsTool**
   - Runs pyright/eslint on file and returns diagnostics
   - Parameters: file_path (str)
   - Returns: List of {line, column, severity, message}

2. **GetDefinitionsTool**
   - Finds definition location for symbol at position
   - Parameters: file_path (str), line (int), column (int)
   - Returns: {file, line, column} or null

3. **GetReferencesTool**
   - Finds all references to symbol
   - Parameters: file_path (str), line (int), column (int)
   - Returns: List of {file, line, column}

4. **GetProjectInfoTool**
   - Analyzes project structure
   - Parameters: None
   - Returns: {language, framework, package_manager, entry_points}

### Implementation Notes
- Use subprocess to call pyright with JSON output
- Parse pyright JSON output for diagnostics
- Gracefully handle missing language servers (return helpful error)
- Cache project analysis results

### Acceptance Criteria
- [ ] get_diagnostics returns type errors for Python files
- [ ] get_definitions finds symbol definitions
- [ ] get_references finds all usages
- [ ] get_project_info detects language/framework
- [ ] Graceful degradation if pyright unavailable

### Files
- MODIFY: sandbox/Dockerfile (add pyright)
- CREATE: backend/app/services/code_chat/tools/lsp.py
- MODIFY: backend/app/services/code_chat/tools/__init__.py
- MODIFY: backend/app/routers/code_chat.py
```

---

### PROMPT 1D: run_shell Tool (@security-specialist + @backend-architect)

```
## Task: Implement run_shell Tool for Code Chat

You are implementing a sandboxed shell execution tool for the ReAct agent. Security is CRITICAL.

### Context
- Existing RunPythonTool in: backend/app/services/code_chat/tools/execution.py
- Sandbox server: sandbox/server.py
- Tool type defined in: frontend/src/types/codeChat.ts (run_shell)

### Requirements

**Security Review (@security-specialist)**
1. Define allowed command whitelist:
   - Safe: ls, cat, head, tail, find, grep, wc, sort, uniq, awk, sed (read-only)
   - Blocked: rm, mv, cp, chmod, chown, wget, curl, ssh, nc, python, bash -c
2. Argument validation to prevent injection
3. Working directory restriction to workspace

**Implementation (@backend-architect)**

**execution.py additions** (~100 lines):
```python
class RunShellTool(BaseTool):
    name = "run_shell"
    description = "Run whitelisted shell commands in sandbox"

    ALLOWED_COMMANDS = {"ls", "cat", "head", "tail", "find", "grep", "wc", ...}

    async def execute(self, command: str) -> ToolResult:
        # Parse command, validate against whitelist
        # Call sandbox /shell endpoint
        # Return output
```

**sandbox/server.py additions**:
- Add POST /shell endpoint
- Command validation
- Timeout and resource limits
- Working directory restriction

### Security Requirements
- MUST validate command against whitelist BEFORE execution
- MUST sanitize arguments (no ;, |, &&, ||, $, `, etc. unless part of valid arg)
- MUST restrict to workspace directory
- MUST have timeout (30 seconds)
- MUST log all commands for audit

### Acceptance Criteria
- [ ] Whitelisted commands execute successfully
- [ ] Blocked commands return clear error
- [ ] Shell injection attempts blocked
- [ ] Commands run only in workspace
- [ ] Timeout works correctly
- [ ] Commands logged for audit

### Files
- MODIFY: backend/app/services/code_chat/tools/execution.py
- MODIFY: sandbox/server.py
- MODIFY: backend/app/services/code_chat/tools/__init__.py
```

---

### PROMPT 2A: DiffPreview Integration (@frontend-engineer)

```
## Task: Integrate DiffPreview into Code Chat Flow

You are integrating the existing DiffPreview component into the Code Chat page. The component exists but is not wired up.

### Context
- DiffPreview component: frontend/src/pages/CodeChatPage/DiffPreview.tsx (COMPLETE)
- CodeChatPage: frontend/src/pages/CodeChatPage/CodeChatPage.tsx
- useCodeChat hook: frontend/src/hooks/useCodeChat.ts
- SSE events include diff_preview type (see codeChat.ts line 315)

### Requirements

**useCodeChat.ts modifications**:
1. Add state for current diff preview: `diffPreview: DiffPreviewData | null`
2. Handle `diff_preview` SSE event type
3. Add callbacks: `approveDiff()`, `rejectDiff()`

**CodeChatPage.tsx modifications**:
1. Import DiffPreview component
2. Add conditional rendering when diffPreview state exists
3. Show DiffPreview in panel with approve/reject buttons
4. Wire up approve/reject to send decision back

**ReActStepViewer.tsx modifications**:
1. For write_file actions, show a diff icon/indicator
2. Clicking shows inline diff (reuse DiffPreview or show summary)

### Acceptance Criteria
- [ ] write_file actions trigger diff preview
- [ ] User sees additions (green) and deletions (red)
- [ ] CREATE/MODIFY badges display correctly
- [ ] User can approve or reject changes
- [ ] Rejected changes stop the action

### Files
- MODIFY: frontend/src/hooks/useCodeChat.ts
- MODIFY: frontend/src/pages/CodeChatPage/CodeChatPage.tsx
- MODIFY: frontend/src/pages/CodeChatPage/ReActStepViewer.tsx
```

---

### PROMPT 2B: Preset CRUD (@backend-architect + @frontend-engineer)

```
## Task: Implement Custom Preset CRUD

You are adding the ability to create, update, and delete custom presets.

### Context
- Current presets: Read-only, defined in backend/app/models/code_chat.py
- PresetSelector: frontend/src/pages/CodeChatPage/PresetSelector.tsx
- usePresets hook: frontend/src/hooks/usePresets.ts

### Requirements

**Backend: presets.py (~150 lines)**
1. File-based persistence: data/custom_presets.json
2. Functions:
   - load_custom_presets() -> List[ModelPreset]
   - save_preset(preset: ModelPreset) -> ModelPreset
   - update_preset(name: str, preset: ModelPreset) -> ModelPreset
   - delete_preset(name: str) -> bool

**Backend: code_chat.py additions**
- POST /api/code-chat/presets - Create new preset
- PUT /api/code-chat/presets/{name} - Update preset
- DELETE /api/code-chat/presets/{name} - Delete preset

**Frontend: SavePresetModal.tsx (~100 lines)**
- Modal with name input and current settings display
- Save button with loading state
- Error handling

**Frontend: usePresets.ts additions**
- useCreatePreset() mutation
- useUpdatePreset() mutation
- useDeletePreset() mutation

**Frontend: PresetSelector.tsx modifications**
- Add "Save Current" button
- Add edit/delete buttons for custom presets

### Acceptance Criteria
- [ ] User can save current settings as preset
- [ ] User can update custom presets
- [ ] User can delete custom presets
- [ ] Built-in presets remain read-only
- [ ] Presets persist across sessions

### Files
- CREATE: backend/app/services/code_chat/presets.py
- CREATE: frontend/src/pages/CodeChatPage/SavePresetModal.tsx
- CREATE: frontend/src/pages/CodeChatPage/SavePresetModal.module.css
- MODIFY: backend/app/routers/code_chat.py
- MODIFY: frontend/src/pages/CodeChatPage/PresetSelector.tsx
- MODIFY: frontend/src/hooks/usePresets.ts
```

---

## Execution Commands

### Start Wave 1 (All Parallel)

```bash
# Terminal 1 - Frontend Engineer on CreateContextModal
claude --agent frontend-engineer "$(cat docs/plans/prompts/1a-create-context-modal.md)"

# Terminal 2 - Backend Architect on Git Tools
claude --agent backend-architect "$(cat docs/plans/prompts/1b-git-tools.md)"

# Terminal 3 - Backend Architect on LSP Tools (or DevOps for Docker part)
claude --agent backend-architect "$(cat docs/plans/prompts/1c-lsp-tools.md)"

# Terminal 4 - Security Specialist + Backend on run_shell
claude --agent security-specialist "$(cat docs/plans/prompts/1d-run-shell.md)"
```

### Start Wave 2 (After Wave 1)

```bash
# Terminal 1 - Frontend Engineer on DiffPreview
claude --agent frontend-engineer "$(cat docs/plans/prompts/2a-diff-preview.md)"

# Terminal 2 - Backend + Frontend on Preset CRUD
claude --agent backend-architect "$(cat docs/plans/prompts/2b-preset-crud.md)"
```

### Wave 3: Testing

```bash
# Run tests after all implementations
docker-compose build --no-cache synapse_core synapse_frontend
docker-compose up -d
docker-compose logs -f synapse_core synapse_frontend

# Backend tests
docker-compose exec synapse_core pytest tests/test_code_chat*.py -v

# Frontend tests
docker-compose exec synapse_frontend npm run test
```

---

## Time Comparison

| Approach | Wave 1 | Wave 2 | Wave 3 | Total |
|----------|--------|--------|--------|-------|
| Sequential | 9.5h | 3.5h | 0.5h | **13.5h** |
| Parallel | 3h | 2h | 0.5h | **5.5h** |
| **Savings** | 6.5h | 1.5h | 0h | **8h (59%)** |

---

## Risk Mitigation

### Risk 1: Merge Conflicts
- **Mitigation:** Wave 1 tasks touch different files, no conflicts expected
- **If occurs:** Wave 1 tasks can be rebased independently

### Risk 2: Agent Context Limits
- **Mitigation:** Each prompt is self-contained with specific file paths
- **If occurs:** Split tasks into smaller chunks

### Risk 3: Backend Dependencies
- **Mitigation:** Git/LSP tools are independent of each other
- **If occurs:** Complete one before starting another

---

## Definition of Done

- [ ] CreateContextModal working end-to-end
- [ ] Git tools (at minimum: status, diff) working
- [ ] LSP diagnostics working for Python
- [ ] run_shell with security review
- [ ] DiffPreview integrated into Code Chat
- [ ] At least read-only presets preserved
- [ ] All tests passing
- [ ] SESSION_NOTES.md updated

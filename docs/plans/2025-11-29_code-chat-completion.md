# S.Y.N.A.P.S.E. ENGINE - Code Chat Mode Completion Plan

**Date:** 2025-11-29
**Status:** Ready for Implementation
**Estimated Time:** 16-24 hours (4-6 development sessions)
**Priority:** HIGH - Blocking user workflow

---

## Executive Summary

The Code Chat mode has been substantially implemented across 5 sessions (~12,945 lines of code), but user testing has revealed several incomplete features that block the full workflow. The primary blocker is the "CREATE NEW INDEX" functionality which shows a placeholder alert instead of creating CGRAG indexes. This plan identifies ALL incomplete features and provides a prioritized implementation roadmap.

**Related Documentation:**
- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Original implementation plan
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history
- [CLAUDE.md](../../CLAUDE.md) - Project instructions

---

## Current Implementation Status

### COMPLETED Components (Sessions 1-5)

| Component | Status | Files | Lines |
|-----------|--------|-------|-------|
| Pydantic Models & Schemas | COMPLETE | 4 | 2,114 |
| Tool Infrastructure (base, file_ops) | COMPLETE | 3 | ~1,200 |
| Search Tools (CGRAG, SearXNG, grep) | COMPLETE | 1 | 640 |
| Memory Manager | COMPLETE | 1 | 497 |
| ReAct Agent Core | COMPLETE | 1 | 732 |
| API Router (9 endpoints) | COMPLETE | 1 | 574 |
| Frontend Hooks (4 hooks) | COMPLETE | 4 | 648 |
| Frontend UI Components | COMPLETE | 6 | ~3,500 |
| Python Sandbox Container | COMPLETE | 3 | ~565 |
| Test Suites | COMPLETE | 4 | ~2,000 |

### INCOMPLETE Features Identified

| Feature | Priority | Blocker? | Estimated Hours |
|---------|----------|----------|-----------------|
| **1. CreateContextModal Component** | CRITICAL | YES | 3-4 |
| **2. DiffPreview Integration** | HIGH | NO | 2-3 |
| **3. Git MCP Tools** | MEDIUM | NO | 4-6 |
| **4. LSP MCP Tools** | MEDIUM | NO | 4-6 |
| **5. run_shell Tool** | LOW | NO | 2-3 |
| **6. Custom Preset CRUD** | LOW | NO | 2-3 |

---

## Incomplete Feature Analysis

### 1. CreateContextModal Component (CRITICAL BLOCKER)

**Current State:**
- [ContextSelector.tsx](../../frontend/src/pages/CodeChatPage/ContextSelector.tsx) has a placeholder:
  ```typescript
  const handleCreateNew = useCallback(() => {
    alert('Create new index feature coming soon!');  // Line 100-102
  }, []);
  ```
- Backend endpoint `/api/code-chat/contexts/create` is FULLY IMPLEMENTED in [code_chat.py](../../backend/app/routers/code_chat.py)
- Frontend hook `useCreateContext` is FULLY IMPLEMENTED in [useContexts.ts](../../frontend/src/hooks/useContexts.ts)
- CGRAG indexing logic is COMPLETE in [context.py](../../backend/app/services/code_chat/context.py)

**What's Missing:**
- `CreateContextModal.tsx` - Modal component for collecting:
  - Context name (text input)
  - Source path (workspace browser or text input)
  - Embedding model selection (dropdown, default: all-MiniLM-L6-v2)
- Integration with `useCreateContext` mutation hook
- Progress indicator during indexing (uses EventBus for cgrag_index_progress events)
- Error handling and validation

**Files to Create:**
- `frontend/src/pages/CodeChatPage/CreateContextModal.tsx` (~150-200 lines)
- `frontend/src/pages/CodeChatPage/CreateContextModal.module.css` (~100-150 lines)

**Files to Modify:**
- `frontend/src/pages/CodeChatPage/ContextSelector.tsx` (replace alert with modal)
- `frontend/src/pages/CodeChatPage/index.ts` (add export)

---

### 2. DiffPreview Integration (HIGH)

**Current State:**
- [DiffPreview.tsx](../../frontend/src/pages/CodeChatPage/DiffPreview.tsx) component is FULLY IMPLEMENTED
- [DiffPreview.module.css](../../frontend/src/pages/CodeChatPage/DiffPreview.module.css) styles are complete
- Component exports are configured in [index.ts](../../frontend/src/pages/CodeChatPage/index.ts)
- Backend emits `diff_preview` events (see [codeChat.ts](../../frontend/src/types/codeChat.ts) line 315)

**What's Missing:**
- DiffPreview is NOT INTEGRATED into CodeChatPage
- ReActStepViewer doesn't show diffs for write_file actions
- No confirmation flow before file writes

**Files to Modify:**
- `frontend/src/pages/CodeChatPage/CodeChatPage.tsx` (add DiffPreview import and state)
- `frontend/src/pages/CodeChatPage/ReActStepViewer.tsx` (show diff for write actions)
- `frontend/src/hooks/useCodeChat.ts` (handle diff_preview events)

---

### 3. Git MCP Tools (MEDIUM)

**Current State:**
- Types defined in [codeChat.ts](../../frontend/src/types/codeChat.ts): `git_status`, `git_diff`, `git_log`, `git_commit`, `git_branch`
- No backend implementation exists
- Planned in [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) section "MCP Tool Implementations"

**What's Missing:**
- `backend/app/services/code_chat/tools/git.py` - Tool implementations
- Registration in [code_chat.py](../../backend/app/routers/code_chat.py) router
- git_commit requires confirmation flow (UI + backend coordination)

**Files to Create:**
- `backend/app/services/code_chat/tools/git.py` (~300-400 lines)

**Files to Modify:**
- `backend/app/services/code_chat/tools/__init__.py` (add exports)
- `backend/app/routers/code_chat.py` (register tools)

---

### 4. LSP MCP Tools (MEDIUM)

**Current State:**
- Types defined: `get_diagnostics`, `get_definitions`, `get_references`, `get_project_info`
- No backend implementation exists
- Planned in [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) section "LSP Tools"

**What's Missing:**
- `backend/app/services/code_chat/tools/lsp.py` - Tool implementations
- Integration with pyright for Python diagnostics
- Integration with typescript-language-server for JS/TS diagnostics

**Files to Create:**
- `backend/app/services/code_chat/tools/lsp.py` (~250-300 lines)

**Files to Modify:**
- `backend/app/services/code_chat/tools/__init__.py`
- `backend/app/routers/code_chat.py`

---

### 5. run_shell Tool (LOW)

**Current State:**
- Type defined: `run_shell`
- [execution.py](../../backend/app/services/code_chat/tools/execution.py) has `RunPythonTool` but not `RunShellTool`

**What's Missing:**
- `RunShellTool` class in execution.py
- Sandboxed shell execution in sandbox container
- Restricted command whitelist (ls, cat, grep, find, etc.)

**Files to Modify:**
- `backend/app/services/code_chat/tools/execution.py` (~100 lines)
- `sandbox/server.py` (add shell endpoint)

---

### 6. Custom Preset CRUD (LOW)

**Current State:**
- Built-in presets work: speed, balanced, quality, coding, research
- Frontend can select presets via [PresetSelector.tsx](../../frontend/src/pages/CodeChatPage/PresetSelector.tsx)
- Backend has `GET /presets` and `GET /presets/{name}` endpoints

**What's Missing:**
- `POST /presets` endpoint for creating custom presets
- `PUT /presets/{name}` endpoint for updating presets
- `DELETE /presets/{name}` endpoint for deleting presets
- Persistence layer (file-based or SQLite)
- Frontend "Save as Preset" modal

**Files to Create:**
- `backend/app/services/code_chat/presets.py` (~150 lines) - Persistence
- `frontend/src/pages/CodeChatPage/SavePresetModal.tsx` (~100 lines)

**Files to Modify:**
- `backend/app/routers/code_chat.py` (add CRUD endpoints)
- `frontend/src/pages/CodeChatPage/PresetSelector.tsx` (add save button)

---

## Implementation Plan

### Phase 1: Critical Blocker Fix (3-4 hours)

**Objective:** Enable users to create CGRAG indexes through the UI

**Tasks:**
1. Create `CreateContextModal.tsx` component
   - Name input with validation
   - Source path selector (reuse WorkspaceSelector or text input)
   - Embedding model dropdown (all-MiniLM-L6-v2, paraphrase-MiniLM-L6-v2)
   - Create button with loading state
   - Error display

2. Create `CreateContextModal.module.css` styles
   - Match terminal aesthetic from other modals
   - Form layout with labels
   - Loading spinner during indexing

3. Update `ContextSelector.tsx`
   - Add `showCreateModal` state
   - Replace alert with modal display
   - Handle successful creation (close modal, refresh list)

4. Update `index.ts` exports

**Acceptance Criteria:**
- [ ] User can click "CREATE NEW INDEX" and see modal
- [ ] User can enter name and select source path
- [ ] User can trigger indexing and see progress
- [ ] Successfully created index appears in list
- [ ] Errors are displayed clearly

---

### Phase 2: DiffPreview Integration (2-3 hours)

**Objective:** Show file diffs before write operations

**Tasks:**
1. Update `useCodeChat.ts`
   - Add `diffPreview` state
   - Handle `diff_preview` SSE events
   - Add `approveDiff` and `rejectDiff` callbacks

2. Update `CodeChatPage.tsx`
   - Import and render DiffPreview component
   - Show during write_file actions
   - Add approve/reject buttons

3. Update `ReActStepViewer.tsx`
   - Show diff icon for write_file actions
   - Inline diff preview option

**Acceptance Criteria:**
- [ ] write_file actions show diff preview
- [ ] User can see additions (green) and deletions (red)
- [ ] CREATE/MODIFY badges display correctly

---

### Phase 3: Git MCP Tools (4-6 hours)

**Objective:** Enable Git operations from Code Chat

**Tasks:**
1. Create `git.py` tool implementations
   - GitStatusTool
   - GitDiffTool
   - GitLogTool
   - GitCommitTool (with confirmation)
   - GitBranchTool

2. Register tools in router

3. Update sandbox for git operations

**Acceptance Criteria:**
- [ ] Agent can check git status
- [ ] Agent can show diffs
- [ ] Agent can view commit history
- [ ] Git commits require user confirmation

---

### Phase 4: LSP Tools (4-6 hours)

**Objective:** Enable code diagnostics from Code Chat

**Tasks:**
1. Create `lsp.py` tool implementations
   - GetDiagnosticsTool (pyright, eslint)
   - GetDefinitionsTool
   - GetReferencesTool
   - GetProjectInfoTool

2. Install language servers in Docker
   - pyright for Python
   - typescript-language-server for JS/TS

**Acceptance Criteria:**
- [ ] Agent can get type errors for Python files
- [ ] Agent can get lint errors for JS/TS files
- [ ] Results are formatted for agent consumption

---

### Phase 5: Polish & Minor Features (2-4 hours)

**Objective:** Complete remaining low-priority features

**Tasks:**
1. Implement `RunShellTool`
2. Add custom preset CRUD
3. Integration testing

---

## Agent Assignments

### Phase 1: CreateContextModal
**Lead:** `@frontend-engineer`
**Support:** `@terminal-ui-specialist`
**Rationale:** Pure frontend task requiring terminal UI expertise

### Phase 2: DiffPreview Integration
**Lead:** `@frontend-engineer`
**Support:** `@websocket-realtime-specialist`
**Rationale:** Frontend integration with SSE event handling

### Phase 3: Git MCP Tools
**Lead:** `@backend-architect`
**Support:** `@security-specialist`
**Rationale:** Backend tool implementation with security considerations for git commands

### Phase 4: LSP Tools
**Lead:** `@backend-architect`
**Support:** `@devops-engineer`
**Rationale:** Backend tools requiring Docker configuration for language servers

### Phase 5: Polish
**Lead:** `@backend-architect`
**Support:** `@testing-specialist`
**Rationale:** Mixed backend work with integration testing

---

## Risks & Mitigation

### Risk 1: CGRAG Indexing Performance
**Description:** Large directories may take too long to index
**Mitigation:**
- Add progress events via EventBus
- Consider background job queue for large indexes
- Set reasonable limits (MAX_FILE_SIZE, exclude patterns)

### Risk 2: Git Command Security
**Description:** Arbitrary git commands could be dangerous
**Mitigation:**
- Whitelist specific git commands
- Require confirmation for commits/pushes
- Never expose raw git output containing credentials

### Risk 3: Language Server Dependencies
**Description:** LSP tools require language servers installed
**Mitigation:**
- Document optional dependencies
- Graceful degradation if servers unavailable
- Pre-install common servers in Docker image

---

## Definition of Done

- [ ] All critical blockers resolved (CreateContextModal works)
- [ ] DiffPreview integrated into code chat flow
- [ ] At least basic Git tools working (status, diff)
- [ ] All changes documented in SESSION_NOTES.md
- [ ] Docker image builds successfully
- [ ] Integration tests pass

---

## Next Actions

### Immediate (Today)
1. Implement CreateContextModal component (Phase 1)
2. Test with actual CGRAG indexing

### Follow-up
3. Integrate DiffPreview (Phase 2)
4. Implement Git tools (Phase 3)
5. Add LSP tools if time permits (Phase 4)

---

## Reference Documentation

### Consulted Agent Files
- [@record-keeper](../../.claude/agents/record-keeper.md) - Historical context
- [@frontend-engineer](../../.claude/agents/frontend-engineer.md) - Frontend patterns
- [@backend-architect](../../.claude/agents/backend-architect.md) - API design
- [@cgrag-specialist](../../.claude/agents/cgrag-specialist.md) - CGRAG integration

### Source Files Referenced
- [ContextSelector.tsx](../../frontend/src/pages/CodeChatPage/ContextSelector.tsx) - Contains placeholder
- [useContexts.ts](../../frontend/src/hooks/useContexts.ts) - Create mutation hook
- [context.py](../../backend/app/services/code_chat/context.py) - CGRAG indexing
- [code_chat.py](../../backend/app/routers/code_chat.py) - API router
- [codeChat.ts](../../frontend/src/types/codeChat.ts) - TypeScript types

### Implementation Plan
- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Original spec
- [SESSION4_PLAN.md](./SESSION4_PLAN.md) - Session 4 details

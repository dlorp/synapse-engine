# Task: Integrate DiffPreview into Code Chat Flow

You are integrating the existing DiffPreview component into the Code Chat page. The component exists but is not wired up to the data flow.

## Context

- DiffPreview component: `frontend/src/pages/CodeChatPage/DiffPreview.tsx` (COMPLETE)
- DiffPreview styles: `frontend/src/pages/CodeChatPage/DiffPreview.module.css` (COMPLETE)
- CodeChatPage: `frontend/src/pages/CodeChatPage/CodeChatPage.tsx`
- useCodeChat hook: `frontend/src/hooks/useCodeChat.ts`
- SSE events include `diff_preview` type (see `frontend/src/types/codeChat.ts`)
- Read SESSION_NOTES.md for recent context

## Requirements

### useCodeChat.ts modifications

Add state and handlers for diff preview:

```typescript
// Add to CodeChatState interface
interface CodeChatState {
  // ... existing state ...
  diffPreview: DiffPreviewData | null;
}

interface DiffPreviewData {
  filePath: string;
  originalContent: string | null;
  newContent: string;
  changeType: 'create' | 'modify' | 'delete';
  actionId: string; // ID to reference when approving/rejecting
}

// In the SSE event handler, add case for diff_preview
case 'diff_preview':
  const diffData = JSON.parse(event.data);
  setState(prev => ({
    ...prev,
    diffPreview: {
      filePath: diffData.file_path,
      originalContent: diffData.original_content,
      newContent: diffData.new_content,
      changeType: diffData.change_type,
      actionId: diffData.action_id,
    }
  }));
  break;

// Add callbacks for approve/reject
const approveDiff = useCallback(async () => {
  if (!state.diffPreview) return;
  // Send approval to backend
  await fetch(`/api/code-chat/sessions/${sessionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action_id: state.diffPreview.actionId })
  });
  setState(prev => ({ ...prev, diffPreview: null }));
}, [state.diffPreview, sessionId]);

const rejectDiff = useCallback(() => {
  if (!state.diffPreview) return;
  // Send rejection to backend
  fetch(`/api/code-chat/sessions/${sessionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action_id: state.diffPreview.actionId })
  });
  setState(prev => ({ ...prev, diffPreview: null }));
}, [state.diffPreview, sessionId]);

// Return from hook
return {
  // ... existing returns ...
  diffPreview: state.diffPreview,
  approveDiff,
  rejectDiff,
};
```

### CodeChatPage.tsx modifications

```typescript
import { DiffPreview } from './DiffPreview';

// In component:
const {
  // ... existing destructuring ...
  diffPreview,
  approveDiff,
  rejectDiff,
} = useCodeChat();

// In render, add after steps section:
{diffPreview && (
  <div className={styles.diffPreviewContainer}>
    <DiffPreview
      filePath={diffPreview.filePath}
      originalContent={diffPreview.originalContent}
      newContent={diffPreview.newContent}
      changeType={diffPreview.changeType}
      onClose={rejectDiff}
    />
    <div className={styles.diffActions}>
      <Button
        variant="primary"
        onClick={approveDiff}
      >
        APPROVE CHANGES
      </Button>
      <Button
        variant="secondary"
        onClick={rejectDiff}
      >
        REJECT
      </Button>
    </div>
  </div>
)}
```

Add to CSS:
```css
.diffPreviewContainer {
  margin: 1rem 0;
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  overflow: hidden;
}

.diffActions {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-primary);
}
```

### ReActStepViewer.tsx modifications

Show diff indicator for write_file actions:

```typescript
// For ACTION steps with tool === 'write_file', add indicator
{step.type === 'action' && step.tool === 'write_file' && (
  <span className={styles.diffIndicator} title="File changes pending">
    [DIFF]
  </span>
)}
```

Add styling:
```css
.diffIndicator {
  color: var(--cyan);
  font-size: var(--text-xs);
  margin-left: 0.5rem;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Note on Backend

The backend should emit `diff_preview` events when `write_file` is called. If this isn't implemented yet, you can:
1. Add a TODO comment noting the backend needs to emit these events
2. For now, test with mock data

Backend would need to add in the agent's write_file handling:
```python
# Before actually writing, emit diff preview
await emit_event(CodeChatStreamEvent(
    event_type="diff_preview",
    data={
        "file_path": file_path,
        "original_content": original_content,  # Read from file or None if new
        "new_content": new_content,
        "change_type": "modify" if original_content else "create",
        "action_id": str(uuid4()),
    }
))
# Then wait for approval before writing
```

## Acceptance Criteria

- [ ] useCodeChat has diffPreview state
- [ ] diff_preview SSE events are handled
- [ ] DiffPreview component renders when diff is pending
- [ ] User sees additions (green) and deletions (red)
- [ ] CREATE/MODIFY badges display correctly
- [ ] Approve button commits the change
- [ ] Reject button cancels the change
- [ ] ReActStepViewer shows [DIFF] indicator for write_file actions

## Files

- **MODIFY:** `frontend/src/hooks/useCodeChat.ts`
- **MODIFY:** `frontend/src/pages/CodeChatPage/CodeChatPage.tsx`
- **MODIFY:** `frontend/src/pages/CodeChatPage/CodeChatPage.module.css`
- **MODIFY:** `frontend/src/pages/CodeChatPage/ReActStepViewer.tsx`
- **MODIFY:** `frontend/src/pages/CodeChatPage/ReActStepViewer.module.css`

## Testing

1. Start a code chat session
2. Ask agent to create/modify a file
3. Verify diff preview appears
4. Verify approve/reject buttons work
5. Verify file changes only happen after approval

# Task: Implement CreateContextModal Component

You are implementing the CreateContextModal component to replace the placeholder alert in ContextSelector.tsx. The backend is FULLY COMPLETE - you only need frontend work.

## Context

- Current placeholder at: `frontend/src/pages/CodeChatPage/ContextSelector.tsx` line 100-102
- Hook already exists: `useCreateContext` in `frontend/src/hooks/useContexts.ts`
- Backend endpoint: `POST /api/code-chat/contexts/create` (fully implemented)
- Type exists: `CreateContextRequest` in `frontend/src/types/codeChat.ts`
- Read SESSION_NOTES.md for recent context (newest sessions first)

## Requirements

### CreateContextModal.tsx (~180 lines)

1. Modal overlay with terminal aesthetic (match ContextSelector modal pattern)
2. Form fields:
   - **Name input** (required, alphanumeric + hyphens only)
   - **Source path input** with browse button (show WorkspaceSelector as nested modal)
   - **Embedding model dropdown** (default: all-MiniLM-L6-v2, option: paraphrase-MiniLM-L6-v2)
3. Submit button with loading state during indexing
4. Cancel button
5. Error display for validation/server errors
6. ESC key closes modal
7. Click outside closes modal

### CreateContextModal.module.css (~150 lines)

- Match terminal aesthetic from ContextSelector.module.css
- Form layout with labels and inputs
- Loading spinner (reuse existing pattern)
- Error message styling (red text)
- Input focus states with cyan border

### ContextSelector.tsx modifications

```typescript
// Add state
const [showCreateModal, setShowCreateModal] = useState(false);

// Replace handleCreateNew (line 100-102)
const handleCreateNew = useCallback(() => {
  setShowCreateModal(true);
}, []);

// Add to render (after the modal div)
{showCreateModal && (
  <CreateContextModal
    onClose={() => setShowCreateModal(false)}
    onSuccess={() => {
      setShowCreateModal(false);
      // Context list will auto-refresh via query invalidation
    }}
  />
)}
```

### index.ts

Add export: `export { CreateContextModal } from './CreateContextModal';`

## Acceptance Criteria

- [ ] User can click "CREATE NEW INDEX" and see modal
- [ ] User can enter name (validated: alphanumeric + hyphens only)
- [ ] User can browse/enter source path using WorkspaceSelector
- [ ] User can select embedding model from dropdown
- [ ] Create button shows loading state during indexing
- [ ] Success closes modal and shows new index in context list
- [ ] Errors display clearly in modal
- [ ] ESC key and click-outside close the modal

## Files

- **CREATE:** `frontend/src/pages/CodeChatPage/CreateContextModal.tsx`
- **CREATE:** `frontend/src/pages/CodeChatPage/CreateContextModal.module.css`
- **MODIFY:** `frontend/src/pages/CodeChatPage/ContextSelector.tsx` (lines 100-102, add state, add modal render)
- **MODIFY:** `frontend/src/pages/CodeChatPage/index.ts` (add export)

## Reference Files

Read these for patterns:
- `frontend/src/pages/CodeChatPage/ContextSelector.tsx` - Modal pattern
- `frontend/src/pages/CodeChatPage/WorkspaceSelector.tsx` - File browser pattern
- `frontend/src/hooks/useContexts.ts` - useCreateContext hook interface
- `frontend/src/types/codeChat.ts` - CreateContextRequest type

## Type Reference

```typescript
interface CreateContextRequest {
  name: string;
  sourcePath: string;
  embeddingModel?: string; // default: 'all-MiniLM-L6-v2'
}

interface CreateContextModalProps {
  onClose: () => void;
  onSuccess: () => void;
}
```

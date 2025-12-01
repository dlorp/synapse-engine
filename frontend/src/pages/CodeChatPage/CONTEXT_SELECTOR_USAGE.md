# ContextSelector Component - Usage Guide

## Overview

The `ContextSelector` component provides a terminal-styled modal for selecting CGRAG indexes in Code Chat mode. It features ASCII-style radio buttons, context metadata display, and actions for refreshing or creating indexes.

## Import

```typescript
import { ContextSelector } from './ContextSelector';
```

## Basic Usage

```typescript
import React, { useState } from 'react';
import { ContextSelector } from './ContextSelector';

export const CodeChatPage: React.FC = () => {
  const [showContextSelector, setShowContextSelector] = useState(false);
  const [selectedContext, setSelectedContext] = useState<string | null>(null);

  const handleContextSelect = (contextName: string | null) => {
    setSelectedContext(contextName);
    console.log('Selected context:', contextName);
  };

  return (
    <div>
      {/* Button to open modal */}
      <Button onClick={() => setShowContextSelector(true)}>
        SELECT CONTEXT
      </Button>

      {/* Display current context */}
      <div>
        Current context: {selectedContext || 'None'}
      </div>

      {/* Context Selector Modal */}
      {showContextSelector && (
        <ContextSelector
          selectedContext={selectedContext}
          onSelect={handleContextSelect}
          onClose={() => setShowContextSelector(false)}
        />
      )}
    </div>
  );
};
```

## Props

```typescript
interface ContextSelectorProps {
  /** Currently selected context name (null = no context) */
  selectedContext: string | null;

  /** Callback invoked when user confirms selection */
  onSelect: (contextName: string | null) => void;

  /** Callback invoked when modal should close */
  onClose: () => void;
}
```

## Features

### 1. Context Selection

- Radio button interface with ASCII indicators `(*)` and `( )`
- Click or keyboard (Enter/Space) to select
- Displays context metadata:
  - Name
  - Chunk count (formatted with thousands separator)
  - Last indexed timestamp (human-readable format)

### 2. "None" Option

- Special dashed-border item at bottom of list
- Allows clearing context selection
- Useful for queries without CGRAG context

### 3. Actions

**CONFIRM Button:**
- Primary action
- Commits selection and closes modal

**REFRESH INDEX Button:**
- Secondary action
- Re-indexes the selected context
- Disabled when no context selected
- Shows loading state during refresh

**CREATE NEW INDEX Button:**
- Secondary action
- Placeholder for future CreateContextModal
- Currently shows alert (TODO: implement creation flow)

### 4. User Experience

**Keyboard Support:**
- ESC key closes modal
- Enter/Space selects focused context item
- Tab navigation between items

**Loading States:**
- Spinner animation while fetching contexts
- "REFRESHING..." button text during refresh

**Error Handling:**
- Red error panel if contexts fail to load
- Console error logging for debugging

**Empty State:**
- "No CGRAG indexes available" message when contexts list is empty

**Accessibility:**
- `role="dialog"` with `aria-modal="true"`
- `role="radiogroup"` for context list
- `role="radio"` with `aria-checked` for each item
- Focus management and keyboard navigation

## Styling

The component uses CSS Modules (`ContextSelector.module.css`) with terminal aesthetics:

- Phosphor orange borders (#ff9500)
- Pure black backgrounds (#000000)
- Cyan accents (#00ffff) for chunk counts
- Smooth transitions and hover effects
- Breathing animations on selected items
- Responsive design (stacks buttons on mobile)

## Data Flow

```
useContexts() hook
  ↓
Fetches contexts from API
  ↓
Displays in radio list
  ↓
User selects context
  ↓
Click CONFIRM
  ↓
onSelect(contextName) callback
  ↓
Parent component updates state
```

## Integration with useContexts Hook

The component uses the `useContexts` hook from `@/hooks/useContexts`:

```typescript
const { data: contexts, isLoading, error } = useContexts();
```

This provides:
- `contexts`: Array of `ContextInfo` objects
- `isLoading`: Boolean indicating fetch in progress
- `error`: Error object if fetch failed

## Integration with useRefreshContext Hook

The REFRESH INDEX button uses the `useRefreshContext` mutation:

```typescript
const refreshMutation = useRefreshContext();

const handleRefresh = async () => {
  if (localSelection) {
    await refreshMutation.mutateAsync(localSelection);
  }
};
```

This:
- Re-indexes the selected context
- Automatically invalidates contexts cache
- Triggers UI refresh with updated metadata

## Future Enhancements

### TODO: CreateContextModal

Replace the placeholder alert with a full modal:

```typescript
const [showCreateModal, setShowCreateModal] = useState(false);

const handleCreateNew = () => {
  setShowCreateModal(true);
};

// Render CreateContextModal when showCreateModal is true
```

The creation modal should:
1. Allow user to input context name
2. Browse for source directory
3. Select embedding model
4. Show progress during indexing
5. Add new context to list on success

## Example: Full Integration

```typescript
export const CodeChatPage: React.FC = () => {
  const [context, setContext] = useState<string | null>(null);
  const [showSelector, setShowSelector] = useState(false);

  return (
    <div className={styles.page}>
      {/* Header with context indicator */}
      <div className={styles.header}>
        <Button onClick={() => setShowSelector(true)}>
          CONTEXT: {context || 'NONE'}
        </Button>
      </div>

      {/* Query interface */}
      <QueryInput contextName={context} />

      {/* Context selector modal */}
      {showSelector && (
        <ContextSelector
          selectedContext={context}
          onSelect={(name) => {
            setContext(name);
            setShowSelector(false);
          }}
          onClose={() => setShowSelector(false)}
        />
      )}
    </div>
  );
};
```

## Visual Reference

```
+--[ CONTEXT SELECTION ]---------------------+
| Available CGRAG Indexes:                   |
+--------------------------------------------+
| (*) synapse-engine    [42,156 chunks]      |
|     Indexed: Nov 29, 2025, 10:30 AM        |
|                                            |
| ( ) my-app            [8,234 chunks]       |
|     Indexed: Nov 28, 2025, 03:00 PM        |
|                                            |
| ( ) documentation     [3,891 chunks]       |
|     Indexed: Nov 27, 2025, 09:15 AM        |
|                                            |
| ( ) None (no context)                      |
+--------------------------------------------+
| [CONFIRM]  [REFRESH INDEX]  [CREATE NEW]   |
+--------------------------------------------+
```

## Notes

- Modal overlay closes on click (but not when clicking modal content)
- Selection is local until CONFIRM is clicked (allows cancellation)
- Contexts are cached for 1 minute to reduce API calls
- Refresh invalidates cache and triggers refetch
- Component is fully responsive and accessible

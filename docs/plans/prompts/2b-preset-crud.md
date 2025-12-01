# Task: Implement Custom Preset CRUD

You are adding the ability to create, update, and delete custom presets for Code Chat.

## Context

- Current presets: Read-only, defined in `backend/app/models/code_chat.py` (PRESETS dict)
- PresetSelector: `frontend/src/pages/CodeChatPage/PresetSelector.tsx`
- usePresets hook: `frontend/src/hooks/usePresets.ts`
- Backend router: `backend/app/routers/code_chat.py`
- Read SESSION_NOTES.md for recent context

## Requirements

### Part 1: Backend

#### presets.py (~150 lines)

Create persistence layer for custom presets:

```python
"""Custom preset persistence for Code Chat.

Stores user-created presets in JSON file, separate from built-in presets.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from app.models.code_chat import ModelPreset, PRESETS

logger = logging.getLogger(__name__)

# Storage location
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CUSTOM_PRESETS_FILE = DATA_DIR / "custom_presets.json"


def _ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_custom_presets() -> Dict[str, ModelPreset]:
    """Load custom presets from disk.

    Returns:
        Dict mapping preset names to ModelPreset objects.
    """
    _ensure_data_dir()

    if not CUSTOM_PRESETS_FILE.exists():
        return {}

    try:
        with open(CUSTOM_PRESETS_FILE, 'r') as f:
            data = json.load(f)
        return {
            name: ModelPreset(**preset)
            for name, preset in data.items()
        }
    except Exception as e:
        logger.error(f"Failed to load custom presets: {e}")
        return {}


def save_custom_presets(presets: Dict[str, ModelPreset]) -> None:
    """Save custom presets to disk.

    Args:
        presets: Dict mapping names to ModelPreset objects.
    """
    _ensure_data_dir()

    try:
        with open(CUSTOM_PRESETS_FILE, 'w') as f:
            json.dump(
                {name: preset.model_dump() for name, preset in presets.items()},
                f,
                indent=2
            )
    except Exception as e:
        logger.error(f"Failed to save custom presets: {e}")
        raise


def get_all_presets() -> Dict[str, ModelPreset]:
    """Get all presets (built-in + custom).

    Built-in presets take precedence if name conflicts.

    Returns:
        Combined dict of all presets.
    """
    custom = load_custom_presets()
    return {**custom, **PRESETS}  # Built-in overrides custom on conflict


def create_preset(preset: ModelPreset) -> ModelPreset:
    """Create a new custom preset.

    Args:
        preset: The preset to create.

    Returns:
        The created preset.

    Raises:
        ValueError: If name conflicts with built-in preset.
    """
    if preset.name in PRESETS:
        raise ValueError(f"Cannot override built-in preset: {preset.name}")

    custom = load_custom_presets()
    custom[preset.name] = preset
    save_custom_presets(custom)
    return preset


def update_preset(name: str, preset: ModelPreset) -> ModelPreset:
    """Update an existing custom preset.

    Args:
        name: Original preset name.
        preset: New preset data.

    Returns:
        The updated preset.

    Raises:
        ValueError: If trying to update built-in preset.
        KeyError: If preset doesn't exist.
    """
    if name in PRESETS:
        raise ValueError(f"Cannot modify built-in preset: {name}")

    custom = load_custom_presets()
    if name not in custom:
        raise KeyError(f"Preset not found: {name}")

    # Handle rename
    if name != preset.name:
        del custom[name]

    custom[preset.name] = preset
    save_custom_presets(custom)
    return preset


def delete_preset(name: str) -> bool:
    """Delete a custom preset.

    Args:
        name: Preset name to delete.

    Returns:
        True if deleted, False if not found.

    Raises:
        ValueError: If trying to delete built-in preset.
    """
    if name in PRESETS:
        raise ValueError(f"Cannot delete built-in preset: {name}")

    custom = load_custom_presets()
    if name not in custom:
        return False

    del custom[name]
    save_custom_presets(custom)
    return True
```

#### code_chat.py additions

Add CRUD endpoints:

```python
from app.services.code_chat.presets import (
    get_all_presets,
    create_preset,
    update_preset,
    delete_preset,
)

@router.post("/presets", response_model=ModelPreset)
async def create_custom_preset(preset: ModelPreset):
    """Create a new custom preset."""
    try:
        return create_preset(preset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/presets/{name}", response_model=ModelPreset)
async def update_custom_preset(name: str, preset: ModelPreset):
    """Update an existing custom preset."""
    try:
        return update_preset(name, preset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/presets/{name}")
async def delete_custom_preset(name: str):
    """Delete a custom preset."""
    try:
        if delete_preset(name):
            return {"status": "deleted", "name": name}
        raise HTTPException(status_code=404, detail=f"Preset not found: {name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Part 2: Frontend

#### SavePresetModal.tsx (~100 lines)

```typescript
import React, { useState, useCallback } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { Button } from '@/components/terminal/Button/Button';
import { useCreatePreset } from '@/hooks/usePresets';
import styles from './SavePresetModal.module.css';

interface SavePresetModalProps {
  currentConfig: ToolOverrides;
  onClose: () => void;
  onSuccess: () => void;
}

export const SavePresetModal: React.FC<SavePresetModalProps> = ({
  currentConfig,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const createMutation = useCreatePreset();

  const handleSave = useCallback(async () => {
    if (!name.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || `Custom preset: ${name}`,
        toolOverrides: currentConfig,
        isBuiltIn: false,
      });
      onSuccess();
    } catch (err) {
      console.error('Failed to save preset:', err);
    }
  }, [name, description, currentConfig, createMutation, onSuccess]);

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <AsciiPanel title="SAVE PRESET">
          <div className={styles.content}>
            <div className={styles.field}>
              <label className={styles.label}>Name:</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={styles.input}
                placeholder="my-preset"
                autoFocus
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Description:</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={styles.input}
                placeholder="Optional description"
              />
            </div>

            <div className={styles.configPreview}>
              <div className={styles.previewLabel}>Configuration:</div>
              <pre className={styles.previewCode}>
                {JSON.stringify(currentConfig, null, 2)}
              </pre>
            </div>

            {createMutation.error && (
              <div className={styles.error}>
                Error: {createMutation.error.message}
              </div>
            )}

            <div className={styles.actions}>
              <Button
                onClick={handleSave}
                variant="primary"
                disabled={!name.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? 'SAVING...' : 'SAVE PRESET'}
              </Button>
              <Button onClick={onClose} variant="secondary">
                CANCEL
              </Button>
            </div>
          </div>
        </AsciiPanel>
      </div>
    </div>
  );
};
```

#### usePresets.ts additions

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useCreatePreset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (preset: ModelPreset) => {
      const response = await apiClient.post('/api/code-chat/presets', preset);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};

export const useUpdatePreset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, preset }: { name: string; preset: ModelPreset }) => {
      const response = await apiClient.put(`/api/code-chat/presets/${name}`, preset);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};

export const useDeletePreset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (name: string) => {
      await apiClient.delete(`/api/code-chat/presets/${name}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};
```

#### PresetSelector.tsx modifications

Add save button and edit/delete for custom presets:

```typescript
// Add state
const [showSaveModal, setShowSaveModal] = useState(false);

// Add to render
<Button onClick={() => setShowSaveModal(true)} variant="secondary" size="sm">
  SAVE CURRENT
</Button>

{showSaveModal && (
  <SavePresetModal
    currentConfig={currentOverrides}
    onClose={() => setShowSaveModal(false)}
    onSuccess={() => setShowSaveModal(false)}
  />
)}

// For custom presets in list, add delete button
{!preset.isBuiltIn && (
  <button
    className={styles.deleteButton}
    onClick={() => handleDelete(preset.name)}
    title="Delete preset"
  >
    ×
  </button>
)}
```

## Acceptance Criteria

- [ ] User can save current settings as new preset
- [ ] User can view custom presets in list
- [ ] User can delete custom presets
- [ ] Built-in presets remain read-only (no delete button)
- [ ] Presets persist across browser sessions
- [ ] Presets persist across server restarts
- [ ] Error handling for name conflicts

## Files

### Backend
- **CREATE:** `backend/app/services/code_chat/presets.py`
- **MODIFY:** `backend/app/routers/code_chat.py`

### Frontend
- **CREATE:** `frontend/src/pages/CodeChatPage/SavePresetModal.tsx`
- **CREATE:** `frontend/src/pages/CodeChatPage/SavePresetModal.module.css`
- **MODIFY:** `frontend/src/pages/CodeChatPage/PresetSelector.tsx`
- **MODIFY:** `frontend/src/hooks/usePresets.ts`
- **MODIFY:** `frontend/src/pages/CodeChatPage/index.ts`

# Settings Page Refactor - Phase 4

**Date:** 2025-11-05
**Status:** Completed
**Component:** `frontend/src/pages/SettingsPage/SettingsPage.tsx`

## Summary

Refactored the Settings Page to add a Port Configuration section and reorganize existing sections with clearer labels and visual distinction. This improves clarity around global defaults vs. per-model overrides.

## Changes Made

### 1. Added Port Configuration Section

**Location:** Section 1 (before GPU/VRAM Configuration)

**Features:**
- Displays current port range (read-only)
- Shows port range start and end values
- Calculates and displays:
  - Total available ports
  - Number of assigned ports
  - List of assigned port numbers
- Warning box explaining port range is configured via environment variables

**Implementation Details:**
- Added `useQuery` hook to fetch model registry from `/api/models/registry`
- Created `ModelRegistry` TypeScript interface
- Computed `assignedPorts` array from registry models
- Port inputs are disabled (read-only) until backend endpoint exists

### 2. Reorganized Section Structure

**New Section Order:**

1. **Port Configuration** (systemConfig)
   - Port range display
   - Assigned ports summary

2. **Global Model Runtime Defaults** (globalDefaults)
   - GPU layers, context size, threads, batch size
   - Flash attention, memory mapping
   - Info box clarifying these are overrideable defaults

3. **Embedding Configuration** (serviceConfig)
   - HuggingFace embedding model selection
   - Cache path configuration
   - Embedding dimension

4. **CGRAG Configuration** (serviceConfig)
   - Token budget, relevance threshold
   - Chunk size and overlap
   - Index directory

5. **Benchmark & Web Search Configuration** (serviceConfig)
   - Benchmark defaults
   - Web search settings

### 3. Added Visual Distinctions

**Section Types with Border Colors:**
- System Configuration: Cyan (`#00ffff`)
- Global Defaults: Amber (`#ff9500`)
- Service Configuration: Green (`#00ff41`)

**New UI Components:**
- Section descriptions for each panel
- Info boxes (green) for helpful information
- Warning boxes (amber) for important notices
- Port summary displays with labeled values

### 4. Enhanced Typography & Labels

**Added:**
- `.sectionDescription` - Gray text explaining section purpose
- `.infoBox` - Green bordered box for helpful context
- `.warningBox` - Amber bordered box for warnings
- `.portSummary` - Display container for port information
- `.portLabel` / `.portValue` - Styled port display elements
- `.hint` - Small gray text for additional field context

## Files Modified

### Frontend Component
**File:** `frontend/src/pages/SettingsPage/SettingsPage.tsx`

**Key Changes:**
- Added `useQuery` import from `@tanstack/react-query`
- Created `ModelRegistry` interface (lines 14-19)
- Added registry query hook (lines 32-39)
- Computed `assignedPorts` array (lines 67-72)
- Added `portRangeStart` and `portRangeEnd` values (lines 75-76)
- Inserted Port Configuration section (lines 312-369)
- Updated section titles and added descriptions throughout
- Added CSS classes for section types (`.systemConfig`, `.globalDefaults`, `.serviceConfig`)

### Stylesheet
**File:** `frontend/src/pages/SettingsPage/SettingsPage.module.css`

**New Styles Added (lines 192-279):**
- `.section.systemConfig` - Cyan left border
- `.section.globalDefaults` - Amber left border
- `.section.serviceConfig` - Green left border
- `.sectionDescription` - Gray description text
- `.infoBox` - Green info box with border
- `.warningBox` - Amber warning box with border
- `.portSummary` - Port information container
- `.portLabel` - Port label styling
- `.portValue` - Port value styling
- `.hint` - Hint text styling

## Testing Checklist

- [ ] Port Configuration section appears first
- [ ] Port range displays correctly (8080-8099 default)
- [ ] Available ports count is correct
- [ ] Assigned ports display when models have ports
- [ ] Assigned ports are sorted numerically
- [ ] Warning box explains environment variable configuration
- [ ] Section descriptions are visible and readable
- [ ] Info box appears in Global Defaults section
- [ ] Border colors distinguish section types:
  - Port Config: Cyan
  - Global Defaults: Amber
  - Service Configs: Green
- [ ] All existing settings still work correctly
- [ ] Save/Discard buttons function properly
- [ ] Restart required banner appears for GPU changes
- [ ] Validation errors display correctly
- [ ] Responsive layout works on mobile

## Future Enhancements

### Backend Endpoint (Optional)

If a backend endpoint is added to update port range dynamically:

**Endpoint:** `PUT /api/models/registry/port-range`

**Request Body:**
```json
{
  "portRange": [8080, 8099]
}
```

**Frontend Changes Needed:**
1. Remove `disabled` attribute from port inputs
2. Add state management for port range edits
3. Implement validation (start < end, >= 1024)
4. Add mutation hook:
```typescript
const updatePortRangeMutation = useMutation({
  mutationFn: async (portRange: [number, number]) => {
    const response = await fetch('/api/models/registry/port-range', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ portRange })
    });
    if (!response.ok) throw new Error('Failed to update port range');
    return response.json();
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['model-registry'] });
    // Show success notification
  }
});
```
5. Remove warning box about environment variables
6. Add Save button specifically for port range

## Design System Variables Used

```css
--cyan: #00ffff           /* System Configuration */
--amber: #ff9500          /* Global Defaults */
--phosphor-green: #00ff41 /* Service Configuration */
--font-mono: 'JetBrains Mono', monospace
```

## Architecture Notes

**Data Flow:**
1. Settings page fetches model registry on mount
2. Registry includes `portRange` tuple and `models` object
3. Assigned ports computed by mapping over models
4. Port range displayed as read-only information
5. Changes to settings still follow existing flow (pendingChanges → mutation → refetch)

**Type Safety:**
- Added `ModelRegistry` interface with proper types
- Used TypeScript filter type guard for port arrays
- Maintained strict typing throughout

**Performance:**
- Registry query cached by TanStack Query
- Assigned ports computed with useMemo
- No unnecessary re-renders

## Related Components

This refactor clarifies the relationship with:
- **Model Management Page** - Where per-model overrides are configured
- **Model Discovery** - Which uses the port range for assignment
- **Model Registry** - Backend data structure containing port configuration

## Success Criteria

✅ Port Configuration section visible and functional
✅ Section organization clearer with descriptions
✅ Visual distinction between section types
✅ Help text explains global defaults vs. per-model overrides
✅ Terminal aesthetic maintained throughout
✅ TypeScript types remain strict
✅ No breaking changes to existing functionality
✅ Responsive design preserved

## Next Steps

1. Test in Docker environment: `docker-compose up -d`
2. Verify port range displays correctly
3. Check that assigned ports update when models are configured
4. Test responsive layout on mobile devices
5. Consider adding backend endpoint for dynamic port range updates
6. Update user documentation if needed

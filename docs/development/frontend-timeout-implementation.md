# Frontend Tier-Specific Timeout Implementation

## Overview

Implemented tier-specific timeout logic in the MAGI frontend to match the backend's timeout configuration. Different query tiers now have appropriate timeout values that account for backend processing, retry logic, and network overhead.

## Implementation Details

### 1. Base API Client Timeout Update

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/api/client.ts`

- Updated default timeout from `30000ms` (30s) to `60000ms` (60s)
- This serves as a baseline that can be overridden per-request
- Provides a safety net for requests that don't explicitly set a timeout

```typescript
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60000, // Base timeout (60s) - can be overridden per-request
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### 2. Tier-Specific Timeout Utility

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/utils/queryTimeouts.ts`

Created a comprehensive timeout utility module with:

#### Timeout Configuration

```typescript
export const TIER_TIMEOUTS: Record<ModelTier, number> = {
  Q2: 45000,   // 45 seconds for simple queries
  Q3: 90000,   // 90 seconds for moderate queries
  Q4: 180000,  // 180 seconds for complex/deep analysis
};
```

These timeouts account for:
- **Q2 (simple)**: 30s backend + retries = 45s frontend timeout
- **Q3 (moderate)**: 45s backend + retries = 90s frontend timeout
- **Q4 (complex)**: 120s backend + retries = 180s frontend timeout

#### Mode-to-Tier Mapping

```typescript
export const MODE_TO_TIER: Record<QueryMode, ModelTier> = {
  auto: 'Q3',      // Default to middle tier for auto mode
  simple: 'Q2',    // Fast tier
  moderate: 'Q3',  // Balanced tier
  complex: 'Q4',   // Deep analysis tier
};
```

#### Utility Functions

1. **`getQueryTimeout(mode: QueryMode): number`**
   - Returns appropriate timeout for a given query mode
   - Defaults to Q3 (90s) for 'auto' mode
   - Example: `getQueryTimeout('simple')` → `45000`

2. **`getTimeoutForTier(tier: ModelTier): number`**
   - Returns timeout for a specific model tier
   - Useful when tier is known from response metadata
   - Example: `getTimeoutForTier('Q4')` → `180000`

3. **`getTimeoutDisplay(mode: QueryMode): string`**
   - Returns human-readable timeout string for UI display
   - Example: `getTimeoutDisplay('complex')` → `"180s"`

### 3. Query Hook Integration

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/hooks/useQuery.ts`

Updated `useQuerySubmit` hook to apply tier-specific timeouts:

```typescript
export const useQuerySubmit = (): UseMutationResult<
  QueryResponse,
  Error,
  QueryRequest
> => {
  return useMutation({
    mutationFn: async (request: QueryRequest): Promise<QueryResponse> => {
      // Determine timeout based on query mode
      const timeout = getQueryTimeout(request.mode);

      // Make request with tier-specific timeout
      const response = await apiClient.post<QueryResponse>(
        endpoints.query.execute,
        request,
        {
          timeout, // Override default timeout with tier-specific value
        }
      );

      return response.data;
    },
  });
};
```

**Key Features:**
- Automatically determines correct timeout based on `request.mode`
- Overrides default axios timeout on a per-request basis
- No global state or side effects
- Fully type-safe with TypeScript

### 4. UI Timeout Indicator

**Files:**
- `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/query/QueryInput.tsx`
- `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/query/QueryInput.module.css`

Added visual indicator showing expected timeout based on selected mode:

#### Component Changes

```typescript
import { getTimeoutDisplay } from '../../utils/queryTimeouts';

// In JSX:
<div className={styles.timeoutHint} aria-label="Maximum query timeout">
  MAX WAIT: {getTimeoutDisplay(mode)}
</div>
```

#### Styling

```css
.timeoutHint {
  color: var(--text-secondary, #666);
  font-size: 10px;
  margin-left: auto;
  padding: 4px 8px;
  border: 1px solid var(--border-secondary, #333);
  background: rgba(0, 0, 0, 0.5);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
```

**Visual Result:**
- Displays in terminal aesthetic style
- Updates dynamically when mode changes
- Shows "MAX WAIT: 45s", "MAX WAIT: 90s", or "MAX WAIT: 180s"
- Positioned next to the EXECUTE button
- Accessible with proper ARIA label

## Timeout Behavior by Mode

| Query Mode | Model Tier | Backend Timeout | Frontend Timeout | UI Display |
|-----------|-----------|----------------|------------------|-----------|
| `simple`  | Q2        | ~30s + retries | 45s              | "45s"     |
| `auto`    | Q3        | ~45s + retries | 90s              | "90s"     |
| `moderate`| Q3        | ~45s + retries | 90s              | "90s"     |
| `complex` | Q4        | ~120s + retries| 180s             | "180s"    |

## Testing

### Test Coverage

Created comprehensive unit tests in `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/utils/queryTimeouts.test.ts`:

- **22 passing tests** covering:
  - Timeout value correctness
  - Mode-to-tier mapping
  - Function return values
  - Display formatting
  - Edge cases and defaults
  - Type safety

### Test Results

```
✓ src/utils/queryTimeouts.test.ts (22 tests) 3ms

Test Files  1 passed (1)
     Tests  22 passed (22)
```

### TypeScript Compilation

```bash
npx tsc --noEmit
# ✓ No errors - all types valid
```

## Usage Examples

### In Components

```typescript
import { getQueryTimeout, getTimeoutDisplay } from '@/utils/queryTimeouts';

// Get timeout for a specific mode
const timeout = getQueryTimeout('complex'); // 180000

// Display in UI
const display = getTimeoutDisplay('simple'); // "45s"

// Dynamic based on state
const [mode, setMode] = useState<QueryMode>('auto');
const currentTimeout = getTimeoutDisplay(mode); // "90s"
```

### In API Calls

```typescript
// Automatically applied in useQuerySubmit hook
const mutation = useQuerySubmit();

mutation.mutate({
  query: "Complex analysis query",
  mode: "complex", // Will use 180s timeout automatically
  useContext: true,
  maxTokens: 2048,
  temperature: 0.7,
});
```

### Manual API Calls

```typescript
import { apiClient } from '@/api/client';
import { getQueryTimeout } from '@/utils/queryTimeouts';

const mode: QueryMode = 'complex';
const timeout = getQueryTimeout(mode);

const response = await apiClient.post('/api/query', data, {
  timeout, // Override default with tier-specific timeout
});
```

## Benefits

1. **Prevents Premature Timeouts**
   - Q4 queries won't timeout at 30s or 60s anymore
   - Each tier has appropriate timeout buffer

2. **Improved User Experience**
   - Users see expected wait time in UI
   - No unexpected timeout errors for complex queries
   - Clear feedback on mode selection

3. **Type Safety**
   - All timeout logic is fully typed
   - Compile-time safety with TypeScript strict mode
   - No magic numbers scattered in code

4. **Maintainability**
   - Single source of truth for timeout configuration
   - Easy to adjust timeouts if backend changes
   - Well-documented with inline comments

5. **Testability**
   - Comprehensive unit test coverage
   - Easy to verify timeout calculations
   - No side effects or global state

## Configuration

To adjust timeouts in the future, modify the `TIER_TIMEOUTS` constant in `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/utils/queryTimeouts.ts`:

```typescript
export const TIER_TIMEOUTS: Record<ModelTier, number> = {
  Q2: 45000,   // Adjust for Q2 tier
  Q3: 90000,   // Adjust for Q3 tier
  Q4: 180000,  // Adjust for Q4 tier
};
```

Changes will automatically propagate to:
- API client requests
- UI timeout displays
- All components using the utility functions

## Files Modified/Created

### Created
1. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/utils/queryTimeouts.ts` - Timeout utility module
2. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/utils/queryTimeouts.test.ts` - Comprehensive tests

### Modified
1. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/api/client.ts` - Updated base timeout
2. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/hooks/useQuery.ts` - Added tier-specific timeout logic
3. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/query/QueryInput.tsx` - Added timeout display
4. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/query/QueryInput.module.css` - Added timeout hint styling

## Next Steps

### Testing Recommendations

1. **Integration Testing**
   - Test with actual backend running
   - Verify timeouts work with different query modes
   - Ensure Q4 queries complete without timeout errors

2. **User Testing**
   - Verify timeout indicator is visible and helpful
   - Check that mode selection updates timeout display correctly
   - Ensure loading states are clear during long queries

3. **Performance Testing**
   - Confirm Q2 queries still complete quickly
   - Verify Q3 queries handle moderate complexity
   - Test Q4 queries with complex analysis tasks

### Potential Enhancements

1. **Dynamic Timeout Adjustment**
   - Could adjust timeout based on CGRAG context size
   - Longer timeout if using more context artifacts

2. **Timeout Progress Indicator**
   - Show progress bar during long Q4 queries
   - Display estimated time remaining

3. **Timeout Analytics**
   - Track how often queries approach timeout limits
   - Identify if timeout values need adjustment

## Implementation Quality

- ✅ **Type Safety**: Full TypeScript strict mode compliance
- ✅ **Test Coverage**: 22 comprehensive unit tests
- ✅ **Performance**: No runtime overhead, pre-calculated values
- ✅ **Accessibility**: ARIA labels on UI elements
- ✅ **Documentation**: Inline comments and TSDoc annotations
- ✅ **Maintainability**: Single source of truth, clear separation of concerns
- ✅ **User Experience**: Clear visual feedback on expected timeouts

## Conclusion

The tier-specific timeout implementation provides a robust, type-safe solution that prevents premature timeouts while maintaining excellent user experience. The implementation is well-tested, maintainable, and follows frontend engineering best practices with proper separation of concerns and comprehensive documentation.

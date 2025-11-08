# Frontend Architecture - Query UI

## Component Hierarchy

```
App
└── HomePage
    ├── Header
    │   ├── Title: "NEURAL SUBSTRATE ORCHESTRATOR"
    │   └── SystemStatus
    │       ├── MetricDisplay (VRAM)
    │       ├── MetricDisplay (QUERIES)
    │       └── MetricDisplay (CACHE)
    │
    ├── InputSection
    │   ├── QueryInput
    │   │   ├── Header (prompt, title, char count)
    │   │   ├── Textarea
    │   │   ├── Controls
    │   │   │   ├── ModeSelector (dropdown)
    │   │   │   ├── CGRAGToggle (checkbox)
    │   │   │   ├── AdvancedToggle (button)
    │   │   │   └── SubmitButton (Button component)
    │   │   └── AdvancedSettings (conditional)
    │   │       ├── MaxTokensSlider
    │   │       └── TemperatureSlider
    │   └── WarningMessage (conditional - no models)
    │
    └── ResponseSection
        ├── LoadingIndicator (conditional)
        ├── ErrorPanel (conditional)
        └── ResponseDisplay
            ├── QueryHeader
            ├── ResponsePanel
            │   ├── ResponseText (pre)
            │   └── CopyButton
            └── MetadataPanel
                ├── MetricRow
                │   ├── MetricDisplay (MODEL)
                │   ├── MetricDisplay (TOKENS)
                │   ├── MetricDisplay (TIME)
                │   └── CacheIndicator (conditional)
                ├── ComplexitySection (conditional)
                │   ├── ComplexityHeader
                │   ├── Reasoning
                │   └── Indicators
                └── CGRAGSection (conditional)
                    ├── CGRAGHeader
                    └── ArtifactList
                        └── Artifact[]
                            ├── ArtifactMain
                            └── ArtifactDetails
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                           User Input                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       QueryInput Component                       │
│  - Captures query text                                          │
│  - Collects mode, useContext, maxTokens, temperature           │
│  - Validates input (non-empty)                                 │
│  - Calls onSubmit handler                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HomePage.handleQuerySubmit                   │
│  - Receives query string and options                           │
│  - Calls queryMutation.mutate()                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       useQuerySubmit Hook                        │
│  - TanStack Query mutation                                      │
│  - Sends POST /api/query                                        │
│  - Manages loading/error/success states                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Client (Axios)                         │
│  - Adds base URL (http://localhost:8000)                       │
│  - Adds headers (Content-Type: application/json)               │
│  - Handles request/response interceptors                       │
│  - Returns response data                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend FastAPI Server                      │
│  - Receives QueryRequest                                        │
│  - Assesses complexity                                          │
│  - Routes to appropriate model tier                            │
│  - Retrieves CGRAG context (if enabled)                        │
│  - Generates response                                           │
│  - Returns QueryResponse with metadata                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  queryMutation.onSuccess Handler                 │
│  - Receives QueryResponse                                       │
│  - Calls setLatestResponse(data)                               │
│  - Updates HomePage state                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ResponseDisplay Component                      │
│  - Receives response prop                                       │
│  - Renders response text                                        │
│  - Renders metadata (model, tokens, time)                      │
│  - Renders complexity assessment                               │
│  - Renders CGRAG artifacts                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                          User Sees Result                        │
└─────────────────────────────────────────────────────────────────┘
```

## State Management

### Global State (TanStack Query)
```typescript
// Model status (useModelStatus)
{
  data: ModelStatusResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  refetchInterval: 5000ms;
}

// Query mutation (useQuerySubmit)
{
  mutate: (request: QueryRequest) => void;
  isPending: boolean;
  isError: boolean;
  error: Error | null;
  data: QueryResponse | undefined;
}
```

### Local State (HomePage)
```typescript
const [latestResponse, setLatestResponse] = useState<QueryResponse | null>(null);
```

### Component State (QueryInput)
```typescript
const [query, setQuery] = useState<string>('');
const [mode, setMode] = useState<QueryMode>('auto');
const [useContext, setUseContext] = useState<boolean>(true);
const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
const [maxTokens, setMaxTokens] = useState<number>(512);
const [temperature, setTemperature] = useState<number>(0.7);
```

## Type Definitions

### Request Types
```typescript
interface QueryRequest {
  query: string;
  mode: QueryMode;
  useContext: boolean;
  maxTokens: number;
  temperature: number;
}

type QueryMode = 'auto' | 'simple' | 'moderate' | 'complex';
```

### Response Types
```typescript
interface QueryResponse {
  id: string;
  query: string;
  response: string;
  metadata: QueryMetadata;
  timestamp: string;
}

interface QueryMetadata {
  modelTier: string;
  modelId: string;
  complexity: QueryComplexity | null;
  tokensUsed: number;
  processingTimeMs: number;
  cgragArtifacts: number;
  cgragArtifactsInfo: ArtifactInfo[];
  cacheHit: boolean;
}
```

## API Endpoints Used

```typescript
endpoints = {
  models: {
    status: '/api/models/status',  // GET - Model status with metrics
  },
  query: {
    execute: '/api/query',         // POST - Submit query
  },
}
```

## CSS Architecture

### Design Tokens (CSS Custom Properties)
```css
:root {
  /* Colors */
  --bg-primary: #000000;
  --bg-panel: #0a0a0a;
  --phosphor-green: #00ff41;
  --cyan: #00ffff;
  --amber: #ff9500;
  --border-primary: #00ff41;
  --border-secondary: #333;

  /* Typography */
  --font-mono: 'JetBrains Mono', monospace;
  --text-xs: 10px;
  --text-sm: 12px;
  --text-md: 14px;
  --text-lg: 16px;
  --text-xl: 20px;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;

  /* Transitions */
  --transition-fast: 0.1s ease;
  --transition-base: 0.2s ease;
  --transition-slow: 0.3s ease;
}
```

### CSS Modules Structure
```
QueryInput.module.css
├── .queryInput (container)
├── .header (title bar)
├── .textarea (input field)
├── .controls (control row)
├── .modeSelector, .toggleGroup, .advancedToggle
└── .advanced (settings panel)
    └── .setting, .slider

ResponseDisplay.module.css
├── .responseDisplay (container)
├── .placeholder (empty state)
├── .queryHeader (query echo)
├── .responseContent (response panel)
│   ├── .responseText
│   └── .copyButton
└── .metadata (metadata panel)
    ├── .metricRow
    ├── .complexity
    └── .cgrag
        └── .artifactList
            └── .artifact

HomePage.module.css
├── .page (main container)
├── .header (system header)
│   ├── .title
│   └── .systemStatus
└── .content
    ├── .inputSection
    │   └── .warningMessage
    └── .responseSection
        ├── .loadingIndicator
        └── .errorMessage
```

## Event Flow

### Query Submission
```
1. User types query in textarea
2. User clicks "EXECUTE" or presses Cmd/Ctrl+Enter
3. QueryInput validates (non-empty)
4. QueryInput calls onSubmit(query, options)
5. HomePage.handleQuerySubmit receives data
6. queryMutation.mutate() called
7. Loading state activates (isPending: true)
8. UI shows loading indicator
9. Backend processes query
10. Response received
11. onSuccess handler called
12. setLatestResponse(data) updates state
13. ResponseDisplay re-renders with new data
14. Loading state deactivates
```

### Error Handling
```
1. Query submitted
2. Backend returns error or timeout
3. queryMutation.onError handler called
4. Error logged to console
5. Error panel displays in UI
6. Previous response remains visible
7. User can retry
```

### CGRAG Toggle
```
1. User clicks CGRAG checkbox
2. setUseContext(!useContext)
3. Checkbox visual state updates
4. Query submission includes useContext value
5. Backend skips/includes context retrieval
6. Response metadata shows cgragArtifacts: 0 or N
7. CGRAG section conditionally renders
```

## Performance Optimizations

### Memoization
```typescript
// Event handlers
const handleSubmit = useCallback(() => {
  // ...
}, [query, mode, useContext, maxTokens, temperature, isLoading, disabled, onSubmit]);

const handleKeyDown = useCallback((e) => {
  // ...
}, [handleSubmit]);

const copyToClipboard = useCallback(() => {
  // ...
}, [response]);
```

### Conditional Rendering
```typescript
// Only render when needed
{queryMutation.isPending && <LoadingIndicator />}
{queryMutation.isError && <ErrorPanel />}
{metadata.complexity && <ComplexitySection />}
{metadata.cgragArtifacts > 0 && <CGRAGSection />}
```

### TanStack Query Caching
```typescript
{
  queryKey: ['modelStatus'],
  refetchInterval: 5000,
  staleTime: 3000,
  // Automatic caching, refetching, and garbage collection
}
```

## Accessibility Features

### Semantic HTML
```html
<label for="mode-select">MODE:</label>
<select id="mode-select" aria-label="Query mode">...</select>

<button aria-label="Submit query" aria-expanded="false">...</button>

<div role="status" aria-live="polite">Processing query...</div>
```

### Keyboard Navigation
```
Tab        → Navigate between controls
Enter      → Activate button
Space      → Toggle checkbox
Cmd+Enter  → Submit query (custom shortcut)
```

### Focus Management
```css
.textarea:focus {
  border-color: var(--phosphor-green);
  outline: none;
}

.button:focus-visible {
  outline: 2px solid var(--phosphor-green);
  outline-offset: 2px;
}
```

## Testing Strategy

### Unit Tests (React Testing Library)
```typescript
// Test component rendering
test('renders QueryInput', () => {
  render(<QueryInput onSubmit={mockFn} />);
  expect(screen.getByPlaceholderText(/enter query/i)).toBeInTheDocument();
});

// Test interactions
test('submits query on Enter', () => {
  const handleSubmit = jest.fn();
  render(<QueryInput onSubmit={handleSubmit} />);
  const textarea = screen.getByRole('textbox');
  fireEvent.change(textarea, { target: { value: 'test' } });
  fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true });
  expect(handleSubmit).toHaveBeenCalledWith('test', expect.any(Object));
});
```

### Integration Tests
```typescript
// Test full query flow
test('complete query flow', async () => {
  render(<HomePage />);
  const input = screen.getByPlaceholderText(/enter query/i);
  fireEvent.change(input, { target: { value: 'What is Python?' } });
  fireEvent.click(screen.getByText(/execute/i));
  await waitFor(() => {
    expect(screen.getByText(/response/i)).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)
```typescript
test('submits query and displays response', async ({ page }) => {
  await page.goto('http://localhost:5174');
  await page.fill('[data-testid="query-input"]', 'What is Python?');
  await page.click('[data-testid="submit-button"]');
  await expect(page.locator('[data-testid="response"]')).toBeVisible();
});
```

## Future Architecture Considerations

### WebSocket Integration
```typescript
// Real-time query status updates
const useQueryStatus = (queryId: string) => {
  const [status, setStatus] = useState<QueryStatus>('pending');

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/query/${queryId}`);
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setStatus(update.status);
    };
    return () => ws.close();
  }, [queryId]);

  return status;
};
```

### Query History
```typescript
// Store and display previous queries
const useQueryHistory = () => {
  return useQuery({
    queryKey: ['queryHistory'],
    queryFn: () => apiClient.get('/api/query/history'),
    staleTime: 60000,
  });
};
```

### Streaming Responses
```typescript
// Token-by-token display
const useStreamingQuery = (request: QueryRequest) => {
  const [tokens, setTokens] = useState<string[]>([]);

  useEffect(() => {
    const eventSource = new EventSource('/api/query/stream');
    eventSource.onmessage = (event) => {
      setTokens(prev => [...prev, event.data]);
    };
    return () => eventSource.close();
  }, [request]);

  return tokens.join('');
};
```

---

**Last Updated:** 2025-01-15
**Status:** Complete and Production Ready

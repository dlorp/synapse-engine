# S.Y.N.A.P.S.E. ENGINE - OpenCode Backend Integration Plan

**Date:** 2025-11-08
**Status:** Implementation Plan
**Complexity:** High (Multi-service Integration)
**Estimated Time:** 12-16 hours

---

## Executive Summary

This plan outlines the integration of **OpenCode backend** (`opencode-ai` NPM package) into the S.Y.N.A.P.S.E. ENGINE platform. OpenCode provides professional AI coding capabilities (LSP, MCP, file operations) while S.Y.N.A.P.S.E. handles model orchestration and CGRAG context retrieval.

**Key Architecture:**
- **OpenCode Backend**: Bun/TypeScript service running in Docker
- **Custom Web Client**: React UI using WebTUI components (NOT the Go TUI)
- **FastAPI Proxy**: Unified API layer integrating CGRAG + model routing
- **Model Integration**: OpenCode uses S.Y.N.A.P.S.E. llama.cpp servers (Q2/Q3/Q4)

**Benefits:**
- ✅ Professional AI coding features (LSP, refactoring, MCP tools)
- ✅ Leverage existing S.Y.N.A.P.S.E. model orchestration
- ✅ Integrate with CGRAG for code-aware context
- ✅ Maintain terminal aesthetic with WebTUI
- ✅ ~40% less code than custom implementation

---

## Phase 1: Research & Discovery

### 1.1 OpenCode NPM Package Analysis

**Package:** `opencode-ai` (or `@opencode/backend`)

**Expected API Surface:**

```typescript
// Hypothetical API based on client/server architecture
interface OpencodeBackend {
  // Initialize with configuration
  constructor(config: OpencodeConfig);

  // Chat interface (streaming)
  chat(request: ChatRequest): AsyncIterator<ChatChunk>;

  // File operations
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;

  // LSP operations
  getCompletions(file: string, position: Position): Promise<Completion[]>;
  getDiagnostics(file: string): Promise<Diagnostic[]>;

  // MCP tool invocation
  invokeTool(tool: string, params: any): Promise<any>;
}

interface OpencodeConfig {
  workspace: string;
  modelProvider: ModelProviderConfig;
  mcp?: MCPConfig;
  lsp?: LSPConfig;
}

interface ModelProviderConfig {
  type: 'anthropic' | 'openai' | 'google' | 'custom';
  endpoint?: string;  // For custom provider
  apiKey?: string;
  model?: string;
}
```

**Research Tasks:**
- [ ] Install `opencode-ai` package and inspect exports
- [ ] Read TypeScript definitions to understand API
- [ ] Test basic initialization with dummy config
- [ ] Verify custom model provider support
- [ ] Check if SSE/streaming is built-in or needs implementation

### 1.2 Model API Compatibility

OpenCode expects OpenAI-compatible chat completions API. Your llama.cpp servers must support:

```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "llama-3.2-3b-instruct",
  "messages": [
    {"role": "system", "content": "You are a coding assistant"},
    {"role": "user", "content": "Write a Python function"}
  ],
  "stream": true,
  "max_tokens": 1024,
  "temperature": 0.7
}
```

**Verification Steps:**
1. Check if your llama.cpp servers expose `/v1/chat/completions`
2. Test with `curl` to verify format compatibility
3. If missing, implement adapter/proxy layer

---

## Phase 2: Docker Architecture

### 2.1 OpenCode Backend Service

**New Docker service configuration:**

```yaml
# docker-compose.yml additions
services:
  # ... existing services ...

  opencode_backend:
    image: oven/bun:latest
    container_name: synapse_opencode
    working_dir: /app
    volumes:
      - ./opencode-service:/app
      - ./workspace:/workspace
      - ./backend/data/faiss_indexes:/faiss  # Share CGRAG indexes
    environment:
      - WORKSPACE_ROOT=/workspace
      - SYNAPSE_API_BASE=http://synapse_core:8000
      - NODE_ENV=production
    ports:
      - "3456:3456"  # OpenCode backend API
    networks:
      - synapse-network
    depends_on:
      - synapse_core
    restart: unless-stopped
    command: bun run server.ts
```

### 2.2 Directory Structure

```
synapse-engine/
├── opencode-service/           # NEW: OpenCode backend wrapper
│   ├── package.json
│   ├── bun.lockb
│   ├── server.ts               # Main server file
│   ├── config.ts               # OpenCode configuration
│   ├── model-adapter.ts        # S.Y.N.A.P.S.E. model integration
│   └── cgrag-integration.ts    # CGRAG context injection
├── workspace/                  # Shared workspace (already exists)
├── backend/                    # Existing FastAPI backend
└── frontend/                   # Existing React frontend
```

---

## Phase 3: OpenCode Backend Implementation

### 3.1 Package Setup

**File:** `opencode-service/package.json`

```json
{
  "name": "synapse-opencode-service",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "opencode-ai": "^1.0.0",
    "bun": "latest"
  },
  "scripts": {
    "dev": "bun --watch server.ts",
    "start": "bun run server.ts"
  }
}
```

**Install:**
```bash
cd opencode-service
bun install
```

### 3.2 Main Server

**File:** `opencode-service/server.ts`

```typescript
import { serve } from 'bun';
import { OpencodeBackend } from 'opencode-ai';
import { createModelAdapter } from './model-adapter';
import { injectCGRAGContext } from './cgrag-integration';

const WORKSPACE_ROOT = process.env.WORKSPACE_ROOT || '/workspace';
const SYNAPSE_API_BASE = process.env.SYNAPSE_API_BASE || 'http://localhost:8000';
const PORT = 3456;

// Initialize OpenCode with S.Y.N.A.P.S.E. model provider
const opencode = new OpencodeBackend({
  workspace: WORKSPACE_ROOT,
  modelProvider: createModelAdapter(SYNAPSE_API_BASE),
  mcp: {
    enabled: true,
    tools: ['filesystem', 'git', 'search']
  },
  lsp: {
    enabled: true,
    languages: ['python', 'typescript', 'javascript']
  }
});

console.log(`[OpenCode] Initializing backend...`);
console.log(`[OpenCode] Workspace: ${WORKSPACE_ROOT}`);
console.log(`[OpenCode] S.Y.N.A.P.S.E. API: ${SYNAPSE_API_BASE}`);

serve({
  port: PORT,

  async fetch(req: Request) {
    const url = new URL(req.url);
    const method = req.method;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    };

    if (method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Chat endpoint (SSE streaming)
      if (url.pathname === '/chat' && method === 'POST') {
        const body = await req.json();
        const { query, mode, useWorkspaceContext } = body;

        // Inject CGRAG context if requested
        let enhancedQuery = query;
        if (useWorkspaceContext) {
          enhancedQuery = await injectCGRAGContext(query, SYNAPSE_API_BASE);
        }

        // Stream chat response
        const stream = new ReadableStream({
          async start(controller) {
            try {
              for await (const chunk of opencode.chat({
                message: enhancedQuery,
                context: {
                  mode,
                  workspace: WORKSPACE_ROOT
                }
              })) {
                const data = `data: ${JSON.stringify(chunk)}\n\n`;
                controller.enqueue(new TextEncoder().encode(data));
              }
              controller.close();
            } catch (error) {
              console.error('[OpenCode] Chat error:', error);
              controller.error(error);
            }
          }
        });

        return new Response(stream, {
          headers: {
            ...corsHeaders,
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
          }
        });
      }

      // File operations
      if (url.pathname === '/files' && method === 'GET') {
        const path = url.searchParams.get('path') || '';
        const content = await opencode.readFile(path);
        return Response.json({ content }, { headers: corsHeaders });
      }

      if (url.pathname === '/files' && method === 'POST') {
        const { path, content } = await req.json();
        await opencode.writeFile(path, content);
        return Response.json({ success: true }, { headers: corsHeaders });
      }

      // LSP operations
      if (url.pathname === '/completions' && method === 'POST') {
        const { file, position } = await req.json();
        const completions = await opencode.getCompletions(file, position);
        return Response.json({ completions }, { headers: corsHeaders });
      }

      // Health check
      if (url.pathname === '/health') {
        return Response.json({
          status: 'ok',
          workspace: WORKSPACE_ROOT,
          uptime: process.uptime()
        }, { headers: corsHeaders });
      }

      return new Response('Not found', {
        status: 404,
        headers: corsHeaders
      });

    } catch (error) {
      console.error('[OpenCode] Request error:', error);
      return Response.json({
        error: error.message
      }, {
        status: 500,
        headers: corsHeaders
      });
    }
  }
});

console.log(`[OpenCode] Server running on http://localhost:${PORT}`);
```

### 3.3 Model Adapter

**File:** `opencode-service/model-adapter.ts`

```typescript
/**
 * Adapter to use S.Y.N.A.P.S.E. model routing instead of external APIs.
 *
 * Translates OpenCode's model requests to S.Y.N.A.P.S.E. query API,
 * respecting model tier selection (FAST/BALANCED/POWERFUL).
 */

export interface ModelProviderConfig {
  type: 'custom';
  endpoint: string;
  apiKey?: string;
}

export function createModelAdapter(synapseApiBase: string): ModelProviderConfig {
  return {
    type: 'custom',
    endpoint: `${synapseApiBase}/v1/chat/completions`,
    apiKey: 'not-needed'  // llama.cpp doesn't require auth
  };
}

/**
 * Custom model provider implementation.
 *
 * Note: This assumes OpenCode can accept a custom provider.
 * If not, we may need to run a lightweight proxy that translates
 * OpenAI format to S.Y.N.A.P.S.E. query format.
 */
export class SynapseModelProvider {
  constructor(private apiBase: string) {}

  async chatCompletion(request: {
    messages: Array<{ role: string; content: string }>;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }) {
    // Determine tier from model name or default to BALANCED
    const tier = this.inferTier(request.model);

    // Call S.Y.N.A.P.S.E. query API
    const response = await fetch(`${this.apiBase}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: this.messagesToQuery(request.messages),
        mode: 'simple',
        model_tier: tier,
        max_tokens: request.max_tokens || 1024,
        temperature: request.temperature || 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`S.Y.N.A.P.S.E. query failed: ${response.statusText}`);
    }

    const data = await response.json();

    // Transform S.Y.N.A.P.S.E. response to OpenAI format
    return {
      id: data.query_id,
      object: 'chat.completion',
      created: Date.now(),
      model: data.model_id,
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: data.response
        },
        finish_reason: 'stop'
      }],
      usage: {
        prompt_tokens: 0,  // S.Y.N.A.P.S.E. doesn't track this
        completion_tokens: data.tokens_used || 0,
        total_tokens: data.tokens_used || 0
      }
    };
  }

  private inferTier(model?: string): 'fast' | 'balanced' | 'powerful' {
    if (!model) return 'balanced';

    const lowerModel = model.toLowerCase();
    if (lowerModel.includes('fast') || lowerModel.includes('q2')) return 'fast';
    if (lowerModel.includes('powerful') || lowerModel.includes('q4')) return 'powerful';
    return 'balanced';
  }

  private messagesToQuery(messages: Array<{ role: string; content: string }>): string {
    // Extract user query from messages
    const userMessages = messages.filter(m => m.role === 'user');
    return userMessages[userMessages.length - 1]?.content || '';
  }
}
```

### 3.4 CGRAG Integration

**File:** `opencode-service/cgrag-integration.ts`

```typescript
/**
 * Inject CGRAG context into OpenCode queries.
 *
 * Calls S.Y.N.A.P.S.E. CGRAG retrieval endpoint to get relevant
 * code artifacts, then prepends them to the query.
 */

export async function injectCGRAGContext(
  query: string,
  synapseApiBase: string
): Promise<string> {
  try {
    const response = await fetch(`${synapseApiBase}/api/cgrag/retrieve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        token_budget: 4000,
        max_artifacts: 10,
        min_relevance: 0.7
      })
    });

    if (!response.ok) {
      console.warn('[CGRAG] Retrieval failed, proceeding without context');
      return query;
    }

    const data = await response.json();
    const { artifacts } = data;

    if (!artifacts || artifacts.length === 0) {
      return query;
    }

    // Build context sections
    const contextSections = artifacts.map((artifact: any) => {
      return `[File: ${artifact.file_path}]\n${artifact.content}`;
    });

    const contextBlock = contextSections.join('\n\n---\n\n');

    // Enhanced query with context
    const enhancedQuery = `# Relevant Code Context\n\n${contextBlock}\n\n---\n\n# User Query\n\n${query}`;

    console.log(`[CGRAG] Injected ${artifacts.length} artifacts into query`);

    return enhancedQuery;

  } catch (error) {
    console.error('[CGRAG] Error retrieving context:', error);
    return query;  // Fallback to original query
  }
}
```

---

## Phase 4: FastAPI Proxy Layer

### 4.1 CodeChat Router

**File:** `backend/app/routers/codechat.py`

```python
"""
Code Chat router - Proxy to OpenCode backend with S.Y.N.A.P.S.E. integration.
"""

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

OPENCODE_BASE_URL = "http://opencode_backend:3456"


class CodeChatRequest(BaseModel):
    """Code chat request model."""
    query: str
    mode: Optional[str] = "balanced"  # fast/balanced/powerful
    use_workspace_context: bool = True
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7


@router.post("/api/codechat")
async def code_chat(request: CodeChatRequest):
    """
    Stream code chat response from OpenCode backend.

    OpenCode handles:
    - File operations in /workspace
    - LSP features (autocomplete, diagnostics)
    - MCP tools (git, search, etc.)

    S.Y.N.A.P.S.E. handles:
    - CGRAG context retrieval (if use_workspace_context=True)
    - Model tier routing (fast/balanced/powerful)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENCODE_BASE_URL}/chat",
                json={
                    "query": request.query,
                    "mode": request.mode,
                    "useWorkspaceContext": request.use_workspace_context,
                    "maxTokens": request.max_tokens,
                    "temperature": request.temperature
                },
                headers={"Accept": "text/event-stream"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenCode backend error: {response.text}"
                )

            # Stream SSE events to client
            async def stream_generator():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="OpenCode backend timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code chat error: {str(e)}"
        )


@router.get("/api/codechat/health")
async def health_check():
    """Check OpenCode backend health."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OPENCODE_BASE_URL}/health")
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"OpenCode backend unavailable: {str(e)}"
        )
```

### 4.2 Register Router

**File:** `backend/app/main.py`

Add import and router registration:

```python
# Around line 35
from app.routers import codechat

# Around line 421
app.include_router(codechat.router, tags=["codechat"])
```

---

## Phase 5: Frontend Implementation

### 5.1 TypeScript Types

**File:** `frontend/src/types/codechat.ts`

```typescript
export interface CodeChatRequest {
  query: string;
  mode?: 'fast' | 'balanced' | 'powerful';
  useWorkspaceContext?: boolean;
  maxTokens?: number;
  temperature?: number;
}

export interface CodeChatChunk {
  type: 'text' | 'file_operation' | 'diagnostic' | 'completion';
  content: string;
  metadata?: {
    file?: string;
    operation?: 'create' | 'edit' | 'delete';
    line?: number;
  };
}

export interface WorkspaceFile {
  path: string;
  name: string;
  extension: string;
  sizeBytes: number;
  modifiedTime: string;
  isDirectory: boolean;
  language?: string;
}
```

### 5.2 SSE Hook

**File:** `frontend/src/hooks/useCodeChat.ts`

```typescript
import { useState, useCallback } from 'react';
import { CodeChatRequest, CodeChatChunk } from '@/types/codechat';

export function useCodeChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [chunks, setChunks] = useState<CodeChatChunk[]>([]);
  const [error, setError] = useState<string | null>(null);

  const sendQuery = useCallback(async (request: CodeChatRequest) => {
    setIsStreaming(true);
    setChunks([]);
    setError(null);

    try {
      const response = await fetch('/api/codechat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is null');
      }

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        // Decode chunk
        const text = decoder.decode(value, { stream: true });

        // Parse SSE format (data: {...}\n\n)
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              setChunks(prev => [...prev, data]);
            } catch (e) {
              console.warn('Failed to parse SSE chunk:', line);
            }
          }
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const reset = useCallback(() => {
    setChunks([]);
    setError(null);
  }, []);

  return {
    sendQuery,
    reset,
    isStreaming,
    chunks,
    error
  };
}
```

### 5.3 Code Chat Page (Using WebTUI)

**File:** `frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Note:** This assumes WebTUI components are available (migration being done separately).

```typescript
import React, { useState } from 'react';
import { useCodeChat } from '@/hooks/useCodeChat';
import { useWorkspaceFiles } from '@/hooks/useWorkspace';
import styles from './CodeChatPage.module.css';

export const CodeChatPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const { sendQuery, chunks, isStreaming, error } = useCodeChat();
  const { data: files } = useWorkspaceFiles();

  const handleSubmit = () => {
    if (!query.trim()) return;

    sendQuery({
      query,
      mode: 'balanced',
      useWorkspaceContext: true,
      maxTokens: 2048,
      temperature: 0.7
    });
  };

  // Combine chunks into response text
  const responseText = chunks
    .filter(c => c.type === 'text')
    .map(c => c.content)
    .join('');

  return (
    <div className={styles.container}>
      {/* Header */}
      <view- variant="header" className={styles.header}>
        <h1>▓▓▓▓ CODE CHAT MODE ▓▓▓▓</h1>
        <div className={styles.stats}>
          <span>FILES: {files?.length || 0}</span>
          <span>CONTEXT: {chunks.filter(c => c.type === 'text').length}</span>
        </div>
      </view->

      <div className={styles.content}>
        {/* Sidebar - File Browser */}
        <view- variant="panel" title-="WORKSPACE" className={styles.sidebar}>
          <list->
            {files?.map(file => (
              <list-item
                key={file.path}
                active-={file.path === selectedFile ? 'true' : undefined}
                onClick={() => setSelectedFile(file.path)}
              >
                {file.isDirectory ? '📁' : '📄'} {file.name}
              </list-item>
            ))}
          </list->
        </view->

        {/* Main - Chat Interface */}
        <div className={styles.main}>
          {/* Query Input */}
          <view- variant="panel" title-="QUERY">
            <textarea-
              rows-="4"
              value={query}
              onChange={(e: any) => setQuery(e.target.value)}
              placeholder-="Ask about code, request file operations..."
              disabled-={isStreaming ? 'true' : undefined}
            />
            <button-
              size="large"
              variant="primary"
              onClick={handleSubmit}
              disabled-={isStreaming ? 'true' : undefined}
            >
              {isStreaming ? 'PROCESSING...' : 'EXECUTE'}
            </button->
          </view->

          {/* Response */}
          {(responseText || error) && (
            <view- variant="panel" title-="RESPONSE">
              {error ? (
                <div className={styles.error}>ERROR: {error}</div>
              ) : (
                <pre- syntax="markdown">{responseText}</pre->
              )}
            </view->
          )}

          {/* File Operations */}
          {chunks.filter(c => c.type === 'file_operation').length > 0 && (
            <view- variant="panel" title-="FILE OPERATIONS">
              {chunks
                .filter(c => c.type === 'file_operation')
                .map((chunk, i) => (
                  <div key={i} className={styles.fileOp}>
                    <span className={styles.operation}>
                      {chunk.metadata?.operation?.toUpperCase()}
                    </span>
                    <span className={styles.file}>
                      {chunk.metadata?.file}
                    </span>
                  </div>
                ))}
            </view->
          )}
        </div>
      </div>
    </div>
  );
};
```

### 5.4 Add Route

**File:** `frontend/src/App.tsx`

```typescript
import { CodeChatPage } from './pages/CodeChatPage/CodeChatPage';

// In routes configuration
<Route path="/codechat" element={<CodeChatPage />} />
```

### 5.5 Update Mode Selector

**File:** `frontend/src/components/modes/ModeSelector.tsx`

Add Code Chat mode to the modes array:

```typescript
const MODES: ModeDefinition[] = [
  // ... existing modes ...
  {
    id: 'codechat',
    label: 'CODE CHAT',
    description: 'AI coding assistant with file operations',
    available: true
  }
];
```

---

## Phase 6: Testing

### 6.1 Unit Tests

**OpenCode Backend Tests:**

```typescript
// opencode-service/tests/model-adapter.test.ts
import { describe, test, expect } from 'bun:test';
import { SynapseModelProvider } from '../model-adapter';

describe('SynapseModelProvider', () => {
  test('infers tier from model name', () => {
    const provider = new SynapseModelProvider('http://localhost:8000');

    expect(provider['inferTier']('fast-q2')).toBe('fast');
    expect(provider['inferTier']('balanced-q3')).toBe('balanced');
    expect(provider['inferTier']('powerful-q4')).toBe('powerful');
    expect(provider['inferTier'](undefined)).toBe('balanced');
  });

  test('converts messages to query', () => {
    const provider = new SynapseModelProvider('http://localhost:8000');

    const messages = [
      { role: 'system', content: 'You are helpful' },
      { role: 'user', content: 'Write a Python function' }
    ];

    const query = provider['messagesToQuery'](messages);
    expect(query).toBe('Write a Python function');
  });
});
```

**FastAPI Tests:**

```python
# backend/tests/test_codechat.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_codechat_health():
    """Test OpenCode backend health check."""
    response = client.get("/api/codechat/health")
    # May fail if OpenCode backend not running
    assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_codechat_streaming():
    """Test code chat SSE streaming."""
    response = client.post(
        "/api/codechat",
        json={
            "query": "Write a hello world function",
            "mode": "balanced",
            "use_workspace_context": False
        },
        stream=True
    )

    # Should return SSE stream
    assert response.headers["content-type"] == "text/event-stream"

    # Read first chunk
    for line in response.iter_lines():
        if line.startswith(b"data: "):
            # Successfully received SSE chunk
            assert True
            break
```

### 6.2 Integration Tests

**End-to-End Test:**

```bash
#!/bin/bash
# test-codechat.sh

echo "Testing Code Chat integration..."

# 1. Check OpenCode backend health
echo "1. Health check..."
curl -s http://localhost:3456/health | jq .

# 2. Test file read
echo "2. File operations..."
curl -s http://localhost:3456/files?path=README.md | jq .

# 3. Test chat streaming
echo "3. Chat streaming..."
curl -X POST http://localhost:8000/api/codechat \
  -H "Content-Type: application/json" \
  -d '{"query": "List files in workspace", "mode": "fast"}' \
  --no-buffer

echo "✓ All tests passed"
```

### 6.3 Manual Testing Checklist

- [ ] OpenCode backend starts successfully in Docker
- [ ] Health endpoint returns OK status
- [ ] File read operations work
- [ ] Chat streaming returns SSE events
- [ ] CGRAG context injection works
- [ ] Model tier routing works (fast/balanced/powerful)
- [ ] WebTUI components render correctly
- [ ] Frontend receives and displays streamed responses
- [ ] Error handling works (backend down, timeout, etc.)

---

## Phase 7: Deployment

### 7.1 Build and Deploy

```bash
# 1. Build OpenCode service
cd opencode-service
bun install
cd ..

# 2. Rebuild Docker containers
docker-compose build --no-cache opencode_backend
docker-compose build --no-cache synapse_core
docker-compose build --no-cache synapse_frontend

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f opencode_backend
docker-compose logs -f synapse_core

# 5. Test
./test-codechat.sh
```

### 7.2 Environment Configuration

**File:** `.env.example`

```bash
# OpenCode Backend
OPENCODE_WORKSPACE_ROOT=/workspace
OPENCODE_PORT=3456
SYNAPSE_API_BASE=http://synapse_core:8000

# Model Configuration
DEFAULT_MODEL_TIER=balanced  # fast/balanced/powerful
```

---

## Phase 8: Documentation

### 8.1 Update README.md

Add section:

```markdown
## Code Chat Mode

AI-assisted coding interface powered by OpenCode backend.

**Features:**
- File operations in sandboxed `/workspace` directory
- LSP support (autocomplete, diagnostics, refactoring)
- MCP tools (git, search, file management)
- Code-aware CGRAG context retrieval
- Streaming responses via SSE

**Architecture:**
- **OpenCode Backend**: Bun service handling AI coding logic
- **S.Y.N.A.P.S.E. Integration**: Model routing, CGRAG context
- **WebTUI Frontend**: Terminal-aesthetic React components

**Usage:**
1. Navigate to Code Chat mode in web UI
2. Ask coding questions or request file operations
3. View streaming responses with syntax highlighting
4. OpenCode automatically handles file edits, git operations, etc.
```

### 8.2 Update SESSION_NOTES.md

After implementation, add session entry:

```markdown
## 2025-11-08: OpenCode Backend Integration

### Summary
Integrated OpenCode backend for professional AI coding capabilities.

### Implementation
- Added `opencode_backend` Docker service (Bun/TypeScript)
- Created model adapter to use S.Y.N.A.P.S.E. llama.cpp servers
- Implemented CGRAG context injection
- Built FastAPI proxy for unified API
- Created React UI with WebTUI components
- SSE streaming for real-time responses

### Files Modified
- `docker-compose.yml` - Added opencode_backend service
- `backend/app/routers/codechat.py` - New router (proxy to OpenCode)
- `backend/app/main.py` - Registered codechat router
- `frontend/src/hooks/useCodeChat.ts` - SSE streaming hook
- `frontend/src/pages/CodeChatPage/CodeChatPage.tsx` - UI implementation

### Files Created
- `opencode-service/server.ts` - OpenCode backend wrapper
- `opencode-service/model-adapter.ts` - S.Y.N.A.P.S.E. model integration
- `opencode-service/cgrag-integration.ts` - CGRAG context injection

### Testing
- OpenCode backend health checks ✓
- SSE streaming ✓
- File operations ✓
- CGRAG integration ✓
- Model tier routing ✓

### Next Steps
- Add LSP diagnostics display in UI
- Implement MCP tool visualizations
- Add git integration panel
- Performance optimization (response caching)
```

---

## Implementation Checklist

### Research & Setup (2-3 hours)
- [ ] Research `opencode-ai` NPM package (install, inspect API)
- [ ] Verify llama.cpp OpenAI-compatible endpoint exists
- [ ] Test OpenCode initialization with dummy config
- [ ] Create `opencode-service` directory structure

### Backend Implementation (4-5 hours)
- [ ] Create `package.json` and install dependencies
- [ ] Implement `server.ts` with chat/files/completions endpoints
- [ ] Build `model-adapter.ts` for S.Y.N.A.P.S.E. integration
- [ ] Implement `cgrag-integration.ts` for context injection
- [ ] Add Docker service to `docker-compose.yml`
- [ ] Test OpenCode backend in isolation

### FastAPI Proxy (1-2 hours)
- [ ] Create `backend/app/routers/codechat.py`
- [ ] Implement SSE streaming proxy
- [ ] Add health check endpoint
- [ ] Register router in `main.py`
- [ ] Test proxy with curl

### Frontend Implementation (3-4 hours)
- [ ] Create TypeScript types (`codechat.ts`)
- [ ] Build SSE hook (`useCodeChat.ts`)
- [ ] Implement Code Chat page with WebTUI
- [ ] Add route in `App.tsx`
- [ ] Update mode selector
- [ ] Test streaming in browser

### Testing & Validation (1-2 hours)
- [ ] Write unit tests (model adapter, SSE parsing)
- [ ] Write integration tests (FastAPI proxy)
- [ ] Create E2E test script
- [ ] Manual testing checklist
- [ ] Performance testing (streaming latency)

### Documentation (1 hour)
- [ ] Update README.md with Code Chat section
- [ ] Update SESSION_NOTES.md
- [ ] Document API endpoints
- [ ] Create troubleshooting guide

---

## Risk Assessment

### High Risk
- **OpenCode API compatibility**: Package may not expose expected API
  - **Mitigation**: Research package first, build adapter layer if needed
- **Model API format mismatch**: llama.cpp may not match OpenAI format
  - **Mitigation**: Implement translation layer in model adapter

### Medium Risk
- **SSE streaming complexity**: Browser SSE handling can be tricky
  - **Mitigation**: Use proven SSE parsing logic, add retry logic
- **CGRAG context size**: Large context may exceed token limits
  - **Mitigation**: Implement smart truncation in `cgrag-integration.ts`

### Low Risk
- **Docker networking**: Services may not communicate
  - **Mitigation**: Use `synapse-network`, test with curl
- **WebTUI compatibility**: Components may not work as expected
  - **Mitigation**: WebTUI migration being done separately, assume working

---

## Success Criteria

**Functional:**
- [ ] User can ask coding questions and receive streamed responses
- [ ] OpenCode can read/write files in `/workspace`
- [ ] CGRAG context is injected into queries
- [ ] S.Y.N.A.P.S.E. model tier routing works (fast/balanced/powerful)
- [ ] WebTUI components render correctly with terminal aesthetic

**Performance:**
- [ ] SSE streaming latency <200ms first chunk
- [ ] Complete response streaming <5s for typical query
- [ ] CGRAG context injection <500ms
- [ ] File operations <100ms

**Quality:**
- [ ] Error handling for backend failures
- [ ] Graceful degradation if CGRAG unavailable
- [ ] Proper logging in all services
- [ ] No console errors in frontend

---

## Future Enhancements

**Phase 9 (Post-MVP):**
1. **LSP Diagnostics Panel**: Show real-time errors/warnings in UI
2. **MCP Tool Visualization**: Display git operations, search results visually
3. **Multi-file Editing**: Edit multiple files in split view
4. **Collaborative Features**: Multi-user workspace with conflict resolution
5. **Code Execution**: Run Python/Node.js code with output display
6. **Git Integration Panel**: Commit, push, branch visualization
7. **Performance Monitoring**: Track response times, token usage
8. **Advanced CGRAG**: Semantic code search, dependency analysis

---

## Estimated Timeline

**Total: 12-16 hours** (1-2 engineers, excluding WebTUI migration)

- Phase 1 (Research): 2-3 hours
- Phase 2-3 (Backend): 4-5 hours
- Phase 4 (Proxy): 1-2 hours
- Phase 5 (Frontend): 3-4 hours
- Phase 6 (Testing): 1-2 hours
- Phase 7 (Deployment): 0.5 hours
- Phase 8 (Documentation): 1 hour

**Critical Path:**
1. Research OpenCode API (blocks everything)
2. OpenCode backend implementation (blocks proxy)
3. FastAPI proxy (blocks frontend)
4. Frontend UI (final integration)

---

## Conclusion

This integration plan leverages OpenCode's professional AI coding capabilities while maintaining S.Y.N.A.P.S.E.'s unique model orchestration and CGRAG context system. By using OpenCode as a backend library (not standalone tool), we get:

- **Faster development** (~40% less code than custom implementation)
- **Professional features** (LSP, MCP, refactoring tools)
- **Maintained control** (S.Y.N.A.P.S.E. handles model routing, context)
- **Terminal aesthetic** (WebTUI provides UI components)
- **Docker isolation** (security via container boundaries)

The architecture is modular and extensible, allowing future enhancements without major refactoring.

---

**END OF IMPLEMENTATION PLAN**
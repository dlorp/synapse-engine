/**
 * Tests for useCodeChat hook.
 *
 * Covers:
 * - Hook initialization
 * - SSE stream handling
 * - Event parsing and state updates
 * - Step accumulation
 * - Cancellation
 * - Error handling
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useCodeChat } from '../useCodeChat';
import type { CodeChatStreamEvent } from '@/types/codeChat';

describe('useCodeChat', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let mockAbortController: { abort: ReturnType<typeof vi.fn>; signal: AbortSignal };

  beforeEach(() => {
    // Mock AbortController
    mockAbortController = {
      abort: vi.fn(),
      signal: new AbortController().signal,
    };
    global.AbortController = vi.fn(() => mockAbortController) as any;

    // Mock fetch
    mockFetch = vi.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('initialization', () => {
    test('initializes with correct default state', () => {
      const { result } = renderHook(() => useCodeChat());

      expect(result.current.steps).toEqual([]);
      expect(result.current.currentState).toBe('idle');
      expect(result.current.answer).toBe(null);
      expect(result.current.error).toBe(null);
      expect(result.current.context).toBe(null);
      expect(result.current.isLoading).toBe(false);
    });

    test('provides submit, cancel, and reset methods', () => {
      const { result } = renderHook(() => useCodeChat());

      expect(typeof result.current.submit).toBe('function');
      expect(typeof result.current.cancel).toBe('function');
      expect(typeof result.current.reset).toBe('function');
    });
  });

  describe('submit', () => {
    test('sends POST request with correct payload', async () => {
      // Mock successful empty response
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      };
      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      const request = {
        query: 'Add logging to main.py',
        workspacePath: '/home/user/project',
        contextName: 'project_docs',
        preset: 'coding',
      };

      await result.current.submit(request);

      expect(mockFetch).toHaveBeenCalledWith('/api/code-chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: mockAbortController.signal,
      });
    });

    test('completes submission and clears loading state', async () => {
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      };
      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      // After submission completes, loading should be false
      expect(result.current.isLoading).toBe(false);
    });

    test('resets state before new submission', async () => {
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      };
      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      // Set some state manually
      result.current.submit({
        query: 'first query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Submit again and verify reset
      await result.current.submit({
        query: 'second query',
        workspacePath: '/test',
      });

      expect(result.current.steps).toEqual([]);
      expect(result.current.answer).toBe(null);
      expect(result.current.error).toBe(null);
      expect(result.current.context).toBe(null);
    });

    test('handles HTTP error response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.error).toBe('HTTP 500: Internal Server Error');
        expect(result.current.currentState).toBe('error');
        expect(result.current.isLoading).toBe(false);
      });
    });

    test('handles missing response body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: null,
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.error).toBe('No response body');
        expect(result.current.currentState).toBe('error');
      });
    });

    test('handles network error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
        expect(result.current.currentState).toBe('error');
      });
    });
  });

  describe('SSE event handling', () => {
    test('handles thought event', async () => {
      const thoughtEvent: CodeChatStreamEvent = {
        type: 'thought',
        content: 'I need to read the file first',
        stepNumber: 1,
        tier: 'balanced',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(thoughtEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Thought doesn't create complete step yet
      expect(result.current.steps).toHaveLength(0);
    });

    test('handles complete thought-action-observation cycle', async () => {
      const events: CodeChatStreamEvent[] = [
        {
          type: 'thought',
          content: 'I need to read the file',
          stepNumber: 1,
          tier: 'balanced',
          timestamp: '2025-11-29T12:00:00Z',
        },
        {
          type: 'action',
          tool: { tool: 'read_file', args: { path: '/test/main.py' } },
          stepNumber: 1,
          timestamp: '2025-11-29T12:00:01Z',
        },
        {
          type: 'observation',
          content: 'File contents: print("hello")',
          stepNumber: 1,
          timestamp: '2025-11-29T12:00:02Z',
        },
      ];

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(
              events.map((e) => `data: ${JSON.stringify(e)}\n`).join('\n') + '\n'
            ),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.steps).toHaveLength(1);
      });

      const step = result.current.steps[0];
      expect(step.stepNumber).toBe(1);
      expect(step.thought).toBe('I need to read the file');
      expect(step.action).toEqual({ tool: 'read_file', args: { path: '/test/main.py' } });
      expect(step.observation).toBe('File contents: print("hello")');
      expect(step.state).toBe('observing');
    });

    test('handles answer event', async () => {
      const answerEvent: CodeChatStreamEvent = {
        type: 'answer',
        content: 'I have added logging to main.py',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(answerEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.answer).toBe('I have added logging to main.py');
        expect(result.current.currentState).toBe('completed');
        expect(result.current.isLoading).toBe(false);
      });
    });

    test('handles error event', async () => {
      const errorEvent: CodeChatStreamEvent = {
        type: 'error',
        content: 'File not found: /test/main.py',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(errorEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.error).toBe('File not found: /test/main.py');
        expect(result.current.currentState).toBe('error');
        expect(result.current.isLoading).toBe(false);
      });
    });

    test('handles context event', async () => {
      const contextEvent: CodeChatStreamEvent = {
        type: 'context',
        content: 'Retrieved 5 relevant code snippets',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(contextEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.context).toBe('Retrieved 5 relevant code snippets');
      });
    });

    test('handles state change event', async () => {
      const stateEvent: CodeChatStreamEvent = {
        type: 'state',
        state: 'executing',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(stateEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.currentState).toBe('executing');
      });
    });

    test('handles multiple steps in sequence', async () => {
      const events: CodeChatStreamEvent[] = [
        // Step 1
        {
          type: 'thought',
          content: 'Read file',
          stepNumber: 1,
          tier: 'balanced',
          timestamp: '2025-11-29T12:00:00Z',
        },
        {
          type: 'action',
          tool: { tool: 'read_file', args: { path: '/test/main.py' } },
          stepNumber: 1,
          timestamp: '2025-11-29T12:00:01Z',
        },
        {
          type: 'observation',
          content: 'File read successfully',
          stepNumber: 1,
          timestamp: '2025-11-29T12:00:02Z',
        },
        // Step 2
        {
          type: 'thought',
          content: 'Write file',
          stepNumber: 2,
          tier: 'balanced',
          timestamp: '2025-11-29T12:00:03Z',
        },
        {
          type: 'action',
          tool: { tool: 'write_file', args: { path: '/test/main.py', content: 'new content' } },
          stepNumber: 2,
          timestamp: '2025-11-29T12:00:04Z',
        },
        {
          type: 'observation',
          content: 'File written successfully',
          stepNumber: 2,
          timestamp: '2025-11-29T12:00:05Z',
        },
      ];

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(
              events.map((e) => `data: ${JSON.stringify(e)}\n`).join('\n') + '\n'
            ),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.steps).toHaveLength(2);
      });

      expect(result.current.steps[0].stepNumber).toBe(1);
      expect(result.current.steps[0].thought).toBe('Read file');
      expect(result.current.steps[1].stepNumber).toBe(2);
      expect(result.current.steps[1].thought).toBe('Write file');
    });

    test('handles malformed SSE event gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('data: {invalid json}\n\n'),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should not crash, just log error
      expect(consoleErrorSpy).toHaveBeenCalled();
      expect(result.current.error).toBe(null); // Malformed events don't set error state

      consoleErrorSpy.mockRestore();
    });
  });

  describe('cancel', () => {
    test('aborts fetch request', async () => {
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: false, value: undefined }), // Never completes
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      // Start submission
      result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      // Cancel immediately
      result.current.cancel();

      expect(mockAbortController.abort).toHaveBeenCalled();
      expect(result.current.currentState).toBe('cancelled');
      expect(result.current.isLoading).toBe(false);
    });

    test('calls cancel endpoint when session exists', async () => {
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Clear mock to track cancel call
      mockFetch.mockClear();

      result.current.cancel();

      // Should call cancel endpoint
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/code-chat/cancel/test-session-123', {
          method: 'POST',
        });
      });
    });

    test('handles cancellation without session gracefully', () => {
      const { result } = renderHook(() => useCodeChat());

      // Cancel without starting query
      result.current.cancel();

      expect(result.current.currentState).toBe('cancelled');
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('reset', () => {
    test('clears all state', async () => {
      // Set up some state first
      const answerEvent: CodeChatStreamEvent = {
        type: 'answer',
        content: 'Test answer',
        timestamp: '2025-11-29T12:00:00Z',
      };

      const mockReader = {
        read: vi
          .fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify(answerEvent)}\n\n`),
          })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      };

      mockFetch.mockResolvedValue({
        ok: true,
        headers: new Map([['X-Session-ID', 'test-session-123']]),
        body: { getReader: () => mockReader },
      });

      const { result } = renderHook(() => useCodeChat());

      await result.current.submit({
        query: 'test query',
        workspacePath: '/test',
      });

      await waitFor(() => {
        expect(result.current.answer).toBe('Test answer');
      });

      // Now reset
      result.current.reset();

      expect(result.current.steps).toEqual([]);
      expect(result.current.currentState).toBe('idle');
      expect(result.current.answer).toBe(null);
      expect(result.current.error).toBe(null);
      expect(result.current.context).toBe(null);
      expect(result.current.isLoading).toBe(false);
    });
  });
});

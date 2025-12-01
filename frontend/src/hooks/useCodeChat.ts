/**
 * React hook for Code Chat SSE streaming.
 *
 * Handles:
 * - SSE connection to /api/code-chat/query
 * - Event parsing and state updates
 * - ReAct step accumulation
 * - Cancellation support
 * - Error handling
 *
 * The hook manages the complete lifecycle of a Code Chat query including
 * real-time updates from the ReAct agent as it plans, executes tools, and
 * generates the final response.
 */

import { useState, useCallback, useRef } from 'react';
import type {
  CodeChatRequest,
  CodeChatStreamEvent,
  ReActStep,
  AgentState,
} from '@/types/codeChat';

/**
 * Pending action awaiting user confirmation.
 */
interface PendingAction {
  /** Action identifier */
  actionId: string;
  /** Tool call details */
  toolCall: CodeChatStreamEvent['tool'];
  /** Diff preview data (for write_file) */
  diffPreview?: Record<string, unknown>;
  /** Step number */
  stepNumber?: number;
}

/**
 * Return type for useCodeChat hook.
 */
interface UseCodeChatResult {
  /** Accumulated ReAct steps */
  steps: ReActStep[];
  /** Current agent state */
  currentState: AgentState;
  /** Final answer (when completed) */
  answer: string | null;
  /** Error message (when error state) */
  error: string | null;
  /** Whether query is in progress */
  isLoading: boolean;
  /** CGRAG context retrieved */
  context: string | null;
  /** Pending action awaiting confirmation */
  pendingAction: PendingAction | null;
  /** Submit a new query */
  submit: (request: CodeChatRequest) => Promise<void>;
  /** Cancel current query */
  cancel: () => void;
  /** Reset state for new query */
  reset: () => void;
  /** Approve pending action */
  approveAction: (actionId: string) => Promise<void>;
  /** Reject pending action */
  rejectAction: (actionId: string) => Promise<void>;
}

/**
 * Hook for Code Chat query execution with SSE streaming.
 *
 * Manages the complete query lifecycle:
 * 1. Submit query to /api/code-chat/query endpoint
 * 2. Receive SSE events (thought, action, observation, answer, etc.)
 * 3. Build ReActStep objects incrementally from events
 * 4. Handle cancellation, errors, and completion
 *
 * The hook uses refs to track the current step being built and the
 * abort controller for cancellation.
 *
 * @returns Object with state and control methods
 *
 * @example
 * const codeChat = useCodeChat();
 *
 * // Submit query
 * codeChat.submit({
 *   query: 'Add logging to main.py',
 *   workspacePath: '/home/user/project',
 *   contextName: 'project_docs',
 *   preset: 'coding'
 * });
 *
 * // Monitor progress
 * console.log(codeChat.currentState); // 'planning' | 'executing' | etc.
 * console.log(codeChat.steps); // Array of completed ReActStep objects
 *
 * // Cancel if needed
 * codeChat.cancel();
 *
 * // Reset for new query
 * codeChat.reset();
 */
export function useCodeChat(): UseCodeChatResult {
  // State
  const [steps, setSteps] = useState<ReActStep[]>([]);
  const [currentState, setCurrentState] = useState<AgentState>('idle');
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  // Refs for managing SSE stream and step building
  const abortControllerRef = useRef<AbortController | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const currentStepRef = useRef<Partial<ReActStep>>({});

  /**
   * Handle incoming SSE event.
   *
   * Events are processed to build ReActStep objects incrementally:
   * - thought: Starts new step
   * - action: Adds action to current step
   * - observation: Completes step and adds to steps array
   * - answer: Sets final answer and completes execution
   * - error/cancelled: Sets error state or cancellation
   * - context: Sets CGRAG context retrieved
   */
  const handleEvent = useCallback((event: CodeChatStreamEvent) => {
    switch (event.type) {
      case 'state':
        if (event.state) {
          setCurrentState(event.state);
        }
        break;

      case 'thought':
        // Start new step
        currentStepRef.current = {
          stepNumber: event.stepNumber || steps.length + 1,
          thought: event.content || '',
          state: 'planning',
          modelTier: event.tier || 'balanced',
          timestamp: event.timestamp,
        };
        break;

      case 'action':
        // Add action to current step
        if (event.tool) {
          currentStepRef.current.action = event.tool;
          currentStepRef.current.state = 'executing';
        }
        break;

      case 'observation':
        // Complete step and add to list
        if (currentStepRef.current.stepNumber) {
          const completedStep: ReActStep = {
            stepNumber: currentStepRef.current.stepNumber,
            thought: currentStepRef.current.thought || '',
            action: currentStepRef.current.action,
            observation: event.content,
            state: 'observing',
            modelTier: currentStepRef.current.modelTier || 'balanced',
            timestamp: currentStepRef.current.timestamp || event.timestamp,
          };
          setSteps((prev) => [...prev, completedStep]);
          currentStepRef.current = {};
        }
        break;

      case 'context':
        setContext(event.content || null);
        break;

      case 'answer':
        setAnswer(event.content || null);
        setCurrentState('completed');
        setIsLoading(false);
        break;

      case 'error':
        setError(event.content || 'Unknown error');
        setCurrentState('error');
        setIsLoading(false);
        break;

      case 'cancelled':
        setCurrentState('cancelled');
        setIsLoading(false);
        break;

      case 'action_pending':
        // Store pending action for user confirmation
        if (event.data && event.data.action_id) {
          setPendingAction({
            actionId: event.data.action_id as string,
            toolCall: event.tool,
            diffPreview: event.data.diff_preview as Record<string, unknown> | undefined,
            stepNumber: event.stepNumber,
          });
        }
        break;

      case 'diff_preview':
        // Diff preview events are informational and don't affect step state
        // They can be handled by parent components listening to events
        break;
    }
  }, [steps.length]);

  /**
   * Submit a new Code Chat query.
   *
   * Resets state, creates SSE connection, and processes events as they arrive.
   * Uses fetch API with ReadableStream to handle SSE format.
   *
   * @param request - CodeChatRequest with query and configuration
   */
  const submit = useCallback(async (request: CodeChatRequest) => {
    // Reset state
    setSteps([]);
    setAnswer(null);
    setError(null);
    setContext(null);
    setCurrentState('planning');
    setIsLoading(true);
    currentStepRef.current = {};

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/code-chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Get session ID from header
      sessionIdRef.current = response.headers.get('X-Session-ID');

      // Read SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      // Read stream until done
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = line.slice(6); // Remove 'data: ' prefix
              const event: CodeChatStreamEvent = JSON.parse(eventData);
              handleEvent(event);
            } catch (e) {
              console.error('Failed to parse SSE event:', e, 'Line:', line);
            }
          }
        }
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was cancelled
        setCurrentState('cancelled');
      } else {
        // Other error
        setError(err instanceof Error ? err.message : 'Unknown error');
        setCurrentState('error');
      }
    } finally {
      setIsLoading(false);
    }
  }, [handleEvent]);

  /**
   * Cancel the current query.
   *
   * Aborts the fetch request and calls the cancel endpoint to notify
   * the backend. The backend will set a cancellation flag that is
   * checked on each iteration of the ReAct loop.
   */
  const cancel = useCallback(() => {
    // Abort fetch
    abortControllerRef.current?.abort();

    // Also call cancel endpoint if we have a session
    if (sessionIdRef.current) {
      fetch(`/api/code-chat/cancel/${sessionIdRef.current}`, { method: 'POST' })
        .catch(console.error);
    }

    setCurrentState('cancelled');
    setIsLoading(false);
  }, []);

  /**
   * Reset all state for a new query.
   *
   * Clears steps, answer, error, and context. Sets state to idle.
   */
  const reset = useCallback(() => {
    setSteps([]);
    setAnswer(null);
    setError(null);
    setContext(null);
    setCurrentState('idle');
    setIsLoading(false);
    setPendingAction(null);
    currentStepRef.current = {};
    sessionIdRef.current = null;
  }, []);

  /**
   * Approve a pending action.
   *
   * Calls the backend confirmation endpoint with approved=true.
   * The agent will execute the action and continue processing.
   *
   * @param actionId - Action identifier to approve
   */
  const approveAction = useCallback(async (actionId: string) => {
    try {
      await fetch(`/api/code-chat/confirm-action?action_id=${encodeURIComponent(actionId)}&approved=true`, {
        method: 'POST',
      });
      // Clear pending action
      setPendingAction(null);
    } catch (err) {
      console.error('Failed to approve action:', err);
      setError(err instanceof Error ? err.message : 'Failed to approve action');
    }
  }, []);

  /**
   * Reject a pending action.
   *
   * Calls the backend confirmation endpoint with approved=false.
   * The agent will skip the action and continue processing.
   *
   * @param actionId - Action identifier to reject
   */
  const rejectAction = useCallback(async (actionId: string) => {
    try {
      await fetch(`/api/code-chat/confirm-action?action_id=${encodeURIComponent(actionId)}&approved=false`, {
        method: 'POST',
      });
      // Clear pending action
      setPendingAction(null);
    } catch (err) {
      console.error('Failed to reject action:', err);
      setError(err instanceof Error ? err.message : 'Failed to reject action');
    }
  }, []);

  return {
    steps,
    currentState,
    answer,
    error,
    context,
    isLoading,
    pendingAction,
    submit,
    cancel,
    reset,
    approveAction,
    rejectAction,
  };
}

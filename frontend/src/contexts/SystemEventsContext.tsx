import React, { createContext, useContext, ReactNode } from 'react';
import { useSystemEvents, SystemEvent } from '../hooks/useSystemEvents';

/**
 * WebSocket connection states
 */
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

/**
 * System Events Context Interface
 */
interface SystemEventsContextType {
  events: SystemEvent[];
  connected: boolean;
  connectionState: ConnectionState;
  error: Error | null;
  reconnect: () => void;
  ensureConnected: () => void;
}

/**
 * Context for system event stream
 */
const SystemEventsContext = createContext<SystemEventsContextType | undefined>(undefined);

/**
 * Provider component for system events
 *
 * Wraps the useSystemEvents hook and provides global access to:
 * - Event stream data
 * - Connection state
 * - Manual reconnect function
 * - ensureConnected() - auto-reconnects if disconnected
 *
 * Usage:
 * ```tsx
 * <SystemEventsProvider>
 *   <App />
 * </SystemEventsProvider>
 * ```
 */
export const SystemEventsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { events, connected, connectionState, error, reconnect } = useSystemEvents();

  /**
   * Ensure connection is active
   *
   * Call this before/after user actions that will generate events:
   * - Sending queries
   * - Starting/stopping models
   * - Configuration changes
   *
   * Only reconnects if currently disconnected
   */
  const ensureConnected = () => {
    if (connectionState === 'disconnected') {
      console.log('[SystemEventsContext] Auto-reconnecting for user action');
      reconnect();
    }
  };

  return (
    <SystemEventsContext.Provider
      value={{
        events,
        connected,
        connectionState,
        error,
        reconnect,
        ensureConnected,
      }}
    >
      {children}
    </SystemEventsContext.Provider>
  );
};

/**
 * Hook to access system events context
 *
 * @throws Error if used outside SystemEventsProvider
 * @returns System events context
 *
 * @example
 * ```tsx
 * const { events, ensureConnected } = useSystemEventsContext();
 *
 * const handleSubmitQuery = async () => {
 *   await submitQuery();
 *   ensureConnected(); // Auto-reconnect to see events
 * };
 * ```
 */
export const useSystemEventsContext = (): SystemEventsContextType => {
  const context = useContext(SystemEventsContext);
  if (!context) {
    throw new Error('useSystemEventsContext must be used within SystemEventsProvider');
  }
  return context;
};

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastContainer } from 'react-toastify';
import { SystemEventsProvider } from './contexts/SystemEventsContext';
import { router } from './router/routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * ErrorBoundary - Catches React rendering errors and displays terminal-styled error screen
 * Prevents blank pages by showing error details with stack traces
 */
class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('⚠️ React Error Boundary caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            background: '#000',
            color: '#ff9500',
            padding: '40px',
            fontFamily: '"JetBrains Mono", monospace',
            minHeight: '100vh',
          }}
        >
          <h1 style={{ color: '#ff0000', marginBottom: '20px' }}>
            ⚠️ SYSTEM ERROR - REACT CRASH
          </h1>
          <div style={{ marginBottom: '20px' }}>
            <strong>Error:</strong> {this.state.error?.message}
          </div>
          <pre
            style={{
              background: '#1a1a1a',
              padding: '20px',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px',
              color: '#00ffff',
            }}
          >
            {this.state.error?.stack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: '#ff9500',
              color: '#000',
              border: 'none',
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: 'pointer',
              marginTop: '20px',
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            RELOAD SYSTEM
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <SystemEventsProvider>
        <ErrorBoundary>
          <RouterProvider router={router} />

          {/* Toast Notification Container - Terminal Aesthetic */}
          <ToastContainer
            position="bottom-right"
            autoClose={2000}
            hideProgressBar={false}
            newestOnTop={true}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="dark"
          />
        </ErrorBoundary>
      </SystemEventsProvider>
    </QueryClientProvider>
  );
};

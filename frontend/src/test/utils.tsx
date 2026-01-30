/**
 * Test utilities for React components and hooks.
 *
 * Provides wrappers with TanStack Query setup for testing hooks.
 */

import { ReactElement, ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

/**
 * Create a new QueryClient for testing with sensible defaults.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        gcTime: Infinity, // Keep data in cache
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Wrapper for testing components that use TanStack Query.
 */
interface WrapperProps {
  children: ReactNode;
}

export function createQueryWrapper(queryClient?: QueryClient) {
  const client = queryClient || createTestQueryClient();

  return function Wrapper({ children }: WrapperProps) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

/**
 * Custom render function that wraps with QueryClientProvider.
 */
export function renderWithQuery(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient, ...renderOptions } = options || {};
  const wrapper = createQueryWrapper(queryClient);

  return render(ui, { wrapper, ...renderOptions });
}

/**
 * Wait for a specific time in tests.
 */
export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

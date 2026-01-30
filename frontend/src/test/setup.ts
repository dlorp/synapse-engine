/**
 * Vitest test setup file.
 *
 * Configures test environment and global mocks.
 */

import { vi } from 'vitest';

// Mock fetch globally
(globalThis as any).fetch = vi.fn();

// Mock WebSocket globally
(globalThis as any).WebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1,
})) as any;

// Mock import.meta.env
vi.stubGlobal('import.meta', {
  env: {
    VITE_API_BASE_URL: '/api',
    VITE_WS_URL: '/ws',
  },
});

/**
 * CORE:INTERFACE Logging Utility
 *
 * Provides structured console logging with `ifc:` service tags per SYSTEM_IDENTITY.md
 *
 * Usage:
 *   import log from '@/utils/logger';
 *   log.info('WebSocket connected');
 *   log.error('API request failed', error);
 */

const log = {
  info: (message: string, ...args: any[]) => {
    console.log(`[ifc:] ${message}`, ...args);
  },
  error: (message: string, ...args: any[]) => {
    console.error(`[ifc:] ${message}`, ...args);
  },
  debug: (message: string, ...args: any[]) => {
    if (import.meta.env.DEV) {
      console.debug(`[ifc:] ${message}`, ...args);
    }
  },
  warn: (message: string, ...args: any[]) => {
    console.warn(`[ifc:] ${message}`, ...args);
  }
};

export default log;

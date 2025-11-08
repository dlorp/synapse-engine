/**
 * Tier-specific timeout configuration for query execution
 *
 * Timeouts account for:
 * - Backend processing time
 * - Automatic retry attempts
 * - Network overhead
 */

export type ModelTier = 'Q2' | 'Q3' | 'Q4';
export type QueryMode = 'two-stage' | 'simple' | 'council' | 'debate' | 'chat';

/**
 * Tier-specific timeout configuration (in milliseconds)
 *
 * Backend timeouts:
 * - Q2: 30s base + retries = 45s total
 * - Q3: 45s base + retries = 90s total
 * - Q4: 120s base + retries = 180s total
 */
export const TIER_TIMEOUTS: Record<ModelTier, number> = {
  Q2: 45000,   // 45 seconds for simple queries
  Q3: 90000,   // 90 seconds for moderate queries
  Q4: 180000,  // 180 seconds for complex/deep analysis
};

/**
 * Map query mode to expected timeout (in milliseconds)
 *
 * Note: These timeouts are estimates for multi-model orchestration modes
 */
export const MODE_TIMEOUTS: Record<QueryMode, number> = {
  'two-stage': 90000,  // Two-stage: Q2 + Q4 = ~90s
  'simple': 45000,     // Single Q2 model = ~45s
  'council': 120000,   // Multiple models discussing = ~120s
  'debate': 150000,    // Extended multi-model debate = ~150s
  'chat': 180000,      // Multi-turn conversation = ~180s
};

/**
 * Map query mode to expected tier for timeout calculation (deprecated, use MODE_TIMEOUTS)
 */
export const MODE_TO_TIER: Record<QueryMode, ModelTier> = {
  'two-stage': 'Q3',  // Default to middle tier
  'simple': 'Q2',     // Fast tier
  'council': 'Q4',    // Complex multi-model tier
  'debate': 'Q4',     // Complex multi-model tier
  'chat': 'Q4',       // Complex multi-model tier
};

/**
 * Get appropriate timeout for a query based on mode
 *
 * @param mode - Query execution mode
 * @returns Timeout in milliseconds
 *
 * @example
 * const timeout = getQueryTimeout('simple'); // 45000
 * const timeout = getQueryTimeout('two-stage'); // 90000
 */
export const getQueryTimeout = (mode: QueryMode = 'two-stage'): number => {
  return MODE_TIMEOUTS[mode];
};

/**
 * Get timeout from actual tier (from response metadata)
 *
 * @param tier - Model tier from response
 * @returns Timeout in milliseconds
 *
 * @example
 * const timeout = getTimeoutForTier('Q4'); // 180000
 */
export const getTimeoutForTier = (tier: ModelTier): number => {
  return TIER_TIMEOUTS[tier];
};

/**
 * Get human-readable timeout string for UI display
 *
 * @param mode - Query execution mode
 * @returns Formatted timeout string (e.g., "45s", "90s")
 *
 * @example
 * const display = getTimeoutDisplay('simple'); // "45s"
 */
export const getTimeoutDisplay = (mode: QueryMode = 'two-stage'): string => {
  const timeoutMs = getQueryTimeout(mode);
  const timeoutSeconds = Math.floor(timeoutMs / 1000);
  return `${timeoutSeconds}s`;
};

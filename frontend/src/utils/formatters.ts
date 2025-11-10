/**
 * Utility functions for formatting metrics and numbers
 * Used across the application for consistent display of resource metrics
 */

/**
 * Format bytes to human-readable format (KB/MB/GB/TB)
 * Uses base-1024 (binary) for consistency with system tools
 *
 * @param bytes - Number of bytes to format
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted string with unit (e.g., "128.5 MB")
 */
export function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);

  return `${value.toFixed(dm)} ${sizes[i]}`;
}

/**
 * Format percentage with consistent decimal places
 *
 * @param value - Percentage value (0-100)
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "45.2%")
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Get color code based on percentage threshold
 * Uses traffic light color scheme:
 * - Green: 0-70% (healthy)
 * - Amber: 70-90% (warning)
 * - Red: >90% (critical)
 *
 * @param percent - Percentage value (0-100)
 * @returns CSS color string
 */
export function getPercentColor(percent: number): string {
  if (percent < 70) return '#00ff00';  // Green - healthy
  if (percent < 90) return '#ff9500';  // Amber - warning
  return '#ff0000';                     // Red - critical
}

/**
 * Format throughput rate (MB/s)
 *
 * @param mbps - Throughput in MB/s
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted throughput string (e.g., "12.3 MB/s")
 */
export function formatThroughput(mbps: number, decimals: number = 1): string {
  return `${mbps.toFixed(decimals)} MB/s`;
}

/**
 * Format memory size in GB
 *
 * @param gb - Memory size in GB
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted memory string (e.g., "14.5 GB")
 */
export function formatMemory(gb: number, decimals: number = 1): string {
  return `${gb.toFixed(decimals)} GB`;
}

/**
 * Format ratio as "active / total"
 *
 * @param active - Active count
 * @param total - Total count
 * @returns Formatted ratio string (e.g., "3 / 8")
 */
export function formatRatio(active: number, total: number): string {
  return `${active} / ${total}`;
}

/**
 * Get status variant based on percentage threshold
 * Returns status string for component styling
 *
 * @param percent - Percentage value (0-100)
 * @returns Status variant ('ok' | 'warning' | 'critical')
 */
export function getPercentStatus(percent: number): 'ok' | 'warning' | 'critical' {
  if (percent < 70) return 'ok';
  if (percent < 90) return 'warning';
  return 'critical';
}

/**
 * Clamp value between min and max
 * Used for progress bar calculations
 *
 * @param value - Value to clamp
 * @param min - Minimum value (default: 0)
 * @param max - Maximum value (default: 100)
 * @returns Clamped value
 */
export function clamp(value: number, min: number = 0, max: number = 100): number {
  return Math.min(Math.max(value, min), max);
}

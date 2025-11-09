/**
 * patterns/types.ts
 *
 * Type definitions for dot matrix animation patterns
 * Defines different pixel reveal timing strategies
 */

export type PatternType =
  | 'sequential'    // Current: top→bottom, left→right
  | 'wave'          // Radial ripple from center
  | 'random'        // Random sparkle
  | 'center-out'    // Manhattan distance from center
  | 'spiral'        // Spiral arm from center
  | 'column'        // Column-by-column left→right
  | 'row'           // Row-by-row top→bottom
  | 'reverse';      // Reverse sequential

export interface PatternResult {
  startTime: number;
  endTime: number;
}

/**
 * patterns/PatternCalculator.ts
 *
 * Calculates pixel reveal timing for different animation patterns
 * Each pattern determines the order in which pixels illuminate
 */

import { PatternType, PatternResult } from './types';

/**
 * Seeded pseudo-random number generator for consistent random patterns
 * Uses Linear Congruential Generator (LCG) algorithm
 */
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }
}

/**
 * Pre-defined spiral order for 5×7 LED grid
 * Starts at center (3,2) and spirals outward clockwise
 */
const SPIRAL_ORDER_5x7: [number, number][] = [
  // Center
  [3, 2],
  // First ring
  [3, 3], [4, 3], [4, 2], [4, 1], [3, 1], [2, 1], [2, 2], [2, 3],
  // Second ring
  [2, 4], [3, 4], [4, 4], [5, 4], [5, 3], [5, 2], [5, 1], [5, 0],
  [4, 0], [3, 0], [2, 0], [1, 0], [1, 1], [1, 2], [1, 3], [1, 4],
  // Outer ring
  [0, 4], [0, 3], [0, 2], [0, 1], [0, 0], [6, 0], [6, 1], [6, 2], [6, 3], [6, 4],
];

export class PatternCalculator {
  private randomCache: Map<number, number[]> = new Map();

  /**
   * Calculate timing for a single pixel based on pattern
   *
   * @param charIndex - Index of character in text
   * @param row - Pixel row (0-6)
   * @param col - Pixel column (0-4)
   * @param pattern - Animation pattern to use
   * @param msPerPixel - Milliseconds per pixel reveal
   * @returns Timing information for pixel animation
   */
  calculatePixelTiming(
    charIndex: number,
    row: number,
    col: number,
    pattern: PatternType,
    msPerPixel: number
  ): PatternResult {
    const pixelIndex = this.getPixelIndexForPattern(row, col, pattern, charIndex);
    const totalIndex = charIndex * 35 + pixelIndex;
    const startTime = totalIndex * msPerPixel;
    const endTime = startTime + msPerPixel;

    return { startTime, endTime };
  }

  /**
   * Get pixel index (0-34) for given pattern and position
   */
  private getPixelIndexForPattern(
    row: number,
    col: number,
    pattern: PatternType,
    charIndex: number
  ): number {
    switch (pattern) {
      case 'sequential':
        return this.sequentialPattern(row, col);

      case 'wave':
        return this.wavePattern(row, col);

      case 'random':
        return this.randomPattern(row, col, charIndex);

      case 'center-out':
        return this.centerOutPattern(row, col);

      case 'spiral':
        return this.spiralPattern(row, col);

      case 'column':
        return this.columnPattern(row, col);

      case 'row':
        return this.rowPattern(row, col);

      case 'reverse':
        return this.reversePattern(row, col);

      default:
        return this.sequentialPattern(row, col);
    }
  }

  /**
   * SEQUENTIAL: top→bottom, left→right
   */
  private sequentialPattern(row: number, col: number): number {
    return row * 5 + col;
  }

  /**
   * WAVE: radial ripple from center
   * Uses Euclidean distance from center point
   */
  private wavePattern(row: number, col: number): number {
    const centerY = 3.5;
    const centerX = 2.5;
    const distance = Math.sqrt((row - centerY) ** 2 + (col - centerX) ** 2);
    const maxDist = Math.sqrt(3.5 ** 2 + 2.5 ** 2); // ≈ 4.3
    const normalizedDist = distance / maxDist;

    // Map normalized distance to pixel index
    return Math.floor(normalizedDist * 34);
  }

  /**
   * RANDOM: random sparkle effect
   * Uses seeded PRNG for consistency across renders
   */
  private randomPattern(row: number, col: number, charIndex: number): number {
    // Generate or retrieve cached random order for this character
    if (!this.randomCache.has(charIndex)) {
      const rng = new SeededRandom(charIndex + 42);
      const positions = Array.from({ length: 35 }, (_, i) => i);

      // Fisher-Yates shuffle with seeded random
      for (let i = positions.length - 1; i > 0; i--) {
        const j = Math.floor(rng.next() * (i + 1));
        const posI = positions[i];
        const posJ = positions[j];
        if (posI !== undefined && posJ !== undefined) {
          positions[i] = posJ;
          positions[j] = posI;
        }
      }

      this.randomCache.set(charIndex, positions);
    }

    const positions = this.randomCache.get(charIndex)!;
    const pixelPos = row * 5 + col;
    return positions.indexOf(pixelPos);
  }

  /**
   * CENTER_OUT: Manhattan distance from center
   * Expands outward in diamond shape
   */
  private centerOutPattern(row: number, col: number): number {
    const centerY = 3.5;
    const centerX = 2.5;
    const manhattanDist = Math.abs(row - centerY) + Math.abs(col - centerX);
    const maxManhattan = 6.0; // Maximum possible distance
    const normalizedDist = manhattanDist / maxManhattan;

    return Math.floor(normalizedDist * 34);
  }

  /**
   * SPIRAL: spiral arm from center
   * Uses pre-defined spiral order array
   */
  private spiralPattern(row: number, col: number): number {
    const pixelIndex = SPIRAL_ORDER_5x7.findIndex(
      ([r, c]) => r === row && c === col
    );

    // If not found in spiral order, use sequential as fallback
    return pixelIndex !== -1 ? pixelIndex : this.sequentialPattern(row, col);
  }

  /**
   * COLUMN: column-by-column left→right
   */
  private columnPattern(row: number, col: number): number {
    return col * 7 + row;
  }

  /**
   * ROW: row-by-row top→bottom
   */
  private rowPattern(row: number, col: number): number {
    return row * 5 + col;
  }

  /**
   * REVERSE: bottom→top, right→left
   */
  private reversePattern(row: number, col: number): number {
    const reversedRow = 6 - row;
    const reversedCol = 4 - col;
    return reversedRow * 5 + reversedCol;
  }

  /**
   * Clear cached data (useful for memory management)
   */
  clearCache(): void {
    this.randomCache.clear();
  }

  /**
   * Pre-calculate pattern for all pixels in text
   * Optional optimization for initial load
   */
  preCalculatePattern(pattern: PatternType, totalChars: number): void {
    if (pattern === 'random') {
      // Pre-generate random orders for all characters
      for (let charIndex = 0; charIndex < totalChars; charIndex++) {
        // Trigger cache population
        this.randomPattern(0, 0, charIndex);
      }
    }
  }
}

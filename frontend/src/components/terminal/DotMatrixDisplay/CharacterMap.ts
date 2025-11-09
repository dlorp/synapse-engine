/**
 * CharacterMap.ts
 *
 * 5x7 LED pixel patterns for dot matrix display
 * Each character is represented as a 7-row x 5-column boolean array
 * true = LED on, false = LED off
 */

export interface LEDPattern {
  char: string;
  pixels: boolean[][];
}

/**
 * Complete character set with 5x7 LED patterns
 * Covers A-Z, false-9, and common symbols
 */
export const LED_CHARACTERS: Record<string, boolean[][]> = {
  // Uppercase Letters (A-Z)
  'A': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
  ],
  'B': [
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, false],
  ],
  'C': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  'D': [
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, false],
  ],
  'E': [
    [true, true, true, true, true],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, true],
  ],
  'F': [
    [true, true, true, true, true],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
  ],
  'G': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, false],
    [true, false, true, true, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  'H': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
  ],
  'I': [
    [true, true, true, true, true],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [true, true, true, true, true],
  ],
  'J': [
    [false, false, false, true, true],
    [false, false, false, false, true],
    [false, false, false, false, true],
    [false, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  'K': [
    [true, false, false, false, true],
    [true, false, false, true, false],
    [true, false, true, false, false],
    [true, true, false, false, false],
    [true, false, true, false, false],
    [true, false, false, true, false],
    [true, false, false, false, true],
  ],
  'L': [
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, true],
  ],
  'M': [
    [true, false, false, false, true],
    [true, true, false, true, true],
    [true, false, true, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
  ],
  'N': [
    [true, false, false, false, true],
    [true, true, false, false, true],
    [true, false, true, false, true],
    [true, false, false, true, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
  ],
  'O': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  'P': [
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [true, false, false, false, false],
  ],
  'Q': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, true, false, true],
    [true, false, false, true, false],
    [false, true, true, false, true],
  ],
  'R': [
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, true, true, true, false],
    [true, false, true, false, false],
    [true, false, false, true, false],
    [true, false, false, false, true],
  ],
  'S': [
    [false, true, true, true, true],
    [true, false, false, false, false],
    [true, false, false, false, false],
    [false, true, true, true, false],
    [false, false, false, false, true],
    [false, false, false, false, true],
    [true, true, true, true, false],
  ],
  'T': [
    [true, true, true, true, true],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
  ],
  'U': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  'V': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, false, true, false],
    [false, false, true, false, false],
  ],
  'W': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [true, false, true, false, true],
    [true, true, false, true, true],
    [true, false, false, false, true],
  ],
  'X': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, false, true, false],
    [false, false, true, false, false],
    [false, true, false, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
  ],
  'Y': [
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, false, true, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
  ],
  'Z': [
    [true, true, true, true, true],
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, false, true, false, false],
    [false, true, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, true],
  ],

  // Numbers (0-9)
  '0': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, true, true],
    [true, false, true, false, true],
    [true, true, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  '1': [
    [false, false, true, false, false],
    [false, true, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, true, true, true, false],
  ],
  '2': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, false, true, false, false],
    [false, true, false, false, false],
    [true, true, true, true, true],
  ],
  '3': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [false, false, false, false, true],
    [false, false, true, true, false],
    [false, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  '4': [
    [false, false, false, true, false],
    [false, false, true, true, false],
    [false, true, false, true, false],
    [true, false, false, true, false],
    [true, true, true, true, true],
    [false, false, false, true, false],
    [false, false, false, true, false],
  ],
  '5': [
    [true, true, true, true, true],
    [true, false, false, false, false],
    [true, true, true, true, false],
    [false, false, false, false, true],
    [false, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  '6': [
    [false, false, true, true, false],
    [false, true, false, false, false],
    [true, false, false, false, false],
    [true, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  '7': [
    [true, true, true, true, true],
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, false, true, false, false],
    [false, true, false, false, false],
    [false, true, false, false, false],
    [false, true, false, false, false],
  ],
  '8': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, false],
  ],
  '9': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [true, false, false, false, true],
    [false, true, true, true, true],
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, true, true, false, false],
  ],

  // Common Symbols
  ' ': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
  ],
  '.': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, true, true, false, false],
    [false, true, true, false, false],
  ],
  ',': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, true, true, false, false],
    [false, true, true, false, false],
    [false, true, false, false, false],
  ],
  '!': [
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, false, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
  ],
  '?': [
    [false, true, true, true, false],
    [true, false, false, false, true],
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, false, true, false, false],
    [false, false, false, false, false],
    [false, false, true, false, false],
  ],
  '-': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [true, true, true, true, true],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
  ],
  '+': [
    [false, false, false, false, false],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [true, true, true, true, true],
    [false, false, true, false, false],
    [false, false, true, false, false],
    [false, false, false, false, false],
  ],
  ':': [
    [false, false, false, false, false],
    [false, true, true, false, false],
    [false, true, true, false, false],
    [false, false, false, false, false],
    [false, true, true, false, false],
    [false, true, true, false, false],
    [false, false, false, false, false],
  ],
  '/': [
    [false, false, false, false, true],
    [false, false, false, true, false],
    [false, false, false, true, false],
    [false, false, true, false, false],
    [false, true, false, false, false],
    [false, true, false, false, false],
    [true, false, false, false, false],
  ],
  '_': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [false, false, false, false, false],
    [true, true, true, true, true],
  ],
  '=': [
    [false, false, false, false, false],
    [false, false, false, false, false],
    [true, true, true, true, true],
    [false, false, false, false, false],
    [true, true, true, true, true],
    [false, false, false, false, false],
    [false, false, false, false, false],
  ],
};

/**
 * LED display configuration constants
 */
export const LED_CONFIG = {
  pixelSize: 4,             // LED dot size in pixels
  pixelGap: 2,              // Gap between LEDs
  charWidth: 5,             // Character width in LED pixels
  charHeight: 7,            // Character height in LED pixels
  charSpacing: 2,           // Space between characters in LED pixels
  glowIntensity: 8,         // Phosphor glow blur radius
  color: '#ff9500',         // Phosphor orange
  backgroundIntensity: 0.08, // Dim glow for "off" pixels (full grid visibility)
} as const;

/**
 * Fallback pattern for unknown characters (displays as empty 5x7 grid)
 */
const FALLBACK_PATTERN: boolean[][] = [
  [false, false, false, false, false],
  [false, false, false, false, false],
  [false, false, false, false, false],
  [false, false, false, false, false],
  [false, false, false, false, false],
  [false, false, false, false, false],
  [false, false, false, false, false],
];

/**
 * Get LED pattern for a character
 * Returns fallback '?' pattern for unknown characters, or empty pattern if '?' is missing
 */
export function getCharacterPattern(char: string): boolean[][] {
  const upperChar = char.toUpperCase();
  return LED_CHARACTERS[upperChar] || LED_CHARACTERS['?'] || FALLBACK_PATTERN;
}

/**
 * Validate that a pattern is 7 rows x 5 columns
 */
export function isValidPattern(pattern: boolean[][]): boolean {
  if (pattern.length !== 7) return false;
  return pattern.every(row => row.length === 5);
}

/**
 * Calculate total width needed for text in pixels
 */
export function calculateTextWidth(text: string): number {
  const { charWidth, pixelSize, pixelGap, charSpacing } = LED_CONFIG;
  const charPixelWidth = charWidth * (pixelSize + pixelGap);
  const totalCharWidth = text.length * charPixelWidth;
  const totalSpacing = (text.length - 1) * charSpacing * (pixelSize + pixelGap);
  return totalCharWidth + totalSpacing + 40; // 40px padding (20px on each side)
}

/**
 * Calculate total height needed for text in pixels
 */
export function calculateTextHeight(): number {
  const { charHeight, pixelSize, pixelGap } = LED_CONFIG;
  return charHeight * (pixelSize + pixelGap) + 40; // 40px padding (20px top/bottom)
}

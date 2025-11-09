/**
 * Phosphor Glow Utility
 *
 * Generates CSS box-shadow values for phosphor CRT glow effects.
 * Supports multiple intensity levels and custom colors.
 *
 * @module utils/phosphorGlow
 */

export type GlowIntensity = 'subtle' | 'medium' | 'intense';

/**
 * Generates multi-layer box-shadow CSS for phosphor glow effect
 *
 * @param color - Hex color value (e.g., '#ff9500')
 * @param intensity - Glow intensity level
 * @returns CSS box-shadow string with multiple layers
 *
 * @example
 * ```typescript
 * const glow = phosphorGlow('#ff9500', 'medium');
 * // Returns: "0 0 10px rgba(255,149,0,0.8), 0 0 20px rgba(255,149,0,0.4), 0 0 30px rgba(255,149,0,0.2)"
 * ```
 */
export function phosphorGlow(color: string, intensity: GlowIntensity = 'medium'): string {
  // Parse hex color to RGB
  const rgb = hexToRgb(color);
  if (!rgb) {
    console.warn(`Invalid color format: ${color}. Using default orange.`);
    return phosphorGlow('#ff9500', intensity);
  }

  const { r, g, b } = rgb;

  // Define shadow layers based on intensity
  const layers = {
    subtle: [
      { blur: 5, opacity: 0.6 },
      { blur: 10, opacity: 0.3 },
      { blur: 15, opacity: 0.1 },
    ],
    medium: [
      { blur: 10, opacity: 0.8 },
      { blur: 20, opacity: 0.4 },
      { blur: 30, opacity: 0.2 },
    ],
    intense: [
      { blur: 10, opacity: 1.0 },
      { blur: 20, opacity: 0.6 },
      { blur: 30, opacity: 0.4 },
      { blur: 40, opacity: 0.2 },
      { blur: 50, opacity: 0.1 },
    ],
  };

  const selectedLayers = layers[intensity];

  // Generate box-shadow string
  const shadows = selectedLayers.map(
    (layer) => `0 0 ${layer.blur}px rgba(${r}, ${g}, ${b}, ${layer.opacity})`
  );

  return shadows.join(', ');
}

/**
 * Generates text-shadow for chromatic aberration effect
 *
 * @param offset - Pixel offset for red/cyan split (default: 1)
 * @returns CSS text-shadow string
 *
 * @example
 * ```typescript
 * const aberration = chromaticAberration(2);
 * // Returns: "-2px 0 0 rgba(255,0,0,0.3), 2px 0 0 rgba(0,255,255,0.3)"
 * ```
 */
export function chromaticAberration(offset: number = 1): string {
  return [
    `-${offset}px 0 0 rgba(255, 0, 0, 0.3)`,
    `${offset}px 0 0 rgba(0, 255, 255, 0.3)`,
  ].join(', ');
}

/**
 * Converts hex color to RGB object
 *
 * @param hex - Hex color string (with or without #)
 * @returns RGB object or null if invalid
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  // Remove # if present
  const cleanHex = hex.replace('#', '');

  // Validate hex format
  if (!/^[0-9A-F]{6}$/i.test(cleanHex)) {
    return null;
  }

  // Parse RGB values
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);

  return { r, g, b };
}

/**
 * Generates CSS for vignette overlay effect
 *
 * @param intensity - Vignette darkness (0-1)
 * @returns CSS background value
 */
export function vignetteOverlay(intensity: number = 0.6): string {
  return `radial-gradient(circle, transparent 50%, rgba(0, 0, 0, ${intensity}) 100%)`;
}

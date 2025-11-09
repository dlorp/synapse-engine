/**
 * AnimatedScanlines Component
 *
 * Renders animated horizontal scanlines for CRT monitor effect.
 * GPU-accelerated using CSS transforms for 60fps performance.
 *
 * @module components/terminal/AnimatedScanlines
 */

import React from 'react';
import styles from './AnimatedScanlines.module.css';

export type ScanlineSpeed = 'slow' | 'medium' | 'fast';

export interface AnimatedScanlinesProps {
  /** Animation speed (default: medium) */
  speed?: ScanlineSpeed;
  /** Scanline opacity 0-1 (default: 0.2) */
  opacity?: number;
  /** Scanline intensity (alias for opacity, deprecated) */
  intensity?: number;
  /** Enable/disable scanlines (default: true) */
  enabled?: boolean;
}

/**
 * AnimatedScanlines - CRT scanline effect overlay
 *
 * Creates animated horizontal lines that scroll vertically to simulate
 * CRT monitor scanlines. Uses GPU-accelerated transforms for 60fps performance.
 * Optimized with will-change hints and compositor layer promotion.
 *
 * @example
 * ```tsx
 * <AnimatedScanlines speed="medium" opacity={0.3} />
 * ```
 */
export const AnimatedScanlines: React.FC<AnimatedScanlinesProps> = ({
  speed = 'medium',
  opacity,
  intensity = 0.2,
  enabled = true,
}) => {
  if (!enabled) {
    return null;
  }

  // Support both opacity and intensity props (backward compatibility)
  const finalOpacity = opacity !== undefined ? opacity : intensity;
  const clampedOpacity = Math.max(0, Math.min(1, finalOpacity));

  const speedClass = {
    slow: styles.slow,
    medium: styles.medium,
    fast: styles.fast,
  }[speed];

  return (
    <div
      className={`${styles.scanlines} ${speedClass}`}
      style={{
        opacity: clampedOpacity,
        // Custom CSS property for dynamic opacity control
        ['--scanline-opacity' as string]: clampedOpacity.toString(),
      }}
      aria-hidden="true"
      data-testid="animated-scanlines"
    />
  );
};

AnimatedScanlines.displayName = 'AnimatedScanlines';

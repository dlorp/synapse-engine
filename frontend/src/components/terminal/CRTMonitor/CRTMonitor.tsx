/**
 * CRTMonitor Component
 *
 * Master wrapper component that applies CRT (cathode ray tube) effects to children.
 * Provides phosphor glow, scanlines, chromatic aberration, screen curvature, and vignette.
 *
 * @module components/terminal/CRTMonitor
 */

import React, { ReactNode } from 'react';
import { AnimatedScanlines, ScanlineSpeed } from '../AnimatedScanlines';
import styles from './CRTMonitor.module.css';

export type CRTIntensity = 'subtle' | 'medium' | 'intense';

export interface CRTMonitorProps {
  /** Child content to render inside CRT effect */
  children: ReactNode;
  /** Effect intensity level (default: medium) */
  intensity?: CRTIntensity;
  /** Bloom glow intensity 0-1 (default: 0.3) */
  bloomIntensity?: number;
  /** Enable scanline animation (default: true) */
  enableScanlines?: boolean;
  /** Enable scanlines alias (deprecated, use enableScanlines) */
  scanlinesEnabled?: boolean;
  /** Enable screen curvature effect (default: true) */
  enableCurvature?: boolean;
  /** Enable curvature alias (deprecated, use enableCurvature) */
  curvatureEnabled?: boolean;
  /** Enable chromatic aberration (default: true) */
  enableAberration?: boolean;
  /** Enable vignette overlay (default: true) */
  enableVignette?: boolean;
  /** Scanline speed (default: medium) */
  scanlineSpeed?: ScanlineSpeed;
  /** Additional CSS class name */
  className?: string;
  /** ARIA label for accessibility */
  ariaLabel?: string;
}

/**
 * CRTMonitor - Wraps content with CRT monitor visual effects
 *
 * This is the foundational component for the terminal aesthetic.
 * All terminal UI components should be wrapped in CRTMonitor for consistent styling.
 *
 * Visual effects applied:
 * - Phosphor glow (multi-layer box-shadow)
 * - Animated scanlines (optional)
 * - Screen curvature (subtle 15° perspective)
 * - Chromatic aberration (text-shadow)
 * - Bloom effect (configurable intensity with blur and screen blend)
 * - Vignette overlay (darkened corners)
 *
 * @example
 * ```tsx
 * <CRTMonitor intensity="medium" bloomIntensity={0.3} scanlinesEnabled={true}>
 *   <div className="synapse-panel">Content here</div>
 * </CRTMonitor>
 * ```
 */
export const CRTMonitor: React.FC<CRTMonitorProps> = ({
  children,
  intensity = 'medium',
  bloomIntensity = 0.3,
  enableScanlines,
  scanlinesEnabled = true,
  enableCurvature,
  curvatureEnabled = true,
  enableAberration = true,
  enableVignette = true,
  scanlineSpeed = 'medium',
  className = '',
  ariaLabel,
}) => {
  // Support both old and new prop names for backward compatibility
  const scanlinesActive = enableScanlines !== undefined ? enableScanlines : scanlinesEnabled;
  const curvatureActive = enableCurvature !== undefined ? enableCurvature : curvatureEnabled;

  // Clamp bloom intensity to valid range
  const clampedBloom = Math.max(0, Math.min(1, bloomIntensity));
  // Build CSS class names based on enabled effects
  const intensityClass = {
    subtle: styles.subtle,
    medium: styles.medium,
    intense: styles.intense,
  }[intensity];

  const containerClasses = [
    styles.crtContainer,
    intensityClass,
    curvatureActive ? styles.curved : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const screenClasses = [
    styles.crtScreen,
    enableAberration ? styles.chromaticAberration : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Map intensity to scanline opacity
  const scanlineOpacity = {
    subtle: 0.1,
    medium: 0.2,
    intense: 0.3,
  }[intensity];

  return (
    <div
      className={containerClasses}
      role="region"
      aria-label={ariaLabel || 'CRT Monitor Display'}
      data-testid="crt-monitor"
    >
      {/* Bloom layer - duplicate children with blur for glow effect */}
      {clampedBloom > 0 && (
        <div
          className={styles.bloomLayer}
          style={{
            opacity: clampedBloom,
            filter: `blur(${clampedBloom * 20}px)`,
          }}
          aria-hidden="true"
          data-testid="bloom-layer"
        >
          {children}
        </div>
      )}

      {/* Main screen content */}
      <div className={screenClasses}>
        {children}
      </div>

      {/* Scanline overlay */}
      {scanlinesActive && (
        <AnimatedScanlines
          speed={scanlineSpeed}
          opacity={scanlineOpacity}
          enabled={true}
        />
      )}

      {/* Vignette overlay */}
      {enableVignette && (
        <div
          className={styles.vignetteOverlay}
          aria-hidden="true"
          data-testid="vignette-overlay"
        />
      )}
    </div>
  );
};

CRTMonitor.displayName = 'CRTMonitor';

import React from 'react';
import clsx from 'clsx';
import { Panel, PanelProps } from '../Panel/Panel';
import styles from './DotMatrixPanel.module.css';

export interface DotMatrixPanelProps extends PanelProps {
  /* ===== BASIC EFFECTS ===== */

  /**
   * Enable scan line effect
   * @default false
   */
  enableScanLines?: boolean;

  /**
   * Scan line speed variant
   * @default 'normal'
   */
  scanLineSpeed?: 'slow' | 'normal' | 'fast';

  /**
   * Enable dot matrix grid background
   * @default false
   */
  enableGrid?: boolean;

  /**
   * Grid density
   * @default 'normal'
   */
  gridDensity?: 'sparse' | 'normal' | 'dense';

  /**
   * Enable animated grid (pulsing)
   * @default false
   */
  animatedGrid?: boolean;

  /**
   * Enable border glow effect
   * @default false
   */
  enableBorderGlow?: boolean;

  /**
   * Border glow color
   * @default 'orange'
   */
  glowColor?: 'orange' | 'cyan' | 'red';

  /**
   * Enable static horizontal scan lines
   * @default false
   */
  enableStaticScanLines?: boolean;

  /**
   * Enable CRT screen effect (vignette)
   * @default false
   */
  enableCrtEffect?: boolean;

  /**
   * Enable CRT flicker
   * @default false
   */
  enableFlicker?: boolean;

  /**
   * Effect intensity (overall opacity multiplier)
   * @default 1
   */
  effectIntensity?: number;

  /* ===== ADVANCED TERMINAL EFFECTS ===== */

  /**
   * Enable glitch effect (horizontal displacement)
   * Use for errors, warnings, or system instability
   * @default false
   */
  enableGlitch?: boolean;

  /**
   * Glitch severity level
   * - 'moderate': Horizontal displacement only
   * - 'severe': Horizontal + vertical clipping
   * @default 'moderate'
   */
  glitchSeverity?: 'moderate' | 'severe';

  /**
   * Enable static noise overlay
   * Use for loading states or signal interference
   * @default false
   */
  enableStaticNoise?: boolean;

  /**
   * Enable interlacing effect (horizontal lines)
   * Creates retro CRT scan line appearance
   * @default false
   */
  enableInterlacing?: boolean;

  /**
   * Enable screen tearing effect
   * Use for connection issues or data corruption
   * @default false
   */
  enableScreenTear?: boolean;

  /**
   * Enable VHS tracking error effect
   * Retro distortion with color shifting
   * @default false
   */
  enableVHSTracking?: boolean;

  /**
   * Enable chromatic aberration (RGB split)
   * Use for emphasis or active states
   * @default false
   */
  enableChromaticAberration?: boolean;
}

export const DotMatrixPanel: React.FC<DotMatrixPanelProps> = ({
  children,
  // Basic effects
  enableScanLines = false,
  scanLineSpeed = 'normal',
  enableGrid = false,
  gridDensity = 'normal',
  animatedGrid = false,
  enableBorderGlow = false,
  glowColor = 'orange',
  enableStaticScanLines = false,
  enableCrtEffect = false,
  enableFlicker = false,
  effectIntensity = 1,
  // Advanced terminal effects
  enableGlitch = false,
  glitchSeverity = 'moderate',
  enableStaticNoise = false,
  enableInterlacing = false,
  enableScreenTear = false,
  enableVHSTracking = false,
  enableChromaticAberration = false,
  className,
  ...panelProps
}) => {
  const panelRef = React.useRef<HTMLDivElement>(null);

  // Build grid class based on configuration
  const gridClass = React.useMemo(() => {
    if (!enableGrid) return null;
    if (animatedGrid) return 'dot-matrix-bg-animated';
    if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
    if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
    return 'dot-matrix-bg';
  }, [enableGrid, animatedGrid, gridDensity]);

  // Build scan line class based on speed
  const scanLineClass = React.useMemo(() => {
    if (!enableScanLines) return null;
    if (scanLineSpeed === 'slow') return 'scan-line-slow';
    if (scanLineSpeed === 'fast') return 'scan-line-fast';
    return null; // Use default scan-line from animations.css
  }, [enableScanLines, scanLineSpeed]);

  // Build border glow class
  const borderGlowClass = React.useMemo(() => {
    if (!enableBorderGlow) return null;
    if (glowColor === 'cyan') return 'border-glow-cyan';
    if (glowColor === 'red') return 'border-glow-red';
    return 'border-glow-orange';
  }, [enableBorderGlow, glowColor]);

  // Build glitch class
  const glitchClass = React.useMemo(() => {
    if (!enableGlitch) return null;
    return glitchSeverity === 'severe' ? 'glitch-severe' : 'glitch';
  }, [enableGlitch, glitchSeverity]);

  return (
    <div
      ref={panelRef}
      className={clsx(
        styles.dotMatrixWrapper,
        // Basic effects
        enableStaticScanLines && 'scan-lines-static',
        enableCrtEffect && 'crt-screen',
        enableFlicker && 'crt-flicker',
        // Advanced effects
        enableStaticNoise && 'static-noise',
        enableInterlacing && 'interlaced',
        enableScreenTear && 'screen-tear',
        enableVHSTracking && 'vhs-tracking',
        enableChromaticAberration && 'chromatic-aberration',
        glitchClass,
        className
      )}
      style={{
        ['--effect-intensity' as string]: effectIntensity,
      }}
      {...(enableChromaticAberration && {
        'data-text': typeof children === 'string' ? children : '',
      })}
    >
      {/* Background Grid Layer */}
      {enableGrid && gridClass && (
        <div className={clsx(styles.gridLayer, gridClass)} />
      )}

      {/* Panel with optional border glow */}
      <Panel
        {...panelProps}
        className={clsx(borderGlowClass && borderGlowClass)}
      >
        {children}
      </Panel>

      {/* Animated Scan Line Layer */}
      {enableScanLines && (
        <div className={clsx(styles.scanLineLayer, scanLineClass || 'scan-line')} />
      )}
    </div>
  );
};

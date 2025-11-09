import React from 'react';
import clsx from 'clsx';
import styles from './TerminalEffect.module.css';

export interface TerminalEffectConfig {
  enableScanLines?: boolean;
  scanLineSpeed?: 'slow' | 'normal' | 'fast';
  enableGrid?: boolean;
  gridDensity?: 'sparse' | 'normal' | 'dense';
  animatedGrid?: boolean;
  enablePhosphorGlow?: boolean;
  phosphorColor?: 'orange' | 'cyan' | 'red';
  staticGlow?: boolean;
  enableStaticScanLines?: boolean;
  enableCrtEffect?: boolean;
  enableFlicker?: boolean;
  enableDataStream?: boolean;
  effectIntensity?: number;
  className?: string;
}

export interface WithTerminalEffectProps {
  terminalEffect?: TerminalEffectConfig;
}

/**
 * Higher-order component that wraps any component with terminal effects
 */
export function withTerminalEffect<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P & WithTerminalEffectProps> {
  const ComponentWithTerminalEffect: React.FC<P & WithTerminalEffectProps> = ({
    terminalEffect,
    ...props
  }) => {
    // If no effect config provided, just render the component as-is
    if (!terminalEffect) {
      return <WrappedComponent {...(props as P)} />;
    }

    const {
      enableScanLines = false,
      scanLineSpeed = 'normal',
      enableGrid = false,
      gridDensity = 'normal',
      animatedGrid = false,
      enablePhosphorGlow = false,
      phosphorColor = 'orange',
      staticGlow = false,
      enableStaticScanLines = false,
      enableCrtEffect = false,
      enableFlicker = false,
      enableDataStream = false,
      effectIntensity = 1,
      className,
    } = terminalEffect;

    // Build grid class
    const gridClass = React.useMemo(() => {
      if (!enableGrid) return null;
      if (animatedGrid) return 'dot-matrix-bg-animated';
      if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
      if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
      return 'dot-matrix-bg';
    }, [enableGrid, animatedGrid, gridDensity]);

    // Build scan line class
    const scanLineClass = React.useMemo(() => {
      if (!enableScanLines) return null;
      if (scanLineSpeed === 'slow') return 'scan-line-slow';
      if (scanLineSpeed === 'fast') return 'scan-line-fast';
      return 'scan-line';
    }, [enableScanLines, scanLineSpeed]);

    // Build phosphor glow class
    const phosphorGlowClass = React.useMemo(() => {
      if (!enablePhosphorGlow) return null;
      if (staticGlow) {
        if (phosphorColor === 'cyan') return 'phosphor-glow-static-cyan';
        if (phosphorColor === 'red') return 'phosphor-glow-static-red';
        return 'phosphor-glow-static-orange';
      } else {
        if (phosphorColor === 'cyan') return 'phosphor-glow-cyan';
        if (phosphorColor === 'red') return 'phosphor-glow-red';
        return 'phosphor-glow-orange';
      }
    }, [enablePhosphorGlow, phosphorColor, staticGlow]);

    return (
      <div
        className={clsx(
          styles.terminalEffectWrapper,
          enableStaticScanLines && 'scan-lines-static',
          enableCrtEffect && 'crt-screen',
          enableFlicker && 'crt-flicker',
          enableDataStream && 'data-stream',
          phosphorGlowClass,
          className
        )}
        style={{
          ['--effect-intensity' as string]: effectIntensity,
        }}
      >
        {/* Background Grid Layer */}
        {enableGrid && gridClass && (
          <div className={clsx(styles.gridLayer, gridClass)} />
        )}

        {/* Wrapped Component */}
        <div className={styles.componentLayer}>
          <WrappedComponent {...(props as P)} />
        </div>

        {/* Animated Scan Line Layer */}
        {enableScanLines && scanLineClass && (
          <div className={clsx(styles.scanLineLayer, scanLineClass)} />
        )}
      </div>
    );
  };

  ComponentWithTerminalEffect.displayName = `withTerminalEffect(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithTerminalEffect;
}

/**
 * Component version of terminal effect wrapper
 */
export const TerminalEffect: React.FC<
  TerminalEffectConfig & { children: React.ReactNode }
> = ({ children, ...config }) => {
  const {
    enableScanLines = false,
    scanLineSpeed = 'normal',
    enableGrid = false,
    gridDensity = 'normal',
    animatedGrid = false,
    enablePhosphorGlow = false,
    phosphorColor = 'orange',
    staticGlow = false,
    enableStaticScanLines = false,
    enableCrtEffect = false,
    enableFlicker = false,
    enableDataStream = false,
    effectIntensity = 1,
    className,
  } = config;

  const gridClass = React.useMemo(() => {
    if (!enableGrid) return null;
    if (animatedGrid) return 'dot-matrix-bg-animated';
    if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
    if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
    return 'dot-matrix-bg';
  }, [enableGrid, animatedGrid, gridDensity]);

  const scanLineClass = React.useMemo(() => {
    if (!enableScanLines) return null;
    if (scanLineSpeed === 'slow') return 'scan-line-slow';
    if (scanLineSpeed === 'fast') return 'scan-line-fast';
    return 'scan-line';
  }, [enableScanLines, scanLineSpeed]);

  const phosphorGlowClass = React.useMemo(() => {
    if (!enablePhosphorGlow) return null;
    if (staticGlow) {
      if (phosphorColor === 'cyan') return 'phosphor-glow-static-cyan';
      if (phosphorColor === 'red') return 'phosphor-glow-static-red';
      return 'phosphor-glow-static-orange';
    } else {
      if (phosphorColor === 'cyan') return 'phosphor-glow-cyan';
      if (phosphorColor === 'red') return 'phosphor-glow-red';
      return 'phosphor-glow-orange';
    }
  }, [enablePhosphorGlow, phosphorColor, staticGlow]);

  return (
    <div
      className={clsx(
        styles.terminalEffectWrapper,
        enableStaticScanLines && 'scan-lines-static',
        enableCrtEffect && 'crt-screen',
        enableFlicker && 'crt-flicker',
        enableDataStream && 'data-stream',
        phosphorGlowClass,
        className
      )}
      style={{
        ['--effect-intensity' as string]: effectIntensity,
      }}
    >
      {enableGrid && gridClass && (
        <div className={clsx(styles.gridLayer, gridClass)} />
      )}
      <div className={styles.componentLayer}>{children}</div>
      {enableScanLines && scanLineClass && (
        <div className={clsx(styles.scanLineLayer, scanLineClass)} />
      )}
    </div>
  );
};

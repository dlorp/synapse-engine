import { useRef, useImperativeHandle, forwardRef } from 'react';
import { ParticleEffect, ParticleEffectRef } from '../ParticleEffect';
import styles from './FireEffect.module.css';

export interface FireEffectProps {
  /**
   * Width of fire effect (default: 200)
   */
  width?: number;

  /**
   * Height of fire effect (default: 300)
   */
  height?: number;

  /**
   * Intensity of fire (0-100, default: 50)
   */
  intensity?: number;

  /**
   * Color scheme: 'orange' | 'blue' | 'green' | 'plasma'
   * Default: 'orange' (phosphor orange fire)
   */
  colorScheme?: 'orange' | 'blue' | 'green' | 'plasma';

  /**
   * Emitter width (default: matches width)
   */
  emitterWidth?: number;

  /**
   * Auto-start on mount (default: true)
   */
  autoStart?: boolean;

  /**
   * Additional CSS classes
   */
  className?: string;
}

export interface FireEffectRef {
  start: () => void;
  stop: () => void;
  setIntensity: (intensity: number) => void;
  getParticleCount: () => number;
}

/**
 * Color palettes for different fire types
 */
const COLOR_PALETTES: Record<string, string[]> = {
  orange: [
    '#ff9500', // Phosphor orange (S.Y.N.A.P.S.E. brand)
    '#ff6b00',
    '#ff4500',
    '#ff2200',
    '#cc0000',
  ],
  blue: [
    '#00ffff',
    '#00ccff',
    '#0099ff',
    '#0066ff',
    '#0033cc',
  ],
  green: [
    '#00ff00',
    '#00cc00',
    '#009900',
    '#006600',
    '#003300',
  ],
  plasma: [
    '#ff00ff',
    '#ff0099',
    '#ff0066',
    '#cc0066',
    '#990066',
  ],
};

export const FireEffect = forwardRef<FireEffectRef, FireEffectProps>(
  (
    {
      width = 200,
      height = 300,
      intensity = 50,
      colorScheme = 'orange',
      emitterWidth,
      autoStart = true,
      className,
    },
    ref
  ) => {
    const particleRef = useRef<ParticleEffectRef>(null);

    // Calculate particle configuration based on intensity
    const intensityFactor = intensity / 100;
    const particleRate = 30 + intensityFactor * 70; // 30-100 particles/sec
    const particleSpeed = 50 + intensityFactor * 100; // 50-150 px/s

    // Get color palette
    const colors = COLOR_PALETTES[colorScheme] || COLOR_PALETTES.orange;

    // Fire particle configuration
    const particleConfig = {
      maxParticles: 500,
      backgroundColor: 'transparent',
      emitter: {
        type: 'line' as const,
        x: 0,
        y: height - 10,
        width: emitterWidth || width,
        height: 0,
        angle: -90, // Upward
        spread: 30, // Flame spread
        rate: particleRate,
        particlesPerEmit: 2,
      },
      particle: {
        minSize: 3,
        maxSize: 8,
        minSpeed: particleSpeed * 0.8,
        maxSpeed: particleSpeed * 1.2,
        minLife: 800,
        maxLife: 1500,
        color: colors,
        startAlpha: 0.9,
        endAlpha: 0,
        gravity: { x: 0, y: -80 }, // Strong upward force
        friction: 0.96, // Slight air resistance
        rotation: true,
        rotationSpeed: 0.2,
        glowIntensity: 15, // Strong glow for fire
      },
    };

    // Note: Intensity changes require component remount
    // Dynamic intensity updates would need ParticleSystem updateConfig exposed in ref

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      start: () => {
        particleRef.current?.start();
      },
      stop: () => {
        particleRef.current?.stop();
      },
      setIntensity: (_newIntensity: number) => {
        // Would need to recreate particle system with new config
        // For now, this is a placeholder
        console.warn('Dynamic intensity not yet implemented');
      },
      getParticleCount: () => {
        return particleRef.current?.getParticleCount() || 0;
      },
    }));

    return (
      <div
        className={`${styles.fireContainer} ${className || ''}`}
        style={{ width, height }}
      >
        <ParticleEffect
          ref={particleRef}
          {...particleConfig}
          width={width}
          height={height}
          autoStart={autoStart}
          autoResize={false}
        />
        {/* Heat distortion overlay */}
        <div className={styles.heatDistortion} aria-hidden="true" />
      </div>
    );
  }
);

FireEffect.displayName = 'FireEffect';

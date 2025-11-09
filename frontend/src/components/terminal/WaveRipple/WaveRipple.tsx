import React, { useEffect, useRef, useState } from 'react';
import { WaveRippleAnimation } from '@/animations/WaveRippleAnimation';
import styles from './WaveRipple.module.css';

export interface WaveRippleProps {
  /**
   * Primary color for waves (default: phosphor orange #ff9500)
   */
  color?: string;

  /**
   * Background color (default: transparent)
   */
  backgroundColor?: string;

  /**
   * Maximum concurrent waves (default: 10)
   */
  maxWaves?: number;

  /**
   * Expansion speed in px/frame (default: 2)
   */
  waveSpeed?: number;

  /**
   * Auto-generate waves at intervals (default: false)
   */
  autoGenerate?: boolean;

  /**
   * Interval between auto-generated waves in ms (default: 2000)
   */
  autoInterval?: number;

  /**
   * Glow intensity, 0-10 (default: 8)
   */
  glowIntensity?: number;

  /**
   * Wave line thickness in pixels (default: 2)
   */
  lineWidth?: number;

  /**
   * Enable click-to-create waves (default: false)
   */
  clickEnabled?: boolean;

  /**
   * Width of canvas (default: full container width)
   */
  width?: number;

  /**
   * Height of canvas (default: full container height)
   */
  height?: number;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Whether to automatically resize with container
   */
  autoResize?: boolean;

  /**
   * Callback when wave is created
   */
  onWaveCreate?: (x: number, y: number) => void;
}

export const WaveRipple: React.FC<WaveRippleProps> = ({
  color = '#ff9500',
  backgroundColor = 'transparent',
  maxWaves = 10,
  waveSpeed = 2,
  autoGenerate = false,
  autoInterval = 2000,
  glowIntensity = 8,
  lineWidth = 2,
  clickEnabled = false,
  width,
  height,
  className,
  autoResize = true,
  onWaveCreate,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<WaveRippleAnimation | null>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });

  // Initialize canvas size
  useEffect(() => {
    if (!containerRef.current) return;

    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setCanvasSize({
          width: width || rect.width,
          height: height || rect.height,
        });
      }
    };

    updateSize();

    if (autoResize) {
      const resizeObserver = new ResizeObserver(updateSize);
      resizeObserver.observe(containerRef.current);
      return () => resizeObserver.disconnect();
    }
  }, [width, height, autoResize]);

  // Initialize and start animation
  useEffect(() => {
    if (!canvasRef.current || canvasSize.width === 0 || canvasSize.height === 0) {
      return;
    }

    const animation = new WaveRippleAnimation(canvasRef.current, {
      color,
      backgroundColor,
      maxWaves,
      waveSpeed,
      autoGenerate,
      autoInterval,
      glowIntensity,
      lineWidth,
    });

    animation.start();
    animationRef.current = animation;

    return () => {
      animation.destroy();
      animationRef.current = null;
    };
  }, [
    color,
    backgroundColor,
    maxWaves,
    waveSpeed,
    autoGenerate,
    autoInterval,
    glowIntensity,
    lineWidth,
    canvasSize,
  ]);

  // Handle click-enabled changes
  useEffect(() => {
    if (animationRef.current) {
      if (clickEnabled) {
        animationRef.current.enableClickWaves();
      } else {
        animationRef.current.disableClickWaves();
      }
    }
  }, [clickEnabled]);

  // Update animation config when props change
  useEffect(() => {
    if (animationRef.current) {
      animationRef.current.updateConfig({
        color,
        backgroundColor,
        maxWaves,
        waveSpeed,
        autoGenerate,
        autoInterval,
        glowIntensity,
        lineWidth,
      });
    }
  }, [
    color,
    backgroundColor,
    maxWaves,
    waveSpeed,
    autoGenerate,
    autoInterval,
    glowIntensity,
    lineWidth,
  ]);

  // Handle canvas resize
  useEffect(() => {
    if (animationRef.current && canvasSize.width > 0 && canvasSize.height > 0) {
      animationRef.current.resize(canvasSize.width, canvasSize.height);
    }
  }, [canvasSize]);

  // Expose imperative handle for creating waves programmatically
  useEffect(() => {
    if (onWaveCreate && canvasRef.current && animationRef.current) {
      const createWave = (x: number, y: number) => {
        animationRef.current?.createWave(x, y);
        onWaveCreate(x, y);
      };
      // Store reference for external access
      (canvasRef.current as any).createWave = createWave;
    }
  }, [onWaveCreate]);

  return (
    <div ref={containerRef} className={`${styles.container} ${className || ''}`}>
      <canvas
        ref={canvasRef}
        width={canvasSize.width}
        height={canvasSize.height}
        className={styles.canvas}
      />
    </div>
  );
};

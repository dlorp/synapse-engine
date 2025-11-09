import React, { useEffect, useRef, useState } from 'react';
import { MatrixRainAnimation } from '@/animations/MatrixRainAnimation';
import styles from './MatrixRain.module.css';

export interface MatrixRainProps {
  /**
   * Primary color for falling characters (default: phosphor orange #ff9500)
   */
  color?: string;

  /**
   * Background color (default: #000000)
   */
  backgroundColor?: string;

  /**
   * Font size for characters in pixels (default: 16)
   */
  fontSize?: number;

  /**
   * Speed multiplier for falling characters (default: 1)
   */
  speed?: number;

  /**
   * Density of columns, 0-1 (default: 0.5)
   */
  density?: number;

  /**
   * Glow intensity, 0-10 (default: 5)
   */
  glowIntensity?: number;

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
}

export const MatrixRain: React.FC<MatrixRainProps> = ({
  color = '#ff9500',
  backgroundColor = '#000000',
  fontSize = 16,
  speed = 1,
  density = 0.5,
  glowIntensity = 5,
  width,
  height,
  className,
  autoResize = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<MatrixRainAnimation | null>(null);
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

    const animation = new MatrixRainAnimation(canvasRef.current, {
      color,
      backgroundColor,
      fontSize,
      speed,
      density,
      glowIntensity,
    });

    animation.start();
    animationRef.current = animation;

    return () => {
      animation.destroy();
      animationRef.current = null;
    };
  }, [color, backgroundColor, fontSize, speed, density, glowIntensity, canvasSize]);

  // Update animation config when props change
  useEffect(() => {
    if (animationRef.current) {
      animationRef.current.updateConfig({
        color,
        backgroundColor,
        fontSize,
        speed,
        density,
        glowIntensity,
      });
    }
  }, [color, backgroundColor, fontSize, speed, density, glowIntensity]);

  // Handle canvas resize
  useEffect(() => {
    if (animationRef.current && canvasSize.width > 0 && canvasSize.height > 0) {
      animationRef.current.resize(canvasSize.width, canvasSize.height);
    }
  }, [canvasSize]);

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

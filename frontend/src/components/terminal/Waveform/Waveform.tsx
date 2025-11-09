import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { WaveformAnimation } from '@/animations/WaveformAnimation';
import styles from './Waveform.module.css';

export interface WaveformProps {
  /**
   * Initial data points
   */
  data?: number[];

  /**
   * Primary color (default: phosphor orange #ff9500)
   */
  color?: string;

  /**
   * Background color (default: #000000)
   */
  backgroundColor?: string;

  /**
   * Visualization style (default: 'line')
   */
  style?: 'line' | 'bars' | 'filled';

  /**
   * Line width in pixels (default: 2)
   */
  lineWidth?: number;

  /**
   * Glow intensity, 0-10 (default: 5)
   */
  glowIntensity?: number;

  /**
   * Enable smooth interpolation (default: true)
   */
  smoothing?: boolean;

  /**
   * Auto-scroll new data (default: true)
   */
  autoScroll?: boolean;

  /**
   * Maximum data points to display (default: 100)
   */
  maxDataPoints?: number;

  /**
   * Minimum Y value (default: auto)
   */
  minValue?: number;

  /**
   * Maximum Y value (default: auto)
   */
  maxValue?: number;

  /**
   * Show background grid (default: false)
   */
  showGrid?: boolean;

  /**
   * Grid color (default: rgba(255, 149, 0, 0.1))
   */
  gridColor?: string;

  /**
   * Show zero baseline (default: true)
   */
  showBaseline?: boolean;

  /**
   * Width of canvas (default: full container width)
   */
  width?: number;

  /**
   * Height of canvas (default: 100)
   */
  height?: number;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Auto-resize with container
   */
  autoResize?: boolean;

  /**
   * Title label
   */
  label?: string;
}

export interface WaveformRef {
  addDataPoint: (value: number) => void;
  setData: (data: number[]) => void;
  clearData: () => void;
}

export const Waveform = forwardRef<WaveformRef, WaveformProps>(
  (
    {
      data = [],
      color = '#ff9500',
      backgroundColor = '#000000',
      style = 'line',
      lineWidth = 2,
      glowIntensity = 5,
      smoothing = true,
      autoScroll = true,
      maxDataPoints = 100,
      minValue,
      maxValue,
      showGrid = false,
      gridColor = 'rgba(255, 149, 0, 0.1)',
      showBaseline = true,
      width,
      height = 100,
      className,
      autoResize = true,
      label,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const animationRef = useRef<WaveformAnimation | null>(null);
    const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });

    // Initialize canvas size
    useEffect(() => {
      if (!containerRef.current) return;

      const updateSize = () => {
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          setCanvasSize({
            width: width || rect.width,
            height: height,
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

      const animation = new WaveformAnimation(canvasRef.current, {
        color,
        backgroundColor,
        style,
        lineWidth,
        glowIntensity,
        smoothing,
        autoScroll,
        maxDataPoints,
        minValue,
        maxValue,
        showGrid,
        gridColor,
        showBaseline,
      });

      // Set initial data
      if (data.length > 0) {
        animation.setData(data);
      }

      animation.start();
      animationRef.current = animation;

      return () => {
        animation.destroy();
        animationRef.current = null;
      };
    }, [canvasSize]); // Only recreate on size change

    // Update config when props change
    useEffect(() => {
      if (animationRef.current) {
        animationRef.current.updateConfig({
          color,
          backgroundColor,
          style,
          lineWidth,
          glowIntensity,
          smoothing,
          autoScroll,
          maxDataPoints,
          minValue,
          maxValue,
          showGrid,
          gridColor,
          showBaseline,
        });
      }
    }, [
      color,
      backgroundColor,
      style,
      lineWidth,
      glowIntensity,
      smoothing,
      autoScroll,
      maxDataPoints,
      minValue,
      maxValue,
      showGrid,
      gridColor,
      showBaseline,
    ]);

    // Update data when prop changes
    useEffect(() => {
      if (animationRef.current && data.length > 0) {
        animationRef.current.setData(data);
      }
    }, [data]);

    // Handle canvas resize
    useEffect(() => {
      if (animationRef.current && canvasSize.width > 0 && canvasSize.height > 0) {
        animationRef.current.resize(canvasSize.width, canvasSize.height);
      }
    }, [canvasSize]);

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      addDataPoint: (value: number) => {
        animationRef.current?.addDataPoint(value);
      },
      setData: (newData: number[]) => {
        animationRef.current?.setData(newData);
      },
      clearData: () => {
        animationRef.current?.clearData();
      },
    }));

    return (
      <div className={`${styles.container} ${className || ''}`}>
        {label && <div className={styles.label}>{label}</div>}
        <div ref={containerRef} className={styles.canvasContainer}>
          <canvas
            ref={canvasRef}
            width={canvasSize.width}
            height={canvasSize.height}
            className={styles.canvas}
          />
        </div>
      </div>
    );
  }
);

Waveform.displayName = 'Waveform';

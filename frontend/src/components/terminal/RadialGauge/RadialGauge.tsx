import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { RadialGaugeAnimation } from '@/animations/RadialGaugeAnimation';
import styles from './RadialGauge.module.css';

export interface RadialGaugeProps {
  /**
   * Current value
   */
  value: number;

  /**
   * Primary color (default: phosphor orange #ff9500)
   */
  color?: string;

  /**
   * Background color (default: #000000)
   */
  backgroundColor?: string;

  /**
   * Display mode (default: 'arc')
   */
  mode?: 'arc' | 'needle' | 'hybrid';

  /**
   * Minimum value (default: 0)
   */
  minValue?: number;

  /**
   * Maximum value (default: 100)
   */
  maxValue?: number;

  /**
   * Start angle in degrees (default: -135)
   */
  startAngle?: number;

  /**
   * End angle in degrees (default: 135)
   */
  endAngle?: number;

  /**
   * Arc/track line width (default: 10)
   */
  lineWidth?: number;

  /**
   * Glow intensity, 0-10 (default: 8)
   */
  glowIntensity?: number;

  /**
   * Show tick marks (default: true)
   */
  showTicks?: boolean;

  /**
   * Number of tick marks (default: 10)
   */
  tickCount?: number;

  /**
   * Show value labels (default: true)
   */
  showLabels?: boolean;

  /**
   * Show current value in center (default: true)
   */
  showValue?: boolean;

  /**
   * Value transition animation speed (default: 0.1)
   */
  animationSpeed?: number;

  /**
   * Background track color
   */
  trackColor?: string;

  /**
   * Critical threshold - turn red above this value
   */
  criticalThreshold?: number;

  /**
   * Warning threshold - turn yellow above this value
   */
  warningThreshold?: number;

  /**
   * Size in pixels (default: 200)
   */
  size?: number;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Label text
   */
  label?: string;

  /**
   * Unit text (e.g., "%", "MB", "°C")
   */
  unit?: string;
}

export interface RadialGaugeRef {
  setValue: (value: number) => void;
  setValueImmediate: (value: number) => void;
}

export const RadialGauge = forwardRef<RadialGaugeRef, RadialGaugeProps>(
  (
    {
      value,
      color = '#ff9500',
      backgroundColor = '#000000',
      mode = 'arc',
      minValue = 0,
      maxValue = 100,
      startAngle = -135,
      endAngle = 135,
      lineWidth = 10,
      glowIntensity = 8,
      showTicks = true,
      tickCount = 10,
      showLabels = true,
      showValue = true,
      animationSpeed = 0.1,
      trackColor = 'rgba(255, 149, 0, 0.2)',
      criticalThreshold,
      warningThreshold,
      size = 200,
      className,
      label,
      unit,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<RadialGaugeAnimation | null>(null);

    // Initialize and start animation
    useEffect(() => {
      if (!canvasRef.current) return;

      const animation = new RadialGaugeAnimation(canvasRef.current, {
        color,
        backgroundColor,
        mode,
        minValue,
        maxValue,
        startAngle,
        endAngle,
        lineWidth,
        glowIntensity,
        showTicks,
        tickCount,
        showLabels,
        showValue,
        animationSpeed,
        trackColor,
        criticalThreshold,
        warningThreshold,
      });

      animation.setValueImmediate(value);
      animation.start();
      animationRef.current = animation;

      return () => {
        animation.destroy();
        animationRef.current = null;
      };
    }, [size]); // Only recreate on size change

    // Update config when props change
    useEffect(() => {
      if (animationRef.current) {
        animationRef.current.updateConfig({
          color,
          backgroundColor,
          mode,
          minValue,
          maxValue,
          startAngle,
          endAngle,
          lineWidth,
          glowIntensity,
          showTicks,
          tickCount,
          showLabels,
          showValue,
          animationSpeed,
          trackColor,
          criticalThreshold,
          warningThreshold,
        });
      }
    }, [
      color,
      backgroundColor,
      mode,
      minValue,
      maxValue,
      startAngle,
      endAngle,
      lineWidth,
      glowIntensity,
      showTicks,
      tickCount,
      showLabels,
      showValue,
      animationSpeed,
      trackColor,
      criticalThreshold,
      warningThreshold,
    ]);

    // Update value when prop changes
    useEffect(() => {
      if (animationRef.current) {
        animationRef.current.setValue(value);
      }
    }, [value]);

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      setValue: (newValue: number) => {
        animationRef.current?.setValue(newValue);
      },
      setValueImmediate: (newValue: number) => {
        animationRef.current?.setValueImmediate(newValue);
      },
    }));

    return (
      <div className={`${styles.container} ${className || ''}`}>
        {label && <div className={styles.label}>{label}</div>}
        <div className={styles.canvasContainer}>
          <canvas
            ref={canvasRef}
            width={size}
            height={size}
            className={styles.canvas}
          />
        </div>
        {unit && <div className={styles.unit}>{unit}</div>}
      </div>
    );
  }
);

RadialGauge.displayName = 'RadialGauge';

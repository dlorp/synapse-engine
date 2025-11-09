/**
 * DotMatrixDisplay.tsx
 *
 * React component for LED dot matrix display with character reveal animation
 * Uses Canvas 2D API for pixel-perfect rendering with phosphor glow
 *
 * Features:
 * - Character-by-character reveal animation
 * - Phosphor orange (#ff9500) LED glow effect
 * - 60fps performance with requestAnimationFrame
 * - Automatic cleanup to prevent memory leaks
 */

import React, { useEffect, useRef } from 'react';
import { DotMatrixAnimation } from '@/animations/DotMatrixAnimation';
import { PatternType } from '@/animations/patterns';
import { EffectType, EffectConfig } from '@/animations/effects';
import { ReactiveConfig } from '@/animations/reactive';
import { calculateTextWidth, calculateTextHeight } from './CharacterMap';
import styles from './DotMatrixDisplay.module.css';

export interface DotMatrixDisplayProps {
  /** Text to display on the LED matrix */
  text: string;
  /** Milliseconds per character reveal (default: 400) */
  revealSpeed?: number;
  /** Loop animation after completion (default: false) */
  loop?: boolean;
  /** Canvas width in pixels (default: auto-calculated from text) */
  width?: number;
  /** Canvas height in pixels (default: auto-calculated) */
  height?: number;
  /** Additional CSS class names */
  className?: string;
  /** Auto-start animation on mount (default: true) */
  autoStart?: boolean;
  /** Animation pattern (default: 'sequential') */
  pattern?: PatternType;
  /** Pixel effects to apply (default: []) */
  effects?: EffectType[];
  /** Effect configuration */
  effectConfig?: EffectConfig;
  /** Reactive state configuration */
  reactive?: ReactiveConfig;
}

// Stable default values to prevent unnecessary re-renders
const DEFAULT_EFFECTS: EffectType[] = [];
const DEFAULT_PATTERN: PatternType = 'sequential';

/**
 * DotMatrixDisplay Component
 *
 * Displays text using a simulated LED dot matrix with character reveal animation.
 * Each character is composed of 5x7 LED pixels with phosphor glow effect.
 *
 * @example
 * ```tsx
 * <DotMatrixDisplay
 *   text="SYNAPSE ENGINE ONLINE"
 *   revealSpeed={400}
 *   loop={false}
 *   pattern="wave"
 *   effects={['blink', 'pulsate']}
 *   reactive={{
 *     enabled: true,
 *     isProcessing: true,
 *   }}
 * />
 * ```
 */
export const DotMatrixDisplay: React.FC<DotMatrixDisplayProps> = ({
  text,
  revealSpeed = 400,
  loop = false,
  width,
  height,
  className,
  autoStart = true,
  pattern = DEFAULT_PATTERN,
  effects = DEFAULT_EFFECTS,
  effectConfig,
  reactive,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<DotMatrixAnimation | null>(null);

  // Calculate dimensions from text if not provided
  const canvasWidth = width || calculateTextWidth(text);
  const canvasHeight = height || calculateTextHeight();

  // Effect 1: Create/recreate animation only when core props change
  // IMPORTANT: reactive is NOT in dependencies to prevent restart on state changes
  useEffect(() => {
    if (!canvasRef.current) return;

    // RESILIENCE CHECK: Skip recreation if animation already exists and is running
    // This prevents StrictMode double-mount from restarting the animation
    if (animationRef.current?.getState().isRunning) {
      return; // Don't recreate, no cleanup needed
    }

    // Create animation instance without reactive (reactive updates separately)
    const animation = new DotMatrixAnimation(canvasRef.current, {
      text,
      revealSpeed,
      loop,
      pattern,
      effects,
      effectConfig,
    });

    animationRef.current = animation;

    // Auto-start if enabled
    if (autoStart) {
      animation.start();
    }

    // Cleanup on unmount
    return () => {
      animation.destroy();
      animationRef.current = null;
    };
  }, [text, revealSpeed, loop, autoStart, pattern, effects, effectConfig]);

  // Effect 2: Update reactive state without recreating animation
  // This allows smooth transitions (IDLE → PROCESSING) without restart
  useEffect(() => {
    if (animationRef.current && reactive) {
      animationRef.current.updateReactiveState(reactive);
    }
  }, [reactive]);

  return (
    <div
      className={`${styles.container} ${className || ''}`}
      role="region"
      aria-label={`LED Display: ${text}`}
    >
      <canvas
        ref={canvasRef}
        width={canvasWidth}
        height={canvasHeight}
        className={styles.canvas}
        aria-hidden="true"
      />
      {/* Screen reader accessible text */}
      <span className={styles.srOnly}>{text}</span>
    </div>
  );
};

/**
 * Controlled variant with exposed animation controls
 */
export interface DotMatrixDisplayControlledProps extends DotMatrixDisplayProps {
  /** Expose animation instance for external control */
  onAnimationReady?: (animation: DotMatrixAnimation) => void;
}

export const DotMatrixDisplayControlled: React.FC<DotMatrixDisplayControlledProps> = ({
  onAnimationReady,
  autoStart = false,
  ...props
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<DotMatrixAnimation | null>(null);

  const canvasWidth = props.width || calculateTextWidth(props.text);
  const canvasHeight = props.height || calculateTextHeight();

  // Use stable defaults for props to prevent unnecessary re-renders
  const pattern = props.pattern || DEFAULT_PATTERN;
  const effects = props.effects || DEFAULT_EFFECTS;

  // Effect 1: Create/recreate animation only when core props change
  // IMPORTANT: props.reactive is NOT in dependencies to prevent restart on state changes
  useEffect(() => {
    if (!canvasRef.current) return;

    // RESILIENCE CHECK: Skip recreation if animation already exists and is running
    // This prevents StrictMode double-mount from restarting the animation
    if (animationRef.current?.getState().isRunning) {
      return; // Don't recreate, no cleanup needed
    }

    const animation = new DotMatrixAnimation(canvasRef.current, {
      text: props.text,
      revealSpeed: props.revealSpeed || 400,
      loop: props.loop || false,
      pattern: pattern,
      effects: effects,
      effectConfig: props.effectConfig,
    });

    animationRef.current = animation;

    if (autoStart) {
      animation.start();
    }

    // Expose animation to parent component
    if (onAnimationReady) {
      onAnimationReady(animation);
    }

    return () => {
      animation.destroy();
      animationRef.current = null;
    };
  }, [props.text, props.revealSpeed, props.loop, pattern, effects, props.effectConfig, autoStart, onAnimationReady]);

  // Effect 2: Update reactive state without recreating animation
  // This allows smooth transitions (IDLE → PROCESSING) without restart
  useEffect(() => {
    if (animationRef.current && props.reactive) {
      animationRef.current.updateReactiveState(props.reactive);
    }
  }, [props.reactive]);

  return (
    <div
      className={`${styles.container} ${props.className || ''}`}
      role="region"
      aria-label={`LED Display: ${props.text}`}
    >
      <canvas
        ref={canvasRef}
        width={canvasWidth}
        height={canvasHeight}
        className={styles.canvas}
        aria-hidden="true"
      />
      <span className={styles.srOnly}>{props.text}</span>
    </div>
  );
};

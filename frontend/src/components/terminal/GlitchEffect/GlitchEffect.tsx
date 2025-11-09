import { useRef, useEffect, useImperativeHandle, forwardRef, useState } from 'react';
import styles from './GlitchEffect.module.css';

export interface GlitchEffectProps {
  /**
   * Width of glitch canvas (default: full container)
   */
  width?: number;

  /**
   * Height of glitch canvas (default: full container)
   */
  height?: number;

  /**
   * Glitch intensity (0-100, default: 50)
   */
  intensity?: number;

  /**
   * Glitch effects to apply
   */
  effects?: {
    rgbSplit?: boolean; // RGB channel separation
    scanlines?: boolean; // Scan line distortion
    blockShift?: boolean; // Random block shifting
    colorNoise?: boolean; // Color noise/static
  };

  /**
   * Auto-trigger interval in ms (0 = manual only, default: 0)
   */
  autoTriggerInterval?: number;

  /**
   * Glitch duration in ms (default: 200)
   */
  duration?: number;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Callback when glitch triggers
   */
  onGlitch?: () => void;

  /**
   * Callback when glitch ends
   */
  onGlitchEnd?: () => void;
}

export interface GlitchEffectRef {
  trigger: () => void;
  stop: () => void;
}

export const GlitchEffect = forwardRef<GlitchEffectRef, GlitchEffectProps>(
  (
    {
      width,
      height,
      intensity = 50,
      effects = {
        rgbSplit: true,
        scanlines: true,
        blockShift: true,
        colorNoise: true,
      },
      autoTriggerInterval = 0,
      duration = 200,
      className,
      onGlitch,
      onGlitchEnd,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isGlitching, setIsGlitching] = useState(false);
    const animationRef = useRef<number | null>(null);
    const intervalRef = useRef<number | null>(null);
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

      const resizeObserver = new ResizeObserver(updateSize);
      resizeObserver.observe(containerRef.current);
      return () => resizeObserver.disconnect();
    }, [width, height]);

    // Apply RGB split effect
    const applyRGBSplit = (imageData: ImageData, offset: number): void => {
      const { data } = imageData;
      const tempData = new Uint8ClampedArray(data);

      for (let i = 0; i < data.length; i += 4) {
        const offsetIndex = i + offset * 4;
        if (offsetIndex < data.length - 4) {
          // Red channel from offset position
          const redValue = tempData[offsetIndex];
          if (redValue !== undefined) data[i] = redValue;
          // Green channel stays
          // Blue channel from negative offset
          const blueOffset = i - offset * 4;
          if (blueOffset >= 0) {
            const blueValue = tempData[blueOffset + 2];
            if (blueValue !== undefined) data[i + 2] = blueValue;
          }
        }
      }
    };

    // Apply scan line distortion
    const applyScanlineDistortion = (
      ctx: CanvasRenderingContext2D,
      w: number,
      h: number
    ): void => {
      const imageData = ctx.getImageData(0, 0, w, h);
      const { data } = imageData;

      for (let y = 0; y < h; y++) {
        if (Math.random() < 0.1) {
          // 10% chance per line
          const shift = Math.floor((Math.random() - 0.5) * intensity * 0.3);
          const row = y * w * 4;

          for (let x = 0; x < w; x++) {
            const srcX = Math.max(0, Math.min(w - 1, x + shift));
            const srcIdx = row + srcX * 4;
            const dstIdx = row + x * 4;

            data[dstIdx] = data[srcIdx] ?? 0;
            data[dstIdx + 1] = data[srcIdx + 1] ?? 0;
            data[dstIdx + 2] = data[srcIdx + 2] ?? 0;
            data[dstIdx + 3] = data[srcIdx + 3] ?? 0;
          }
        }
      }

      ctx.putImageData(imageData, 0, 0);
    };

    // Apply random block shifting
    const applyBlockShift = (
      ctx: CanvasRenderingContext2D,
      w: number,
      h: number
    ): void => {
      const blockCount = Math.floor(5 + (intensity / 100) * 15);

      for (let i = 0; i < blockCount; i++) {
        const blockW = Math.floor(20 + Math.random() * 100);
        const blockH = Math.floor(10 + Math.random() * 50);
        const x = Math.floor(Math.random() * (w - blockW));
        const y = Math.floor(Math.random() * (h - blockH));
        const shiftX = Math.floor((Math.random() - 0.5) * intensity * 0.5);
        const shiftY = Math.floor((Math.random() - 0.5) * intensity * 0.2);

        const imageData = ctx.getImageData(x, y, blockW, blockH);
        ctx.putImageData(imageData, x + shiftX, y + shiftY);
      }
    };

    // Apply color noise
    const applyColorNoise = (
      ctx: CanvasRenderingContext2D,
      w: number,
      h: number
    ): void => {
      const imageData = ctx.getImageData(0, 0, w, h);
      const { data } = imageData;
      const noiseAmount = (intensity / 100) * 0.3;

      for (let i = 0; i < data.length; i += 4) {
        if (Math.random() < noiseAmount) {
          data[i] = Math.random() * 255; // R
          data[i + 1] = Math.random() * 255; // G
          data[i + 2] = Math.random() * 255; // B
        }
      }

      ctx.putImageData(imageData, 0, 0);
    };

    // Trigger glitch effect
    const triggerGlitch = (): void => {
      if (!canvasRef.current || isGlitching) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      setIsGlitching(true);
      onGlitch?.();

      const startTime = performance.now();
      const w = canvas.width;
      const h = canvas.height;

      const animate = (timestamp: number): void => {
        const elapsed = timestamp - startTime;

        if (elapsed >= duration) {
          // Clear canvas and end glitch
          ctx.clearRect(0, 0, w, h);
          setIsGlitching(false);
          onGlitchEnd?.();
          return;
        }

        // Clear and prepare for effects
        ctx.clearRect(0, 0, w, h);

        // Create base noise pattern
        const imageData = ctx.createImageData(w, h);
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
          const value = Math.random() * 50;
          data[i] = value; // R
          data[i + 1] = value; // G
          data[i + 2] = value; // B
          data[i + 3] = 30; // Low alpha for background noise
        }

        ctx.putImageData(imageData, 0, 0);

        // Apply selected effects
        if (effects.rgbSplit) {
          const offset = Math.floor(3 + (intensity / 100) * 10);
          const imageData = ctx.getImageData(0, 0, w, h);
          applyRGBSplit(imageData, offset);
          ctx.putImageData(imageData, 0, 0);
        }

        if (effects.blockShift) {
          applyBlockShift(ctx, w, h);
        }

        if (effects.scanlines) {
          applyScanlineDistortion(ctx, w, h);
        }

        if (effects.colorNoise) {
          applyColorNoise(ctx, w, h);
        }

        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
    };

    // Stop glitch
    const stopGlitch = (): void => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      setIsGlitching(false);

      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
    };

    // Auto-trigger setup
    useEffect(() => {
      if (autoTriggerInterval > 0) {
        intervalRef.current = window.setInterval(() => {
          triggerGlitch();
        }, autoTriggerInterval);

        return () => {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
        };
      }
    }, [autoTriggerInterval, intensity, duration]);

    // Cleanup
    useEffect(() => {
      return () => {
        stopGlitch();
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }, []);

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      trigger: triggerGlitch,
      stop: stopGlitch,
    }));

    return (
      <div
        ref={containerRef}
        className={`${styles.glitchContainer} ${className || ''}`}
        aria-live="polite"
        aria-label="Visual glitch effect"
      >
        <canvas
          ref={canvasRef}
          width={canvasSize.width}
          height={canvasSize.height}
          className={`${styles.glitchCanvas} ${isGlitching ? styles.active : ''}`}
        />
      </div>
    );
  }
);

GlitchEffect.displayName = 'GlitchEffect';

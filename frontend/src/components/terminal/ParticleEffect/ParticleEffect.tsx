import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { ParticleSystem } from '@/animations/ParticleSystem';
import styles from './ParticleEffect.module.css';

interface Vector2D {
  x: number;
  y: number;
}

export interface ParticleEffectProps {
  /**
   * Maximum particles allowed (default: 1000)
   */
  maxParticles?: number;

  /**
   * Background color (default: transparent)
   */
  backgroundColor?: string;

  /**
   * Emitter configuration
   */
  emitter?: {
    type?: 'point' | 'line' | 'area' | 'burst';
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    angle?: number;
    spread?: number;
    rate?: number;
    particlesPerEmit?: number;
    burstSize?: number;
  };

  /**
   * Particle configuration
   */
  particle?: {
    minSize?: number;
    maxSize?: number;
    minSpeed?: number;
    maxSpeed?: number;
    minLife?: number;
    maxLife?: number;
    color?: string | string[];
    startAlpha?: number;
    endAlpha?: number;
    gravity?: Vector2D;
    friction?: number;
    rotation?: boolean;
    rotationSpeed?: number;
    glowIntensity?: number;
  };

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
   * Auto-resize with container
   */
  autoResize?: boolean;

  /**
   * Auto-start on mount (default: true)
   */
  autoStart?: boolean;
}

export interface ParticleEffectRef {
  start: () => void;
  stop: () => void;
  clear: () => void;
  burst: () => void;
  setEmitterPosition: (x: number, y: number) => void;
  addForce: (
    type: 'gravity' | 'wind' | 'attract' | 'repel',
    force: Vector2D,
    x?: number,
    y?: number,
    radius?: number
  ) => void;
  clearForces: () => void;
  getParticleCount: () => number;
}

export const ParticleEffect = forwardRef<ParticleEffectRef, ParticleEffectProps>(
  (
    {
      maxParticles = 1000,
      backgroundColor = 'transparent',
      emitter,
      particle,
      width,
      height,
      className,
      autoResize = true,
      autoStart = true,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const systemRef = useRef<ParticleSystem | null>(null);
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

    // Initialize particle system
    useEffect(() => {
      if (!canvasRef.current || canvasSize.width === 0 || canvasSize.height === 0) {
        return;
      }

      const system = new ParticleSystem(canvasRef.current, {
        maxParticles,
        backgroundColor,
        emitter,
        particle,
      });

      if (autoStart) {
        system.start();
      }

      systemRef.current = system;

      return () => {
        system.destroy();
        systemRef.current = null;
      };
    }, [canvasSize]); // Only recreate on size change

    // Update config when props change
    useEffect(() => {
      if (systemRef.current) {
        systemRef.current.updateConfig({
          maxParticles,
          backgroundColor,
          emitter,
          particle,
        });
      }
    }, [maxParticles, backgroundColor, emitter, particle]);

    // Handle canvas resize
    useEffect(() => {
      if (systemRef.current && canvasSize.width > 0 && canvasSize.height > 0) {
        systemRef.current.resize(canvasSize.width, canvasSize.height);
      }
    }, [canvasSize]);

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      start: () => {
        systemRef.current?.start();
      },
      stop: () => {
        systemRef.current?.stop();
      },
      clear: () => {
        systemRef.current?.clear();
      },
      burst: () => {
        systemRef.current?.burst();
      },
      setEmitterPosition: (x: number, y: number) => {
        systemRef.current?.setEmitterPosition(x, y);
      },
      addForce: (
        type: 'gravity' | 'wind' | 'attract' | 'repel',
        force: Vector2D,
        x?: number,
        y?: number,
        radius?: number
      ) => {
        systemRef.current?.addForce(type, force, x, y, radius);
      },
      clearForces: () => {
        systemRef.current?.clearForces();
      },
      getParticleCount: () => {
        return systemRef.current?.getParticleCount() || 0;
      },
    }));

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
  }
);

ParticleEffect.displayName = 'ParticleEffect';

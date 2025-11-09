/**
 * Wave Ripple Animation
 *
 * Creates expanding circular waves with fade-out effect.
 * Can be triggered by clicks or auto-generate ambient waves.
 *
 * Features:
 * - Multiple concurrent waves
 * - Smooth expansion and fade
 * - Phosphor glow effect
 * - Click-triggered or automatic generation
 * - Performance optimized for 60fps
 */

interface WaveRippleConfig {
  color?: string;
  backgroundColor?: string;
  maxWaves?: number; // Maximum concurrent waves (default: 10)
  waveSpeed?: number; // Expansion speed px/frame (default: 2)
  autoGenerate?: boolean; // Auto-generate waves (default: false)
  autoInterval?: number; // ms between auto waves (default: 2000)
  glowIntensity?: number; // 0-10 (default: 8)
  lineWidth?: number; // Wave line thickness (default: 2)
}

interface Wave {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  alpha: number;
  speed: number;
}

export class WaveRippleAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: Required<WaveRippleConfig>;
  private animationId: number | null = null;
  private waves: Wave[] = [];
  private autoGenerateInterval: number | null = null;
  private clickHandler: ((e: MouseEvent) => void) | null = null;

  constructor(canvas: HTMLCanvasElement, config: WaveRippleConfig = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context not available');
    this.ctx = ctx;

    // Default config
    this.config = {
      color: config.color || '#ff9500',
      backgroundColor: config.backgroundColor || 'transparent',
      maxWaves: config.maxWaves || 10,
      waveSpeed: config.waveSpeed || 2,
      autoGenerate: config.autoGenerate || false,
      autoInterval: config.autoInterval || 2000,
      glowIntensity: config.glowIntensity || 8,
      lineWidth: config.lineWidth || 2,
    };
  }

  /**
   * Create a new wave at specified coordinates
   */
  public createWave(x: number, y: number): void {
    // Calculate max radius (distance to furthest corner)
    const corners = [
      { x: 0, y: 0 },
      { x: this.canvas.width, y: 0 },
      { x: 0, y: this.canvas.height },
      { x: this.canvas.width, y: this.canvas.height },
    ];

    const maxRadius = Math.max(
      ...corners.map((corner) =>
        Math.sqrt(Math.pow(corner.x - x, 2) + Math.pow(corner.y - y, 2))
      )
    );

    // Add wave with slight speed variation
    const speedVariation = 0.8 + Math.random() * 0.4;
    const wave: Wave = {
      x,
      y,
      radius: 0,
      maxRadius: maxRadius * 1.2, // Expand beyond canvas
      alpha: 1,
      speed: this.config.waveSpeed * speedVariation,
    };

    this.waves.push(wave);

    // Remove oldest wave if exceeding max
    if (this.waves.length > this.config.maxWaves) {
      this.waves.shift();
    }
  }

  /**
   * Create wave at random position (for auto-generation)
   */
  private createRandomWave(): void {
    const x = Math.random() * this.canvas.width;
    const y = Math.random() * this.canvas.height;
    this.createWave(x, y);
  }

  /**
   * Draw a single wave
   */
  private drawWave(wave: Wave): void {
    const { color, glowIntensity, lineWidth } = this.config;

    // Set glow effect
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity * wave.alpha;

    // Set stroke style
    this.ctx.strokeStyle = color;
    this.ctx.globalAlpha = wave.alpha;
    this.ctx.lineWidth = lineWidth;

    // Draw circle
    this.ctx.beginPath();
    this.ctx.arc(wave.x, wave.y, wave.radius, 0, Math.PI * 2);
    this.ctx.stroke();

    // Reset
    this.ctx.shadowBlur = 0;
    this.ctx.globalAlpha = 1;
  }

  /**
   * Update wave states and remove completed waves
   */
  private updateWaves(): void {
    this.waves = this.waves.filter((wave) => {
      // Expand radius
      wave.radius += wave.speed;

      // Fade out as wave expands
      const progress = wave.radius / wave.maxRadius;
      wave.alpha = Math.max(0, 1 - progress);

      // Remove if fully faded or beyond max radius
      return wave.alpha > 0.01 && wave.radius < wave.maxRadius;
    });
  }

  /**
   * Render animation frame
   */
  private render(): void {
    // Clear canvas
    if (this.config.backgroundColor === 'transparent') {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    } else {
      this.ctx.fillStyle = this.config.backgroundColor;
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    // Update wave states
    this.updateWaves();

    // Draw all active waves
    this.waves.forEach((wave) => this.drawWave(wave));

    // Continue animation
    this.animationId = requestAnimationFrame(() => this.render());
  }

  /**
   * Enable click-to-create waves
   */
  public enableClickWaves(): void {
    if (this.clickHandler) return; // Already enabled

    this.clickHandler = (e: MouseEvent) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this.createWave(x, y);
    };

    this.canvas.addEventListener('click', this.clickHandler);
    this.canvas.style.cursor = 'pointer';
  }

  /**
   * Disable click-to-create waves
   */
  public disableClickWaves(): void {
    if (this.clickHandler) {
      this.canvas.removeEventListener('click', this.clickHandler);
      this.clickHandler = null;
      this.canvas.style.cursor = 'default';
    }
  }

  /**
   * Start animation and optional auto-generation
   */
  public start(): void {
    if (this.animationId !== null) {
      this.stop();
    }

    // Start render loop
    this.animationId = requestAnimationFrame(() => this.render());

    // Start auto-generation if enabled
    if (this.config.autoGenerate) {
      this.autoGenerateInterval = window.setInterval(() => {
        this.createRandomWave();
      }, this.config.autoInterval);
    }
  }

  /**
   * Stop animation and auto-generation
   */
  public stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }

    if (this.autoGenerateInterval !== null) {
      clearInterval(this.autoGenerateInterval);
      this.autoGenerateInterval = null;
    }
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<WaveRippleConfig>): void {
    const wasAutoGenerating = this.config.autoGenerate;
    this.config = { ...this.config, ...config };

    // Restart auto-generation if settings changed
    if (config.autoGenerate !== undefined || config.autoInterval !== undefined) {
      if (this.autoGenerateInterval !== null) {
        clearInterval(this.autoGenerateInterval);
        this.autoGenerateInterval = null;
      }

      if (this.config.autoGenerate && this.animationId !== null) {
        this.autoGenerateInterval = window.setInterval(() => {
          this.createRandomWave();
        }, this.config.autoInterval);
      }
    }
  }

  /**
   * Resize canvas
   */
  public resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
  }

  /**
   * Clear all waves
   */
  public clear(): void {
    this.waves = [];
  }

  /**
   * Cleanup and destroy
   */
  public destroy(): void {
    this.stop();
    this.disableClickWaves();
    this.waves = [];
  }
}

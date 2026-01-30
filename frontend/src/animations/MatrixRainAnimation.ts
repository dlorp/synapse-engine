/**
 * Matrix Rain Animation
 *
 * Classic falling character effect with phosphor orange aesthetic.
 * Optimized for 60fps performance with canvas rendering.
 *
 * Features:
 * - Multiple vertical columns with independent speeds
 * - Trailing fade effect
 * - Random character selection
 * - Phosphor glow on characters
 */

interface MatrixRainConfig {
  color?: string;
  backgroundColor?: string;
  fontSize?: number;
  speed?: number; // Multiplier for fall speed (default: 1)
  density?: number; // 0-1, how many columns (default: 0.5)
  glowIntensity?: number; // 0-10 (default: 5)
}

interface RainColumn {
  x: number;
  y: number;
  speed: number;
  chars: string[];
}

const MATRIX_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()_+-=[]{}|;:,.<>?';

export class MatrixRainAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: Required<MatrixRainConfig>;
  private animationId: number | null = null;
  private columns: RainColumn[] = [];
  private columnWidth: number;
  private columnCount: number;
  private rowCount: number;

  constructor(canvas: HTMLCanvasElement, config: MatrixRainConfig = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context not available');
    this.ctx = ctx;

    // Default config
    this.config = {
      color: config.color || '#ff9500',
      backgroundColor: config.backgroundColor || '#000000',
      fontSize: config.fontSize || 16,
      speed: config.speed || 1,
      density: config.density || 0.5,
      glowIntensity: config.glowIntensity || 5,
    };

    this.columnWidth = this.config.fontSize;
    this.columnCount = Math.floor(this.canvas.width / this.columnWidth);
    this.rowCount = Math.floor(this.canvas.height / this.config.fontSize);

    this.initializeColumns();
  }

  private initializeColumns(): void {
    this.columns = [];
    const activeColumns = Math.floor(this.columnCount * this.config.density);

    for (let i = 0; i < activeColumns; i++) {
      // Distribute columns evenly with some randomness
      const baseX = (i / activeColumns) * this.columnCount;
      const randomOffset = Math.random() * 2 - 1;
      const columnIndex = Math.floor(baseX + randomOffset);

      this.columns.push({
        x: columnIndex * this.columnWidth,
        y: -Math.random() * this.canvas.height, // Start above canvas
        speed: (0.5 + Math.random() * 1.5) * this.config.speed,
        chars: this.generateCharColumn(),
      });
    }
  }

  private generateCharColumn(): string[] {
    const length = this.rowCount + 10; // Extra for trailing effect
    return Array.from({ length }, () =>
      MATRIX_CHARS[Math.floor(Math.random() * MATRIX_CHARS.length)] ?? 'A'
    );
  }

  private randomizeCharacter(column: RainColumn, index: number): void {
    // Randomly change characters for dynamic effect
    if (Math.random() < 0.05) {
      column.chars[index] = MATRIX_CHARS[Math.floor(Math.random() * MATRIX_CHARS.length)] ?? 'A';
    }
  }

  private drawCharacter(char: string, x: number, y: number, alpha: number): void {
    const { color, fontSize, glowIntensity } = this.config;

    // Set glow effect
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity * alpha;

    // Set text style
    this.ctx.fillStyle = color;
    this.ctx.globalAlpha = alpha;
    this.ctx.font = `${fontSize}px "JetBrains Mono", "Courier New", monospace`;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    // Draw character
    this.ctx.fillText(char, x, y);

    // Reset
    this.ctx.shadowBlur = 0;
    this.ctx.globalAlpha = 1;
  }

  private render(): void {
    // Semi-transparent black for trailing effect
    this.ctx.fillStyle = this.config.backgroundColor + '15'; // 15 = ~8% opacity
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Update and draw each column
    this.columns.forEach((column) => {
      const currentRow = Math.floor(column.y / this.config.fontSize);

      // Draw characters with fade trail
      for (let i = 0; i < 20; i++) {
        const charIndex = currentRow - i;
        if (charIndex >= 0 && charIndex < column.chars.length) {
          const y = charIndex * this.config.fontSize + this.config.fontSize / 2;

          // Fade based on position in trail
          let alpha = 1 - (i / 20);

          // Brightest at the head
          if (i === 0) {
            alpha = 1;
          }

          // Draw if within canvas bounds
          if (y >= 0 && y <= this.canvas.height) {
            this.randomizeCharacter(column, charIndex);
            this.drawCharacter(
              column.chars[charIndex] ?? 'A',
              column.x + this.columnWidth / 2,
              y,
              alpha
            );
          }
        }
      }

      // Move column down
      column.y += column.speed * this.config.speed;

      // Reset column when it goes off screen
      if (column.y > this.canvas.height + this.config.fontSize * 20) {
        column.y = -this.config.fontSize * 10;
        column.chars = this.generateCharColumn();
        column.speed = (0.5 + Math.random() * 1.5) * this.config.speed;
      }
    });

    // Continue animation
    this.animationId = requestAnimationFrame(() => this.render());
  }

  public start(): void {
    if (this.animationId !== null) {
      this.stop();
    }
    this.animationId = requestAnimationFrame(() => this.render());
  }

  public stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  public updateConfig(config: Partial<MatrixRainConfig>): void {
    this.config = { ...this.config, ...config };

    // Recalculate column dimensions if font size changed
    if (config.fontSize) {
      this.columnWidth = this.config.fontSize;
      this.columnCount = Math.floor(this.canvas.width / this.columnWidth);
      this.rowCount = Math.floor(this.canvas.height / this.config.fontSize);
    }

    // Reinitialize columns if density changed
    if (config.density !== undefined) {
      this.initializeColumns();
    }
  }

  public resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
    this.columnCount = Math.floor(width / this.columnWidth);
    this.rowCount = Math.floor(height / this.config.fontSize);
    this.initializeColumns();
  }

  public destroy(): void {
    this.stop();
    this.columns = [];
  }
}

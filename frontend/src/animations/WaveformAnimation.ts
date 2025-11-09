/**
 * Waveform Animation
 *
 * Visualizes time-series data as smooth waveforms.
 * Ideal for displaying metrics like token rate, latency, etc.
 *
 * Features:
 * - Multiple visualization styles (line, bars, filled)
 * - Smooth interpolation between data points
 * - Auto-scrolling for real-time data
 * - Phosphor glow effect
 * - Performance optimized for 60fps
 */

interface WaveformConfig {
  color?: string;
  backgroundColor?: string;
  style?: 'line' | 'bars' | 'filled'; // Visualization style
  lineWidth?: number;
  glowIntensity?: number;
  smoothing?: boolean; // Smooth interpolation (default: true)
  autoScroll?: boolean; // Auto-scroll new data (default: true)
  maxDataPoints?: number; // Maximum data points to display (default: 100)
  minValue?: number; // Minimum Y value (default: auto)
  maxValue?: number; // Maximum Y value (default: auto)
  showGrid?: boolean; // Show background grid (default: false)
  gridColor?: string;
  showBaseline?: boolean; // Show zero baseline (default: true)
}

export class WaveformAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: Required<WaveformConfig>;
  private animationId: number | null = null;
  private dataPoints: number[] = [];
  private scrollOffset: number = 0;

  constructor(canvas: HTMLCanvasElement, config: WaveformConfig = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context not available');
    this.ctx = ctx;

    // Default config
    this.config = {
      color: config.color || '#ff9500',
      backgroundColor: config.backgroundColor || '#000000',
      style: config.style || 'line',
      lineWidth: config.lineWidth || 2,
      glowIntensity: config.glowIntensity || 5,
      smoothing: config.smoothing !== undefined ? config.smoothing : true,
      autoScroll: config.autoScroll !== undefined ? config.autoScroll : true,
      maxDataPoints: config.maxDataPoints || 100,
      minValue: config.minValue !== undefined ? config.minValue : NaN,
      maxValue: config.maxValue !== undefined ? config.maxValue : NaN,
      showGrid: config.showGrid || false,
      gridColor: config.gridColor || 'rgba(255, 149, 0, 0.1)',
      showBaseline: config.showBaseline !== undefined ? config.showBaseline : true,
    };
  }

  /**
   * Add new data point
   */
  public addDataPoint(value: number): void {
    this.dataPoints.push(value);

    // Trim to max data points
    if (this.dataPoints.length > this.config.maxDataPoints) {
      this.dataPoints.shift();
      if (this.config.autoScroll) {
        this.scrollOffset++;
      }
    }
  }

  /**
   * Set all data points at once
   */
  public setData(data: number[]): void {
    this.dataPoints = data.slice(-this.config.maxDataPoints);
    this.scrollOffset = 0;
  }

  /**
   * Clear all data
   */
  public clearData(): void {
    this.dataPoints = [];
    this.scrollOffset = 0;
  }

  /**
   * Get value range from data
   */
  private getValueRange(): { min: number; max: number } {
    if (this.dataPoints.length === 0) {
      return { min: 0, max: 1 };
    }

    const min = isNaN(this.config.minValue)
      ? Math.min(...this.dataPoints, 0)
      : this.config.minValue;
    const max = isNaN(this.config.maxValue)
      ? Math.max(...this.dataPoints, 1)
      : this.config.maxValue;

    return { min, max };
  }

  /**
   * Map data value to canvas Y coordinate
   */
  private valueToY(value: number, min: number, max: number): number {
    const range = max - min;
    const normalized = (value - min) / range;
    return this.canvas.height - normalized * this.canvas.height;
  }

  /**
   * Draw background grid
   */
  private drawGrid(): void {
    if (!this.config.showGrid) return;

    const { gridColor } = this.config;
    const gridLines = 5;

    this.ctx.strokeStyle = gridColor;
    this.ctx.lineWidth = 1;

    // Horizontal grid lines
    for (let i = 0; i <= gridLines; i++) {
      const y = (i / gridLines) * this.canvas.height;
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.canvas.width, y);
      this.ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i <= gridLines; i++) {
      const x = (i / gridLines) * this.canvas.width;
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.canvas.height);
      this.ctx.stroke();
    }
  }

  /**
   * Draw baseline at zero
   */
  private drawBaseline(min: number, max: number): void {
    if (!this.config.showBaseline || min > 0 || max < 0) return;

    const y = this.valueToY(0, min, max);

    this.ctx.strokeStyle = this.config.gridColor;
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([5, 5]);
    this.ctx.beginPath();
    this.ctx.moveTo(0, y);
    this.ctx.lineTo(this.canvas.width, y);
    this.ctx.stroke();
    this.ctx.setLineDash([]);
  }

  /**
   * Draw waveform as line
   */
  private drawLineWaveform(min: number, max: number): void {
    if (this.dataPoints.length < 2) return;

    const { color, lineWidth, glowIntensity } = this.config;
    const pointSpacing = this.canvas.width / (this.config.maxDataPoints - 1);

    // Set glow
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity;

    // Set stroke
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.lineJoin = 'round';
    this.ctx.lineCap = 'round';

    this.ctx.beginPath();

    // Draw smooth curve through points
    for (let i = 0; i < this.dataPoints.length; i++) {
      const x = i * pointSpacing;
      const y = this.valueToY(this.dataPoints[i], min, max);

      if (i === 0) {
        this.ctx.moveTo(x, y);
      } else if (this.config.smoothing && i < this.dataPoints.length - 1) {
        // Smooth curve using quadratic bezier
        const prevX = (i - 1) * pointSpacing;
        const prevY = this.valueToY(this.dataPoints[i - 1], min, max);
        const midX = (prevX + x) / 2;
        const midY = (prevY + y) / 2;
        this.ctx.quadraticCurveTo(prevX, prevY, midX, midY);
      } else {
        this.ctx.lineTo(x, y);
      }
    }

    this.ctx.stroke();
    this.ctx.shadowBlur = 0;
  }

  /**
   * Draw waveform as bars
   */
  private drawBarsWaveform(min: number, max: number): void {
    if (this.dataPoints.length === 0) return;

    const { color, glowIntensity } = this.config;
    const barWidth = this.canvas.width / this.config.maxDataPoints;
    const zeroY = this.valueToY(0, min, max);

    // Set glow
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity;

    this.ctx.fillStyle = color;

    for (let i = 0; i < this.dataPoints.length; i++) {
      const x = i * barWidth;
      const y = this.valueToY(this.dataPoints[i], min, max);
      const barHeight = Math.abs(zeroY - y);

      this.ctx.fillRect(x, Math.min(y, zeroY), barWidth * 0.8, barHeight);
    }

    this.ctx.shadowBlur = 0;
  }

  /**
   * Draw filled waveform
   */
  private drawFilledWaveform(min: number, max: number): void {
    if (this.dataPoints.length < 2) return;

    const { color, glowIntensity } = this.config;
    const pointSpacing = this.canvas.width / (this.config.maxDataPoints - 1);
    const bottomY = this.canvas.height;

    // Create gradient fill
    const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
    gradient.addColorStop(0, color);
    gradient.addColorStop(1, color + '20'); // 20 = ~12% opacity

    this.ctx.fillStyle = gradient;
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity;

    this.ctx.beginPath();
    this.ctx.moveTo(0, bottomY);

    // Draw top edge
    for (let i = 0; i < this.dataPoints.length; i++) {
      const x = i * pointSpacing;
      const y = this.valueToY(this.dataPoints[i], min, max);

      if (i === 0) {
        this.ctx.lineTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    }

    // Close path at bottom
    this.ctx.lineTo(
      (this.dataPoints.length - 1) * pointSpacing,
      bottomY
    );
    this.ctx.closePath();
    this.ctx.fill();

    this.ctx.shadowBlur = 0;
  }

  /**
   * Render frame
   */
  private render(): void {
    // Clear canvas
    this.ctx.fillStyle = this.config.backgroundColor;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Get value range
    const { min, max } = this.getValueRange();

    // Draw grid
    this.drawGrid();

    // Draw baseline
    this.drawBaseline(min, max);

    // Draw waveform based on style
    switch (this.config.style) {
      case 'line':
        this.drawLineWaveform(min, max);
        break;
      case 'bars':
        this.drawBarsWaveform(min, max);
        break;
      case 'filled':
        this.drawFilledWaveform(min, max);
        break;
    }

    // Continue animation
    this.animationId = requestAnimationFrame(() => this.render());
  }

  /**
   * Start animation
   */
  public start(): void {
    if (this.animationId !== null) {
      this.stop();
    }
    this.animationId = requestAnimationFrame(() => this.render());
  }

  /**
   * Stop animation
   */
  public stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<WaveformConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Resize canvas
   */
  public resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.stop();
    this.dataPoints = [];
  }
}

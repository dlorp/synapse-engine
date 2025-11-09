/**
 * Radial Gauge Animation
 *
 * Circular gauge display for metrics and percentages.
 * Similar to speedometer or progress circle.
 *
 * Features:
 * - Configurable value range
 * - Smooth value transitions
 * - Multiple display modes (arc, needle, hybrid)
 * - Tick marks and labels
 * - Phosphor glow effect
 * - Performance optimized for 60fps
 */

interface RadialGaugeConfig {
  color?: string;
  backgroundColor?: string;
  mode?: 'arc' | 'needle' | 'hybrid'; // Display mode
  minValue?: number; // Minimum value (default: 0)
  maxValue?: number; // Maximum value (default: 100)
  startAngle?: number; // Start angle in degrees (default: -135)
  endAngle?: number; // End angle in degrees (default: 135)
  lineWidth?: number; // Arc/track width (default: 10)
  glowIntensity?: number; // 0-10 (default: 8)
  showTicks?: boolean; // Show tick marks (default: true)
  tickCount?: number; // Number of ticks (default: 10)
  showLabels?: boolean; // Show value labels (default: true)
  showValue?: boolean; // Show current value in center (default: true)
  animationSpeed?: number; // Value transition speed (default: 0.1)
  trackColor?: string; // Background track color
  criticalThreshold?: number; // Turn red above this value (optional)
  warningThreshold?: number; // Turn yellow above this value (optional)
}

export class RadialGaugeAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: Required<RadialGaugeConfig>;
  private animationId: number | null = null;
  private currentValue: number = 0;
  private targetValue: number = 0;
  private centerX: number;
  private centerY: number;
  private radius: number;

  constructor(canvas: HTMLCanvasElement, config: RadialGaugeConfig = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context not available');
    this.ctx = ctx;

    // Default config
    this.config = {
      color: config.color || '#ff9500',
      backgroundColor: config.backgroundColor || '#000000',
      mode: config.mode || 'arc',
      minValue: config.minValue !== undefined ? config.minValue : 0,
      maxValue: config.maxValue !== undefined ? config.maxValue : 100,
      startAngle: config.startAngle !== undefined ? config.startAngle : -135,
      endAngle: config.endAngle !== undefined ? config.endAngle : 135,
      lineWidth: config.lineWidth || 10,
      glowIntensity: config.glowIntensity || 8,
      showTicks: config.showTicks !== undefined ? config.showTicks : true,
      tickCount: config.tickCount || 10,
      showLabels: config.showLabels !== undefined ? config.showLabels : true,
      showValue: config.showValue !== undefined ? config.showValue : true,
      animationSpeed: config.animationSpeed || 0.1,
      trackColor: config.trackColor || 'rgba(255, 149, 0, 0.2)',
      criticalThreshold: config.criticalThreshold !== undefined ? config.criticalThreshold : Infinity,
      warningThreshold: config.warningThreshold !== undefined ? config.warningThreshold : Infinity,
    };

    this.centerX = this.canvas.width / 2;
    this.centerY = this.canvas.height / 2;
    this.radius = Math.min(this.centerX, this.centerY) - this.config.lineWidth - 20;
  }

  /**
   * Set target value (will animate to this value)
   */
  public setValue(value: number): void {
    this.targetValue = Math.max(
      this.config.minValue,
      Math.min(this.config.maxValue, value)
    );
  }

  /**
   * Set value immediately without animation
   */
  public setValueImmediate(value: number): void {
    this.targetValue = Math.max(
      this.config.minValue,
      Math.min(this.config.maxValue, value)
    );
    this.currentValue = this.targetValue;
  }

  /**
   * Convert degrees to radians
   */
  private degToRad(degrees: number): number {
    return (degrees * Math.PI) / 180;
  }

  /**
   * Map value to angle
   */
  private valueToAngle(value: number): number {
    const { minValue, maxValue, startAngle, endAngle } = this.config;
    const range = maxValue - minValue;
    const angleRange = endAngle - startAngle;
    const normalized = (value - minValue) / range;
    return startAngle + normalized * angleRange;
  }

  /**
   * Get color based on thresholds
   */
  private getColorForValue(value: number): string {
    if (value >= this.config.criticalThreshold) {
      return '#ff0000'; // Red
    }
    if (value >= this.config.warningThreshold) {
      return '#ffaa00'; // Amber
    }
    return this.config.color;
  }

  /**
   * Draw background track
   */
  private drawTrack(): void {
    const { startAngle, endAngle, lineWidth, trackColor } = this.config;

    this.ctx.strokeStyle = trackColor;
    this.ctx.lineWidth = lineWidth;
    this.ctx.lineCap = 'round';

    this.ctx.beginPath();
    this.ctx.arc(
      this.centerX,
      this.centerY,
      this.radius,
      this.degToRad(startAngle),
      this.degToRad(endAngle)
    );
    this.ctx.stroke();
  }

  /**
   * Draw tick marks
   */
  private drawTicks(): void {
    if (!this.config.showTicks) return;

    const { startAngle, endAngle, tickCount } = this.config;
    const angleRange = endAngle - startAngle;
    const angleStep = angleRange / tickCount;

    this.ctx.strokeStyle = this.config.color;
    this.ctx.lineWidth = 2;

    for (let i = 0; i <= tickCount; i++) {
      const angle = this.degToRad(startAngle + i * angleStep);
      const innerRadius = this.radius - 5;
      const outerRadius = this.radius + 5;

      const x1 = this.centerX + Math.cos(angle) * innerRadius;
      const y1 = this.centerY + Math.sin(angle) * innerRadius;
      const x2 = this.centerX + Math.cos(angle) * outerRadius;
      const y2 = this.centerY + Math.sin(angle) * outerRadius;

      this.ctx.beginPath();
      this.ctx.moveTo(x1, y1);
      this.ctx.lineTo(x2, y2);
      this.ctx.stroke();
    }
  }

  /**
   * Draw value labels
   */
  private drawLabels(): void {
    if (!this.config.showLabels) return;

    const { startAngle, endAngle, minValue, maxValue, tickCount } = this.config;
    const angleRange = endAngle - startAngle;
    const angleStep = angleRange / tickCount;
    const valueStep = (maxValue - minValue) / tickCount;

    this.ctx.fillStyle = this.config.color;
    this.ctx.font = '10px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    for (let i = 0; i <= tickCount; i++) {
      const angle = this.degToRad(startAngle + i * angleStep);
      const value = Math.round(minValue + i * valueStep);
      const labelRadius = this.radius + 15;

      const x = this.centerX + Math.cos(angle) * labelRadius;
      const y = this.centerY + Math.sin(angle) * labelRadius;

      this.ctx.fillText(value.toString(), x, y);
    }
  }

  /**
   * Draw value arc
   */
  private drawArc(): void {
    const { startAngle, lineWidth, glowIntensity } = this.config;
    const currentAngle = this.valueToAngle(this.currentValue);
    const color = this.getColorForValue(this.currentValue);

    // Set glow
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = glowIntensity;

    // Draw arc
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.lineCap = 'round';

    this.ctx.beginPath();
    this.ctx.arc(
      this.centerX,
      this.centerY,
      this.radius,
      this.degToRad(startAngle),
      this.degToRad(currentAngle)
    );
    this.ctx.stroke();

    this.ctx.shadowBlur = 0;
  }

  /**
   * Draw needle
   */
  private drawNeedle(): void {
    const currentAngle = this.valueToAngle(this.currentValue);
    const color = this.getColorForValue(this.currentValue);

    // Set glow
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = this.config.glowIntensity;

    // Draw needle
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 3;
    this.ctx.lineCap = 'round';

    const angle = this.degToRad(currentAngle);
    const needleLength = this.radius - 10;
    const x = this.centerX + Math.cos(angle) * needleLength;
    const y = this.centerY + Math.sin(angle) * needleLength;

    this.ctx.beginPath();
    this.ctx.moveTo(this.centerX, this.centerY);
    this.ctx.lineTo(x, y);
    this.ctx.stroke();

    // Draw center circle
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(this.centerX, this.centerY, 5, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.shadowBlur = 0;
  }

  /**
   * Draw center value display
   */
  private drawValueDisplay(): void {
    if (!this.config.showValue) return;

    const color = this.getColorForValue(this.currentValue);
    const displayValue = Math.round(this.currentValue);

    this.ctx.fillStyle = color;
    this.ctx.font = 'bold 24px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = 5;

    this.ctx.fillText(displayValue.toString(), this.centerX, this.centerY + 30);

    this.ctx.shadowBlur = 0;
  }

  /**
   * Update current value (smooth transition)
   */
  private updateValue(): void {
    const diff = this.targetValue - this.currentValue;
    if (Math.abs(diff) > 0.1) {
      this.currentValue += diff * this.config.animationSpeed;
    } else {
      this.currentValue = this.targetValue;
    }
  }

  /**
   * Render frame
   */
  private render(): void {
    // Clear canvas
    this.ctx.fillStyle = this.config.backgroundColor;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Update value with smooth transition
    this.updateValue();

    // Draw components
    this.drawTrack();
    this.drawTicks();
    this.drawLabels();

    // Draw value based on mode
    switch (this.config.mode) {
      case 'arc':
        this.drawArc();
        break;
      case 'needle':
        this.drawNeedle();
        break;
      case 'hybrid':
        this.drawArc();
        this.drawNeedle();
        break;
    }

    this.drawValueDisplay();

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
  public updateConfig(config: Partial<RadialGaugeConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Resize canvas and recalculate dimensions
   */
  public resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
    this.centerX = width / 2;
    this.centerY = height / 2;
    this.radius = Math.min(this.centerX, this.centerY) - this.config.lineWidth - 20;
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.stop();
  }
}

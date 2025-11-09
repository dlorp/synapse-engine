/**
 * DotMatrixAnimation.ts
 *
 * Canvas-based animation class for LED dot matrix display
 * Handles character-by-character reveal with phosphor glow effect
 * Performance: 60fps with requestAnimationFrame
 */

import { LED_CONFIG, getCharacterPattern } from '@/components/terminal/DotMatrixDisplay/CharacterMap';
import { PatternCalculator, PatternType } from './patterns';
import { EffectProcessor, EffectType, EffectConfig } from './effects';
import { ReactiveStateManager, ReactiveConfig } from './reactive';

export interface AnimationConfig {
  text: string;
  revealSpeed: number; // milliseconds per character
  loop: boolean;
  pattern?: PatternType; // Animation pattern (default: 'sequential')
  effects?: EffectType[]; // Pixel effects (default: [])
  effectConfig?: EffectConfig; // Effect configuration
  reactive?: ReactiveConfig; // Reactive state configuration
}

export class DotMatrixAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private config: AnimationConfig;
  private animationId: number | null = null;
  private currentCharIndex: number = 0;
  private startTime: number = 0;
  private isDestroyed: boolean = false;

  // Pixel-level animation tracking
  private pixelsPerChar: number = 35; // 5×7 grid
  private msPerPixel: number = 15;    // ~15ms per pixel = ~0.5s per character
  private cumulativePixelOffsets: number[] = []; // Cumulative pixel positions per character

  // Pattern system
  private pattern: PatternType;
  private patternCalculator: PatternCalculator;

  // Effect system
  private effects: EffectType[];
  private effectProcessor: EffectProcessor;

  // Reactive system
  private reactiveStateManager: ReactiveStateManager;
  private reactiveConfig: ReactiveConfig | null = null;
  private reactiveUpdateDebounce: number | null = null;

  constructor(canvas: HTMLCanvasElement, config: AnimationConfig) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Canvas 2D context not available');
    }
    this.ctx = ctx;
    this.config = config;

    // Initialize reactive state manager
    this.reactiveStateManager = new ReactiveStateManager();

    // Set base pattern from config (used as fallback for reactive states)
    this.pattern = config.pattern || 'sequential';

    // Apply reactive state if enabled
    if (config.reactive?.enabled) {
      const reactiveState = this.reactiveStateManager.getStateConfig(
        config.reactive,
        this.pattern // Pass base pattern to reactive state manager
      );
      this.pattern = reactiveState.pattern;
      this.effects = reactiveState.effects;
      this.reactiveConfig = config.reactive;
    } else {
      this.effects = config.effects || [];
    }

    // Initialize pattern calculator
    this.patternCalculator = new PatternCalculator();
    this.patternCalculator.preCalculatePattern(this.pattern, config.text.length);

    // Initialize effect processor
    this.effectProcessor = new EffectProcessor(config.effectConfig);

    // Calculate cumulative pixel offsets for each character (spaces use fewer pixels)
    this.calculateCumulativeOffsets();

    // Disable image smoothing for crisp LED pixels
    this.ctx.imageSmoothingEnabled = false;
  }

  /**
   * Get effective pixel count for a character
   * Space characters use minimal pixels to avoid animation pause
   */
  private getEffectivePixelCount(char: string): number {
    return char === ' ' ? 3 : this.pixelsPerChar; // Spaces use only 3 pixels worth of time
  }

  /**
   * Calculate cumulative pixel offsets for each character
   * This allows spaces to animate faster while maintaining proper timing
   */
  private calculateCumulativeOffsets(): void {
    this.cumulativePixelOffsets = [];
    let cumulative = 0;

    for (let i = 0; i < this.config.text.length; i++) {
      this.cumulativePixelOffsets.push(cumulative);
      cumulative += this.getEffectivePixelCount(this.config.text[i]);
    }
  }

  /**
   * Draw a single LED pixel with phosphor glow
   * Renders as circular LED for classic dot matrix aesthetic
   */
  private drawLEDPixel(x: number, y: number, intensity: number, shadowBlur: number): void {
    const { pixelSize, color } = LED_CONFIG;

    // Apply phosphor glow effect with custom shadow blur
    this.ctx.shadowColor = color;
    this.ctx.shadowBlur = shadowBlur;
    this.ctx.fillStyle = color;
    this.ctx.globalAlpha = intensity;

    // Draw LED dot as a filled circle (classic LED aesthetic)
    const centerX = x + pixelSize / 2;
    const centerY = y + pixelSize / 2;
    const radius = pixelSize / 2;

    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    this.ctx.fill();

    // Reset shadow and alpha
    this.ctx.shadowBlur = 0;
    this.ctx.globalAlpha = 1;
  }

  /**
   * Calculate intensity and shadow blur for a specific pixel
   * Uses pattern calculator and effect processor
   */
  private getPixelProperties(
    charIndex: number,
    row: number,
    col: number,
    isPixelOn: boolean,
    elapsed: number
  ): { intensity: number; shadowBlur: number } {
    const { backgroundIntensity, glowIntensity } = LED_CONFIG;

    // If pixel is "off" in character pattern, always show dim background
    if (!isPixelOn) {
      return {
        intensity: backgroundIntensity,
        shadowBlur: glowIntensity * backgroundIntensity,
      };
    }

    // Get the cumulative pixel offset for this character
    const charOffset = this.cumulativePixelOffsets[charIndex] || 0;

    // Calculate pixel timing using pattern calculator with character offset
    const { startTime: pixelStartTime, endTime: pixelEndTime } =
      this.patternCalculator.calculatePixelTiming(
        charIndex,
        row,
        col,
        this.pattern,
        this.msPerPixel
      );

    // Adjust timing based on cumulative offset (accounts for space compression)
    const adjustedStartTime = charOffset * this.msPerPixel + (pixelStartTime - charIndex * this.pixelsPerChar * this.msPerPixel);
    const adjustedEndTime = charOffset * this.msPerPixel + (pixelEndTime - charIndex * this.pixelsPerChar * this.msPerPixel);

    // Calculate base intensity
    let baseIntensity: number;
    const pixelElapsed = elapsed - adjustedStartTime;
    const isFullyLit = elapsed >= adjustedEndTime;

    if (elapsed < adjustedStartTime) {
      // Pixel hasn't started yet
      baseIntensity = backgroundIntensity;
    } else if (isFullyLit) {
      // Pixel is fully illuminated
      baseIntensity = 1.0;
    } else {
      // Pixel is currently illuminating - fade in
      const fadeProgress = pixelElapsed / this.msPerPixel;
      baseIntensity = backgroundIntensity + (1.0 - backgroundIntensity) * fadeProgress;
    }

    // Calculate base shadow blur
    const baseShadowBlur = glowIntensity * baseIntensity;

    // Apply effects if any
    if (this.effects.length === 0) {
      return { intensity: baseIntensity, shadowBlur: baseShadowBlur };
    }

    return this.effectProcessor.applyEffects(
      baseIntensity,
      baseShadowBlur,
      elapsed,
      pixelElapsed,
      this.msPerPixel,
      isFullyLit,
      this.effects
    );
  }

  /**
   * Draw a complete character at the specified position
   * Renders full 5×7 grid with pixel-by-pixel animation
   */
  private drawCharacter(
    char: string,
    charIndex: number,
    startX: number,
    startY: number,
    elapsed: number
  ): void {
    const pattern = getCharacterPattern(char);
    const { pixelSize, pixelGap } = LED_CONFIG;

    for (let row = 0; row < pattern.length; row++) {
      const rowPattern = pattern[row];
      if (!rowPattern) continue;

      for (let col = 0; col < rowPattern.length; col++) {
        const x = startX + col * (pixelSize + pixelGap);
        const y = startY + row * (pixelSize + pixelGap);

        // Calculate pixel properties (intensity and shadow blur) with effects
        const { intensity, shadowBlur } = this.getPixelProperties(
          charIndex,
          row,
          col,
          rowPattern[col],
          elapsed
        );

        this.drawLEDPixel(x, y, intensity, shadowBlur);
      }
    }
  }

  /**
   * Main render loop - called by requestAnimationFrame
   * Uses pixel-level animation for sequential LED illumination
   */
  private render(timestamp: number): void {
    if (this.isDestroyed) return;

    // Initialize start time on first frame
    if (!this.startTime) {
      this.startTime = timestamp;
    }

    const elapsed = timestamp - this.startTime;

    // Clear canvas with black background
    this.ctx.fillStyle = '#000000';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Calculate positioning
    const { charWidth, charSpacing, pixelSize, pixelGap } = LED_CONFIG;
    const charTotalWidth = charWidth * (pixelSize + pixelGap) + charSpacing * (pixelSize + pixelGap);

    // Calculate which character is currently being animated
    const totalPixelsRevealed = Math.floor(elapsed / this.msPerPixel);
    const currentCharByPixel = Math.floor(totalPixelsRevealed / this.pixelsPerChar);
    this.currentCharIndex = Math.min(currentCharByPixel + 1, this.config.text.length);

    // Draw all characters up to current position (with pixel-level animation)
    for (let i = 0; i < this.config.text.length; i++) {
      const char = this.config.text[i];
      if (!char) continue; // Skip if character is undefined

      const x = 20 + i * charTotalWidth; // 20px left padding
      const y = 20; // 20px top padding

      // Draw character with pixel-by-pixel animation
      this.drawCharacter(char, i, x, y, elapsed);
    }

    // Calculate total animation duration using effective pixels (accounts for space compression)
    const lastCharIndex = this.config.text.length - 1;
    const totalPixels = lastCharIndex >= 0
      ? this.cumulativePixelOffsets[lastCharIndex] + this.getEffectivePixelCount(this.config.text[lastCharIndex])
      : 0;
    const totalDuration = totalPixels * this.msPerPixel;

    // Continue animation or loop
    if (elapsed < totalDuration) {
      // Still animating pixels
      this.animationId = requestAnimationFrame((ts) => this.render(ts));
    } else if (this.config.loop) {
      // All pixels revealed - restart if looping
      this.startTime = 0;
      this.currentCharIndex = 0;
      this.animationId = requestAnimationFrame((ts) => this.render(ts));
    } else if (this.effects.length > 0) {
      // Animation complete but effects need to continue animating
      this.animationId = requestAnimationFrame((ts) => this.render(ts));
    }
  }

  /**
   * Start the animation
   */
  public start(): void {
    if (this.isDestroyed) {
      console.warn('Cannot start destroyed animation');
      return;
    }

    this.stop(); // Stop any existing animation
    this.startTime = 0;
    this.currentCharIndex = 0;
    this.animationId = requestAnimationFrame((ts) => this.render(ts));
  }

  /**
   * Stop the animation (pause at current frame)
   */
  public stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /**
   * Reset animation to initial state
   */
  public reset(): void {
    this.stop();
    this.startTime = 0;
    this.currentCharIndex = 0;

    // Clear canvas
    this.ctx.fillStyle = '#000000';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * Update animation configuration
   */
  public updateConfig(config: Partial<AnimationConfig>): void {
    const shouldRestart = this.animationId !== null;

    // Update config
    this.config = { ...this.config, ...config };

    // Handle reactive state updates separately
    if (config.reactive !== undefined) {
      this.updateReactiveState(config.reactive);
      return; // Reactive updates handle restart internally
    }

    // Recalculate cumulative offsets if text changed
    if (config.text !== undefined) {
      this.calculateCumulativeOffsets();
    }

    // Update pattern if changed
    if (config.pattern && config.pattern !== this.pattern) {
      this.pattern = config.pattern;
      this.patternCalculator.clearCache();
      this.patternCalculator.preCalculatePattern(this.pattern, this.config.text.length);
    }

    // Update effects if changed
    if (config.effects !== undefined) {
      this.effects = config.effects;
    }

    // Update effect config if changed
    if (config.effectConfig) {
      this.effectProcessor.updateConfig(config.effectConfig);
    }

    if (shouldRestart) {
      this.start();
    }
  }

  /**
   * Update reactive state configuration
   * Smoothly transitions between states with debouncing
   */
  public updateReactiveState(config: ReactiveConfig): void {
    // Clear existing debounce timer
    if (this.reactiveUpdateDebounce !== null) {
      window.clearTimeout(this.reactiveUpdateDebounce);
    }

    // Debounce rapid state changes (100ms)
    this.reactiveUpdateDebounce = window.setTimeout(() => {
      // Check if state has actually changed
      if (
        this.reactiveConfig &&
        !this.reactiveStateManager.hasStateChanged(this.reactiveConfig, config)
      ) {
        return;
      }

      // Get new reactive state (pass base pattern from config)
      const basePattern = this.config.pattern || 'sequential';
      const oldState = this.reactiveConfig
        ? this.reactiveStateManager.getStateConfig(this.reactiveConfig, basePattern)
        : { pattern: this.pattern, effects: this.effects };
      const newState = this.reactiveStateManager.getStateConfig(config, basePattern);

      // Update reactive config
      this.reactiveConfig = config;

      // Check if animation should restart
      const shouldRestart =
        this.animationId !== null &&
        this.reactiveStateManager.shouldRestartAnimation(oldState, newState);

      // Update pattern and effects
      if (newState.pattern !== this.pattern) {
        this.pattern = newState.pattern;
        this.patternCalculator.clearCache();
        this.patternCalculator.preCalculatePattern(this.pattern, this.config.text.length);
      }

      this.effects = newState.effects;

      // Restart animation if needed
      if (shouldRestart) {
        this.start();
      }

      this.reactiveUpdateDebounce = null;
    }, 100);
  }

  /**
   * Cleanup and destroy animation
   * MUST be called on component unmount to prevent memory leaks
   */
  public destroy(): void {
    this.stop();
    this.isDestroyed = true;

    // Clear reactive debounce timer
    if (this.reactiveUpdateDebounce !== null) {
      window.clearTimeout(this.reactiveUpdateDebounce);
      this.reactiveUpdateDebounce = null;
    }

    // Clear pattern cache
    this.patternCalculator.clearCache();

    // Clear canvas
    this.ctx.fillStyle = '#000000';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * Get current animation state
   */
  public getState(): {
    isRunning: boolean;
    currentCharIndex: number;
    totalChars: number;
    progress: number;
  } {
    return {
      isRunning: this.animationId !== null,
      currentCharIndex: this.currentCharIndex,
      totalChars: this.config.text.length,
      progress: this.config.text.length > 0
        ? this.currentCharIndex / this.config.text.length
        : 0,
    };
  }
}

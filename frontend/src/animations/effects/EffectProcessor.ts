/**
 * effects/EffectProcessor.ts
 *
 * Processes pixel effects to modify intensity and glow
 * Effects can be combined and applied during different animation phases
 */

import { EffectType, EffectResult, EffectConfig, DEFAULT_EFFECT_CONFIG } from './types';

export class EffectProcessor {
  private config: Required<EffectConfig>;

  constructor(config?: EffectConfig) {
    this.config = { ...DEFAULT_EFFECT_CONFIG, ...config };
  }

  /**
   * Apply all effects to a pixel
   *
   * @param baseIntensity - Base pixel intensity (0-1)
   * @param baseShadowBlur - Base glow blur radius
   * @param elapsed - Total time elapsed since animation start (ms)
   * @param pixelElapsed - Time elapsed since pixel started animating (ms)
   * @param msPerPixel - Duration of pixel fade-in (ms)
   * @param isFullyLit - Whether pixel has completed fade-in
   * @param effects - Array of effects to apply
   * @returns Modified intensity and shadow blur
   */
  applyEffects(
    baseIntensity: number,
    baseShadowBlur: number,
    elapsed: number,
    pixelElapsed: number,
    msPerPixel: number,
    isFullyLit: boolean,
    effects: EffectType[]
  ): EffectResult {
    let intensity = baseIntensity;
    let shadowBlur = baseShadowBlur;

    for (const effect of effects) {
      const result = this.applyEffect(
        effect,
        intensity,
        shadowBlur,
        elapsed,
        pixelElapsed,
        msPerPixel,
        isFullyLit
      );
      intensity = result.intensity;
      shadowBlur = result.shadowBlur;
    }

    return { intensity, shadowBlur };
  }

  /**
   * Apply a single effect
   */
  private applyEffect(
    effect: EffectType,
    intensity: number,
    shadowBlur: number,
    elapsed: number,
    pixelElapsed: number,
    msPerPixel: number,
    isFullyLit: boolean
  ): EffectResult {
    switch (effect) {
      case 'blink':
        return this.blinkEffect(intensity, shadowBlur, pixelElapsed, msPerPixel);

      case 'pulsate':
        return this.pulsateEffect(intensity, shadowBlur, elapsed, pixelElapsed, msPerPixel, isFullyLit);

      case 'flicker':
        return this.flickerEffect(intensity, shadowBlur);

      case 'glow-pulse':
        return this.glowPulseEffect(intensity, shadowBlur, elapsed);

      default:
        return { intensity, shadowBlur };
    }
  }

  /**
   * BLINK: Rapid on/off during fade-in phase
   * Only applies while pixel is fading in
   */
  private blinkEffect(
    intensity: number,
    shadowBlur: number,
    pixelElapsed: number,
    msPerPixel: number
  ): EffectResult {
    // Only blink during fade-in phase
    if (pixelElapsed >= msPerPixel) {
      return { intensity, shadowBlur };
    }

    const blinkPeriod = 1000 / this.config.blinkFrequency; // 20ms for 50Hz
    const blinkPhase = (pixelElapsed % blinkPeriod) / blinkPeriod;
    const blink = blinkPhase < 0.5 ? 1.0 : 0.3;

    return {
      intensity: intensity * blink,
      shadowBlur: shadowBlur * blink,
    };
  }

  /**
   * PULSATE: Gentle breathing effect after fully lit
   * Only applies after pixel is fully illuminated
   */
  private pulsateEffect(
    intensity: number,
    shadowBlur: number,
    elapsed: number,
    pixelElapsed: number,
    msPerPixel: number,
    isFullyLit: boolean
  ): EffectResult {
    // Only pulsate after fully lit
    if (!isFullyLit) {
      return { intensity, shadowBlur };
    }

    const time = elapsed - (elapsed - pixelElapsed + msPerPixel);
    const pulse = 0.85 + 0.15 * Math.sin(time * 2 * Math.PI / this.config.pulsePeriod);

    return {
      intensity: intensity * pulse,
      shadowBlur,
    };
  }

  /**
   * FLICKER: Random intensity variations (continuous)
   * Simulates unstable power supply
   */
  private flickerEffect(
    intensity: number,
    shadowBlur: number
  ): EffectResult {
    const noise = 1.0 - this.config.flickerIntensity + Math.random() * (this.config.flickerIntensity * 2);

    return {
      intensity: intensity * noise,
      shadowBlur,
    };
  }

  /**
   * GLOW_PULSE: Oscillating glow intensity (continuous)
   * Modifies shadow blur for pulsing glow effect
   */
  private glowPulseEffect(
    intensity: number,
    shadowBlur: number,
    elapsed: number
  ): EffectResult {
    const pulse = 1.0 + 0.3 * Math.sin(elapsed * 2 * Math.PI / this.config.glowPulsePeriod);

    return {
      intensity,
      shadowBlur: shadowBlur * pulse,
    };
  }

  /**
   * Update effect configuration
   */
  updateConfig(config: EffectConfig): void {
    this.config = { ...this.config, ...config };
  }
}

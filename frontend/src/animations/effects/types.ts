/**
 * effects/types.ts
 *
 * Type definitions for dot matrix pixel effects
 * Effects modify pixel intensity and glow during and after animation
 */

export type EffectType = 'blink' | 'pulsate' | 'flicker' | 'glow-pulse';

export interface EffectResult {
  intensity: number;
  shadowBlur: number;
}

export interface EffectConfig {
  blinkFrequency?: number;   // Hz, default: 50
  pulsePeriod?: number;      // ms, default: 2000
  glowPulsePeriod?: number;  // ms, default: 1500
  flickerIntensity?: number; // 0-1, default: 0.1
}

export const DEFAULT_EFFECT_CONFIG: Required<EffectConfig> = {
  blinkFrequency: 50,
  pulsePeriod: 2000,
  glowPulsePeriod: 1500,
  flickerIntensity: 0.1,
};

/**
 * reactive/ReactiveStateManager.ts
 *
 * Manages reactive state changes for dot matrix animations
 * Changes pattern/effects based on system state (processing, error, success)
 */

import { PatternType } from '../patterns';
import { EffectType } from '../effects';

export interface ReactiveConfig {
  enabled: boolean;
  isProcessing?: boolean;
  hasError?: boolean;
  isSuccess?: boolean;
}

export interface ReactiveState {
  pattern: PatternType;
  effects: EffectType[];
}

export class ReactiveStateManager {
  /**
   * Get pattern and effects configuration based on reactive state
   *
   * @param config - Reactive configuration
   * @param basePattern - Base pattern to use (from static prop, default: 'sequential')
   *
   * State priority (highest to lowest):
   * 1. Processing - Keep base pattern with blink and pulsate effects
   * 2. Error - Override to sequential pattern with flicker effect (intentional disruption)
   * 3. Success - Keep base pattern with glow-pulse effect
   * 4. Idle - Keep base pattern with pulsate effect
   */
  getStateConfig(config: ReactiveConfig, basePattern: PatternType = 'sequential'): ReactiveState {
    // If reactive system disabled, return base pattern with no effects
    if (!config.enabled) {
      return { pattern: basePattern, effects: [] };
    }

    // PROCESSING state - active computation (keep base pattern, add effects)
    if (config.isProcessing) {
      return {
        pattern: basePattern,
        effects: ['blink', 'pulsate'],
      };
    }

    // ERROR state - something went wrong (override to sequential + flicker for visual disruption)
    if (config.hasError) {
      return {
        pattern: 'sequential',
        effects: ['flicker'],
      };
    }

    // SUCCESS state - operation completed successfully (keep base pattern, add glow)
    if (config.isSuccess) {
      return {
        pattern: basePattern,
        effects: ['glow-pulse'],
      };
    }

    // IDLE state - default state (keep base pattern, add pulsate)
    return {
      pattern: basePattern,
      effects: ['pulsate'],
    };
  }

  /**
   * Check if state has changed significantly
   * Used to determine if animation should update
   */
  hasStateChanged(oldConfig: ReactiveConfig, newConfig: ReactiveConfig): boolean {
    return (
      oldConfig.isProcessing !== newConfig.isProcessing ||
      oldConfig.hasError !== newConfig.hasError ||
      oldConfig.isSuccess !== newConfig.isSuccess ||
      oldConfig.enabled !== newConfig.enabled
    );
  }

  /**
   * Determine if state change should trigger restart
   * Some state transitions are smooth, others require restart
   *
   * ONLY pattern changes require restart
   * Effect changes apply live without restart
   */
  shouldRestartAnimation(oldState: ReactiveState, newState: ReactiveState): boolean {
    // Pattern change requires restart (different pixel timing)
    if (oldState.pattern !== newState.pattern) {
      return true;
    }

    // Effect-only changes do NOT require restart
    // Effects apply to each pixel during rendering without timing changes
    // This allows smooth transitions like IDLE → PROCESSING without restart

    return false;
  }
}

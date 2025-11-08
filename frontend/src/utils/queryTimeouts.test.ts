/**
 * Tests for tier-specific query timeout utilities
 */

import { describe, test, expect } from 'vitest';
import {
  TIER_TIMEOUTS,
  MODE_TO_TIER,
  getQueryTimeout,
  getTimeoutForTier,
  getTimeoutDisplay,
  type ModelTier,
  type QueryMode,
} from './queryTimeouts';

describe('queryTimeouts', () => {
  describe('TIER_TIMEOUTS', () => {
    test('defines correct timeouts for each tier', () => {
      expect(TIER_TIMEOUTS.Q2).toBe(45000); // 45 seconds
      expect(TIER_TIMEOUTS.Q3).toBe(90000); // 90 seconds
      expect(TIER_TIMEOUTS.Q4).toBe(180000); // 180 seconds
    });

    test('all timeouts are in milliseconds', () => {
      Object.values(TIER_TIMEOUTS).forEach(timeout => {
        expect(timeout).toBeGreaterThan(1000); // At least 1 second
        expect(timeout % 1000).toBe(0); // Whole seconds
      });
    });
  });

  describe('MODE_TO_TIER', () => {
    test('maps all query modes to tiers', () => {
      expect(MODE_TO_TIER['two-stage']).toBe('Q3');
      expect(MODE_TO_TIER.simple).toBe('Q2');
      expect(MODE_TO_TIER.council).toBe('Q4');
      expect(MODE_TO_TIER.debate).toBe('Q4');
      expect(MODE_TO_TIER.chat).toBe('Q4');
    });

    test('two-stage mode defaults to Q3', () => {
      expect(MODE_TO_TIER['two-stage']).toBe('Q3');
    });
  });

  describe('getQueryTimeout', () => {
    test('returns correct timeout for simple mode', () => {
      expect(getQueryTimeout('simple')).toBe(45000);
    });

    test('returns correct timeout for two-stage mode', () => {
      expect(getQueryTimeout('two-stage')).toBe(90000);
    });

    test('returns correct timeout for council mode', () => {
      expect(getQueryTimeout('council')).toBe(120000);
    });

    test('returns correct timeout for debate mode', () => {
      expect(getQueryTimeout('debate')).toBe(150000);
    });

    test('returns correct timeout for chat mode', () => {
      expect(getQueryTimeout('chat')).toBe(180000);
    });

    test('returns two-stage timeout when no mode specified', () => {
      expect(getQueryTimeout()).toBe(90000);
    });

    test('handles all QueryMode values', () => {
      const modes: QueryMode[] = ['simple', 'two-stage', 'council', 'debate', 'chat'];
      modes.forEach(mode => {
        const timeout = getQueryTimeout(mode);
        expect(timeout).toBeGreaterThan(0);
        expect(typeof timeout).toBe('number');
      });
    });
  });

  describe('getTimeoutForTier', () => {
    test('returns correct timeout for Q2 tier', () => {
      expect(getTimeoutForTier('Q2')).toBe(45000);
    });

    test('returns correct timeout for Q3 tier', () => {
      expect(getTimeoutForTier('Q3')).toBe(90000);
    });

    test('returns correct timeout for Q4 tier', () => {
      expect(getTimeoutForTier('Q4')).toBe(180000);
    });

    test('handles all ModelTier values', () => {
      const tiers: ModelTier[] = ['Q2', 'Q3', 'Q4'];
      tiers.forEach(tier => {
        const timeout = getTimeoutForTier(tier);
        expect(timeout).toBeGreaterThan(0);
        expect(typeof timeout).toBe('number');
      });
    });
  });

  describe('getTimeoutDisplay', () => {
    test('formats timeout correctly for simple mode', () => {
      expect(getTimeoutDisplay('simple')).toBe('45s');
    });

    test('formats timeout correctly for two-stage mode', () => {
      expect(getTimeoutDisplay('two-stage')).toBe('90s');
    });

    test('formats timeout correctly for council mode', () => {
      expect(getTimeoutDisplay('council')).toBe('120s');
    });

    test('formats timeout correctly for debate mode', () => {
      expect(getTimeoutDisplay('debate')).toBe('150s');
    });

    test('formats timeout correctly for chat mode', () => {
      expect(getTimeoutDisplay('chat')).toBe('180s');
    });

    test('returns default timeout when no mode specified', () => {
      expect(getTimeoutDisplay()).toBe('90s');
    });

    test('returns string ending with "s"', () => {
      const modes: QueryMode[] = ['simple', 'two-stage', 'council', 'debate', 'chat'];
      modes.forEach(mode => {
        const display = getTimeoutDisplay(mode);
        expect(display).toMatch(/^\d+s$/);
      });
    });
  });

  describe('timeout ordering', () => {
    test('Q2 timeout < Q3 timeout < Q4 timeout', () => {
      expect(TIER_TIMEOUTS.Q2).toBeLessThan(TIER_TIMEOUTS.Q3);
      expect(TIER_TIMEOUTS.Q3).toBeLessThan(TIER_TIMEOUTS.Q4);
    });

    test('simple < two-stage < council < debate < chat', () => {
      const simpleTimeout = getQueryTimeout('simple');
      const twoStageTimeout = getQueryTimeout('two-stage');
      const councilTimeout = getQueryTimeout('council');
      const debateTimeout = getQueryTimeout('debate');
      const chatTimeout = getQueryTimeout('chat');

      expect(simpleTimeout).toBeLessThan(twoStageTimeout);
      expect(twoStageTimeout).toBeLessThan(councilTimeout);
      expect(councilTimeout).toBeLessThan(debateTimeout);
      expect(debateTimeout).toBeLessThan(chatTimeout);
    });
  });
});

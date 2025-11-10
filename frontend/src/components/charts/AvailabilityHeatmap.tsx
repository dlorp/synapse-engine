/**
 * AvailabilityHeatmap Component
 *
 * Visual indicator of model availability per tier using horizontal progress bars.
 * Color-coded: green (100%), amber (50-99%), red (<50%)
 *
 * Performance: <5ms render time (memoized)
 */

import React, { useMemo } from 'react';
import type { RoutingMetrics } from '@/types/metrics';
import styles from './AvailabilityHeatmap.module.css';

export interface AvailabilityHeatmapProps {
  modelAvailability: RoutingMetrics['modelAvailability'];
}

interface TierStatus {
  tier: string;
  available: number;
  total: number;
  percentage: number;
  status: 'healthy' | 'degraded' | 'critical';
}

/**
 * Calculate availability status for color-coding
 */
const getAvailabilityStatus = (percentage: number): TierStatus['status'] => {
  if (percentage === 100) return 'healthy';
  if (percentage >= 50) return 'degraded';
  return 'critical';
};

/**
 * Build tier status data
 */
const buildTierStatus = (
  modelAvailability: RoutingMetrics['modelAvailability']
): TierStatus[] => {
  return modelAvailability.map(tier => {
    const percentage = tier.total > 0 ? (tier.available / tier.total) * 100 : 0;
    return {
      tier: tier.tier,
      available: tier.available,
      total: tier.total,
      percentage,
      status: getAvailabilityStatus(percentage),
    };
  });
};

/**
 * Generate ASCII progress bar
 */
const generateProgressBar = (percentage: number, width: number = 20): string => {
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

export const AvailabilityHeatmap: React.FC<AvailabilityHeatmapProps> = React.memo(({
  modelAvailability,
}) => {
  const tierStatuses = useMemo(
    () => buildTierStatus(modelAvailability),
    [modelAvailability]
  );

  return (
    <div className={styles.heatmap}>
      {tierStatuses.map(tier => (
        <div key={tier.tier} className={styles.tierRow}>
          {/* Tier label */}
          <div className={styles.tierLabel}>{tier.tier}:</div>

          {/* Progress bar */}
          <div
            className={`${styles.progressBar} ${styles[tier.status]}`}
            role="progressbar"
            aria-valuenow={tier.percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${tier.tier} availability: ${tier.percentage.toFixed(0)}%`}
          >
            {generateProgressBar(tier.percentage)}
          </div>

          {/* Stats */}
          <div className={styles.stats}>
            <span className={styles.fraction}>
              {tier.available}/{tier.total}
            </span>
            <span className={`${styles.percentage} ${styles[tier.status]}`}>
              ({tier.percentage.toFixed(0)}%)
            </span>
          </div>
        </div>
      ))}
    </div>
  );
});

AvailabilityHeatmap.displayName = 'AvailabilityHeatmap';

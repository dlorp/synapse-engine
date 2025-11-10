/**
 * ResourceMetricCard - Single metric card component
 * Displays individual resource metrics with optional progress bar
 * Memoized for performance optimization
 */

import React, { useMemo } from 'react';
import styles from './ResourceMetricCard.module.css';
import { clamp } from '@/utils/formatters';

export interface ResourceMetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  percent?: number;
  status?: 'ok' | 'warning' | 'critical';
  secondary?: string;
}

export const ResourceMetricCard: React.FC<ResourceMetricCardProps> = React.memo(({
  label,
  value,
  unit,
  percent,
  status = 'ok',
  secondary,
}) => {
  // Memoize progress bar width to prevent recalculation
  const progressWidth = useMemo(() => {
    if (percent === undefined) return 0;
    return clamp(percent, 0, 100);
  }, [percent]);

  // Memoize class names
  const cardClassName = useMemo(() => {
    return `${styles.card} ${styles[status]}`;
  }, [status]);

  return (
    <div className={cardClassName}>
      <div className={styles.label}>{label}</div>

      <div className={styles.divider} />

      <div className={styles.value}>
        {value}
        {unit && <span className={styles.unit}> {unit}</span>}
      </div>

      {percent !== undefined && (
        <div className={styles.progressContainer}>
          <div
            className={styles.progressBar}
            style={{ width: `${progressWidth}%` }}
            role="progressbar"
            aria-valuenow={progressWidth}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      )}

      {secondary && (
        <div className={styles.secondary}>{secondary}</div>
      )}
    </div>
  );
});

ResourceMetricCard.displayName = 'ResourceMetricCard';

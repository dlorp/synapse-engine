import React from 'react';
import clsx from 'clsx';
import styles from './MetricDisplay.module.css';

export type TrendType = 'up' | 'down' | 'neutral';
export type MetricStatus = 'active' | 'processing' | 'error' | 'warning' | 'default';

export interface MetricDisplayProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: TrendType;
  status?: MetricStatus;
  className?: string;
}

export const MetricDisplay: React.FC<MetricDisplayProps> = ({
  label,
  value,
  unit,
  trend,
  status = 'default',
  className,
}) => {
  return (
    <div className={clsx(styles.metric, className)}>
      <div className={styles.label}>{label}</div>
      <div className={styles.valueRow}>
        <span className={clsx(styles.value, status !== 'default' && styles[status])}>
          {value}
        </span>
        {unit && <span className={styles.unit}>{unit}</span>}
        {trend && <span className={clsx(styles.trend, styles[trend])} />}
      </div>
    </div>
  );
};

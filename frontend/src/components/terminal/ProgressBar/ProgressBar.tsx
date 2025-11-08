import React from 'react';
import clsx from 'clsx';
import styles from './ProgressBar.module.css';

export interface ProgressBarProps {
  current: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  showValues?: boolean;
  variant?: 'default' | 'accent' | 'warning' | 'error';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  max,
  label,
  showPercentage = false,
  showValues = false,
  variant = 'default',
  className,
}) => {
  const percentage = Math.min(100, Math.max(0, (current / max) * 100));

  return (
    <div className={clsx(styles.container, className)}>
      {(label || showValues) && (
        <div className={styles.header}>
          {label && <span className={styles.label}>{label}</span>}
          {showValues && (
            <span className={styles.values}>
              {current} / {max}
            </span>
          )}
        </div>
      )}
      <div className={styles.track}>
        <div
          className={clsx(styles.fill, styles[variant])}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={current}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      {showPercentage && (
        <div className={styles.percentage}>{percentage.toFixed(1)}%</div>
      )}
    </div>
  );
};

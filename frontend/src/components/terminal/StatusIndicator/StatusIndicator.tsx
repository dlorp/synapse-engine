import React from 'react';
import clsx from 'clsx';
import styles from './StatusIndicator.module.css';

export type StatusType = 'active' | 'idle' | 'processing' | 'error' | 'offline';

export interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  showDot?: boolean;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  showDot = true,
  pulse = false,
  size = 'md',
  className,
}) => {
  return (
    <div className={clsx(styles.indicator, className)}>
      {showDot && (
        <span
          className={clsx(
            styles.dot,
            styles[status],
            styles[size],
            pulse && styles.pulse
          )}
        />
      )}
      {label && (
        <span className={clsx(styles.label, styles[status])}>{label}</span>
      )}
    </div>
  );
};

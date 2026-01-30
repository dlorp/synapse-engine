/**
 * ASCII Sparkline Component
 *
 * Compact inline sparkline visualization using asciichart.
 * Renders 20 datapoints in 3-5 lines with min/max/current values.
 *
 * Performance target: <3ms render time per sparkline
 */

import React, { useMemo } from 'react';
import * as asciichart from 'asciichart';
import styles from './AsciiSparkline.module.css';

export interface AsciiSparklineProps {
  data: number[];
  label: string;
  unit?: string;
  color?: string;
  height?: number;
  decimals?: number;
  className?: string;
}

export const AsciiSparkline: React.FC<AsciiSparklineProps> = ({
  data,
  label,
  unit = '',
  color = '#ff9500',
  height = 3,
  decimals = 1,
  className,
}) => {
  // Memoize chart rendering for performance (<3ms target)
  const chart = useMemo(() => {
    if (data.length === 0) {
      return '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁';  // Empty sparkline (20 chars)
    }

    try {
      return asciichart.plot(data, {
        height,
        format: () => '',  // No Y-axis labels for compact display
      });
    } catch (error) {
      console.error('Failed to render sparkline:', error);
      return '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁';
    }
  }, [data, height]);

  // Calculate min/max/current values
  const stats = useMemo(() => {
    if (data.length === 0) {
      return { min: 0, max: 0, current: 0 };
    }

    const min = Math.min(...data);
    const max = Math.max(...data);
    const current = data[data.length - 1] ?? 0;

    return { min, max, current };
  }, [data]);

  // Format numbers with specified decimals
  const formatValue = (value: number): string => {
    return value.toFixed(decimals);
  };

  const classNames = [styles.sparkline, className].filter(Boolean).join(' ');

  return (
    <div className={classNames}>
      <div className={styles.label}>{label}</div>

      <div className={styles.chartContainer} style={{ color }}>
        <pre className={styles.chart}>{chart}</pre>
      </div>

      <div className={styles.stats}>
        <span className={styles.current}>
          {formatValue(stats.current)}{unit}
        </span>
        <span className={styles.range}>
          (min: {formatValue(stats.min)}, max: {formatValue(stats.max)})
        </span>
      </div>
    </div>
  );
};

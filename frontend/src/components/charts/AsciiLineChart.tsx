/**
 * ASCII Line Chart Component
 *
 * Renders time-series data as ASCII art using asciichart library.
 * Displays query rate over time with phosphor orange styling.
 */

import React, { useMemo } from 'react';
import * as asciichart from 'asciichart';
import styles from './AsciiLineChart.module.css';

export interface AsciiLineChartProps {
  data: number[];
  height?: number;
  color?: string;
  title?: string;
  xLabel?: string;
  yLabel?: string;
  className?: string;
}

export const AsciiLineChart: React.FC<AsciiLineChartProps> = ({
  data,
  height = 10,
  color = '#ff9500',
  title,
  xLabel,
  yLabel,
  className,
}) => {
  // Memoize chart to avoid re-rendering on every frame
  const chart = useMemo(() => {
    if (data.length === 0) {
      return 'No data available';
    }

    try {
      return asciichart.plot(data, {
        height,
        format: (x: number) => x.toFixed(1).padStart(6),
      });
    } catch (error) {
      console.error('Failed to render ASCII chart:', error);
      return 'Error rendering chart';
    }
  }, [data, height]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (data.length === 0) {
      return { min: 0, max: 0, avg: 0 };
    }

    const min = Math.min(...data);
    const max = Math.max(...data);
    const avg = data.reduce((sum, val) => sum + val, 0) / data.length;

    return { min, max, avg };
  }, [data]);

  const classNames = [styles.chart, className].filter(Boolean).join(' ');

  return (
    <div className={classNames}>
      {title && <div className={styles.title}>{title}</div>}

      <div className={styles.chartContainer} style={{ color }}>
        <pre className={styles.chartContent}>{chart}</pre>
      </div>

      <div className={styles.labels}>
        {yLabel && <div className={styles.yLabel}>{yLabel}</div>}
        {xLabel && <div className={styles.xLabel}>{xLabel}</div>}
      </div>

      <div className={styles.stats}>
        <span className={styles.stat}>MIN: {stats.min.toFixed(1)}</span>
        <span className={styles.stat}>AVG: {stats.avg.toFixed(1)}</span>
        <span className={styles.stat}>MAX: {stats.max.toFixed(1)}</span>
      </div>
    </div>
  );
};

/**
 * ASCII Bar Chart Component
 *
 * Renders horizontal bar chart using Unicode block characters.
 * Used for displaying model tier distribution (Q2/Q3/Q4).
 */

import React, { useMemo } from 'react';
import styles from './AsciiBarChart.module.css';

export interface BarData {
  label: string;
  value: number;
  color?: string;
}

export interface AsciiBarChartProps {
  data: BarData[];
  maxBarLength?: number;  // Max bar width in characters
  showPercentage?: boolean;
  showValue?: boolean;
  className?: string;
}

// Unicode block characters for bar rendering (full to empty)
const BLOCKS = ['█', '▓', '▒', '░'];

export const AsciiBarChart: React.FC<AsciiBarChartProps> = ({
  data,
  maxBarLength = 40,
  showPercentage = true,
  showValue = true,
  className,
}) => {
  // Calculate total for percentage calculations
  const total = useMemo(() => {
    return data.reduce((sum, item) => sum + item.value, 0);
  }, [data]);

  // Render a single bar
  const renderBar = (value: number, color?: string) => {
    if (total === 0) return '';

    const percentage = (value / total) * 100;
    const barLength = Math.round((percentage / 100) * maxBarLength);

    // Full blocks
    const fullBlocks = Math.floor(barLength);
    const fullBar = (BLOCKS[0] ?? '█').repeat(fullBlocks);

    // Empty blocks
    const emptyBlocks = maxBarLength - fullBlocks;
    const emptyBar = (BLOCKS[3] ?? '░').repeat(emptyBlocks);

    return (
      <span className={styles.bar} style={{ color: color || 'inherit' }}>
        {fullBar}
        {emptyBar}
      </span>
    );
  };

  const classNames = [styles.chart, className].filter(Boolean).join(' ');

  return (
    <div className={classNames}>
      {data.map((item, index) => {
        const percentage = total > 0 ? ((item.value / total) * 100).toFixed(0) : '0';

        return (
          <div key={index} className={styles.row}>
            <div className={styles.label}>{item.label}:</div>
            <div className={styles.barContainer}>
              {renderBar(item.value, item.color)}
            </div>
            <div className={styles.info}>
              {showPercentage && <span className={styles.percentage}>{percentage}%</span>}
              {showValue && <span className={styles.value}>({item.value})</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

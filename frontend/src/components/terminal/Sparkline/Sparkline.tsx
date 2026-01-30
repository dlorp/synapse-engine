/**
 * Sparkline Component - Inline ASCII sparkline visualization
 *
 * Renders a compact sparkline chart using Unicode block characters.
 * Suitable for displaying trends in metric displays.
 *
 * Features:
 * - Block character rendering (▁▂▃▄▅▆▇█)
 * - Auto-scaling to fit data range
 * - Smooth transitions with CSS
 * - Configurable width and color
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';
import styles from './Sparkline.module.css';

export interface SparklineProps {
  data: number[];
  width?: number; // Number of bars to display
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'error';
  className?: string;
}

// Unicode block characters from lowest to highest
const BLOCK_CHARS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

/**
 * Map a value to a block character based on min/max range
 */
const valueToBlock = (value: number, min: number, max: number): string => {
  if (max === min) return BLOCK_CHARS[0] ?? '▁'; // All values same

  const normalized = (value - min) / (max - min);
  const index = Math.floor(normalized * (BLOCK_CHARS.length - 1));
  return BLOCK_CHARS[Math.max(0, Math.min(index, BLOCK_CHARS.length - 1))] ?? '▁';
};

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 15,
  color = 'primary',
  className,
}) => {
  // Prepare data: take last N values and fill with zeros if needed
  const displayData = useMemo(() => {
    if (data.length === 0) {
      return Array(width).fill(0);
    }

    const sliced = data.slice(-width);
    const padded = [...Array(Math.max(0, width - sliced.length)).fill(0), ...sliced];
    return padded;
  }, [data, width]);

  // Calculate min/max for normalization
  const { min, max } = useMemo(() => {
    if (displayData.length === 0) return { min: 0, max: 0 };
    return {
      min: Math.min(...displayData),
      max: Math.max(...displayData),
    };
  }, [displayData]);

  // Convert data to block characters
  const blocks = useMemo(() => {
    return displayData.map((value) => valueToBlock(value, min, max));
  }, [displayData, min, max]);

  return (
    <span
      className={clsx(styles.sparkline, styles[color], className)}
      role="img"
      aria-label={`Sparkline chart with ${data.length} data points`}
    >
      {blocks.join('')}
    </span>
  );
};

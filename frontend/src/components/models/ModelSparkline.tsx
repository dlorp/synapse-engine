/**
 * ModelSparkline - Per-Model Performance Sparkline
 *
 * Lightweight wrapper around AsciiSparkline for model-specific metrics.
 * Formats data with appropriate units and colors based on metric type.
 *
 * Performance: <3ms render time (inherits from AsciiSparkline)
 */

import React from 'react';
import { AsciiSparkline } from '@/components/charts/AsciiSparkline';
import styles from './ModelSparkline.module.css';

export interface ModelSparklineProps {
  data: number[];
  metricType: 'tokens' | 'memory' | 'latency';
  modelId: string;
  className?: string;
}

/**
 * Metric configuration: labels, units, colors, decimal precision
 */
const METRIC_CONFIG = {
  tokens: {
    label: 'Tokens/sec',
    unit: ' t/s',
    color: '#00ffff', // Cyan for throughput
    decimals: 1,
    height: 3
  },
  memory: {
    label: 'Memory',
    unit: ' GB',
    color: '#ff9500', // Phosphor orange (primary brand color)
    decimals: 2,
    height: 3
  },
  latency: {
    label: 'Latency',
    unit: ' ms',
    color: '#00ff41', // Green for response time
    decimals: 0,
    height: 3
  }
} as const;

export const ModelSparkline: React.FC<ModelSparklineProps> = React.memo(({
  data,
  metricType,
  modelId,
  className
}) => {
  const config = METRIC_CONFIG[metricType];

  // Generate unique key for React reconciliation
  const key = `${modelId}-${metricType}`;

  return (
    <div className={`${styles.modelSparkline} ${className || ''}`} data-metric={metricType}>
      <AsciiSparkline
        data={data}
        label={config.label}
        unit={config.unit}
        color={config.color}
        height={config.height}
        decimals={config.decimals}
      />
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for performance optimization
  // Only re-render if data actually changed (not just reference)
  return (
    prevProps.modelId === nextProps.modelId &&
    prevProps.metricType === nextProps.metricType &&
    JSON.stringify(prevProps.data) === JSON.stringify(nextProps.data)
  );
});

ModelSparkline.displayName = 'ModelSparkline';

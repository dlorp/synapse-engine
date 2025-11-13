/**
 * AdvancedMetricsPanel Component - Time-Series Metrics Visualization
 *
 * Phase 4, Component 3 - Advanced metrics visualization with Chart.js integration.
 *
 * Features:
 * - Performance Trends: Single metric over time with time range selector
 * - Model Comparison: Compare Q2/Q3/Q4 performance side-by-side
 * - Multi-Metric Correlation: Multiple metrics on same chart with dual Y-axes
 * - ASCII Sparklines: Unicode block element visualization of last 10 data points
 * - Real-time updates: Poll every 10 seconds via TanStack Query
 * - Terminal aesthetic: Phosphor orange color scheme, smooth 60fps animations
 *
 * API Endpoints:
 * - GET /api/timeseries?metric={name}&range={range}&tier={tier}&model={id}
 * - GET /api/timeseries/comparison?metrics={comma-separated}&range={range}
 * - GET /api/timeseries/models?metric={name}&range={range}
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';
import { AsciiPanel, TerminalSpinner } from '@/components/terminal';
import styles from './AdvancedMetricsPanel.module.css';

// Register Chart.js components and plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  zoomPlugin
);

// ============================================================================
// TypeScript Interfaces
// ============================================================================

interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  metadata: {
    model_id?: string;
    tier?: string;
    query_mode?: string;
  };
}

interface TimeSeriesResponse {
  metricName: string;
  timeRange: string;
  unit: string;
  dataPoints: TimeSeriesDataPoint[];
  summary: {
    min: number;
    max: number;
    avg: number;
    p50: number;
    p95: number;
    p99: number;
  };
}

interface ComparisonResponse {
  metrics: {
    [key: string]: TimeSeriesResponse;
  };
  timeRange: string;
}

interface ModelComparisonResponse {
  metricName: string;
  timeRange: string;
  unit: string;
  tiers: {
    Q2: TimeSeriesDataPoint[];
    Q3: TimeSeriesDataPoint[];
    Q4: TimeSeriesDataPoint[];
  };
}

type MetricType =
  | 'response_time'
  | 'tokens_per_second'
  | 'cache_hit_rate'
  | 'complexity_score'
  | 'cgrag_retrieval_time';

type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d';

type ViewMode = 'trends' | 'comparison' | 'correlation';

// Metric display configuration
const METRIC_CONFIG: Record<MetricType, { label: string; unit: string; color: string }> = {
  response_time: { label: 'Response Time', unit: 's', color: '#ff9500' },
  tokens_per_second: { label: 'Tokens/Sec', unit: 'tokens/s', color: '#00ffff' },
  cache_hit_rate: { label: 'Cache Hit Rate', unit: '%', color: '#00ff41' },
  complexity_score: { label: 'Complexity Score', unit: '', color: '#ff6b00' },
  cgrag_retrieval_time: { label: 'CGRAG Time', unit: 'ms', color: '#ff00ff' },
};

const TIER_COLORS = {
  Q2: '#ff9500', // Phosphor orange
  Q3: '#00ffff', // Cyan
  Q4: '#ff00ff', // Magenta
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generate ASCII sparkline from numeric values using Unicode block elements
 */
const generateSparkline = (values: number[]): string => {
  if (values.length === 0) return '─'.repeat(10);

  const blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;

  return values.slice(-10).map(val => {
    if (range === 0) return blocks[4]; // middle block
    const normalized = (val - min) / range;
    const index = Math.floor(normalized * (blocks.length - 1));
    return blocks[Math.max(0, Math.min(blocks.length - 1, index))];
  }).join('');
};

/**
 * Format number with appropriate precision
 */
const formatValue = (value: number, unit: string): string => {
  if (unit === '%') return `${value.toFixed(1)}%`;
  if (unit === 'ms') return `${value.toFixed(0)}ms`;
  if (unit === 's') return `${value.toFixed(2)}s`;
  if (unit === 'tokens/s') return `${value.toFixed(1)}`;
  return value.toFixed(2);
};

// ============================================================================
// Main Component
// ============================================================================

export const AdvancedMetricsPanel: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('trends');
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('response_time');
  const [selectedRange, setSelectedRange] = useState<TimeRange>('6h');
  const [selectedTier] = useState<string | null>(null);
  const [correlationMetrics] = useState<MetricType[]>([
    'response_time',
    'tokens_per_second',
  ]);

  // ============================================================================
  // API Queries
  // ============================================================================

  // Single metric trends
  const { data: trendsData, isLoading: trendsLoading } = useQuery<TimeSeriesResponse>({
    queryKey: ['metrics-timeseries', selectedMetric, selectedRange, selectedTier],
    queryFn: async () => {
      const params = new URLSearchParams({
        metric: selectedMetric,
        range: selectedRange,
      });
      if (selectedTier) params.append('tier', selectedTier);

      const response = await fetch(`/api/timeseries/?${params}`);
      if (!response.ok) throw new Error('Failed to fetch metrics');
      return response.json();
    },
    refetchInterval: 10000, // Poll every 10 seconds
    enabled: viewMode === 'trends',
  });

  // Model tier comparison
  const { data: comparisonData, isLoading: comparisonLoading } = useQuery<ModelComparisonResponse>({
    queryKey: ['metrics-comparison', selectedMetric, selectedRange],
    queryFn: async () => {
      const params = new URLSearchParams({
        metric: selectedMetric,
        range: selectedRange,
      });

      const response = await fetch(`/api/timeseries/models/?${params}`);
      if (!response.ok) throw new Error('Failed to fetch comparison data');
      return response.json();
    },
    refetchInterval: 10000,
    enabled: viewMode === 'comparison',
  });

  // Multi-metric correlation
  const { data: correlationData, isLoading: correlationLoading } = useQuery<ComparisonResponse>({
    queryKey: ['metrics-correlation', correlationMetrics, selectedRange],
    queryFn: async () => {
      const params = new URLSearchParams({
        metrics: correlationMetrics.join(','),
        range: selectedRange,
      });

      const response = await fetch(`/api/timeseries/comparison/?${params}`);
      if (!response.ok) throw new Error('Failed to fetch correlation data');
      return response.json();
    },
    refetchInterval: 10000,
    enabled: viewMode === 'correlation',
  });

  // ============================================================================
  // Chart Configuration
  // ============================================================================

  const baseChartOptions: ChartOptions<'line'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: 'var(--webtui-primary, #ff9500)',
          font: {
            family: 'var(--font-mono, "JetBrains Mono", monospace)',
            size: 11,
          },
          padding: 12,
          usePointStyle: true,
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        borderColor: 'var(--webtui-primary, #ff9500)',
        borderWidth: 1,
        titleColor: 'var(--webtui-accent, #00ffff)',
        bodyColor: 'var(--webtui-text-primary, #ff9500)',
        titleFont: {
          family: 'var(--font-mono, "JetBrains Mono", monospace)',
          size: 12,
          weight: 'bold',
        },
        bodyFont: {
          family: 'var(--font-mono, "JetBrains Mono", monospace)',
          size: 11,
        },
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y ?? 0;
            const dataset = context.dataset as any;
            const unit = dataset.unit || '';
            return `${label}: ${formatValue(value, unit)}`;
          },
        },
      },
      zoom: {
        zoom: {
          wheel: {
            enabled: true,
            speed: 0.1,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x',
        },
        pan: {
          enabled: true,
          mode: 'x',
        },
        limits: {
          x: { min: 'original', max: 'original' },
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: selectedRange === '1h' ? 'minute' :
                selectedRange === '6h' ? 'hour' :
                selectedRange === '24h' ? 'hour' : 'day',
          displayFormats: {
            minute: 'HH:mm',
            hour: 'HH:mm',
            day: 'MM/dd',
          },
        },
        grid: {
          color: 'rgba(255, 149, 0, 0.1)',
          lineWidth: 1,
        },
        ticks: {
          color: 'var(--webtui-text-secondary, #888)',
          font: {
            family: 'var(--font-mono, "JetBrains Mono", monospace)',
            size: 10,
          },
          maxRotation: 0,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 149, 0, 0.1)',
          lineWidth: 1,
        },
        ticks: {
          color: 'var(--webtui-text-secondary, #888)',
          font: {
            family: 'var(--font-mono, "JetBrains Mono", monospace)',
            size: 10,
          },
        },
      },
    },
  }), [selectedRange]);

  // ============================================================================
  // Chart Data Preparation
  // ============================================================================

  const trendsChartData = useMemo(() => {
    if (!trendsData?.dataPoints) return null;

    const config = METRIC_CONFIG[selectedMetric];
    return {
      labels: trendsData.dataPoints.map(dp => new Date(dp.timestamp)),
      datasets: [{
        label: config.label,
        data: trendsData.dataPoints.map(dp => dp.value),
        borderColor: config.color,
        backgroundColor: `${config.color}20`,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointBackgroundColor: config.color,
        pointBorderColor: config.color,
        borderWidth: 2,
        fill: true,
        unit: config.unit,
      }],
    };
  }, [trendsData, selectedMetric]);

  const comparisonChartData = useMemo(() => {
    if (!comparisonData?.tiers) return null;

    const config = METRIC_CONFIG[selectedMetric];
    return {
      labels: comparisonData.tiers.Q2?.map(dp => new Date(dp.timestamp)) || [],
      datasets: [
        {
          label: 'Q2 (FAST)',
          data: comparisonData.tiers.Q2?.map(dp => dp.value) || [],
          borderColor: TIER_COLORS.Q2,
          backgroundColor: `${TIER_COLORS.Q2}20`,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 6,
          borderWidth: 2,
          fill: false,
          unit: config.unit,
        },
        {
          label: 'Q3 (BALANCED)',
          data: comparisonData.tiers.Q3?.map(dp => dp.value) || [],
          borderColor: TIER_COLORS.Q3,
          backgroundColor: `${TIER_COLORS.Q3}20`,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 6,
          borderWidth: 2,
          fill: false,
          unit: config.unit,
        },
        {
          label: 'Q4 (POWERFUL)',
          data: comparisonData.tiers.Q4?.map(dp => dp.value) || [],
          borderColor: TIER_COLORS.Q4,
          backgroundColor: `${TIER_COLORS.Q4}20`,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 6,
          borderWidth: 2,
          fill: false,
          unit: config.unit,
        },
      ].filter(ds => ds.data.length > 0),
    };
  }, [comparisonData, selectedMetric]);

  const correlationChartData = useMemo(() => {
    if (!correlationData?.metrics) return null;

    const datasets = correlationMetrics.map((metric, index) => {
      const metricData = correlationData.metrics[metric];
      const config = METRIC_CONFIG[metric];

      if (!metricData?.dataPoints) return null;

      return {
        label: config.label,
        data: metricData.dataPoints.map((dp: TimeSeriesDataPoint) => dp.value),
        borderColor: config.color,
        backgroundColor: `${config.color}20`,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        borderWidth: 2,
        fill: false,
        yAxisID: index === 0 ? 'y' : 'y1',
        unit: config.unit,
      };
    }).filter(Boolean);

    const firstMetricKey = correlationMetrics[0];
    if (!firstMetricKey) return null;

    const firstMetric = correlationData.metrics[firstMetricKey];
    return {
      labels: firstMetric?.dataPoints.map((dp: TimeSeriesDataPoint) => new Date(dp.timestamp)) || [],
      datasets: datasets as any[],
    };
  }, [correlationData, correlationMetrics]);

  // Correlation chart needs dual Y-axes
  const correlationChartOptions: ChartOptions<'line'> = useMemo(() => {
    if (correlationMetrics.length < 2) return baseChartOptions;

    const metric1 = correlationMetrics[0];
    const metric2 = correlationMetrics[1];
    if (!metric1 || !metric2) return baseChartOptions;

    const config1 = METRIC_CONFIG[metric1];
    const config2 = METRIC_CONFIG[metric2];

    return {
      ...baseChartOptions,
      scales: {
        ...baseChartOptions.scales,
        y: {
          ...baseChartOptions.scales?.y,
          position: 'left',
          title: {
            display: true,
            text: `${config1.label} (${config1.unit})`,
            color: config1.color,
            font: {
              family: 'var(--font-mono, "JetBrains Mono", monospace)',
              size: 11,
            },
          },
        },
        y1: {
          type: 'linear',
          position: 'right',
          beginAtZero: true,
          grid: {
            drawOnChartArea: false,
          },
          ticks: {
            color: 'var(--webtui-text-secondary, #888)',
            font: {
              family: 'var(--font-mono, "JetBrains Mono", monospace)',
              size: 10,
            },
          },
          title: {
            display: true,
            text: `${config2.label} (${config2.unit})`,
            color: config2.color,
            font: {
              family: 'var(--font-mono, "JetBrains Mono", monospace)',
              size: 11,
            },
          },
        },
      },
    };
  }, [baseChartOptions, correlationMetrics]);

  // ============================================================================
  // ASCII Sparklines
  // ============================================================================

  const sparklineData = useMemo(() => {
    if (viewMode === 'trends' && trendsData?.dataPoints) {
      const values = trendsData.dataPoints.map(dp => dp.value);
      return {
        sparkline: generateSparkline(values),
        summary: trendsData.summary,
      };
    }
    return null;
  }, [viewMode, trendsData]);

  // ============================================================================
  // Render Functions
  // ============================================================================

  const renderTimeRangeSelector = () => (
    <div className={styles.timeRangeSelector}>
      {(['1h', '6h', '24h', '7d', '30d'] as TimeRange[]).map(range => (
        <button
          key={range}
          className={`${styles.rangeButton} ${selectedRange === range ? styles.active : ''}`}
          onClick={() => setSelectedRange(range)}
        >
          {range.toUpperCase()}
        </button>
      ))}
    </div>
  );

  const renderMetricSelector = () => (
    <div className={styles.metricSelector}>
      {(Object.keys(METRIC_CONFIG) as MetricType[]).map(metric => (
        <button
          key={metric}
          className={`${styles.metricButton} ${selectedMetric === metric ? styles.active : ''}`}
          onClick={() => setSelectedMetric(metric)}
        >
          {METRIC_CONFIG[metric].label}
        </button>
      ))}
    </div>
  );

  const renderViewModeSelector = () => (
    <div className={styles.viewModeSelector}>
      <button
        className={`${styles.viewButton} ${viewMode === 'trends' ? styles.active : ''}`}
        onClick={() => setViewMode('trends')}
      >
        TRENDS
      </button>
      <button
        className={`${styles.viewButton} ${viewMode === 'comparison' ? styles.active : ''}`}
        onClick={() => setViewMode('comparison')}
      >
        TIER COMPARISON
      </button>
      <button
        className={`${styles.viewButton} ${viewMode === 'correlation' ? styles.active : ''}`}
        onClick={() => setViewMode('correlation')}
      >
        MULTI-METRIC
      </button>
    </div>
  );

  const renderSparkline = () => {
    if (!sparklineData) return null;

    return (
      <div className={styles.sparklineContainer}>
        <div className={styles.sparkline}>
          {sparklineData.sparkline}
        </div>
        <div className={styles.sparklineSummary}>
          <span>MIN: {formatValue(sparklineData.summary.min, METRIC_CONFIG[selectedMetric].unit)}</span>
          <span>AVG: {formatValue(sparklineData.summary.avg, METRIC_CONFIG[selectedMetric].unit)}</span>
          <span>MAX: {formatValue(sparklineData.summary.max, METRIC_CONFIG[selectedMetric].unit)}</span>
          <span>P95: {formatValue(sparklineData.summary.p95, METRIC_CONFIG[selectedMetric].unit)}</span>
          <span>P99: {formatValue(sparklineData.summary.p99, METRIC_CONFIG[selectedMetric].unit)}</span>
        </div>
      </div>
    );
  };

  const renderChart = () => {
    const isLoading = trendsLoading || comparisonLoading || correlationLoading;

    if (isLoading) {
      return (
        <div className={styles.emptyState}>
          <TerminalSpinner style="arc" size={24} />
          <div className={styles.emptyText}>LOADING METRICS DATA...</div>
        </div>
      );
    }

    if (viewMode === 'trends') {
      if (!trendsChartData || trendsChartData.datasets[0]?.data.length === 0) {
        return (
          <div className={styles.emptyState}>
            <div className={styles.emptyText}>NO METRICS AVAILABLE</div>
            <div className={styles.emptySubtext}>SUBMIT QUERIES TO POPULATE</div>
          </div>
        );
      }
      return (
        <>
          {renderSparkline()}
          <div className={styles.chartContainer}>
            <Line data={trendsChartData} options={baseChartOptions} />
          </div>
        </>
      );
    }

    if (viewMode === 'comparison') {
      if (!comparisonChartData || comparisonChartData.datasets.length === 0) {
        return (
          <div className={styles.emptyState}>
            <div className={styles.emptyText}>NO COMPARISON DATA AVAILABLE</div>
            <div className={styles.emptySubtext}>SUBMIT QUERIES ACROSS TIERS TO POPULATE</div>
          </div>
        );
      }
      return (
        <div className={styles.chartContainer}>
          <Line data={comparisonChartData} options={baseChartOptions} />
        </div>
      );
    }

    if (viewMode === 'correlation') {
      if (!correlationChartData || correlationChartData.datasets.length === 0) {
        return (
          <div className={styles.emptyState}>
            <div className={styles.emptyText}>NO CORRELATION DATA AVAILABLE</div>
            <div className={styles.emptySubtext}>SUBMIT QUERIES TO POPULATE</div>
          </div>
        );
      }
      return (
        <div className={styles.chartContainer}>
          <Line data={correlationChartData} options={correlationChartOptions} />
        </div>
      );
    }

    return null;
  };

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <AsciiPanel title="ADVANCED METRICS VISUALIZATION">
      <div className={styles.metricsPanel}>
        {/* View Mode Selector */}
        {renderViewModeSelector()}

        {/* Time Range Selector */}
        {renderTimeRangeSelector()}

        {/* Metric Selector (only for trends and comparison) */}
        {(viewMode === 'trends' || viewMode === 'comparison') && renderMetricSelector()}

        {/* Chart */}
        {renderChart()}

        {/* Zoom Controls Hint */}
        <div className={styles.controlsHint}>
          MOUSE WHEEL: ZOOM | DRAG: PAN | DOUBLE-CLICK: RESET
        </div>
      </div>
    </AsciiPanel>
  );
};

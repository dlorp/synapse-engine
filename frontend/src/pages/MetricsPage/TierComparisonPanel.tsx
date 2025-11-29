/**
 * Tier Comparison Panel
 *
 * Displays real-time performance comparison across Q2/Q3/Q4 model tiers:
 * - Sparklines for tokens/sec over time (last 20 samples)
 * - Sparklines for latency over time (last 20 samples)
 * - Request counts and error rates
 *
 * Updates every second via TanStack Query.
 * Performance target: <9ms total render time (3ms per tier).
 */

import React, { useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { TerminalSpinner } from '@/components/terminal/TerminalSpinner/TerminalSpinner';
import { AsciiSparkline } from '@/components/charts/AsciiSparkline';
import { useTierMetrics } from '@/hooks/useTierMetrics';
import { useModelStatus } from '@/hooks/useModelStatus';
import styles from './TierComparisonPanel.module.css';

/**
 * Individual tier card component
 * Memoized for performance optimization
 */
interface TierCardProps {
  name: "Q2" | "Q3" | "Q4";
  tokensPerSec: number[];
  latencyMs: number[];
  requestCount: number;
  errorRate: number;
}

const TierCard: React.FC<TierCardProps> = React.memo(({
  name,
  tokensPerSec,
  latencyMs,
  requestCount,
  errorRate,
}) => {
  // Color-code tier names for visual distinction
  const tierColor = useMemo(() => {
    switch (name) {
      case 'Q2':
        return '#00ff00'; // Green (FAST)
      case 'Q3':
        return '#00ffff'; // Cyan (BALANCED)
      case 'Q4':
        return '#ff9500'; // Orange (POWERFUL)
      default:
        return '#ff9500';
    }
  }, [name]);

  // Tier display names
  const tierLabel = useMemo(() => {
    switch (name) {
      case 'Q2':
        return 'Q2 (FAST)';
      case 'Q3':
        return 'Q3 (BALANCED)';
      case 'Q4':
        return 'Q4 (POWERFUL)';
      default:
        return name;
    }
  }, [name]);

  // Format large numbers with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US');
  };

  // Format error rate as percentage
  const formatErrorRate = (rate: number): string => {
    return (rate * 100).toFixed(1);
  };

  // Generate breathing bar chart for performance visualization
  // Uses ASCII_MASTER_GUIDE.md pattern: █ for filled, ░ for empty
  const generateBarChart = (value: number, maxValue: number = 100, width: number = 20): string => {
    const filled = Math.floor((value / maxValue) * width);
    const empty = width - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  };

  // Calculate current performance values
  const currentTokens = tokensPerSec[tokensPerSec.length - 1] || 0;
  const currentLatency = latencyMs[latencyMs.length - 1] || 0;

  // Normalize values for bar charts (0-100 scale)
  const tokensPercent = Math.min((currentTokens / 100) * 100, 100); // Assume max 100 tok/s
  const latencyPercent = Math.min((currentLatency / 1000) * 100, 100); // Assume max 1000ms

  return (
    <div className={styles.tierCard}>
      <div className={styles.tierHeader} style={{ color: tierColor }}>
        {tierLabel}
      </div>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Requests:</span>
          <span className={styles.statValue}>{formatNumber(requestCount)}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Error Rate:</span>
          <span className={styles.statValue}>{formatErrorRate(errorRate)}%</span>
        </div>
      </div>

      {/* Breathing bar graphs for performance metrics */}
      <div className={styles.barCharts}>
        <div className={styles.barChart}>
          <div className={styles.barLabel}>Tokens/sec</div>
          <pre className={styles.breathingBar}>
            {generateBarChart(tokensPercent, 100, 30)} {currentTokens.toFixed(1)}
          </pre>
        </div>

        <div className={styles.barChart}>
          <div className={styles.barLabel}>Latency</div>
          <pre className={styles.breathingBar}>
            {generateBarChart(100 - latencyPercent, 100, 30)} {currentLatency.toFixed(0)}ms
          </pre>
        </div>
      </div>

      <div className={styles.sparklines}>
        <AsciiSparkline
          data={tokensPerSec}
          label="Tokens/sec trend"
          unit=" tok/s"
          color="#ff9500"
          height={3}
          decimals={1}
        />

        <AsciiSparkline
          data={latencyMs}
          label="Latency trend"
          unit="ms"
          color="#ff9500"
          height={3}
          decimals={0}
        />
      </div>
    </div>
  );
});

TierCard.displayName = 'TierCard';

/**
 * Main tier comparison panel component
 */
export const TierComparisonPanel: React.FC = () => {
  const { data: metrics, error, isLoading } = useTierMetrics();
  const { data: modelStatus } = useModelStatus();

  // Check which tiers have running models
  const runningTiers = useMemo(() => {
    if (!modelStatus) return new Set<string>();

    const runningModels = modelStatus.models.filter(
      m => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
    );

    return new Set(runningModels.map(m => m.tier));
  }, [modelStatus]);

  // Sort tiers in order Q2 -> Q3 -> Q4 and filter by running models
  const sortedTiers = useMemo(() => {
    if (!metrics) return [];

    const tierOrder: Record<string, number> = { Q2: 0, Q3: 1, Q4: 2 };
    return [...metrics.tiers]
      .filter(tier => runningTiers.has(tier.name))
      .sort((a, b) => (tierOrder[a.name] ?? 0) - (tierOrder[b.name] ?? 0));
  }, [metrics, runningTiers]);

  // Render loading state
  if (isLoading) {
    return (
      <AsciiPanel title="TIER PERFORMANCE COMPARISON">
        <div className={styles.loading}>
          <TerminalSpinner style="arc" size={24} />
          <span className={styles.loadingText}>Loading tier metrics...</span>
        </div>
      </AsciiPanel>
    );
  }

  // Render error state
  if (error) {
    return (
      <AsciiPanel title="TIER PERFORMANCE COMPARISON">
        <div className={styles.error}>
          <div className={styles.errorTitle}>ERROR: Failed to load tier metrics</div>
          <div className={styles.errorMessage}>{error.message}</div>
        </div>
      </AsciiPanel>
    );
  }

  // Render empty state (no data from backend)
  if (!metrics) {
    return (
      <AsciiPanel title="TIER PERFORMANCE COMPARISON">
        <div className={styles.empty}>No tier metrics data available</div>
      </AsciiPanel>
    );
  }

  // No models running state
  if (sortedTiers.length === 0) {
    return (
      <AsciiPanel title="TIER PERFORMANCE COMPARISON">
        <div className={styles.awaitingModels}>
          <div className={styles.emptyTierGrid}>
            <div className={styles.emptyTierBox}>
              <div className={styles.emptyTierArt}>
                <span>┌─────┐</span>
                <span>│ ░░░ │</span>
                <span>│ ░░░ │</span>
                <span>└─────┘</span>
              </div>
              <div className={styles.emptyTierLabel}>Q2</div>
              <div className={styles.emptyTierStatus}>OFFLINE</div>
            </div>

            <div className={styles.emptyTierBox}>
              <div className={styles.emptyTierArt}>
                <span>┌─────┐</span>
                <span>│ ░░░ │</span>
                <span>│ ░░░ │</span>
                <span>└─────┘</span>
              </div>
              <div className={styles.emptyTierLabel}>Q3</div>
              <div className={styles.emptyTierStatus}>OFFLINE</div>
            </div>

            <div className={styles.emptyTierBox}>
              <div className={styles.emptyTierArt}>
                <span>┌─────┐</span>
                <span>│ ░░░ │</span>
                <span>│ ░░░ │</span>
                <span>└─────┘</span>
              </div>
              <div className={styles.emptyTierLabel}>Q4</div>
              <div className={styles.emptyTierStatus}>OFFLINE</div>
            </div>
          </div>

          <div className={styles.emptyHint}>
            → Deploy models to enable tier comparison analytics
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel title="TIER PERFORMANCE COMPARISON">
      <div className={styles.container}>
        <div className={styles.grid}>
          {sortedTiers.map((tier) => (
            <TierCard
              key={tier.name}
              name={tier.name}
              tokensPerSec={tier.tokensPerSec}
              latencyMs={tier.latencyMs}
              requestCount={tier.requestCount}
              errorRate={tier.errorRate}
            />
          ))}
        </div>
      </div>
    </AsciiPanel>
  );
};

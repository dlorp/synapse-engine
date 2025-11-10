/**
 * SystemStatusPanelEnhanced Component - Essential system status metrics
 *
 * Mission Control system status panel with 5 essential metrics (static snapshots).
 * Shows current system state for query submission readiness.
 * Updated per UI Consolidation Plan Phase 1 (2025-11-09).
 *
 * Features:
 * - 5 essential metrics (Active Models, Active Queries, Cache Hit Rate, Context Util, Uptime)
 * - Static values only (no sparklines - trends moved to MetricsPage)
 * - Integrated Quick Actions footer with 4 buttons
 * - Compact design (~40% height reduction)
 * - Color-coded status indicators
 * - Responsive layout (mobile → tablet → desktop)
 * - WebSocket/polling-based live updates
 */

import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DotMatrixPanel } from '../DotMatrixPanel';
import { StatusIndicator } from '../StatusIndicator';
import { ModelStatusResponse } from '@/types/models';
import styles from './SystemStatusPanel.module.css';

export interface SystemStatusPanelEnhancedProps {
  modelStatus: ModelStatusResponse;
  className?: string;
  title?: string;
  compact?: boolean;
  // Quick Actions callbacks
  onRescan?: () => void;
  onEnableAll?: () => void;
  onDisableAll?: () => void;
  isLoading?: boolean;
}

/**
 * Format uptime duration as human-readable string
 */
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
};

/**
 * Calculate system uptime from oldest model start time
 */
const calculateSystemUptime = (models: any[]): number => {
  if (models.length === 0) return 0;

  const maxUptime = Math.max(...models.map((m) => m.uptimeSeconds || 0));
  return maxUptime;
};

/**
 * Calculate context window utilization (placeholder - needs backend data)
 */
const calculateContextUtilization = (models: any[]): { percentage: number; tokensUsed: number; tokensTotal: number } => {
  // TODO: Implement when backend provides context window data
  // For now, estimate based on active queries
  const activeModels = models.filter((m) => m.state === 'processing');
  const percentage = Math.min(100, activeModels.length * 15); // Rough estimate
  const tokensTotal = 8000; // Default context window
  const tokensUsed = Math.round((percentage / 100) * tokensTotal);
  return { percentage, tokensUsed, tokensTotal };
};

export const SystemStatusPanelEnhanced: React.FC<SystemStatusPanelEnhancedProps> = ({
  modelStatus,
  className,
  title = 'SYSTEM STATUS',
  compact = false,
  onRescan,
  onEnableAll,
  onDisableAll,
  isLoading = false,
}) => {
  const navigate = useNavigate();

  // Calculate derived metrics
  const activeModels = useMemo(() => {
    const models = modelStatus.models.filter(
      (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
    );
    const byTier = {
      q2: models.filter((m) => m.tier === 'Q2').length,
      q3: models.filter((m) => m.tier === 'Q3').length,
      q4: models.filter((m) => m.tier === 'Q4').length,
    };
    return { total: models.length, ...byTier };
  }, [modelStatus.models]);

  const systemUptime = useMemo(
    () => calculateSystemUptime(modelStatus.models),
    [modelStatus.models]
  );

  const contextUtilization = useMemo(
    () => calculateContextUtilization(modelStatus.models),
    [modelStatus.models]
  );

  // Quick Actions Footer Component
  const QuickActionsFooter = () => (
    <div className={styles.quickActionsFooter}>
      <div className={styles.actionButtons}>
        <button onClick={onRescan} disabled={isLoading} className={styles.actionButton}>
          <span className={styles.actionIcon}>⟲</span>
          <span className={styles.actionLabel}>RE-SCAN</span>
        </button>
        <button onClick={onEnableAll} disabled={isLoading} className={styles.actionButton}>
          <span className={styles.actionIcon}>⊕</span>
          <span className={styles.actionLabel}>ENABLE ALL</span>
        </button>
        <button onClick={onDisableAll} disabled={isLoading} className={styles.actionButton}>
          <span className={styles.actionIcon}>⊖</span>
          <span className={styles.actionLabel}>DISABLE ALL</span>
        </button>
        <button onClick={() => navigate('/model-management')} className={styles.actionButton}>
          <span className={styles.actionIcon}>◧</span>
          <span className={styles.actionLabel}>MANAGE</span>
        </button>
      </div>
    </div>
  );

  // Enhanced empty state when no models are active
  if (activeModels.total === 0) {
    return (
      <DotMatrixPanel
        title={title}
        enableGrid
        gridDensity="dense"
        enableScanLines
        scanLineSpeed="slow"
        enableBorderGlow
        glowColor="orange"
        className={className}
      >
        <div className={styles.allModelsOffline}>
          {/* Prominent offline header */}
          <div className={styles.offlineHeader}>
            <div className={styles.offlineTitle}>ALL MODELS OFFLINE</div>
            <div className={styles.offlineSubtitle}>NEURAL SUBSTRATE INACTIVE</div>
          </div>

          {/* ASCII tree structure showing model hierarchy */}
          <div className={styles.searchTree}>
            <div className={styles.treeRoot}>
              <span className={styles.treeRootLabel}>SYNAPSE_ENGINE</span>
            </div>
            <div className={styles.treeTrunk}>
              <span className={styles.trunkLine}>│</span>
            </div>
            <div className={styles.treeBranches}>
              <div className={styles.branchLine}>
                <span className={styles.branchConnector}>├─</span>
                <span className={styles.branchLabel}>Q2 Neural Layer</span>
                <span className={styles.scanningDots}>░░░</span>
              </div>
              <div className={styles.branchLine}>
                <span className={styles.branchConnector}>├─</span>
                <span className={styles.branchLabel}>Q3 Neural Layer</span>
                <span className={styles.scanningDots}>░░░</span>
              </div>
              <div className={styles.branchLine}>
                <span className={styles.branchConnector}>└─</span>
                <span className={styles.branchLabel}>Q4 Neural Layer</span>
                <span className={styles.scanningDots}>░░░</span>
              </div>
            </div>
          </div>

          {/* Scanning status with animated indicator */}
          <div className={styles.scanningStatus}>
            <div className={styles.scanningLine}></div>
            <div className={styles.scanningText}>
              <span className={styles.scanningIcon}>◆</span>
              <span>Scanning for model instances</span>
              <span className={styles.scanningEllipsis}>...</span>
            </div>
          </div>

          {/* Action hint */}
          <div className={styles.offlineHint}>
            → Deploy models via Model Management to activate neural substrate
          </div>
        </div>

        {/* Quick Actions Footer */}
        <QuickActionsFooter />
      </DotMatrixPanel>
    );
  }

  return (
    <DotMatrixPanel
      title={title}
      enableGrid
      gridDensity="dense"
      enableScanLines
      scanLineSpeed="slow"
      enableBorderGlow
      glowColor="orange"
      className={className}
    >
      <div className={compact ? styles.compactGrid : styles.gridEnhanced}>
        {/* 1. Active Models with tier breakdown */}
        <div className={styles.metricRow}>
          <span className={styles.label}>ACTIVE MODELS</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {activeModels.total}
            </span>
            <span className={styles.breakdown}>
              {' '}(Q2:{activeModels.q2} Q3:{activeModels.q3} Q4:{activeModels.q4})
            </span>
          </span>
        </div>

        {/* 2. Active Queries */}
        <div className={styles.metricRow}>
          <span className={styles.label}>ACTIVE QUERIES</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {modelStatus.activeQueries}
            </span>
            {modelStatus.activeQueries > 0 && (
              <StatusIndicator
                status="processing"
                pulse
                showDot
                size="sm"
                className={styles.inlineStatus}
              />
            )}
          </span>
        </div>

        {/* 3. Cache Hit Rate (static value, no sparkline) */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CACHE HIT RATE</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {(modelStatus.cacheHitRate * 100).toFixed(1)}%
            </span>
            {modelStatus.cacheHitRate < 0.5 && (
              <StatusIndicator
                status="warning"
                showDot
                size="sm"
                className={styles.inlineStatus}
              />
            )}
          </span>
        </div>

        {/* 4. Context Window Utilization */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CONTEXT UTIL</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {contextUtilization.percentage.toFixed(1)}%
            </span>
            <span className={styles.breakdown}>
              {' '}({(contextUtilization.tokensUsed / 1000).toFixed(1)}K/{(contextUtilization.tokensTotal / 1000).toFixed(0)}K tokens)
            </span>
          </span>
        </div>

        {/* 5. System Uptime */}
        <div className={styles.metricRow}>
          <span className={styles.label}>SYSTEM UPTIME</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {formatUptime(systemUptime)}
            </span>
          </span>
        </div>
      </div>

      {/* Quick Actions Footer */}
      <QuickActionsFooter />
    </DotMatrixPanel>
  );
};

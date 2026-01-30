/**
 * ContextWindowPanel - Context window token allocation visualization
 *
 * Displays how the context window (token budget) is distributed across components:
 * 1. SYSTEM PROMPT - Model system instructions
 * 2. CGRAG CONTEXT - Retrieved artifacts from vector database
 * 3. USER QUERY - User's input query
 * 4. RESPONSE BUDGET - Reserved tokens for model response
 *
 * Visual Features:
 * - ASCII bar chart showing token allocation
 * - Color-coded utilization warnings (green/orange/red)
 * - Expandable CGRAG artifacts list with relevance scores
 * - Real-time updates via polling
 *
 * Backend Integration:
 * - REST API polling: GET /api/context/allocation/{query_id}
 * - Polls every 1s when query_id is available
 *
 * @see {@link ${PROJECT_DIR}/CLAUDE.md} for project context
 */

import React, { useState, useEffect } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import { useQuery } from '@tanstack/react-query';
import styles from './ContextWindowPanel.module.css';

/**
 * Context component breakdown
 */
interface ContextComponent {
  component: 'system_prompt' | 'cgrag_context' | 'user_query' | 'response_budget';
  tokens_used: number;
  tokens_allocated: number;
  percentage: number;
  content_preview?: string;
}

/**
 * CGRAG artifact metadata
 */
interface CGRAGArtifact {
  artifact_id: string;
  source_file: string;
  relevance_score: number;
  token_count: number;
  content_preview: string;
}

/**
 * Complete context allocation data from backend
 */
interface ContextAllocation {
  query_id: string;
  model_id: string;
  context_window_size: number;
  total_tokens_used: number;
  tokens_remaining: number;
  utilization_percentage: number;
  components: ContextComponent[];
  cgrag_artifacts: CGRAGArtifact[];
  warning?: string;
}

/**
 * ContextAllocationView - Visual token allocation display
 */
const ContextAllocationView: React.FC<{ allocation: ContextAllocation }> = ({ allocation }) => {
  /**
   * Map component type to human-readable label
   */
  const getComponentLabel = (component: string): string => {
    const labels: Record<string, string> = {
      system_prompt: 'SYSTEM PROMPT',
      cgrag_context: 'CGRAG CONTEXT',
      user_query: 'USER QUERY',
      response_budget: 'RESPONSE BUDGET',
    };
    return labels[component] ?? component.toUpperCase();
  };

  /**
   * Generate ASCII bar visualization (50 chars = 100%)
   */
  const renderBar = (percentage: number): string => {
    const maxBarLength = 50;
    const barLength = Math.round((percentage / 100) * maxBarLength);
    return '■'.repeat(Math.max(0, barLength));
  };

  /**
   * Get CSS class for utilization color coding
   */
  const getUtilizationColor = (percentage: number): string => {
    if (percentage < 60) return styles.utilizationLow ?? '';
    if (percentage < 80) return styles.utilizationMedium ?? '';
    return styles.utilizationHigh ?? '';
  };

  return (
    <div className={styles.allocationView}>
      {/* Token Budget Bars */}
      <div className={styles.budgetBars}>
        {allocation.components.map(component => {
          const label = getComponentLabel(component.component);
          const bar = renderBar(component.percentage);
          const percentage = component.percentage.toFixed(1);

          return (
            <div key={component.component} className={styles.budgetRow}>
              <span className={styles.componentLabel}>
                {label.padEnd(18)}
              </span>
              <span className={styles.bar}>
                [{bar}]
              </span>
              <span className={styles.tokenCount}>
                {component.tokens_used} tokens ({percentage}%)
              </span>
            </div>
          );
        })}
      </div>

      {/* Separator */}
      <div className={styles.separator}>
        ─────────────────────────────────────────────────────────────
      </div>

      {/* Summary */}
      <div className={styles.summary}>
        <span>TOTAL: {allocation.context_window_size} tokens</span>
        <span className={styles.divider}>|</span>
        <span className={getUtilizationColor(allocation.utilization_percentage)}>
          USED: {allocation.total_tokens_used} ({allocation.utilization_percentage.toFixed(1)}%)
        </span>
        <span className={styles.divider}>|</span>
        <span>REMAINING: {allocation.tokens_remaining}</span>
      </div>

      {/* Warning */}
      {allocation.warning && (
        <div className={styles.warning}>
          ⚠ {allocation.warning}
        </div>
      )}

      {/* CGRAG Artifacts List */}
      {allocation.cgrag_artifacts.length > 0 && (
        <details className={styles.artifactsDetails}>
          <summary className={styles.artifactsSummary}>
            CGRAG ARTIFACTS ({allocation.cgrag_artifacts.length})
          </summary>
          <div className={styles.artifactsList}>
            {allocation.cgrag_artifacts.map((artifact, idx) => (
              <div key={artifact.artifact_id} className={styles.artifact}>
                <div className={styles.artifactHeader}>
                  <span className={styles.artifactNumber}>#{idx + 1}</span>
                  <span className={styles.artifactFile}>{artifact.source_file}</span>
                  <span className={styles.artifactTokens}>{artifact.token_count} tokens</span>
                  <span className={styles.artifactScore}>
                    Relevance: {(artifact.relevance_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className={styles.artifactPreview}>
                  {artifact.content_preview}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
};

/**
 * ContextWindowPanel - Main component
 */
export const ContextWindowPanel: React.FC = () => {
  const [latestQueryId, setLatestQueryId] = useState<string | null>(null);
  const { events } = useSystemEventsContext();

  /**
   * Listen for new query submissions via WebSocket
   * Tracks the most recent query_id from pipeline or query events
   */
  useEffect(() => {
    // Find most recent query event
    const queryEvents = events.filter(
      (e: any) =>
        e.type === 'query_submitted' ||
        e.type === 'pipeline_stage_start' ||
        e.type?.includes('query') ||
        e.type?.includes('pipeline')
    );

    if (queryEvents.length > 0) {
      const latestEvent = queryEvents[queryEvents.length - 1] as any;
      if (latestEvent.query_id) {
        setLatestQueryId(latestEvent.query_id);
      }
    }
  }, [events]);

  /**
   * Poll context allocation for latest query
   * Refetch every 1s while query_id is available
   */
  const { data: allocation, isLoading } = useQuery<ContextAllocation | null>({
    queryKey: ['context-allocation', latestQueryId],
    queryFn: async () => {
      if (!latestQueryId) return null;

      const response = await fetch(`/api/context/allocation/${latestQueryId}`);

      // Return null if not found (context might not be tracked yet)
      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch context allocation: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!latestQueryId,
    refetchInterval: 1000, // Poll every 1s
    retry: false, // Don't retry on 404s
  });

  return (
    <AsciiPanel title="CONTEXT WINDOW ALLOCATION">
      <div className={styles.container}>
        {!latestQueryId || (!isLoading && !allocation) ? (
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>NO ALLOCATION DATA</p>
            <p className={styles.hint}>Submit a query to see token allocation</p>
          </div>
        ) : isLoading ? (
          <div className={styles.loadingState}>
            <p>LOADING ALLOCATION...</p>
          </div>
        ) : allocation ? (
          <ContextAllocationView allocation={allocation} />
        ) : null}
      </div>
    </AsciiPanel>
  );
};

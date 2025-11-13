/**
 * ProcessingPipelinePanel - Real-time query processing pipeline visualization
 *
 * Displays the 6-stage processing pipeline with ASCII flow diagram:
 * 1. INPUT - Query received
 * 2. COMPLEXITY - Complexity assessment (Q2/Q3/Q4 tier selection)
 * 3. CGRAG - Context retrieval from FAISS
 * 4. ROUTING - Model selection
 * 5. GENERATION - LLM response generation
 * 6. RESPONSE - Final response ready
 *
 * Visual States:
 * - Pending (gray) - Not started yet
 * - Active (cyan with pulse) - Currently processing
 * - Completed (phosphor orange) - Done
 * - Failed (red) - Error occurred
 *
 * Backend Integration:
 * - WebSocket events for real-time updates (pipeline_stage_start, pipeline_stage_complete, pipeline_stage_failed)
 * - REST API polling for pipeline status: GET /api/pipeline/status/{query_id}
 *
 * @see {@link /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/CLAUDE.md} for project context
 */

import React, { useState, useEffect, useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import { useQuery } from '@tanstack/react-query';
import styles from './ProcessingPipelinePanel.module.css';

/**
 * Pipeline stage configuration
 */
interface PipelineStage {
  stage_name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  start_time?: string;
  end_time?: string;
  duration_ms?: number;
  metadata: Record<string, any>;
}

/**
 * Pipeline status from backend API
 */
interface PipelineStatus {
  query_id: string;
  current_stage: 'input' | 'complexity' | 'cgrag' | 'routing' | 'generation' | 'response';
  overall_status: 'processing' | 'completed' | 'failed';
  stages: PipelineStage[];
  model_selected?: string;
  tier?: string;
  cgrag_artifacts_count?: number;
}

/**
 * PipelineFlow - ASCII flow diagram visualization
 */
const PipelineFlow: React.FC<{ status: PipelineStatus }> = ({ status }) => {
  /**
   * Get ASCII icon for stage status
   */
  const getStageIcon = (stage: PipelineStage): string => {
    switch (stage.status) {
      case 'pending':
        return '◯'; // Empty circle
      case 'active':
        return '●'; // Filled circle
      case 'completed':
        return '✓'; // Checkmark
      case 'failed':
        return '✗'; // X mark
    }
  };

  /**
   * Get CSS class for stage status
   */
  const getStageColor = (stage: PipelineStage): string => {
    switch (stage.status) {
      case 'pending':
        return styles.stagePending;
      case 'active':
        return styles.stageActive;
      case 'completed':
        return styles.stageCompleted;
      case 'failed':
        return styles.stageFailed;
    }
  };

  /**
   * Format stage metadata for display
   */
  const formatMetadata = (metadata: Record<string, any>): string => {
    if (!metadata || Object.keys(metadata).length === 0) {
      return '';
    }

    return Object.entries(metadata)
      .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
      .join(', ');
  };

  return (
    <div className={styles.asciiFlow}>
      {/* Pipeline stages */}
      <pre className={styles.flowDiagram}>
        {status.stages.map((stage, idx) => (
          <div key={stage.stage_name} className={getStageColor(stage)}>
            {getStageIcon(stage)} {stage.stage_name.toUpperCase()}
            {stage.duration_ms !== undefined && ` [${stage.duration_ms}ms]`}
            {idx < status.stages.length - 1 && (
              <div className={styles.arrow}>    ↓</div>
            )}
            {formatMetadata(stage.metadata) && (
              <div className={styles.metadata}>
                {formatMetadata(stage.metadata)}
              </div>
            )}
          </div>
        ))}
      </pre>

      {/* Summary on completion */}
      {status.overall_status === 'completed' && (
        <div className={styles.summary}>
          <p>✓ PIPELINE COMPLETE</p>
          {status.model_selected && (
            <p>Model: {status.model_selected} {status.tier && `(${status.tier})`}</p>
          )}
          {status.cgrag_artifacts_count !== undefined && (
            <p>CGRAG Artifacts: {status.cgrag_artifacts_count}</p>
          )}
        </div>
      )}

      {/* Error summary */}
      {status.overall_status === 'failed' && (
        <div className={styles.errorSummary}>
          <p>✗ PIPELINE FAILED</p>
          <p>Stage: {status.current_stage.toUpperCase()}</p>
          {status.stages.find(s => s.status === 'failed')?.metadata?.error && (
            <p className={styles.errorDetail}>
              {status.stages.find(s => s.status === 'failed')?.metadata?.error}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ProcessingPipelinePanel - Main component
 */
export const ProcessingPipelinePanel: React.FC = () => {
  const [latestQueryId, setLatestQueryId] = useState<string | null>(null);
  const { events } = useSystemEventsContext();

  /**
   * Listen for new query submissions via WebSocket
   * Tracks the most recent query_id from pipeline_stage_start events
   */
  useEffect(() => {
    // Find most recent pipeline_stage_start event with stage=input
    const pipelineEvents = events.filter(
      (e: any) => e.type === 'pipeline_stage_start' || e.type?.includes('pipeline')
    );

    if (pipelineEvents.length > 0) {
      const latestEvent = pipelineEvents[pipelineEvents.length - 1] as any;
      if (latestEvent.query_id) {
        setLatestQueryId(latestEvent.query_id);
      }
    }
  }, [events]);

  /**
   * Poll pipeline status for latest query
   * Refetch every 500ms while processing, stop when completed/failed
   */
  const { data: pipelineStatus, isLoading } = useQuery<PipelineStatus | null>({
    queryKey: ['pipeline-status', latestQueryId],
    queryFn: async () => {
      if (!latestQueryId) return null;

      const response = await fetch(`/api/pipeline/status/${latestQueryId}`);

      // Return null if not found (pipeline might not be tracked yet)
      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch pipeline status: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!latestQueryId,
    refetchInterval: (data) => {
      // Stop polling if pipeline is completed or failed
      if (data?.overall_status === 'completed' || data?.overall_status === 'failed') {
        return false;
      }
      // Poll every 500ms while processing
      return 500;
    },
    retry: false, // Don't retry on 404s
  });

  /**
   * Determine if we should show empty state
   */
  const showEmptyState = useMemo(() => {
    return !latestQueryId || (!isLoading && !pipelineStatus);
  }, [latestQueryId, isLoading, pipelineStatus]);

  return (
    <AsciiPanel title="NEURAL PROCESSING PIPELINE">
      <div className={styles.pipelineContainer}>
        {showEmptyState ? (
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>AWAITING QUERY...</p>
            <p className={styles.hint}>Submit a query to see the processing pipeline</p>
          </div>
        ) : isLoading ? (
          <div className={styles.loadingState}>
            <p>INITIALIZING PIPELINE...</p>
          </div>
        ) : pipelineStatus ? (
          <PipelineFlow status={pipelineStatus} />
        ) : null}
      </div>
    </AsciiPanel>
  );
};

/**
 * CustomNode Component - React Flow Custom Node for System Topology
 *
 * Renders a terminal-styled node with:
 * - Type-specific icon
 * - Status-dependent border color and glow
 * - Node label and metadata
 * - Pulsing animation for active nodes
 *
 * Node Types:
 * - orchestrator:  Neural Substrate Orchestrator
 * - model:  LLM Model Instance (Q2/Q3/Q4)
 * - service:  Service (CGRAG, WebSearch, Cache)
 * - storage:  Storage (FAISS, Redis)
 *
 * Status Colors:
 * - healthy: phosphor green (#00ff00)
 * - degraded: amber (#ff9500)
 * - unhealthy: red (#ff0000)
 * - offline: gray (#666666)
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import styles from './CustomNode.module.css';

interface CustomNodeData {
  label: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  nodeType: 'orchestrator' | 'model' | 'service' | 'storage';
  metadata: {
    version?: string;
    uptime_hours?: number;
    queries_processed?: number;
    tier?: string;
    memory_usage_mb?: number;
  };
  isHighlighted?: boolean;
}

/**
 * Get icon emoji based on node type
 */
const getNodeIcon = (type: CustomNodeData['nodeType']): string => {
  const icons = {
    orchestrator: '',
    model: '',
    service: '',
    storage: '',
  };
  return icons[type] || '◆';
};

/**
 * Format uptime hours to human-readable string
 */
const formatUptime = (hours?: number): string => {
  if (!hours) return '--';
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${Math.round(hours)}h`;
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return `${days}d ${remainingHours}h`;
};

/**
 * CustomNode Component
 */
export const CustomNode = memo<NodeProps<CustomNodeData>>(({ data }) => {
  const { label, status, nodeType, metadata, isHighlighted } = data;

  return (
    <div
      className={`${styles.customNode} ${styles[`status-${status}`]} ${
        isHighlighted ? styles.highlighted : ''
      }`}
      data-status={status}
      data-node-type={nodeType}
    >
      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className={styles.handle}
        id="top"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className={styles.handle}
        id="bottom"
      />
      <Handle
        type="target"
        position={Position.Left}
        className={styles.handle}
        id="left"
      />
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
        id="right"
      />

      {/* Node Content */}
      <div className={styles.nodeContent}>
        {/* Icon */}
        <div className={styles.nodeIcon}>{getNodeIcon(nodeType)}</div>

        {/* Label */}
        <div className={styles.nodeLabel}>{label}</div>

        {/* Status Badge */}
        <div className={styles.statusBadge} data-status={status}>
          {status.toUpperCase()}
        </div>

        {/* Metadata */}
        <div className={styles.nodeMetadata}>
          {metadata.tier && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>TIER:</span>
              <span className={styles.metadataValue}>{metadata.tier}</span>
            </div>
          )}
          {metadata.uptime_hours !== undefined && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>UP:</span>
              <span className={styles.metadataValue}>
                {formatUptime(metadata.uptime_hours)}
              </span>
            </div>
          )}
          {metadata.queries_processed !== undefined && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>QUERIES:</span>
              <span className={styles.metadataValue}>
                {metadata.queries_processed}
              </span>
            </div>
          )}
          {metadata.memory_usage_mb !== undefined && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>MEM:</span>
              <span className={styles.metadataValue}>
                {metadata.memory_usage_mb.toFixed(0)}MB
              </span>
            </div>
          )}
          {metadata.version && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>VER:</span>
              <span className={styles.metadataValue}>{metadata.version}</span>
            </div>
          )}
        </div>
      </div>

      {/* Highlight Pulse Effect */}
      {isHighlighted && <div className={styles.highlightPulse} />}
    </div>
  );
});

CustomNode.displayName = 'CustomNode';

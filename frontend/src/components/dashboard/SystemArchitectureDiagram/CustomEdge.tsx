/**
 * CustomEdge Component - React Flow Custom Edge for System Connections
 *
 * Renders a terminal-styled edge with:
 * - Connection type styling (data_flow, control, dependency)
 * - Edge label showing connection type and metadata
 * - Animated flow particles for active connections
 * - Hover tooltip with throughput and latency
 *
 * Connection Types:
 * - data_flow: Solid orange line with arrow (query data flow)
 * - control: Dashed cyan line (control signals, health checks)
 * - dependency: Dotted gray line (service dependencies)
 */

import React, { memo } from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import styles from './CustomEdge.module.css';

interface CustomEdgeData {
  connectionType: 'data_flow' | 'control' | 'dependency';
  active: boolean;
  metadata: {
    throughput_qps?: number;
    avg_latency_ms?: number;
  };
}

/**
 * Get edge style based on connection type
 */
const getEdgeStyle = (
  type: CustomEdgeData['connectionType'],
  active: boolean
) => {
  const baseStyle: React.CSSProperties = {
    strokeWidth: 2,
  };

  switch (type) {
    case 'data_flow':
      return {
        ...baseStyle,
        stroke: active ? 'var(--webtui-primary, #ff9500)' : '#ff950080',
        strokeDasharray: undefined,
      };
    case 'control':
      return {
        ...baseStyle,
        stroke: active ? 'var(--webtui-accent, #00ffff)' : '#00ffff80',
        strokeDasharray: '5,5',
      };
    case 'dependency':
      return {
        ...baseStyle,
        stroke: active ? '#888' : '#66666680',
        strokeDasharray: '2,3',
        strokeWidth: 1,
      };
    default:
      return baseStyle;
  }
};

/**
 * CustomEdge Component
 */
export const CustomEdge = memo<EdgeProps<CustomEdgeData>>(
  ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    markerEnd,
  }) => {
    const connectionType = data?.connectionType || 'data_flow';
    const active = data?.active ?? false;
    const metadata = data?.metadata || {};

    const [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });

    const edgeStyle = getEdgeStyle(connectionType, active);

    // Format metadata for tooltip
    const tooltipContent = [];
    if (metadata.throughput_qps !== undefined) {
      tooltipContent.push(`${metadata.throughput_qps.toFixed(2)} QPS`);
    }
    if (metadata.avg_latency_ms !== undefined) {
      tooltipContent.push(`${metadata.avg_latency_ms.toFixed(0)}ms avg`);
    }

    return (
      <>
        {/* Base Edge Path */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={markerEnd}
          style={edgeStyle}
        />

        {/* Edge Label */}
        <EdgeLabelRenderer>
          <div
            className={`${styles.edgeLabel} ${
              active ? styles.active : styles.inactive
            }`}
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: 'all',
            }}
            title={tooltipContent.join(' | ')}
          >
            <div className={styles.labelContent}>
              <span className={styles.labelType}>
                {connectionType.replace('_', ' ').toUpperCase()}
              </span>
              {tooltipContent.length > 0 && (
                <span className={styles.labelMetadata}>
                  {tooltipContent.join(' | ')}
                </span>
              )}
            </div>
          </div>
        </EdgeLabelRenderer>

        {/* Animated Flow Particle (only for active data_flow) */}
        {active && connectionType === 'data_flow' && (
          <EdgeLabelRenderer>
            <div
              className={styles.flowParticle}
              style={{
                position: 'absolute',
                transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                pointerEvents: 'none',
              }}
            >
              <div className={styles.particle} />
            </div>
          </EdgeLabelRenderer>
        )}
      </>
    );
  }
);

CustomEdge.displayName = 'CustomEdge';

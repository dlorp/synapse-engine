/**
 * SystemArchitectureDiagram Component - Interactive System Topology Visualization
 *
 * Phase 4, Component 4 - Real-time interactive node-based topology diagram using React Flow.
 *
 * Features:
 * - Interactive node graph with pan/zoom controls
 * - Custom nodes for orchestrator, models, services, storage
 * - Custom edges for data flow, control, and dependencies
 * - Health status visualization (color-coded, pulsing animations)
 * - Real-time updates via polling and WebSocket events
 * - Query path traversal animation
 * - Detailed health metrics popup on node click
 * - Terminal aesthetic with phosphor orange theme
 *
 * API Endpoints:
 * - GET /api/topology - Full system topology with nodes, connections, health
 * - GET /api/topology/health/{component_id} - Component-specific health metrics
 * - GET /api/topology/dataflow/{query_id} - Query traversal path
 *
 * WebSocket Events:
 * - topology_health_update - Real-time health status changes
 * - query_started - New query submitted (triggers path visualization)
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  NodeTypes,
  EdgeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AsciiPanel, TerminalSpinner } from '@/components/terminal';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import { CustomNode } from './CustomNode';
import { CustomEdge } from './CustomEdge';
import { HealthMetricsPopup } from './HealthMetricsPopup';
import styles from './SystemArchitectureDiagram.module.css';

// ============================================================================
// TypeScript Interfaces
// ============================================================================

export interface ComponentNode {
  id: string;
  type: 'orchestrator' | 'model' | 'service' | 'storage';
  label: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  metadata: {
    version?: string;
    uptime_hours?: number;
    queries_processed?: number;
    tier?: string;
    memory_usage_mb?: number;
  };
  position: { x: number; y: number };
}

export interface ComponentConnection {
  source: string;
  target: string;
  type: 'data_flow' | 'control' | 'dependency';
  label: string;
  active: boolean;
  metadata: {
    throughput_qps?: number;
    avg_latency_ms?: number;
  };
}

export interface SystemTopology {
  nodes: ComponentNode[];
  connections: ComponentConnection[];
  last_updated: string;
  overall_health: 'healthy' | 'degraded' | 'unhealthy';
}

export interface HealthMetrics {
  component_id: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  uptime_seconds: number;
  memory_usage_mb: number;
  cpu_percent: number;
  error_rate: number;
  avg_latency_ms: number;
  last_check: string;
}

interface QueryPathNode {
  node_id: string;
  timestamp: string;
  duration_ms?: number;
}

interface QueryPath {
  query_id: string;
  path: QueryPathNode[];
  total_duration_ms: number;
}

// ============================================================================
// Main Component
// ============================================================================

export const SystemArchitectureDiagram: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [queryPath, setQueryPath] = useState<QueryPath | null>(null);
  const [animatingPathIndex, setAnimatingPathIndex] = useState<number>(-1);

  const { events } = useSystemEventsContext();

  // ============================================================================
  // API Queries
  // ============================================================================

  // Fetch system topology
  const { data: topology, isLoading } = useQuery<SystemTopology>({
    queryKey: ['system-topology'],
    queryFn: async () => {
      const response = await fetch('/api/topology/');
      if (!response.ok) throw new Error('Failed to fetch topology');
      return response.json();
    },
    refetchInterval: 5000, // Poll every 5 seconds for health updates
  });

  // ============================================================================
  // Node & Edge Type Registration
  // ============================================================================

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      customNode: CustomNode,
    }),
    []
  );

  const edgeTypes: EdgeTypes = useMemo(
    () => ({
      customEdge: CustomEdge,
    }),
    []
  );

  // ============================================================================
  // Transform API Data to React Flow Format
  // ============================================================================

  useEffect(() => {
    if (!topology) return;

    // Transform nodes
    const flowNodes: Node[] = topology.nodes.map((node) => ({
      id: node.id,
      type: 'customNode',
      position: node.position,
      data: {
        label: node.label,
        status: node.status,
        nodeType: node.type,
        metadata: node.metadata,
        isHighlighted: false,
      },
    }));

    // Transform edges
    const flowEdges: Edge[] = topology.connections.map((conn, idx) => ({
      id: `edge-${idx}`,
      source: conn.source,
      target: conn.target,
      type: 'customEdge',
      label: conn.label,
      data: {
        connectionType: conn.type,
        active: conn.active,
        metadata: conn.metadata,
      },
      animated: conn.active,
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [topology, setNodes, setEdges]);

  // ============================================================================
  // WebSocket Event Handling
  // ============================================================================

  // Listen for model state changes (topology health updates)
  useEffect(() => {
    const stateChanges = events.filter(
      (event) => event.type === 'model_state'
    );

    if (stateChanges.length === 0) return;

    // Get most recent state change
    const latestUpdate = stateChanges[stateChanges.length - 1];

    // Update node status based on model state changes
    // Parse message for model ID and status if available
    if (latestUpdate && latestUpdate.message) {
      // Message format: "Model <id> state changed to <status>"
      const match = latestUpdate.message.match(/Model (\S+) state changed to (\S+)/);
      if (match) {
        const [, modelId, status] = match;
        setNodes((nds) =>
          nds.map((node) => {
            if (node.id === modelId) {
              // Map model state to topology status
              let nodeStatus: 'healthy' | 'degraded' | 'unhealthy' | 'offline' = 'healthy';
              if (status === 'active' || status === 'idle') nodeStatus = 'healthy';
              else if (status === 'processing') nodeStatus = 'healthy';
              else if (status === 'error') nodeStatus = 'unhealthy';
              else if (status === 'offline') nodeStatus = 'offline';

              return {
                ...node,
                data: {
                  ...node.data,
                  status: nodeStatus,
                },
              };
            }
            return node;
          })
        );
      }
    }
  }, [events, setNodes]);

  // Listen for query routing events (query path visualization)
  useEffect(() => {
    const routeEvents = events.filter(
      (event) => event.type === 'query_route'
    );

    if (routeEvents.length === 0) return;

    const latestQuery = routeEvents[routeEvents.length - 1];

    // Extract query ID from message if available
    if (latestQuery && latestQuery.message) {
      // Message format might contain query ID
      const match = latestQuery.message.match(/query[_\s]?id[:\s]+([a-zA-Z0-9-]+)/i);
      if (match) {
        const queryId = match[1];
        if (queryId) {
          fetchQueryPath(queryId);
        }
      }
    }
  }, [events]);

  // ============================================================================
  // Query Path Visualization
  // ============================================================================

  const fetchQueryPath = async (queryId: string) => {
    try {
      const response = await fetch(`/api/topology/dataflow/${queryId}`);
      if (!response.ok) throw new Error('Failed to fetch query path');
      const path: QueryPath = await response.json();
      setQueryPath(path);
      setAnimatingPathIndex(0);
    } catch (error) {
      console.error('Error fetching query path:', error);
    }
  };

  // Animate query traversal through nodes
  useEffect(() => {
    if (!queryPath || animatingPathIndex < 0) return;
    if (animatingPathIndex >= queryPath.path.length) {
      // Animation complete
      setAnimatingPathIndex(-1);
      setQueryPath(null);
      return;
    }

    const currentNode = queryPath.path[animatingPathIndex];
    const duration = currentNode?.duration_ms || 500;

    // Highlight current node
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          isHighlighted: node.id === currentNode?.node_id,
        },
      }))
    );

    // Move to next node after duration
    const timer = setTimeout(() => {
      setAnimatingPathIndex((prev) => prev + 1);
    }, duration);

    return () => clearTimeout(timer);
  }, [queryPath, animatingPathIndex, setNodes]);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
    },
    []
  );

  const handleClosePopup = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // ============================================================================
  // Render
  // ============================================================================

  if (isLoading) {
    return (
      <AsciiPanel title="SYSTEM ARCHITECTURE TOPOLOGY">
        <div className={styles.emptyState}>
          <TerminalSpinner style="arc" size={24} />
          <div className={styles.emptyText}>LOADING SYSTEM TOPOLOGY...</div>
        </div>
      </AsciiPanel>
    );
  }

  if (!topology) {
    return (
      <AsciiPanel title="SYSTEM ARCHITECTURE TOPOLOGY">
        <div className={styles.emptyState}>
          <div className={styles.emptyText}>SYSTEM TOPOLOGY OFFLINE</div>
          <div className={styles.emptySubtext}>
            UNABLE TO CONNECT TO TOPOLOGY SERVICE
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel title="SYSTEM ARCHITECTURE TOPOLOGY">
      <div className={styles.diagramContainer}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          className={styles.reactFlow}
          minZoom={0.2}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        >
          <Controls className={styles.controls} />
          <Background
            variant={BackgroundVariant.Dots}
            gap={12}
            size={1}
            color="rgba(255, 149, 0, 0.1)"
          />
        </ReactFlow>

        {/* Query Path Indicator */}
        {queryPath && animatingPathIndex >= 0 && (
          <div className={styles.queryPathIndicator}>
            <div className={styles.queryPathLabel}>
              QUERY PATH: {queryPath.query_id}
            </div>
            <div className={styles.queryPathProgress}>
              NODE {animatingPathIndex + 1} / {queryPath.path.length}
            </div>
          </div>
        )}

        {/* Health metrics popup */}
        {selectedNode && (
          <HealthMetricsPopup
            componentId={selectedNode}
            onClose={handleClosePopup}
          />
        )}

        {/* Legend */}
        <div className={styles.legend}>
          <div className={styles.legendTitle}>LEGEND</div>
          <div className={styles.legendItem}>
            <div
              className={styles.legendDot}
              style={{ backgroundColor: 'var(--webtui-success)' }}
            />
            <span>HEALTHY</span>
          </div>
          <div className={styles.legendItem}>
            <div
              className={styles.legendDot}
              style={{ backgroundColor: 'var(--webtui-primary)' }}
            />
            <span>DEGRADED</span>
          </div>
          <div className={styles.legendItem}>
            <div
              className={styles.legendDot}
              style={{ backgroundColor: 'var(--webtui-error)' }}
            />
            <span>UNHEALTHY</span>
          </div>
          <div className={styles.legendItem}>
            <div
              className={styles.legendDot}
              style={{ backgroundColor: '#666' }}
            />
            <span>OFFLINE</span>
          </div>
        </div>

        {/* System Health Badge */}
        <div
          className={`${styles.healthBadge} ${styles[topology.overall_health]}`}
        >
          SYSTEM: {topology.overall_health.toUpperCase()}
        </div>
      </div>
    </AsciiPanel>
  );
};

/**
 * NetworkGraph Component - Canvas-based network visualization
 *
 * Real-time network graph showing model connections, query routing, and CGRAG flow.
 * Uses force-directed layout with physics simulation for organic movement.
 *
 * Features:
 * - Phosphor orange (#ff9500) nodes with pulsating glow
 * - Cyan (#00ffff) links for data flow
 * - Interactive hover states with border glow
 * - 60fps canvas rendering
 * - Reduced motion support
 */

import React, { useRef, useEffect, useCallback, useMemo } from 'react';
import { TerminalEffect } from '../TerminalEffect';
import styles from './NetworkGraph.module.css';

export interface NetworkNode {
  id: string;
  label: string;
  type: 'model' | 'cgrag' | 'query' | 'cache';
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  active?: boolean;
  value?: number; // Link strength/weight
}

export interface NetworkGraphProps {
  nodes: NetworkNode[];
  links: NetworkLink[];
  width?: number;
  height?: number;
  className?: string;
  onNodeClick?: (node: NetworkNode) => void;
  onNodeHover?: (node: NetworkNode | null) => void;
}

interface SimulationNode extends NetworkNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const NODE_RADIUS = 8;
const LINK_WIDTH = 2;
const FORCE_STRENGTH = 0.05;
const DAMPING = 0.8;
const CENTER_FORCE = 0.01;

export const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  links,
  width = 600,
  height = 400,
  className,
  onNodeClick,
  onNodeHover,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const hoveredNodeRef = useRef<string | null>(null);
  const simulationNodesRef = useRef<SimulationNode[]>([]);
  const mousePositionRef = useRef({ x: 0, y: 0 });

  // Initialize simulation nodes
  const initializeNodes = useCallback(() => {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.3;

    simulationNodesRef.current = nodes.map((node, i) => {
      const angle = (i / nodes.length) * Math.PI * 2;
      return {
        ...node,
        x: node.x ?? centerX + Math.cos(angle) * radius,
        y: node.y ?? centerY + Math.sin(angle) * radius,
        vx: node.vx ?? 0,
        vy: node.vy ?? 0,
      };
    });
  }, [nodes, width, height]);

  // Physics simulation step
  const simulatePhysics = useCallback(() => {
    const simNodes = simulationNodesRef.current;
    const centerX = width / 2;
    const centerY = height / 2;

    // Apply forces
    for (let i = 0; i < simNodes.length; i++) {
      const nodeA = simNodes[i];

      // Center force (gravity toward center)
      const dx = centerX - nodeA.x;
      const dy = centerY - nodeA.y;
      nodeA.vx += dx * CENTER_FORCE;
      nodeA.vy += dy * CENTER_FORCE;

      // Repulsion between nodes
      for (let j = i + 1; j < simNodes.length; j++) {
        const nodeB = simNodes[j];
        const dx = nodeB.x - nodeA.x;
        const dy = nodeB.y - nodeA.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 100 && dist > 0) {
          const force = (100 - dist) / dist * FORCE_STRENGTH;
          nodeA.vx -= dx * force;
          nodeA.vy -= dy * force;
          nodeB.vx += dx * force;
          nodeB.vy += dy * force;
        }
      }

      // Attraction along links
      links.forEach(link => {
        const isSource = link.source === nodeA.id;
        const isTarget = link.target === nodeA.id;

        if (isSource || isTarget) {
          const otherNodeId = isSource ? link.target : link.source;
          const otherNode = simNodes.find(n => n.id === otherNodeId);

          if (otherNode) {
            const dx = otherNode.x - nodeA.x;
            const dy = otherNode.y - nodeA.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const targetDist = 80;

            if (dist > 0) {
              const force = (dist - targetDist) / dist * FORCE_STRENGTH * 0.5;
              nodeA.vx += dx * force;
              nodeA.vy += dy * force;
            }
          }
        }
      });

      // Apply damping
      nodeA.vx *= DAMPING;
      nodeA.vy *= DAMPING;

      // Update position
      nodeA.x += nodeA.vx;
      nodeA.y += nodeA.vy;

      // Keep in bounds
      nodeA.x = Math.max(NODE_RADIUS * 2, Math.min(width - NODE_RADIUS * 2, nodeA.x));
      nodeA.y = Math.max(NODE_RADIUS * 2, Math.min(height - NODE_RADIUS * 2, nodeA.y));
    }
  }, [links, width, height]);

  // Render graph to canvas
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const simNodes = simulationNodesRef.current;

    // Draw links
    ctx.lineWidth = LINK_WIDTH;
    links.forEach(link => {
      const sourceNode = simNodes.find(n => n.id === link.source);
      const targetNode = simNodes.find(n => n.id === link.target);

      if (sourceNode && targetNode) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x, sourceNode.y);
        ctx.lineTo(targetNode.x, targetNode.y);

        // Active links in cyan, inactive in darker orange
        if (link.active) {
          ctx.strokeStyle = '#00ffff';
          ctx.shadowBlur = 8;
          ctx.shadowColor = '#00ffff';
        } else {
          ctx.strokeStyle = 'rgba(255, 149, 0, 0.3)';
          ctx.shadowBlur = 0;
        }

        ctx.stroke();
        ctx.shadowBlur = 0;
      }
    });

    // Draw nodes
    simNodes.forEach(node => {
      const isHovered = hoveredNodeRef.current === node.id;

      ctx.beginPath();
      ctx.arc(node.x, node.y, NODE_RADIUS, 0, Math.PI * 2);

      // Node color by type
      switch (node.type) {
        case 'model':
          ctx.fillStyle = '#ff9500';
          break;
        case 'cgrag':
          ctx.fillStyle = '#00ffff';
          break;
        case 'query':
          ctx.fillStyle = '#ff0000';
          break;
        case 'cache':
          ctx.fillStyle = '#00ff00';
          break;
        default:
          ctx.fillStyle = '#ff9500';
      }

      ctx.fill();

      // Phosphor glow
      const glowRadius = isHovered ? NODE_RADIUS * 3 : NODE_RADIUS * 2;
      const glowIntensity = isHovered ? 0.4 : 0.2;

      ctx.shadowBlur = glowRadius;
      ctx.shadowColor = ctx.fillStyle;
      ctx.globalAlpha = glowIntensity;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.shadowBlur = 0;

      // Draw label
      if (isHovered) {
        ctx.fillStyle = '#ff9500';
        ctx.font = '10px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowBlur = 4;
        ctx.shadowColor = '#ff9500';
        ctx.fillText(node.label, node.x, node.y - NODE_RADIUS - 8);
        ctx.shadowBlur = 0;
      }
    });
  }, [links, width, height]);

  // Animation loop
  const animate = useCallback(() => {
    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!prefersReducedMotion) {
      simulatePhysics();
    }

    render();
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [simulatePhysics, render]);

  // Mouse move handler for hover detection
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    mousePositionRef.current = { x, y };

    // Find hovered node
    const simNodes = simulationNodesRef.current;
    const hoveredNode = simNodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      return Math.sqrt(dx * dx + dy * dy) <= NODE_RADIUS;
    });

    const newHoveredId = hoveredNode?.id ?? null;

    if (newHoveredId !== hoveredNodeRef.current) {
      hoveredNodeRef.current = newHoveredId;

      if (onNodeHover) {
        const actualNode = hoveredNode ? nodes.find(n => n.id === hoveredNode.id) ?? null : null;
        onNodeHover(actualNode);
      }

      // Update cursor
      canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
    }
  }, [nodes, onNodeHover]);

  // Mouse click handler
  const handleMouseClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onNodeClick) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const simNodes = simulationNodesRef.current;
    const clickedNode = simNodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      return Math.sqrt(dx * dx + dy * dy) <= NODE_RADIUS;
    });

    if (clickedNode) {
      const actualNode = nodes.find(n => n.id === clickedNode.id);
      if (actualNode) {
        onNodeClick(actualNode);
      }
    }
  }, [nodes, onNodeClick]);

  // Initialize and start animation
  useEffect(() => {
    initializeNodes();
    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [initializeNodes, animate]);

  // Update nodes when props change
  useEffect(() => {
    initializeNodes();
  }, [nodes, initializeNodes]);

  return (
    <TerminalEffect
      enableScanLines
      scanLineSpeed="slow"
      enablePhosphorGlow
      phosphorColor="orange"
      className={className}
    >
      <div className={styles.container}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className={styles.canvas}
          onMouseMove={handleMouseMove}
          onClick={handleMouseClick}
          aria-label="Network graph visualization"
        />
      </div>
    </TerminalEffect>
  );
};

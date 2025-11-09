/**
 * HeatMap Component - Canvas-based heat map visualization
 *
 * Dot-matrix-style grid heat map for metrics visualization.
 * Shows intensity with color gradients and phosphor glow on hot spots.
 *
 * Features:
 * - Dot-matrix grid with color intensity
 * - Phosphor glow on high-intensity cells
 * - Configurable color gradient (orange → red)
 * - Smooth value transitions
 * - 60fps canvas rendering
 * - Row/column labels with phosphor-glow-static-orange
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { DotMatrixPanel } from '../DotMatrixPanel';
import styles from './HeatMap.module.css';

export interface HeatMapCell {
  row: number;
  col: number;
  value: number; // 0-1 normalized intensity
}

export interface HeatMapProps {
  data: HeatMapCell[];
  rows: number;
  cols: number;
  rowLabels?: string[];
  colLabels?: string[];
  width?: number;
  height?: number;
  className?: string;
  colorScale?: 'orange-red' | 'cyan-blue' | 'green-yellow';
  showLabels?: boolean;
  minValue?: number;
  maxValue?: number;
  onCellClick?: (row: number, col: number, value: number) => void;
  onCellHover?: (row: number, col: number, value: number) => void;
}

const LABEL_MARGIN = 40;
const CELL_PADDING = 2;

export const HeatMap: React.FC<HeatMapProps> = ({
  data,
  rows,
  cols,
  rowLabels,
  colLabels,
  width = 600,
  height = 400,
  className,
  colorScale = 'orange-red',
  showLabels = true,
  minValue = 0,
  maxValue = 1,
  onCellClick,
  onCellHover,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const currentDataRef = useRef<Map<string, number>>(new Map());
  const targetDataRef = useRef<Map<string, number>>(new Map());

  // Color scale functions
  const getColor = useCallback((value: number): string => {
    // Clamp value between 0 and 1
    const normalized = Math.max(0, Math.min(1, value));

    switch (colorScale) {
      case 'orange-red': {
        const r = 255;
        const g = Math.floor(149 * (1 - normalized)); // 149 (orange) → 0 (red)
        const b = 0;
        return `rgb(${r}, ${g}, ${b})`;
      }
      case 'cyan-blue': {
        const r = 0;
        const g = Math.floor(255 * (1 - normalized * 0.5)); // Fade cyan to blue
        const b = 255;
        return `rgb(${r}, ${g}, ${b})`;
      }
      case 'green-yellow': {
        const r = Math.floor(255 * normalized);
        const g = 255;
        const b = 0;
        return `rgb(${r}, ${g}, ${b})`;
      }
      default:
        return '#ff9500';
    }
  }, [colorScale]);

  // Smooth interpolation for value transitions
  const interpolate = useCallback((current: number, target: number, speed: number = 0.1): number => {
    return current + (target - current) * speed;
  }, []);

  // Update target data from props
  useEffect(() => {
    const newTargets = new Map<string, number>();

    data.forEach(cell => {
      const key = `${cell.row},${cell.col}`;
      // Normalize value to 0-1 range
      const normalized = (cell.value - minValue) / (maxValue - minValue);
      newTargets.set(key, normalized);
    });

    targetDataRef.current = newTargets;
  }, [data, minValue, maxValue]);

  // Render heat map to canvas
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Calculate grid dimensions
    const labelOffset = showLabels ? LABEL_MARGIN : 0;
    const gridWidth = width - labelOffset;
    const gridHeight = height - labelOffset;
    const cellWidth = gridWidth / cols;
    const cellHeight = gridHeight / rows;

    // Update current values with smooth interpolation
    const currentData = currentDataRef.current;
    const targetData = targetDataRef.current;

    targetData.forEach((targetValue, key) => {
      const currentValue = currentData.get(key) ?? 0;
      const newValue = interpolate(currentValue, targetValue, 0.1);
      currentData.set(key, newValue);
    });

    // Draw cells
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const key = `${row},${col}`;
        const value = currentData.get(key) ?? 0;

        const x = labelOffset + col * cellWidth;
        const y = row * cellHeight;

        // Draw cell
        ctx.fillStyle = getColor(value);
        ctx.fillRect(
          x + CELL_PADDING,
          y + CELL_PADDING,
          cellWidth - CELL_PADDING * 2,
          cellHeight - CELL_PADDING * 2
        );

        // Add phosphor glow for high-intensity cells
        if (value > 0.5) {
          ctx.shadowBlur = value * 12;
          ctx.shadowColor = getColor(value);
          ctx.fillRect(
            x + CELL_PADDING,
            y + CELL_PADDING,
            cellWidth - CELL_PADDING * 2,
            cellHeight - CELL_PADDING * 2
          );
          ctx.shadowBlur = 0;
        }
      }
    }

    // Draw labels
    if (showLabels) {
      ctx.fillStyle = '#ff9500';
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';

      // Row labels
      for (let row = 0; row < rows; row++) {
        const label = rowLabels?.[row] ?? `R${row}`;
        const y = row * cellHeight + cellHeight / 2;

        ctx.shadowBlur = 4;
        ctx.shadowColor = '#ff9500';
        ctx.fillText(label, labelOffset - 5, y);
      }

      // Column labels
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';

      for (let col = 0; col < cols; col++) {
        const label = colLabels?.[col] ?? `C${col}`;
        const x = labelOffset + col * cellWidth + cellWidth / 2;

        ctx.shadowBlur = 4;
        ctx.shadowColor = '#ff9500';
        ctx.fillText(label, x, height - LABEL_MARGIN + 5);
      }

      ctx.shadowBlur = 0;
    }
  }, [width, height, rows, cols, showLabels, rowLabels, colLabels, getColor, interpolate]);

  // Animation loop
  const animate = useCallback(() => {
    render();
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [render]);

  // Mouse move handler for hover detection
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onCellHover) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const labelOffset = showLabels ? LABEL_MARGIN : 0;
    const gridWidth = width - labelOffset;
    const gridHeight = height - labelOffset;
    const cellWidth = gridWidth / cols;
    const cellHeight = gridHeight / rows;

    // Check if mouse is over grid area
    if (x >= labelOffset && y < height - (showLabels ? LABEL_MARGIN : 0)) {
      const col = Math.floor((x - labelOffset) / cellWidth);
      const row = Math.floor(y / cellHeight);

      if (row >= 0 && row < rows && col >= 0 && col < cols) {
        const key = `${row},${col}`;
        const value = currentDataRef.current.get(key) ?? 0;
        onCellHover(row, col, value);
      }
    }
  }, [width, height, rows, cols, showLabels, onCellHover]);

  // Mouse click handler
  const handleMouseClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onCellClick) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const labelOffset = showLabels ? LABEL_MARGIN : 0;
    const gridWidth = width - labelOffset;
    const gridHeight = height - labelOffset;
    const cellWidth = gridWidth / cols;
    const cellHeight = gridHeight / rows;

    if (x >= labelOffset && y < height - (showLabels ? LABEL_MARGIN : 0)) {
      const col = Math.floor((x - labelOffset) / cellWidth);
      const row = Math.floor(y / cellHeight);

      if (row >= 0 && row < rows && col >= 0 && col < cols) {
        const key = `${row},${col}`;
        const value = currentDataRef.current.get(key) ?? 0;
        onCellClick(row, col, value);
      }
    }
  }, [width, height, rows, cols, showLabels, onCellClick]);

  // Start animation on mount
  useEffect(() => {
    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [animate]);

  return (
    <DotMatrixPanel
      enableGrid
      gridDensity="dense"
      enableScanLines
      scanLineSpeed="slow"
      enableBorderGlow
      glowColor="orange"
      className={className}
      noPadding
    >
      <div className={styles.container}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className={styles.canvas}
          onMouseMove={handleMouseMove}
          onClick={handleMouseClick}
          aria-label="Heat map visualization"
        />
      </div>
    </DotMatrixPanel>
  );
};

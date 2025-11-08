import React, { useMemo } from 'react';
import type { DiscoveredModel } from '@/types/models';
import styles from './PortSelector.module.css';

export interface PortSelectorProps {
  model: DiscoveredModel;
  allModels: DiscoveredModel[];
  portRange: [number, number];
  isServerRunning: boolean;
  onPortChange: (modelId: string, port: number) => Promise<void>;
}

/**
 * PortSelector - Dropdown for selecting model port with conflict detection
 *
 * Features:
 * - Shows only available ports from registry range
 * - Filters out ports already assigned to other models
 * - Visual indicator for conflicts
 * - Disabled state when server is running
 * - Terminal aesthetic design
 */
export const PortSelector: React.FC<PortSelectorProps> = ({
  model,
  allModels,
  portRange,
  isServerRunning,
  onPortChange,
}) => {
  /**
   * Calculate available ports and detect conflicts
   */
  const { availablePorts, occupiedPorts, hasConflict } = useMemo(() => {
    const [minPort, maxPort] = portRange;
    const allPorts: number[] = [];

    // Generate all ports in range
    for (let port = minPort; port <= maxPort; port++) {
      allPorts.push(port);
    }

    // Find occupied ports (excluding current model)
    const occupied = new Set<number>();
    Object.values(allModels).forEach((m) => {
      if (m.modelId !== model.modelId && m.port !== null) {
        occupied.add(m.port);
      }
    });

    // Check if current model has a conflict
    const conflict = model.port !== null && occupied.has(model.port);

    return {
      availablePorts: allPorts,
      occupiedPorts: occupied,
      hasConflict: conflict,
    };
  }, [allModels, model.modelId, model.port, portRange]);

  /**
   * Handle port selection change
   */
  const handleChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newPort = parseInt(event.target.value, 10);
    if (!isNaN(newPort) && newPort !== model.port) {
      await onPortChange(model.modelId, newPort);
    }
  };

  // Count truly available ports (not occupied)
  const availableCount = availablePorts.filter(p => !occupiedPorts.has(p)).length;

  return (
    <div className={styles.container}>
      <select
        value={model.port ?? ''}
        onChange={handleChange}
        disabled={isServerRunning}
        className={`${styles.select} ${hasConflict ? styles.conflict : ''} ${
          isServerRunning ? styles.disabled : ''
        }`}
        aria-label={`Port for ${model.family} ${model.sizeParams}B`}
      >
        {model.port === null && (
          <option value="">AUTO-ASSIGN</option>
        )}
        {availablePorts.map((port) => {
          const isOccupied = occupiedPorts.has(port);
          return (
            <option
              key={port}
              value={port}
              disabled={isOccupied}
              className={isOccupied ? styles.occupiedOption : ''}
            >
              {port} {isOccupied ? '(IN USE)' : ''}
            </option>
          );
        })}
      </select>

      {/* Status indicators */}
      <div className={styles.statusRow}>
        {isServerRunning && (
          <span className={styles.warningText}>
            ⚠ SERVER RUNNING - STOP TO CHANGE PORT
          </span>
        )}
        {hasConflict && !isServerRunning && (
          <span className={styles.conflictText}>
            ⚠ PORT CONFLICT DETECTED
          </span>
        )}
        {!isServerRunning && !hasConflict && (
          <span className={styles.infoText}>
            AVAILABLE: {availableCount} PORTS ({portRange[0]}-{portRange[1]})
          </span>
        )}
      </div>
    </div>
  );
};

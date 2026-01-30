/**
 * InstanceCardGrid - Responsive grid container for instance cards
 *
 * Features:
 * - Responsive grid (3/2/1 columns based on viewport)
 * - Groups instances by base model with headers
 * - Sorts by status (active first) then by display name
 */

import React, { useMemo } from 'react';
import { InstanceCard } from './InstanceCard';
import type { InstanceConfig, InstanceGroup } from '@/types/instances';
import styles from './InstanceCardGrid.module.css';

export interface InstanceCardGridProps {
  instances: InstanceConfig[];
  modelNames?: Record<string, string>; // modelId -> display name
  onEditInstance?: (instance: InstanceConfig) => void;
  groupByModel?: boolean;
}

export const InstanceCardGrid: React.FC<InstanceCardGridProps> = ({
  instances,
  modelNames = {},
  onEditInstance,
  groupByModel = true,
}) => {
  // Sort and optionally group instances
  const sortedInstances = useMemo(() => {
    return [...instances].sort((a, b) => {
      // Active instances first
      if (a.status === 'active' && b.status !== 'active') return -1;
      if (a.status !== 'active' && b.status === 'active') return 1;

      // Then by display name
      return a.displayName.localeCompare(b.displayName);
    });
  }, [instances]);

  const groupedInstances = useMemo((): InstanceGroup[] => {
    if (!groupByModel) {
      return [{
        modelId: 'all',
        modelDisplayName: 'All Instances',
        modelTier: '',
        instances: sortedInstances,
      }];
    }

    const groups: Record<string, InstanceConfig[]> = {};

    for (const instance of sortedInstances) {
      const modelGroup = groups[instance.modelId];
      if (!modelGroup) {
        groups[instance.modelId] = [instance];
      } else {
        modelGroup.push(instance);
      }
    }

    return Object.entries(groups).map(([modelId, instances]) => ({
      modelId,
      modelDisplayName: modelNames[modelId] || modelId,
      modelTier: '', // Could be enhanced to include tier
      instances,
    }));
  }, [sortedInstances, groupByModel, modelNames]);

  if (instances.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>◇</div>
        <div className={styles.emptyText}>NO INSTANCES CONFIGURED</div>
        <div className={styles.emptyHint}>
          Create an instance to get started
        </div>
      </div>
    );
  }

  return (
    <div className={styles.gridContainer}>
      {groupedInstances.map((group) => (
        <div key={group.modelId} className={styles.modelGroup}>
          {groupByModel && groupedInstances.length > 1 && (
            <div className={styles.groupHeader}>
              <span className={styles.groupName}>{group.modelDisplayName}</span>
              <span className={styles.groupCount}>{group.instances.length} instance{group.instances.length !== 1 ? 's' : ''}</span>
            </div>
          )}
          <div className={styles.grid}>
            {group.instances.map((instance) => (
              <InstanceCard
                key={instance.instanceId}
                instance={instance}
                modelDisplayName={modelNames[instance.modelId]}
                onEdit={onEditInstance}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

InstanceCardGrid.displayName = 'InstanceCardGrid';

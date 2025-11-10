/**
 * DecisionMatrix Component
 *
 * Displays routing decision matrix showing query complexity → model tier mapping.
 * Uses ASCII box drawing characters for terminal aesthetic.
 *
 * Performance: <5ms render time (memoized)
 */

import React, { useMemo } from 'react';
import type { RoutingMetrics } from '@/types/metrics';
import styles from './DecisionMatrix.module.css';

export interface DecisionMatrixProps {
  decisionMatrix: RoutingMetrics['decisionMatrix'];
}

interface MatrixCell {
  count: number;
  percentage: number;
  isHighest: boolean;
}

type MatrixData = Record<string, Record<string, MatrixCell>>;

/**
 * Build matrix data structure with percentages and highlighting
 */
const buildMatrixData = (
  decisionMatrix: RoutingMetrics['decisionMatrix']
): MatrixData => {
  const complexities: Array<"SIMPLE" | "MODERATE" | "COMPLEX"> = ["SIMPLE", "MODERATE", "COMPLEX"];
  const tiers: Array<"Q2" | "Q3" | "Q4"> = ["Q2", "Q3", "Q4"];

  const matrix: MatrixData = {};

  // Initialize matrix
  complexities.forEach(complexity => {
    matrix[complexity] = {};
    tiers.forEach(tier => {
      if (!matrix[complexity]) {
        matrix[complexity] = {};
      }
      matrix[complexity]![tier] = { count: 0, percentage: 0, isHighest: false };
    });
  });

  // Populate counts from data
  decisionMatrix.forEach(item => {
    if (matrix[item.complexity] && matrix[item.complexity]![item.tier]) {
      matrix[item.complexity]![item.tier] = {
        count: item.count,
        percentage: 0,
        isHighest: false,
      };
    }
  });

  // Calculate percentages and find highest per row
  complexities.forEach(complexity => {
    const complexityRow = matrix[complexity];
    if (!complexityRow) return;

    const total = tiers.reduce((sum, tier) => {
      const cell = complexityRow[tier];
      return sum + (cell?.count || 0);
    }, 0);

    if (total > 0) {
      let maxPercentage = 0;

      // Calculate percentages
      tiers.forEach(tier => {
        const cell = complexityRow[tier];
        if (cell) {
          const percentage = (cell.count / total) * 100;
          cell.percentage = percentage;
          maxPercentage = Math.max(maxPercentage, percentage);
        }
      });

      // Mark highest
      tiers.forEach(tier => {
        const cell = complexityRow[tier];
        if (cell && cell.percentage === maxPercentage) {
          cell.isHighest = true;
        }
      });
    }
  });

  return matrix;
};

export const DecisionMatrix: React.FC<DecisionMatrixProps> = React.memo(({ decisionMatrix }) => {
  const matrixData = useMemo(() => buildMatrixData(decisionMatrix), [decisionMatrix]);

  const complexities: Array<"SIMPLE" | "MODERATE" | "COMPLEX"> = ["SIMPLE", "MODERATE", "COMPLEX"];
  const tiers: Array<"Q2" | "Q3" | "Q4"> = ["Q2", "Q3", "Q4"];

  return (
    <div className={styles.matrix}>
      {/* Header row */}
      <div className={styles.headerRow}>
        <div className={styles.headerCell} />
        {tiers.map(tier => (
          <div key={tier} className={styles.headerCell}>
            {tier}
          </div>
        ))}
      </div>

      {/* Data rows */}
      {complexities.map(complexity => {
        const complexityRow = matrixData[complexity];
        if (!complexityRow) return null;

        return (
          <div key={complexity} className={styles.dataRow}>
            <div className={styles.labelCell}>
              {complexity}
            </div>
            {tiers.map(tier => {
              const cell = complexityRow[tier];
              if (!cell) return null;

              return (
                <div
                  key={tier}
                  className={`${styles.dataCell} ${cell.isHighest ? styles.highest : ''}`}
                >
                  <div className={styles.count}>{cell.count.toLocaleString()}</div>
                  <div className={styles.percentage}>
                    {cell.percentage > 0 ? `${cell.percentage.toFixed(0)}%` : '-'}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}

      {/* Legend */}
      <div className={styles.legend}>
        Highlighted cells show highest percentage per complexity level
      </div>
    </div>
  );
});

DecisionMatrix.displayName = 'DecisionMatrix';

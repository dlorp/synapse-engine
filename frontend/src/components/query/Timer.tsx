/**
 * Timer Component
 *
 * Real-time elapsed timer for query processing.
 * Updates every 100ms with color-coded feedback based on duration.
 */

import React, { useState, useEffect } from 'react';
import { QueryMode } from '@/types/query';
import styles from './Timer.module.css';

/**
 * Get expected completion time hint based on query mode
 */
const getExpectedTimeHint = (mode: QueryMode): string => {
  switch (mode) {
    case 'simple':
      return '<2s';
    case 'two-stage':
      return '<8s';
    case 'council':
      return '<20s';
    case 'benchmark':
      return '<30s';
    default:
      return '<5s'; // Default estimate
  }
};

interface TimerProps {
  /** Additional CSS class */
  className?: string;
  /** Query mode for expected time estimation */
  mode?: QueryMode;
}

export const Timer: React.FC<TimerProps> = ({ className, mode = 'two-stage' }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startTime = Date.now();

    // Update every 100ms for smooth counting
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 100);

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, []);

  // Format as MM:SS
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  // Color-code based on elapsed time
  const colorClass =
    elapsed < 10 ? styles.normal :   // 0-10s: green (normal)
    elapsed < 20 ? styles.moderate : // 10-20s: cyan (moderate)
    styles.long;                     // 20s+: amber (long)

  const expectedTime = getExpectedTimeHint(mode);

  return (
    <div className={`${styles.timerContainer} ${className || ''}`}>
      <span className={styles.pulsingDot}>●</span>
      <span className={styles.label}>PROCESSING QUERY...</span>
      <span className={`${styles.timer} ${colorClass}`}>{formatted}</span>
      <span className={styles.expected}>EXPECTED: {expectedTime}</span>
    </div>
  );
};

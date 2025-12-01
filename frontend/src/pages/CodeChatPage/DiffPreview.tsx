/**
 * DiffPreview Component - File Diff Display for Code Chat
 *
 * Displays file changes with line-by-line highlighting in unified view.
 * Shows additions, deletions, and context lines with color-coded styling.
 *
 * Features:
 * - Line-by-line diff visualization
 * - CREATE/MODIFY/DELETE badges
 * - Syntax-highlighted line numbers
 * - Color-coded additions (green) and deletions (red)
 * - Scrollable content area for large diffs
 * - Terminal-aesthetic styling
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';
import { AsciiPanel } from '@/components/terminal';
import styles from './DiffPreview.module.css';

// ============================================================================
// Types
// ============================================================================

/**
 * Represents a single line in a diff view.
 */
export interface DiffLine {
  /** Line number in the new file (displayed in gutter) */
  lineNumber: number;
  /** Line number in the original file (if applicable) */
  originalLineNumber?: number;
  /** Type of diff line */
  type: 'add' | 'remove' | 'context';
  /** Line content (text) */
  content: string;
}

/**
 * Props for DiffPreview component.
 */
export interface DiffPreviewProps {
  /** File path being displayed */
  filePath: string;
  /** Original file content (null if creating new file) */
  originalContent: string | null;
  /** New file content */
  newContent: string;
  /** Type of change operation */
  changeType: 'create' | 'modify' | 'delete';
  /** Pre-computed diff lines from server (optional) */
  diffLines?: DiffLine[];
  /** View mode (currently only unified is supported) */
  viewMode?: 'unified' | 'side-by-side';
  /** Additional CSS class for container */
  className?: string;
  /** Callback when close button is clicked */
  onClose?: () => void;
}

// ============================================================================
// Diff Computation
// ============================================================================

/**
 * Computes a simple line-by-line diff when server doesn't provide one.
 * This is a basic fallback implementation - server should provide optimized diffs.
 *
 * @param original - Original file content (null if new file)
 * @param newContent - New file content
 * @returns Array of DiffLine objects
 */
function computeSimpleDiff(
  original: string | null,
  newContent: string
): DiffLine[] {
  const result: DiffLine[] = [];

  // Handle new file creation
  if (original === null || original === '') {
    const lines = newContent.split('\n');
    lines.forEach((line, index) => {
      result.push({
        lineNumber: index + 1,
        type: 'add',
        content: line,
      });
    });
    return result;
  }

  // Handle file deletion
  if (newContent === '') {
    const lines = original.split('\n');
    lines.forEach((line, index) => {
      result.push({
        lineNumber: index + 1,
        originalLineNumber: index + 1,
        type: 'remove',
        content: line,
      });
    });
    return result;
  }

  // Line-by-line comparison for modifications
  const oldLines = original.split('\n');
  const newLines = newContent.split('\n');
  const maxLength = Math.max(oldLines.length, newLines.length);

  let newLineNum = 1;
  let oldLineNum = 1;

  for (let i = 0; i < maxLength; i++) {
    const oldLine = oldLines[i];
    const newLine = newLines[i];

    // Both lines exist and are identical (context)
    if (oldLine !== undefined && newLine !== undefined && oldLine === newLine) {
      result.push({
        lineNumber: newLineNum++,
        originalLineNumber: oldLineNum++,
        type: 'context',
        content: oldLine,
      });
    }
    // Lines differ - mark old as remove, new as add
    else {
      if (oldLine !== undefined) {
        result.push({
          lineNumber: newLineNum,
          originalLineNumber: oldLineNum++,
          type: 'remove',
          content: oldLine,
        });
      }
      if (newLine !== undefined) {
        result.push({
          lineNumber: newLineNum++,
          originalLineNumber: oldLineNum,
          type: 'add',
          content: newLine,
        });
      }
    }
  }

  return result;
}

// ============================================================================
// Component
// ============================================================================

/**
 * DiffPreview component displays file diffs with line-by-line highlighting.
 */
export const DiffPreview: React.FC<DiffPreviewProps> = ({
  filePath,
  originalContent,
  newContent,
  changeType,
  diffLines,
  viewMode: _viewMode = 'unified',
  className,
  onClose,
}) => {
  // ============================================================================
  // Computed State
  // ============================================================================

  /**
   * Compute diff lines if not provided by server.
   */
  const lines = useMemo(() => {
    if (diffLines) return diffLines;
    return computeSimpleDiff(originalContent, newContent);
  }, [diffLines, originalContent, newContent]);

  /**
   * Get badge configuration based on change type.
   */
  const badgeConfig = useMemo(() => {
    switch (changeType) {
      case 'create':
        return { text: 'CREATE', className: styles.badgeCreate };
      case 'modify':
        return { text: 'MODIFY', className: styles.badgeModify };
      case 'delete':
        return { text: 'DELETE', className: styles.badgeDelete };
      default:
        return { text: 'UNKNOWN', className: '' };
    }
  }, [changeType]);

  /**
   * Determine max line number width for padding.
   */
  const maxLineNumber = useMemo(() => {
    return Math.max(...lines.map((l) => l.lineNumber));
  }, [lines]);

  const lineNumberWidth = useMemo(() => {
    return Math.max(4, maxLineNumber.toString().length);
  }, [maxLineNumber]);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  /**
   * Format line number with appropriate padding.
   */
  const formatLineNumber = (num: number | undefined): string => {
    if (num === undefined) return ''.padStart(lineNumberWidth, ' ');
    return num.toString().padStart(lineNumberWidth, ' ');
  };

  /**
   * Get prefix character for diff line type.
   */
  const getLinePrefix = (type: DiffLine['type']): string => {
    switch (type) {
      case 'add':
        return '+';
      case 'remove':
        return '-';
      case 'context':
        return ' ';
      default:
        return ' ';
    }
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className={clsx(styles.diffContainer, className)}>
      <AsciiPanel
        title={`DIFF: ${filePath}`}
        titleRight={
          <span className={clsx(styles.badge, badgeConfig.className)}>
            [{badgeConfig.text}]
          </span>
        }
      >
        {onClose && (
          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close diff preview"
          >
            ×
          </button>
        )}

        <div className={styles.diffContent}>
          {lines.length === 0 ? (
            <div className={styles.emptyState}>No changes to display</div>
          ) : (
            lines.map((line, index) => (
              <div
                key={`${line.lineNumber}-${index}`}
                className={clsx(
                  styles.diffLine,
                  line.type === 'add' && styles.lineAdd,
                  line.type === 'remove' && styles.lineRemove,
                  line.type === 'context' && styles.lineContext
                )}
              >
                <span className={styles.lineNumber}>
                  {formatLineNumber(line.lineNumber)}
                </span>
                <span className={styles.linePrefix}>
                  {getLinePrefix(line.type)}
                </span>
                <span className={styles.lineContent}>
                  {line.content || '\u00A0'}
                </span>
              </div>
            ))
          )}
        </div>
      </AsciiPanel>
    </div>
  );
};

DiffPreview.displayName = 'DiffPreview';

/**
 * WorkspaceSelector - TUI file browser modal for workspace selection.
 *
 * Provides directory browsing with project detection, git status,
 * and keyboard navigation for selecting Code Chat workspaces.
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { Button } from '@/components/terminal/Button/Button';
import { AsciiPanel } from '@/components/terminal/AsciiPanel/AsciiPanel';
import { useWorkspaces, useWorkspaceValidation } from '@/hooks/useWorkspaces';
import styles from './WorkspaceSelector.module.css';

export interface WorkspaceSelectorProps {
  /** Current workspace path (may be empty) */
  currentWorkspace: string;
  /** Callback when workspace is selected */
  onSelect: (path: string) => void;
  /** Callback to close modal */
  onClose: () => void;
}

/**
 * WorkspaceSelector component.
 *
 * Terminal-aesthetic modal for browsing and selecting workspace directories.
 * Features:
 * - Directory tree navigation with parent/child traversal
 * - Project type detection (Python, Node, Rust, Go, etc.)
 * - Git repository indicators
 * - Workspace metadata display (file count, CGRAG index status)
 * - Keyboard navigation (ESC to close, Enter to select)
 * - Loading states and error handling
 *
 * @example
 * <WorkspaceSelector
 *   currentWorkspace="/home/user/projects/synapse"
 *   onSelect={(path) => setWorkspace(path)}
 *   onClose={() => setShowSelector(false)}
 * />
 */
export const WorkspaceSelector: React.FC<WorkspaceSelectorProps> = ({
  currentWorkspace,
  onSelect,
  onClose,
}) => {
  // Start browsing from current workspace or mounted workspace directory
  const [browsePath, setBrowsePath] = useState(currentWorkspace || '/workspace');
  const [selectedPath, setSelectedPath] = useState(currentWorkspace);

  // Fetch directory listing
  const { data, isLoading, error, refetch } = useWorkspaces(browsePath);

  // Fetch workspace metadata for selected path
  const { data: validationData } = useWorkspaceValidation(selectedPath);

  /**
   * Handle ESC key to close modal.
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter' && selectedPath) {
        handleSelect();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPath, onClose]);

  /**
   * Navigate to a directory.
   */
  const handleNavigate = (path: string) => {
    setBrowsePath(path);
    setSelectedPath(path);
  };

  /**
   * Navigate to parent directory.
   */
  const handleParentNav = () => {
    if (data?.parentPath) {
      setBrowsePath(data.parentPath);
    }
  };

  /**
   * Navigate to home directory.
   */
  const handleHome = () => {
    setBrowsePath('/');
  };

  /**
   * Confirm selection and close modal.
   */
  const handleSelect = () => {
    if (selectedPath) {
      onSelect(selectedPath);
      onClose();
    }
  };

  /**
   * Stop propagation on modal click to prevent overlay close.
   */
  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div
      className={styles.overlay}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="workspace-selector-title"
    >
      <div className={styles.modal} onClick={handleModalClick}>
        <AsciiPanel title="WORKSPACE SELECTION" variant="accent">
          {/* Current workspace display */}
          <div className={styles.currentPath}>
            <span className={styles.currentPathLabel}>CURRENT:</span>
            <span className={styles.currentPathValue}>
              {currentWorkspace || 'None selected'}
            </span>
          </div>

          {/* Path navigation bar */}
          <div className={styles.pathBar}>
            <span className={styles.browsePath}>{browsePath}</span>
            <Button
              onClick={handleParentNav}
              disabled={!data?.parentPath}
              variant="secondary"
              size="sm"
              className={styles.navButton}
              title="Navigate to parent directory"
            >
              [^]
            </Button>
          </div>

          {/* Directory list */}
          <div className={styles.listContainer}>
            {isLoading ? (
              <div className={styles.loading}>
                <div className={styles.loadingSpinner}>▮▮▯▯▯</div>
                <div className={styles.loadingText}>SCANNING DIRECTORIES...</div>
              </div>
            ) : error ? (
              <div className={styles.error}>
                <div className={styles.errorIcon}>✕</div>
                <div className={styles.errorMessage}>
                  Error: {error.message || 'Failed to load directory'}
                </div>
              </div>
            ) : !data?.directories || data.directories.length === 0 ? (
              <div className={styles.empty}>
                <div className={styles.emptyIcon}>∅</div>
                <div className={styles.emptyMessage}>No subdirectories found</div>
              </div>
            ) : (
              <div className={styles.directoryList}>
                {data.directories.map((dir) => {
                  const isSelected = dir.path === selectedPath;
                  return (
                  <div
                    key={dir.path}
                    className={clsx(styles.directoryItem, isSelected && styles.selected)}
                    onClick={() => setSelectedPath(dir.path)}
                    onDoubleClick={() => handleNavigate(dir.path)}
                    tabIndex={0}
                    role="button"
                    aria-selected={isSelected}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleNavigate(dir.path);
                      }
                    }}
                  >
                    <span className={styles.prefix}>+--</span>
                    <span className={styles.name}>{dir.name}/</span>

                    {isSelected && (
                      <span className={styles.selectedBadge}>[SELECTED]</span>
                    )}

                    {dir.projectType && (
                      <span
                        className={styles.projectBadge}
                        title={`${dir.projectType} project`}
                      >
                        {dir.projectType}
                      </span>
                    )}

                    {dir.isGitRepo && (
                      <span
                        className={styles.gitBadge}
                        title="Git repository"
                      >
                        git
                      </span>
                    )}
                  </div>
                );
                })}
              </div>
            )}
          </div>

          {/* Workspace metadata (if available) */}
          {validationData && validationData.valid && (
            <div className={styles.metadata}>
              <div className={styles.metadataTitle}>WORKSPACE INFO:</div>
              <div className={styles.metadataGrid}>
                {validationData.projectInfo && (
                  <>
                    <div className={styles.metadataItem}>
                      <span className={styles.metadataLabel}>Type:</span>
                      <span className={styles.metadataValue}>
                        {validationData.projectInfo.type}
                      </span>
                    </div>
                    {validationData.projectInfo.name && (
                      <div className={styles.metadataItem}>
                        <span className={styles.metadataLabel}>Name:</span>
                        <span className={styles.metadataValue}>
                          {validationData.projectInfo.name}
                        </span>
                      </div>
                    )}
                  </>
                )}
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>Files:</span>
                  <span className={styles.metadataValue}>
                    {validationData.fileCount?.toLocaleString() ?? 'N/A'}
                  </span>
                </div>
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>Git:</span>
                  <span className={styles.metadataValue}>
                    {validationData.isGitRepo ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>CGRAG:</span>
                  <span className={styles.metadataValue}>
                    {validationData.hasCgragIndex ? 'Indexed' : 'Not indexed'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className={styles.actions}>
            <Button
              onClick={handleSelect}
              disabled={!selectedPath}
              variant="primary"
              className={styles.actionButton}
            >
              SELECT
            </Button>
            <Button
              onClick={() => refetch()}
              variant="secondary"
              className={styles.actionButton}
            >
              REFRESH
            </Button>
            <Button
              onClick={handleHome}
              variant="secondary"
              className={styles.actionButton}
            >
              HOME
            </Button>
            <Button
              onClick={onClose}
              variant="ghost"
              className={styles.actionButton}
            >
              CANCEL
            </Button>
          </div>
        </AsciiPanel>
      </div>
    </div>
  );
};

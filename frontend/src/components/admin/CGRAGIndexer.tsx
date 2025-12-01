/**
 * CGRAG Indexer Component
 *
 * Provides UI for indexing documents into the CGRAG vector database.
 * Shows indexing status, progress, and available directories.
 */

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import styles from './CGRAGIndexer.module.css';

interface IndexStatus {
  index_exists: boolean;
  chunks_indexed: number;
  index_size_mb: number;
  last_indexed: string | null;
  is_indexing: boolean;
  indexing_progress: number;
  indexing_total: number;
  indexing_current_file: string | null;
  indexing_error: string | null;
  supported_extensions: string[];
}

interface Directory {
  path: string;
  description: string;
  file_count: number;
  exists: boolean;
}

interface DirectoriesResponse {
  directories: Directory[];
  supported_extensions: string[];
}

export const CGRAGIndexer: React.FC = () => {
  const queryClient = useQueryClient();

  // Fetch current index status
  const { data: status, isLoading: statusLoading } = useQuery<IndexStatus>({
    queryKey: ['cgrag', 'status'],
    queryFn: async () => {
      const response = await apiClient.get('cgrag/status');
      return response.data;
    },
    refetchInterval: (query) => {
      // Poll faster during indexing
      return query.state.data?.is_indexing ? 2000 : 10000;
    },
  });

  // Fetch available directories
  const { data: directories } = useQuery<DirectoriesResponse>({
    queryKey: ['cgrag', 'directories'],
    queryFn: async () => {
      const response = await apiClient.get('cgrag/directories');
      return response.data;
    },
  });

  // Start indexing mutation
  const indexMutation = useMutation({
    mutationFn: async (directory: string) => {
      const response = await apiClient.post('cgrag/index', { directory });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cgrag', 'status'] });
    },
  });

  const getStatusColor = (exists: boolean, isIndexing: boolean) => {
    if (isIndexing) return styles.statusIndexing;
    if (exists) return styles.statusHealthy;
    return styles.statusEmpty;
  };

  const formatSize = (mb: number) => {
    if (mb < 1) return `${Math.round(mb * 1024)} KB`;
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.headerLine}>{'─'.repeat(3)} CGRAG VECTOR INDEX {'─'.repeat(120)}</span>
      </div>

      <div className={styles.content}>
        {/* Status Section */}
        <div className={styles.statusSection}>
          <div className={styles.statusRow}>
            <span className={styles.label}>STATUS:</span>
            <span className={getStatusColor(status?.index_exists || false, status?.is_indexing || false)}>
              {statusLoading ? 'LOADING...' :
               status?.is_indexing ? 'INDEXING...' :
               status?.index_exists ? 'READY' : 'NO INDEX'}
            </span>
          </div>

          {status?.index_exists && (
            <>
              <div className={styles.statusRow}>
                <span className={styles.label}>CHUNKS:</span>
                <span className={styles.value}>{status.chunks_indexed.toLocaleString()}</span>
              </div>
              <div className={styles.statusRow}>
                <span className={styles.label}>SIZE:</span>
                <span className={styles.value}>{formatSize(status.index_size_mb)}</span>
              </div>
            </>
          )}

          {status?.is_indexing && (
            <div className={styles.progressSection}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${status.indexing_total > 0
                      ? (status.indexing_progress / status.indexing_total) * 100
                      : 0}%`
                  }}
                />
              </div>
              <div className={styles.progressText}>
                {status.indexing_progress}/{status.indexing_total} files
              </div>
            </div>
          )}

          {status?.indexing_error && (
            <div className={styles.error}>
              ERROR: {status.indexing_error}
            </div>
          )}
        </div>

        {/* Directories Section */}
        <div className={styles.directoriesSection}>
          <div className={styles.sectionTitle}>AVAILABLE DIRECTORIES</div>

          {directories?.directories.map((dir) => (
            <div key={dir.path} className={styles.directoryRow}>
              <div className={styles.directoryInfo}>
                <span className={styles.directoryPath}>{dir.path}</span>
                <span className={styles.directoryDesc}>{dir.description}</span>
                <span className={styles.fileCount}>
                  {dir.exists ? `${dir.file_count} indexable files` : 'Not found'}
                </span>
              </div>
              <button
                className={styles.indexButton}
                onClick={() => indexMutation.mutate(dir.path)}
                disabled={!dir.exists || status?.is_indexing || indexMutation.isPending}
              >
                {status?.is_indexing ? 'INDEXING...' : 'INDEX'}
              </button>
            </div>
          ))}
        </div>

        {/* Supported Extensions */}
        <div className={styles.extensionsSection}>
          <span className={styles.extensionsLabel}>SUPPORTED:</span>
          <span className={styles.extensions}>
            {status?.supported_extensions.join(' ')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CGRAGIndexer;

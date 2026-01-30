/**
 * EnhancedChunkCard - Display retrieved chunk with full metadata
 *
 * Features:
 * - Document breadcrumb (file → section → chunk)
 * - Relevance score badge
 * - Hybrid search score breakdown
 * - Reranking score changes
 * - Entity extraction display
 * - Code syntax highlighting
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';
import { Highlight, themes, Language } from 'prism-react-renderer';
import { EnhancedChunk } from '../../../types/cgrag';
import styles from './EnhancedChunkCard.module.css';

export interface EnhancedChunkCardProps {
  chunk: EnhancedChunk;
  rank: number;
  showScores?: boolean;
  showEntities?: boolean;
  className?: string;
}

/**
 * Format score as percentage.
 */
const formatScore = (score: number): string => {
  return (score * 100).toFixed(1);
};

/**
 * Get score color class.
 */
const getScoreColor = (score: number): string => {
  if (score >= 0.7) return styles.scoreHigh;
  if (score >= 0.4) return styles.scoreMed;
  return styles.scoreLow;
};

/**
 * Map common language names to Prism language identifiers.
 */
const mapLanguage = (lang?: string): Language => {
  if (!lang) return 'plain' as Language;
  
  const languageMap: Record<string, Language> = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'rb': 'ruby',
    'yml': 'yaml',
    'sh': 'bash',
    'shell': 'bash',
    'zsh': 'bash',
    'dockerfile': 'docker',
    'md': 'markdown',
  };
  
  const normalized = lang.toLowerCase();
  return (languageMap[normalized] || normalized) as Language;
};

export const EnhancedChunkCard: React.FC<EnhancedChunkCardProps> = ({
  chunk,
  rank,
  showScores = true,
  showEntities = false,
  className,
}) => {
  // Format breadcrumb
  const breadcrumbPath = useMemo(() => {
    const parts = [
      chunk.breadcrumb.file,
      ...chunk.breadcrumb.sections,
    ];
    return parts.join(' › ');
  }, [chunk.breadcrumb]);

  // Get mapped language for Prism
  const prismLanguage = useMemo(() => mapLanguage(chunk.language), [chunk.language]);

  // Calculate rank change
  const rankChange = chunk.rerankingScore
    ? chunk.rerankingScore.initialRank - chunk.rerankingScore.finalRank
    : 0;

  return (
    <div className={clsx(styles.card, className)}>
      {/* Header: Rank + Breadcrumb */}
      <div className={styles.header}>
        <div className={styles.rank}>#{rank}</div>
        <div className={styles.breadcrumb} title={breadcrumbPath}>
          {breadcrumbPath}
        </div>
        <div
          className={clsx(
            styles.relevanceScore,
            getScoreColor(chunk.relevanceScore)
          )}
        >
          {formatScore(chunk.relevanceScore)}%
        </div>
      </div>

      {/* Line range (for code) */}
      {chunk.breadcrumb.lineRange && (
        <div className={styles.lineRange}>
          Lines {chunk.breadcrumb.lineRange.start}-{chunk.breadcrumb.lineRange.end}
        </div>
      )}

      {/* Chunk text */}
      <div
        className={clsx(styles.text, {
          [styles.codeText]: chunk.language,
        })}
      >
        {chunk.language && (
          <div className={styles.languageTag}>{chunk.language}</div>
        )}
        {chunk.language ? (
          <Highlight
            theme={themes.nightOwl}
            code={chunk.text}
            language={prismLanguage}
          >
            {({ className, style, tokens, getLineProps, getTokenProps }) => (
              <pre className={clsx(className, styles.textContent)} style={{ ...style, margin: 0, background: 'transparent' }}>
                {tokens.map((line, i) => (
                  <div key={i} {...getLineProps({ line })}>
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                  </div>
                ))}
              </pre>
            )}
          </Highlight>
        ) : (
          <pre className={styles.textContent}>{chunk.text}</pre>
        )}
      </div>

      {/* Score breakdown */}
      {showScores && (chunk.hybridScore || chunk.rerankingScore) && (
        <div className={styles.scores}>
          {chunk.hybridScore && (
            <div className={styles.scoreSection}>
              <div className={styles.scoreLabel}>HYBRID SEARCH</div>
              <div className={styles.scoreGrid}>
                <div className={styles.scoreItem}>
                  <span className={styles.scoreKey}>Vector:</span>
                  <span className={clsx(styles.scoreValue, styles.vectorColor)}>
                    {formatScore(chunk.hybridScore.vectorScore)}%
                  </span>
                </div>
                <div className={styles.scoreItem}>
                  <span className={styles.scoreKey}>BM25:</span>
                  <span className={clsx(styles.scoreValue, styles.bm25Color)}>
                    {formatScore(chunk.hybridScore.bm25Score)}%
                  </span>
                </div>
                <div className={styles.scoreItem}>
                  <span className={styles.scoreKey}>Fusion:</span>
                  <span className={clsx(styles.scoreValue, styles.fusionColor)}>
                    {formatScore(chunk.hybridScore.fusionScore)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {chunk.rerankingScore && (
            <div className={styles.scoreSection}>
              <div className={styles.scoreLabel}>RERANKING</div>
              <div className={styles.scoreGrid}>
                <div className={styles.scoreItem}>
                  <span className={styles.scoreKey}>Initial:</span>
                  <span className={styles.scoreValue}>
                    {formatScore(chunk.rerankingScore.initialScore)}%
                  </span>
                </div>
                {chunk.rerankingScore.fineScore !== undefined && (
                  <div className={styles.scoreItem}>
                    <span className={styles.scoreKey}>Final:</span>
                    <span className={styles.scoreValue}>
                      {formatScore(chunk.rerankingScore.fineScore)}%
                    </span>
                  </div>
                )}
                <div className={styles.scoreItem}>
                  <span className={styles.scoreKey}>Rank Δ:</span>
                  <span
                    className={clsx(styles.scoreValue, {
                      [styles.rankImproved]: rankChange > 0,
                      [styles.rankDeclined]: rankChange < 0,
                    })}
                  >
                    {rankChange > 0 ? '+' : ''}
                    {rankChange}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Entities */}
      {showEntities && chunk.entities && chunk.entities.length > 0 && (
        <div className={styles.entities}>
          <div className={styles.entitiesLabel}>ENTITIES</div>
          <div className={styles.entityTags}>
            {chunk.entities.slice(0, 10).map((entity, index) => (
              <span
                key={`${entity.text}-${index}`}
                className={styles.entityTag}
                title={`${entity.label}${entity.confidence ? ` (${(entity.confidence * 100).toFixed(0)}%)` : ''}`}
              >
                {entity.text}
              </span>
            ))}
            {chunk.entities.length > 10 && (
              <span className={styles.entityMore}>
                +{chunk.entities.length - 10} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Footer: Token count + indexed timestamp */}
      <div className={styles.footer}>
        <span className={styles.footerItem}>
          {chunk.tokenCount} tokens
        </span>
        <span className={styles.footerItem}>
          Indexed: {new Date(chunk.indexedAt).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
};

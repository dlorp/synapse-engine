/**
 * QueryInput Component
 *
 * Terminal-styled query input with CGRAG toggle and advanced settings.
 * Mode selection is now handled by the ModeSelector component.
 */

import React, { useState, useCallback } from 'react';
import { Button } from '../terminal/Button/Button';
import styles from './QueryInput.module.css';

interface QueryOptions {
  useContext: boolean;
  useWebSearch: boolean;
  maxTokens: number;
  temperature: number;
}

interface QueryInputProps {
  onSubmit: (query: string, options: QueryOptions) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading = false,
  disabled = false,
}) => {
  const [query, setQuery] = useState('');
  const [useContext, setUseContext] = useState(true);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxTokens, setMaxTokens] = useState(512);
  const [temperature, setTemperature] = useState(0.7);

  const handleSubmit = useCallback(() => {
    if (!query.trim() || isLoading || disabled) return;

    onSubmit(query, {
      useContext,
      useWebSearch,
      maxTokens,
      temperature,
    });
  }, [query, useContext, useWebSearch, maxTokens, temperature, isLoading, disabled, onSubmit]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const isSubmitDisabled = !query.trim() || isLoading || disabled;

  return (
    <div className={styles.queryInput}>
      <div className={styles.header}>
        <span className={styles.prompt}>$</span>
        <span className={styles.title}>QUERY TERMINAL</span>
        <span className={styles.charCount}>{query.length} chars</span>
      </div>

      <textarea
        className={styles.textarea}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter query... (Cmd/Ctrl+Enter to submit)"
        disabled={isLoading || disabled}
        rows={4}
        aria-label="Query input"
      />

      <div className={styles.controls}>
        <div className={styles.toggleGroup}>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={useContext}
              onChange={(e) => setUseContext(e.target.checked)}
              disabled={isLoading || disabled}
            />
            <span>CGRAG CONTEXT</span>
          </label>

          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={useWebSearch}
              onChange={(e) => setUseWebSearch(e.target.checked)}
              disabled={isLoading || disabled}
            />
            <span>WEB SEARCH</span>
          </label>
        </div>

        <button
          className={styles.advancedToggle}
          onClick={() => setShowAdvanced(!showAdvanced)}
          disabled={isLoading || disabled}
          type="button"
          aria-expanded={showAdvanced}
          aria-controls="advanced-settings"
        >
          {showAdvanced ? '▼' : '▶'} ADVANCED
        </button>

        <Button
          onClick={handleSubmit}
          disabled={isSubmitDisabled}
          variant="primary"
          aria-label="Submit query"
        >
          {isLoading ? 'PROCESSING...' : 'EXECUTE'}
        </Button>
      </div>

      {showAdvanced && (
        <div className={styles.advanced} id="advanced-settings">
          <div className={styles.setting}>
            <label htmlFor="max-tokens-slider">
              MAX TOKENS: {maxTokens}
            </label>
            <input
              id="max-tokens-slider"
              type="range"
              min="128"
              max="4096"
              step="128"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              disabled={isLoading || disabled}
              className={styles.slider}
            />
          </div>
          <div className={styles.setting}>
            <label htmlFor="temperature-slider">
              TEMPERATURE: {temperature.toFixed(2)}
            </label>
            <input
              id="temperature-slider"
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              disabled={isLoading || disabled}
              className={styles.slider}
            />
          </div>
        </div>
      )}
    </div>
  );
};

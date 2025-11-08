import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Panel } from '../../terminal/Panel/Panel';
import styles from './QuickActions.module.css';

interface QuickActionsProps {
  onRescan: () => void;
  onEnableAll: () => void;
  onDisableAll: () => void;
  isLoading?: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  onRescan,
  onEnableAll,
  onDisableAll,
  isLoading = false
}) => {
  const navigate = useNavigate();

  return (
    <Panel title="QUICK ACTIONS" variant="default">
      <div className={styles.actions}>
        <button
          className={styles.action}
          onClick={onRescan}
          disabled={isLoading}
          title="Re-scan HuggingFace cache for new models"
        >
          <span className={styles.icon}>⟲</span>
          <span className={styles.label}>Re-scan HUB</span>
        </button>

        <button
          className={styles.action}
          onClick={onEnableAll}
          disabled={isLoading}
          title="Enable all discovered models"
        >
          <span className={styles.icon}>⊕</span>
          <span className={styles.label}>Enable All</span>
        </button>

        <button
          className={styles.action}
          onClick={onDisableAll}
          disabled={isLoading}
          title="Disable all models"
        >
          <span className={styles.icon}>⊖</span>
          <span className={styles.label}>Disable All</span>
        </button>

        <button
          className={styles.action}
          onClick={() => navigate('/model-management')}
          title="Go to model management page"
        >
          <span className={styles.icon}>◧</span>
          <span className={styles.label}>Manage Models</span>
        </button>
      </div>
    </Panel>
  );
};

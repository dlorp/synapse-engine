import React from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { useUIStore } from '@/stores';
import { useModelStatus } from '@/hooks/useModelStatus';
import styles from './Sidebar.module.css';

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { data: modelStatus } = useModelStatus();

  // Format uptime seconds to HH:MM:SS
  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const modelCount = modelStatus?.models.filter(
    (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ).length ?? 0;
  const uptime = modelStatus?.models[0]?.uptimeSeconds ?? 0; // Use first model's uptime
  const activeQueries = modelStatus?.activeQueries ?? 0;

  return (
    <aside
      className={clsx(
        styles.sidebar,
        sidebarCollapsed ? styles.collapsed : styles.expanded
      )}
    >
      <div className={styles.toggle}>
        <button
          className={styles.toggleButton}
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? '▶' : '◀'}
        </button>
      </div>

      <nav className={styles.nav}>
        <NavLink
          to="/"
          className={({ isActive }) =>
            clsx(styles.navItem, isActive && styles.active)
          }
        >
          <span className={styles.icon}>⌘</span>
          <span className={styles.label}>Query</span>
        </NavLink>

        <NavLink
          to="/model-management"
          className={({ isActive }) =>
            clsx(styles.navItem, isActive && styles.active)
          }
        >
          <span className={styles.icon}>◧</span>
          <span className={styles.label}>Models</span>
        </NavLink>

        <NavLink
          to="/metrics"
          className={({ isActive }) =>
            clsx(styles.navItem, isActive && styles.active)
          }
        >
          <span className={styles.icon}>◈</span>
          <span className={styles.label}>Metrics</span>
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            clsx(styles.navItem, isActive && styles.active)
          }
        >
          <span className={styles.icon}>⚙</span>
          <span className={styles.label}>Settings</span>
        </NavLink>

        <NavLink
          to="/admin"
          className={({ isActive }) =>
            clsx(styles.navItem, isActive && styles.active)
          }
        >
          <span className={styles.icon}>◎</span>
          <span className={styles.label}>Admin</span>
        </NavLink>
      </nav>

      <div className={styles.stats}>
        <div className={styles.statsTitle}>System Status</div>
        <div className={styles.statItem}>Models: {modelCount}</div>
        <div className={styles.statItem}>Uptime: {formatUptime(uptime)}</div>
        <div className={styles.statItem}>Queries: {activeQueries}</div>
      </div>
    </aside>
  );
};

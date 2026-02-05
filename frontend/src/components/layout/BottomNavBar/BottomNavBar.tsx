import React, { useEffect, useCallback } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { useModelStatus } from '@/hooks/useModelStatus';
import styles from './BottomNavBar.module.css';

interface NavItem {
  key: string;
  icon: string;
  path: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: '1', icon: '⌘', path: '/', label: 'QUERY' },
  { key: '2', icon: '▣', path: '/code-chat', label: 'CODE' },
  { key: '3', icon: '◧', path: '/model-management', label: 'MODELS' },
  { key: '4', icon: '◈', path: '/metrics', label: 'METRICS' },
  { key: '5', icon: '⚙', path: '/settings', label: 'SETTINGS' },
  { key: '6', icon: '◎', path: '/admin', label: 'ADMIN' },
];

export const BottomNavBar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: modelStatus } = useModelStatus();

  // Format uptime seconds to MM:SS
  const formatUptime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate stats
  const modelCount = modelStatus?.models.filter(
    (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ).length ?? 0;
  const uptime = modelStatus?.models[0]?.uptimeSeconds ?? 0;
  const activeQueries = modelStatus?.activeQueries ?? 0;

  // Keyboard navigation handler
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Ignore if user is typing in an input field
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return;
    }

    const navItem = NAV_ITEMS.find(item => item.key === event.key);
    if (navItem) {
      event.preventDefault();
      navigate(navItem.path);
    }
  }, [navigate]);

  // Register keyboard listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <nav className={styles.bottomNav} role="navigation" aria-label="Main navigation">
      {/* Top double-border */}
      <div className={styles.borderTop} aria-hidden="true">
        {`╔${'═'.repeat(200)}╗`}
      </div>

      {/* Navigation content row */}
      <div className={styles.navContent}>
        <span className={styles.borderChar} aria-hidden="true">║</span>

        {/* Navigation items */}
        <div className={styles.navItems}>
          {NAV_ITEMS.map((item, index) => (
            <React.Fragment key={item.key}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  clsx(styles.navItem, isActive && styles.active)
                }
                aria-current={location.pathname === item.path ? 'page' : undefined}
              >
                <span className={styles.shortcutKey}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
              </NavLink>
              {index < NAV_ITEMS.length - 1 && (
                <span className={styles.separator} aria-hidden="true">│</span>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Spacer */}
        <div className={styles.spacer} />

        {/* Status section */}
        <div className={styles.statusSection}>
          <span className={styles.separator} aria-hidden="true">│</span>
          <span className={styles.statusItem} title="Active Models">
            <span className={styles.statusIcon}>◉</span>
            <span className={styles.statusValue}>{modelCount}M</span>
          </span>
          <span className={styles.separator} aria-hidden="true">│</span>
          <span className={styles.statusItem} title="Uptime">
            <span className={styles.statusIcon}>⏱</span>
            <span className={styles.statusValue}>{formatUptime(uptime)}</span>
          </span>
          <span className={styles.separator} aria-hidden="true">│</span>
          <span className={styles.statusItem} title="Active Queries">
            <span className={styles.statusIcon}></span>
            <span className={styles.statusValue}>{activeQueries}Q</span>
          </span>
        </div>

        <span className={styles.borderChar} aria-hidden="true">║</span>
      </div>

      {/* Bottom double-border */}
      <div className={styles.borderBottom} aria-hidden="true">
        {`╚${'═'.repeat(200)}╝`}
      </div>
    </nav>
  );
};

import React from 'react';
import { Outlet } from 'react-router-dom';
import clsx from 'clsx';
import { Sidebar } from '../Sidebar';
import { useUIStore } from '@/stores';
import styles from './RootLayout.module.css';

export const RootLayout: React.FC = () => {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);

  return (
    <div
      className={clsx(styles.layout, sidebarCollapsed && styles.collapsed)}
    >
      <div className={styles.sidebar}>
        <Sidebar />
      </div>

      <main className={styles.main}>
        <Outlet />
      </main>

      <div className={styles.scanLine} aria-hidden="true" />
    </div>
  );
};

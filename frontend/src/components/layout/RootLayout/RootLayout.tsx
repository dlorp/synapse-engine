import React from 'react';
import { Outlet } from 'react-router-dom';
import { BottomNavBar } from '../BottomNavBar';
import styles from './RootLayout.module.css';

export const RootLayout: React.FC = () => {
  return (
    <div className={styles.layout}>
      <main className={styles.main}>
        <Outlet />
      </main>

      <BottomNavBar />

      <div className={styles.scanLine} aria-hidden="true" />
    </div>
  );
};

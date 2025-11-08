import React, { useState, useEffect } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { format } from 'date-fns';
import { StatusIndicator } from '@/components/terminal';
import { useWebSocketStore } from '@/stores';
import styles from './Header.module.css';

export const Header: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const connected = useWebSocketStore((state) => state.connected);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link to="/" className={styles.logo}>
          <div className={styles.logoIcon}>S</div>
          <div className={styles.logoTextContainer}>
            <span className={styles.logoText}>S.Y.N.A.P.S.E. ENGINE</span>
            <span className={styles.logoSubtext}>CORE:INTERFACE</span>
          </div>
        </Link>

        <nav className={styles.nav}>
          <NavLink
            to="/"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to="/models"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            Models
          </NavLink>
          <NavLink
            to="/metrics"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            Metrics
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            Settings
          </NavLink>
        </nav>
      </div>

      <div className={styles.right}>
        <StatusIndicator
          status={connected ? 'active' : 'offline'}
          label={connected ? 'CONNECTED' : 'OFFLINE'}
          showDot
          pulse={connected}
          size="sm"
        />
        <time className={styles.time}>
          {format(currentTime, 'HH:mm:ss')}
        </time>
      </div>
    </header>
  );
};

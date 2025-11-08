import React from 'react';
import { Link } from 'react-router-dom';
import { Panel, Button } from '@/components/terminal';
import styles from '../HomePage/HomePage.module.css';

export const NotFoundPage: React.FC = () => {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>404 - Not Found</h1>

      <Panel title="Error" variant="error">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', alignItems: 'center', padding: '48px' }}>
          <div style={{ fontSize: '48px', fontFamily: 'var(--font-display)', color: 'var(--text-error)' }}>
            ERROR 404
          </div>
          <div className={styles.placeholder} style={{ textAlign: 'center' }}>
            The requested resource could not be found.
            <br />
            System integrity maintained. No anomalies detected.
          </div>
          <Link to="/">
            <Button variant="primary">Return to Home</Button>
          </Link>
        </div>
      </Panel>
    </div>
  );
};

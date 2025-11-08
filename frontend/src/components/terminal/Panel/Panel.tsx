import React from 'react';
import clsx from 'clsx';
import styles from './Panel.module.css';

export interface PanelProps {
  children: React.ReactNode;
  title?: string;
  titleRight?: string;
  variant?: 'default' | 'accent' | 'warning' | 'error';
  noPadding?: boolean;
  className?: string;
}

export const Panel: React.FC<PanelProps> = ({
  children,
  title,
  titleRight,
  variant = 'default',
  noPadding = false,
  className,
}) => {
  return (
    <div className={clsx(styles.panel, styles[variant], className)}>
      {(title || titleRight) && (
        <div className={styles.header}>
          {title && <div className={styles.title}>{title}</div>}
          {titleRight && <div className={styles.titleRight}>{titleRight}</div>}
        </div>
      )}
      <div className={clsx(styles.content, noPadding && styles.noPadding)}>
        {children}
      </div>
    </div>
  );
};

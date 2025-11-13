import React from 'react';
import clsx from 'clsx';
import styles from './AsciiPanel.module.css';

export interface AsciiPanelProps {
  children: React.ReactNode;
  title?: string;
  titleRight?: React.ReactNode;
  className?: string;
  variant?: 'default' | 'accent' | 'warning' | 'error';
}

export const AsciiPanel: React.FC<AsciiPanelProps> = ({
  children,
  title,
  titleRight,
  className,
  variant = 'default'
}) => {
  return (
    <div className={clsx(styles.asciiPanel, styles[variant], className)}>
      {title && (
        <div className={clsx(
          styles.asciiPanelHeader,
          titleRight && styles.asciiPanelHeaderWithRight
        )}>
          {titleRight ? (
            <>
              <span className={styles.asciiPanelTitle}>
                {`${'─ ' + title + ' '}${'─'.repeat(50)}`}
              </span>
              <span className={styles.asciiPanelTitleRight}>
                {titleRight}
              </span>
            </>
          ) : (
            <span className={styles.asciiPanelTitle}>
              {`${'─ ' + title + ' '}${'─'.repeat(200)}`}
            </span>
          )}
        </div>
      )}
      <div className={styles.asciiPanelBody}>
        {children}
      </div>
    </div>
  );
};

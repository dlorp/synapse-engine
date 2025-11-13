import React from 'react';
import styles from './AsciiSectionHeader.module.css';

export interface AsciiSectionHeaderProps {
  title: string;
  className?: string;
}

export const AsciiSectionHeader: React.FC<AsciiSectionHeaderProps> = ({ title, className }) => {
  return (
    <div className={`${styles.asciiSectionHeader} ${className || ''}`}>
      {`${'─ ' + title + ' '}${'─'.repeat(150)}`}
    </div>
  );
};

import React from 'react';
import clsx from 'clsx';
import styles from './Divider.module.css';

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'default' | 'primary' | 'accent' | 'neutral';
  spacing?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Divider: React.FC<DividerProps> = ({
  orientation = 'horizontal',
  variant = 'default',
  spacing = 'md',
  className,
}) => {
  return (
    <hr
      className={clsx(
        styles.divider,
        styles[orientation],
        styles[variant],
        styles[spacing],
        className
      )}
      role="separator"
      aria-orientation={orientation}
    />
  );
};

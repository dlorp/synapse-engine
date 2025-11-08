import React from 'react';
import clsx from 'clsx';
import styles from './Input.module.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className,
  id,
  ...rest
}) => {
  const inputId = id || `input-${Math.random().toString(36).substring(7)}`;

  return (
    <div className={styles.container}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}
      <div className={styles.inputWrapper}>
        <input
          id={inputId}
          className={clsx(
            styles.input,
            error && styles.error,
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...rest}
        />
      </div>
      {error && (
        <div
          id={`${inputId}-error`}
          className={styles.errorMessage}
          role="alert"
        >
          <span className={styles.errorIcon}>!</span>
          {error}
        </div>
      )}
    </div>
  );
};

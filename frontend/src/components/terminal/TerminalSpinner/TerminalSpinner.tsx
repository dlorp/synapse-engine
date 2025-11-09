import React from 'react';
import styles from './TerminalSpinner.module.css';

export type SpinnerStyle = 'arc' | 'dots' | 'bar' | 'block';

export interface TerminalSpinnerProps {
  style?: SpinnerStyle;
  size?: number; // pixels
  color?: string;
  speed?: number; // seconds per rotation
  className?: string;
}

const SPINNER_FRAMES = {
  arc: ['◜', '◝', '◞', '◟'],
  dots: ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧'],
  bar: ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'],
  block: ['▖', '▘', '▝', '▗'],
} as const;

export const TerminalSpinner: React.FC<TerminalSpinnerProps> = ({
  style = 'arc',
  size = 24,
  color = '#ff9500',
  speed = 0.8,
  className,
}) => {
  const [frameIndex, setFrameIndex] = React.useState(0);
  const frames = SPINNER_FRAMES[style];

  React.useEffect(() => {
    const intervalMs = (speed * 1000) / frames.length;
    const interval = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % frames.length);
    }, intervalMs);

    return () => clearInterval(interval);
  }, [style, speed, frames.length]);

  const classNames = [styles.spinner, className].filter(Boolean).join(' ');

  return (
    <span
      className={classNames}
      style={{
        fontSize: `${size}px`,
        color,
      }}
      role="status"
      aria-label="Loading"
    >
      {frames[frameIndex]}
    </span>
  );
};

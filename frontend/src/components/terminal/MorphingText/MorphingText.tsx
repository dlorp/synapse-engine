import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import styles from './MorphingText.module.css';

export interface MorphingTextProps {
  /**
   * Text to display (will morph from current to this)
   */
  text: string;

  /**
   * Morph style: 'fade' | 'slide' | 'scramble'
   * Default: 'scramble'
   */
  morphStyle?: 'fade' | 'slide' | 'scramble';

  /**
   * Duration of morph animation in ms (default: 800)
   */
  duration?: number;

  /**
   * Delay before starting morph in ms (default: 0)
   */
  delay?: number;

  /**
   * Easing function (default: 'ease-in-out')
   */
  easing?: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';

  /**
   * Characters to use for scramble effect (default: uppercase alphanumeric)
   */
  scrambleChars?: string;

  /**
   * Loop morphing (default: false)
   */
  loop?: boolean;

  /**
   * Text array for looping (default: none)
   */
  loopTexts?: string[];

  /**
   * Loop interval in ms (default: 3000)
   */
  loopInterval?: number;

  /**
   * Font size (default: '16px')
   */
  fontSize?: string;

  /**
   * Color (default: phosphor orange #ff9500)
   */
  color?: string;

  /**
   * Enable phosphor glow effect (default: true)
   */
  glow?: boolean;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Callback when morph starts
   */
  onMorphStart?: () => void;

  /**
   * Callback when morph completes
   */
  onMorphComplete?: () => void;
}

export interface MorphingTextRef {
  morphTo: (newText: string) => void;
  reset: () => void;
}

const DEFAULT_SCRAMBLE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';

export const MorphingText = forwardRef<MorphingTextRef, MorphingTextProps>(
  (
    {
      text,
      morphStyle = 'scramble',
      duration = 800,
      delay = 0,
      easing = 'ease-in-out',
      scrambleChars = DEFAULT_SCRAMBLE_CHARS,
      loop = false,
      loopTexts,
      loopInterval = 3000,
      fontSize = '16px',
      color = '#ff9500',
      glow = true,
      className,
      onMorphStart,
      onMorphComplete,
    },
    ref
  ) => {
    const [displayText, setDisplayText] = useState(text);
    const [currentIndex, setCurrentIndex] = useState(0);
    const morphTimeoutRef = useRef<number | null>(null);
    const loopTimeoutRef = useRef<number | null>(null);

    // Get random scramble character
    const getRandomChar = (): string => {
      return scrambleChars[Math.floor(Math.random() * scrambleChars.length)] ?? 'X';
    };

    // Morph to new text with scramble effect
    const morphToScramble = (newText: string): void => {
      const oldText = displayText;
      const maxLength = Math.max(oldText.length, newText.length);
      const steps = Math.ceil(duration / 50); // 50ms per frame
      let currentStep = 0;

      const interval = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;

        let result = '';
        for (let i = 0; i < maxLength; i++) {
          const charProgress = Math.max(0, Math.min(1, (progress * maxLength - i) / 3));

          if (charProgress >= 1) {
            // Character fully morphed
            result += newText[i] || ' ';
          } else if (charProgress > 0) {
            // Character morphing - show random characters
            result += getRandomChar();
          } else {
            // Character not yet morphing
            result += oldText[i] || ' ';
          }
        }

        setDisplayText(result.trimEnd());

        if (currentStep >= steps) {
          clearInterval(interval);
          setDisplayText(newText);
          onMorphComplete?.();
        }
      }, 50);
    };

    // Morph to new text with fade effect
    const morphToFade = (newText: string): void => {
      setDisplayText(newText);
      setTimeout(() => {
        onMorphComplete?.();
      }, duration);
    };

    // Morph to new text with slide effect
    const morphToSlide = (newText: string): void => {
      const oldText = displayText;
      const maxLength = Math.max(oldText.length, newText.length);
      const steps = Math.ceil(duration / 30);
      let currentStep = 0;

      const interval = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;

        let result = '';
        for (let i = 0; i < maxLength; i++) {
          const charProgress = Math.max(0, Math.min(1, (progress * maxLength - i) / 2));

          if (charProgress >= 0.5) {
            result += newText[i] || ' ';
          } else {
            result += oldText[i] || ' ';
          }
        }

        setDisplayText(result.trimEnd());

        if (currentStep >= steps) {
          clearInterval(interval);
          setDisplayText(newText);
          onMorphComplete?.();
        }
      }, 30);
    };

    // Execute morph based on style
    const morphTo = (newText: string): void => {
      if (displayText === newText) return;

      onMorphStart?.();

      if (morphTimeoutRef.current) {
        clearTimeout(morphTimeoutRef.current);
      }

      morphTimeoutRef.current = window.setTimeout(() => {
        switch (morphStyle) {
          case 'scramble':
            morphToScramble(newText);
            break;
          case 'fade':
            morphToFade(newText);
            break;
          case 'slide':
            morphToSlide(newText);
            break;
        }
      }, delay);
    };

    // Handle text prop changes
    useEffect(() => {
      if (text !== displayText && !loop) {
        morphTo(text);
      }
    }, [text]);

    // Handle looping
    useEffect(() => {
      if (loop && loopTexts && loopTexts.length > 0) {
        loopTimeoutRef.current = window.setTimeout(() => {
          const nextIndex = (currentIndex + 1) % loopTexts.length;
          setCurrentIndex(nextIndex);
          const nextText = loopTexts[nextIndex];
          if (nextText !== undefined) {
            morphTo(nextText);
          }
        }, loopInterval);

        return () => {
          if (loopTimeoutRef.current) {
            clearTimeout(loopTimeoutRef.current);
          }
        };
      }
    }, [currentIndex, loop, loopTexts, loopInterval]);

    // Cleanup
    useEffect(() => {
      return () => {
        if (morphTimeoutRef.current) {
          clearTimeout(morphTimeoutRef.current);
        }
        if (loopTimeoutRef.current) {
          clearTimeout(loopTimeoutRef.current);
        }
      };
    }, []);

    // Expose imperative methods
    useImperativeHandle(ref, () => ({
      morphTo: (newText: string) => {
        morphTo(newText);
      },
      reset: () => {
        setDisplayText(text);
        setCurrentIndex(0);
      },
    }));

    // Easing class mapping
    const easingClass = {
      linear: styles.easingLinear,
      'ease-in': styles.easingEaseIn,
      'ease-out': styles.easingEaseOut,
      'ease-in-out': styles.easingEaseInOut,
    }[easing] ?? styles.easingEaseInOut;

    // Morph style class mapping
    const morphStyleClass = {
      fade: styles.morphFade,
      slide: styles.morphSlide,
      scramble: styles.morphScramble,
    }[morphStyle] ?? styles.morphScramble;

    return (
      <span
        className={`${styles.morphingText} ${morphStyleClass} ${easingClass} ${
          glow ? styles.glow : ''
        } ${className || ''}`}
        style={{
          fontSize,
          color,
          '--morph-duration': `${duration}ms`,
        } as React.CSSProperties}
        aria-live="polite"
        aria-label={displayText}
      >
        {displayText.split('').map((char, index) => (
          <span key={index} className={styles.char}>
            {char}
          </span>
        ))}
      </span>
    );
  }
);

MorphingText.displayName = 'MorphingText';

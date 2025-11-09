/**
 * FigletBanner Component - Large ASCII art banner
 *
 * Display large ASCII art text with phosphor glow and scan lines.
 * Perfect for homepage headers and section dividers.
 *
 * Features:
 * - Pre-rendered Figlet-style ASCII art
 * - Pulsating phosphor-glow-orange effect
 * - Optional scan-line animation
 * - Center-aligned monospace display
 * - Reduced motion support
 */

import React from 'react';
import clsx from 'clsx';
import { TerminalEffect } from '../TerminalEffect';
import styles from './FigletBanner.module.css';

export interface FigletBannerProps {
  text?: string;
  variant?: 'standard' | 'slant' | 'banner' | 'block';
  className?: string;
  enableScanLines?: boolean;
  enablePulse?: boolean;
}

/**
 * Pre-rendered ASCII art for common text
 * Generated using Figlet-style rendering
 */
const ASCII_ART: Record<string, string> = {
  'S.Y.N.A.P.S.E. ENGINE': `
 ███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗    ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
 ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
 ███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗      █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗
 ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝      ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝
 ███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗
 ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝`,

  'SYNAPSE ENGINE': `
 ███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗
 ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝
 ███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗
 ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝
 ███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗
 ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝

 ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
 ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
 █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗
 ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝
 ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗
 ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝`,

  'NEURAL SUBSTRATE': `
 ███╗   ██╗███████╗██╗   ██╗██████╗  █████╗ ██╗
 ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔══██╗██║
 ██╔██╗ ██║█████╗  ██║   ██║██████╔╝███████║██║
 ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██╔══██║██║
 ██║ ╚████║███████╗╚██████╔╝██║  ██║██║  ██║███████╗
 ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

 ███████╗██╗   ██╗██████╗ ███████╗████████╗██████╗  █████╗ ████████╗███████╗
 ██╔════╝██║   ██║██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
 ███████╗██║   ██║██████╔╝███████╗   ██║   ██████╔╝███████║   ██║   █████╗
 ╚════██║██║   ██║██╔══██╗╚════██║   ██║   ██╔══██╗██╔══██║   ██║   ██╔══╝
 ███████║╚██████╔╝██████╔╝███████║   ██║   ██║  ██║██║  ██║   ██║   ███████╗
 ╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝`,

  'SYSTEM ONLINE': `
 ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗
 ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║
 ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║
 ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║
 ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║
 ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝

  ██████╗ ███╗   ██╗██╗     ██╗███╗   ██╗███████╗
 ██╔═══██╗████╗  ██║██║     ██║████╗  ██║██╔════╝
 ██║   ██║██╔██╗ ██║██║     ██║██╔██╗ ██║█████╗
 ██║   ██║██║╚██╗██║██║     ██║██║╚██╗██║██╔══╝
 ╚██████╔╝██║ ╚████║███████╗██║██║ ╚████║███████╗
  ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝`,

  'READY': `
 ██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗
 ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
 ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝
 ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝
 ██║  ██║███████╗██║  ██║██████╔╝   ██║
 ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝`,
};

/**
 * Generate simple block-style ASCII art if pre-rendered version not found
 */
const generateSimpleASCII = (text: string): string => {
  // Simple fallback - just return the text with some decoration
  return `
╔${'═'.repeat(text.length + 2)}╗
║ ${text} ║
╚${'═'.repeat(text.length + 2)}╝`;
};

export const FigletBanner: React.FC<FigletBannerProps> = ({
  text = 'S.Y.N.A.P.S.E. ENGINE',
  variant = 'standard',
  className,
  enableScanLines = true,
  enablePulse = true,
}) => {
  // Get ASCII art for text, fallback to simple generation
  const asciiArt = ASCII_ART[text] || generateSimpleASCII(text);

  return (
    <TerminalEffect
      enableScanLines={enableScanLines}
      scanLineSpeed="fast"
      enablePhosphorGlow={enablePulse}
      phosphorColor="orange"
      className={className}
    >
      <div className={styles.container}>
        <pre
          className={clsx(
            styles.banner,
            styles[variant],
            enablePulse && 'phosphor-glow-orange'
          )}
          aria-label={`ASCII art banner: ${text}`}
        >
          {asciiArt}
        </pre>
      </div>
    </TerminalEffect>
  );
};

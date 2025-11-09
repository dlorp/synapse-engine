/**
 * DotMatrixTestPage.tsx
 *
 * Test page for DotMatrixDisplay component
 * Navigate to /dot-matrix-test to view
 */

import React from 'react';
import { DotMatrixDisplay } from '@/components/terminal';

export const DotMatrixTestPage: React.FC = () => {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#000',
        padding: '40px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '40px',
        alignItems: 'center',
      }}
    >
      {/* Page Title */}
      <h1
        style={{
          color: '#ff9500',
          fontFamily: 'JetBrains Mono, monospace',
          textAlign: 'center',
          marginBottom: '20px',
        }}
      >
        DOT MATRIX LED DISPLAY - TEST PAGE
      </h1>

      {/* Test 1: Default Banner */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 1: Default Banner (SYNAPSE ENGINE ONLINE)
        </h2>
        <DotMatrixDisplay
          text="SYNAPSE ENGINE ONLINE"
          revealSpeed={400}
          width={800}
          height={80}
        />
      </div>

      {/* Test 2: Short Text */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 2: Short Text (HELLO WORLD)
        </h2>
        <DotMatrixDisplay text="HELLO WORLD" revealSpeed={300} />
      </div>

      {/* Test 3: Numbers and Symbols */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 3: Numbers and Symbols (STATUS: ACTIVE!)
        </h2>
        <DotMatrixDisplay text="STATUS: ACTIVE!" revealSpeed={200} />
      </div>

      {/* Test 4: Looping Animation */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 4: Looping Animation (LOADING...)
        </h2>
        <DotMatrixDisplay text="LOADING..." revealSpeed={250} loop={true} />
      </div>

      {/* Test 5: All Numbers */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 5: Numbers (0123456789)
        </h2>
        <DotMatrixDisplay text="0123456789" revealSpeed={200} />
      </div>

      {/* Test 6: Alphabet */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 6: Full Alphabet (A-Z)
        </h2>
        <DotMatrixDisplay text="ABCDEFGHIJKLMNOPQRSTUVWXYZ" revealSpeed={150} />
      </div>

      {/* Test 7: Enhanced Features Demo */}
      <div>
        <h2
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            marginBottom: '10px',
          }}
        >
          Test 7: Enhanced Features (Round Pixels + Full Grid + Pixel Animation)
        </h2>
        <p
          style={{
            color: '#ff9500',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px',
            marginBottom: '10px',
            opacity: 0.7,
          }}
        >
          Watch for: ● Round LED pixels ● Dim background grid ● Sequential pixel illumination
        </p>
        <DotMatrixDisplay text="NEURAL SUBSTRATE" revealSpeed={200} />
      </div>

      {/* Instructions */}
      <div
        style={{
          marginTop: '40px',
          padding: '20px',
          border: '1px solid #ff9500',
          borderRadius: '4px',
          maxWidth: '800px',
        }}
      >
        <h3
          style={{
            color: '#ff9500',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '16px',
            marginBottom: '10px',
          }}
        >
          TESTING CHECKLIST - ENHANCED LED DISPLAY
        </h3>
        <ul
          style={{
            color: '#00ffff',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
            lineHeight: '1.8',
          }}
        >
          <li>✓ Round LED pixels (not square) - like classic LED displays</li>
          <li>✓ Full 5×7 grid visible with dim background glow on "off" pixels</li>
          <li>✓ Pixel-by-pixel sequential illumination (top→bottom, left→right)</li>
          <li>✓ Each LED pixel has phosphor orange glow (#ff9500)</li>
          <li>✓ Animation runs at 60fps (no jank or stuttering)</li>
          <li>✓ Test 4 (LOADING...) loops infinitely</li>
          <li>✓ Border glows on hover</li>
          <li>✓ Open DevTools Performance tab to verify consistent 60fps</li>
        </ul>
      </div>
    </div>
  );
};

/**
 * DotMatrixExample.tsx
 *
 * Example integration of DotMatrixDisplay component
 * Shows how to use the component on HomePage or other pages
 */

import React from 'react';
import { DotMatrixDisplay, DotMatrixDisplayControlled } from '@/components/terminal';
import { DotMatrixAnimation } from '@/animations';

/**
 * Basic Example - Auto-playing banner
 */
export const BasicExample: React.FC = () => {
  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <DotMatrixDisplay
        text="SYNAPSE ENGINE ONLINE"
        revealSpeed={400}
        loop={false}
      />
    </div>
  );
};

/**
 * Controlled Example - Manual control over animation
 */
export const ControlledExample: React.FC = () => {
  const [animation, setAnimation] = React.useState<DotMatrixAnimation | null>(null);

  const handleStart = () => {
    animation?.start();
  };

  const handleStop = () => {
    animation?.stop();
  };

  const handleReset = () => {
    animation?.reset();
  };

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <DotMatrixDisplayControlled
        text="CONTROLLED DISPLAY"
        revealSpeed={300}
        loop={true}
        onAnimationReady={setAnimation}
        autoStart={false}
      />

      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button onClick={handleStart} style={{ color: '#ff9500' }}>Start</button>
        <button onClick={handleStop} style={{ color: '#ff9500' }}>Stop</button>
        <button onClick={handleReset} style={{ color: '#ff9500' }}>Reset</button>
      </div>
    </div>
  );
};

/**
 * HomePage Integration Example
 */
export const HomePageBannerExample: React.FC = () => {
  return (
    <div
      style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        padding: '40px 20px',
        background: '#000',
      }}
    >
      <DotMatrixDisplay
        text="SYNAPSE ENGINE ONLINE"
        revealSpeed={400}
        loop={false}
        width={800}
        height={80}
      />
    </div>
  );
};

/**
 * Multiple Lines Example (create multiple displays)
 */
export const MultiLineExample: React.FC = () => {
  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <div style={{ marginBottom: '20px' }}>
        <DotMatrixDisplay text="NEURAL SUBSTRATE" revealSpeed={300} />
      </div>
      <div style={{ marginBottom: '20px' }}>
        <DotMatrixDisplay text="ORCHESTRATOR" revealSpeed={300} />
      </div>
      <div>
        <DotMatrixDisplay text="STATUS: ACTIVE" revealSpeed={300} />
      </div>
    </div>
  );
};

/**
 * Integration code for existing HomePage.tsx
 *
 * Add this import at the top:
 * ```typescript
 * import { DotMatrixDisplay } from '@/components/terminal';
 * ```
 *
 * Add this JSX in the HomePage component:
 * ```tsx
 * export const HomePage: React.FC = () => {
 *   return (
 *     <CRTMonitor bloomIntensity={0.3} scanlinesEnabled>
 *       <div className={styles.homePage}>
 *         {/* Dot Matrix Banner - NEW *\/}
 *         <div className={styles.bannerContainer}>
 *           <DotMatrixDisplay
 *             text="SYNAPSE ENGINE ONLINE"
 *             revealSpeed={400}
 *             width={800}
 *             height={80}
 *           />
 *         </div>
 *
 *         {/* Rest of existing content *\/}
 *         <div className={styles.content}>
 *           {/* ... existing HomePage content ... *\/}
 *         </div>
 *       </div>
 *     </CRTMonitor>
 *   );
 * };
 * ```
 *
 * Add this CSS to HomePage.module.css:
 * ```css
 * .bannerContainer {
 *   display: flex;
 *   justify-content: center;
 *   margin: 20px 0 40px 0;
 * }
 *
 * .homePage {
 *   padding: 20px;
 *   color: #ff9500;
 *   min-height: 100vh;
 * }
 * ```
 */

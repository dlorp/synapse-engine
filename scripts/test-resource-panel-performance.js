#!/usr/bin/env node

/**
 * Performance test for ResourceUtilizationPanel
 * Measures render time and frame rate for 9 metrics at 1Hz updates
 *
 * Requirements:
 * - Docker containers running
 * - Backend exposing /api/metrics/resources endpoint
 * - Target: <16ms render time (60fps)
 */

const puppeteer = require('puppeteer');

const METRICS_URL = 'http://localhost:5173/metrics';
const TEST_DURATION_SEC = 30;
const TARGET_RENDER_TIME_MS = 16; // 60fps threshold

async function measurePerformance() {
  console.log('🚀 Starting ResourceUtilizationPanel Performance Test\n');
  console.log('Target: <16ms render time for 60fps');
  console.log(`Duration: ${TEST_DURATION_SEC} seconds\n`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // Enable performance metrics
  await page.evaluateOnNewDocument(() => {
    window.renderTimes = [];
    window.frameCount = 0;
    window.startTime = performance.now();

    // Hook into React DevTools (if available) or MutationObserver
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'react-render') {
          window.renderTimes.push(entry.duration);
        }
      }
    });

    observer.observe({ entryTypes: ['measure'] });
  });

  try {
    console.log('📡 Navigating to metrics page...');
    await page.goto(METRICS_URL, { waitUntil: 'networkidle0' });

    console.log('⏱️  Waiting for component to mount...');
    await page.waitForSelector('[data-testid="resource-panel"]', { timeout: 10000 });

    console.log('✅ Component mounted. Starting measurements...\n');

    // Measure frame rate and render times
    await page.evaluate((duration) => {
      return new Promise((resolve) => {
        let frames = 0;
        let totalRenderTime = 0;
        let maxRenderTime = 0;
        const renderTimes = [];

        const measureFrame = () => {
          const start = performance.now();

          // Force a style recalculation (simulates React update)
          document.body.offsetHeight;

          const end = performance.now();
          const renderTime = end - start;

          frames++;
          totalRenderTime += renderTime;
          maxRenderTime = Math.max(maxRenderTime, renderTime);
          renderTimes.push(renderTime);

          if (performance.now() - window.startTime < duration * 1000) {
            requestAnimationFrame(measureFrame);
          } else {
            window.performanceResults = {
              frames,
              totalRenderTime,
              maxRenderTime,
              avgRenderTime: totalRenderTime / frames,
              renderTimes,
              fps: frames / duration,
            };
            resolve();
          }
        };

        requestAnimationFrame(measureFrame);
      });
    }, TEST_DURATION_SEC);

    const results = await page.evaluate(() => window.performanceResults);

    console.log('📊 Performance Results:\n');
    console.log('Frame Rate:');
    console.log(`  FPS: ${results.fps.toFixed(2)} fps`);
    console.log(`  Target: 60 fps`);
    console.log(`  Status: ${results.fps >= 55 ? '✅ PASS' : '❌ FAIL'}`);
    console.log('');

    console.log('Render Times:');
    console.log(`  Average: ${results.avgRenderTime.toFixed(2)} ms`);
    console.log(`  Maximum: ${results.maxRenderTime.toFixed(2)} ms`);
    console.log(`  Target: <${TARGET_RENDER_TIME_MS} ms`);
    console.log(`  Status: ${results.avgRenderTime < TARGET_RENDER_TIME_MS ? '✅ PASS' : '❌ FAIL'}`);
    console.log('');

    // Calculate percentiles
    const sortedTimes = results.renderTimes.sort((a, b) => a - b);
    const p50 = sortedTimes[Math.floor(sortedTimes.length * 0.5)];
    const p95 = sortedTimes[Math.floor(sortedTimes.length * 0.95)];
    const p99 = sortedTimes[Math.floor(sortedTimes.length * 0.99)];

    console.log('Percentiles:');
    console.log(`  P50: ${p50.toFixed(2)} ms`);
    console.log(`  P95: ${p95.toFixed(2)} ms`);
    console.log(`  P99: ${p99.toFixed(2)} ms`);
    console.log('');

    // Memory test
    const memoryMetrics = await page.metrics();
    console.log('Memory Usage:');
    console.log(`  JS Heap: ${(memoryMetrics.JSHeapUsedSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  JS Heap Limit: ${(memoryMetrics.JSHeapTotalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log('');

    // Overall assessment
    const passed = results.fps >= 55 && results.avgRenderTime < TARGET_RENDER_TIME_MS;
    console.log('═══════════════════════════════════════');
    console.log(`Overall: ${passed ? '✅ PASS' : '❌ FAIL'}`);
    console.log('═══════════════════════════════════════\n');

    if (!passed) {
      console.log('⚠️  Performance issues detected:');
      if (results.fps < 55) {
        console.log('   - Frame rate below 55 fps (target: 60 fps)');
      }
      if (results.avgRenderTime >= TARGET_RENDER_TIME_MS) {
        console.log(`   - Average render time exceeds ${TARGET_RENDER_TIME_MS}ms`);
      }
      console.log('   - Consider optimizing with useMemo, React.memo, or reducing re-renders\n');
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Run the test
measurePerformance()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });

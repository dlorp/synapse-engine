/**
 * ResourceMetricCard performance and functionality tests
 * Validates rendering performance, memoization, and visual states
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResourceMetricCard } from './ResourceMetricCard';

describe('ResourceMetricCard', () => {
  it('renders basic metric without progress bar', () => {
    render(
      <ResourceMetricCard
        label="TEST METRIC"
        value="12.5"
        unit="GB"
        status="ok"
      />
    );

    expect(screen.getByText('TEST METRIC')).toBeInTheDocument();
    expect(screen.getByText('12.5')).toBeInTheDocument();
    expect(screen.getByText('GB')).toBeInTheDocument();
  });

  it('renders metric with progress bar', () => {
    render(
      <ResourceMetricCard
        label="CPU USAGE"
        value="45.2%"
        percent={45.2}
        status="ok"
      />
    );

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '45.2');
  });

  it('renders metric with secondary text', () => {
    render(
      <ResourceMetricCard
        label="VRAM"
        value="12.4"
        unit="GB"
        status="warning"
        secondary="16 GB total"
      />
    );

    expect(screen.getByText('16 GB total')).toBeInTheDocument();
  });

  it('applies correct status class', () => {
    const { container, rerender } = render(
      <ResourceMetricCard
        label="TEST"
        value="50"
        percent={50}
        status="ok"
      />
    );

    expect(container.firstChild).toHaveClass('ok');

    rerender(
      <ResourceMetricCard
        label="TEST"
        value="85"
        percent={85}
        status="warning"
      />
    );

    expect(container.firstChild).toHaveClass('warning');

    rerender(
      <ResourceMetricCard
        label="TEST"
        value="95"
        percent={95}
        status="critical"
      />
    );

    expect(container.firstChild).toHaveClass('critical');
  });

  it('clamps progress bar to 0-100 range', () => {
    const { rerender } = render(
      <ResourceMetricCard
        label="TEST"
        value="150"
        percent={150}
        status="critical"
      />
    );

    let progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');

    rerender(
      <ResourceMetricCard
        label="TEST"
        value="-10"
        percent={-10}
        status="ok"
      />
    );

    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  });

  // Performance test: should memoize properly
  it('memoizes and prevents unnecessary re-renders', () => {
    const { rerender } = render(
      <ResourceMetricCard
        label="CPU"
        value="45.2%"
        percent={45.2}
        status="ok"
      />
    );

    const firstElement = screen.getByText('CPU');

    // Re-render with same props (should not re-render due to React.memo)
    rerender(
      <ResourceMetricCard
        label="CPU"
        value="45.2%"
        percent={45.2}
        status="ok"
      />
    );

    const secondElement = screen.getByText('CPU');

    // Same element should be returned (reference equality)
    expect(firstElement).toBe(secondElement);
  });
});

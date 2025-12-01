/**
 * PresetSelector Component Tests
 *
 * Tests for the preset dropdown with portal behavior and CUSTOM option.
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PresetSelector } from '../PresetSelector';

// Mock usePresets hook
vi.mock('@/hooks/usePresets', () => ({
  usePresets: () => ({
    data: [
      {
        name: 'SYNAPSE_DEFAULT',
        description: 'Default preset',
        systemPrompt: 'You are a helpful assistant',
        planningTier: 'balanced',
        toolConfigs: {},
        isCustom: false,
      },
      {
        name: 'SYNAPSE_ANALYST',
        description: 'Analytical preset',
        systemPrompt: null,
        planningTier: 'powerful',
        toolConfigs: {},
        isCustom: false,
      },
    ],
    isLoading: false,
    error: null,
  }),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('PresetSelector', () => {
  test('renders dropdown button with current preset', () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('DEFAULT')).toBeInTheDocument();
  });

  test('opens dropdown menu when button is clicked', async () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /default/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/ANALYST/)).toBeInTheDocument();
    });
  });

  test('includes CUSTOM option in dropdown', async () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /default/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/CUSTOM/)).toBeInTheDocument();
    });
  });

  test('calls onPresetChange when option is selected', async () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /default/i });
    fireEvent.click(button);

    await waitFor(() => {
      const analystOption = screen.getByText(/ANALYST/);
      fireEvent.click(analystOption.closest('button')!);
    });

    expect(onPresetChange).toHaveBeenCalledWith('SYNAPSE_ANALYST');
  });

  test('displays selected state correctly', async () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /default/i });
    fireEvent.click(button);

    await waitFor(() => {
      const defaultOption = screen.getByText(/DEFAULT/).closest('button');
      expect(defaultOption).toHaveAttribute('aria-selected', 'true');
    });
  });

  test('closes dropdown when clicking outside (portal behavior)', async () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /default/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/ANALYST/)).toBeInTheDocument();
    });

    // Click outside the dropdown
    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(screen.queryByText(/ANALYST/)).not.toBeInTheDocument();
    });
  });

  test('supports keyboard shortcuts (D, A, C, V, R, J, U)', () => {
    const onPresetChange = vi.fn();
    render(
      <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />,
      { wrapper: createWrapper() }
    );

    // Press 'A' for ANALYST
    fireEvent.keyDown(window, { key: 'a' });
    expect(onPresetChange).toHaveBeenCalledWith('SYNAPSE_ANALYST');

    // Press 'U' for CUSTOM
    fireEvent.keyDown(window, { key: 'u' });
    expect(onPresetChange).toHaveBeenCalledWith('CUSTOM');
  });

  test('does not trigger shortcuts when input is focused', () => {
    const onPresetChange = vi.fn();
    render(
      <div>
        <input type="text" />
        <PresetSelector selectedPreset="SYNAPSE_DEFAULT" onPresetChange={onPresetChange} />
      </div>,
      { wrapper: createWrapper() }
    );

    const input = screen.getByRole('textbox');
    input.focus();

    // Press 'A' while input is focused - should NOT trigger preset change
    fireEvent.keyDown(input, { key: 'a' });
    expect(onPresetChange).not.toHaveBeenCalled();
  });
});

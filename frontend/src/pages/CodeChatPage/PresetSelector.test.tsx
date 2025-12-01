/**
 * PresetSelector Component Tests
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PresetSelector } from './PresetSelector';
import { ToolName, ToolModelConfig } from '@/types/codeChat';

describe('PresetSelector', () => {
  test('renders preset dropdown with correct options', () => {
    const handleChange = vi.fn();

    render(
      <PresetSelector selectedPreset="balanced" onPresetChange={handleChange} />
    );

    // Check label is present
    expect(screen.getByText('PRESET:')).toBeInTheDocument();

    // Check dropdown exists
    const select = screen.getByLabelText('Model preset selection');
    expect(select).toBeInTheDocument();

    // Check all preset options exist
    expect(screen.getByText('SPEED')).toBeInTheDocument();
    expect(screen.getByText('BALANCED')).toBeInTheDocument();
    expect(screen.getByText('QUALITY')).toBeInTheDocument();
    expect(screen.getByText('CODING')).toBeInTheDocument();
    expect(screen.getByText('RESEARCH')).toBeInTheDocument();
  });

  test('calls onPresetChange when selection changes', () => {
    const handleChange = vi.fn();

    render(
      <PresetSelector selectedPreset="balanced" onPresetChange={handleChange} />
    );

    const select = screen.getByLabelText('Model preset selection') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'quality' } });

    expect(handleChange).toHaveBeenCalledWith('quality');
  });

  test('shows advanced toggle when onOverrideChange provided', () => {
    const handlePresetChange = vi.fn();
    const handleOverrideChange = vi.fn();

    render(
      <PresetSelector
        selectedPreset="balanced"
        onPresetChange={handlePresetChange}
        onOverrideChange={handleOverrideChange}
      />
    );

    expect(screen.getByText('Show per-tool overrides')).toBeInTheDocument();
  });

  test('hides advanced toggle when onOverrideChange not provided', () => {
    const handlePresetChange = vi.fn();

    render(
      <PresetSelector selectedPreset="balanced" onPresetChange={handlePresetChange} />
    );

    expect(screen.queryByText('Show per-tool overrides')).not.toBeInTheDocument();
  });

  test('toggles override controls visibility', () => {
    const handlePresetChange = vi.fn();
    const handleOverrideChange = vi.fn();

    render(
      <PresetSelector
        selectedPreset="balanced"
        onPresetChange={handlePresetChange}
        onOverrideChange={handleOverrideChange}
      />
    );

    // Initially hidden
    expect(screen.queryByText('read file:')).not.toBeInTheDocument();

    // Click checkbox to show
    const checkbox = screen.getByLabelText('Show per-tool overrides') as HTMLInputElement;
    fireEvent.click(checkbox);

    // Now visible
    expect(screen.getByText('read file:')).toBeInTheDocument();
    expect(screen.getByText('write file:')).toBeInTheDocument();
    expect(screen.getByText('search code:')).toBeInTheDocument();
    expect(screen.getByText('web search:')).toBeInTheDocument();
    expect(screen.getByText('run python:')).toBeInTheDocument();
  });

  test('calls onOverrideChange when tool tier changed', () => {
    const handlePresetChange = vi.fn();
    const handleOverrideChange = vi.fn();

    render(
      <PresetSelector
        selectedPreset="balanced"
        onPresetChange={handlePresetChange}
        onOverrideChange={handleOverrideChange}
        showOverrides={true}
      />
    );

    // Change read_file tier
    const readFileSelect = screen.getByLabelText('Model tier for read file') as HTMLSelectElement;
    fireEvent.change(readFileSelect, { target: { value: 'powerful' } });

    expect(handleOverrideChange).toHaveBeenCalledWith({
      read_file: { tier: 'powerful' },
    });
  });

  test('displays existing override values', () => {
    const handlePresetChange = vi.fn();
    const handleOverrideChange = vi.fn();

    const overrides: Partial<Record<ToolName, ToolModelConfig>> = {
      read_file: { tier: 'fast' },
      write_file: { tier: 'powerful' },
    };

    render(
      <PresetSelector
        selectedPreset="balanced"
        onPresetChange={handlePresetChange}
        onOverrideChange={handleOverrideChange}
        toolOverrides={overrides}
        showOverrides={true}
      />
    );

    // Check read_file shows 'fast'
    const readFileSelect = screen.getByLabelText('Model tier for read file') as HTMLSelectElement;
    expect(readFileSelect.value).toBe('fast');

    // Check write_file shows 'powerful'
    const writeFileSelect = screen.getByLabelText(
      'Model tier for write file'
    ) as HTMLSelectElement;
    expect(writeFileSelect.value).toBe('powerful');

    // Check search_code defaults to 'balanced' (no override)
    const searchCodeSelect = screen.getByLabelText(
      'Model tier for search code'
    ) as HTMLSelectElement;
    expect(searchCodeSelect.value).toBe('balanced');
  });

  test('applies custom className', () => {
    const handleChange = vi.fn();

    const { container } = render(
      <PresetSelector
        selectedPreset="balanced"
        onPresetChange={handleChange}
        className="custom-class"
      />
    );

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain('custom-class');
  });
});

/**
 * PresetSelector - Compact dropdown button for preset selection
 *
 * Features:
 * - Inline dropdown button showing current preset
 * - Vertical dropdown menu with all presets
 * - Mnemonic letter shortcuts (D/A/C/V/R/J)
 * - Underlined shortcut letters in preset names
 * - Terminal aesthetic with phosphor orange theme (#ff9500)
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { usePresets } from '@/hooks/usePresets';
import styles from './PresetSelector.module.css';

interface PresetSelectorProps {
  selectedPreset: string;
  onPresetChange: (presetId: string) => void;
  disabled?: boolean;
}

// Preset key mappings - mnemonic letters
const PRESET_KEY_MAP: Record<string, { key: string; display: React.ReactNode }> = {
  'SYNAPSE_DEFAULT': {
    key: 'd',
    display: <><u>D</u>EFAULT</>
  },
  'SYNAPSE_ANALYST': {
    key: 'a',
    display: <><u>A</u>NALYST</>
  },
  'SYNAPSE_CODER': {
    key: 'c',
    display: <><u>C</u>ODER</>
  },
  'SYNAPSE_CREATIVE': {
    key: 'v',
    display: <>CREATI<u>V</u>E</>
  },
  'SYNAPSE_RESEARCH': {
    key: 'r',
    display: <><u>R</u>ESEARCH</>
  },
  'SYNAPSE_JUDGE': {
    key: 'j',
    display: <><u>J</u>UDGE</>
  },
  'CUSTOM': {
    key: 'u',
    display: <>C<u>U</u>STOM</>
  },
};

// Reverse mapping: key -> preset ID
const KEY_TO_PRESET: Record<string, string> = Object.fromEntries(
  Object.entries(PRESET_KEY_MAP).map(([id, { key }]) => [key, id])
);

// Preset order for dropdown
const PRESET_ORDER = [
  'SYNAPSE_DEFAULT',
  'SYNAPSE_ANALYST',
  'SYNAPSE_CODER',
  'SYNAPSE_CREATIVE',
  'SYNAPSE_RESEARCH',
  'SYNAPSE_JUDGE',
  'CUSTOM', // Custom is last
];

export const PresetSelector: React.FC<PresetSelectorProps> = ({
  selectedPreset,
  onPresetChange,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState<{ top: number; left: number; width: number } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { data: allPresets, isLoading } = usePresets();

  // Calculate dropdown position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4, // 4px gap
        left: rect.left + window.scrollX,
        width: Math.max(rect.width, 180), // At least 180px wide
      });
    } else {
      setDropdownPosition(null);
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        buttonRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Keyboard shortcuts (D/A/C/V/R/J) for preset selection
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if user is in an input field
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement ||
        (e.target as HTMLElement).isContentEditable
      ) {
        return;
      }

      // Check for preset shortcut keys (case-insensitive)
      const key = e.key.toLowerCase();
      const presetId = KEY_TO_PRESET[key];

      if (presetId && !disabled) {
        e.preventDefault();
        onPresetChange(presetId);
        setIsOpen(false);
      }

      // Escape closes dropdown
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onPresetChange, disabled, isOpen]);

  const getPresetDescription = useCallback((presetId: string): string => {
    if (presetId === 'CUSTOM') {
      return 'Use a custom system prompt for this query';
    }
    if (!allPresets) return '';
    const preset = allPresets.find(p => p.name === presetId);
    return preset?.description || '';
  }, [allPresets]);

  const getShortName = (presetId: string): string => {
    const match = presetId.match(/^SYNAPSE_(.+)$/);
    return match ? match[1] : presetId;
  };

  const handleSelect = (presetId: string) => {
    onPresetChange(presetId);
    setIsOpen(false);
  };

  // Render dropdown menu in portal
  const renderDropdownMenu = () => {
    if (!isOpen || !dropdownPosition) return null;

    return createPortal(
      <div
        ref={dropdownRef}
        className={styles.dropdownMenu}
        role="listbox"
        style={{
          position: 'absolute',
          top: `${dropdownPosition.top}px`,
          left: `${dropdownPosition.left}px`,
          minWidth: `${dropdownPosition.width}px`,
        }}
      >
        {PRESET_ORDER.map((presetId) => {
          const keyInfo = PRESET_KEY_MAP[presetId];
          const isSelected = selectedPreset === presetId;

          return (
            <button
              key={presetId}
              className={`${styles.dropdownOption} ${isSelected ? styles.selected : ''}`}
              onClick={() => handleSelect(presetId)}
              disabled={disabled}
              type="button"
              role="option"
              aria-selected={isSelected}
              title={getPresetDescription(presetId)}
            >
              <span className={styles.optionKey}>[{keyInfo?.key.toUpperCase()}]</span>
              <span className={styles.optionLabel}>{keyInfo?.display || getShortName(presetId)}</span>
              {isSelected && <span className={styles.checkmark}>●</span>}
            </button>
          );
        })}
      </div>,
      document.body
    );
  };

  return (
    <div className={styles.presetSelector}>
      {/* Dropdown Button */}
      <button
        ref={buttonRef}
        className={`${styles.dropdownButton} ${isOpen ? styles.open : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isLoading}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title={getPresetDescription(selectedPreset)}
      >
        <span className={styles.buttonIcon}>◆</span>
        <span className={styles.buttonLabel}>{getShortName(selectedPreset)}</span>
        <span className={styles.buttonArrow}>{isOpen ? '▲' : '▼'}</span>
      </button>

      {/* Dropdown Menu (rendered in portal) */}
      {renderDropdownMenu()}
    </div>
  );
};

PresetSelector.displayName = 'PresetSelector';

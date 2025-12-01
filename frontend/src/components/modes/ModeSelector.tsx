import React, { useState } from 'react';
import styles from './ModeSelector.module.css';

export type QueryMode = 'two-stage' | 'simple' | 'council' | 'benchmark';

export interface ModeConfig {
  adversarial?: boolean;
  serial?: boolean;
  councilMaxTurns?: number;
  councilDynamicTermination?: boolean;
  councilPersonaProfile?: string;
  councilPersonas?: {
    pro?: string;
    con?: string;
  };
  councilModerator?: boolean;
  councilModeratorActive?: boolean;
  councilModeratorModel?: string;
  councilProModel?: string;
  councilConModel?: string;
  councilPresetOverrides?: Record<string, string>;
}

interface ModeSelectorProps {
  currentMode: QueryMode;
  onModeChange: (mode: QueryMode, config?: ModeConfig) => void;
  queryPreset?: string;
}

interface ModeDefinition {
  id: QueryMode;
  label: string;
  description: string;
  available: boolean;
}

const MODES: ModeDefinition[] = [
  {
    id: 'two-stage',
    label: 'TWO-STAGE',
    description: 'Fast model + CGRAG → Powerful refinement',
    available: true
  },
  {
    id: 'simple',
    label: 'SIMPLE',
    description: 'Single model query',
    available: true
  },
  {
    id: 'council',
    label: 'COUNCIL',
    description: 'Multiple models collaborate or debate',
    available: true
  },
  {
    id: 'benchmark',
    label: 'BENCHMARK',
    description: 'Compare all models side-by-side',
    available: true
  }
];

export const ModeSelector: React.FC<ModeSelectorProps> = ({
  currentMode,
  onModeChange,
  queryPreset = 'SYNAPSE_ANALYST'
}) => {
  const [isAdversarial, setIsAdversarial] = useState(false);
  const [benchmarkSerial, setBenchmarkSerial] = useState(false);

  // Multi-chat dialogue state
  const [councilMaxTurns, setCouncilMaxTurns] = useState(10);
  const [councilDynamicTermination, setCouncilDynamicTermination] = useState(true);
  const [councilPersonaProfile, setCouncilPersonaProfile] = useState('');
  const [councilPersonaPro, setCouncilPersonaPro] = useState('');
  const [councilPersonaCon, setCouncilPersonaCon] = useState('');

  // Moderator state
  const [councilModerator, setCouncilModerator] = useState(false);
  const [councilModeratorActive, setCouncilModeratorActive] = useState(false);
  const [councilModeratorModel, setCouncilModeratorModel] = useState('');
  const [councilProModel, setCouncilProModel] = useState('');
  const [councilConModel, setCouncilConModel] = useState('');

  // Preset override state
  const [presetOverrides, setPresetOverrides] = useState<Record<string, string>>({});

  const handleModeClick = (modeId: QueryMode) => {
    onModeChange(modeId);
  };

  const handlePresetOverride = (role: string, presetId: string) => {
    setPresetOverrides(prev => {
      if (presetId === 'inherited') {
        // Remove override - use inherited
        const { [role]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [role]: presetId };
    });
  };

  const handleAdversarialChange = (checked: boolean) => {
    setIsAdversarial(checked);
    onModeChange('council', {
      adversarial: checked,
      councilMaxTurns,
      councilDynamicTermination,
      councilPersonaProfile: councilPersonaProfile || undefined,
      councilPersonas: !councilPersonaProfile && (councilPersonaPro || councilPersonaCon)
        ? { pro: councilPersonaPro, con: councilPersonaCon }
        : undefined,
      councilModerator,
      councilModeratorActive,
      councilModeratorModel: councilModeratorModel || undefined,
      councilProModel: councilProModel || undefined,
      councilConModel: councilConModel || undefined,
      councilPresetOverrides: Object.keys(presetOverrides).length > 0 ? presetOverrides : undefined
    });
  };

  const updateCouncilConfig = () => {
    onModeChange('council', {
      adversarial: isAdversarial,
      councilMaxTurns,
      councilDynamicTermination,
      councilPersonaProfile: councilPersonaProfile || undefined,
      councilPersonas: !councilPersonaProfile && (councilPersonaPro || councilPersonaCon)
        ? { pro: councilPersonaPro, con: councilPersonaCon }
        : undefined,
      councilModerator,
      councilModeratorActive,
      councilModeratorModel: councilModeratorModel || undefined,
      councilProModel: councilProModel || undefined,
      councilConModel: councilConModel || undefined,
      councilPresetOverrides: Object.keys(presetOverrides).length > 0 ? presetOverrides : undefined
    });
  };

  const handleBenchmarkSerialChange = (checked: boolean) => {
    setBenchmarkSerial(checked);
    onModeChange('benchmark', { serial: checked });
  };

  return (
    <div className={styles.modeSelectorContainer}>
      <div className={styles.sectionContent}>
        <div className={styles.modeGrid}>
        {MODES.map(mode => (
          <button
            key={mode.id}
            className={`
              ${styles.modeButton}
              ${currentMode === mode.id ? styles.active : ''}
              ${!mode.available ? styles.disabled : ''}
            `}
            onClick={() => mode.available && handleModeClick(mode.id)}
            disabled={!mode.available}
            aria-label={`${mode.label}: ${mode.description}`}
          >
            <div className={styles.modeLabel}>{mode.label}</div>
            <div className={styles.modeDescription}>{mode.description}</div>
            {!mode.available && (
              <div className={styles.comingSoon}>COMING SOON</div>
            )}
          </button>
        ))}
      </div>

      {currentMode === 'council' && (
        <div className={styles.councilConfig}>
          <div className={styles.configHeader}>
            ▓ COUNCIL MODE CONFIGURATION
          </div>

          {/* Adversarial/Consensus Toggle */}
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={isAdversarial}
              onChange={(e) => handleAdversarialChange(e.target.checked)}
              className={styles.adversarialCheckbox}
            />
            Enable Adversarial Debate
          </label>
          <div className={styles.configDescription}>
            {isAdversarial ? (
              <>
                <strong>Adversarial Mode:</strong> Two models argue opposing viewpoints
                with alternating counterarguments.
              </>
            ) : (
              <>
                <strong>Consensus Mode:</strong> Multiple models collaborate through
                sequential refinement to reach agreement.
              </>
            )}
          </div>

          {/* Max Turns Slider */}
          <div className={styles.configOption}>
            <label className={styles.configLabel}>
              Max Dialogue Turns: {councilMaxTurns}
            </label>
            <input
              type="range"
              min={2}
              max={20}
              value={councilMaxTurns}
              onChange={(e) => setCouncilMaxTurns(Number(e.target.value))}
              className={styles.slider}
            />
            <span className={styles.sliderHint}>
              {councilMaxTurns < 6 ? 'Quick' : councilMaxTurns < 12 ? 'Balanced' : 'Extended'}
            </span>
          </div>

          {/* Dynamic Termination Checkbox */}
          <div className={styles.configOption}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={councilDynamicTermination}
                onChange={(e) => setCouncilDynamicTermination(e.target.checked)}
              />
              <span>Dynamic Termination</span>
            </label>
            <span className={styles.hint}>
              End early if stalemate or concession detected
            </span>
          </div>

          {/* Persona Configuration Section */}
          <div className={styles.configSection}>
            <h4 className={styles.sectionTitle}>Persona Configuration</h4>

            {/* Named Profile Dropdown */}
            <div className={styles.configOption}>
              <label className={styles.configLabel}>Named Profile</label>
              <select
                value={councilPersonaProfile}
                onChange={(e) => setCouncilPersonaProfile(e.target.value)}
                className={styles.select}
              >
                <option value="">-- Custom Personas --</option>
                <option value="classic">Classic (Optimist vs. Skeptic)</option>
                <option value="technical">Technical (Architect vs. Engineer)</option>
                <option value="business">Business (PM vs. Risk Analyst)</option>
                <option value="scientific">Scientific (Researcher vs. Peer Reviewer)</option>
                <option value="ethical">Ethical (Ethicist vs. Pragmatist)</option>
                <option value="political">Political (Progressive vs. Conservative)</option>
              </select>
            </div>

            {/* Custom Personas (only show if no profile selected) */}
            {!councilPersonaProfile && (
              <>
                <div className={styles.configOption}>
                  <label className={styles.configLabel}>PRO Persona</label>
                  <input
                    type="text"
                    value={councilPersonaPro}
                    onChange={(e) => setCouncilPersonaPro(e.target.value)}
                    placeholder="e.g., an environmental advocate..."
                    className={styles.input}
                  />
                </div>

                <div className={styles.configOption}>
                  <label className={styles.configLabel}>CON Persona</label>
                  <input
                    type="text"
                    value={councilPersonaCon}
                    onChange={(e) => setCouncilPersonaCon(e.target.value)}
                    placeholder="e.g., a fiscal conservative..."
                    className={styles.input}
                  />
                </div>
              </>
            )}
          </div>

          {/* Moderator Options Section */}
          <div className={styles.configSection}>
            <h4 className={styles.sectionTitle}>Moderator Options</h4>

            <div className={styles.moderatorToggles}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={councilModerator}
                  onChange={(e) => {
                    setCouncilModerator(e.target.checked);
                    updateCouncilConfig();
                  }}
                />
                <span>Post-Debate Analysis</span>
              </label>

              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={councilModeratorActive}
                  onChange={(e) => {
                    setCouncilModeratorActive(e.target.checked);
                    updateCouncilConfig();
                  }}
                />
                <span>Active Interjections</span>
              </label>
            </div>

            <div className={styles.moderatorHint}>
              Post-Debate: Comprehensive analysis after dialogue completes
              <br />
              Active Interjections: Real-time guidance during debate (coming soon)
            </div>
          </div>

          {/* Model Selection Section (only for adversarial mode) */}
          {isAdversarial && (
            <div className={styles.configSection}>
              <h4 className={styles.sectionTitle}>Model Selection</h4>

              <div className={styles.modelSelectionGrid}>
                <div className={styles.configOption}>
                  <label className={styles.configLabel}>PRO Model</label>
                  <select
                    value={councilProModel}
                    onChange={(e) => {
                      setCouncilProModel(e.target.value);
                      updateCouncilConfig();
                    }}
                    className={styles.select}
                  >
                    <option value="">Auto-select (POWERFUL)</option>
                    <option value="Q4_1">Q4 Model 1</option>
                    <option value="Q4_2">Q4 Model 2</option>
                    <option value="Q3_1">Q3 Model 1</option>
                  </select>
                </div>

                <div className={styles.configOption}>
                  <label className={styles.configLabel}>CON Model</label>
                  <select
                    value={councilConModel}
                    onChange={(e) => {
                      setCouncilConModel(e.target.value);
                      updateCouncilConfig();
                    }}
                    className={styles.select}
                  >
                    <option value="">Auto-select (POWERFUL)</option>
                    <option value="Q4_1">Q4 Model 1</option>
                    <option value="Q4_2">Q4 Model 2</option>
                    <option value="Q3_1">Q3 Model 1</option>
                  </select>
                </div>

                {councilModerator && (
                  <div className={styles.configOption}>
                    <label className={styles.configLabel}>Moderator Model</label>
                    <select
                      value={councilModeratorModel}
                      onChange={(e) => {
                        setCouncilModeratorModel(e.target.value);
                        updateCouncilConfig();
                      }}
                      className={styles.select}
                    >
                      <option value="">Auto-select (POWERFUL)</option>
                      <option value="Q4_1">Q4 Model 1</option>
                      <option value="Q4_2">Q4 Model 2</option>
                    </select>
                  </div>
                )}
              </div>

              <div className={styles.modelHint}>
                Auto-select will use the most powerful available model
              </div>
            </div>
          )}

          {/* Preset Configuration Section */}
          {isAdversarial && (
            <div className={styles.configSection}>
              <h4 className={styles.sectionTitle}>Preset Configuration</h4>

              <div className={styles.presetInfo}>
                <span className={styles.presetLabel}>Query Preset:</span>
                <span className={styles.presetValue}>{queryPreset}</span>
              </div>

              <div className={styles.participantPresets}>
                {/* PRO Participant Preset */}
                <div className={styles.configOption}>
                  <label className={styles.configLabel}>PRO Preset</label>
                  <select
                    value={presetOverrides.pro || 'inherited'}
                    onChange={(e) => {
                      handlePresetOverride('pro', e.target.value);
                      updateCouncilConfig();
                    }}
                    className={styles.select}
                  >
                    <option value="inherited">INHERITED ({queryPreset})</option>
                    <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
                    <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
                    <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
                    <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
                    <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE</option>
                  </select>
                  {presetOverrides.pro && (
                    <span className={styles.overrideIndicator}>(Override)</span>
                  )}
                </div>

                {/* CON Participant Preset */}
                <div className={styles.configOption}>
                  <label className={styles.configLabel}>CON Preset</label>
                  <select
                    value={presetOverrides.con || 'inherited'}
                    onChange={(e) => {
                      handlePresetOverride('con', e.target.value);
                      updateCouncilConfig();
                    }}
                    className={styles.select}
                  >
                    <option value="inherited">INHERITED ({queryPreset})</option>
                    <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
                    <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
                    <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
                    <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
                    <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE</option>
                  </select>
                  {presetOverrides.con && (
                    <span className={styles.overrideIndicator}>(Override)</span>
                  )}
                </div>

                {/* Moderator Preset (only if moderator enabled) */}
                {councilModerator && (
                  <div className={styles.configOption}>
                    <label className={styles.configLabel}>Moderator Preset</label>
                    <select
                      value={presetOverrides.moderator || 'inherited'}
                      onChange={(e) => {
                        handlePresetOverride('moderator', e.target.value);
                        updateCouncilConfig();
                      }}
                      className={styles.select}
                    >
                      <option value="inherited">INHERITED ({queryPreset})</option>
                      <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
                      <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
                      <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
                      <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
                      <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE (Recommended)</option>
                    </select>
                    {presetOverrides.moderator && (
                      <span className={styles.overrideIndicator}>(Override)</span>
                    )}
                  </div>
                )}
              </div>

              <div className={styles.presetHint}>
                Participants inherit query preset by default. Override to customize behavior.
              </div>
            </div>
          )}
        </div>
      )}

      {currentMode === 'benchmark' && (
        <div className={styles.benchmarkConfig}>
          <div className={styles.configHeader}>
            ▓ BENCHMARK MODE CONFIGURATION
          </div>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={benchmarkSerial}
              onChange={(e) => handleBenchmarkSerialChange(e.target.checked)}
              className={styles.serialCheckbox}
            />
            Use Serial Execution (VRAM-Constrained)
          </label>
          <div className={styles.configDescription}>
            {benchmarkSerial ? (
              <>
                <strong>Serial Mode:</strong> Models execute one at a time to conserve VRAM.
                Total time will be longer but memory-safe.
              </>
            ) : (
              <>
                <strong>Parallel Mode:</strong> All models execute simultaneously for fastest
                results. Requires sufficient VRAM for all models.
              </>
            )}
          </div>
          <div className={styles.vramHint}>
            💡 Use serial mode if you have &lt;8GB VRAM or experience OOM errors
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

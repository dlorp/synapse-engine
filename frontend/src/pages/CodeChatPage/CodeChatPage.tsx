/**
 * CodeChatPage Component - Agentic Code Assistant with ReAct Loop Visualization
 *
 * Multi-model orchestrated coding assistant with:
 * - Workspace and context selection
 * - Real-time ReAct step visualization
 * - Tool execution tracking
 * - Markdown-rendered final answers
 *
 * This page provides a terminal-aesthetic interface for the Code Chat mode,
 * displaying the agent's reasoning process (thoughts), tool executions (actions),
 * and observations in real-time as they stream from the backend.
 */

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { CRTMonitor, AsciiPanel, Button } from '@/components/terminal';
import { ReActStepViewer } from './ReActStepViewer';
import { WorkspaceSelector } from './WorkspaceSelector';
import { ContextSelector } from './ContextSelector';
import { PresetSelector } from './PresetSelector';
import { DiffPreview } from './DiffPreview';
import { useCodeChat } from '@/hooks/useCodeChat';
import { useWorkspaceValidation } from '@/hooks/useWorkspaces';
import { usePresets } from '@/hooks/usePresets';
import type { AgentState, CodeChatRequest, ToolName, ToolModelConfig } from '@/types/codeChat';
import styles from './CodeChatPage.module.css';

/**
 * Main Code Chat page component.
 *
 * Manages configuration state (workspace, context, preset), query submission,
 * and real-time ReAct step visualization from the streaming API.
 */
export const CodeChatPage: React.FC = () => {
  // ============================================================================
  // Local State
  // ============================================================================

  /** User's query input */
  const [query, setQuery] = useState('');

  /** Selected workspace directory path */
  const [workspacePath, setWorkspacePath] = useState<string>('');

  /** Selected CGRAG context name */
  const [contextName, setContextName] = useState<string | null>(null);

  /** Selected preset (balanced, coding, quality, etc.) */
  const [preset, setPreset] = useState<string>('balanced');

  /** Per-tool model tier overrides */
  const [toolOverrides, setToolOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});

  /** Enable CGRAG context retrieval */
  const [useCgrag, setUseCgrag] = useState(false);

  /** Enable web search */
  const [useWebSearch, setUseWebSearch] = useState(false);

  /** Modal visibility state */
  const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);
  const [showContextSelector, setShowContextSelector] = useState(false);

  // ============================================================================
  // Hooks
  // ============================================================================

  /** Code Chat streaming hook */
  const {
    steps,
    currentState,
    answer,
    error,
    context,
    isLoading,
    pendingAction,
    submit,
    cancel,
    reset,
    approveAction,
    rejectAction,
  } = useCodeChat();

  /** Workspace validation hook */
  const { data: workspaceInfo } = useWorkspaceValidation(workspacePath);

  /** Fetch all presets to get their configurations */
  const { data: presets } = usePresets();

  // ============================================================================
  // Computed State
  // ============================================================================

  /** Get the full configuration for the currently selected preset */
  const currentPresetConfig = presets?.find(p => p.name === preset);

  // Debug: Log preset config to verify transformation from snake_case
  React.useEffect(() => {
    if (currentPresetConfig) {
      console.debug(`[CodeChatPage] Loaded preset config for '${preset}':`, {
        name: currentPresetConfig.name,
        planningTier: currentPresetConfig.planningTier,
        toolConfigKeys: Object.keys(currentPresetConfig.toolConfigs),
        sampleToolConfig: currentPresetConfig.toolConfigs.read_file,
      });
    }
  }, [currentPresetConfig, preset]);

  /** Whether agent is currently active (planning, executing, or observing) */
  const isActive = ['planning', 'executing', 'observing'].includes(currentState);

  /** Whether submit button should be enabled */
  const canSubmit = query.trim().length > 0 && workspacePath.length > 0 && !isLoading;

  // ============================================================================
  // Event Handlers
  // ============================================================================

  /**
   * Handle query submission.
   *
   * Validates configuration and submits query to the Code Chat API via SSE.
   */
  const handleSubmit = async () => {
    if (!canSubmit) return;

    const request: CodeChatRequest = {
      query: query.trim(),
      workspacePath,
      contextName,
      useCgrag,
      useWebSearch,
      preset,
      toolOverrides: Object.keys(toolOverrides).length > 0 ? toolOverrides : undefined,
      maxIterations: 10,
    };

    await submit(request);
  };

  /**
   * Handle cancel button click.
   *
   * Aborts the current query and notifies the backend.
   */
  const handleCancel = () => {
    cancel();
  };

  /**
   * Handle reset button click.
   *
   * Clears all steps, answer, and error state for a new query.
   */
  const handleReset = () => {
    reset();
    setQuery('');
  };

  /**
   * Handle preset change.
   *
   * Clears tool overrides when preset changes so user sees new preset defaults.
   */
  const handlePresetChange = (newPreset: string) => {
    setPreset(newPreset);
    setToolOverrides({}); // Clear overrides to show new preset defaults
  };

  /**
   * Get CSS class for current agent state.
   */
  const getStateClass = (state: AgentState): string => {
    const stateKey = `state${state.charAt(0).toUpperCase() + state.slice(1)}` as keyof typeof styles;
    return (styles[stateKey] as string | undefined) || (styles.stateIdle as string) || '';
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <CRTMonitor bloomIntensity={0.3} scanlinesEnabled curvatureEnabled>
      <div className={styles.page}>
        {/* Configuration Panel */}
        <AsciiPanel title="CODE CHAT CONFIGURATION">
          <div className={styles.configPanel}>
            {/* Workspace Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>WORKSPACE:</label>
              <div className={styles.configValue}>
                {workspacePath ? (
                  <>
                    <span className={styles.workspacePath}>{workspacePath}</span>
                    {workspaceInfo?.valid && workspaceInfo.projectInfo && (
                      <span className={styles.projectType}>
                        [{workspaceInfo.projectInfo.type.toUpperCase()}]
                      </span>
                    )}
                    {workspaceInfo?.isGitRepo && (
                      <span className={styles.gitIndicator}>[GIT]</span>
                    )}
                  </>
                ) : (
                  <span className={styles.notSelected}>NOT SELECTED</span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowWorkspaceSelector(true)}
                  disabled={isLoading}
                >
                  SELECT
                </Button>
              </div>
            </div>

            {/* Context Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>CONTEXT:</label>
              <div className={styles.configValue}>
                {contextName ? (
                  <span className={styles.contextName}>{contextName}</span>
                ) : (
                  <span className={styles.notSelected}>NONE</span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowContextSelector(true)}
                  disabled={isLoading}
                >
                  SELECT
                </Button>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={useCgrag}
                    onChange={(e) => setUseCgrag(e.target.checked)}
                    disabled={!contextName || isLoading}
                    className={styles.checkbox}
                  />
                  USE CGRAG
                </label>
              </div>
            </div>

            {/* Preset Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>PRESET:</label>
              <div className={styles.configValue}>
                <PresetSelector
                  selectedPreset={preset}
                  onPresetChange={handlePresetChange}
                  presetConfig={currentPresetConfig}
                  toolOverrides={toolOverrides}
                  onOverrideChange={setToolOverrides}
                />
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={useWebSearch}
                    onChange={(e) => setUseWebSearch(e.target.checked)}
                    disabled={isLoading}
                    className={styles.checkbox}
                  />
                  WEB SEARCH
                </label>
              </div>
            </div>
          </div>
        </AsciiPanel>

        {/* State Indicator Bar */}
        <div className={styles.stateBar}>
          <div className={styles.stateIndicator}>
            <span className={getStateClass(currentState)}>
              [{currentState.toUpperCase()}]
            </span>
            {steps.length > 0 && (
              <span className={styles.stepCount}>STEP {steps.length}</span>
            )}
          </div>
          <div className={styles.stateActions}>
            {isActive && (
              <Button onClick={handleCancel} variant="danger" size="sm">
                CANCEL
              </Button>
            )}
            {(currentState === 'completed' || currentState === 'error' || currentState === 'cancelled') && (
              <Button onClick={handleReset} variant="secondary" size="sm">
                RESET
              </Button>
            )}
          </div>
        </div>

        {/* Query Input */}
        <AsciiPanel title="QUERY">
          <div className={styles.inputSection}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your coding task or question..."
              disabled={isLoading}
              className={styles.queryTextarea}
              rows={4}
              aria-label="Code Chat query input"
            />
            <div className={styles.inputActions}>
              <Button
                onClick={handleSubmit}
                disabled={!canSubmit}
                variant="primary"
              >
                EXECUTE
              </Button>
            </div>
          </div>
        </AsciiPanel>

        {/* Error Display */}
        {error && (
          <AsciiPanel title="ERROR" variant="error">
            <div className={styles.errorMessage}>
              <pre>{error}</pre>
            </div>
          </AsciiPanel>
        )}

        {/* Pending Action Confirmation (Diff Preview) */}
        {pendingAction && pendingAction.diffPreview && (
          <div className={styles.pendingActionContainer}>
            <DiffPreview
              filePath={pendingAction.diffPreview.file_path as string}
              originalContent={pendingAction.diffPreview.original_content as string | null}
              newContent={pendingAction.diffPreview.new_content as string}
              changeType={pendingAction.diffPreview.change_type as 'create' | 'modify' | 'delete'}
              diffLines={pendingAction.diffPreview.diff_lines as Array<{
                lineNumber: number;
                type: 'add' | 'remove' | 'context';
                content: string;
              }>}
            />
            <div className={styles.confirmationButtons}>
              <Button
                onClick={() => approveAction(pendingAction.actionId)}
                variant="primary"
                size="md"
              >
                APPROVE
              </Button>
              <Button
                onClick={() => rejectAction(pendingAction.actionId)}
                variant="danger"
                size="md"
              >
                REJECT
              </Button>
            </div>
          </div>
        )}

        {/* CGRAG Context Display */}
        {context && (
          <AsciiPanel title="RETRIEVED CONTEXT">
            <div className={styles.contextPreview}>
              <pre className={styles.contextText}>{context.slice(0, 500)}...</pre>
            </div>
          </AsciiPanel>
        )}

        {/* ReAct Steps Container */}
        {steps.length > 0 && (
          <div className={styles.stepsContainer}>
            <AsciiPanel title="REACT EXECUTION TRACE">
              <div className={styles.stepsInner}>
                {steps.map((step) => (
                  <ReActStepViewer key={step.stepNumber} step={step} />
                ))}
              </div>
            </AsciiPanel>
          </div>
        )}

        {/* Final Answer */}
        {answer && (
          <AsciiPanel title="ANSWER" variant="accent">
            <div className={styles.answerPanel}>
              <ReactMarkdown>
                {answer}
              </ReactMarkdown>
            </div>
          </AsciiPanel>
        )}

        {/* Modal Components */}
        {showWorkspaceSelector && (
          <WorkspaceSelector
            currentWorkspace={workspacePath}
            onSelect={setWorkspacePath}
            onClose={() => setShowWorkspaceSelector(false)}
          />
        )}

        {showContextSelector && (
          <ContextSelector
            selectedContext={contextName}
            onSelect={setContextName}
            onClose={() => setShowContextSelector(false)}
          />
        )}
      </div>
    </CRTMonitor>
  );
};

CodeChatPage.displayName = 'CodeChatPage';

/**
 * ResponseDisplay Component
 *
 * Displays query response with metadata, complexity assessment,
 * and CGRAG artifacts in terminal aesthetic style.
 */

import React, { useCallback, useState, useMemo } from 'react';
import { toast } from 'react-toastify';
import { QueryResponse, BenchmarkResult } from '../../types/query';
import { Panel } from '../terminal/Panel/Panel';
import { MetricDisplay } from '../terminal/MetricDisplay/MetricDisplay';
import styles from './ResponseDisplay.module.css';

interface ResponseDisplayProps {
  response: QueryResponse | null;
}

interface ParsedResponse {
  thinking: string | null;
  answer: string;
}

/**
 * Detect reasoning patterns commonly used in model thinking processes.
 */
function hasReasoningPatterns(text: string): boolean {
  const reasoningPatterns = [
    /\bLet me think\b/i,
    /\bI need to\b/i,
    /\bFirst,?\s/i,
    /\bSecond,?\s/i,
    /\bThird,?\s/i,
    /\bStep \d+:/i,
    /\bLet's break\b/i,
    /\bConsider\b/i,
    /\bAnalyzing\b/i,
    /\bExamining\b/i,
    /\bWe need to\b/i,
    /\bI should\b/i,
    /\bThis means\b/i,
    /\bTherefore,?\s/i,
  ];

  return reasoningPatterns.some(pattern => pattern.test(text));
}

/**
 * Parse response to detect reasoning/thinking sections from models like DeepSeek R1, Qwen3.
 * Separates verbose reasoning from the final answer.
 *
 * Detection strategies (in priority order):
 * 1. <think> tags - explicit thinking markers used by DeepSeek R1
 * 2. Reasoning pattern detection - "Let me think", "I need to", etc.
 * 3. Delimiter patterns - "Answer:", "In conclusion:", etc.
 * 4. Length heuristic with reasoning indicators
 */
function parseResponse(response: string): ParsedResponse {
  // PRIORITY 1: Check for <think> tags (DeepSeek R1 format)
  const thinkMatch = response.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch && thinkMatch[1]) {
    const thinking = thinkMatch[1].trim();
    const answer = response.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    if (thinking.length > 50 && answer.length > 0) {
      return { thinking, answer };
    }
  }

  // PRIORITY 2: Detect reasoning patterns at the START of response
  // This catches models like Qwen3 that start with "Okay, I need to..." or "Let me think..."
  const reasoningStartPatterns = [
    /^(Okay,?\s+(?:I need to|let me|so|first|let's))/i,
    /^(Let me (?:think|start|figure|analyze|consider))/i,
    /^(I need to (?:figure out|think about|consider|analyze))/i,
    /^(First,?\s+(?:I|let me|we))/i,
    /^(Hmm\.?\s+)/i,
    /^(Alright,?\s+(?:so|let me|I))/i,
    /^(So,?\s+(?:I need|let me|the user))/i,
    /^(To (?:answer|address|figure out|solve) this)/i,
  ];

  const startsWithReasoning = reasoningStartPatterns.some(pattern => pattern.test(response));

  // PRIORITY 3: Look for common answer delimiters
  const answerPatterns = [
    /(?:^|\n)(?:Final )?Answer:\s*/i,
    /(?:^|\n)In conclusion:?\s*/i,
    /(?:^|\n)Therefore:?\s*/i,
    /(?:^|\n)So,?\s+(?:in summary|to summarize|the answer)\b/i,
    /(?:^|\n)To summarize:?\s*/i,
    /(?:^|\n)Summary:\s*/i,
    /(?:^|\n)The answer is:?\s*/i,
    /(?:^|\n)In short:?\s*/i,
    /(?:^|\n)(?:Based on|Given) (?:this|the above|my analysis):?\s*/i,
  ];

  for (const pattern of answerPatterns) {
    const match = response.match(pattern);
    if (match && match.index !== undefined) {
      const splitIndex = match.index + match[0].length;
      const thinking = response.slice(0, match.index).trim();
      const answer = response.slice(splitIndex).trim();

      if (thinking.length > 100) {
        return { thinking, answer };
      }
    }
  }

  // PRIORITY 4: If response starts with reasoning and is long, split it
  if (startsWithReasoning && response.length > 300) {
    // Look for transition to answer in the latter half
    const searchStart = Math.floor(response.length * 0.4);
    const latterHalf = response.slice(searchStart);

    // Look for conclusion indicators
    const conclusionPatterns = [
      /\n\n(?:So |Therefore |Thus |In conclusion|Based on|Given this|The answer|To answer)/i,
      /\n\n(?:Current|Today's|The weather|The date|Here's|For |To summarize)/i,
      /\.\s*(?:So,? |Therefore,? |Thus,? |In summary,? )/i,
    ];

    for (const pattern of conclusionPatterns) {
      const match = latterHalf.match(pattern);
      if (match && match.index !== undefined) {
        const actualIndex = searchStart + match.index;
        const thinking = response.slice(0, actualIndex).trim();
        const answer = response.slice(actualIndex).trim();

        if (thinking.length > 100 && answer.length > 50) {
          return { thinking, answer };
        }
      }
    }

    // If no clear conclusion found, use paragraph-based split
    const lastParagraph = response.lastIndexOf('\n\n');
    if (lastParagraph > response.length * 0.3 && lastParagraph < response.length * 0.9) {
      return {
        thinking: response.slice(0, lastParagraph).trim(),
        answer: response.slice(lastParagraph).trim(),
      };
    }

    // Fallback: treat entire response as thinking with a generic answer note
    if (response.length > 500) {
      return {
        thinking: response,
        answer: "[Model provided reasoning but no clear final answer. See thinking process above.]",
      };
    }
  }

  // PRIORITY 5: Long responses with reasoning indicators - more aggressive split
  if (response.length > 400 && hasReasoningPatterns(response)) {
    // Split at paragraph boundaries in the second half
    const midpoint = Math.floor(response.length * 0.5);
    const searchText = response.slice(midpoint);
    const paragraphBreak = searchText.indexOf('\n\n');

    if (paragraphBreak > 0) {
      const splitPoint = midpoint + paragraphBreak;
      return {
        thinking: response.slice(0, splitPoint).trim(),
        answer: response.slice(splitPoint).trim(),
      };
    }
  }

  // Short responses or no reasoning detected - no split needed
  return { thinking: null, answer: response };
}

export const ResponseDisplay: React.FC<ResponseDisplayProps> = ({
  response,
}) => {
  const [showThinking, setShowThinking] = useState(false);
  const [showFullResponse, setShowFullResponse] = useState(false);

  const parsedResponse = useMemo<ParsedResponse | null>(() => {
    if (!response) return null;
    return parseResponse(response.response);
  }, [response]);

  const copyToClipboard = useCallback(() => {
    if (!response) return;

    navigator.clipboard
      .writeText(response.response)
      .then(() => {
        toast.success('✓ Response copied to clipboard', {
          position: 'bottom-right',
          autoClose: 2000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
      })
      .catch((err) => {
        console.error('Failed to copy:', err);
        toast.error('✗ Failed to copy response', {
          position: 'bottom-right',
          autoClose: 3000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
      });
  }, [response]);

  const toggleThinking = useCallback(() => {
    setShowThinking((prev) => !prev);
  }, []);

  const toggleFullResponse = useCallback(() => {
    setShowFullResponse((prev) => !prev);
  }, []);

  if (!response) {
    return (
      <div className={styles.placeholder}>
        <span className={styles.cursor}>_</span>
        <span className={styles.placeholderText}>Awaiting query...</span>
      </div>
    );
  }

  const { metadata } = response;

  return (
    <div className={styles.responseDisplay}>
      {/* Query Header */}
      <div className={styles.queryHeader}>
        <span className={styles.label}>QUERY:</span>
        <span className={styles.queryText}>{response.query}</span>
      </div>

      {/* Response Content */}
      <Panel title="RESPONSE" variant="default">
        <div className={styles.responseContent}>
          {/* Full Response Toggle (only show if thinking was detected) */}
          {parsedResponse?.thinking && !showFullResponse && (
            <div className={styles.displayModeToggle}>
              <button
                className={styles.modeButton}
                onClick={toggleFullResponse}
                type="button"
                aria-label="Show full unsplit response"
              >
                SHOW FULL RESPONSE
              </button>
            </div>
          )}

          {showFullResponse ? (
            /* Full Response View (no splitting) */
            <div className={styles.fullResponseSection}>
              <div className={styles.fullResponseHeader}>
                <span className={styles.fullResponseLabel}>FULL RESPONSE</span>
                <button
                  className={styles.backButton}
                  onClick={toggleFullResponse}
                  type="button"
                  aria-label="Return to split view"
                >
                  ← SPLIT VIEW
                </button>
              </div>
              <div className={styles.answerSection}>
                <pre className={styles.responseText}>
                  {response.response}
                </pre>
              </div>
            </div>
          ) : (
            /* Split View (thinking + answer) */
            <>
              {/* Thinking Process Section (Collapsible) */}
              {parsedResponse?.thinking && (
                <div className={styles.thinkingSection}>
                  <button
                    className={styles.thinkingToggle}
                    onClick={toggleThinking}
                    type="button"
                    aria-label={showThinking ? 'Hide thinking process' : 'Show thinking process'}
                    aria-expanded={showThinking}
                  >
                    <span className={styles.thinkingIcon}>
                      {showThinking ? '▼' : '▶'}
                    </span>
                    <span className={styles.thinkingLabel}>THOUGHT PROCESS</span>
                    <span className={styles.thinkingHint}>
                      ({parsedResponse.thinking.length} chars)
                    </span>
                  </button>
                  {showThinking && (
                    <pre className={styles.thinkingText}>
                      {parsedResponse.thinking}
                    </pre>
                  )}
                </div>
              )}

              {/* Answer Section (Scrollable) */}
              <div className={styles.answerSection}>
                <pre className={styles.responseText}>
                  {parsedResponse?.answer || response.response}
                </pre>
              </div>
            </>
          )}

          <button
            className={styles.copyButton}
            onClick={copyToClipboard}
            type="button"
            aria-label="Copy response to clipboard"
          >
            COPY
          </button>
        </div>
      </Panel>

      {/* Metadata Panel */}
      <Panel title="METADATA" variant="accent">
        <div className={styles.metadata}>
          {/* Primary Metrics */}
          <div className={styles.metricRow}>
            <MetricDisplay
              label="MODEL"
              value={`${metadata.modelId} [${metadata.modelTier}]`}
            />
            <MetricDisplay label="TOKENS" value={metadata.tokensUsed.toString()} />
            <MetricDisplay
              label="TIME"
              value={`${(metadata.processingTimeMs / 1000).toFixed(2)}s`}
            />
            {metadata.cacheHit && (
              <div className={styles.cacheIndicator}>
                <span className={styles.cacheIcon}>●</span>
                <span>CACHE HIT</span>
              </div>
            )}
          </div>

          {/* Complexity Assessment */}
          {metadata.complexity && (
            <div className={styles.complexity}>
              <div className={styles.complexityHeader}>
                <span className={styles.complexityLabel}>COMPLEXITY:</span>
                <span className={styles.complexityTier}>
                  {metadata.complexity.tier}
                </span>
                <span className={styles.complexityScore}>
                  Score: {metadata.complexity.score.toFixed(2)}
                </span>
              </div>
              <div className={styles.reasoning}>
                {metadata.complexity.reasoning}
              </div>
              {Object.keys(metadata.complexity.indicators).length > 0 && (
                <div className={styles.indicators}>
                  <span className={styles.indicatorsLabel}>Indicators:</span>
                  {Object.entries(metadata.complexity.indicators).map(
                    ([key, value]) => (
                      <span key={key} className={styles.indicator}>
                        {key}: {String(value)}
                      </span>
                    )
                  )}
                </div>
              )}
            </div>
          )}

          {/* CGRAG Artifacts */}
          {(metadata.cgragArtifacts > 0 ||
            (metadata.cgragArtifactsInfo && metadata.cgragArtifactsInfo.length > 0)) && (
            <div className={styles.cgrag}>
              <div className={styles.cgragHeader}>
                <span className={styles.cgragIcon}>▓</span>
                <span>
                  CGRAG ARTIFACTS: {metadata.cgragArtifacts || metadata.cgragArtifactsInfo?.length || 0}
                </span>
              </div>
              {metadata.cgragArtifactsInfo && metadata.cgragArtifactsInfo.length > 0 ? (
                <div className={styles.artifactList}>
                  {metadata.cgragArtifactsInfo.map((artifact, idx) => (
                    <div key={idx} className={styles.artifact}>
                      <div className={styles.artifactMain}>
                        <span className={styles.artifactIndex}>
                          [{idx + 1}]
                        </span>
                        <span className={styles.artifactPath}>
                          {artifact.filePath}
                        </span>
                      </div>
                      <div className={styles.artifactDetails}>
                        <span className={styles.artifactScore}>
                          Relevance: {(artifact.relevanceScore * 100).toFixed(1)}%
                        </span>
                        <span className={styles.artifactChunk}>
                          Chunk: {artifact.chunkIndex}
                        </span>
                        <span className={styles.artifactTokens}>
                          {artifact.tokenCount} tokens
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.artifactPlaceholder}>
                  No artifact details available
                </div>
              )}
            </div>
          )}
        </div>
      </Panel>

      {/* Web Search Results Panel */}
      {metadata.webSearchResults && metadata.webSearchResults.length > 0 && (
        <Panel title="WEB SEARCH RESULTS" variant="accent">
          <div className={styles.webSearchPanel}>
            {/* Header with count and timing */}
            <div className={styles.webSearchHeader}>
              <span className={styles.webSearchLabel}>
                FOUND: {metadata.webSearchResults.length} results
              </span>
              {metadata.webSearchTimeMs && (
                <span className={styles.webSearchTime}>
                  Search time: {metadata.webSearchTimeMs}ms
                </span>
              )}
            </div>

            {/* Results Grid */}
            <div className={styles.webSearchResultsGrid}>
              {metadata.webSearchResults.map((result, idx) => (
                <div key={`${result.url}-${idx}`} className={styles.webSearchResult}>
                  {/* Result Index and Score */}
                  <div className={styles.webSearchResultHeader}>
                    <span className={styles.webSearchResultIndex}>
                      [{idx + 1}]
                    </span>
                    {result.score && (
                      <span className={styles.webSearchResultScore}>
                        Score: {(result.score * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>

                  {/* Title */}
                  <div className={styles.webSearchResultTitle}>
                    {result.title}
                  </div>

                  {/* URL */}
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.webSearchResultUrl}
                  >
                    {result.url}
                  </a>

                  {/* Content/Snippet */}
                  {result.content && (
                    <div className={styles.webSearchResultContent}>
                      {result.content}
                    </div>
                  )}

                  {/* Metadata (engine, date) */}
                  <div className={styles.webSearchResultMeta}>
                    {result.engine && (
                      <span className={styles.webSearchResultEngine}>
                        Engine: {result.engine}
                      </span>
                    )}
                    {result.publishedDate && (
                      <span className={styles.webSearchResultDate}>
                        Published: {result.publishedDate}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Info Note */}
            <div className={styles.webSearchNote}>
              🔍 Web search results included in context for enhanced accuracy
            </div>
          </div>
        </Panel>
      )}

      {/* Two-Stage Processing Panel */}
      {metadata.queryMode === 'two-stage' && (
        <Panel title="TWO-STAGE PROCESSING" variant="accent">
          <div className={styles.twoStageInfo}>
            {/* Stage 1 */}
            <div className={styles.stage}>
              <div className={styles.stageHeader}>
                <span className={styles.stageLabel}>
                  STAGE 1: {metadata.stage1Tier?.toUpperCase()}
                </span>
                <span className={styles.stageModel}>{metadata.stage1ModelId}</span>
                <span className={styles.stageTime}>
                  {metadata.stage1ProcessingTime}ms
                </span>
              </div>

              {metadata.stage1Response && (
                <details className={styles.stageDetails}>
                  <summary className={styles.stageSummary}>
                    View Stage 1 Response ({metadata.stage1Tokens} tokens)
                  </summary>
                  <pre className={styles.stageResponse}>
                    {metadata.stage1Response}
                  </pre>
                </details>
              )}
            </div>

            {/* Arrow indicator */}
            <div className={styles.stageArrow}>
              ↓ REFINEMENT ↓
            </div>

            {/* Stage 2 */}
            <div className={styles.stage}>
              <div className={styles.stageHeader}>
                <span className={styles.stageLabel}>
                  STAGE 2: {metadata.stage2Tier?.toUpperCase()}
                </span>
                <span className={styles.stageModel}>{metadata.stage2ModelId}</span>
                <span className={styles.stageTime}>
                  {metadata.stage2ProcessingTime}ms
                </span>
              </div>

              <div className={styles.stageNote}>
                Final response shown above
              </div>
            </div>

            {/* Total timing */}
            <div className={styles.totalTiming}>
              Total: {metadata.processingTimeMs}ms
            </div>
          </div>
        </Panel>
      )}

      {/* Moderator Analysis Panel */}
      {metadata.queryMode === 'council' && metadata.councilModeratorAnalysis && (
        <Panel title="MODERATOR ANALYSIS" variant="accent">
          <div className={styles.moderatorAnalysis}>
            {/* Header */}
            <div className={styles.moderatorHeader}>
              <span className={styles.moderatorModel}>
                Model: {metadata.councilModeratorModel || 'Auto-selected'}
              </span>
              {metadata.councilModeratorTokens && (
                <span className={styles.moderatorTokens}>
                  {metadata.councilModeratorTokens} tokens
                </span>
              )}
              {metadata.councilModeratorInterjections !== undefined && (
                <span className={styles.moderatorInterjections}>
                  {metadata.councilModeratorInterjections} interjections
                </span>
              )}
            </div>

            {/* Analysis Text */}
            <div className={styles.analysisText}>
              <pre className={styles.analysisContent}>
                {metadata.councilModeratorAnalysis}
              </pre>
            </div>

            {/* Structured Breakdown (collapsible) */}
            {metadata.councilModeratorBreakdown && (
              <details className={styles.breakdownDetails}>
                <summary className={styles.breakdownSummary}>
                  View Structured Breakdown
                </summary>
                <div className={styles.breakdownContent}>
                  {/* Argument Strength */}
                  {metadata.councilModeratorBreakdown.argument_strength && (
                    <div className={styles.breakdownSection}>
                      <h4 className={styles.breakdownTitle}>ARGUMENT STRENGTH</h4>
                      <div className={styles.argumentGrid}>
                        <div className={styles.argumentSide}>
                          <span className={styles.sideLabel}>PRO Strengths:</span>
                          <ul>
                            {metadata.councilModeratorBreakdown.argument_strength.pro_strengths?.map((s: string, i: number) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                        <div className={styles.argumentSide}>
                          <span className={styles.sideLabel}>CON Strengths:</span>
                          <ul>
                            {metadata.councilModeratorBreakdown.argument_strength.con_strengths?.map((s: string, i: number) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Logical Fallacies */}
                  {metadata.councilModeratorBreakdown.logical_fallacies &&
                   metadata.councilModeratorBreakdown.logical_fallacies.length > 0 && (
                    <div className={styles.breakdownSection}>
                      <h4 className={styles.breakdownTitle}>LOGICAL FALLACIES</h4>
                      <ul className={styles.fallacyList}>
                        {metadata.councilModeratorBreakdown.logical_fallacies.map((f: string, i: number) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Overall Winner */}
                  {metadata.councilModeratorBreakdown.overall_winner && (
                    <div className={styles.breakdownSection}>
                      <h4 className={styles.breakdownTitle}>OVERALL ASSESSMENT</h4>
                      <div className={styles.winnerDisplay}>
                        Winner: <span className={styles.winnerBadge}>
                          {metadata.councilModeratorBreakdown.overall_winner.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </Panel>
      )}

      {/* Council Mode Panel */}
      {metadata.queryMode === 'council' && metadata.councilResponses && (
        <Panel title="COUNCIL DELIBERATION" variant="accent">
          <div className={styles.councilInfo}>
            {/* Header */}
            <div className={styles.councilHeader}>
              <span className={styles.councilLabel}>
                MODE: {metadata.councilMode?.toUpperCase() || 'CONSENSUS'}
              </span>
              <span className={styles.councilParticipants}>
                PARTICIPANTS: {metadata.councilParticipants?.length || 0}
              </span>
              <span className={styles.councilRounds}>
                ROUNDS: {metadata.councilRounds || 2}
              </span>
            </div>

            {/* Consensus Mode View */}
            {metadata.councilMode === 'consensus' && (
              <div className={styles.participantGrid}>
                {metadata.councilResponses.map((participant: any, idx: number) => (
                  <div key={participant.model_id} className={styles.participant}>
                    <div className={styles.participantHeader}>
                      <span className={styles.participantLabel}>
                        MODEL {String.fromCharCode(65 + idx)}
                      </span>
                      <span className={styles.participantModel}>
                        {participant.model_id}
                      </span>
                    </div>

                    {/* Round 1 */}
                    <details className={styles.round}>
                      <summary className={styles.roundSummary}>
                        Round 1: Initial Response ({participant.round1?.split(' ').length || 0} words)
                      </summary>
                      <pre className={styles.roundResponse}>
                        {participant.round1}
                      </pre>
                    </details>

                    {/* Round 2 */}
                    <details className={styles.round}>
                      <summary className={styles.roundSummary}>
                        Round 2: Refined Response ({participant.round2?.split(' ').length || 0} words)
                      </summary>
                      <pre className={styles.roundResponse}>
                        {participant.round2}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            )}

            {/* Adversarial/Debate Mode View */}
            {metadata.councilMode === 'adversarial' && !response.councilDialogue && (
              <div className={styles.debateView}>
                <div className={styles.debateGrid}>
                  {/* PRO Side */}
                  <div className={styles.debateSide}>
                    <div className={styles.sideHeader} style={{borderColor: 'var(--text-success)'}}>
                      <span className={styles.sideLabel}>PRO POSITION</span>
                      <span className={styles.sideModel}>
                        {metadata.councilResponses?.[0]?.model_id}
                      </span>
                    </div>

                    <details className={styles.debateRound} open>
                      <summary className={styles.debateRoundSummary}>
                        Round 1: Opening Argument
                      </summary>
                      <pre className={styles.debateArgument}>
                        {metadata.councilResponses?.[0]?.round1}
                      </pre>
                    </details>

                    <details className={styles.debateRound}>
                      <summary className={styles.debateRoundSummary}>
                        Round 2: Rebuttal
                      </summary>
                      <pre className={styles.debateArgument}>
                        {metadata.councilResponses?.[0]?.round2}
                      </pre>
                    </details>
                  </div>

                  {/* CON Side */}
                  <div className={styles.debateSide}>
                    <div className={styles.sideHeader} style={{borderColor: 'var(--text-error)'}}>
                      <span className={styles.sideLabel}>CON POSITION</span>
                      <span className={styles.sideModel}>
                        {metadata.councilResponses?.[1]?.model_id}
                      </span>
                    </div>

                    <details className={styles.debateRound} open>
                      <summary className={styles.debateRoundSummary}>
                        Round 1: Opening Argument
                      </summary>
                      <pre className={styles.debateArgument}>
                        {metadata.councilResponses?.[1]?.round1}
                      </pre>
                    </details>

                    <details className={styles.debateRound}>
                      <summary className={styles.debateRoundSummary}>
                        Round 2: Rebuttal
                      </summary>
                      <pre className={styles.debateArgument}>
                        {metadata.councilResponses?.[1]?.round2}
                      </pre>
                    </details>
                  </div>
                </div>

                <div className={styles.debateSummary}>
                  ⚖️ Neutral summary of debate shown above
                </div>
              </div>
            )}

            {/* Multi-Chat Dialogue View (NEW) */}
            {response.councilDialogue && response.councilTurns && (
              <div className={styles.dialogueView}>
                <div className={styles.dialogueHeader}>
                  <span className={styles.dialogueTitle}>
                    {metadata.councilMode === 'adversarial' ? 'DEBATE DIALOGUE' : 'CONSENSUS DIALOGUE'}
                  </span>
                  <span className={styles.dialogueMeta}>
                    {response.councilTotalTurns} turns • {response.councilTerminationReason?.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className={styles.dialogueTranscript}>
                  {response.councilTurns.map((turn, idx) => {
                    const isModerator = turn.speakerId === 'MODERATOR';
                    const position = isModerator ? 'MODERATOR' : (turn.turnNumber % 2 === 1 ? 'PRO' : 'CON');
                    const isLeft = position === 'PRO';

                    return (
                      <div
                        key={idx}
                        className={`${styles.dialogueTurn} ${
                          isModerator ? styles.turnModerator :
                          isLeft ? styles.turnLeft : styles.turnRight
                        }`}
                      >
                        <div className={styles.turnHeader}>
                          <span className={styles.turnNumber}>Turn {turn.turnNumber}</span>
                          <span className={`${styles.turnPosition} ${
                            isModerator ? styles.moderator : styles[position.toLowerCase()]
                          }`}>
                            {position}
                          </span>
                          {!isModerator && <span className={styles.turnPersona}>{turn.persona}</span>}
                        </div>

                        <div className={styles.turnContent}>
                          {turn.content}
                        </div>

                        <div className={styles.turnFooter}>
                          <span className={styles.turnTokens}>{turn.tokensUsed} tokens</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className={styles.dialogueSynthesis}>
                  <div className={styles.synthesisHeader}>SYNTHESIS</div>
                  <div className={styles.synthesisContent}>
                    {response.councilSynthesis || response.response}
                  </div>
                </div>
              </div>
            )}

            {/* Consensus Note */}
            {metadata.councilMode === 'consensus' && (
              <div className={styles.consensusNote}>
                ✓ Final consensus answer shown above (synthesized from all refined responses)
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* Benchmark Mode Panel */}
      {metadata.queryMode === 'benchmark' && metadata.benchmarkResults && (
        <Panel title="BENCHMARK COMPARISON" variant="accent">
          <div className={styles.benchmarkInfo}>
            {/* Header with Summary */}
            {metadata.benchmarkSummary && (
              <div className={styles.benchmarkHeader}>
                <span className={styles.benchmarkLabel}>
                  MODE: {metadata.benchmarkExecutionMode?.toUpperCase() || 'PARALLEL'}
                </span>
                <span className={styles.benchmarkMetric}>
                  MODELS: {metadata.benchmarkSummary.successfulModels}/{metadata.benchmarkSummary.totalModels}
                </span>
                <span className={styles.benchmarkMetric}>
                  TOTAL TIME: {(metadata.benchmarkSummary.totalTimeMs / 1000).toFixed(2)}s
                </span>
                <span className={styles.benchmarkMetric}>
                  AVG TOKENS: {Math.round(metadata.benchmarkSummary.avgTokens)}
                </span>
              </div>
            )}

            {/* Results Grid */}
            <div className={styles.benchmarkGrid}>
              {metadata.benchmarkResults.map((result: BenchmarkResult, idx: number) => (
                <div
                  key={result.modelId}
                  className={`${styles.benchmarkResult} ${!result.success ? styles.benchmarkFailed : ''}`}
                >
                  {/* Result Header */}
                  <div className={styles.benchmarkResultHeader}>
                    <span className={styles.benchmarkModelLabel}>
                      MODEL {idx + 1}
                    </span>
                    <span className={styles.benchmarkModelId}>
                      {result.modelId}
                    </span>
                    <span className={styles.benchmarkTier}>
                      [{result.tier}]
                    </span>
                    {!result.success && (
                      <span className={styles.benchmarkErrorBadge}>
                        ✗ FAILED
                      </span>
                    )}
                  </div>

                  {/* Metrics */}
                  <div className={styles.benchmarkMetrics}>
                    <div className={styles.benchmarkMetricRow}>
                      <span className={styles.benchmarkMetricLabel}>TIME:</span>
                      <span className={styles.benchmarkMetricValue}>
                        {(result.processingTimeMs / 1000).toFixed(2)}s
                      </span>
                    </div>
                    <div className={styles.benchmarkMetricRow}>
                      <span className={styles.benchmarkMetricLabel}>TOKENS:</span>
                      <span className={styles.benchmarkMetricValue}>
                        {result.tokens}
                      </span>
                    </div>
                    <div className={styles.benchmarkMetricRow}>
                      <span className={styles.benchmarkMetricLabel}>VRAM:</span>
                      <span className={styles.benchmarkMetricValue}>
                        {result.estimatedVramGb.toFixed(2)} GB
                      </span>
                    </div>
                  </div>

                  {/* Response or Error */}
                  {result.success ? (
                    <details className={styles.benchmarkResponse}>
                      <summary className={styles.benchmarkResponseSummary}>
                        View Response ({result.responseText?.split(' ').length || 0} words)
                      </summary>
                      <pre className={styles.benchmarkResponseText}>
                        {result.responseText}
                      </pre>
                    </details>
                  ) : (
                    <div className={styles.benchmarkError}>
                      <span className={styles.benchmarkErrorLabel}>ERROR:</span>
                      <span className={styles.benchmarkErrorText}>
                        {result.error || 'Unknown error'}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Comparison Note */}
            <div className={styles.benchmarkNote}>
              ℹ️ Best answer shown above (selected from all successful responses)
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
};

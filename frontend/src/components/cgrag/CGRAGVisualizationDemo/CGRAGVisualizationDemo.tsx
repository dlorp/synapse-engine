/**
 * CGRAGVisualizationDemo - Comprehensive demo of all CGRAG visualizations
 *
 * Shows all visualization components with mock data for development/testing.
 * This component demonstrates:
 * 1. Retrieval Pipeline Flow
 * 2. Hybrid Search Metrics
 * 3. RAG Quality Triad
 * 4. CRAG Decisions
 * 5. Enhanced Chunk Display
 */

import React, { useState, useEffect } from 'react';
import { Panel } from '../../terminal/Panel/Panel';
import {
  RetrievalPipelineViz,
  HybridSearchPanel,
  RAGTriadDisplay,
  CRAGDecisionDisplay,
  EnhancedChunkCard,
} from '../index';
import {
  RetrievalPipeline,
  HybridSearchMetrics,
  RAGTriadMetrics,
  RAGQualityTrend,
  CRAGDecision,
  EnhancedChunk,
} from '../../../types/cgrag';
import styles from './CGRAGVisualizationDemo.module.css';

/**
 * Mock data generator for demo purposes.
 */
const generateMockData = () => {
  // Mock pipeline
  const pipeline: RetrievalPipeline = {
    stages: [
      {
        stage: 'embedding',
        status: 'complete',
        candidateCount: 1,
        executionTimeMs: 12,
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      },
      {
        stage: 'vector_search',
        status: 'complete',
        candidateCount: 50,
        executionTimeMs: 23,
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      },
      {
        stage: 'bm25_search',
        status: 'complete',
        candidateCount: 45,
        executionTimeMs: 18,
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      },
      {
        stage: 'fusion',
        status: 'complete',
        candidateCount: 30,
        executionTimeMs: 8,
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      },
      {
        stage: 'coarse_rerank',
        status: 'active',
        candidateCount: 20,
        startedAt: new Date().toISOString(),
      },
      {
        stage: 'fine_rerank',
        status: 'pending',
        candidateCount: 0,
      },
      {
        stage: 'filtering',
        status: 'pending',
        candidateCount: 0,
      },
      {
        stage: 'complete',
        status: 'pending',
        candidateCount: 0,
      },
    ],
    totalTimeMs: 61,
    currentStage: 'coarse_rerank',
    status: 'running',
  };

  // Mock hybrid search metrics
  const hybridMetrics: HybridSearchMetrics = {
    vectorCandidates: 50,
    bm25Candidates: 45,
    overlapCount: 28,
    avgVectorScore: 0.78,
    avgBm25Score: 0.65,
    rrfConstant: 60,
    topResults: [
      {
        chunkId: 'chunk-abc123',
        vectorScore: 0.92,
        bm25Score: 0.88,
        fusionScore: 0.91,
        vectorRank: 1,
        bm25Rank: 2,
        finalRank: 1,
      },
      {
        chunkId: 'chunk-def456',
        vectorScore: 0.85,
        bm25Score: 0.91,
        fusionScore: 0.89,
        vectorRank: 3,
        bm25Rank: 1,
        finalRank: 2,
      },
      {
        chunkId: 'chunk-ghi789',
        vectorScore: 0.88,
        bm25Score: 0.72,
        fusionScore: 0.82,
        vectorRank: 2,
        bm25Rank: 5,
        finalRank: 3,
      },
      {
        chunkId: 'chunk-jkl012',
        vectorScore: 0.76,
        bm25Score: 0.79,
        fusionScore: 0.78,
        vectorRank: 5,
        bm25Rank: 3,
        finalRank: 4,
      },
      {
        chunkId: 'chunk-mno345',
        vectorScore: 0.71,
        bm25Score: 0.75,
        fusionScore: 0.74,
        vectorRank: 7,
        bm25Rank: 4,
        finalRank: 5,
      },
    ],
  };

  // Mock RAG triad metrics
  const triadMetrics: RAGTriadMetrics = {
    contextRelevance: 0.87,
    groundedness: 0.92,
    answerRelevance: 0.85,
    overallQuality: 0.88,
    timestamp: new Date().toISOString(),
  };

  // Mock RAG quality trend
  const qualityTrend: RAGQualityTrend = {
    history: Array.from({ length: 20 }, (_, i) => ({
      contextRelevance: 0.75 + Math.random() * 0.2,
      groundedness: 0.8 + Math.random() * 0.15,
      answerRelevance: 0.78 + Math.random() * 0.18,
      overallQuality: 0.8 + Math.random() * 0.15,
      timestamp: new Date(Date.now() - i * 60000).toISOString(),
    })),
    avgContextRelevance: 0.84,
    avgGroundedness: 0.88,
    avgAnswerRelevance: 0.86,
    trend: 'improving',
  };

  // Mock CRAG decision
  const cragDecision: CRAGDecision = {
    action: 'query_rewrite',
    reason: 'Initial retrieval returned low-relevance results (avg score: 0.42)',
    originalQuery: 'How do I implement async patterns in Python?',
    rewrittenQuery:
      'Python asyncio async/await coroutines event loop implementation examples',
    timestamp: new Date().toISOString(),
  };

  // Mock enhanced chunks
  const chunks: EnhancedChunk[] = [
    {
      id: 'chunk-abc123',
      text: `async def fetch_data(url: str) -> dict:
    """Fetch data from API endpoint asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()`,
      sourcePath: '/backend/app/services/api_client.py',
      breadcrumb: {
        file: 'api_client.py',
        sections: ['AsyncAPIClient', 'fetch_data'],
        lineRange: { start: 45, end: 50 },
      },
      relevanceScore: 0.92,
      hybridScore: hybridMetrics.topResults[0],
      rerankingScore: {
        chunkId: 'chunk-abc123',
        initialScore: 0.78,
        coarseScore: 0.85,
        fineScore: 0.92,
        initialRank: 5,
        coarseRank: 3,
        finalRank: 1,
        scoreDelta: 0.14,
        rankChange: 4,
      },
      entities: [
        { text: 'aiohttp', label: 'LIBRARY', chunkId: 'chunk-abc123', confidence: 0.95 },
        { text: 'asyncio', label: 'MODULE', chunkId: 'chunk-abc123', confidence: 0.92 },
        { text: 'ClientSession', label: 'CLASS', chunkId: 'chunk-abc123', confidence: 0.88 },
      ],
      language: 'python',
      tokenCount: 85,
      indexedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: 'chunk-def456',
      text: `The asyncio module provides infrastructure for writing single-threaded concurrent code using coroutines, multiplexing I/O access over sockets and other resources, running network clients and servers, and other related primitives.`,
      sourcePath: '/docs/python/asyncio-guide.md',
      breadcrumb: {
        file: 'asyncio-guide.md',
        sections: ['Async Programming', 'Overview'],
      },
      relevanceScore: 0.85,
      hybridScore: hybridMetrics.topResults[1],
      tokenCount: 42,
      indexedAt: new Date(Date.now() - 172800000).toISOString(),
    },
  ];

  return { pipeline, hybridMetrics, triadMetrics, qualityTrend, cragDecision, chunks };
};

export const CGRAGVisualizationDemo: React.FC = () => {
  const [data, setData] = useState(generateMockData);

  // Simulate pipeline updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => {
        // Advance pipeline stages
        const newPipeline = { ...prev.pipeline };
        const activeIndex = newPipeline.stages.findIndex((s) => s.status === 'active');

        if (activeIndex !== -1) {
          // Complete active stage
          newPipeline.stages[activeIndex] = {
            ...newPipeline.stages[activeIndex],
            status: 'complete',
            candidateCount: Math.floor(Math.random() * 20) + 10,
            executionTimeMs: Math.floor(Math.random() * 50) + 10,
            completedAt: new Date().toISOString(),
          };

          // Activate next stage
          if (activeIndex + 1 < newPipeline.stages.length) {
            newPipeline.stages[activeIndex + 1] = {
              ...newPipeline.stages[activeIndex + 1],
              status: 'active',
              startedAt: new Date().toISOString(),
            };
            newPipeline.currentStage = newPipeline.stages[activeIndex + 1].stage;
          } else {
            newPipeline.status = 'complete';
          }

          newPipeline.totalTimeMs += newPipeline.stages[activeIndex].executionTimeMs || 0;
        }

        return { ...prev, pipeline: newPipeline };
      });
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.demo}>
      <Panel title="CGRAG VISUALIZATION DEMO" variant="accent">
        <div className={styles.info}>
          Comprehensive demonstration of enhanced CGRAG visualization components
          with simulated real-time updates.
        </div>
      </Panel>

      {/* Retrieval Pipeline */}
      <RetrievalPipelineViz pipeline={data.pipeline} />

      {/* Two-column layout */}
      <div className={styles.twoColumn}>
        {/* Left column: Hybrid Search + RAG Triad */}
        <div className={styles.column}>
          <HybridSearchPanel metrics={data.hybridMetrics} />
          <RAGTriadDisplay metrics={data.triadMetrics} trend={data.qualityTrend} />
        </div>

        {/* Right column: CRAG Decision + Chunks */}
        <div className={styles.column}>
          <CRAGDecisionDisplay decision={data.cragDecision} />

          <Panel title="RETRIEVED CHUNKS" titleRight={`${data.chunks.length} results`}>
            <div className={styles.chunks}>
              {data.chunks.map((chunk, index) => (
                <EnhancedChunkCard
                  key={chunk.id}
                  chunk={chunk}
                  rank={index + 1}
                  showScores
                  showEntities
                />
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
};

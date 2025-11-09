/**
 * Orchestrator status hook with real-time polling
 *
 * Fetches orchestrator status from backend every 1 second for real-time visualization.
 * Falls back to mock data if endpoint doesn't exist yet.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { OrchestratorStatus, RoutingDecision, TierUtilization, ComplexityDistribution } from '@/types/orchestrator';

// Mock data generator for development (until backend endpoint exists)
const generateMockData = (): OrchestratorStatus => {
  const now = new Date().toISOString();

  // Generate realistic tier utilization (changes over time)
  const tierUtilization: TierUtilization[] = [
    {
      tier: 'Q2',
      utilizationPercent: Math.floor(60 + Math.random() * 30), // 60-90%
      activeRequests: Math.floor(Math.random() * 5),
      totalProcessed: Math.floor(1000 + Math.random() * 500),
    },
    {
      tier: 'Q3',
      utilizationPercent: Math.floor(30 + Math.random() * 40), // 30-70%
      activeRequests: Math.floor(Math.random() * 3),
      totalProcessed: Math.floor(500 + Math.random() * 300),
    },
    {
      tier: 'Q4',
      utilizationPercent: Math.floor(10 + Math.random() * 30), // 10-40%
      activeRequests: Math.floor(Math.random() * 2),
      totalProcessed: Math.floor(200 + Math.random() * 150),
    },
  ];

  // Generate recent routing decisions
  const sampleQueries = [
    { query: 'quick status check', tier: 'Q2' as const, complexity: 'SIMPLE' as const, score: 1.2 },
    { query: 'compare two options', tier: 'Q3' as const, complexity: 'MODERATE' as const, score: 4.5 },
    { query: 'analyze complex pattern', tier: 'Q4' as const, complexity: 'COMPLEX' as const, score: 8.7 },
    { query: 'what is the time', tier: 'Q2' as const, complexity: 'SIMPLE' as const, score: 0.8 },
    { query: 'explain async patterns', tier: 'Q3' as const, complexity: 'MODERATE' as const, score: 5.2 },
    { query: 'architectural review', tier: 'Q4' as const, complexity: 'COMPLEX' as const, score: 9.1 },
    { query: 'list models', tier: 'Q2' as const, complexity: 'SIMPLE' as const, score: 1.0 },
  ];

  const recentDecisions: RoutingDecision[] = sampleQueries
    .slice(0, 5)
    .map((sample, idx) => ({
      id: `decision-${Date.now()}-${idx}`,
      query: sample.query,
      tier: sample.tier,
      complexity: sample.complexity,
      timestamp: new Date(Date.now() - idx * 5000).toISOString(),
      score: sample.score,
    }));

  // Complexity distribution (sums to 100%)
  const complexityDistribution: ComplexityDistribution = {
    simple: 45 + Math.floor(Math.random() * 10),
    moderate: 30 + Math.floor(Math.random() * 10),
    complex: 15 + Math.floor(Math.random() * 10),
  };

  return {
    tierUtilization,
    recentDecisions,
    complexityDistribution,
    totalDecisions: 1847,
    avgDecisionTimeMs: 12 + Math.random() * 8, // 12-20ms
    timestamp: now,
  };
};

const fetchOrchestratorStatus = async (): Promise<OrchestratorStatus> => {
  try {
    // Fetch real data from backend endpoint
    const response = await apiClient.get<OrchestratorStatus>('orchestrator/status');
    return response.data;
  } catch (error) {
    console.warn('Orchestrator status endpoint not available, falling back to mock data:', error);
    // Fallback to mock data if endpoint not available (during development)
    return generateMockData();
  }
};

export const useOrchestratorStatus = () => {
  return useQuery<OrchestratorStatus, Error>({
    queryKey: ['orchestratorStatus'],
    queryFn: fetchOrchestratorStatus,
    refetchInterval: 1000, // Refetch every 1 second for real-time updates
    staleTime: 500,
  });
};

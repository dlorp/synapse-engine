import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { CGRAGIndexer } from '../../components/admin';
import styles from './AdminPage.module.css';

interface HealthComponent {
  status: string;
  message?: string;
  models_count?: number;
  enabled_count?: number;
  last_scan?: string;
  total?: number;
  ready?: number;
  servers?: any[];
  available?: string[];
  count?: number;
  scan_path?: string;
}

interface HealthResponse {
  timestamp: string;
  status: string;
  components: Record<string, HealthComponent>;
}

interface TestResult {
  endpoint: string;
  status: 'passed' | 'failed';
  message: string;
}

interface TestResults {
  total: number;
  passed: number;
  failed: number;
  tests: TestResult[];
}

interface DiscoveryResult {
  message: string;
  models_found: number;
  scan_path: string;
  timestamp: string;
}

interface SystemInfo {
  python: {
    version: string;
    platform: string;
    processor: string;
  };
  environment: {
    profile: string;
    scan_path: string;
    llama_server_path: string;
  };
  services: Record<string, boolean>;
}

// ASCII Chart Utilities
const generateSparkline = (values: number[]): string => {
  const chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;

  return values.map(v => {
    const normalized = (v - min) / range;
    const index = Math.min(Math.floor(normalized * chars.length), chars.length - 1);
    return chars[index];
  }).join('');
};

const generateBarChart = (value: number, maxValue: number = 100, width: number = 20): string => {
  const filled = Math.floor((value / maxValue) * width);
  const empty = width - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

const generateLineChart = (values: number[], width: number = 60, height: number = 7): string[] => {
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;

  const lines: string[] = [];

  for (let y = height - 1; y >= 0; y--) {
    let line = '';
    const threshold = min + (range * y / (height - 1));

    for (let x = 0; x < Math.min(values.length, width); x++) {
      const value = values[x] ?? 0;
      const nextValue = x < values.length - 1 ? (values[x + 1] ?? 0) : value;

      if (value >= threshold && nextValue >= threshold) {
        line += '─';
      } else if (value >= threshold && nextValue < threshold) {
        line += '┐'; // Single-line corner (U+2510)
      } else if (value < threshold && nextValue >= threshold) {
        line += '└'; // Single-line corner (U+2514)
      } else {
        line += ' ';
      }
    }
    lines.push(line);
  }

  return lines;
};

// ASCII Frame Padding Utilities
const padLine = (content: string, width: number): string => {
  if (content.length > width) {
    return content.substring(0, width);
  }
  return content.padEnd(width, ' ');
};

export const AdminPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [testResults, setTestResults] = useState<TestResults | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<DiscoveryResult | null>(null);

  // Mock time-series data for visualizations (will be replaced with real metrics)
  const [metricsHistory, setMetricsHistory] = useState({
    cpu: Array(20).fill(0).map(() => Math.random() * 100),
    memory: Array(20).fill(0).map(() => Math.random() * 100),
    diskIO: Array(20).fill(0).map(() => Math.random() * 100),
    network: Array(20).fill(0).map(() => Math.random() * 100),
    requestRate: Array(60).fill(0).map(() => Math.random() * 150),
  });

  // Simulate live data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetricsHistory(prev => ({
        cpu: [...prev.cpu.slice(1), Math.random() * 100],
        memory: [...prev.memory.slice(1), Math.random() * 100],
        diskIO: [...prev.diskIO.slice(1), Math.random() * 100],
        network: [...prev.network.slice(1), Math.random() * 100],
        requestRate: [...prev.requestRate.slice(1), Math.random() * 150],
      }));
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  // Health check query
  const { data: health, refetch: refetchHealth, isLoading: healthLoading } = useQuery<HealthResponse>({
    queryKey: ['admin', 'health'],
    queryFn: async () => {
      const response = await apiClient.get('admin/health/detailed');
      return response.data;
    },
    refetchInterval: 10000, // Every 10s
  });

  // System info query
  const { data: systemInfo } = useQuery<SystemInfo>({
    queryKey: ['admin', 'system'],
    queryFn: async () => {
      const response = await apiClient.get('admin/system/info');
      return response.data;
    },
  });

  // Discovery mutation
  const runDiscovery = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('admin/discover');
      return response.data;
    },
    onSuccess: (data) => {
      setDiscoveryResult(data);
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
      refetchHealth();
    },
  });

  // Test endpoints mutation
  const runTests = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('admin/test/endpoints');
      return response.data;
    },
    onSuccess: (data) => {
      setTestResults(data);
    },
  });

  // Restart servers mutation
  const restartServers = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('admin/servers/restart');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serverStatus'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
      refetchHealth();
    },
  });

  // Stop servers mutation
  const stopServers = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('admin/servers/stop');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serverStatus'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
      refetchHealth();
    },
  });

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
      case 'passed':
        return styles.statusHealthy || '';
      case 'degraded':
        return styles.statusWarning || '';
      case 'unavailable':
      case 'failed':
        return styles.statusError || '';
      default:
        return '';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className={styles.adminPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>SYSTEM ADMIN & TESTING</h1>
        <div className={styles.subtitle}>Browser-based system operations and diagnostics</div>
      </div>

      {/* System Health */}
      <div className={styles.asciiPanel}>
        {healthLoading ? (
          <div className={styles.asciiPanelBody}>
            <div className={styles.loading}>LOADING HEALTH STATUS...</div>
          </div>
        ) : health ? (
          <div className={styles.asciiPanelBody}>
            {/* ASCII System Topology Diagram */}
            <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const serversReady = health.components.servers?.ready || 0;
  const serversTotal = health.components.servers?.total || 0;
  const modelsCount = health.components.registry?.models_count || 0;
  const profilesCount = health.components.profiles?.count || 0;
  const statusText = health.status.toUpperCase();

  const header = '─ SYSTEM HEALTH ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('TOPOLOGY:', FRAME_WIDTH)}
${padLine('[FASTAPI]──[ORCHESTRATOR]──[NEURAL SUBSTRATE]', FRAME_WIDTH)}
${padLine('    │             │                 │', FRAME_WIDTH)}
${padLine(`    │             ├──[Q2]─────────┼─── ${serversReady}/${serversTotal} ACTIVE`, FRAME_WIDTH)}
${padLine('    │             ├──[Q3]─────────┤', FRAME_WIDTH)}
${padLine('    │             └──[Q4]─────────┘', FRAME_WIDTH)}
${padLine('    │', FRAME_WIDTH)}
${padLine(`    └───[REGISTRY: ${modelsCount} models]`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`STATUS: ${statusText.padEnd(10)} │ Profiles: ${profilesCount} │ Ready: ${serversReady}`, FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
            </pre>

            <div className={styles.healthContainer}>
              <div className={styles.healthHeader}>
                <span className={styles.healthLabel}>OVERALL STATUS:</span>
                <span className={`${styles.healthStatus} ${getStatusColor(health.status)}`}>
                  {health.status.toUpperCase()}
                </span>
                <span className={styles.healthTime}>{formatTimestamp(health.timestamp)}</span>
              </div>
            </div>

            {/* System Metrics with Sparklines - OUTSIDE healthContainer for edge-to-edge */}
            <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const cpuVal = (metricsHistory.cpu[metricsHistory.cpu.length - 1] ?? 0).toFixed(0).padStart(2);
  const memVal = (metricsHistory.memory[metricsHistory.memory.length - 1] ?? 0).toFixed(0).padStart(2);
  const diskVal = (metricsHistory.diskIO[metricsHistory.diskIO.length - 1] ?? 0).toFixed(0).padStart(2);
  const netVal = (metricsHistory.network[metricsHistory.network.length - 1] ?? 0).toFixed(0).padStart(2);

  const cpuSparkline = generateSparkline(metricsHistory.cpu);
  const memSparkline = generateSparkline(metricsHistory.memory);
  const diskSparkline = generateSparkline(metricsHistory.diskIO);
  const netSparkline = generateSparkline(metricsHistory.network);

  const cpuBar = generateBarChart(metricsHistory.cpu[metricsHistory.cpu.length - 1] ?? 0, 100, 10);
  const memBar = generateBarChart(metricsHistory.memory[metricsHistory.memory.length - 1] ?? 0, 100, 10);
  const diskBar = generateBarChart(metricsHistory.diskIO[metricsHistory.diskIO.length - 1] ?? 0, 100, 10);
  const netBar = generateBarChart(metricsHistory.network[metricsHistory.network.length - 1] ?? 0, 100, 10);

  const header = '─ SYSTEM METRICS (LIVE) ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine(`CPU:    [${cpuSparkline}] ${cpuVal}% [${cpuBar}]`, FRAME_WIDTH)}
${padLine(`Memory: [${memSparkline}] ${memVal}% [${memBar}]`, FRAME_WIDTH)}
${padLine(`Disk:   [${diskSparkline}] ${diskVal}% [${diskBar}]`, FRAME_WIDTH)}
${padLine(`Net:    [${netSparkline}] ${netVal}% [${netBar}]`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
              </pre>

              {/* API Request Rate Chart */}
              <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const chartLines = generateLineChart(metricsHistory.requestRate, 55, 7);

  const header = '─ API REQUEST RATE (req/s) ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine(`150│${(chartLines[0] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`   │${(chartLines[1] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`100│${(chartLines[2] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`   │${(chartLines[3] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(` 50│${(chartLines[4] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`   │${(chartLines[5] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`  0│${(chartLines[6] ?? '').padEnd(60)}`, FRAME_WIDTH)}
${padLine(`   └${'─'.repeat(55)}`, FRAME_WIDTH)}
${padLine('     0s      60s     120s     180s     240s', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
              </pre>

              {/* Tier Performance Comparison */}
              <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ MODEL TIER PERFORMANCE ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('Q2_FAST      ████████████████████████████ 85.2 tok/s', FRAME_WIDTH)}
${padLine('Q3_BALANCED  ██████████████████ 52.7 tok/s', FRAME_WIDTH)}
${padLine('Q4_POWERFUL  ████████████ 28.4 tok/s', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine('├────────┼────────┼────────┼────────┼────────┼', FRAME_WIDTH)}
${padLine('0       20       40       60       80      100', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
              </pre>

            {/* Registry/Server/Profile sections - NO wrapper to allow edge-to-edge headers */}
            {/* Registry Status */}
            <div className={styles.asciiSection}>
              <div className={styles.asciiSectionHeader}>{`${'─ REGISTRY STATUS '}${'─'.repeat(150)}`}</div>
                <div className={styles.asciiSectionBody}>
                  {health.components.registry && (
                    <div className={styles.component}>
                      <div className={styles.componentHeader}>
                        <div className={styles.componentName}>MODEL REGISTRY</div>
                        <div className={`${styles.componentStatus} ${getStatusColor(health.components.registry.status)}`}>
                          {health.components.registry.status.toUpperCase()}
                        </div>
                      </div>
                      {health.components.registry.message && (
                        <div className={styles.componentMessage}>{health.components.registry.message}</div>
                      )}
                      {health.components.registry.models_count !== undefined && (
                        <div className={styles.componentDetails}>
                          <div>Models: {health.components.registry.models_count}</div>
                          <div>Enabled: {health.components.registry.enabled_count}</div>
                          {health.components.registry.last_scan && (
                            <div className={styles.lastScan}>Last Scan: {formatTimestamp(health.components.registry.last_scan)}</div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Server Status */}
              <div className={styles.asciiSection}>
                <div className={styles.asciiSectionHeader}>{`${'─ SERVER STATUS '}${'─'.repeat(150)}`}</div>
                <div className={styles.asciiSectionBody}>
                  {health.components.servers && (
                    <div className={styles.component}>
                      <div className={styles.componentHeader}>
                        <div className={styles.componentName}>MODEL SERVERS</div>
                        <div className={`${styles.componentStatus} ${getStatusColor(health.components.servers.status)}`}>
                          {health.components.servers.status.toUpperCase()}
                        </div>
                      </div>
                      {health.components.servers.message && (
                        <div className={styles.componentMessage}>{health.components.servers.message}</div>
                      )}
                      {health.components.servers.total !== undefined && health.components.servers.ready !== undefined && (
                        <div className={styles.componentDetails}>
                          <div>Servers: {health.components.servers.ready}/{health.components.servers.total}</div>
                          {health.components.servers.ready !== health.components.servers.total && (
                            <div className={styles.statusWarning}>
                              {health.components.servers.total - health.components.servers.ready} server(s) not ready
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Profile Status */}
              <div className={styles.asciiSection}>
                <div className={styles.asciiSectionHeader}>{`${'─ PROFILE STATUS '}${'─'.repeat(150)}`}</div>
                <div className={styles.asciiSectionBody}>
                  {health.components.profiles && (
                    <div className={styles.component}>
                      <div className={styles.componentHeader}>
                        <div className={styles.componentName}>CONFIGURATION PROFILES</div>
                        <div className={`${styles.componentStatus} ${getStatusColor(health.components.profiles.status)}`}>
                          {health.components.profiles.status.toUpperCase()}
                        </div>
                      </div>
                      {health.components.profiles.message && (
                        <div className={styles.componentMessage}>{health.components.profiles.message}</div>
                      )}
                      {health.components.profiles.count !== undefined && (
                        <div className={styles.componentDetails}>
                          <div>Available Profiles: {health.components.profiles.count}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Discovery Status */}
              <div className={styles.asciiSection}>
                <div className={styles.asciiSectionHeader}>{`${'─ DISCOVERY STATUS '}${'─'.repeat(150)}`}</div>
                <div className={styles.asciiSectionBody}>
                  {health.components.discovery && (
                    <div className={styles.component}>
                      <div className={styles.componentHeader}>
                        <div className={styles.componentName}>MODEL DISCOVERY</div>
                        <div className={`${styles.componentStatus} ${getStatusColor(health.components.discovery.status)}`}>
                          {health.components.discovery.status.toUpperCase()}
                        </div>
                      </div>
                      {health.components.discovery.message && (
                        <div className={styles.componentMessage}>{health.components.discovery.message}</div>
                      )}
                      {health.components.discovery.scan_path !== undefined && (
                        <div className={styles.componentDetails}>
                          <div className={styles.scanPath}>Scan Path: {health.components.discovery.scan_path}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

            {/* Refresh button with padding */}
            <div className={styles.healthContainer}>
              <button
                className={styles.actionButton}
                onClick={() => refetchHealth()}
              >
                REFRESH HEALTH
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.asciiPanelBody}>
            <div className={styles.error}>Failed to load health status</div>
          </div>
        )}
      </div>

      {/* Discovery */}
      <div className={styles.asciiPanel}>
        <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const scanStatus = runDiscovery.isPending ? '⚡ SCANNING...' : '◉ READY      ';
  const indexStatus = discoveryResult ? '✓' : '○';
  const modelsCount = String(health?.components.registry?.models_count || 0).padStart(2, '0');
  const progressBar = runDiscovery.isPending ? '[████████████░░░░░░░░] 60%' : '[████████████████████] 100%';

  const header = '─ MODEL DISCOVERY ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('FILE SYSTEM SCAN - NEURAL SUBSTRATE DISCOVERY', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`📦 HUB_ROOT [/models]                        ${scanStatus}`, FRAME_WIDTH)}
${padLine('├─┬ 📂 Q2_QUANTIZATION [FAST TIER]', FRAME_WIDTH)}
${padLine(`│ ├─ 📄 model_q2_k.gguf ......... [~2.1GB] ${indexStatus} INDEXED`, FRAME_WIDTH)}
${padLine(`│ └─ 📄 model_q2_k_small.gguf ... [~1.8GB] ${indexStatus} INDEXED`, FRAME_WIDTH)}
${padLine('│', FRAME_WIDTH)}
${padLine('├─┬ 📂 Q3_QUANTIZATION [BALANCED TIER]', FRAME_WIDTH)}
${padLine(`│ ├─ 📄 model_q3_k_m.gguf ......... [~3.5GB] ${indexStatus} INDEXED`, FRAME_WIDTH)}
${padLine(`│ └─ 📄 model_q3_k_l.gguf ......... [~4.2GB] ${indexStatus} INDEXED`, FRAME_WIDTH)}
${padLine('│', FRAME_WIDTH)}
${padLine('└─┬ 📂 Q4_QUANTIZATION [POWERFUL TIER]', FRAME_WIDTH)}
${padLine(`  └─ 📄 model_q4_k_m.gguf ......... [~5.8GB] ${indexStatus} INDEXED`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`📋 registry.json ............. [${modelsCount} models registered]`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`PROGRESS: ${progressBar}`, FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
        </pre>

          <div className={styles.discoverySection}>
            <p className={styles.sectionDesc}>
              Scan the HUB directory for GGUF models and update the registry.
              This will search for model files and register them in the system.
            </p>

            <button
              className={`${styles.actionButton} ${styles.primaryButton}`}
              onClick={() => runDiscovery.mutate()}
              disabled={runDiscovery.isPending}
            >
              {runDiscovery.isPending ? 'SCANNING...' : 'RUN DISCOVERY'}
            </button>

            {discoveryResult && (
              <div className={styles.resultBox}>
                <div className={styles.resultSuccess}>✅ {discoveryResult.message}</div>
                <div className={styles.resultDetails}>
                  <div className={styles.resultRow}>
                    <span className={styles.resultLabel}>Models Found:</span>
                    <span className={styles.resultValue}>{discoveryResult.models_found}</span>
                  </div>
                  <div className={styles.resultRow}>
                    <span className={styles.resultLabel}>Scan Path:</span>
                    <span className={styles.resultValue}>{discoveryResult.scan_path}</span>
                  </div>
                  <div className={styles.resultRow}>
                    <span className={styles.resultLabel}>Time:</span>
                    <span className={styles.resultValue}>{formatTimestamp(discoveryResult.timestamp)}</span>
                  </div>
                </div>
              </div>
            )}

            {runDiscovery.isError && (
              <div className={styles.resultBox}>
                <div className={styles.resultError}>
                  ❌ Discovery Failed: {(runDiscovery.error as any)?.response?.data?.detail?.message || (runDiscovery.error as Error).message}
                </div>
              </div>
            )}
          </div>
      </div>

      {/* CGRAG Vector Index Management */}
      <CGRAGIndexer />

      {/* API Testing */}
      <div className={styles.asciiPanel}>
        <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const getTestStatus = (searchTerm: string) => {
    const test = testResults?.tests.find(t => t.endpoint.includes(searchTerm));
    if (test?.status === 'passed') return '✓ PASS';
    if (test?.status === 'failed') return '✗ FAIL';
    return '○ PEND';
  };

  const healthStatus = getTestStatus('/health');
  const registryStatus = getTestStatus('registry');
  const serversStatus = getTestStatus('servers');
  const profilesStatus = getTestStatus('profiles');
  const discoveryStatus = getTestStatus('Discovery');

  const overallStatus = runTests.isPending
    ? '⚡ TESTING...'
    : testResults
      ? `✓ ${testResults.passed}/${testResults.total} PASSED`
      : '○ READY     ';

  const header = '─ API ENDPOINT TEST MAP ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('CLIENT ───[HTTP]───> FASTAPI ───> ROUTER ───> SERVICE', FRAME_WIDTH)}
${padLine('                        │', FRAME_WIDTH)}
${padLine(`                        ├─ /health ............. ${healthStatus}`, FRAME_WIDTH)}
${padLine('                        │', FRAME_WIDTH)}
${padLine(`                        ├─ /models/registry ... ${registryStatus}`, FRAME_WIDTH)}
${padLine('                        │', FRAME_WIDTH)}
${padLine(`                        ├─ /models/servers .... ${serversStatus}`, FRAME_WIDTH)}
${padLine('                        │', FRAME_WIDTH)}
${padLine(`                        ├─ /models/profiles ... ${profilesStatus}`, FRAME_WIDTH)}
${padLine('                        │', FRAME_WIDTH)}
${padLine(`                        └─ Discovery Service ... ${discoveryStatus}`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`STATUS: ${overallStatus}`, FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
        </pre>

        <div className={styles.testingSection}>
            <p className={styles.sectionDesc}>
              Test all API endpoints and verify system functionality.
              This runs a comprehensive test suite across all major endpoints.
            </p>

            <button
              className={styles.actionButton}
              onClick={() => runTests.mutate()}
              disabled={runTests.isPending}
            >
              {runTests.isPending ? 'TESTING...' : 'RUN TESTS'}
            </button>

            {testResults && (
              <div className={styles.testResults}>
                <div className={styles.testSummary}>
                  <span className={styles.testTotal}>Total: {testResults.total}</span>
                  <span className={styles.testPassed}>Passed: {testResults.passed}</span>
                  <span className={styles.testFailed}>Failed: {testResults.failed}</span>
                </div>

                <div className={styles.testList}>
                  {testResults.tests.map((test, idx) => (
                    <div key={idx} className={styles.testItem}>
                      <span className={`${styles.testIcon} ${getStatusColor(test.status)}`}>
                        {test.status === 'passed' ? '✅' : '❌'}
                      </span>
                      <div className={styles.testContent}>
                        <div className={styles.testEndpoint}>{test.endpoint}</div>
                        <div className={styles.testMessage}>{test.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
      </div>

      {/* Server Management */}
      <div className={styles.asciiPanel}>
        <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const servers = health?.components.servers?.servers as any[] | undefined;
  const q2State = servers?.find((s: any) => s.tier === 'Q2')?.state === 'running' ? '█████████' : '░░░░░░░░░';
  const q3State = servers?.find((s: any) => s.tier === 'Q3')?.state === 'running' ? '█████████' : '░░░░░░░░░';
  const q4State = servers?.find((s: any) => s.tier === 'Q4')?.state === 'running' ? '█████████' : '░░░░░░░░░';

  const q2Active = servers?.filter((s: any) => s.tier === 'Q2' && s.state === 'running').length ?? 0;
  const q3Active = servers?.filter((s: any) => s.tier === 'Q3' && s.state === 'running').length ?? 0;
  const q4Active = servers?.filter((s: any) => s.tier === 'Q4' && s.state === 'running').length ?? 0;

  const controlStatus = restartServers.isPending ? '⚡ RESTARTING' : stopServers.isPending ? '⚠ STOPPING ' : '◉ READY     ';

  const header = '─ SERVER RACK STATUS ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('┌────────────────┐  ┌────────────────┐  ┌────────────────┐', FRAME_WIDTH)}
${padLine('│  Q2 FAST       │  │  Q3 BALANCED   │  │  Q4 POWERFUL   │', FRAME_WIDTH)}
${padLine('│  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────────┐  │', FRAME_WIDTH)}
${padLine(`│  │ ${q2State} │  │  │  │ ${q3State} │  │  │  │ ${q4State} │  │`, FRAME_WIDTH)}
${padLine('│  └──────────┘  │  │  └──────────┘  │  │  └──────────┘  │', FRAME_WIDTH)}
${padLine('│  :8080-8082    │  │  :8090-8091    │  │  :8100         │', FRAME_WIDTH)}
${padLine(`│  [${q2Active} active]    │  │  [${q3Active} active]    │  │  [${q4Active} active]    │`, FRAME_WIDTH)}
${padLine('└────────────────┘  └────────────────┘  └────────────────┘', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`CONTROL PANEL: ${controlStatus}`, FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
        </pre>

        <div className={styles.serverSection}>
            <p className={styles.sectionDesc}>
              Control model servers. Use restart to reload configuration or stop to shut down all servers.
            </p>

            <div className={styles.serverButtons}>
              <button
                className={`${styles.actionButton} ${styles.warningButton}`}
                onClick={() => {
                  if (window.confirm('This will stop and restart all running servers. Continue?')) {
                    restartServers.mutate();
                  }
                }}
                disabled={restartServers.isPending}
              >
                {restartServers.isPending ? 'RESTARTING...' : 'RESTART ALL SERVERS'}
              </button>

              <button
                className={`${styles.actionButton} ${styles.dangerButton}`}
                onClick={() => {
                  if (window.confirm('This will stop all running servers. Continue?')) {
                    stopServers.mutate();
                  }
                }}
                disabled={stopServers.isPending}
              >
                {stopServers.isPending ? 'STOPPING...' : 'STOP ALL SERVERS'}
              </button>
            </div>

            {restartServers.isSuccess && (
              <div className={styles.resultBox}>
                <div className={styles.resultSuccess}>✅ Servers restarted successfully</div>
              </div>
            )}

            {stopServers.isSuccess && (
              <div className={styles.resultBox}>
                <div className={styles.resultSuccess}>✅ All servers stopped</div>
              </div>
            )}

            {(restartServers.isError || stopServers.isError) && (
              <div className={styles.resultBox}>
                <div className={styles.resultError}>
                  ❌ Operation failed: {((restartServers.error || stopServers.error) as any)?.response?.data?.detail?.message || ((restartServers.error || stopServers.error) as Error).message}
                </div>
              </div>
            )}
          </div>
      </div>

      {/* System Info */}
      <div className={styles.asciiPanel}>
        {systemInfo ? (
          <>
            <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const profileName = systemInfo.environment.profile.padEnd(10).substring(0, 10);
  const platformName = systemInfo.python.platform.slice(0, 10).padEnd(10);
  const servicesReady = Object.values(systemInfo.services).filter(Boolean).length;
  const servicesTotal = Object.keys(systemInfo.services).length;
  const systemStatus = Object.values(systemInfo.services).every(Boolean) ? 'OPERATIONAL' : 'DEGRADED    ';

  const header = '─ SYSTEM ARCHITECTURE ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('┌─────────────────────────────────────────────────────────┐', FRAME_WIDTH)}
${padLine('│  RUNTIME ENVIRONMENT                                    │', FRAME_WIDTH)}
${padLine('│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │', FRAME_WIDTH)}
${padLine('│  │ Profile:   │  │ Platform:  │  │ Services:  │        │', FRAME_WIDTH)}
${padLine(`│  │ ${profileName} │  │ ${platformName} │  │ ${servicesReady}/${servicesTotal} ready   │        │`, FRAME_WIDTH)}
${padLine('│  └────────────┘  └────────────┘  └────────────┘        │', FRAME_WIDTH)}
${padLine('└─────────────────────────────────────────────────────────┘', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine('DATA FLOW:', FRAME_WIDTH)}
${padLine('┌─────┐    ┌──────────┐    ┌────────┐    ┌─────────┐', FRAME_WIDTH)}
${padLine('│ API │───▶│  CGRAG   │───▶│ Models │───▶│ Results │', FRAME_WIDTH)}
${padLine('└─────┘    └──────────┘    └────────┘    └─────────┘', FRAME_WIDTH)}
${padLine('   ▲            │               │              │', FRAME_WIDTH)}
${padLine('   │            ▼               ▼              ▼', FRAME_WIDTH)}
${padLine('┌─────┐    ┌──────────┐    ┌────────┐    ┌─────────┐', FRAME_WIDTH)}
${padLine('│Redis│◀───│  FAISS   │◀───│ Events │◀───│  Cache  │', FRAME_WIDTH)}
${padLine('└─────┘    └──────────┘    └────────┘    └─────────┘', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${padLine(`STATUS: ALL SYSTEMS ${systemStatus}`, FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
            </pre>

            {/* System info sections - NO wrapper to allow edge-to-edge headers */}
            <div className={styles.asciiSection}>
              <div className={styles.asciiSectionHeader}>{`${'─ ENVIRONMENT '}${'─'.repeat(150)}`}</div>
                  <div className={styles.asciiSectionBody}>
                    <div className={styles.infoGrid}>
                      <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Profile:</span>
                        <span className={styles.infoValue}>{systemInfo.environment.profile}</span>
                      </div>
                      <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Scan Path:</span>
                        <span className={styles.infoValue}>{systemInfo.environment.scan_path}</span>
                      </div>
                      <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>llama-server:</span>
                        <span className={styles.infoValue}>{systemInfo.environment.llama_server_path}</span>
                      </div>
                    </div>
                  </div>
            </div>

            <div className={styles.asciiSection}>
              <div className={styles.asciiSectionHeader}>{`${'─ PYTHON RUNTIME '}${'─'.repeat(150)}`}</div>
                  <div className={styles.asciiSectionBody}>
                    <div className={styles.infoGrid}>
                      <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Platform:</span>
                        <span className={styles.infoValue}>{systemInfo.python.platform}</span>
                      </div>
                      <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Processor:</span>
                        <span className={styles.infoValue}>{systemInfo.python.processor || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
            </div>

            <div className={styles.asciiSection}>
              <div className={styles.asciiSectionHeader}>{`${'─ SERVICE STATUS '}${'─'.repeat(150)}`}</div>
                  <div className={styles.asciiSectionBody}>
                    <div className={styles.infoGrid}>
                      {Object.entries(systemInfo.services).map(([name, initialized]) => (
                        <div key={name} className={styles.infoItem}>
                          <span className={styles.infoLabel}>
                            {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                          </span>
                          <span className={`${styles.infoValue} ${initialized ? styles.statusHealthy : styles.statusError}`}>
                            {initialized ? 'INITIALIZED' : 'NOT INITIALIZED'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
            </div>
          </>
        ) : (
          <div className={styles.loading}>LOADING SYSTEM INFO...</div>
        )}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { Panel } from '../../components/terminal/Panel/Panel';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
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

export const AdminPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [testResults, setTestResults] = useState<TestResults | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<DiscoveryResult | null>(null);

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
      <Panel title="SYSTEM HEALTH" variant="accent">
        {healthLoading ? (
          <div className={styles.loading}>LOADING HEALTH STATUS...</div>
        ) : health ? (
          <div className={styles.healthContainer}>
            <div className={styles.healthHeader}>
              <span className={styles.healthLabel}>OVERALL STATUS:</span>
              <span className={`${styles.healthStatus} ${getStatusColor(health.status)}`}>
                {health.status.toUpperCase()}
              </span>
              <span className={styles.healthTime}>{formatTimestamp(health.timestamp)}</span>
            </div>

            <div className={styles.componentsGrid}>
              {Object.entries(health.components).map(([name, component]) => (
                <div key={name} className={styles.component}>
                  <div className={styles.componentHeader}>
                    <div className={styles.componentName}>{name.toUpperCase()}</div>
                    <div className={`${styles.componentStatus} ${getStatusColor(component.status)}`}>
                      {component.status.toUpperCase()}
                    </div>
                  </div>

                  {component.message && (
                    <div className={styles.componentMessage}>{component.message}</div>
                  )}

                  {component.models_count !== undefined && (
                    <div className={styles.componentDetails}>
                      <div>Models: {component.models_count}</div>
                      <div>Enabled: {component.enabled_count}</div>
                      {component.last_scan && (
                        <div className={styles.lastScan}>Last Scan: {formatTimestamp(component.last_scan)}</div>
                      )}
                    </div>
                  )}

                  {component.total !== undefined && component.ready !== undefined && (
                    <div className={styles.componentDetails}>
                      <div>Servers: {component.ready}/{component.total}</div>
                      {component.ready !== component.total && (
                        <div className={styles.statusWarning}>
                          {component.total - component.ready} server(s) not ready
                        </div>
                      )}
                    </div>
                  )}

                  {component.count !== undefined && (
                    <div className={styles.componentDetails}>
                      <div>Available Profiles: {component.count}</div>
                    </div>
                  )}

                  {component.scan_path !== undefined && (
                    <div className={styles.componentDetails}>
                      <div className={styles.scanPath}>Scan Path: {component.scan_path}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button
              className={styles.actionButton}
              onClick={() => refetchHealth()}
            >
              REFRESH HEALTH
            </button>
          </div>
        ) : (
          <div className={styles.error}>Failed to load health status</div>
        )}
      </Panel>

      {/* Discovery */}
      <Panel title="MODEL DISCOVERY" variant="default">
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
      </Panel>

      {/* API Testing */}
      <Panel title="API ENDPOINT TESTING" variant="default">
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
      </Panel>

      {/* Server Management */}
      <Panel title="SERVER MANAGEMENT" variant="default">
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
      </Panel>

      {/* System Info */}
      <Panel title="SYSTEM INFORMATION" variant="default">
        {systemInfo ? (
          <div className={styles.systemInfo}>
            <div className={styles.infoSection}>
              <h3 className={styles.infoTitle}>ENVIRONMENT</h3>
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

            <div className={styles.infoSection}>
              <h3 className={styles.infoTitle}>PYTHON</h3>
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

            <div className={styles.infoSection}>
              <h3 className={styles.infoTitle}>SERVICES</h3>
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
        ) : (
          <div className={styles.loading}>LOADING SYSTEM INFO...</div>
        )}
      </Panel>
    </div>
  );
};

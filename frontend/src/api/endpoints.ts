// Endpoints are relative paths - axios client.ts will prepend baseURL
export const endpoints = {
  models: {
    status: 'models/status',
    detail: (name: string) => `models/${name}`,
  },
  query: {
    execute: 'query',
    history: 'query/history',
    byId: (id: string) => `query/${id}`,
  },
  metrics: {
    system: 'metrics/system',
    models: 'metrics/models',
  },
  settings: {
    get: 'settings',
    update: 'settings',
    reset: 'settings/reset',
    schema: 'settings/schema',
    vramEstimate: 'settings/vram-estimate',
    export: 'settings/export',
    import: 'settings/import',
    validate: 'settings/validate',
  },
  admin: {
    restartServers: 'admin/servers/restart',
    stopServers: 'admin/servers/stop',
    externalServersStatus: 'admin/external-servers/status',
  },
} as const;

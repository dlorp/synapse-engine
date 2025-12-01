# CGRAG Infrastructure Quick Reference

**Version:** 1.0 | **Updated:** 2025-11-30

---

## Quick Start Commands

```bash
# Start monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Check health
./scripts/check-cgrag-health.sh --verbose

# Run backup
./scripts/backup-cgrag-indexes.sh

# View logs
docker-compose logs -f prometheus grafana
```

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | None |
| **Qdrant UI** | http://localhost:6333/dashboard | None |
| **Redis Exporter** | http://localhost:9121/metrics | None |
| **Backend Metrics** | http://localhost:8000/metrics | None |

---

## Key Configuration Files

```bash
# Environment
.env.cgrag.example              # CGRAG settings template

# Docker
docker-compose.monitoring.yml   # Monitoring services

# Prometheus
config/prometheus/prometheus.yml          # Main config
config/prometheus/rules/cgrag_alerts.yml  # Alert rules

# Grafana
config/grafana/provisioning/datasources/prometheus.yml  # Datasource
config/grafana/dashboards/cgrag/cgrag_overview.json    # Dashboard

# Scripts
scripts/backup-cgrag-indexes.sh           # Backup automation
scripts/check-cgrag-health.sh             # Health checks
```

---

## Critical Environment Variables

```bash
# Vector Database
RECALL_VECTOR_DB=auto                      # auto|qdrant|faiss
RECALL_QDRANT_URL=http://synapse_qdrant:6333

# Hybrid Search
RECALL_HYBRID_SEARCH=true
RECALL_HYBRID_ALPHA=0.7                    # 0.0=BM25, 1.0=Vector

# Reranker
RECALL_RERANKER_ENABLED=true
RECALL_RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Knowledge Graph
RECALL_KG_ENABLED=true
RECALL_KG_ENTITY_EXTRACTION=spacy

# Performance
RECALL_TOKEN_BUDGET=8000
RECALL_MIN_RELEVANCE=0.7
RECALL_EMBEDDING_CACHE=true

# Monitoring
PROMETHEUS_ENABLED=true
```

---

## Performance Targets

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Retrieval Latency (p95) | <100ms | >100ms (warn), >200ms (critical) |
| Cache Hit Rate | >70% | <70% (warn) |
| Embedding Generation | <50ms | >50ms (warn) |
| Reranker Latency | <300ms | >300ms (warn) |
| Memory Usage | <80% | >80% (warn) |

---

## Common Operations

### Start/Stop Services

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Stop all services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Restart specific service
docker-compose restart prometheus

# View service status
docker-compose ps
```

### Backup Operations

```bash
# Manual backup
./scripts/backup-cgrag-indexes.sh

# Backup with 7-day retention
./scripts/backup-cgrag-indexes.sh --retention 7

# Backup to S3
./scripts/backup-cgrag-indexes.sh --s3-upload

# Verify existing backups
./scripts/backup-cgrag-indexes.sh --verify-only

# List backups
ls -lh /path/to/backups/cgrag/
```

### Health Checks

```bash
# Text output
./scripts/check-cgrag-health.sh --verbose

# JSON output
./scripts/check-cgrag-health.sh --json

# Prometheus metrics
./scripts/check-cgrag-health.sh --prometheus

# With alerting
./scripts/check-cgrag-health.sh --alert-webhook https://hooks.slack.com/...
```

### Log Inspection

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f prometheus

# Last 100 lines
docker-compose logs --tail=100 grafana

# Filter by timestamp
docker-compose logs --since 2025-11-30T10:00:00
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service>

# Check resources
docker stats

# Verify volumes
docker volume ls | grep synapse

# Recreate service
docker-compose up -d --force-recreate <service>
```

### No Metrics in Prometheus

```bash
# Check backend /metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# View Prometheus logs
docker-compose logs prometheus | grep error
```

### Grafana Shows No Data

```bash
# Test Prometheus datasource
curl http://localhost:3000/api/datasources/1/health

# Check time range (ensure data exists in that range)
# Default: Last 15 minutes

# Verify metrics exist
curl http://localhost:9090/api/v1/query?query=cgrag_retrieval_latency_seconds

# Check Grafana logs
docker-compose logs grafana | grep error
```

### High Retrieval Latency

```bash
# Check index size
du -sh backend/data/faiss_indexes/

# Optimize FAISS index
docker-compose exec synapse_core python -m app.cli.optimize_cgrag_index

# Check system resources
docker stats synapse_core

# Review slow queries in Grafana
# Dashboard → CGRAG Overview → Top Slow Queries
```

### Low Cache Hit Rate

```bash
# Check Redis memory
docker exec synapse_redis redis-cli -a <password> INFO MEMORY

# Increase cache TTL
# Edit .env.cgrag: RECALL_EMBEDDING_CACHE_TTL=172800

# Increase Redis memory
# Edit docker-compose.yml: --maxmemory 512mb

# Review query patterns
docker-compose logs synapse_core | grep "CGRAG query"
```

---

## Backup & Recovery

### Quick Backup

```bash
./scripts/backup-cgrag-indexes.sh
```

### Quick Recovery

```bash
# 1. Stop services
docker-compose down

# 2. Extract backup
cd /path/to/backups/cgrag/20251130_020000
tar -xzf faiss.tar.gz -C /tmp/restore/

# 3. Copy to data directory
cp -r /tmp/restore/faiss/* /path/to/backend/data/faiss_indexes/

# 4. Restart services
docker-compose up -d

# 5. Verify health
./scripts/check-cgrag-health.sh --verbose
```

---

## Monitoring Dashboards

### CGRAG Performance Overview

**URL:** http://localhost:3000/d/cgrag-overview

**Panels:**
1. Retrieval Latency (p95, p99) - Target: <100ms
2. Cache Hit Rate - Target: >70%
3. Current Cache Hit Rate - Gauge
4. Avg Retrieval Latency - Gauge
5. Query Rate - Requests/sec
6. Index Size - Total storage
7. Embedding Generation Time
8. Hybrid Search Components
9. Reranker Performance
10. Knowledge Graph Metrics
11. Top Slow Queries

---

## Alert Summary

### Critical (Immediate Action)

- Retrieval latency >200ms (p95)
- Backend API down
- Redis connectivity lost
- Reranker errors >0.1/sec

### Warning (Attention Needed)

- Retrieval latency >100ms (p95)
- Cache hit rate <70%
- Embedding generation >50ms
- Reranker latency >300ms

### Info (Tracking)

- Index size >5GB
- High query volume >100/sec
- Knowledge graph stale >24h

---

## Prometheus Queries

```promql
# Retrieval latency (p95)
histogram_quantile(0.95, rate(cgrag_retrieval_latency_seconds_bucket[5m]))

# Cache hit rate
rate(cgrag_cache_hit_total[5m]) / (rate(cgrag_cache_hit_total[5m]) + rate(cgrag_cache_miss_total[5m]))

# Query rate
rate(cgrag_retrieval_total[5m])

# Embedding generation time (p95)
histogram_quantile(0.95, rate(cgrag_embedding_generation_seconds_bucket[5m]))

# Reranker latency (p95)
histogram_quantile(0.95, rate(cgrag_reranker_latency_seconds_bucket[5m]))

# Knowledge graph size
cgrag_knowledge_graph_nodes
cgrag_knowledge_graph_edges
```

---

## Cron Schedule Templates

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup-cgrag-indexes.sh --retention 7 >> /var/log/synapse/backup.log 2>&1

# Weekly S3 upload (Sunday 3 AM)
0 3 * * 0 /path/to/scripts/backup-cgrag-indexes.sh --retention 30 --s3-upload >> /var/log/synapse/backup.log 2>&1

# Health check every 5 minutes
*/5 * * * * /path/to/scripts/check-cgrag-health.sh --json >> /var/log/synapse/health.log 2>&1

# Prometheus metrics cleanup (monthly)
0 0 1 * * docker exec synapse_prometheus promtool tsdb clean /prometheus
```

---

## Resource Requirements

| Component | RAM | CPU | Disk |
|-----------|-----|-----|------|
| Qdrant | 2-3GB | 2 cores | 5-10GB |
| Prometheus | 1-2GB | 0.5-1 cores | 10-15GB |
| Grafana | 256-512MB | 0.25-0.5 cores | 1GB |
| Redis Exporter | 64-128MB | 0.1 cores | <100MB |
| **Total** | **4-6GB** | **3-4 cores** | **15-25GB** |

---

## Documentation Links

- [Deployment Guide](./CGRAG_INFRASTRUCTURE_DEPLOYMENT.md)
- [Enhancement Plan](./plans/CGRAG_ENHANCEMENT_PLAN.md)
- [Implementation Summary](../CGRAG_INFRASTRUCTURE_SUMMARY.md)
- [Session Notes](../SESSION_NOTES.md)

---

## Support

**Issues:** File in GitHub repository
**Questions:** Contact DevOps team
**Urgent:** Page on-call engineer

---

**Last Updated:** 2025-11-30 | **Version:** 1.0

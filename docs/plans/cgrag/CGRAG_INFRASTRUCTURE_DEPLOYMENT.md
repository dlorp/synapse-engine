# CGRAG Infrastructure Deployment Guide

**Date:** 2025-11-30
**Status:** Ready for Implementation
**Author:** DevOps Engineer

---

## Overview

This guide covers deploying the enhanced CGRAG infrastructure stack with monitoring, backups, and health checks for the S.Y.N.A.P.S.E. ENGINE project.

### Infrastructure Components

| Component | Purpose | Resource Requirements |
|-----------|---------|---------------------|
| **Qdrant** | Vector database (optional) | 2-3GB RAM, 2 CPU cores |
| **Prometheus** | Metrics collection | 1-2GB RAM, 0.5-1 CPU core |
| **Grafana** | Metrics visualization | 256-512MB RAM, 0.25-0.5 CPU core |
| **Redis Exporter** | Redis metrics | 64-128MB RAM, 0.1 CPU core |
| **FAISS** | Fallback vector database | In-process (synapse_core) |

### Total Additional Resources

- **Memory:** ~4-6GB
- **CPU:** ~3-4 cores
- **Disk:** ~15-20GB (metrics retention: 30 days)

---

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start all services including monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# View logs
docker-compose logs -f prometheus grafana
```

### 2. Access Dashboards

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Qdrant UI:** http://localhost:6333/dashboard (if enabled)

### 3. Verify Health

```bash
# Run comprehensive health check
./scripts/check-cgrag-health.sh --verbose

# Expected output:
# backend_api          PASS HTTP 200 (45ms)
# cgrag_endpoint       PASS Status: healthy
# faiss_indexes        PASS 3 index(es), 1.2G
# redis_connectivity   PASS PING successful
# retrieval_latency    PASS 67ms
```

---

## Detailed Deployment Steps

### Step 1: Prepare Configuration Files

#### 1.1 Copy Environment Variables

```bash
# Copy CGRAG environment configuration
cp .env.cgrag.example .env.cgrag

# Edit configuration
vim .env.cgrag

# Key variables to customize:
# - RECALL_VECTOR_DB (auto|qdrant|faiss)
# - RECALL_HYBRID_SEARCH (true|false)
# - RECALL_RERANKER_ENABLED (true|false)
# - RECALL_KG_ENABLED (true|false)
```

#### 1.2 Verify Docker Volumes

```bash
# Create Redis data volume if not exists
docker volume create synapse_redis_data

# Create Qdrant data volume (if using Qdrant)
docker volume create synapse_qdrant_data

# Verify volumes
docker volume ls | grep synapse
```

#### 1.3 Check Resource Availability

```bash
# Check available memory
free -h

# Check available disk space
df -h

# Ensure at least:
# - 6GB free RAM
# - 20GB free disk space
```

### Step 2: Deploy Services

#### 2.1 Start Core Services (Without Monitoring)

```bash
# Start base services first
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Expected output:
# synapse_core      healthy
# synapse_redis     healthy
# synapse_recall    healthy
# synapse_frontend  healthy
```

#### 2.2 Start Monitoring Stack

```bash
# Start monitoring extension
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# View startup logs
docker-compose logs -f prometheus grafana qdrant

# Wait for healthy status (30-60s)
docker-compose ps prometheus grafana
```

#### 2.3 Verify Service Health

```bash
# Check all services
docker-compose ps

# Test Prometheus scraping
curl http://localhost:9090/-/healthy

# Test Grafana
curl http://localhost:3000/api/health

# Test Qdrant (if enabled)
curl http://localhost:6333/
```

### Step 3: Configure Monitoring

#### 3.1 Access Grafana

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Change password (recommended)
4. Navigate to **Dashboards** → **CGRAG** → **CGRAG Performance Overview**

#### 3.2 Verify Data Sources

1. Navigate to **Configuration** → **Data Sources**
2. Verify **Prometheus** is connected (green)
3. Click **Test** to verify connectivity

#### 3.3 Review Dashboards

Pre-configured dashboards:

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| **CGRAG Performance Overview** | Primary monitoring | Latency, cache hit rate, query rate |
| **Retrieval Metrics** | Detailed retrieval stats | Embedding time, hybrid search breakdown |
| **Cache Performance** | Redis cache analysis | Hit rate, memory usage, evictions |
| **System Resources** | Resource utilization | CPU, memory, disk I/O |

### Step 4: Configure Alerting

#### 4.1 Review Alert Rules

```bash
# View CGRAG alert rules
cat config/prometheus/rules/cgrag_alerts.yml

# Key alerts:
# - Retrieval latency >100ms (p95)
# - Cache hit rate <70%
# - Reranker errors
# - Knowledge graph query latency
```

#### 4.2 Configure Alert Notifications (Optional)

Edit `config/prometheus/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

Create `config/alertmanager/alertmanager.yml`:

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'slack-notifications'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#synapse-alerts'
        title: 'CGRAG Alert'
        text: '{{ .CommonAnnotations.description }}'
```

### Step 5: Setup Backup Automation

#### 5.1 Test Manual Backup

```bash
# Run manual backup
./scripts/backup-cgrag-indexes.sh --verbose

# Expected output:
# [INFO] Created backup directory: /path/to/backups/cgrag/20251130_143025
# [INFO] Found 3 FAISS index(es)
# [INFO] FAISS backup complete: 1.2G
# [INFO] Qdrant backup complete: 850M
# [INFO] Redis backup complete: 45M
# [INFO] Backup verification successful
```

#### 5.2 Configure Automated Backups

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/scripts/backup-cgrag-indexes.sh --retention 7 >> /var/log/synapse/cgrag-backup.log 2>&1

# Add weekly backup on Sunday at 3 AM with S3 upload
0 3 * * 0 /path/to/scripts/backup-cgrag-indexes.sh --retention 30 --s3-upload >> /var/log/synapse/cgrag-backup.log 2>&1
```

#### 5.3 Configure S3 Upload (Optional)

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
apt-get install awscli  # Linux

# Configure AWS credentials
aws configure

# Set S3 bucket in environment
export S3_BUCKET=synapse-backups
export S3_PREFIX=cgrag-indexes

# Test S3 upload
./scripts/backup-cgrag-indexes.sh --s3-upload --verbose
```

### Step 6: Configure Health Checks

#### 6.1 Test Health Check Script

```bash
# Run health check
./scripts/check-cgrag-health.sh --verbose

# Review output for any failures
# All checks should show PASS or SKIP
```

#### 6.2 Schedule Periodic Health Checks

```bash
# Add to crontab for every 5 minutes
*/5 * * * * /path/to/scripts/check-cgrag-health.sh --json >> /var/log/synapse/cgrag-health.log 2>&1

# Add health check with alerting (every 15 minutes)
*/15 * * * * /path/to/scripts/check-cgrag-health.sh --alert-webhook https://hooks.slack.com/... >> /var/log/synapse/cgrag-health.log 2>&1
```

#### 6.3 Integrate with Docker Healthcheck

Add to `docker-compose.yml`:

```yaml
services:
  synapse_core:
    healthcheck:
      test: ["/scripts/check-cgrag-health.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

---

## Performance Tuning

### Qdrant Optimization

#### For <100k Documents

```yaml
# docker-compose.monitoring.yml
environment:
  - QDRANT__STORAGE__OPTIMIZERS__DEFAULT_SEGMENT_NUMBER=2
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
```

#### For 100k-1M Documents

```yaml
environment:
  - QDRANT__STORAGE__OPTIMIZERS__DEFAULT_SEGMENT_NUMBER=8
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=8
```

#### For >1M Documents

```yaml
environment:
  - QDRANT__STORAGE__OPTIMIZERS__DEFAULT_SEGMENT_NUMBER=16
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=16
```

### Prometheus Optimization

#### Reduce Scrape Frequency (Lower Load)

```yaml
# config/prometheus/prometheus.yml
global:
  scrape_interval: 30s  # Increase from 15s
```

#### Increase Retention (Longer History)

```yaml
# docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=90d'  # Increase from 30d
  - '--storage.tsdb.retention.size=50GB'  # Increase from 10GB
```

### Redis Optimization

#### Increase Memory Limit

```yaml
# docker-compose.yml
services:
  synapse_redis:
    command: >
      redis-server
      --maxmemory 512mb  # Increase from 256mb
```

#### Tune Eviction Policy

```yaml
command: >
  redis-server
  --maxmemory-policy allkeys-lfu  # Change from allkeys-lru
```

---

## Monitoring Best Practices

### Key Metrics to Watch

| Metric | Target | Action if Outside Range |
|--------|--------|------------------------|
| **Retrieval Latency (p95)** | <100ms | Check FAISS/Qdrant load, optimize indexes |
| **Cache Hit Rate** | >70% | Increase cache TTL, review query patterns |
| **Embedding Generation** | <50ms | Check CPU load, consider GPU acceleration |
| **Reranker Latency** | <300ms | Reduce batch size, use smaller model |
| **Memory Usage** | <80% | Scale resources, optimize chunk sizes |

### Grafana Dashboard Layout

**Top Row (High-Level KPIs)**
- Current cache hit rate (gauge)
- Avg retrieval latency p95 (gauge)
- Query rate (gauge)
- Index size (gauge)

**Second Row (Latency Trends)**
- Retrieval latency over time (graph)
- Cache hit rate over time (graph)

**Third Row (Component Breakdown)**
- Embedding generation time (graph)
- Hybrid search components (graph)

**Fourth Row (Advanced Metrics)**
- Reranker performance (graph)
- Knowledge graph metrics (graph)

**Bottom Row (Detailed Analysis)**
- Top slow queries (table)

### Alert Configuration

**Critical Alerts** (Immediate Action)
- Retrieval latency >200ms (p95)
- Backend API down
- Redis connectivity lost
- Reranker errors >0.1/sec

**Warning Alerts** (Attention Needed)
- Retrieval latency >100ms (p95)
- Cache hit rate <70%
- Embedding generation >50ms
- Memory usage >80%

**Info Alerts** (Tracking)
- Index size >5GB
- High query volume (>100/sec)
- Knowledge graph stale (>24h)

---

## Backup and Recovery

### Backup Strategy

**Daily Backups**
```bash
# Keep 7 days locally
./scripts/backup-cgrag-indexes.sh --retention 7
```

**Weekly Backups**
```bash
# Keep 30 days, upload to S3
./scripts/backup-cgrag-indexes.sh --retention 30 --s3-upload
```

**Monthly Backups**
```bash
# Keep 365 days, upload to S3 with Glacier lifecycle
./scripts/backup-cgrag-indexes.sh --retention 365 --s3-upload
```

### Recovery Procedure

#### 1. Stop Services

```bash
docker-compose down
```

#### 2. List Available Backups

```bash
ls -lh /path/to/backups/cgrag/

# Output:
# 20251130_020000/  (most recent)
# 20251129_020000/
# 20251128_020000/
```

#### 3. Verify Backup Integrity

```bash
# Navigate to backup directory
cd /path/to/backups/cgrag/20251130_020000

# Verify checksums
sha256sum -c checksums.sha256

# Expected output:
# faiss.tar.gz: OK
# qdrant.tar.gz: OK
# redis/dump.rdb.gz: OK
```

#### 4. Restore FAISS Indexes

```bash
# Extract FAISS backup
tar -xzf faiss.tar.gz -C /tmp/restore/

# Copy to data directory
cp -r /tmp/restore/faiss/* /path/to/backend/data/faiss_indexes/

# Verify files
ls -lh /path/to/backend/data/faiss_indexes/
```

#### 5. Restore Qdrant (if using)

```bash
# Extract Qdrant backup
tar -xzf qdrant.tar.gz -C /tmp/restore/

# Copy to volume
docker run --rm \
  -v synapse_qdrant_data:/target \
  -v /tmp/restore/qdrant:/source:ro \
  alpine:latest \
  sh -c "cp -r /source/* /target/"
```

#### 6. Restore Redis Cache

```bash
# Extract Redis backup
gunzip -c redis/dump.rdb.gz > /tmp/restore/dump.rdb

# Copy to volume
docker run --rm \
  -v synapse_redis_data:/target \
  -v /tmp/restore:/source:ro \
  alpine:latest \
  sh -c "cp /source/dump.rdb /target/"
```

#### 7. Restart Services

```bash
# Start services
docker-compose up -d

# Wait for healthy status
docker-compose ps

# Verify health
./scripts/check-cgrag-health.sh --verbose
```

#### 8. Verify Recovery

```bash
# Test CGRAG retrieval
curl -X POST http://localhost:8000/api/cgrag/test-query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'

# Check index count
curl http://localhost:8000/api/cgrag/stats | jq '.indexes'

# Expected: Same number of indexes as before
```

---

## Troubleshooting

### Problem: Qdrant Container Won't Start

**Symptoms:**
```bash
docker-compose logs qdrant
# Error: Failed to open database
```

**Solutions:**

1. Check volume permissions:
```bash
docker volume inspect synapse_qdrant_data
```

2. Increase memory allocation:
```yaml
# docker-compose.monitoring.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 3G
```

3. Clear corrupted volume:
```bash
docker-compose down
docker volume rm synapse_qdrant_data
docker volume create synapse_qdrant_data
docker-compose up -d
```

### Problem: Prometheus Not Scraping Metrics

**Symptoms:**
```bash
# Prometheus UI shows targets as DOWN
```

**Solutions:**

1. Verify backend /metrics endpoint:
```bash
curl http://localhost:8000/metrics

# Should return Prometheus-format metrics
```

2. Check Prometheus logs:
```bash
docker-compose logs prometheus | grep error
```

3. Verify network connectivity:
```bash
docker exec synapse_prometheus ping synapse_core
```

4. Reload Prometheus config:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Problem: Grafana Shows No Data

**Symptoms:**
```bash
# Dashboards are empty or show "No data"
```

**Solutions:**

1. Verify Prometheus data source:
```bash
# Grafana UI → Configuration → Data Sources → Prometheus
# Click "Test" - should show "Data source is working"
```

2. Check time range:
```bash
# Ensure dashboard time range matches data availability
# Default: Last 15 minutes
```

3. Verify metrics exist in Prometheus:
```bash
# Prometheus UI → Graph
# Query: cgrag_retrieval_latency_seconds
# Should show data
```

4. Check Prometheus retention:
```bash
docker exec synapse_prometheus \
  promtool tsdb analyze /prometheus
```

### Problem: High Retrieval Latency

**Symptoms:**
```bash
./scripts/check-cgrag-health.sh
# retrieval_latency    WARN 250ms (threshold: 100ms)
```

**Solutions:**

1. Check index size:
```bash
du -sh /path/to/backend/data/faiss_indexes/

# If >5GB, consider optimization
```

2. Optimize FAISS index:
```python
# Run index optimization
python -m app.cli.optimize_cgrag_index
```

3. Enable Qdrant for faster search:
```bash
# .env.cgrag
RECALL_VECTOR_DB=qdrant
```

4. Reduce reranker batch size:
```bash
# .env.cgrag
RECALL_RERANKER_BATCH_SIZE=16  # Reduce from 32
```

5. Check system resources:
```bash
docker stats synapse_core

# If CPU >80%, increase allocation
```

### Problem: Low Cache Hit Rate

**Symptoms:**
```bash
# Grafana shows cache hit rate <70%
```

**Solutions:**

1. Increase cache TTL:
```bash
# .env.cgrag
RECALL_EMBEDDING_CACHE_TTL=172800  # 48 hours (from 24)
```

2. Increase Redis memory:
```yaml
# docker-compose.yml
command: >
  redis-server
  --maxmemory 512mb  # Increase from 256mb
```

3. Review query patterns:
```bash
# Check query diversity in logs
docker-compose logs synapse_core | grep "CGRAG query"
```

4. Enable query result caching:
```bash
# .env.cgrag
RECALL_QUERY_CACHE_TTL=600  # 10 minutes
```

---

## Production Checklist

### Pre-Deployment

- [ ] Review resource requirements (6GB RAM, 4 CPUs)
- [ ] Configure environment variables (.env.cgrag)
- [ ] Set strong passwords (Grafana, Redis)
- [ ] Plan disk space for metrics retention (20GB)
- [ ] Configure backup storage (local + S3)
- [ ] Set up alert notifications (Slack, email)

### Deployment

- [ ] Start core services and verify health
- [ ] Start monitoring stack and verify connectivity
- [ ] Access Grafana and review dashboards
- [ ] Configure alert rules and test notifications
- [ ] Run initial backup and verify integrity
- [ ] Schedule automated backups (cron)
- [ ] Schedule health checks (cron)

### Post-Deployment

- [ ] Monitor metrics for 24 hours
- [ ] Tune alert thresholds based on baseline
- [ ] Review backup logs daily for first week
- [ ] Test recovery procedure in non-production environment
- [ ] Document any environment-specific configurations
- [ ] Train team on Grafana dashboards and alerts
- [ ] Establish runbooks for common issues

### Security

- [ ] Change default Grafana password
- [ ] Use strong Redis password
- [ ] Enable HTTPS for Grafana (reverse proxy)
- [ ] Restrict Prometheus/Grafana to internal network
- [ ] Encrypt backups if storing offsite
- [ ] Review Docker security (non-root users)
- [ ] Enable audit logging for admin actions

---

## Next Steps

1. **Implement Backend Metrics Instrumentation**
   - Add Prometheus client to `backend/requirements.txt`
   - Instrument CGRAG service with metrics
   - See: [CGRAG_ENHANCEMENT_PLAN.md](./plans/CGRAG_ENHANCEMENT_PLAN.md)

2. **Test in Development**
   - Deploy monitoring stack locally
   - Generate sample load for metrics
   - Verify dashboards show data
   - Test backup/restore procedure

3. **Optimize for Production**
   - Tune resource allocations
   - Set appropriate retention policies
   - Configure external alerting
   - Implement log aggregation

4. **Documentation**
   - Create runbooks for common incidents
   - Document backup/restore procedures
   - Train team on monitoring tools
   - Establish on-call rotation

---

## Additional Resources

### Documentation
- [CGRAG Enhancement Plan](./plans/CGRAG_ENHANCEMENT_PLAN.md)
- [SESSION_NOTES.md](../SESSION_NOTES.md)
- [docker-compose.monitoring.yml](../docker-compose.monitoring.yml)

### Configuration Files
- [prometheus.yml](../config/prometheus/prometheus.yml)
- [cgrag_alerts.yml](../config/prometheus/rules/cgrag_alerts.yml)
- [.env.cgrag.example](../.env.cgrag.example)

### Scripts
- [backup-cgrag-indexes.sh](../scripts/backup-cgrag-indexes.sh)
- [check-cgrag-health.sh](../scripts/check-cgrag-health.sh)

### External Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Redis Documentation](https://redis.io/documentation)

---

**Last Updated:** 2025-11-30
**Maintained By:** DevOps Team

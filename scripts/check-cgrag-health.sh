#!/usr/bin/env bash
# =============================================================================
# CGRAG Health Check Script
# =============================================================================
# Comprehensive health monitoring for CGRAG system components
#
# Checks:
# - FAISS/Qdrant index availability and integrity
# - Redis cache connectivity and memory usage
# - Reranker model availability
# - Embedding model load status
# - Knowledge graph database connectivity
# - API endpoint responsiveness
# - Metrics exposition
#
# Exit Codes:
#   0 - All checks passed (healthy)
#   1 - One or more checks failed (unhealthy)
#   2 - Critical failure (immediate action required)
#
# Usage:
#   ./scripts/check-cgrag-health.sh [OPTIONS]
#
# Options:
#   --verbose         Show detailed output
#   --json            Output results as JSON
#   --prometheus      Output Prometheus metrics
#   --alert-webhook   Webhook URL for alerts (Slack, Discord, etc.)
#
# Examples:
#   # Basic health check
#   ./scripts/check-cgrag-health.sh
#
#   # Verbose output for debugging
#   ./scripts/check-cgrag-health.sh --verbose
#
#   # JSON output for monitoring systems
#   ./scripts/check-cgrag-health.sh --json
#
#   # Health check with alerting
#   ./scripts/check-cgrag-health.sh --alert-webhook https://hooks.slack.com/...
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# API endpoints
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${MEMEX_PASSWORD:-change_this_secure_redis_password}"

# Timeouts (seconds)
HTTP_TIMEOUT="${HTTP_TIMEOUT:-10}"
REDIS_TIMEOUT="${REDIS_TIMEOUT:-5}"

# Thresholds
LATENCY_THRESHOLD_MS="${LATENCY_THRESHOLD_MS:-100}"
CACHE_HIT_RATE_THRESHOLD="${CACHE_HIT_RATE_THRESHOLD:-0.7}"
MEMORY_THRESHOLD_PCT="${MEMORY_THRESHOLD_PCT:-80}"

# Output format
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
VERBOSE="${VERBOSE:-false}"

# Alert webhook
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

# Check results
declare -A CHECK_RESULTS
declare -A CHECK_DETAILS
OVERALL_STATUS="healthy"
CRITICAL_FAILURES=0

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose)
      VERBOSE=true
      shift
      ;;
    --json)
      OUTPUT_FORMAT="json"
      shift
      ;;
    --prometheus)
      OUTPUT_FORMAT="prometheus"
      shift
      ;;
    --alert-webhook)
      ALERT_WEBHOOK="$2"
      shift 2
      ;;
    -h|--help)
      grep '^#' "$0" | grep -v '#!/usr/bin/env' | sed 's/^# //' | sed 's/^#//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

log_verbose() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "[VERBOSE] $*" >&2
  fi
}

log_error() {
  echo "[ERROR] $*" >&2
}

record_check() {
  local check_name="$1"
  local status="$2"
  local details="${3:-}"

  CHECK_RESULTS["$check_name"]="$status"
  CHECK_DETAILS["$check_name"]="$details"

  if [[ "$status" == "fail" ]]; then
    OVERALL_STATUS="unhealthy"
  fi

  if [[ "$status" == "critical" ]]; then
    OVERALL_STATUS="critical"
    ((CRITICAL_FAILURES++))
  fi

  if [[ "$VERBOSE" == "true" ]]; then
    echo "[$check_name] $status - $details"
  fi
}

# -----------------------------------------------------------------------------
# Health Check Functions
# -----------------------------------------------------------------------------

check_backend_api() {
  log_verbose "Checking backend API..."

  local start_time
  start_time=$(date +%s%3N)

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "$HTTP_TIMEOUT" \
    "$BACKEND_URL/health/healthz" || echo "000")

  local end_time
  end_time=$(date +%s%3N)
  local latency=$((end_time - start_time))

  if [[ "$http_code" == "200" ]]; then
    record_check "backend_api" "pass" "HTTP 200 (${latency}ms)"
  else
    record_check "backend_api" "critical" "HTTP $http_code"
  fi
}

check_cgrag_endpoint() {
  log_verbose "Checking CGRAG endpoint..."

  local response
  response=$(curl -s --max-time "$HTTP_TIMEOUT" \
    "$BACKEND_URL/api/cgrag/health" || echo "{\"error\": true}")

  local status
  status=$(echo "$response" | jq -r '.status // "unknown"')

  if [[ "$status" == "healthy" ]]; then
    record_check "cgrag_endpoint" "pass" "Status: $status"
  else
    record_check "cgrag_endpoint" "fail" "Status: $status"
  fi
}

check_faiss_indexes() {
  log_verbose "Checking FAISS indexes..."

  local faiss_dir="${FAISS_DIR:-${PROJECT_DIR}/backend/data/faiss_indexes}"

  if [[ ! -d "$faiss_dir" ]]; then
    record_check "faiss_indexes" "fail" "Directory not found: $faiss_dir"
    return
  fi

  local index_count
  index_count=$(find "$faiss_dir" -name "*.index" | wc -l | tr -d ' ')

  if [[ $index_count -gt 0 ]]; then
    local total_size
    total_size=$(du -sh "$faiss_dir" | cut -f1)
    record_check "faiss_indexes" "pass" "$index_count index(es), $total_size"
  else
    record_check "faiss_indexes" "fail" "No indexes found"
  fi
}

check_qdrant() {
  log_verbose "Checking Qdrant..."

  # Check if Qdrant is enabled/running
  if ! docker ps --format '{{.Names}}' | grep -q synapse_qdrant 2>/dev/null; then
    record_check "qdrant" "skip" "Container not running (using FAISS fallback)"
    return
  fi

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "$HTTP_TIMEOUT" \
    "$QDRANT_URL/" || echo "000")

  if [[ "$http_code" == "200" ]]; then
    # Get collection info
    local collections
    collections=$(curl -s --max-time "$HTTP_TIMEOUT" \
      "$QDRANT_URL/collections" | jq -r '.result.collections | length' || echo "0")

    record_check "qdrant" "pass" "HTTP 200, $collections collection(s)"
  else
    record_check "qdrant" "fail" "HTTP $http_code"
  fi
}

check_redis_connectivity() {
  log_verbose "Checking Redis connectivity..."

  # Check if docker command is available
  if ! command -v docker &>/dev/null; then
    record_check "redis_connectivity" "skip" "Docker not available"
    return
  fi

  # Check if Redis container is running
  if ! docker ps --format '{{.Names}}' | grep -q synapse_redis; then
    record_check "redis_connectivity" "critical" "Container not running"
    return
  fi

  # Test Redis connection with PING
  local pong
  pong=$(docker exec synapse_redis redis-cli -a "$REDIS_PASSWORD" PING 2>/dev/null || echo "ERROR")

  if [[ "$pong" == "PONG" ]]; then
    record_check "redis_connectivity" "pass" "PING successful"
  else
    record_check "redis_connectivity" "critical" "PING failed"
  fi
}

check_redis_memory() {
  log_verbose "Checking Redis memory usage..."

  if ! docker ps --format '{{.Names}}' | grep -q synapse_redis; then
    record_check "redis_memory" "skip" "Container not running"
    return
  fi

  # Get memory info
  local mem_info
  mem_info=$(docker exec synapse_redis redis-cli -a "$REDIS_PASSWORD" INFO MEMORY 2>/dev/null || echo "")

  if [[ -z "$mem_info" ]]; then
    record_check "redis_memory" "fail" "Failed to get memory info"
    return
  fi

  # Parse memory usage
  local used_memory
  used_memory=$(echo "$mem_info" | grep '^used_memory:' | cut -d: -f2 | tr -d '\r')

  local maxmemory
  maxmemory=$(echo "$mem_info" | grep '^maxmemory:' | cut -d: -f2 | tr -d '\r')

  # Calculate percentage if maxmemory is set
  if [[ "$maxmemory" != "0" ]]; then
    local usage_pct=$((used_memory * 100 / maxmemory))

    if [[ $usage_pct -lt $MEMORY_THRESHOLD_PCT ]]; then
      record_check "redis_memory" "pass" "${usage_pct}% used"
    else
      record_check "redis_memory" "fail" "${usage_pct}% used (threshold: ${MEMORY_THRESHOLD_PCT}%)"
    fi
  else
    # Convert to MB for display
    local used_mb=$((used_memory / 1024 / 1024))
    record_check "redis_memory" "pass" "${used_mb}MB used (no limit)"
  fi
}

check_embedding_cache() {
  log_verbose "Checking embedding cache..."

  if ! docker ps --format '{{.Names}}' | grep -q synapse_redis; then
    record_check "embedding_cache" "skip" "Redis not running"
    return
  fi

  # Count embedding cache keys
  local cache_keys
  cache_keys=$(docker exec synapse_redis redis-cli -a "$REDIS_PASSWORD" \
    KEYS "embedding:*" 2>/dev/null | wc -l | tr -d ' ')

  if [[ $cache_keys -gt 0 ]]; then
    record_check "embedding_cache" "pass" "$cache_keys cached embedding(s)"
  else
    record_check "embedding_cache" "warn" "No cached embeddings (cold start)"
  fi
}

check_reranker_model() {
  log_verbose "Checking reranker model..."

  # Query backend for reranker status
  local response
  response=$(curl -s --max-time "$HTTP_TIMEOUT" \
    "$BACKEND_URL/api/cgrag/reranker/status" 2>/dev/null || echo "{\"loaded\": false}")

  local loaded
  loaded=$(echo "$response" | jq -r '.loaded // false')

  if [[ "$loaded" == "true" ]]; then
    local model_name
    model_name=$(echo "$response" | jq -r '.model // "unknown"')
    record_check "reranker_model" "pass" "Loaded: $model_name"
  else
    record_check "reranker_model" "warn" "Not loaded (reranking disabled)"
  fi
}

check_knowledge_graph() {
  log_verbose "Checking knowledge graph..."

  # Query backend for KG status
  local response
  response=$(curl -s --max-time "$HTTP_TIMEOUT" \
    "$BACKEND_URL/api/cgrag/knowledge-graph/status" 2>/dev/null || echo "{\"enabled\": false}")

  local enabled
  enabled=$(echo "$response" | jq -r '.enabled // false')

  if [[ "$enabled" == "true" ]]; then
    local entity_count
    entity_count=$(echo "$response" | jq -r '.entities // 0')

    local edge_count
    edge_count=$(echo "$response" | jq -r '.edges // 0')

    record_check "knowledge_graph" "pass" "$entity_count entities, $edge_count edges"
  else
    record_check "knowledge_graph" "skip" "Not enabled"
  fi
}

check_retrieval_latency() {
  log_verbose "Checking retrieval latency..."

  # Perform test query
  local start_time
  start_time=$(date +%s%3N)

  local response
  response=$(curl -s --max-time "$HTTP_TIMEOUT" \
    -X POST "$BACKEND_URL/api/cgrag/test-query" \
    -H "Content-Type: application/json" \
    -d '{"query": "health check test query", "top_k": 5}' \
    2>/dev/null || echo "{\"error\": true}")

  local end_time
  end_time=$(date +%s%3N)
  local latency=$((end_time - start_time))

  if [[ $(echo "$response" | jq -r '.error // false') == "false" ]]; then
    if [[ $latency -lt $LATENCY_THRESHOLD_MS ]]; then
      record_check "retrieval_latency" "pass" "${latency}ms"
    else
      record_check "retrieval_latency" "warn" "${latency}ms (threshold: ${LATENCY_THRESHOLD_MS}ms)"
    fi
  else
    record_check "retrieval_latency" "fail" "Query failed"
  fi
}

check_prometheus_metrics() {
  log_verbose "Checking Prometheus metrics exposition..."

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "$HTTP_TIMEOUT" \
    "$BACKEND_URL/metrics" || echo "000")

  if [[ "$http_code" == "200" ]]; then
    # Count CGRAG metrics
    local metric_count
    metric_count=$(curl -s --max-time "$HTTP_TIMEOUT" "$BACKEND_URL/metrics" | \
      grep '^cgrag_' | wc -l | tr -d ' ')

    record_check "prometheus_metrics" "pass" "$metric_count CGRAG metric(s) exposed"
  else
    record_check "prometheus_metrics" "fail" "HTTP $http_code"
  fi
}

# -----------------------------------------------------------------------------
# Output Functions
# -----------------------------------------------------------------------------

output_text() {
  echo "========================================="
  echo "CGRAG Health Check Results"
  echo "========================================="
  echo "Overall Status: $OVERALL_STATUS"
  echo ""

  for check_name in "${!CHECK_RESULTS[@]}"; do
    local status="${CHECK_RESULTS[$check_name]}"
    local details="${CHECK_DETAILS[$check_name]}"

    # Color code status
    local status_display
    case "$status" in
      pass)
        status_display="\033[32mPASS\033[0m"
        ;;
      warn)
        status_display="\033[33mWARN\033[0m"
        ;;
      fail)
        status_display="\033[31mFAIL\033[0m"
        ;;
      critical)
        status_display="\033[31m\033[1mCRIT\033[0m"
        ;;
      skip)
        status_display="\033[90mSKIP\033[0m"
        ;;
      *)
        status_display="$status"
        ;;
    esac

    printf "%-25s %b %s\n" "$check_name" "$status_display" "$details"
  done

  echo ""
  echo "========================================="
}

output_json() {
  local checks_json="["

  local first=true
  for check_name in "${!CHECK_RESULTS[@]}"; do
    if [[ "$first" == "false" ]]; then
      checks_json+=","
    fi
    first=false

    local status="${CHECK_RESULTS[$check_name]}"
    local details="${CHECK_DETAILS[$check_name]}"

    checks_json+=$(jq -n \
      --arg name "$check_name" \
      --arg status "$status" \
      --arg details "$details" \
      '{name: $name, status: $status, details: $details}')
  done

  checks_json+="]"

  jq -n \
    --arg overall "$OVERALL_STATUS" \
    --argjson checks "$checks_json" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{overall_status: $overall, timestamp: $timestamp, checks: $checks}'
}

output_prometheus() {
  echo "# HELP cgrag_health_check Health check result (1=pass, 0=fail)"
  echo "# TYPE cgrag_health_check gauge"

  for check_name in "${!CHECK_RESULTS[@]}"; do
    local status="${CHECK_RESULTS[$check_name]}"

    local value
    case "$status" in
      pass)
        value=1
        ;;
      *)
        value=0
        ;;
    esac

    echo "cgrag_health_check{check=\"$check_name\",status=\"$status\"} $value"
  done

  # Overall health metric
  local overall_value
  if [[ "$OVERALL_STATUS" == "healthy" ]]; then
    overall_value=1
  else
    overall_value=0
  fi

  echo "cgrag_health_overall{status=\"$OVERALL_STATUS\"} $overall_value"
}

send_alert() {
  if [[ -z "$ALERT_WEBHOOK" ]]; then
    return
  fi

  local failed_checks=""
  for check_name in "${!CHECK_RESULTS[@]}"; do
    local status="${CHECK_RESULTS[$check_name]}"
    if [[ "$status" == "fail" || "$status" == "critical" ]]; then
      failed_checks+="- $check_name: $status (${CHECK_DETAILS[$check_name]})\n"
    fi
  done

  if [[ -n "$failed_checks" ]]; then
    local message="CGRAG Health Check: $OVERALL_STATUS\n\nFailed checks:\n$failed_checks"

    curl -X POST "$ALERT_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{\"text\": \"$message\"}" \
      --silent --show-error || log_error "Failed to send alert"
  fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
  log_verbose "Starting CGRAG health checks..."

  # Run all checks
  check_backend_api
  check_cgrag_endpoint
  check_faiss_indexes
  check_qdrant
  check_redis_connectivity
  check_redis_memory
  check_embedding_cache
  check_reranker_model
  check_knowledge_graph
  check_retrieval_latency
  check_prometheus_metrics

  # Output results
  case "$OUTPUT_FORMAT" in
    json)
      output_json
      ;;
    prometheus)
      output_prometheus
      ;;
    *)
      output_text
      ;;
  esac

  # Send alerts if configured
  send_alert

  # Exit with appropriate code
  if [[ "$OVERALL_STATUS" == "healthy" ]]; then
    exit 0
  elif [[ $CRITICAL_FAILURES -gt 0 ]]; then
    exit 2
  else
    exit 1
  fi
}

# Run main
main

# =============================================================================
# Notes:
# =============================================================================
# 1. Integration with Monitoring:
#    - Docker healthcheck: HEALTHCHECK CMD /scripts/check-cgrag-health.sh
#    - Kubernetes readiness: readinessProbe exec check-cgrag-health.sh
#    - Prometheus: Scrape /metrics with --prometheus flag
#
# 2. Automation:
#    - Cron: */5 * * * * /scripts/check-cgrag-health.sh --json >> /var/log/health.log
#    - Systemd timer: check-cgrag-health.timer
#    - Kubernetes CronJob: Schedule periodic health checks
#
# 3. Alert Channels:
#    - Slack: --alert-webhook https://hooks.slack.com/...
#    - Discord: --alert-webhook https://discord.com/api/webhooks/...
#    - Custom: POST JSON to any webhook endpoint
#
# 4. Troubleshooting:
#    - Run with --verbose for detailed output
#    - Check individual component logs
#    - Verify network connectivity
#    - Review Prometheus metrics for historical trends
#
# 5. Adding New Checks:
#    - Create check_<component>() function
#    - Call from main()
#    - Use record_check() to store results
#    - Document expected behavior
# =============================================================================

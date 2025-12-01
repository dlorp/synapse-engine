#!/usr/bin/env bash
# =============================================================================
# CGRAG Index Backup Script
# =============================================================================
# Automated backup of FAISS/Qdrant indexes, metadata, and Redis cache
#
# Features:
# - Timestamped backups with configurable retention
# - Supports both FAISS and Qdrant
# - Compresses backups with gzip
# - Integrity verification with checksums
# - Automatic cleanup of old backups
# - Slack/email notifications (optional)
#
# Usage:
#   ./scripts/backup-cgrag-indexes.sh [OPTIONS]
#
# Options:
#   --retention DAYS    Number of days to retain backups (default: 30)
#   --no-compression    Skip gzip compression
#   --verify-only       Only verify existing backups
#   --s3-upload         Upload to S3 after backup (requires aws-cli)
#   --quiet             Suppress output (log to file only)
#
# Examples:
#   # Daily backup (run via cron)
#   ./scripts/backup-cgrag-indexes.sh
#
#   # Backup with 7-day retention
#   ./scripts/backup-cgrag-indexes.sh --retention 7
#
#   # Backup and upload to S3
#   ./scripts/backup-cgrag-indexes.sh --s3-upload
#
# Schedule via cron (daily at 2 AM):
#   0 2 * * * /path/to/scripts/backup-cgrag-indexes.sh >> /var/log/cgrag-backup.log 2>&1
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Backup directory (absolute path)
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/backups/cgrag}"

# Source directories
FAISS_DIR="${FAISS_DIR:-${PROJECT_DIR}/backend/data/faiss_indexes}"
QDRANT_VOLUME="${QDRANT_VOLUME:-synapse_qdrant_data}"
REDIS_VOLUME="${REDIS_VOLUME:-synapse_redis_data}"

# Retention policy (days)
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Compression
COMPRESS="${COMPRESS:-true}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"  # 1-9, higher = better compression, slower

# S3 upload (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-cgrag-backups}"

# Notifications
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-}"

# Logging
LOG_FILE="${LOG_FILE:-/var/log/synapse/cgrag-backup.log}"

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case $1 in
    --retention)
      RETENTION_DAYS="$2"
      shift 2
      ;;
    --no-compression)
      COMPRESS=false
      shift
      ;;
    --verify-only)
      VERIFY_ONLY=true
      shift
      ;;
    --s3-upload)
      S3_UPLOAD=true
      shift
      ;;
    --quiet)
      QUIET=true
      shift
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
# Logging
# -----------------------------------------------------------------------------

log() {
  local level="$1"
  shift
  local message="$*"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  # Format: [TIMESTAMP] [LEVEL] MESSAGE
  local log_entry="[$timestamp] [$level] $message"

  # Write to log file
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "$log_entry" >> "$LOG_FILE"

  # Write to stdout (unless quiet)
  if [[ "${QUIET:-false}" != "true" ]]; then
    echo "$log_entry"
  fi
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# -----------------------------------------------------------------------------
# Notification Helpers
# -----------------------------------------------------------------------------

send_slack_notification() {
  local message="$1"

  if [[ -z "$SLACK_WEBHOOK" ]]; then
    return 0
  fi

  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"CGRAG Backup: $message\"}" \
    --silent --show-error || log_warn "Failed to send Slack notification"
}

send_email_notification() {
  local subject="$1"
  local body="$2"

  if [[ -z "$EMAIL_RECIPIENT" ]]; then
    return 0
  fi

  echo "$body" | mail -s "$subject" "$EMAIL_RECIPIENT" || log_warn "Failed to send email notification"
}

# -----------------------------------------------------------------------------
# Backup Functions
# -----------------------------------------------------------------------------

create_backup_directory() {
  local timestamp
  timestamp=$(date '+%Y%m%d_%H%M%S')

  BACKUP_PATH="$BACKUP_DIR/$timestamp"

  mkdir -p "$BACKUP_PATH"
  log_info "Created backup directory: $BACKUP_PATH"
}

backup_faiss_indexes() {
  log_info "Backing up FAISS indexes..."

  if [[ ! -d "$FAISS_DIR" ]]; then
    log_warn "FAISS directory not found: $FAISS_DIR"
    return 1
  fi

  # Count index files
  local index_count
  index_count=$(find "$FAISS_DIR" -name "*.index" | wc -l)

  if [[ $index_count -eq 0 ]]; then
    log_warn "No FAISS indexes found in $FAISS_DIR"
    return 1
  fi

  log_info "Found $index_count FAISS index(es)"

  # Create destination directory
  local dest="$BACKUP_PATH/faiss"
  mkdir -p "$dest"

  # Copy FAISS indexes and metadata
  cp -r "$FAISS_DIR"/* "$dest/" || {
    log_error "Failed to copy FAISS indexes"
    return 1
  }

  # Calculate total size
  local size
  size=$(du -sh "$dest" | cut -f1)
  log_info "FAISS backup complete: $size"

  # Compress if enabled
  if [[ "$COMPRESS" == "true" ]]; then
    log_info "Compressing FAISS backup..."
    tar -czf "$dest.tar.gz" -C "$BACKUP_PATH" faiss || {
      log_error "Failed to compress FAISS backup"
      return 1
    }
    rm -rf "$dest"
    log_info "FAISS backup compressed: $(du -sh "$dest.tar.gz" | cut -f1)"
  fi

  return 0
}

backup_qdrant_volume() {
  log_info "Backing up Qdrant volume..."

  # Check if Qdrant is running
  if ! docker ps --format '{{.Names}}' | grep -q synapse_qdrant; then
    log_warn "Qdrant container not running, skipping backup"
    return 1
  fi

  # Check if volume exists
  if ! docker volume inspect "$QDRANT_VOLUME" &>/dev/null; then
    log_warn "Qdrant volume not found: $QDRANT_VOLUME"
    return 1
  fi

  local dest="$BACKUP_PATH/qdrant"
  mkdir -p "$dest"

  # Create snapshot via Qdrant API (preferred method)
  log_info "Creating Qdrant snapshot..."
  local snapshot_name="backup_$(date '+%Y%m%d_%H%M%S')"

  curl -X POST "http://localhost:6333/collections/synapse_cgrag/snapshots?wait=true" \
    -H 'Content-Type: application/json' \
    -d "{\"snapshot_name\": \"$snapshot_name\"}" \
    --silent --show-error || {
    log_warn "Failed to create Qdrant snapshot via API, falling back to volume copy"

    # Fallback: Direct volume copy (requires container stop for consistency)
    docker run --rm \
      -v "$QDRANT_VOLUME:/source:ro" \
      -v "$dest:/backup" \
      alpine:latest \
      sh -c "cp -r /source/* /backup/" || {
      log_error "Failed to backup Qdrant volume"
      return 1
    }
  }

  # Download snapshot if API method succeeded
  if [[ -n "$snapshot_name" ]]; then
    curl "http://localhost:6333/collections/synapse_cgrag/snapshots/$snapshot_name" \
      --output "$dest/$snapshot_name.snapshot" \
      --silent --show-error || {
      log_error "Failed to download Qdrant snapshot"
      return 1
    }
  fi

  local size
  size=$(du -sh "$dest" | cut -f1)
  log_info "Qdrant backup complete: $size"

  # Compress if enabled
  if [[ "$COMPRESS" == "true" ]]; then
    log_info "Compressing Qdrant backup..."
    tar -czf "$dest.tar.gz" -C "$BACKUP_PATH" qdrant || {
      log_error "Failed to compress Qdrant backup"
      return 1
    }
    rm -rf "$dest"
    log_info "Qdrant backup compressed: $(du -sh "$dest.tar.gz" | cut -f1)"
  fi

  return 0
}

backup_redis_cache() {
  log_info "Backing up Redis cache (CGRAG embeddings)..."

  # Check if Redis is running
  if ! docker ps --format '{{.Names}}' | grep -q synapse_redis; then
    log_warn "Redis container not running, skipping backup"
    return 1
  fi

  local dest="$BACKUP_PATH/redis"
  mkdir -p "$dest"

  # Trigger Redis BGSAVE
  docker exec synapse_redis redis-cli -a "${MEMEX_PASSWORD:-change_this_secure_redis_password}" BGSAVE || {
    log_error "Failed to trigger Redis BGSAVE"
    return 1
  }

  # Wait for BGSAVE to complete
  log_info "Waiting for Redis BGSAVE to complete..."
  local attempts=0
  while [[ $attempts -lt 30 ]]; do
    local last_save
    last_save=$(docker exec synapse_redis redis-cli -a "${MEMEX_PASSWORD:-change_this_secure_redis_password}" LASTSAVE)
    sleep 2
    local current_save
    current_save=$(docker exec synapse_redis redis-cli -a "${MEMEX_PASSWORD:-change_this_secure_redis_password}" LASTSAVE)

    if [[ "$last_save" != "$current_save" ]]; then
      log_info "Redis BGSAVE completed"
      break
    fi

    ((attempts++))
  done

  # Copy RDB file from volume
  docker run --rm \
    -v "$REDIS_VOLUME:/source:ro" \
    -v "$dest:/backup" \
    alpine:latest \
    sh -c "cp /source/dump.rdb /backup/dump.rdb" || {
    log_error "Failed to copy Redis dump file"
    return 1
  }

  local size
  size=$(du -sh "$dest/dump.rdb" | cut -f1)
  log_info "Redis backup complete: $size"

  # Compress if enabled
  if [[ "$COMPRESS" == "true" ]]; then
    gzip -"$COMPRESSION_LEVEL" "$dest/dump.rdb" || {
      log_error "Failed to compress Redis backup"
      return 1
    }
    log_info "Redis backup compressed: $(du -sh "$dest/dump.rdb.gz" | cut -f1)"
  fi

  return 0
}

generate_checksums() {
  log_info "Generating checksums for integrity verification..."

  local checksum_file="$BACKUP_PATH/checksums.sha256"

  # Generate SHA256 checksums for all backup files
  find "$BACKUP_PATH" -type f ! -name 'checksums.sha256' -exec sha256sum {} \; > "$checksum_file" || {
    log_error "Failed to generate checksums"
    return 1
  }

  local checksum_count
  checksum_count=$(wc -l < "$checksum_file")
  log_info "Generated $checksum_count checksums"

  return 0
}

verify_backup() {
  local backup_path="$1"

  log_info "Verifying backup: $backup_path"

  local checksum_file="$backup_path/checksums.sha256"

  if [[ ! -f "$checksum_file" ]]; then
    log_error "Checksum file not found: $checksum_file"
    return 1
  fi

  # Verify checksums
  if ! (cd "$(dirname "$checksum_file")" && sha256sum -c checksums.sha256 --quiet); then
    log_error "Backup verification failed: checksum mismatch"
    return 1
  fi

  log_info "Backup verification successful"
  return 0
}

cleanup_old_backups() {
  log_info "Cleaning up backups older than $RETENTION_DAYS days..."

  local deleted_count=0

  # Find and delete old backups
  while IFS= read -r -d '' backup; do
    rm -rf "$backup"
    ((deleted_count++))
    log_info "Deleted old backup: $(basename "$backup")"
  done < <(find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -print0)

  if [[ $deleted_count -eq 0 ]]; then
    log_info "No old backups to delete"
  else
    log_info "Deleted $deleted_count old backup(s)"
  fi
}

upload_to_s3() {
  if [[ -z "$S3_BUCKET" ]]; then
    log_info "S3 upload disabled (S3_BUCKET not set)"
    return 0
  fi

  log_info "Uploading backup to S3: s3://$S3_BUCKET/$S3_PREFIX/$(basename "$BACKUP_PATH")"

  # Check if aws-cli is installed
  if ! command -v aws &>/dev/null; then
    log_error "aws-cli not installed, skipping S3 upload"
    return 1
  fi

  # Upload to S3
  aws s3 sync "$BACKUP_PATH" "s3://$S3_BUCKET/$S3_PREFIX/$(basename "$BACKUP_PATH")" \
    --storage-class STANDARD_IA \
    --quiet || {
    log_error "Failed to upload backup to S3"
    return 1
  }

  log_info "S3 upload complete"
  return 0
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
  local start_time
  start_time=$(date +%s)

  log_info "========================================="
  log_info "CGRAG Backup Started"
  log_info "========================================="

  # Verify-only mode
  if [[ "${VERIFY_ONLY:-false}" == "true" ]]; then
    log_info "Running in verify-only mode"

    for backup in "$BACKUP_DIR"/*; do
      if [[ -d "$backup" ]]; then
        verify_backup "$backup"
      fi
    done

    exit 0
  fi

  # Create backup directory
  create_backup_directory

  # Backup components
  local backup_status=0

  backup_faiss_indexes || backup_status=$?
  backup_qdrant_volume || backup_status=$?
  backup_redis_cache || backup_status=$?

  # Generate checksums
  generate_checksums || backup_status=$?

  # Verify backup
  verify_backup "$BACKUP_PATH" || backup_status=$?

  # Upload to S3 if enabled
  if [[ "${S3_UPLOAD:-false}" == "true" ]]; then
    upload_to_s3 || backup_status=$?
  fi

  # Cleanup old backups
  cleanup_old_backups

  # Calculate duration
  local end_time
  end_time=$(date +%s)
  local duration=$((end_time - start_time))

  # Calculate total backup size
  local total_size
  total_size=$(du -sh "$BACKUP_PATH" | cut -f1)

  log_info "========================================="
  log_info "CGRAG Backup Complete"
  log_info "Duration: ${duration}s"
  log_info "Total Size: $total_size"
  log_info "Location: $BACKUP_PATH"
  log_info "========================================="

  # Send notifications
  if [[ $backup_status -eq 0 ]]; then
    send_slack_notification "Backup successful (${duration}s, $total_size)"
    send_email_notification "CGRAG Backup Success" "Backup completed in ${duration}s. Size: $total_size. Location: $BACKUP_PATH"
  else
    send_slack_notification "Backup completed with errors (${duration}s)"
    send_email_notification "CGRAG Backup Warning" "Backup completed with errors. Check logs: $LOG_FILE"
  fi

  exit $backup_status
}

# Run main
main

# =============================================================================
# Notes:
# =============================================================================
# 1. Backup Strategy:
#    - FAISS: Full backup of index files and metadata
#    - Qdrant: Snapshot via API (preferred) or volume copy (fallback)
#    - Redis: BGSAVE + RDB file copy (embeddings cache)
#
# 2. Retention Policy:
#    - Daily: Keep 7 days
#    - Weekly: Keep 4 weeks
#    - Monthly: Keep 12 months
#    - Implement via cron with different retention settings
#
# 3. Compression:
#    - gzip level 6 balances speed/size (typical 70-80% reduction)
#    - Disable for fastest backup (--no-compression)
#    - Use level 9 for maximum compression (slower)
#
# 4. Integrity Verification:
#    - SHA256 checksums generated for all files
#    - Verify before restore: sha256sum -c checksums.sha256
#    - Run periodic verification: --verify-only
#
# 5. S3 Upload:
#    - Requires aws-cli configured with credentials
#    - STANDARD_IA storage class for cost optimization
#    - Lifecycle policy for glacier archival (optional)
#
# 6. Restore Procedure:
#    - Stop services: docker-compose down
#    - Extract backup: tar -xzf faiss.tar.gz
#    - Copy to data directory: cp -r faiss/* backend/data/faiss_indexes/
#    - Restart services: docker-compose up -d
#
# 7. Monitoring:
#    - Check logs: tail -f /var/log/synapse/cgrag-backup.log
#    - Alert on failures via Slack/email
#    - Monitor backup size growth over time
#
# 8. Performance:
#    - FAISS backup: ~1-5 minutes for 1GB index
#    - Qdrant snapshot: ~2-10 minutes for large collections
#    - Redis BGSAVE: <1 minute (non-blocking)
#    - Compression: Adds 20-50% overhead
#
# 9. Disaster Recovery:
#    - Keep offsite backups (S3, remote server)
#    - Test restore procedure quarterly
#    - Document RTO/RPO requirements
#    - Maintain backup runbook
#
# 10. Cron Schedule Examples:
#     # Daily backup at 2 AM
#     0 2 * * * /path/to/backup-cgrag-indexes.sh --retention 7
#
#     # Weekly backup on Sunday at 3 AM
#     0 3 * * 0 /path/to/backup-cgrag-indexes.sh --retention 30 --s3-upload
#
#     # Monthly backup on 1st at 4 AM
#     0 4 1 * * /path/to/backup-cgrag-indexes.sh --retention 365 --s3-upload
# =============================================================================

#!/bin/bash
################################################################################
# Database Backup Script for HAVEN Token Platform
#
# This script creates PostgreSQL backups with compression, encryption,
# and rotation. Supports both full and incremental backups.
#
# Usage:
#   ./backup_database.sh [OPTIONS]
#
# Options:
#   --type <full|incremental>  Backup type (default: full)
#   --retention <days>         Days to retain backups (default: 30)
#   --encrypt                  Enable GPG encryption
#   --s3-upload                Upload to S3 bucket
#   --help                     Show this help message
#
# Environment Variables:
#   DB_HOST               Database host (default: localhost)
#   DB_PORT               Database port (default: 5432)
#   DB_NAME               Database name (default: haven)
#   DB_USER               Database user (default: postgres)
#   DB_PASSWORD           Database password
#   BACKUP_DIR            Backup directory (default: /var/backups/haven)
#   GPG_RECIPIENT         GPG key for encryption
#   S3_BUCKET             S3 bucket for backup storage
#   AWS_PROFILE           AWS profile for S3 upload
#   SLACK_WEBHOOK_URL     Slack webhook for notifications
#
# Exit Codes:
#   0 - Success
#   1 - General error
#   2 - Database connection error
#   3 - Backup creation error
#   4 - Upload error
################################################################################

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-haven}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Backup configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/haven}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_TYPE="full"
ENABLE_ENCRYPTION=false
ENABLE_S3_UPLOAD=false

# Timestamp for backup files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_PATH=$(date +"%Y/%m/%d")

# Log file
LOG_DIR="${BACKUP_DIR}/logs"
LOG_FILE="${LOG_DIR}/backup_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ─────────────────────────────────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"

    case "${level}" in
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}" >&2
            ;;
        WARNING)
            echo -e "${YELLOW}[WARNING]${NC} ${message}"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} ${message}"
            ;;
    esac
}

show_help() {
    cat << EOF
Database Backup Script for HAVEN Token Platform

Usage: $0 [OPTIONS]

Options:
  --type <full|incremental>  Backup type (default: full)
  --retention <days>         Days to retain backups (default: 30)
  --encrypt                  Enable GPG encryption
  --s3-upload                Upload to S3 bucket
  --help                     Show this help message

Environment Variables:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  BACKUP_DIR, GPG_RECIPIENT, S3_BUCKET, AWS_PROFILE

Examples:
  # Full backup with encryption
  $0 --type full --encrypt

  # Full backup with S3 upload
  $0 --type full --s3-upload

  # Incremental backup with 7-day retention
  $0 --type incremental --retention 7

EOF
    exit 0
}

check_dependencies() {
    log "INFO" "Checking dependencies..."

    local missing_deps=()

    if ! command -v pg_dump &> /dev/null; then
        missing_deps+=("pg_dump (postgresql-client)")
    fi

    if ! command -v gzip &> /dev/null; then
        missing_deps+=("gzip")
    fi

    if [ "${ENABLE_ENCRYPTION}" = true ] && ! command -v gpg &> /dev/null; then
        missing_deps+=("gpg")
    fi

    if [ "${ENABLE_S3_UPLOAD}" = true ] && ! command -v aws &> /dev/null; then
        missing_deps+=("aws-cli")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi

    log "SUCCESS" "All dependencies satisfied"
}

create_directories() {
    log "INFO" "Creating backup directories..."

    mkdir -p "${BACKUP_DIR}/full"
    mkdir -p "${BACKUP_DIR}/incremental"
    mkdir -p "${LOG_DIR}"

    log "SUCCESS" "Directories created"
}

test_database_connection() {
    log "INFO" "Testing database connection..."

    export PGPASSWORD="${DB_PASSWORD}"

    if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1" > /dev/null 2>&1; then
        log "ERROR" "Failed to connect to database"
        exit 2
    fi

    log "SUCCESS" "Database connection successful"
}

create_full_backup() {
    local backup_file="${BACKUP_DIR}/full/haven_full_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"

    log "INFO" "Creating full database backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    # Create backup with pg_dump
    if ! pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        --file="${backup_file}" 2>> "${LOG_FILE}"; then
        log "ERROR" "Failed to create database backup"
        exit 3
    fi

    # Get backup size
    local backup_size=$(du -h "${backup_file}" | cut -f1)
    log "INFO" "Backup size: ${backup_size}"

    # Compress backup
    log "INFO" "Compressing backup..."
    if ! gzip -9 "${backup_file}"; then
        log "ERROR" "Failed to compress backup"
        exit 3
    fi

    local compressed_size=$(du -h "${compressed_file}" | cut -f1)
    log "SUCCESS" "Backup compressed: ${compressed_size}"

    # Encrypt if enabled
    if [ "${ENABLE_ENCRYPTION}" = true ]; then
        encrypt_backup "${compressed_file}"
    fi

    # Calculate checksum
    local checksum=$(sha256sum "${compressed_file}" | awk '{print $1}')
    echo "${checksum}  ${compressed_file}" > "${compressed_file}.sha256"
    log "INFO" "Checksum: ${checksum}"

    BACKUP_FILE="${compressed_file}"
}

create_incremental_backup() {
    local backup_file="${BACKUP_DIR}/incremental/haven_incremental_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"

    log "INFO" "Creating incremental backup..."

    # Find last full backup
    local last_full=$(find "${BACKUP_DIR}/full" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

    if [ -z "${last_full}" ]; then
        log "WARNING" "No full backup found, creating full backup instead"
        create_full_backup
        return
    fi

    log "INFO" "Last full backup: ${last_full}"

    # For PostgreSQL, incremental backups require WAL archiving
    # This is a simplified version that backs up only recent changes
    export PGPASSWORD="${DB_PASSWORD}"

    # Query to get recently modified data (last 24 hours)
    # This is application-specific and should be customized
    if ! pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=plain \
        --no-owner \
        --no-acl \
        --file="${backup_file}" \
        --table=transactions \
        --table=redemption_requests \
        --table=aurora_bookings \
        --table=tribe_events 2>> "${LOG_FILE}"; then
        log "ERROR" "Failed to create incremental backup"
        exit 3
    fi

    # Compress
    gzip -9 "${backup_file}"

    BACKUP_FILE="${compressed_file}"
    log "SUCCESS" "Incremental backup created"
}

encrypt_backup() {
    local file="$1"
    local encrypted_file="${file}.gpg"

    if [ -z "${GPG_RECIPIENT:-}" ]; then
        log "ERROR" "GPG_RECIPIENT not set"
        exit 1
    fi

    log "INFO" "Encrypting backup with GPG..."

    if ! gpg --encrypt --recipient "${GPG_RECIPIENT}" --output "${encrypted_file}" "${file}"; then
        log "ERROR" "Failed to encrypt backup"
        exit 3
    fi

    # Remove unencrypted file
    rm -f "${file}"

    BACKUP_FILE="${encrypted_file}"
    log "SUCCESS" "Backup encrypted"
}

upload_to_s3() {
    local file="$1"
    local s3_path="s3://${S3_BUCKET}/haven-backups/${DATE_PATH}/$(basename ${file})"

    log "INFO" "Uploading to S3: ${s3_path}"

    local aws_args=""
    if [ -n "${AWS_PROFILE:-}" ]; then
        aws_args="--profile ${AWS_PROFILE}"
    fi

    if ! aws ${aws_args} s3 cp "${file}" "${s3_path}" --storage-class STANDARD_IA; then
        log "ERROR" "Failed to upload to S3"
        exit 4
    fi

    # Upload checksum if exists
    if [ -f "${file}.sha256" ]; then
        aws ${aws_args} s3 cp "${file}.sha256" "${s3_path}.sha256"
    fi

    log "SUCCESS" "Backup uploaded to S3"
}

verify_backup() {
    local file="$1"

    log "INFO" "Verifying backup integrity..."

    # Verify checksum
    if [ -f "${file}.sha256" ]; then
        if ! sha256sum -c "${file}.sha256" > /dev/null 2>&1; then
            log "ERROR" "Backup checksum verification failed"
            exit 3
        fi
        log "SUCCESS" "Checksum verified"
    fi

    # Verify gzip integrity
    if [[ "${file}" == *.gz ]]; then
        if ! gzip -t "${file}" > /dev/null 2>&1; then
            log "ERROR" "Backup file is corrupted"
            exit 3
        fi
        log "SUCCESS" "Backup file integrity verified"
    fi
}

rotate_old_backups() {
    log "INFO" "Rotating old backups (keeping ${RETENTION_DAYS} days)..."

    local deleted_count=0

    # Delete old full backups
    while IFS= read -r -d '' file; do
        rm -f "${file}" "${file}.sha256" "${file}.gpg"
        ((deleted_count++))
    done < <(find "${BACKUP_DIR}/full" -name "*.sql.gz*" -type f -mtime +${RETENTION_DAYS} -print0)

    # Delete old incremental backups
    while IFS= read -r -d '' file; do
        rm -f "${file}" "${file}.sha256" "${file}.gpg"
        ((deleted_count++))
    done < <(find "${BACKUP_DIR}/incremental" -name "*.sql.gz*" -type f -mtime +${RETENTION_DAYS} -print0)

    # Delete old logs
    find "${LOG_DIR}" -name "backup_*.log" -type f -mtime +${RETENTION_DAYS} -delete

    log "INFO" "Deleted ${deleted_count} old backup files"
}

send_notification() {
    local status="$1"
    local message="$2"

    if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
        return
    fi

    local color="good"
    if [ "${status}" = "failure" ]; then
        color="danger"
    fi

    local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "${color}",
            "title": "Database Backup ${status^}",
            "text": "${message}",
            "fields": [
                {
                    "title": "Environment",
                    "value": "${ENVIRONMENT:-production}",
                    "short": true
                },
                {
                    "title": "Database",
                    "value": "${DB_NAME}",
                    "short": true
                },
                {
                    "title": "Backup Type",
                    "value": "${BACKUP_TYPE}",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "${TIMESTAMP}",
                    "short": true
                }
            ]
        }
    ]
}
EOF
)

    curl -X POST -H 'Content-type: application/json' \
        --data "${payload}" \
        "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1
}

# ─────────────────────────────────────────────────────────────────────────
# ARGUMENT PARSING
# ─────────────────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --encrypt)
            ENABLE_ENCRYPTION=true
            shift
            ;;
        --s3-upload)
            ENABLE_S3_UPLOAD=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# ─────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────

main() {
    log "INFO" "=== HAVEN Token Database Backup Started ==="
    log "INFO" "Backup type: ${BACKUP_TYPE}"
    log "INFO" "Retention: ${RETENTION_DAYS} days"

    # Pre-flight checks
    check_dependencies
    create_directories
    test_database_connection

    # Create backup
    local start_time=$(date +%s)

    case "${BACKUP_TYPE}" in
        full)
            create_full_backup
            ;;
        incremental)
            create_incremental_backup
            ;;
        *)
            log "ERROR" "Invalid backup type: ${BACKUP_TYPE}"
            exit 1
            ;;
    esac

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Verify backup
    verify_backup "${BACKUP_FILE}"

    # Upload to S3 if enabled
    if [ "${ENABLE_S3_UPLOAD}" = true ]; then
        upload_to_s3 "${BACKUP_FILE}"
    fi

    # Rotate old backups
    rotate_old_backups

    # Get final backup info
    local final_size=$(du -h "${BACKUP_FILE}" | cut -f1)

    log "SUCCESS" "=== Backup Completed Successfully ==="
    log "INFO" "Backup file: ${BACKUP_FILE}"
    log "INFO" "Backup size: ${final_size}"
    log "INFO" "Duration: ${duration} seconds"

    # Send success notification
    send_notification "success" "Backup completed in ${duration} seconds (${final_size})"

    exit 0
}

# Trap errors and send failure notification
trap 'send_notification "failure" "Backup failed. Check logs at ${LOG_FILE}"; exit 1' ERR

# Run main function
main

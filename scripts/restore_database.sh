#!/bin/bash
################################################################################
# Database Restore Script for HAVEN Token Platform
#
# This script restores PostgreSQL database from backups with verification
# and rollback capabilities.
#
# Usage:
#   ./restore_database.sh [OPTIONS]
#
# Options:
#   --backup-file <path>       Path to backup file to restore
#   --list-backups             List available backups
#   --from-s3                  Download backup from S3
#   --target-db <name>         Target database (default: haven)
#   --verify-only              Only verify backup, don't restore
#   --force                    Skip confirmation prompt
#   --help                     Show this help message
#
# Environment Variables:
#   DB_HOST               Database host (default: localhost)
#   DB_PORT               Database port (default: 5432)
#   DB_NAME               Target database name (default: haven)
#   DB_USER               Database user (default: postgres)
#   DB_PASSWORD           Database password
#   BACKUP_DIR            Backup directory (default: /var/backups/haven)
#   S3_BUCKET             S3 bucket for backup storage
#
# Exit Codes:
#   0 - Success
#   1 - General error
#   2 - Backup file not found
#   3 - Database connection error
#   4 - Restore failed
################################################################################

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

# Load environment
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
BACKUP_FILE=""
TARGET_DB="${DB_NAME}"
VERIFY_ONLY=false
FORCE=false
FROM_S3=false
LIST_BACKUPS=false

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Log file
LOG_DIR="${BACKUP_DIR}/logs"
LOG_FILE="${LOG_DIR}/restore_${TIMESTAMP}.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
        INFO)
            echo -e "${BLUE}[INFO]${NC} ${message}"
            ;;
    esac
}

show_help() {
    cat << EOF
Database Restore Script for HAVEN Token Platform

Usage: $0 [OPTIONS]

Options:
  --backup-file <path>       Path to backup file to restore
  --list-backups             List available backups
  --from-s3                  Download backup from S3
  --target-db <name>         Target database (default: ${DB_NAME})
  --verify-only              Only verify backup, don't restore
  --force                    Skip confirmation prompt
  --help                     Show this help message

Examples:
  # List available backups
  $0 --list-backups

  # Restore specific backup
  $0 --backup-file /var/backups/haven/full/haven_full_20250115_120000.sql.gz

  # Restore latest backup from S3
  $0 --from-s3 --force

  # Verify backup without restoring
  $0 --backup-file backup.sql.gz --verify-only

EOF
    exit 0
}

check_dependencies() {
    log "INFO" "Checking dependencies..."

    local missing_deps=()

    if ! command -v psql &> /dev/null; then
        missing_deps+=("psql (postgresql-client)")
    fi

    if ! command -v pg_restore &> /dev/null; then
        missing_deps+=("pg_restore (postgresql-client)")
    fi

    if ! command -v gunzip &> /dev/null; then
        missing_deps+=("gunzip")
    fi

    if [ "${FROM_S3}" = true ] && ! command -v aws &> /dev/null; then
        missing_deps+=("aws-cli")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi

    log "SUCCESS" "All dependencies satisfied"
}

list_available_backups() {
    log "INFO" "Available backups:"
    echo ""

    echo -e "${GREEN}=== Full Backups ===${NC}"
    if [ -d "${BACKUP_DIR}/full" ]; then
        find "${BACKUP_DIR}/full" -name "*.sql.gz*" -type f -printf "%T@ %Tc %s %p\n" \
            | sort -rn \
            | awk '{size=$3; $1=$2=$3=""; printf "%-20s  Size: %10.2f MB  %s\n", strftime("%Y-%m-%d %H:%M:%S", $1), size/1024/1024, $0}' \
            | head -10
    else
        echo "No full backups found"
    fi

    echo ""
    echo -e "${GREEN}=== Incremental Backups ===${NC}"
    if [ -d "${BACKUP_DIR}/incremental" ]; then
        find "${BACKUP_DIR}/incremental" -name "*.sql.gz*" -type f -printf "%T@ %Tc %s %p\n" \
            | sort -rn \
            | awk '{size=$3; $1=$2=$3=""; printf "%-20s  Size: %10.2f MB  %s\n", strftime("%Y-%m-%d %H:%M:%S", $1), size/1024/1024, $0}' \
            | head -10
    else
        echo "No incremental backups found"
    fi

    exit 0
}

download_from_s3() {
    log "INFO" "Downloading backup from S3..."

    local s3_bucket="${S3_BUCKET}"
    if [ -z "${s3_bucket}" ]; then
        log "ERROR" "S3_BUCKET not set"
        exit 1
    fi

    # List recent backups
    local recent_backup=$(aws s3 ls "s3://${s3_bucket}/haven-backups/" --recursive \
        | grep "\.sql\.gz$" \
        | sort -r \
        | head -1 \
        | awk '{print $4}')

    if [ -z "${recent_backup}" ]; then
        log "ERROR" "No backups found in S3"
        exit 2
    fi

    log "INFO" "Latest backup: ${recent_backup}"

    # Download backup
    local local_file="${BACKUP_DIR}/temp/$(basename ${recent_backup})"
    mkdir -p "$(dirname ${local_file})"

    if ! aws s3 cp "s3://${s3_bucket}/${recent_backup}" "${local_file}"; then
        log "ERROR" "Failed to download backup from S3"
        exit 2
    fi

    # Download checksum if available
    aws s3 cp "s3://${s3_bucket}/${recent_backup}.sha256" "${local_file}.sha256" 2>/dev/null || true

    BACKUP_FILE="${local_file}"
    log "SUCCESS" "Backup downloaded from S3"
}

verify_backup() {
    local file="$1"

    log "INFO" "Verifying backup file..."

    # Check if file exists
    if [ ! -f "${file}" ]; then
        log "ERROR" "Backup file not found: ${file}"
        exit 2
    fi

    # Verify checksum if available
    if [ -f "${file}.sha256" ]; then
        log "INFO" "Verifying checksum..."
        if ! sha256sum -c "${file}.sha256" > /dev/null 2>&1; then
            log "ERROR" "Checksum verification failed"
            exit 2
        fi
        log "SUCCESS" "Checksum verified"
    else
        log "WARNING" "No checksum file found, skipping verification"
    fi

    # Test gzip integrity
    if [[ "${file}" == *.gz ]] || [[ "${file}" == *.gz.gpg ]]; then
        log "INFO" "Testing archive integrity..."

        local test_file="${file}"

        # Decrypt if encrypted
        if [[ "${file}" == *.gpg ]]; then
            log "INFO" "Decrypting backup..."
            local decrypted="${file%.gpg}"
            if ! gpg --decrypt --output "${decrypted}" "${file}" 2>/dev/null; then
                log "ERROR" "Failed to decrypt backup"
                exit 2
            fi
            test_file="${decrypted}"
        fi

        if [[ "${test_file}" == *.gz ]]; then
            if ! gzip -t "${test_file}" > /dev/null 2>&1; then
                log "ERROR" "Backup archive is corrupted"
                [ -f "${decrypted:-}" ] && rm -f "${decrypted}"
                exit 2
            fi
        fi

        [ -f "${decrypted:-}" ] && rm -f "${decrypted}"
        log "SUCCESS" "Archive integrity verified"
    fi

    # Get backup info
    local size=$(du -h "${file}" | cut -f1)
    local mod_time=$(stat -c %y "${file}" 2>/dev/null || stat -f "%Sm" "${file}")

    log "INFO" "Backup size: ${size}"
    log "INFO" "Backup date: ${mod_time}"
    log "SUCCESS" "Backup verification completed"
}

test_database_connection() {
    log "INFO" "Testing database connection..."

    export PGPASSWORD="${DB_PASSWORD}"

    if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        log "ERROR" "Failed to connect to database server"
        exit 3
    fi

    log "SUCCESS" "Database connection successful"
}

create_pre_restore_backup() {
    log "INFO" "Creating pre-restore backup of ${TARGET_DB}..."

    export PGPASSWORD="${DB_PASSWORD}"

    local pre_backup="${BACKUP_DIR}/pre-restore/haven_pre_restore_${TIMESTAMP}.sql.gz"
    mkdir -p "$(dirname ${pre_backup})"

    # Check if database exists
    if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -lqt | cut -d \| -f 1 | grep -qw "${TARGET_DB}"; then
        if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TARGET_DB}" | gzip > "${pre_backup}"; then
            log "SUCCESS" "Pre-restore backup created: ${pre_backup}"
            echo "${pre_backup}" > "${BACKUP_DIR}/temp/pre_restore_backup.txt"
        else
            log "WARNING" "Failed to create pre-restore backup"
        fi
    else
        log "INFO" "Target database doesn't exist, skipping pre-restore backup"
    fi
}

confirm_restore() {
    if [ "${FORCE}" = true ]; then
        return 0
    fi

    echo ""
    log "WARNING" "This will restore database: ${TARGET_DB}"
    log "WARNING" "All existing data in ${TARGET_DB} will be replaced!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "INFO" "Restore cancelled by user"
        exit 0
    fi
}

restore_database() {
    local file="$1"

    log "INFO" "Starting database restore..."

    export PGPASSWORD="${DB_PASSWORD}"

    # Prepare file (decrypt and decompress)
    local sql_file="${file}"

    # Decrypt if needed
    if [[ "${file}" == *.gpg ]]; then
        log "INFO" "Decrypting backup..."
        sql_file="${file%.gpg}"
        if ! gpg --decrypt --output "${sql_file}" "${file}"; then
            log "ERROR" "Failed to decrypt backup"
            exit 4
        fi
    fi

    # Decompress if needed
    if [[ "${sql_file}" == *.gz ]]; then
        log "INFO" "Decompressing backup..."
        local temp_sql="${BACKUP_DIR}/temp/restore_${TIMESTAMP}.sql"
        mkdir -p "$(dirname ${temp_sql})"
        if ! gunzip -c "${sql_file}" > "${temp_sql}"; then
            log "ERROR" "Failed to decompress backup"
            exit 4
        fi
        sql_file="${temp_sql}"
    fi

    # Drop existing database if it exists
    log "INFO" "Dropping existing database: ${TARGET_DB}"
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TARGET_DB};" || true

    # Create fresh database
    log "INFO" "Creating database: ${TARGET_DB}"
    if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${TARGET_DB};"; then
        log "ERROR" "Failed to create database"
        exit 4
    fi

    # Restore from SQL file
    log "INFO" "Restoring database from backup..."
    local start_time=$(date +%s)

    if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TARGET_DB}" \
        -f "${sql_file}" > "${LOG_DIR}/restore_output_${TIMESTAMP}.log" 2>&1; then
        log "ERROR" "Database restore failed. Check ${LOG_DIR}/restore_output_${TIMESTAMP}.log"
        exit 4
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Cleanup temporary files
    [ -f "${temp_sql:-}" ] && rm -f "${temp_sql}"
    [ -f "${sql_file%.gz}" ] && rm -f "${sql_file%.gz}"

    log "SUCCESS" "Database restored successfully in ${duration} seconds"
}

verify_restored_database() {
    log "INFO" "Verifying restored database..."

    export PGPASSWORD="${DB_PASSWORD}"

    # Check if database exists
    if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -lqt | cut -d \| -f 1 | grep -qw "${TARGET_DB}"; then
        log "ERROR" "Restored database not found"
        exit 4
    fi

    # Get table count
    local table_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TARGET_DB}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

    log "INFO" "Tables in restored database: ${table_count}"

    # Get sample data counts
    local users_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TARGET_DB}" \
        -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "0")

    local transactions_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TARGET_DB}" \
        -t -c "SELECT COUNT(*) FROM transactions;" 2>/dev/null | tr -d ' ' || echo "0")

    log "INFO" "Users: ${users_count}, Transactions: ${transactions_count}"

    log "SUCCESS" "Database verification completed"
}

rollback_restore() {
    log "WARNING" "Rolling back restore..."

    local pre_backup_file="${BACKUP_DIR}/temp/pre_restore_backup.txt"

    if [ ! -f "${pre_backup_file}" ]; then
        log "ERROR" "No pre-restore backup found, cannot rollback"
        exit 4
    fi

    local pre_backup=$(cat "${pre_backup_file}")

    if [ ! -f "${pre_backup}" ]; then
        log "ERROR" "Pre-restore backup file not found: ${pre_backup}"
        exit 4
    fi

    log "INFO" "Restoring from pre-restore backup: ${pre_backup}"

    BACKUP_FILE="${pre_backup}"
    restore_database "${BACKUP_FILE}"

    log "SUCCESS" "Rollback completed"
}

# ─────────────────────────────────────────────────────────────────────────
# ARGUMENT PARSING
# ─────────────────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --target-db)
            TARGET_DB="$2"
            shift 2
            ;;
        --list-backups)
            LIST_BACKUPS=true
            shift
            ;;
        --from-s3)
            FROM_S3=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
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
    mkdir -p "${LOG_DIR}"

    log "INFO" "=== HAVEN Token Database Restore Started ==="

    # Handle special modes
    if [ "${LIST_BACKUPS}" = true ]; then
        list_available_backups
    fi

    # Checks
    check_dependencies
    test_database_connection

    # Get backup file
    if [ "${FROM_S3}" = true ]; then
        download_from_s3
    fi

    if [ -z "${BACKUP_FILE}" ]; then
        log "ERROR" "No backup file specified. Use --backup-file or --from-s3"
        exit 1
    fi

    # Verify backup
    verify_backup "${BACKUP_FILE}"

    if [ "${VERIFY_ONLY}" = true ]; then
        log "INFO" "Verify-only mode, exiting"
        exit 0
    fi

    # Confirm restore
    confirm_restore

    # Create pre-restore backup
    create_pre_restore_backup

    # Restore database
    restore_database "${BACKUP_FILE}"

    # Verify restoration
    verify_restored_database

    log "SUCCESS" "=== Database Restore Completed Successfully ==="

    exit 0
}

# Trap errors and offer rollback
trap 'log "ERROR" "Restore failed. Run with --rollback to restore previous state"; exit 4' ERR

# Run main
main

#!/bin/bash
################################################################################
# Backup Verification Script for HAVEN Token Platform
#
# Verifies backup integrity, performs test restorations, and reports status.
#
# Usage:
#   ./verify_backup.sh [OPTIONS]
#
# Options:
#   --latest                   Verify latest backup
#   --file <path>              Verify specific backup file
#   --full-restore-test        Perform full restoration test
#   --send-report              Send verification report via email/Slack
#   --help                     Show help
################################################################################

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/haven}"
LOG_DIR="${BACKUP_DIR}/logs"
LOG_FILE="${LOG_DIR}/verify_$(date +%Y%m%d_%H%M%S).log"
TEST_DB_NAME="haven_verify_test"
VERIFY_LATEST=false
FULL_RESTORE_TEST=false
SEND_REPORT=false
BACKUP_FILE=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Results tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

mkdir -p "${LOG_DIR}"

log() {
    local level="$1"
    shift
    local message="$@"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_check() {
    local status="$1"
    local message="$2"

    ((TOTAL_CHECKS++))

    case "${status}" in
        PASS)
            ((PASSED_CHECKS++))
            echo -e "${GREEN}✓${NC} ${message}" | tee -a "${LOG_FILE}"
            ;;
        FAIL)
            ((FAILED_CHECKS++))
            echo -e "${RED}✗${NC} ${message}" | tee -a "${LOG_FILE}"
            ;;
        WARN)
            ((WARNINGS++))
            echo -e "${YELLOW}⚠${NC} ${message}" | tee -a "${LOG_FILE}"
            ;;
    esac
}

show_help() {
    cat << EOF
Backup Verification Script

Usage: $0 [OPTIONS]

Options:
  --latest                   Verify latest backup
  --file <path>              Verify specific backup file
  --full-restore-test        Perform full restoration test
  --send-report              Send verification report
  --help                     Show this help

Examples:
  $0 --latest
  $0 --file /var/backups/haven/full/backup.sql.gz --full-restore-test
EOF
    exit 0
}

find_latest_backup() {
    local latest=$(find "${BACKUP_DIR}/full" -name "*.sql.gz" -type f -printf '%T@ %p\n' \
        | sort -rn | head -1 | cut -d' ' -f2-)

    if [ -z "${latest}" ]; then
        log "ERROR" "No backups found in ${BACKUP_DIR}/full"
        exit 1
    fi

    echo "${latest}"
}

verify_file_exists() {
    if [ ! -f "${BACKUP_FILE}" ]; then
        log_check "FAIL" "Backup file not found: ${BACKUP_FILE}"
        return 1
    fi
    log_check "PASS" "Backup file exists"
}

verify_file_size() {
    local size=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}")
    local size_mb=$((size / 1024 / 1024))

    if [ ${size} -eq 0 ]; then
        log_check "FAIL" "Backup file is empty"
        return 1
    elif [ ${size_mb} -lt 1 ]; then
        log_check "WARN" "Backup file is very small: ${size_mb}MB"
        return 0
    fi

    log_check "PASS" "Backup file size: ${size_mb}MB"
}

verify_checksum() {
    if [ ! -f "${BACKUP_FILE}.sha256" ]; then
        log_check "WARN" "No checksum file found"
        return 0
    fi

    if sha256sum -c "${BACKUP_FILE}.sha256" > /dev/null 2>&1; then
        log_check "PASS" "Checksum verification passed"
    else
        log_check "FAIL" "Checksum verification failed"
        return 1
    fi
}

verify_compression() {
    if [[ "${BACKUP_FILE}" == *.gz ]]; then
        if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
            log_check "PASS" "Compression integrity verified"
        else
            log_check "FAIL" "Backup file is corrupted"
            return 1
        fi
    fi
}

verify_sql_structure() {
    log "INFO" "Verifying SQL structure..."

    local temp_sql=$(mktemp)

    if [[ "${BACKUP_FILE}" == *.gz ]]; then
        gunzip -c "${BACKUP_FILE}" > "${temp_sql}"
    else
        cp "${BACKUP_FILE}" "${temp_sql}"
    fi

    # Check for essential tables
    local has_users=$(grep -c "CREATE TABLE.*users" "${temp_sql}" || echo "0")
    local has_transactions=$(grep -c "CREATE TABLE.*transactions" "${temp_sql}" || echo "0")

    rm -f "${temp_sql}"

    if [ ${has_users} -gt 0 ] && [ ${has_transactions} -gt 0 ]; then
        log_check "PASS" "SQL structure contains required tables"
    else
        log_check "FAIL" "SQL structure missing required tables"
        return 1
    fi
}

test_restoration() {
    log "INFO" "Performing restoration test..."

    export PGPASSWORD="${DB_PASSWORD}"

    # Drop test database if exists
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" 2>/dev/null || true

    # Create test database
    if ! psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "CREATE DATABASE ${TEST_DB_NAME};"; then
        log_check "FAIL" "Failed to create test database"
        return 1
    fi

    # Decompress if needed
    local sql_file="${BACKUP_FILE}"
    if [[ "${BACKUP_FILE}" == *.gz ]]; then
        sql_file=$(mktemp)
        gunzip -c "${BACKUP_FILE}" > "${sql_file}"
    fi

    # Restore to test database
    if psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" \
        -d "${TEST_DB_NAME}" -f "${sql_file}" > /dev/null 2>&1; then
        log_check "PASS" "Test restoration successful"
    else
        log_check "FAIL" "Test restoration failed"
        [ -f "${sql_file}" ] && rm -f "${sql_file}"
        return 1
    fi

    # Cleanup
    if [[ "${BACKUP_FILE}" == *.gz ]]; then
        rm -f "${sql_file}"
    fi

    # Verify data
    local table_count=$(psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" \
        -U "${DB_USER:-postgres}" -d "${TEST_DB_NAME}" -t \
        -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" \
        | tr -d ' ')

    if [ ${table_count} -gt 0 ]; then
        log_check "PASS" "Test database contains ${table_count} tables"
    else
        log_check "FAIL" "Test database has no tables"
        return 1
    fi

    # Sample data verification
    local users_count=$(psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" \
        -U "${DB_USER:-postgres}" -d "${TEST_DB_NAME}" -t \
        -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "0")

    log "INFO" "Sample data: Users=${users_count}"

    # Cleanup test database
    psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres \
        -c "DROP DATABASE ${TEST_DB_NAME};" 2>/dev/null || true

    log_check "PASS" "Test database cleanup completed"
}

generate_report() {
    local report_file="${LOG_DIR}/verification_report_$(date +%Y%m%d).txt"

    cat > "${report_file}" << EOF
====================================
HAVEN Token Backup Verification Report
====================================

Date: $(date)
Backup File: ${BACKUP_FILE}

Summary:
--------
Total Checks: ${TOTAL_CHECKS}
Passed: ${PASSED_CHECKS}
Failed: ${FAILED_CHECKS}
Warnings: ${WARNINGS}

Status: $( [ ${FAILED_CHECKS} -eq 0 ] && echo "✓ PASSED" || echo "✗ FAILED" )

Details:
--------
EOF

    cat "${LOG_FILE}" >> "${report_file}"

    echo "${report_file}"
}

send_report() {
    local report_file=$(generate_report)
    local status=$( [ ${FAILED_CHECKS} -eq 0 ] && echo "SUCCESS" || echo "FAILURE" )

    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color=$( [ ${FAILED_CHECKS} -eq 0 ] && echo "good" || echo "danger" )

        local payload=$(cat <<EOF
{
    "attachments": [{
        "color": "${color}",
        "title": "Backup Verification ${status}",
        "fields": [
            {"title": "Total Checks", "value": "${TOTAL_CHECKS}", "short": true},
            {"title": "Passed", "value": "${PASSED_CHECKS}", "short": true},
            {"title": "Failed", "value": "${FAILED_CHECKS}", "short": true},
            {"title": "Warnings", "value": "${WARNINGS}", "short": true}
        ],
        "footer": "HAVEN Token Backup System"
    }]
}
EOF
)

        curl -X POST -H 'Content-type: application/json' \
            --data "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1
    fi

    log "INFO" "Report generated: ${report_file}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --latest) VERIFY_LATEST=true; shift ;;
        --file) BACKUP_FILE="$2"; shift 2 ;;
        --full-restore-test) FULL_RESTORE_TEST=true; shift ;;
        --send-report) SEND_REPORT=true; shift ;;
        --help) show_help ;;
        *) echo "Unknown option: $1"; show_help ;;
    esac
done

# Main execution
main() {
    log "INFO" "=== Backup Verification Started ==="

    if [ "${VERIFY_LATEST}" = true ]; then
        BACKUP_FILE=$(find_latest_backup)
        log "INFO" "Verifying latest backup: ${BACKUP_FILE}"
    fi

    if [ -z "${BACKUP_FILE}" ]; then
        log "ERROR" "No backup file specified"
        exit 1
    fi

    # Run verification checks
    verify_file_exists || exit 1
    verify_file_size
    verify_checksum
    verify_compression

    if [ "${FULL_RESTORE_TEST}" = true ]; then
        verify_sql_structure
        test_restoration
    fi

    # Generate and send report
    if [ "${SEND_REPORT}" = true ]; then
        send_report
    fi

    log "INFO" "=== Verification Completed ==="
    log "INFO" "Summary: ${PASSED_CHECKS}/${TOTAL_CHECKS} checks passed, ${FAILED_CHECKS} failed, ${WARNINGS} warnings"

    # Exit with error if any checks failed
    [ ${FAILED_CHECKS} -eq 0 ]
}

main

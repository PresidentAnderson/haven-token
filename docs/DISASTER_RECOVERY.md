# HAVEN Token Disaster Recovery Plan

**Version:** 1.0
**Last Updated:** 2025-01-08
**Owner:** DevOps & Security Team

---

## Table of Contents

1. [Overview](#overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Backup Strategy](#backup-strategy)
4. [Recovery Procedures](#recovery-procedures)
5. [Runbooks](#runbooks)
6. [Testing & Validation](#testing--validation)
7. [Contact Information](#contact-information)
8. [Change Log](#change-log)

---

## Overview

This document outlines the disaster recovery (DR) procedures for the HAVEN Token platform, covering:
- Database backups and restoration
- System recovery procedures
- Incident response workflows
- Communication protocols

### Scope

- **In Scope:** PostgreSQL database, smart contracts, backend services, configurations
- **Out of Scope:** Third-party integrations (Aurora PMS, Tribe app), cloud infrastructure (managed by cloud provider)

### Assumptions

- Cloud infrastructure (AWS/GCP) is available
- Backup storage (S3) is accessible
- Network connectivity is functional
- GPG encryption keys are available

---

## Recovery Objectives

### RTO (Recovery Time Objective)

**Target:** 2 hours maximum for full system recovery

| Component | RTO Target | Priority |
|-----------|------------|----------|
| Database (PostgreSQL) | 30 minutes | Critical |
| Backend API | 15 minutes | Critical |
| Smart Contracts | N/A (immutable) | Critical |
| Analytics Dashboard | 2 hours | Medium |
| Documentation | 24 hours | Low |

### RPO (Recovery Point Objective)

**Target:** Maximum 1 hour data loss

| Data Type | RPO Target | Backup Frequency |
|-----------|------------|------------------|
| Transaction Data | 15 minutes | Continuous (WAL archiving) |
| User Data | 1 hour | Hourly incremental |
| Configuration | 24 hours | Daily |
| Logs | 1 hour | Real-time streaming |

### Data Criticality

**Critical Data (Must not be lost):**
- User wallet addresses and credentials
- Transaction records (mint/burn/transfer)
- Redemption requests and payouts
- Smart contract deployment addresses

**Important Data (Acceptable 1-hour loss):**
- Booking records
- Event attendance
- Analytics data
- Audit logs

**Non-Critical Data (Acceptable 24-hour loss):**
- Cached data
- Session data
- Temporary files

---

## Backup Strategy

### Backup Types

#### 1. Full Database Backups

**Frequency:** Daily at 2:00 AM UTC

```bash
# Automated via cron
0 2 * * * /opt/haven/scripts/backup_database.sh --type full --encrypt --s3-upload
```

**Retention:**
- Daily backups: 30 days
- Weekly backups (Sunday): 90 days
- Monthly backups (1st): 1 year

#### 2. Incremental Backups

**Frequency:** Every 6 hours

```bash
# Cron schedule
0 */6 * * * /opt/haven/scripts/backup_database.sh --type incremental --s3-upload
```

**Retention:** 7 days

#### 3. Transaction Logs (WAL)

**Frequency:** Continuous (PostgreSQL WAL archiving)

```bash
# PostgreSQL configuration (postgresql.conf)
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://haven-wal-archive/%f'
```

**Retention:** 7 days

### Backup Locations

| Backup Type | Primary Location | Secondary Location | Encryption |
|-------------|------------------|-------------------|------------|
| Full DB | S3 `s3://haven-backups/full/` | GCS `gs://haven-dr/full/` | GPG (AES-256) |
| Incremental | S3 `s3://haven-backups/incremental/` | Local `/var/backups/haven/` | GPG |
| WAL Archive | S3 `s3://haven-wal-archive/` | - | None (PostgreSQL encryption) |
| Config Files | S3 `s3://haven-config/` | Git repository | GPG |

### Backup Verification

**Automated Daily Verification:**

```bash
# Run verification script
/opt/haven/scripts/verify_backup.sh --latest

# Expected output
✓ Backup file integrity verified
✓ Checksum validated
✓ Encryption working
✓ Restoration test passed
```

**Monthly Manual Verification:**
- Full restore to staging environment
- Data integrity checks
- Performance testing
- Documentation update

---

## Recovery Procedures

### Disaster Scenarios

1. **Database Corruption** - PostgreSQL data corruption
2. **Data Center Failure** - Complete AWS region outage
3. **Ransomware Attack** - System encryption/data loss
4. **Human Error** - Accidental deletion/modification
5. **Smart Contract Bug** - Critical vulnerability discovered

---

## Runbooks

### Runbook 1: Database Corruption Recovery

**Scenario:** PostgreSQL database is corrupted or inaccessible

**Detection:**
- Health check endpoint returns 503
- Database connection errors in logs
- Alert from monitoring system

**Recovery Steps:**

```bash
# 1. Assess the damage
psql -h db-host -U postgres -c "SELECT pg_database.datname FROM pg_database;"

# 2. Stop application services
systemctl stop haven-backend
systemctl stop haven-workers

# 3. Create emergency backup (if possible)
pg_dump -h db-host -U postgres haven > /tmp/emergency_backup_$(date +%s).sql

# 4. List available backups
/opt/haven/scripts/restore_database.sh --list-backups

# 5. Download latest backup from S3
/opt/haven/scripts/restore_database.sh --from-s3 --verify-only

# 6. Restore database
/opt/haven/scripts/restore_database.sh --from-s3 --force

# 7. Verify restoration
psql -h db-host -U postgres -d haven -c "SELECT COUNT(*) FROM users;"
psql -h db-host -U postgres -d haven -c "SELECT COUNT(*) FROM transactions;"

# 8. Restart services
systemctl start haven-backend
systemctl start haven-workers

# 9. Verify application health
curl https://api.haventoken.com/health

# 10. Monitor for 15 minutes
tail -f /var/log/haven/backend.log
```

**Estimated Time:** 30-45 minutes
**Data Loss:** < 6 hours (last incremental backup)

---

### Runbook 2: Complete Data Center Failure

**Scenario:** Entire AWS region is unavailable

**Recovery Steps:**

```bash
# 1. Activate DR environment in secondary region
terraform apply -var="region=us-west-2" -var="dr_mode=true"

# 2. Update DNS to point to DR environment
# (Automated via Route53 health checks)

# 3. Restore database from S3 in secondary region
aws s3 sync s3://haven-backups-us-east-1/full/ /var/backups/haven/full/ --region us-west-2

# 4. Restore latest backup
/opt/haven/scripts/restore_database.sh \
  --backup-file /var/backups/haven/full/haven_full_latest.sql.gz \
  --force

# 5. Apply WAL archives to recover recent transactions
/opt/haven/scripts/apply_wal_archives.sh --since "1 hour ago"

# 6. Update environment configuration
export DATABASE_URL="postgresql://postgres@dr-db-host:5432/haven"
export RPC_URL="https://base-sepolia.g.alchemy.com/v2/..."

# 7. Start all services
docker-compose -f docker-compose.dr.yml up -d

# 8. Verify services
curl https://dr-api.haventoken.com/health
curl https://dr-api.haventoken.com/analytics/token-stats

# 9. Notify users of temporary DR mode
# (Send via email, social media, status page)

# 10. Monitor and prepare for migration back to primary region
```

**Estimated Time:** 1-2 hours
**Data Loss:** < 15 minutes (WAL archives)

---

### Runbook 3: Ransomware Attack Recovery

**Scenario:** Systems encrypted by ransomware, data held hostage

**Immediate Actions:**

```bash
# 1. ISOLATE SYSTEMS IMMEDIATELY
# - Disconnect from network
# - Disable API endpoints
# - Stop all services

# 2. Preserve evidence
sudo dd if=/dev/sda of=/mnt/forensics/disk_image.dd bs=4M
tar czf /mnt/forensics/logs_$(date +%s).tar.gz /var/log/

# 3. Contact security team & law enforcement
# - security@haventoken.com
# - FBI IC3: https://www.ic3.gov

# 4. Assess scope of infection
find / -name "*.encrypted" -o -name "*.locked" -o -name "RANSOM*"

# 5. DO NOT PAY RANSOM

# 6. Rebuild infrastructure from clean images
terraform destroy --target=module.infected_instances
terraform apply --target=module.clean_instances

# 7. Restore from clean backup (pre-infection)
# Identify last clean backup timestamp
/opt/haven/scripts/restore_database.sh \
  --backup-file /var/backups/haven/full/haven_full_20250107_020000.sql.gz \
  --force

# 8. Audit all API keys, credentials, wallets
# - Rotate all secrets
# - Generate new API keys
# - Review blockchain transactions for unauthorized activity

# 9. Harden security before going live
# - Update all dependencies
# - Enable additional monitoring
# - Implement additional firewall rules
# - Enable MFA for all admin accounts

# 10. Gradually restore service
# - Start in read-only mode
# - Verify data integrity
# - Enable write operations
# - Monitor for 48 hours
```

**Estimated Time:** 4-8 hours
**Data Loss:** Depends on backup age (target: < 24 hours)

---

### Runbook 4: Accidental Data Deletion

**Scenario:** Critical data accidentally deleted (e.g., transactions table dropped)

**Recovery Steps:**

```bash
# 1. Stop all write operations immediately
systemctl stop haven-backend
systemctl stop haven-workers

# 2. Check PostgreSQL WAL for deleted data
psql -h db-host -U postgres -d haven -c "\
  SELECT * FROM pg_stat_activity \
  WHERE query LIKE '%DROP TABLE%' OR query LIKE '%DELETE FROM%';"

# 3. If recent (< 15 min), use Point-in-Time Recovery (PITR)
# Identify exact timestamp before deletion
BEFORE_DELETION="2025-01-08 14:30:00"

# Create new database from backup and WAL replay
pg_restore -h db-host -U postgres --target-time="${BEFORE_DELETION}" \
  -d haven_recovery /var/backups/haven/full/latest.dump

# 4. Export deleted data
pg_dump -h db-host -U postgres -d haven_recovery \
  --table=transactions --data-only > deleted_transactions.sql

# 5. Import deleted data to production
psql -h db-host -U postgres -d haven < deleted_transactions.sql

# 6. Verify data restoration
psql -h db-host -U postgres -d haven -c "SELECT COUNT(*) FROM transactions;"

# 7. Restart services
systemctl start haven-backend
systemctl start haven-workers

# 8. Audit logs to prevent recurrence
grep "DROP TABLE\|DELETE FROM" /var/log/postgresql/*.log

# 9. Implement additional safeguards
# - Enable query logging
# - Restrict DROP permissions
# - Add pre-delete hooks
```

**Estimated Time:** 1-2 hours
**Data Loss:** None (if caught within 15 minutes)

---

### Runbook 5: Smart Contract Bug Discovery

**Scenario:** Critical vulnerability found in HAVEN token contract

**Response Steps:**

```bash
# 1. PAUSE CONTRACT IMMEDIATELY (if pausable)
# Execute via Hardhat script
npx hardhat run scripts/emergency_pause.ts --network base-mainnet

# 2. Assess vulnerability impact
# - Review affected functions
# - Check for exploits in blockchain
# - Calculate potential loss

# 3. Notify users via all channels
# - Website banner
# - Email blast
# - Social media
# - Discord/Telegram

# 4. Freeze token transfers (if possible)
# Execute pause function or use admin controls

# 5. Prepare fix
# - Write patched contract
# - Conduct security audit
# - Test on testnet

# 6. Deploy fixed contract
npx hardhat run scripts/deploy_v2.ts --network base-mainnet

# 7. Migrate state to new contract
# - Snapshot balances
# - Redeploy with correct state
# - Update all references

# 8. Resume operations
# - Unpause contract
# - Update API to use new contract address
# - Verify all integrations

# 9. Post-mortem analysis
# - Document vulnerability
# - Update security practices
# - Compensate affected users if needed
```

**Estimated Time:** 24-48 hours
**Data Loss:** Depends on exploit severity

---

## Testing & Validation

### Quarterly DR Drill Schedule

| Quarter | Drill Type | Scenario | Duration |
|---------|------------|----------|----------|
| Q1 | Tabletop Exercise | Database corruption | 2 hours |
| Q2 | Simulated Recovery | Data center failure | 4 hours |
| Q3 | Full DR Test | Complete system recovery | 8 hours |
| Q4 | Red Team Exercise | Security breach simulation | 16 hours |

### Success Criteria

**Must Pass:**
- [ ] Database restored with < 1% data loss
- [ ] RTO met (< 2 hours)
- [ ] RPO met (< 1 hour)
- [ ] All services operational
- [ ] Blockchain integration working
- [ ] User authentication functional

**Should Pass:**
- [ ] Monitoring re-enabled
- [ ] Logs archived
- [ ] Documentation updated
- [ ] Team debriefed

---

## Contact Information

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| DR Lead | TBD | +1-XXX-XXX-XXXX | dr-lead@haventoken.com |
| DevOps Lead | TBD | +1-XXX-XXX-XXXX | devops@haventoken.com |
| Security Lead | TBD | +1-XXX-XXX-XXXX | security@haventoken.com |
| CTO | TBD | +1-XXX-XXX-XXXX | cto@haventoken.com |

### Escalation Path

1. **Level 1:** On-call engineer (PagerDuty)
2. **Level 2:** DevOps lead
3. **Level 3:** CTO + Security lead
4. **Level 4:** CEO + Board

### External Partners

- **AWS Support:** Premium Support (24/7)
- **Database Consultants:** PostgreSQL Experts
- **Security Firm:** TBD
- **Legal Counsel:** TBD

---

## Backup Monitoring

### Automated Alerts

```bash
# Cron job to monitor backup status
0 3 * * * /opt/haven/scripts/check_backup_health.sh

# Alert on failures via:
# - PagerDuty
# - Slack #ops-alerts
# - Email: ops@haventoken.com
```

### Metrics to Monitor

- Backup success rate (target: 100%)
- Backup duration (target: < 30 minutes)
- Backup size trend
- Restore test success rate (target: 100%)
- Time since last successful backup (alert if > 25 hours)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-08 | 1.0 | Initial disaster recovery plan | DevOps Team |

---

## Appendix

### A. Backup File Naming Convention

```
Format: haven_{type}_{date}_{time}.sql.gz[.gpg]

Examples:
- haven_full_20250108_020000.sql.gz
- haven_incremental_20250108_140000.sql.gz.gpg
- haven_pre_restore_20250108_153045.sql.gz
```

### B. Required Tools & Access

**Software:**
- PostgreSQL client (psql, pg_dump, pg_restore)
- AWS CLI (with S3 access)
- GPG (with decryption keys)
- Docker & Docker Compose
- Terraform
- Hardhat/Node.js

**Access Required:**
- Database credentials (master user)
- AWS credentials (S3, EC2, RDS)
- GPG decryption keys
- Smart contract deployer private key
- GitHub repository access

### C. Pre-Disaster Checklist

- [ ] Backups running successfully
- [ ] Backup verification passing
- [ ] DR environment tested monthly
- [ ] Contact list up to date
- [ ] Documentation current
- [ ] Team trained on procedures
- [ ] Encryption keys accessible
- [ ] Secondary region configured
- [ ] Monitoring alerts configured
- [ ] Communication templates prepared

### D. Post-Disaster Checklist

- [ ] Root cause identified
- [ ] Recovery documented
- [ ] Post-mortem completed
- [ ] Lessons learned shared
- [ ] Procedures updated
- [ ] Prevention measures implemented
- [ ] Stakeholders notified
- [ ] Compensation issued (if applicable)
- [ ] Security review conducted
- [ ] Monitoring enhanced

---

**Document Review Schedule:** Quarterly or after any disaster recovery event

**Next Review Date:** 2025-04-08

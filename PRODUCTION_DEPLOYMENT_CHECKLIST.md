# HAVEN Token - Production Deployment Checklist

## Pre-Deployment Checklist

### 1. Environment Configuration

#### Redis Setup
- [ ] Production Redis instance provisioned
- [ ] Redis authentication configured (password/TLS)
- [ ] Redis persistence enabled (RDB + AOF)
- [ ] Redis backup strategy implemented
- [ ] Connection pooling configured
- [ ] Redis monitoring enabled
- [ ] `REDIS_URL` environment variable set

#### Database
- [ ] PostgreSQL production instance ready
- [ ] Database migrations tested in staging
- [ ] Backup and recovery procedures tested
- [ ] Connection pooling configured
- [ ] Database monitoring enabled
- [ ] `DATABASE_URL` environment variable set

#### Security Keys
- [ ] Wallet encryption key generated (Fernet)
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] Admin API key generated (secure random)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Keys stored securely (KMS/secrets manager)
- [ ] Key rotation policy established
- [ ] `WALLET_ENCRYPTION_KEY` environment variable set
- [ ] `ADMIN_API_KEY` environment variable set

#### KMS Integration (Recommended)
- [ ] KMS provider selected (AWS KMS, GCP KMS, Azure Key Vault)
- [ ] KMS key created for wallet encryption
- [ ] Service principal/IAM role configured
- [ ] KMS integration tested
- [ ] `KMS_ENABLED=true` environment variable set
- [ ] `KMS_KEY_ID` environment variable set

---

### 2. Alerting Configuration

#### Email Alerts
- [ ] SMTP service selected (SendGrid, AWS SES, Gmail, etc.)
- [ ] SMTP credentials configured
- [ ] Email templates tested
- [ ] Recipient list configured
- [ ] Email delivery tested in staging
- [ ] `ALERT_EMAIL_ENABLED=true` set
- [ ] SMTP environment variables set:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASSWORD`
  - `ALERT_FROM_EMAIL`
  - `ALERT_TO_EMAILS`

#### Webhook Alerts
- [ ] Webhook endpoints configured (Slack, PagerDuty, etc.)
- [ ] Webhook authentication configured
- [ ] Webhook delivery tested
- [ ] Webhook retry logic verified
- [ ] `ALERT_WEBHOOK_ENABLED=true` set
- [ ] `ALERT_WEBHOOK_URLS` environment variable set

#### Alert Routing
- [ ] Critical alerts routed to on-call
- [ ] Warning alerts routed to monitoring team
- [ ] Info alerts logged only
- [ ] Alert escalation policy defined
- [ ] On-call schedule configured

---

### 3. Database Migrations

#### Migration Files
- [ ] Review all new table definitions:
  - `wallet_custody`
  - `wallet_audit_logs`
  - `alert_logs`
  - `error_logs`
- [ ] Alembic migration generated
  ```bash
  alembic revision --autogenerate -m "Add security and monitoring tables"
  ```
- [ ] Migration tested in staging
- [ ] Rollback plan prepared
- [ ] Migration executed in production
  ```bash
  alembic upgrade head
  ```

#### Index Verification
- [ ] Verify indexes created on:
  - `wallet_custody.wallet_id`
  - `wallet_custody.wallet_address`
  - `wallet_custody.status`
  - `wallet_audit_logs.wallet_id`
  - `wallet_audit_logs.severity`
  - `alert_logs.severity`
  - `alert_logs.category`
  - `error_logs.error_type`
  - `error_logs.user_id`

---

### 4. Application Integration

#### Code Integration
- [ ] Update `app.py` with service initialization (see IMPLEMENTATION_GUIDE.md)
- [ ] Update `token_agent.py` to use nonce manager
- [ ] Update `token_agent.py` to use circuit breakers
- [ ] Add exception handlers to FastAPI app
- [ ] Include admin router in FastAPI app
- [ ] Verify all imports work correctly

#### Dependency Installation
- [ ] All Python dependencies installed
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Verify versions match:
  - redis==5.0.1
  - cryptography==41.0.7
  - httpx==0.25.2

#### Service Initialization
- [ ] Nonce manager initialization tested
- [ ] Wallet custody service initialization tested
- [ ] Alerting service initialization tested
- [ ] Transaction monitor initialization tested
- [ ] Circuit breakers registered and tested

---

### 5. Testing

#### Unit Tests
- [ ] All unit tests passing
  ```bash
  pytest backend/tests/ -v
  ```
- [ ] Test coverage > 80%
  ```bash
  pytest backend/tests/ --cov=backend --cov-report=html
  ```

#### Integration Tests
- [ ] Nonce management tested under load
- [ ] Wallet creation/rotation tested
- [ ] Circuit breaker failover tested
- [ ] Alert delivery tested (email + webhooks)
- [ ] Transaction monitoring tested
- [ ] Admin API endpoints tested

#### Staging Environment
- [ ] Full deployment tested in staging
- [ ] End-to-end transaction flow tested
- [ ] Error handling scenarios tested
- [ ] Alert delivery verified
- [ ] Performance benchmarks met

---

### 6. Monitoring & Observability

#### Application Monitoring
- [ ] Health check endpoint updated with circuit breaker status
- [ ] Metrics collection enabled
- [ ] Dashboards configured for:
  - Transaction monitoring
  - Circuit breaker status
  - Nonce manager health
  - Alert delivery status
- [ ] Log aggregation configured (ELK, Datadog, etc.)

#### Alerts & Notifications
- [ ] Alert thresholds configured:
  - Pending transaction threshold (default: 5 minutes)
  - Gas spike threshold (default: 2x)
  - Circuit breaker failure threshold (default: 5)
- [ ] Alert notification channels tested
- [ ] On-call escalation tested

#### Database Monitoring
- [ ] Database performance monitoring enabled
- [ ] Query performance analyzed
- [ ] Connection pool monitoring enabled
- [ ] Slow query alerts configured

---

### 7. Security Hardening

#### Access Control
- [ ] Admin API endpoints restricted to authorized IPs
- [ ] HTTPS enforced for all endpoints
- [ ] API key rotation policy implemented
- [ ] Rate limiting configured on admin endpoints
- [ ] CORS configured properly

#### Audit Logging
- [ ] All wallet operations logged
- [ ] Private key access events logged with HIGH severity
- [ ] Admin actions logged
- [ ] Audit log retention policy defined
- [ ] Audit log review process established

#### Secrets Management
- [ ] Encryption keys stored in secrets manager
- [ ] Database credentials rotated
- [ ] API keys rotated
- [ ] SMTP credentials secured
- [ ] Environment variables secured

#### Network Security
- [ ] Redis access restricted (VPC/firewall)
- [ ] Database access restricted (VPC/firewall)
- [ ] Admin API accessible only from secure network
- [ ] TLS/SSL enabled for all external connections

---

### 8. Performance Optimization

#### Redis Performance
- [ ] Connection pooling configured (10-20 connections)
- [ ] Pipeline operations where possible
- [ ] TTL set on temporary keys
- [ ] Memory limits configured
- [ ] Eviction policy set

#### Database Performance
- [ ] Connection pooling configured (20-50 connections)
- [ ] Prepared statements used
- [ ] Indexes optimized
- [ ] Query performance analyzed
- [ ] Database vacuum scheduled

#### Circuit Breaker Tuning
- [ ] Failure thresholds tuned based on observed patterns
- [ ] Timeout values optimized
- [ ] Success thresholds validated
- [ ] Recovery testing frequency appropriate

#### Transaction Monitor Tuning
- [ ] Monitoring frequency optimized (1-minute default)
- [ ] Gas price baseline updated regularly
- [ ] Alert batching configured if needed

---

### 9. Operational Procedures

#### Incident Response
- [ ] Runbook created for common incidents:
  - High pending transaction count
  - Circuit breaker stuck open
  - Nonce errors
  - Failed alerts
- [ ] Escalation procedures documented
- [ ] On-call rotation established
- [ ] Incident response training completed

#### Maintenance Procedures
- [ ] Regular audit log review scheduled (weekly)
- [ ] Wallet operation review scheduled (weekly)
- [ ] Alert threshold review scheduled (monthly)
- [ ] Performance optimization review scheduled (monthly)
- [ ] Security audit scheduled (quarterly)

#### Backup & Recovery
- [ ] Database backup tested
- [ ] Redis backup tested
- [ ] Wallet custody table backup verified
- [ ] Encryption key backup secured
- [ ] Disaster recovery plan documented
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined

---

### 10. Documentation

#### Technical Documentation
- [ ] Implementation guide reviewed
- [ ] API documentation updated
- [ ] Architecture diagrams created
- [ ] Sequence diagrams for critical flows
- [ ] Configuration reference complete

#### Operational Documentation
- [ ] Runbooks created for:
  - Deployment procedures
  - Incident response
  - Routine maintenance
  - Troubleshooting guide
- [ ] Admin API usage guide
- [ ] Monitoring dashboard guide

#### Training
- [ ] Development team trained on new components
- [ ] Operations team trained on monitoring and alerts
- [ ] Security team briefed on custody and encryption
- [ ] On-call team trained on incident response

---

### 11. Go-Live Readiness

#### Pre-Launch Verification
- [ ] All environment variables set and verified
- [ ] All services initialized successfully
- [ ] Health check returns healthy status
- [ ] Test transaction processed successfully
- [ ] Test alert sent successfully
- [ ] Circuit breaker responds correctly to failures
- [ ] Nonce manager handling transactions correctly
- [ ] Wallet custody operations working
- [ ] Admin API accessible and secured

#### Launch Day Checklist
- [ ] Deployment scheduled during low-traffic window
- [ ] On-call team notified and standing by
- [ ] Rollback plan ready
- [ ] Monitoring dashboards open
- [ ] Communication channels ready (Slack, etc.)
- [ ] Stakeholders notified

#### Post-Launch Monitoring (First 24 Hours)
- [ ] Monitor error rates
- [ ] Monitor transaction success rates
- [ ] Monitor alert delivery
- [ ] Monitor circuit breaker status
- [ ] Monitor nonce manager performance
- [ ] Monitor database performance
- [ ] Monitor Redis performance
- [ ] Review audit logs
- [ ] Check for any security anomalies

---

### 12. Post-Deployment Tasks

#### First Week
- [ ] Review all error logs
- [ ] Analyze alert patterns
- [ ] Tune circuit breaker thresholds if needed
- [ ] Optimize monitoring frequency if needed
- [ ] Review wallet operations
- [ ] Performance benchmark comparison

#### First Month
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Alert threshold optimization
- [ ] Documentation updates based on learnings
- [ ] Team retrospective on deployment

---

## Production Environment Variables Template

```bash
# Core Services
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@db-host:5432/haven_prod
REDIS_URL=redis://:password@redis-host:6379

# Blockchain
RPC_URL=https://mainnet.base.org
CHAIN_ID=8453
HAVEN_CONTRACT_ADDRESS=0x...
BACKEND_PRIVATE_KEY=0x...

# Security - Wallet Custody
WALLET_ENCRYPTION_KEY=<fernet-key-from-kms>
KMS_ENABLED=true
KMS_KEY_ID=arn:aws:kms:region:account:key/xxx

# Security - Admin API
ADMIN_API_KEY=<secure-random-key>
API_KEY=<secure-random-key>

# Alerting - Email
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
ALERT_FROM_EMAIL=alerts@haven.com
ALERT_TO_EMAILS=ops@haven.com,security@haven.com

# Alerting - Webhooks
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URLS=https://hooks.slack.com/services/xxx,https://pagerduty.com/integration/xxx

# Monitoring Configuration
PENDING_TX_THRESHOLD_MINUTES=5
GAS_SPIKE_THRESHOLD=2.0

# CORS
ALLOWED_ORIGINS=https://app.haven.com,https://admin.haven.com

# Server
PORT=8000
WORKERS=4
```

---

## Success Criteria

Deployment is considered successful when:

- [ ] All health checks passing for 24 hours
- [ ] Zero critical errors in error logs
- [ ] Transaction success rate > 99%
- [ ] Alert delivery working 100%
- [ ] Circuit breakers functioning correctly
- [ ] Nonce manager handling all transactions without conflicts
- [ ] Wallet operations proceeding normally
- [ ] No security incidents
- [ ] Performance within acceptable thresholds
- [ ] Team confident in system stability

---

## Rollback Plan

If critical issues are encountered:

1. **Immediate Actions:**
   - [ ] Stop new deployments
   - [ ] Assess severity and impact
   - [ ] Notify stakeholders

2. **Rollback Steps:**
   - [ ] Revert application to previous version
   - [ ] Rollback database migrations if needed
   - [ ] Restore Redis state if needed
   - [ ] Verify health after rollback
   - [ ] Communicate status

3. **Post-Rollback:**
   - [ ] Root cause analysis
   - [ ] Fix issues in staging
   - [ ] Re-test thoroughly
   - [ ] Plan re-deployment

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Developer | | | |
| Security Lead | | | |
| DevOps Lead | | | |
| Product Owner | | | |

---

**Document Version:** 1.0
**Last Updated:** November 8, 2025
**Next Review:** Post-deployment + 1 week

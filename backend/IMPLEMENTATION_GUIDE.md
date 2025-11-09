# HAVEN Token - Critical Security & Stability Enhancements Implementation Guide

## Overview

This guide documents the implementation of 5 critical security and stability enhancements for the HAVEN Token backend system.

## Implemented Components

### CR-1: Nonce Management System
**Location:** `backend/services/nonce_manager.py`

**Features:**
- Redis-backed nonce tracking per wallet
- Distributed lock mechanism to prevent race conditions
- Automatic synchronization with blockchain state
- Nonce recovery for failed transactions
- Atomic nonce reservation for transaction building

**Usage:**
```python
from services.nonce_manager import init_nonce_manager, get_nonce_manager

# Initialize (in app.py startup)
nonce_manager = init_nonce_manager(
    redis_url="redis://localhost:6379",
    w3=w3_instance,
    lock_timeout=30
)

# Use in transaction processing
nonce = nonce_manager.reserve_nonce(wallet_address)
# ... build and send transaction ...
# On error:
corrected_nonce = nonce_manager.handle_nonce_error(wallet_address, failed_nonce)
```

**Key Methods:**
- `reserve_nonce(wallet_address)` - Atomically get and increment nonce
- `reset_nonce(wallet_address)` - Reset to blockchain state
- `handle_nonce_error(wallet_address, failed_nonce)` - Recover from nonce errors
- `get_status(wallet_address)` - Get nonce status for debugging

---

### CR-2: Wallet Custody Management
**Location:** `backend/services/wallet_custody.py`, `backend/api/admin.py`

**Features:**
- Fernet encryption for private key storage
- KMS integration support
- Secure wallet creation and retrieval
- Wallet rotation capability
- Comprehensive audit logging

**Usage:**
```python
from services.wallet_custody import init_wallet_custody_service, get_wallet_custody_service

# Initialize (in app.py startup)
custody_service = init_wallet_custody_service(
    encryption_key=os.getenv("WALLET_ENCRYPTION_KEY"),
    db_session=db,
    kms_enabled=False
)

# Create wallet
wallet = custody_service.create_wallet(
    wallet_id="user_123",
    metadata={"user_type": "premium"}
)

# Get wallet (without private key)
wallet_info = custody_service.get_wallet(wallet_id="user_123")

# Get private key (use with extreme caution - logs audit event)
private_key = custody_service.get_private_key(wallet_id="user_123")

# Rotate wallet
new_wallet = custody_service.rotate_wallet(wallet_id="user_123")
```

**Admin API Endpoints:**
- `POST /api/v1/admin/wallets` - Create wallet
- `GET /api/v1/admin/wallets/{wallet_id}` - Get wallet info
- `GET /api/v1/admin/wallets` - List all wallets
- `POST /api/v1/admin/wallets/{wallet_id}/rotate` - Rotate wallet
- `POST /api/v1/admin/wallets/{wallet_id}/revoke` - Revoke wallet
- `GET /api/v1/admin/audit/wallet-logs` - Get audit logs

**Security Notes:**
- Private keys are encrypted with Fernet (symmetric encryption)
- All wallet operations are logged to audit trail
- Private key access is logged with HIGH severity
- Supports KMS integration for enhanced key management

---

### CR-3: Transaction Monitoring & Alerting
**Location:** `backend/services/transaction_monitor.py`, `backend/services/alerting.py`

**Features:**
- Real-time monitoring of pending transactions (>5 min threshold)
- Failed transaction detection and alerting
- Gas price spike detection
- Email and webhook alert delivery
- Database logging of all alerts

**Usage:**
```python
from services.alerting import init_alerting_service
from services.transaction_monitor import init_transaction_monitor

# Initialize alerting service
alerting_service = init_alerting_service(
    db_session=db,
    email_enabled=True,
    email_config={
        'smtp_host': os.getenv('SMTP_HOST'),
        'smtp_port': os.getenv('SMTP_PORT'),
        'smtp_user': os.getenv('SMTP_USER'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'from_email': os.getenv('ALERT_FROM_EMAIL'),
        'to_emails': os.getenv('ALERT_TO_EMAILS')
    },
    webhook_enabled=True,
    webhook_urls=[os.getenv('ALERT_WEBHOOK_URL')]
)

# Initialize transaction monitor
monitor = init_transaction_monitor(
    db_session=db,
    w3=w3,
    alerting_service=alerting_service,
    pending_threshold_minutes=5,
    gas_spike_threshold_multiplier=2.0
)

# Run monitoring cycle (schedule this periodically)
await monitor.run_monitoring_cycle()
```

**Scheduled Tasks:**
Add to your scheduler (APScheduler):
```python
scheduler.add_job(
    monitor.run_monitoring_cycle,
    "interval",
    minutes=1,
    id="transaction_monitoring"
)
```

**Alert Categories:**
- `transaction_pending` - Transaction stuck in pending
- `transaction_failed` - Transaction failed
- `gas_price_spike` - Gas price exceeded threshold

**Admin Endpoints:**
- `GET /api/v1/admin/transactions/status` - Get monitoring dashboard
- `POST /api/v1/admin/transactions/{tx_id}/retry` - Retry failed transaction

---

### CR-4: Circuit Breaker Pattern
**Location:** `backend/middleware/circuit_breaker.py`

**Features:**
- Three states: CLOSED, OPEN, HALF_OPEN
- Configurable thresholds and timeouts
- Redis-backed state management
- Automatic recovery testing
- Health status reporting

**Configuration:**
- Failure threshold: 5 failures → OPEN
- Success threshold: 2 successes → CLOSED
- Timeout: 30 seconds before HALF_OPEN attempt

**Usage:**
```python
from middleware.circuit_breaker import (
    register_circuit_breaker,
    CircuitBreakerConfig,
    get_circuit_breaker
)

# Initialize circuit breakers (in app.py startup)
blockchain_cb = register_circuit_breaker(
    name="blockchain",
    redis_client=redis_client,
    config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=30
    )
)

# Use in token_agent.py
def get_balance(self, wallet_address: str) -> float:
    circuit_breaker = get_circuit_breaker("blockchain")
    return circuit_breaker.call(self._get_balance_impl, wallet_address)

# Or use as decorator
from middleware.circuit_breaker import circuit_breaker

@circuit_breaker("blockchain")
def blockchain_operation():
    # ... operation ...
    pass
```

**Admin Endpoints:**
- `GET /api/v1/admin/health/circuit-breakers` - Get all circuit breaker statuses
- `POST /api/v1/admin/health/circuit-breakers/{name}/reset` - Manually reset circuit breaker

**Health Check Integration:**
Update `/health` endpoint to include circuit breaker status:
```python
@app.get("/health")
async def health_check():
    from middleware.circuit_breaker import get_all_statuses

    cb_statuses = get_all_statuses()

    return {
        "status": "healthy",
        "circuit_breakers": cb_statuses,
        # ... other health checks ...
    }
```

---

### CR-5: Comprehensive Error Handling
**Location:** `backend/exceptions.py`, `backend/middleware/error_handler.py`

**Features:**
- Hierarchical exception structure
- Structured error responses with error codes
- User-friendly error messages
- Context-aware error logging
- Database error logging for audit

**Exception Hierarchy:**
- `HAVENBaseException` - Base for all custom exceptions
  - `BlockchainError` - Blockchain-related errors
    - `ConnectionError`, `TransactionError`, `NonceError`, etc.
  - `ValidationError` - Input validation errors
    - `InvalidAddressError`, `InvalidAmountError`, etc.
  - `BusinessLogicError` - Business logic errors
    - `UserNotFoundError`, `DuplicateTransactionError`, etc.
  - `SystemError` - System-level errors
    - `DatabaseError`, `RedisError`, `CircuitBreakerOpenError`, etc.
  - `AuthenticationError`, `AuthorizationError` - Auth errors
  - `WalletCustodyError` - Wallet custody errors

**Usage:**
```python
from exceptions import (
    InsufficientBalanceError,
    UserNotFoundError,
    ValidationError
)

# Raise exceptions
if balance < amount:
    raise InsufficientBalanceError(
        message="Insufficient balance for transaction",
        wallet_address=wallet_address,
        required_amount=amount,
        available_amount=balance
    )

# Exception handler integration (in app.py)
from middleware.error_handler import haven_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException

app.add_exception_handler(HAVENBaseException, haven_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
```

**Error Response Format:**
```json
{
  "error": "INSUFFICIENT_BALANCE",
  "message": "Insufficient balance for transaction",
  "user_message": "Insufficient HAVEN balance. Required: 100, Available: 50",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "req_123",
  "timestamp": "2025-11-08T10:30:00Z",
  "details": {
    "wallet_address": "0x123...",
    "required_amount": 100,
    "available_amount": 50,
    "token_type": "HAVEN"
  }
}
```

---

## Integration Steps

### 1. Update app.py

Add to startup section:

```python
import os
import redis
from services.nonce_manager import init_nonce_manager
from services.wallet_custody import init_wallet_custody_service
from services.alerting import init_alerting_service
from services.transaction_monitor import init_transaction_monitor
from middleware.circuit_breaker import register_circuit_breaker, CircuitBreakerConfig
from middleware.error_handler import haven_exception_handler
from exceptions import HAVENBaseException

# Initialize Redis
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("🚀 Starting HAVEN Token API...")

    # Initialize services
    from services.token_agent import token_agent

    # Nonce Manager
    nonce_manager = init_nonce_manager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        w3=token_agent.w3,
        lock_timeout=30
    )

    # Wallet Custody
    custody_service = init_wallet_custody_service(
        encryption_key=os.getenv("WALLET_ENCRYPTION_KEY"),
        db_session=SessionLocal(),
        kms_enabled=os.getenv("KMS_ENABLED", "false").lower() == "true",
        kms_key_id=os.getenv("KMS_KEY_ID")
    )

    # Alerting Service
    alerting_service = init_alerting_service(
        db_session=SessionLocal(),
        email_enabled=os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
        email_config={
            'smtp_host': os.getenv('SMTP_HOST'),
            'smtp_port': os.getenv('SMTP_PORT', '587'),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL'),
            'to_emails': os.getenv('ALERT_TO_EMAILS')
        },
        webhook_enabled=os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
        webhook_urls=os.getenv("ALERT_WEBHOOK_URLS", "").split(",") if os.getenv("ALERT_WEBHOOK_URLS") else []
    )

    # Transaction Monitor
    monitor = init_transaction_monitor(
        db_session=SessionLocal(),
        w3=token_agent.w3,
        alerting_service=alerting_service,
        pending_threshold_minutes=int(os.getenv("PENDING_TX_THRESHOLD_MINUTES", "5")),
        gas_spike_threshold_multiplier=float(os.getenv("GAS_SPIKE_THRESHOLD", "2.0"))
    )

    # Circuit Breakers
    register_circuit_breaker(
        name="blockchain",
        redis_client=redis_client,
        config=CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=30
        )
    )

    # Schedule monitoring
    scheduler.add_job(
        monitor.run_monitoring_cycle,
        "interval",
        minutes=1,
        id="transaction_monitoring"
    )

    # ... existing jobs ...

    scheduler.start()
    logger.info("✅ All services initialized")

    yield

    logger.info("🛑 Shutting down HAVEN Token API...")
    scheduler.shutdown()

# Register exception handlers
app.add_exception_handler(HAVENBaseException, haven_exception_handler)

# Include admin router
from api import admin
app.include_router(admin.router)
```

### 2. Update token_agent.py

Integrate nonce manager and circuit breaker:

```python
from services.nonce_manager import get_nonce_manager
from middleware.circuit_breaker import get_circuit_breaker
from exceptions import TransactionError, NonceError, InsufficientBalanceError

async def process_mint(self, tx_id: str, user_id: str, amount: float, reason: str, db: Session):
    """Process mint with nonce management and circuit breaker."""
    try:
        # ... existing code ...

        # Use nonce manager
        nonce_manager = get_nonce_manager()
        nonce = nonce_manager.reserve_nonce(self.account.address)

        # Build transaction with reserved nonce
        mint_tx = self.contract.functions.mint(
            wallet_address,
            amount_wei,
            reason
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            # ... rest of tx params ...
        })

        # Wrap blockchain calls in circuit breaker
        circuit_breaker = get_circuit_breaker("blockchain")
        tx_hash = circuit_breaker.call(
            self.w3.eth.send_raw_transaction,
            signed_tx.rawTransaction
        )

        # ... rest of implementation ...

    except Exception as e:
        # Handle nonce errors
        if "nonce" in str(e).lower():
            corrected_nonce = nonce_manager.handle_nonce_error(
                self.account.address,
                nonce
            )
            raise NonceError(
                message=f"Nonce error: {str(e)}",
                wallet_address=self.account.address,
                expected_nonce=nonce,
                actual_nonce=corrected_nonce
            )
        raise TransactionError(f"Mint transaction failed: {str(e)}")
```

### 3. Update .env

Add new environment variables:

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Wallet Custody
WALLET_ENCRYPTION_KEY=<base64-encoded-fernet-key>
KMS_ENABLED=false
KMS_KEY_ID=

# Alerting
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@haven.com
SMTP_PASSWORD=<password>
ALERT_FROM_EMAIL=alerts@haven.com
ALERT_TO_EMAILS=admin@haven.com,ops@haven.com

ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URLS=https://hooks.slack.com/services/xxx,https://webhook.site/xxx

# Monitoring
PENDING_TX_THRESHOLD_MINUTES=5
GAS_SPIKE_THRESHOLD=2.0

# Admin API
ADMIN_API_KEY=<secure-random-key>
```

### 4. Run Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test files
pytest backend/tests/test_nonce_manager.py -v
pytest backend/tests/test_wallet_custody.py -v
pytest backend/tests/test_circuit_breaker.py -v
pytest backend/tests/test_exceptions.py -v
pytest backend/tests/test_alerting.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### 5. Database Migrations

Create migration for new tables:

```bash
# Generate migration
alembic revision --autogenerate -m "Add security and monitoring tables"

# Review and apply
alembic upgrade head
```

New tables created:
- `wallet_custody` - Encrypted wallet storage
- `wallet_audit_logs` - Wallet operation audit trail
- `alert_logs` - Alert history
- `error_logs` - Error logging for debugging

---

## Security Considerations

1. **Wallet Encryption Key**: Generate a secure Fernet key and store it securely (KMS recommended for production)
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```

2. **Admin API Key**: Use a strong random key for admin endpoints
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

3. **Redis Security**: Use password-protected Redis and TLS in production

4. **Alert Webhooks**: Validate webhook endpoints and use HTTPS

5. **Database Access**: Ensure error logs and wallet custody tables have restricted access

---

## Monitoring & Observability

### Key Metrics to Monitor

1. **Nonce Management**
   - Nonce sync errors
   - Lock contention
   - Nonce reset frequency

2. **Circuit Breakers**
   - Open/half-open state frequency
   - Failure rates
   - Recovery times

3. **Transaction Monitoring**
   - Pending transaction count
   - Failed transaction rate
   - Gas price trends

4. **Wallet Custody**
   - Wallet creation rate
   - Private key access events
   - Rotation frequency

### Health Checks

Enhanced health endpoint should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "blockchain": "connected",
  "redis": "connected",
  "circuit_breakers": {
    "blockchain": {
      "state": "closed",
      "failure_count": 0
    }
  },
  "monitoring": {
    "pending_transactions": 2,
    "stuck_transactions": 0,
    "gas_price_gwei": 0.001
  }
}
```

---

## Troubleshooting

### Common Issues

1. **Nonce too low errors**
   - Check nonce sync with blockchain
   - Use admin endpoint to reset nonce
   - Verify Redis connectivity

2. **Circuit breaker stuck open**
   - Check underlying service health
   - Review failure logs
   - Manually reset if service recovered

3. **Wallet decryption errors**
   - Verify encryption key hasn't changed
   - Check KMS connectivity if enabled
   - Review audit logs for anomalies

4. **Alerts not sending**
   - Verify email/webhook configuration
   - Check SMTP connectivity
   - Review alert logs for errors

---

## Performance Considerations

1. **Redis Connection Pooling**: Use connection pooling for Redis to handle high concurrency

2. **Nonce Lock Timeout**: Adjust lock timeout based on average transaction time

3. **Circuit Breaker Thresholds**: Tune thresholds based on observed failure patterns

4. **Monitoring Frequency**: Balance monitoring frequency with system load

---

## Maintenance

### Regular Tasks

1. **Review Alert Logs** (Daily)
   - Check for recurring issues
   - Adjust alert thresholds if needed

2. **Audit Wallet Operations** (Weekly)
   - Review wallet audit logs
   - Check for unauthorized access attempts

3. **Circuit Breaker Analysis** (Weekly)
   - Analyze failure patterns
   - Adjust thresholds if needed

4. **Nonce Health Check** (Weekly)
   - Review nonce sync issues
   - Clear stale locks if any

### Backup & Recovery

1. **Wallet Custody Backups**
   - Encrypted wallet storage should be backed up securely
   - Store encryption keys separately (use KMS)

2. **Redis Persistence**
   - Configure Redis persistence for nonce data
   - Regular backups of Redis data

---

## Support & Documentation

- Implementation Guide: This document
- API Documentation: See `/docs` endpoint (Swagger UI)
- Test Examples: See `backend/tests/` directory
- Exception Reference: See `backend/exceptions.py`

---

## Version History

- v1.0.0 (2025-11-08): Initial implementation of all 5 critical enhancements

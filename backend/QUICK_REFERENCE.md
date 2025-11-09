# HAVEN Token Backend - Quick Reference Guide

## Common Tasks & Code Snippets

### Nonce Management

```python
from services.nonce_manager import get_nonce_manager

# Get next nonce for transaction
nonce_manager = get_nonce_manager()
nonce = nonce_manager.reserve_nonce(wallet_address)

# Build and send transaction
tx = contract.functions.mint(...).build_transaction({
    'nonce': nonce,
    # ... other params
})

# On transaction error
try:
    # ... send transaction
except Exception as e:
    if "nonce" in str(e).lower():
        corrected_nonce = nonce_manager.handle_nonce_error(wallet_address, nonce)
```

### Wallet Custody

```python
from services.wallet_custody import get_wallet_custody_service

custody = get_wallet_custody_service()

# Create new wallet
wallet = custody.create_wallet(
    wallet_id=user_id,
    metadata={"user_type": "premium"}
)

# Get wallet (safe - no private key)
wallet_info = custody.get_wallet(wallet_id=user_id)

# Get private key (CAUTION - logs audit event)
private_key = custody.get_private_key(wallet_id=user_id)
```

### Circuit Breaker

```python
from middleware.circuit_breaker import get_circuit_breaker

# Wrap risky blockchain calls
circuit_breaker = get_circuit_breaker("blockchain")

try:
    result = circuit_breaker.call(risky_function, arg1, arg2)
except CircuitBreakerOpenError:
    # Service is down, fail gracefully
    return {"status": "service_unavailable"}
```

### Exception Handling

```python
from exceptions import (
    InsufficientBalanceError,
    UserNotFoundError,
    ValidationError
)

# Raise exceptions with context
if balance < amount:
    raise InsufficientBalanceError(
        message="Insufficient balance",
        wallet_address=address,
        required_amount=amount,
        available_amount=balance
    )

# Exceptions auto-convert to proper HTTP responses
```

### Alerting

```python
from services.alerting import get_alerting_service, Alert, AlertSeverity

alerting = get_alerting_service()

# Send alert
alert = Alert(
    title="Critical Issue",
    message="Transaction failed after 3 retries",
    severity=AlertSeverity.CRITICAL,
    category="transaction_failed",
    data={"tx_id": tx_id, "user_id": user_id}
)

await alerting.send_alert(alert)
```

### Admin API Authentication

```bash
# All admin endpoints require X-Admin-Key header
curl -X GET http://localhost:8000/api/v1/admin/wallets \
  -H "X-Admin-Key: your-admin-key"
```

## Environment Variables Quick Reference

```bash
# Core Services
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost:5432/haven

# Security
WALLET_ENCRYPTION_KEY=<fernet-key>
ADMIN_API_KEY=<secure-key>

# Alerting (optional)
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_USER=alerts@haven.com
SMTP_PASSWORD=<password>
ALERT_TO_EMAILS=admin@haven.com

ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URLS=https://hooks.slack.com/xxx

# Monitoring Thresholds
PENDING_TX_THRESHOLD_MINUTES=5
GAS_SPIKE_THRESHOLD=2.0
```

## Testing Commands

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_nonce_manager.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run single test
pytest backend/tests/test_wallet_custody.py::TestWalletCustodyService::test_create_wallet -v
```

## Admin API Endpoints

### Wallet Management
- `POST /api/v1/admin/wallets` - Create wallet
- `GET /api/v1/admin/wallets/{wallet_id}` - Get wallet
- `GET /api/v1/admin/wallets` - List wallets
- `POST /api/v1/admin/wallets/{wallet_id}/rotate` - Rotate wallet
- `POST /api/v1/admin/wallets/{wallet_id}/revoke` - Revoke wallet

### Transaction Monitoring
- `GET /api/v1/admin/transactions/status` - Monitoring dashboard
- `POST /api/v1/admin/transactions/{tx_id}/retry` - Retry failed tx

### System Health
- `GET /api/v1/admin/health/circuit-breakers` - Circuit breaker status
- `POST /api/v1/admin/health/circuit-breakers/{name}/reset` - Reset circuit
- `GET /api/v1/admin/health/nonce-status/{address}` - Nonce status
- `POST /api/v1/admin/health/nonce-reset/{address}` - Reset nonce

### Audit Logs
- `GET /api/v1/admin/audit/wallet-logs` - Wallet audit logs

## Common Error Codes

- `BLOCKCHAIN_ERROR` - Blockchain connection/operation failed
- `TRANSACTION_ERROR` - Transaction failed
- `NONCE_ERROR` - Nonce mismatch or conflict
- `INSUFFICIENT_BALANCE` - Not enough tokens
- `USER_NOT_FOUND` - User doesn't exist
- `DUPLICATE_TRANSACTION` - Transaction already processed
- `CIRCUIT_BREAKER_OPEN` - Service temporarily unavailable
- `VALIDATION_ERROR` - Invalid input
- `WALLET_NOT_FOUND` - Wallet doesn't exist
- `AUTHENTICATION_ERROR` - Invalid credentials
- `AUTHORIZATION_ERROR` - Insufficient permissions

## Troubleshooting

### Nonce Issues
```bash
# Check nonce status
curl -X GET http://localhost:8000/api/v1/admin/health/nonce-status/0x123... \
  -H "X-Admin-Key: key"

# Reset nonce
curl -X POST http://localhost:8000/api/v1/admin/health/nonce-reset/0x123... \
  -H "X-Admin-Key: key"
```

### Circuit Breaker Issues
```bash
# Check status
curl -X GET http://localhost:8000/api/v1/admin/health/circuit-breakers \
  -H "X-Admin-Key: key"

# Reset circuit
curl -X POST http://localhost:8000/api/v1/admin/health/circuit-breakers/blockchain/reset \
  -H "X-Admin-Key: key"
```

### Transaction Monitoring
```bash
# Get monitoring status
curl -X GET http://localhost:8000/api/v1/admin/transactions/status \
  -H "X-Admin-Key: key"

# Retry failed transaction
curl -X POST http://localhost:8000/api/v1/admin/transactions/tx_123/retry \
  -H "X-Admin-Key: key"
```

## Key Security Notes

1. **NEVER log private keys** - they're only decrypted when absolutely necessary
2. **ALWAYS use HTTPS** in production for admin endpoints
3. **ROTATE admin API keys** regularly
4. **MONITOR audit logs** for suspicious activity
5. **USE KMS** for encryption key management in production
6. **SECURE Redis** with authentication and TLS
7. **LIMIT admin access** to authorized personnel only

## Performance Tips

1. **Redis Connection Pooling** - Use connection pooling for high throughput
2. **Nonce Lock Timeout** - Adjust based on your transaction time
3. **Circuit Breaker Thresholds** - Tune based on observed patterns
4. **Monitoring Frequency** - Balance between real-time and system load
5. **Alert Batching** - Consider batching alerts for high-volume events

## Support Resources

- **Full Documentation:** `/backend/IMPLEMENTATION_GUIDE.md`
- **API Docs:** `http://localhost:8000/docs` (Swagger UI)
- **Test Examples:** `/backend/tests/`
- **Exception Reference:** `/backend/exceptions.py`

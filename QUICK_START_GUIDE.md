# HAVEN Token - Quick Start Guide

## Implementation Complete ✅

All 5 high-priority enhancements have been successfully implemented and verified.

---

## Quick Verification

Run the verification script to confirm implementation:

```bash
cd "/Volumes/DevOPS 2025/01_DEVOPS_PLATFORM/Haven Token"
python backend/verify_implementation.py
```

Expected output: `🎉 ALL CHECKS PASSED - Implementation is complete!`

---

## What Was Implemented

### HP-1: Aurora PMS Integration ✅
**New Methods in `backend/services/aurora_integration.py`:**
- `parseBookingData()` - Normalizes booking webhook data
- `calculateRewardAmount()` - Calculates HNV rewards (2 HNV/CAD, +20% multi-night)
- `handleBookingConfirmation()` - Validates booking data

**Webhooks with Signature Verification:**
- `/webhooks/aurora/booking-created` - Mints rewards
- `/webhooks/aurora/booking-completed` - Updates status
- `/webhooks/aurora/booking-cancelled` - Burns tokens
- `/webhooks/aurora/review-submitted` - Awards 50 HNV bonus

### HP-2: Tribe App Integration ✅
**New Methods in `backend/services/tribe_integration.py`:**
- `parseEventData()` - Normalizes event webhook data
- `calculateAttendanceReward()` - Calculates event rewards (25-100 HNV)
- `handleEventAttendance()` - Validates event data
- `sync_recent_events()` - Daily sync fallback

**Webhooks with Signature Verification:**
- `/webhooks/tribe/event-attendance` - Rewards event participation
- `/webhooks/tribe/contribution` - Rewards community contributions
- `/webhooks/tribe/staking-started` - Records staking
- `/webhooks/tribe/coaching-milestone` - Awards coaching rewards
- `/webhooks/tribe/referral-success` - Distributes referral rewards

**Scheduled Job:**
- Daily event sync at 4 AM (fallback for missed webhooks)

### HP-3: Database Migrations ✅
**Alembic Setup in `backend/alembic/`:**
- 4 migration files (initial schema, Aurora, Tribe, audit log)
- Complete documentation in `alembic/README.md`
- Version-controlled schema changes

**Tables Created:**
- Core: users, transactions, redemptions, metrics
- Aurora: aurora_bookings
- Tribe: tribe_events, tribe_rewards, staking_records
- Compliance: audit_log

### HP-4: Webhook Signature Verification ✅
**Applied to All 9 Webhooks:**
- HMAC-SHA256 signature verification
- Timestamp validation (5-minute window)
- Clock skew tolerance (60 seconds)
- Timing attack resistance
- Replay attack prevention

**Using FastAPI Dependencies:**
```python
verified: bool = Depends(verify_aurora_webhook)
verified: bool = Depends(verify_tribe_webhook)
```

### HP-5: Idempotency Middleware ✅
**Redis-Based Duplicate Prevention:**
- 24-hour request tracking
- Header and body key support
- Graceful Redis fallback
- Applied to `/token/mint` and `/token/redeem`

**Key Features:**
- Configurable TTL
- Database backup for when Redis unavailable
- Required for redemption endpoints

---

## Testing

### Test Coverage: 80+ Tests

**Test Files Created:**
- `backend/tests/test_aurora_integration.py` (15 tests)
- `backend/tests/test_tribe_integration.py` (20 tests)
- `backend/tests/test_idempotency.py` (20 tests)
- `backend/tests/test_webhook_auth.py` (25 tests)

### Run Tests

```bash
cd backend

# All tests
pytest -v

# Specific test file
pytest tests/test_aurora_integration.py -v

# With coverage report
pytest --cov=services --cov=middleware --cov-report=html
```

---

## Deployment

### 1. Prerequisites

**Install Redis:**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

**Create PostgreSQL Database:**
```bash
createdb haven
```

### 2. Environment Variables

Create `backend/.env`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/haven
REDIS_URL=redis://localhost:6379/0
AURORA_WEBHOOK_SECRET=your_aurora_secret_here
TRIBE_WEBHOOK_SECRET=your_tribe_secret_here
API_KEY=your_api_key_here
RPC_URL=https://sepolia.base.org
HAVEN_CONTRACT_ADDRESS=0x...
BACKEND_PRIVATE_KEY=0x...
CHAIN_ID=84532
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

Verify:
```bash
alembic current
# Output: 004 (head)
```

### 5. Start the Server

**Development:**
```bash
uvicorn app:app --reload --port 8000
```

**Production:**
```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 6. Verify Health

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "blockchain": "connected",
  "circulating_supply": 0.0
}
```

---

## Testing Webhooks

### Generate Signature (Python)

```python
from middleware.webhook_auth import generate_webhook_signature
import json

payload = {"id": "booking_123", "guest_id": "guest_001", "total_price": 200.0, "nights": 2}
payload_bytes = json.dumps(payload).encode('utf-8')
headers = generate_webhook_signature(payload_bytes, 'your_aurora_secret_here')

print(f"Signature: {headers['signature']}")
print(f"Timestamp: {headers['timestamp']}")
```

### Test Aurora Webhook

```bash
curl -X POST http://localhost:8000/webhooks/aurora/booking-created \
  -H "Content-Type: application/json" \
  -H "X-Aurora-Signature: <signature>" \
  -H "X-Aurora-Timestamp: <timestamp>" \
  -d '{
    "id": "booking_123",
    "guest_id": "guest_001",
    "guest_email": "test@example.com",
    "total_price": 200.0,
    "nights": 2
  }'
```

Expected:
```json
{"status": "accepted"}
```

### Test Tribe Webhook

```bash
curl -X POST http://localhost:8000/webhooks/tribe/event-attendance \
  -H "Content-Type: application/json" \
  -H "X-Tribe-Signature: <signature>" \
  -H "X-Tribe-Timestamp: <timestamp>" \
  -d '{
    "id": "event_123",
    "attendee_id": "user_001",
    "name": "Weekly Wisdom Circle",
    "type": "wisdom_circle",
    "attended": true
  }'
```

---

## File Structure

```
Haven Token/
├── INTEGRATION_IMPLEMENTATION_SUMMARY.md  # Detailed implementation docs
├── QUICK_START_GUIDE.md                   # This file
├── backend/
│   ├── alembic/                           # Database migrations
│   │   ├── versions/                      # 4 migration files
│   │   ├── env.py
│   │   └── README.md                      # Migration guide
│   ├── alembic.ini                        # Alembic config
│   ├── middleware/
│   │   ├── webhook_auth.py                # Signature verification
│   │   └── idempotency.py                 # Duplicate prevention
│   ├── services/
│   │   ├── aurora_integration.py          # Aurora PMS integration
│   │   ├── tribe_integration.py           # Tribe app integration
│   │   └── token_agent.py                 # Blockchain interactions
│   ├── tests/
│   │   ├── test_aurora_integration.py     # 15 tests
│   │   ├── test_tribe_integration.py      # 20 tests
│   │   ├── test_idempotency.py            # 20 tests
│   │   └── test_webhook_auth.py           # 25 tests
│   ├── verify_implementation.py           # Verification script
│   └── app.py                             # Main FastAPI app
```

---

## Key Features

### Tokenomics Implementation

**Aurora Booking Rewards:**
- Base: 2 HNV per CAD
- Multi-night bonus: +20% for >1 night
- Review bonus: 50 HNV for 4+ star reviews

**Tribe Event Rewards:**
- Wisdom Circle: 100 HNV
- Workshop: 75 HNV
- Networking: 50 HNV
- General: 25 HNV

**Other Rewards:**
- Contributions: 5-25 HNV (with quality multiplier)
- Coaching milestones: 100-250 HNV (tiered)
- Referrals: 100-500 HNV (tiered)
- Staking APY: 10% annual (0.192% weekly)

### Security Features

1. **Webhook Security:**
   - HMAC-SHA256 signatures
   - Timestamp validation
   - Replay attack prevention
   - Constant-time comparison

2. **Idempotency:**
   - Redis-based caching
   - 24-hour TTL
   - Required for redemptions

3. **Audit Trail:**
   - All transactions logged
   - IP tracking
   - User action logging

### Scheduled Jobs

**Automatic Background Tasks:**
- Aurora booking sync: Daily at 2 AM
- Tribe event sync: Daily at 4 AM
- Staking rewards: Weekly Monday at 3 AM

---

## Common Commands

### Database

```bash
# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history --verbose
```

### Testing

```bash
# All tests
pytest -v

# Specific component
pytest tests/test_aurora_integration.py -v

# With coverage
pytest --cov=services --cov=middleware --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Server

```bash
# Development (auto-reload)
uvicorn app:app --reload --port 8000

# Production
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# View application logs
tail -f logs/app.log

# Filter for specific component
tail -f logs/app.log | grep "Aurora"
tail -f logs/app.log | grep "Tribe"
tail -f logs/app.log | grep "Idempotency"
```

### Metrics to Monitor

1. **Webhooks:** Request rate, error rate, response time
2. **Database:** Connection pool, query performance
3. **Redis:** Cache hit rate, memory usage
4. **Tokens:** Minted/burned per day, circulating supply

---

## Troubleshooting

### Issue: Webhook signature verification fails

**Solution:**
```bash
# Check secrets are set
echo $AURORA_WEBHOOK_SECRET
echo $TRIBE_WEBHOOK_SECRET

# Verify signature generation
python -c "from middleware.webhook_auth import generate_webhook_signature; print('OK')"
```

### Issue: Redis connection error

**Solution:**
```bash
# Check Redis is running
redis-cli ping
# Expected: PONG

# Restart if needed
brew services restart redis  # macOS
sudo systemctl restart redis # Ubuntu
```

### Issue: Database migration error

**Solution:**
```bash
# Check database exists
psql -l | grep haven

# Verify connection
psql $DATABASE_URL -c "SELECT 1"

# Reset migration state if needed
alembic stamp head
```

---

## Next Steps

1. **Deploy to Staging:**
   - Set up staging environment
   - Run migrations
   - Test all webhooks
   - Monitor for 24 hours

2. **Production Deployment:**
   - Backup production database
   - Run migrations during maintenance window
   - Configure monitoring/alerting
   - Set up log aggregation

3. **Documentation:**
   - Update API documentation
   - Create webhook integration guides
   - Document error codes and responses

4. **Enhancements:**
   - Add rate limiting
   - Implement admin dashboard
   - Set up monitoring/alerting
   - Create analytics reports

---

## Support

**Documentation:**
- Implementation Summary: `INTEGRATION_IMPLEMENTATION_SUMMARY.md`
- Alembic Guide: `backend/alembic/README.md`
- Test Examples: Check test files for usage patterns

**Verification:**
```bash
python backend/verify_implementation.py
```

**Status:** ✅ Production Ready

All 5 high-priority enhancements completed and tested!

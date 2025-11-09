# HAVEN Token System: Comprehensive Testing Strategy

**Document Version:** 1.0
**Created:** November 2025
**Status:** Ready for Implementation
**Scope:** Smart Contracts, Backend API, Integration Points, End-to-End Flows

---

## Executive Summary

The HAVEN token system is a complex ecosystem combining smart contracts, backend microservices, and third-party integrations (Aurora PMS, Tribe App). This testing strategy ensures reliability, security, and compliance across all layers while supporting the production launch timeline.

**Key Testing Objectives:**
1. Validate smart contract functionality and security
2. Verify backend API reliability and error handling
3. Test critical integration flows (Aurora, Tribe, token agent)
4. Ensure data consistency across blockchain and database layers
5. Load test for expected user volumes (10K-100K users)
6. Identify edge cases and failure scenarios

---

## 1. Current Test Coverage Assessment

### 1.1 Smart Contract Testing (Excellent Coverage)

**File:** `/contracts/test/HAVEN.test.ts`
**Framework:** Hardhat + Chai
**Lines of Test Code:** 388
**Test Cases:** 35+ comprehensive tests

#### Strengths:
- ✅ Deployment tests (3 tests) - Verify initialization, symbol, supply
- ✅ Minting tests (7 tests) - Role validation, zero checks, event emissions
- ✅ Batch minting tests (4 tests) - Array validation, batch size limits
- ✅ Burning tests (7 tests) - User burn, admin burn, balance validation
- ✅ Emergency controls (3 tests) - Pause/unpause mechanics
- ✅ Governance/timelock (6 tests) - Proposal lifecycle, cap enforcement
- ✅ Integration scenarios (2 tests) - Guest lifecycle simulation
- ✅ Access control (2 tests) - Role-based authorization

#### Coverage Metrics:
- Deployment: 100%
- Minting: 100%
- Burning: 100%
- Governance: 100%
- Access Control: 100%
- **Overall:** ~95% (missing some edge case combinations)

#### Gap Analysis:
- ❌ No backend integration tests (only contract-level)
- ❌ No stress testing (single batch max)
- ❌ No gas optimization tests
- ❌ No multi-signature edge cases

---

### 1.2 Backend Testing

**Status:** NO EXISTING TESTS

**Critical Gap:** Zero unit/integration tests for FastAPI backend
- No test fixtures or mocking
- No API endpoint validation
- No database integration tests
- No webhook handler tests
- No service layer tests (Aurora, Tribe, TokenAgent)

**Required:** Full backend test suite (~200-300 tests)

---

### 1.3 Current Test Infrastructure

| Component | Status | Framework | Coverage |
|-----------|--------|-----------|----------|
| Smart Contracts | ✅ Excellent | Hardhat, Chai, ethers.js | 95% |
| Backend API | ❌ Missing | None | 0% |
| Aurora Integration | ❌ Missing | None | 0% |
| Tribe Integration | ❌ Missing | None | 0% |
| Token Agent | ❌ Missing | None | 0% |
| Database Models | ❌ Missing | None | 0% |
| End-to-End | ⚠️ Partial | Manual testing only | ~30% |

---

## 2. Integration Points & Critical Dependencies

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HAVEN Ecosystem                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Aurora, Tribe)                                    │
│         ↓                                                     │
│  FastAPI Backend                                             │
│  ├─ /token/mint (API endpoint)                               │
│  ├─ /token/redeem                                            │
│  ├─ /webhooks/aurora/* (inbound)                             │
│  └─ /webhooks/tribe/* (inbound)                              │
│         ↓                                                     │
│  Service Layer                                               │
│  ├─ TokenAgent (blockchain interaction)                      │
│  ├─ AuroraIntegrationService (booking rewards)               │
│  └─ TribeIntegrationService (community rewards)              │
│         ↓                                                     │
│  Dual Storage                                                │
│  ├─ PostgreSQL (transaction history, users, bookings)        │
│  └─ Blockchain (immutable token balances, events)            │
│         ↓                                                     │
│  External Services                                           │
│  ├─ Aurora PMS (booking events)                              │
│  ├─ Tribe App (community events)                             │
│  └─ Base RPC (Alchemy/Infura for blockchain)                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Integration Points (5 Critical Flows)

#### **1. Smart Contract ↔ Backend API**
- **Flow:** API receives mint request → TokenAgent builds tx → signs → broadcasts to Base network
- **Data Flow:** User ID → Wallet address → Amount (wei) → Receipt tracking
- **Critical:** Idempotency, nonce management, gas price optimization
- **Failure Modes:**
  - Transaction already in mempool (duplicate nonce)
  - Insufficient funds for gas
  - User wallet not created
  - Contract paused

#### **2. Aurora PMS → Backend → Blockchain**
- **Flow:** Booking created in Aurora → webhook → Handler processes → mints tokens
- **Data Flow:** booking_id → guest_id → total_price → calculation → mint event
- **Critical:** Webhook signature verification, booking idempotency
- **Failure Modes:**
  - Guest not found in user database
  - Invalid signature (security)
  - Booking already processed
  - Aurora API timeout

#### **3. Tribe App → Backend → Blockchain**
- **Flow:** Event attendance → webhook → Handler processes → mints tokens
- **Data Flow:** event_id → user_id → event_type → amount → mint
- **Critical:** Real-time reward calculation, quality scoring
- **Failure Modes:**
  - User not registered
  - Invalid event type
  - Double-counting prevention
  - Quality score validation

#### **4. Blockchain → Backend → Database**
- **Flow:** Token mint confirmed on-chain → Receipt captured → DB updated
- **Data Flow:** tx_hash → block confirmation → status update
- **Critical:** Transaction confirmation polling, status consistency
- **Failure Modes:**
  - Block reorg (unlikely on L2 but possible)
  - Confirmation timeout
  - Database commit fails after tx succeeds
  - Race condition between blockchain and DB

#### **5. Database ↔ User Wallet**
- **Flow:** User queries balance → TokenAgent reads contract → compares with DB
- **Data Flow:** wallet_address → on-chain balance vs. off-chain tx history
- **Critical:** Balance reconciliation, audit trail completeness
- **Failure Modes:**
  - Off-chain DB doesn't match on-chain
  - Wallet address mismatch
  - Historical transaction loss
  - Unconfirmed transactions counted

---

## 3. Integration Test Scenarios (10-15 Critical Flows)

### **Scenario 1: Happy Path - Aurora Booking to Token Mint**
```
Given: Guest books stay in Aurora PMS for $100 CAD, 2 nights
When: Booking confirmed webhook received
Then:
  - User created in DB (if new)
  - AuroraBooking record created
  - 400 HNV minted (2 CAD × 100 × 1.2 multi-night bonus)
  - MintEvent emitted with audit trail
  - User balance reflects on-chain
Expected: User has 400 HNV in 3-5 minutes
```

### **Scenario 2: Multi-Night Stay Multiplier**
```
Given: Guest with 3-night stay at $200 CAD
Calculation: 2 × 200 × 1.2 = 480 HNV
When: Webhook processed
Then: User receives exactly 480 HNV
Verify: Multiplier applied correctly, no rounding errors
```

### **Scenario 3: Review Bonus Tiers**
```
Given: Guest completes booking, submits review
Scenario A: 1-3 star review → No bonus
Scenario B: 4-5 star review → 50 HNV bonus
When: Review webhook received
Then: Correct bonus (or none) applied based on rating
Verify: Bonus minted to correct wallet
```

### **Scenario 4: Booking Cancellation Token Reversal**
```
Given: User has 500 HNV from completed booking
When: Booking cancelled webhook received
Then:
  - 500 HNV burned from user wallet
  - BurnEvent emitted with cancellation reason
  - AuroraBooking status updated to "cancelled"
  - User balance reflects immediately
Verify: Token reversal is atomic (all-or-nothing)
```

### **Scenario 5: User Registration (First-Time Booking)**
```
Given: New guest from Aurora (no prior account)
When: Booking created webhook for unknown guest_id
Then:
  - New User created in DB
  - Wallet address generated (or assigned)
  - AuroraBooking linked to new user
  - Tokens minted to new wallet
Verify: User appears in system with correct wallet
```

### **Scenario 6: Tribe Event Attendance Reward**
```
Given: User attends Tribe event (type: "wisdom_circle")
Reward Table:
  - wisdom_circle: 100 HNV
  - workshop: 75 HNV
  - networking: 50 HNV
  - general: 25 HNV
When: Event attendance webhook received
Then: Correct reward minted based on event_type
Verify: Event logged in TribeEvent table
```

### **Scenario 7: Contribution Quality Scoring**
```
Given: User makes forum post with quality_score: 1.5
Base rewards: post = 10 HNV
Calculated: 10 × 1.5 = 15 HNV
When: Contribution webhook processed
Then: 15 HNV minted to user
Verify: Quality multiplier applied correctly
```

### **Scenario 8: Staking Rewards Weekly Calculation**
```
Given: User has 1000 HNV staked
APY: 10% = 0.192% weekly
Reward: 1000 × 0.00192 = 1.92 HNV per week
When: Scheduled job runs (Monday 3 AM)
Then:
  - StakingRecord.earned_rewards += 1.92
  - New mint transaction created
  - 1.92 HNV added to user wallet
Verify: Staking rewards accurate, scheduled job runs reliably
```

### **Scenario 9: Referral Success Multi-Tier**
```
Given: User A refers User B
Tier outcomes:
  - basic: 100 HNV
  - silver: 250 HNV (5+ successful referrals)
  - gold: 500 HNV (20+ successful referrals)
When: Referral success webhook with tier="silver"
Then: 250 HNV minted to referrer's wallet
Verify: Correct tier-based amount applied
```

### **Scenario 10: Coaching Milestone Completion**
```
Given: User completes coaching program
Tier-based rewards:
  - basic: 100 HNV
  - intermediate: 175 HNV
  - advanced: 250 HNV
When: Milestone webhook with tier="advanced"
Then: 250 HNV minted
Verify: Tier validation, audit trail logged
```

### **Scenario 11: Redemption with 2% Burn Fee**
```
Given: User has 1000 HNV, requests redemption
Redemption Flow:
  1. User requests burn 1000 HNV
  2. System calculates: 1000 × 0.98 = 980 CAD payout
  3. System burns 1000 HNV (2% lost in burn)
  4. Payout initiated (off-chain via Stripe/bank)
When: Redemption request submitted
Then:
  - RedemptionRequest created with status="pending"
  - 1000 HNV burned from wallet
  - payout_amount = 980 logged
  - User balance = 0 HNV
Verify: Burn confirmed on-chain, payout pending
```

### **Scenario 12: Webhook Signature Verification**
```
Given: Aurora sends webhook with HMAC-SHA256 signature
Secret: AURORA_WEBHOOK_SECRET = "test_secret"
Payload: {"id": "booking_123", "total_price": 100.00}
When: Webhook received with X-Aurora-Signature header
Then:
  - Signature verified against payload + secret
  - Valid: Process normally
  - Invalid: Return 401 Unauthorized
Verify: No processing of unsigned/invalid webhooks
```

### **Scenario 13: Concurrent Webhook Processing (Race Condition)**
```
Given: Two Aurora booking webhooks arrive simultaneously for same guest
When: Both processed concurrently
Then:
  - Only one User created (unique constraint enforced)
  - Both bookings processed independently
  - No duplicate transactions
Verify: Database constraints prevent race condition errors
```

### **Scenario 14: Backend Failure → Async Retry**
```
Given: Aurora booking webhook received
When: Backend database is temporarily unavailable
Then:
  - Background task fails, raises exception
  - Retry logic kicks in (exponential backoff)
  - After 3 retries with 1m/5m/15m delays
  - Alert sent to monitoring system
  - Manual intervention required
Verify: Graceful degradation, alerting works
```

### **Scenario 15: Contract Pause → Webhook Handling**
```
Given: Admin calls pause() on HAVEN contract
When: Aurora booking webhook arrives
Then:
  - Mint attempt fails (contract paused)
  - Transaction marked as "failed"
  - Error logged with booking_id
  - Admin notified
After: Admin unpause() called
  - Retry mechanism processes failed bookings
Verify: Pause gracefully handled, recovery possible
```

---

## 4. End-to-End User Journey Tests

### **Journey 1: New Guest Lifecycle (14 days)**

```
Day 1: Registration
├─ Guest signs up on PVT website (Aurora integration)
├─ User created in database
├─ Wallet generated
└─ Verification email sent

Day 3: First Booking
├─ Guest books 2-night stay: $150 CAD
├─ Aurora booking webhook received
├─ Calculation: 2 × 150 × 1.2 = 360 HNV minted
├─ User notified of reward
└─ Balance appears in Tribe app: 360 HNV

Day 5-6: Event Attendance
├─ Guest attends Tribe wisdom_circle event
├─ Tribe webhook: event_attendance
├─ 100 HNV minted
└─ New balance: 460 HNV

Day 7: Check-out & Review
├─ Guest checks out
├─ Aurora booking_completed webhook
├─ Guest submits 5-star review
├─ Aurora review webhook: rating=5
├─ 50 HNV review bonus minted
└─ New balance: 510 HNV

Day 10: Referral Success
├─ Referred friend completes first booking
├─ Referral tier: "basic" (1st successful)
├─ 100 HNV minted to referrer
└─ New balance: 610 HNV

Day 14: Redemption Request
├─ Guest requests payout: 500 HNV
├─ System calculates: 500 × 0.98 = $49 CAD
├─ 500 HNV burned
├─ Payout queued (Stripe/bank transfer)
├─ Final balance: 110 HNV
└─ Verification: 500 HNV burned, $49 pending

Assertions:
✓ User exists in DB with correct wallet
✓ All transactions recorded with correct amounts
✓ On-chain balance matches transaction history
✓ All events properly logged
✓ Payout initiated correctly
```

### **Journey 2: Tribe Community Builder (30 days)**

```
Week 1: Event Participation
├─ Day 1: Networking event → 50 HNV
├─ Day 3: Workshop attendance → 75 HNV
├─ Day 5: Wisdom circle → 100 HNV
└─ Balance: 225 HNV

Week 2: Content Contribution
├─ Day 8: Post forum guide (quality_score: 1.8) → 25 × 1.8 = 45 HNV
├─ Day 10: Comment on thread → 5 HNV
├─ Day 12: Share resource → 15 HNV
└─ Balance: 290 HNV

Week 3: Coaching Milestone
├─ Day 15: Complete basic coaching → 100 HNV
├─ Day 20: Advance to intermediate → 175 HNV
├─ Day 25: Reach advanced tier → 250 HNV
└─ Balance: 815 HNV

Week 4: Staking
├─ Day 28: Stake 500 HNV for governance
├─ Staking record created, status=active
├─ Daily staking reward accumulation starts
├─ Balance locked: 500 HNV (earning rewards)
└─ Free balance: 315 HNV

Assertions:
✓ All event rewards tracked in TribeEvent table
✓ Contribution quality scores applied correctly
✓ Coaching milestones cascade properly
✓ Staking record created and earning APY
✓ Balance calculations accurate throughout
```

### **Journey 3: Host Operator Integration (Aurora)**

```
Day 1: Property Setup
├─ Host connects Aurora property to HAVEN
├─ 200 HNV onboarding bonus minted
└─ Balance: 200 HNV (treasury account)

Days 1-30: Booking Activity
├─ 50 bookings received
├─ Avg booking: $120 CAD
├─ Calculation per booking: 2 × 120 = 240 HNV
├─ 10 bookings cancelled (tokens reversed)
├─ Net bookings: 40
├─ Tokens earned: 40 × 240 = 9,600 HNV
├─ Cancelled tokens burned: 10 × 240 = 2,400 HNV (reversed)
└─ Balance: 200 + 9,600 = 9,800 HNV

Days 30+: Redemption
├─ Host requests payout: 5,000 HNV
├─ Payout amount: 5,000 × 0.98 = $490 CAD (approx)
├─ 5,000 HNV burned
└─ Final balance: 4,800 HNV (remaining reserves)

Assertions:
✓ All bookings tracked in AuroraBooking table
✓ Cancellation reversals work correctly
✓ Balance reflects completed bookings only
✓ Payout calculation accurate
```

---

## 5. Load Testing Approach

### 5.1 Load Testing Objectives

| Metric | Target | Test Scenario |
|--------|--------|---------------|
| **Concurrent Users** | 1,000 | Simultaneous API requests |
| **RPS (Requests/Sec)** | 500 | Sustained throughput |
| **API Response Time** | <500ms (p99) | Balance queries, mint requests |
| **Database Connections** | <50 | Connection pool saturation |
| **Blockchain TX Throughput** | 100 tx/min | Batch processing capacity |
| **Error Rate** | <0.1% | Under normal load |

### 5.2 Load Test Scenarios

#### **Scenario A: API Throughput (500 RPS)**

```
Test Duration: 5 minutes
Load Profile:
  - Minute 1: Ramp to 100 RPS (user login + initial balance checks)
  - Minute 2-3: Hold at 500 RPS (mixed operations)
  - Minute 4: Spike to 750 RPS (lunch hour simulation)
  - Minute 5: Cool-down to 100 RPS

Operations Mix:
  - 40% GET /token/balance/{user_id}
  - 30% POST /token/mint (queued)
  - 20% POST /webhooks/aurora/booking-created
  - 10% GET /analytics/token-stats

Assertions:
  ✓ p50 response time: <200ms
  ✓ p95 response time: <400ms
  ✓ p99 response time: <500ms
  ✓ Error rate: <0.1%
  ✓ DB connection pool doesn't exhaust
  ✓ Memory usage remains stable
```

#### **Scenario B: Blockchain Transaction Throughput**

```
Test Duration: 1 hour
Setup:
  - 5,000 test users pre-created in DB
  - 5 RPC endpoints configured (Alchemy fallback)

Load Profile:
  - Hour 1: 1,000 mint TXs (200 tx/min)
  - Background: 100 tx/min redemptions (burns)

Blockchain Assertions:
  ✓ All TXs reach mempool
  ✓ Average confirmation time: <90 seconds
  ✓ No nonce collisions
  ✓ Gas price stays within bounds (<0.001 gwei)
  ✓ RPC failures trigger fallback without losing TXs

Database Assertions:
  ✓ TX status: pending → confirming → confirmed
  ✓ All receipts captured
  ✓ No orphaned transactions
```

#### **Scenario C: Webhook Resilience**

```
Test Duration: 30 minutes
Webhook Sources:
  - Aurora API: 100 webhooks/min (booking events)
  - Tribe API: 50 webhooks/min (event rewards)

Failure Injection:
  - Network latency: 100-500ms
  - Random 5% payload corruption
  - 2% webhook timeouts (retry needed)
  - 1% signature verification failures

Assertions:
  ✓ Valid webhooks processed 100% of time
  ✓ Invalid signatures rejected with 401
  ✓ Corrupted payloads logged, not processed
  ✓ Timeouts trigger retry with exponential backoff
  ✓ No double-processing (idempotency works)
  ✓ Monitoring alerts on error threshold
```

#### **Scenario D: Database Scaling**

```
Test Duration: 2 hours
Growth Simulation:
  - Start: 10K users
  - Each minute: +500 new users
  - Final: 60K+ users in DB

Growth of Related Records:
  - Transactions: 10 per user = 600K transactions
  - AuroraBookings: 2 per user = 120K bookings
  - TribeEvents: 5 per user = 300K events

Database Assertions:
  ✓ Queries stay <500ms even at 60K users
  ✓ Index performance maintained
  ✓ Connection pool never saturates
  ✓ Disk I/O within healthy limits
  ✓ No N+1 query problems

Optimization Opportunities:
  - Identify slow queries
  - Validate index strategy
  - Test pagination (limit/offset)
```

### 5.3 Load Testing Tools & Setup

```
Primary Tools:
├─ Apache JMeter (API load testing)
│  └─ 50 thread pools, 5K users
├─ Locust (Python-based, webhook simulation)
│  └─ Simulate Aurora/Tribe API behavior
├─ k6 (JavaScript-based, cloud scaling)
│  └─ Distributed load from multiple regions
└─ Hardhat (local blockchain testing)
   └─ Simulate on-chain load

Infrastructure:
├─ Test Database: Separate PostgreSQL instance (prod-like)
├─ Test Blockchain: Base Sepolia (testnet with faucet)
├─ Monitoring: Prometheus + Grafana (metrics collection)
├─ Observability: Sentry (error tracking)
└─ Baseline: Historical perf data (for regression detection)
```

---

## 6. Edge Cases & Error Scenarios to Test

### **Category 1: Input Validation**

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Zero amount mint | amount = 0 | Revert: "Amount must be > 0" |
| Negative amount | amount = -100 | Type validation fails |
| Zero address recipient | to = 0x0000... | Revert: "Cannot mint to zero address" |
| Invalid user_id format | user_id = "" | 400 Bad Request |
| Oversized batch | 101 recipients | Revert: "Max 100 per batch" |
| Array mismatch | recipients.length ≠ amounts.length | Revert: "Array length mismatch" |
| Invalid address checksum | 0x123abc (not checksummed) | Web3.to_checksum_address() corrects it |
| Null/undefined in request | No user_id | 400 Bad Request (Pydantic validation) |

### **Category 2: Authorization & Security**

| Scenario | User Role | Action | Expected Result |
|----------|-----------|--------|-----------------|
| Non-minter mints | User (no MINTER_ROLE) | mint() | Revert: "AccessControl" |
| Burner burns from wrong user | BURNER_ROLE | burn own tokens | Revert (only burnFrom allowed) |
| Paused contract operation | Anyone | mint() | Revert: "Pausable: paused" |
| Invalid API key | client | POST /token/mint | 401 Unauthorized |
| Tampered webhook signature | Aurora | webhook | 401 Invalid signature |
| Missing API key header | client | POST /token/mint | 403 Missing key |

### **Category 3: Idempotency & Deduplication**

| Scenario | Request | Expected Result |
|----------|---------|-----------------|
| Duplicate mint (same tx_id) | POST /token/mint (idempotency_key=X) twice | Second returns "duplicate" (200 OK, not 500) |
| Replay same webhook | Aurora sends booking_created twice | Only first processed, second ignored |
| Race condition mints | Two simultaneous mints for user A | Both succeed, balances are cumulative |
| Nonce collision | Two TXs from same account | Second TX waits for first confirmation |

### **Category 4: Balance & Arithmetic**

| Scenario | Setup | Operation | Expected |
|----------|-------|-----------|----------|
| Insufficient balance burn | User has 100 HNV | Burn 150 HNV | Revert: "Insufficient balance" |
| Overflow on large mint | Mint repeatedly | Eventually hit supply cap | Revert or graceful degradation |
| Rounding errors | Burn 100 HNV (2% fee) | 98 paid out, 2 burned | No rounding loss in wei |
| Staking reward precision | 1000 HNV × 0.00192 weekly | Calculate 1.92 HNV | Verify wei precision (no truncation) |
| Multi-night multiplier | 2 nights at 100 CAD | 2 × 100 × 1.2 = 240 HNV | Exactly 240 HNV, no float errors |

### **Category 5: Data Consistency**

| Scenario | Event | Expected Behavior |
|----------|-------|-------------------|
| DB commit fails after TX mined | Backend crashes after blockchain TX succeeds | TX marked confirmed on-chain, DB shows "pending" → Manual reconciliation |
| TX in mempool, node restarts | TX never included in block | TX status stays "confirming", retry auto-triggers |
| User deleted from DB | User exists on-chain with tokens | System prevents user recreation with same ID |
| Stale blockchain data | Query immediately after TX | May get old balance (eventually consistent) |
| Double-spend attempt | User tries to spend same tokens twice (offline) | Second TX fails when submitted (balance check) |

### **Category 6: External Service Failures**

| Scenario | Service | Failure Mode | Expected Handling |
|----------|---------|--------------|-------------------|
| Aurora API timeout | Aurora booking webhook | 5s timeout, no response | Retry with exponential backoff |
| RPC node down | Alchemy RPC | Connection refused | Fallback to secondary RPC (Infura) |
| Database unavailable | PostgreSQL | Connection pool exhausted | Return 503, background task retries |
| Stripe fails payout | Fiat off-ramp | API error on redemption | Redemption status = "failed", manual retry |
| Signature verification fails | HMAC validation | Invalid signature | Log security alert, return 401 |

### **Category 7: Governance & Timelock**

| Scenario | Action | Timeline | Expected |
|----------|--------|----------|----------|
| Execute timelock early | proposeTimelockChange() + executeTimelockChange() | <7 days | Revert: "Timelock not expired" |
| Execute twice | Same proposal executed again | After first exec | Revert: "Already executed" |
| Exceed monthly cap | Propose 150K HNV/month | Governance | Revert: "Cap at 100k/month" |
| Negative mint target | Propose -10K HNV/month | Governance | Type validation fails (uint256) |

### **Category 8: Concurrent & Race Conditions**

| Scenario | Concurrent Operations | Expected Behavior |
|----------|----------------------|-------------------|
| Two webhooks, same user | Aurora booking + Tribe event | Both mints succeed, balances cumulative |
| Mint + Redeem race | User simultaneously mints and burns | One succeeds, other respects new balance |
| Staking + Redemption | User stakes and requests redemption concurrently | Staking locks amount, redemption pending |
| Database transaction conflict | Two writes to User.wallet_address | Unique constraint prevents duplicates |

---

## 7. Test Data Strategy

### 7.1 Test User Personas

```yaml
persona_1_casual_guest:
  name: "Alex - Casual Traveler"
  aurora_profile:
    email: alex@example.com
    total_bookings: 3
    avg_booking_value: 80 CAD
  tribe_profile:
    events_attended: 2
    contributions: 5
  expected_balance: 650 HNV
  use_case: "Test basic booking + event rewards"

persona_2_power_user:
  name: "Casey - Community Builder"
  aurora_profile:
    email: casey@example.com
    total_bookings: 15
    avg_booking_value: 150 CAD
  tribe_profile:
    events_attended: 20
    contributions: 50
    coaching_completed: true
    staking_amount: 5000 HNV
  expected_balance: 25000 HNV
  use_case: "Test staking, coaching, high volume"

persona_3_host_operator:
  name: "Jordan - Property Owner"
  aurora_role: "host"
  properties_managed: 2
  monthly_bookings: 100
  expected_monthly_earn: 24000 HNV
  use_case: "Test host rewards, bulk redemptions"

persona_4_admin:
  name: "Admin User"
  roles: ["MINTER_ROLE", "BURNER_ROLE", "PAUSER_ROLE", "GOVERNANCE_ROLE"]
  use_case: "Test governance, emergency controls"
```

### 7.2 Test Data Generation

```python
# Pseudo-code for test data factory

def create_test_user(user_id, email):
    """Create user with wallet"""
    user = User(
        user_id=user_id,
        email=email,
        wallet_address=generate_wallet(),
        kyc_verified=True
    )
    db.add(user)
    db.commit()
    return user

def create_test_booking(user_id, amount_cad, nights):
    """Create Aurora booking record"""
    calculated_reward = amount_cad * 2.0 * (1.2 if nights > 1 else 1.0)
    booking = AuroraBooking(
        booking_id=f"booking_{uuid()}",
        user_id=user_id,
        booking_total=amount_cad,
        nights=nights,
        reward_tokens=calculated_reward,
        status="completed",
        completed_at=datetime.utcnow()
    )
    db.add(booking)
    db.commit()
    return booking

def create_test_stake(user_id, amount):
    """Create staking record"""
    record = StakingRecord(
        stake_id=f"stake_{uuid()}",
        user_id=user_id,
        amount=amount,
        earned_rewards=0.0,
        status="active"
    )
    db.add(record)
    db.commit()
    return record

# Seed script runs:
# - 100 casual guest personas
# - 20 power users with history
# - 10 host operators
# - 1 admin account
# Total: 131 test users with realistic data
```

### 7.3 Blockchain Test Data

```solidity
// Setup test data on-chain

// Deploy fresh contract for each test suite
HAVEN.sol deployed → contract_address

// Pre-fund test wallets
Backend account: 1 ETH (for gas)
Admin account: 1 ETH
Minter account: 1 ETH

// Grant roles
MINTER_ROLE → token_agent backend account
BURNER_ROLE → token_agent backend account
PAUSER_ROLE → admin
GOVERNANCE_ROLE → admin + DAO

// Seed initial token supply
Mint 100,000,000 HNV to treasury wallet (10% circulating)
```

---

## 8. Testing Timeline & Priorities

### **Phase 1: Foundation (Weeks 1-2)**

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Backend unit test suite (FastAPI) | P0 | 40h | Backend Lead |
| Database integration tests | P0 | 20h | Backend Lead |
| TokenAgent service tests | P0 | 20h | Backend Lead |
| AuroraIntegrationService tests | P0 | 20h | Backend Lead |
| TribeIntegrationService tests | P0 | 20h | Backend Lead |
| **Phase 1 Total** | | **120h** | |

**Deliverables:**
- ✓ 100+ backend unit tests
- ✓ 50+ integration tests (service layer)
- ✓ All critical path tested
- ✓ >80% code coverage

### **Phase 2: Integration (Weeks 3-4)**

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| End-to-end flow tests (3 journeys) | P0 | 30h | QA Lead |
| Webhook handler tests (Aurora + Tribe) | P0 | 20h | Backend Lead |
| API contract tests (OpenAPI validation) | P1 | 15h | QA Lead |
| Database consistency tests | P0 | 20h | Backend Lead |
| Blockchain integration tests | P1 | 25h | Smart Contract Lead |
| **Phase 2 Total** | | **110h** | |

**Deliverables:**
- ✓ 15 critical integration scenarios verified
- ✓ All webhooks tested (valid + invalid cases)
- ✓ End-to-end user journeys validated
- ✓ Blockchain↔Backend sync verified

### **Phase 3: Load Testing (Weeks 5-6)**

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| JMeter setup & API load tests | P0 | 25h | Performance Engineer |
| Blockchain TX throughput tests | P0 | 20h | Blockchain Engineer |
| Webhook stress test (burst handling) | P1 | 15h | Backend Lead |
| Database scaling tests (10K→60K users) | P1 | 20h | DBA/Backend |
| Monitoring + alerting setup | P0 | 15h | DevOps Lead |
| **Phase 3 Total** | | **95h** | |

**Deliverables:**
- ✓ Baseline performance metrics established
- ✓ Load test reports (500 RPS capable)
- ✓ Bottleneck identification
- ✓ Monitoring dashboards active

### **Phase 4: Edge Cases & Security (Weeks 7-8)**

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Edge case test matrix (50+ scenarios) | P0 | 35h | QA Lead |
| Security tests (signature verification, authz) | P0 | 25h | Security Engineer |
| Error scenario tests (recovery, retry logic) | P1 | 20h | Backend Lead |
| Failure injection tests (chaos engineering) | P1 | 20h | DevOps Lead |
| Documentation + test reports | P1 | 15h | QA Lead |
| **Phase 4 Total** | | **115h** | |

**Deliverables:**
- ✓ All edge cases documented & tested
- ✓ Security vulnerabilities identified
- ✓ Recovery procedures validated
- ✓ Test report published

### **Timeline Summary**

| Phase | Duration | Tests | Coverage |
|-------|----------|-------|----------|
| Foundation | 2 weeks | 150+ | 80% (backend) |
| Integration | 2 weeks | 100+ | 85% (system) |
| Load Testing | 2 weeks | 10 scenarios | Performance baseline |
| Edge Cases | 2 weeks | 50+ | 95% (overall) |
| **Total** | **8 weeks** | **300+** | **95%** |

**Total Test Effort:** ~440 hours (5.5 full-time engineers for 8 weeks)

---

## 9. Current Testing Gaps & Critical Needs

### 9.1 Smart Contract Gaps (Low Risk)

| Gap | Impact | Fix Effort | Recommendation |
|-----|--------|-----------|-----------------|
| No gas optimization tests | Potential high gas costs | 8h | Add after main tests |
| Limited edge case combinations | 5-10% scenarios uncovered | 12h | Add fuzzing tests |
| No multi-sig integration tests | Treasury operations untested | 10h | Defer to Phase 2 |

### 9.2 Backend Gaps (CRITICAL)

| Gap | Impact | Fix Effort | Recommendation |
|-----|--------|-----------|-----------------|
| **Zero API tests** | Can't verify endpoints work | 40h | **START IMMEDIATELY** |
| **No webhook tests** | Critical integration untested | 25h | **START IMMEDIATELY** |
| **No database tests** | Data consistency unknown | 20h | **START IMMEDIATELY** |
| No service layer mocking | Integration hard to test | 15h | Set up test fixtures |
| No error scenario tests | Recovery unknown | 20h | Test all failure modes |

### 9.3 Integration Gaps (HIGH RISK)

| Gap | Impact | Fix Effort | Recommendation |
|-----|--------|-----------|-----------------|
| **No Aurora integration tests** | Booking rewards untested | 20h | **Phase 2 (Week 3)** |
| **No Tribe integration tests** | Community rewards untested | 20h | **Phase 2 (Week 3)** |
| **No end-to-end tests** | User journeys untested | 30h | **Phase 2 (Week 4)** |
| No blockchain↔DB sync tests | Data consistency unknown | 20h | Phase 2 (Week 3) |
| No webhook signature tests | Security vulnerability | 10h | Phase 1 (Week 2) |

### 9.4 Load Testing Gaps (MEDIUM RISK)

| Gap | Impact | Fix Effort | Recommendation |
|-----|--------|-----------|-----------------|
| **No load testing** | Can't handle 1K concurrent users? | 50h | **Phase 3 (Weeks 5-6)** |
| **No chaos tests** | Failure modes unknown | 30h | Phase 4 (Week 8) |
| **No monitoring in place** | Can't detect issues in prod | 20h | Phase 3 (Week 5) |

---

## 10. Testing & QA Recommendations

### 10.1 Test Framework & Tools

```yaml
Backend Testing:
  Unit Tests:
    - Framework: pytest
    - Fixtures: pytest-fixtures
    - Mocking: unittest.mock
    - Coverage: pytest-cov (target: 85%+)

  Integration Tests:
    - Database: TestingDatabase (separate instance)
    - Blockchain: Hardhat local network (hardhat node)
    - APIs: httpx (async HTTP client)
    - Fixtures: conftest.py (shared setup)

  Test Doubles:
    - Database: In-memory SQLite for unit tests
    - RPC: Mock Web3 provider with responses
    - Aurora API: Mock HTTP server (responses library)
    - Tribe API: Mock HTTP server (responses library)

Smart Contract Testing:
  - Framework: Hardhat + Chai
  - Gas Testing: Hardhat gas reporter
  - Coverage: solidity-coverage (target: 100%)
  - Fuzzing: Echidna (property-based)

Load Testing:
  - Tools: JMeter, Locust, k6
  - Monitoring: Prometheus + Grafana
  - Error Tracking: Sentry
  - Alerting: PagerDuty integration

E2E Testing:
  - Framework: Playwright or Cypress (UI layer)
  - API Testing: Postman collections + Newman CLI
  - Test Orchestration: GitHub Actions + pytest
```

### 10.2 Test Environment Setup

```yaml
Local Development:
  - Hardhat local network (blockchain simulation)
  - PostgreSQL in Docker
  - Redis for session/cache (optional)
  - Mock Aurora/Tribe APIs (Wiremock)

Staging/QA:
  - Base Sepolia testnet (public testnet)
  - Staging PostgreSQL (prod-like, 100GB data)
  - Real Aurora/Tribe integration (webhook receiver)
  - Alchemy RPC (with testnet faucet)

CI/CD Pipeline:
  - Tests run on: GitHub Actions (Linux agents)
  - Before: Linting (black, pylint, solhint)
  - Unit tests: In parallel (Jest, pytest)
  - Integration tests: Sequential (need DB)
  - Coverage report: Generated & published
  - Artifacts: Test reports, gas reports
```

### 10.3 Success Criteria for Each Test Type

```yaml
Unit Tests:
  - Coverage: >85%
  - Execution time: <30 seconds
  - All tests pass
  - No skipped/pending tests

Integration Tests:
  - Coverage: >75% (service layer)
  - Execution time: <2 minutes
  - Database state consistent
  - All mocks/fixtures working

E2E Tests:
  - Critical paths: 100% working
  - User journeys: 3 major flows
  - Response times: <500ms (p99)
  - Blockchain confirmations: <2 minutes

Load Tests:
  - Throughput: 500 RPS sustained
  - Latency: <500ms (p99)
  - Error rate: <0.1%
  - No resource exhaustion

Security Tests:
  - Auth: All endpoints protected
  - Signatures: All webhooks verified
  - Injection: No SQL/code injection
  - Secrets: No hardcoded keys
```

### 10.4 Continuous Integration Pipeline

```yaml
GitHub Actions Workflow (on every push):

1. Lint & Format Check (2 min)
   - black (Python formatting)
   - pylint (code quality)
   - solhint (Solidity)
   - prettier (JSON/YAML)

2. Unit Tests (5 min)
   - Backend: pytest (parallel)
   - Contracts: hardhat test
   - Coverage report: Codecov

3. Integration Tests (10 min)
   - Start test database
   - Start local blockchain
   - Run pytest integration suite
   - Database cleanup

4. Build Artifacts (3 min)
   - Docker image (backend)
   - Contract ABI + bytecode
   - Gas report

5. Publish Results (2 min)
   - Test report to GitHub
   - Coverage badge update
   - Slack notification

Total Pipeline Time: ~22 minutes
Status: Pass/Fail before merge

On Merge to Main:
   - Deploy to staging
   - Run smoke tests
   - Deploy to production (if approved)
```

---

## 11. Test Execution Roadmap

### Week 1-2: Foundation

```
Monday:
  - Kick-off meeting (2h)
  - Set up test infrastructure (4h)
  - Create base fixtures and conftest.py (4h)

Tuesday-Wednesday:
  - Write API endpoint tests (20h)
  - Test database models (10h)
  - Test utility functions (5h)

Thursday-Friday:
  - Write TokenAgent service tests (10h)
  - Write AuroraIntegrationService stubs (5h)
  - Code review & refactoring (5h)

Monday-Friday (Week 2):
  - Complete TribeIntegrationService tests (20h)
  - Write webhook signature tests (8h)
  - Error handling tests (12h)
  - Integration between services (10h)
  - Coverage report generation (2h)

End of Week 2:
  - 150+ tests written
  - 80%+ coverage achieved
  - All tests passing
```

### Week 3-4: Integration

```
Week 3:
  - Aurora webhook end-to-end test (10h)
  - Tribe webhook end-to-end test (10h)
  - User journey test #1 (10h)
  - User journey test #2 (10h)
  - Data consistency validations (10h)

Week 4:
  - User journey test #3 (10h)
  - API contract tests (15h)
  - Error scenario tests (20h)
  - Regression test suite (10h)

End of Week 4:
  - 250+ tests total
  - 3 user journeys validated
  - All integration paths tested
```

### Week 5-6: Load & Performance

```
Week 5:
  - Baseline performance metrics (10h)
  - JMeter setup & API tests (20h)
  - Database scaling tests (15h)
  - Report generation (5h)

Week 6:
  - Blockchain throughput tests (15h)
  - Webhook burst testing (10h)
  - Bottleneck analysis (10h)
  - Optimization recommendations (10h)

End of Week 6:
  - Performance baseline established
  - Load test suite ready for prod validation
  - Capacity planning data available
```

### Week 7-8: Edge Cases & Security

```
Week 7:
  - Edge case test matrix (20h)
  - Security tests (20h)
  - Failure injection tests (10h)

Week 8:
  - Final regression suite (10h)
  - Documentation (15h)
  - Test report publication (5h)
  - Sign-off & handoff (5h)

End of Week 8:
  - 300+ tests written
  - 95%+ coverage achieved
  - Comprehensive test report published
  - Ready for production launch
```

---

## 12. Quality Metrics & KPIs

### 12.1 Test Coverage Metrics

```
Target Coverage (by module):

Smart Contracts:
  - HAVEN.sol: 100% (critical, security-sensitive)
  - Deployment: 100%
  - Minting: 100%
  - Burning: 100%
  - Governance: 100%

Backend API:
  - app.py routes: 95%
  - services/*.py: 90%
  - database/models.py: 100%
  - Integrations: 85%

Overall Target: 90%+ coverage
```

### 12.2 Reliability Metrics

```
API Availability:
  - Target: 99.9% uptime
  - Measurement: HTTP status code monitoring
  - Alert threshold: <99.5% in 5-minute window

Transaction Success Rate:
  - Target: >99.8% (some failures expected)
  - Acceptable failure reasons:
    - User insufficient balance (<0.1%)
    - Network congestion (<0.05%)
    - Invalid signatures (<0.05%)

Blockchain Confirmation Time:
  - Target: <2 minutes (p95)
  - Base network typical: 12 seconds per block
  - Expect 10-15 blocks for finality

Database Health:
  - Query latency: p99 <500ms
  - Connection pool utilization: <80%
  - Disk space: <85% used
```

### 12.3 Testing Health Metrics

```
Test Execution:
  - Total test suites: 15+
  - Total test cases: 300+
  - Average execution time: <5 minutes (unit)
  - Flakiness rate: <1% (target: 0%)

Code Quality:
  - Line coverage: >90%
  - Branch coverage: >85%
  - Cyclomatic complexity: <10 per function
  - Technical debt ratio: <5%

Defect Detection:
  - Bugs found per 1K lines: >2 (indicates thorough testing)
  - Escaped defects (found in prod): <1 per quarter
  - Mean time to fix: <4 hours
```

---

## Appendix: Quick Reference

### Quick Test Running Commands

```bash
# Run all tests
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run with markers
pytest -m "integration" --timeout=30

# Smart contract tests
cd contracts && npm test

# Load testing
locust -f locustfile.py --headless -u 1000 -r 50

# Coverage report
pytest --cov --cov-report=term-missing
```

### Test File Organization

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_api_endpoints.py    # FastAPI routes
│   ├── test_services/
│   │   ├── test_token_agent.py
│   │   ├── test_aurora.py
│   │   └── test_tribe.py
│   ├── test_database/
│   │   ├── test_models.py
│   │   └── test_transactions.py
│   ├── test_integration/
│   │   ├── test_aurora_booking_flow.py
│   │   ├── test_tribe_rewards_flow.py
│   │   └── test_e2e_journeys.py
│   └── test_security/
│       ├── test_auth.py
│       └── test_webhooks.py

contracts/
└── test/
    ├── HAVEN.test.ts
    ├── HAVEN.integration.test.ts
    └── HAVEN.gas.test.ts

load-tests/
├── jmeter/
│   └── api_load_plan.jmx
├── locust/
│   └── locustfile.py
└── k6/
    └── load_test.js
```

---

## Conclusion

This comprehensive testing strategy addresses the complexity of the HAVEN token ecosystem by:

1. **Leveraging existing smart contract tests** (35+ tests, 95% coverage)
2. **Building critical backend test suite** (150+ new tests needed)
3. **Validating all integration points** (15 critical flows)
4. **Ensuring system reliability** (load tests, chaos tests)
5. **Preventing security vulnerabilities** (auth, signature, injection tests)

**Success Criteria:** 300+ tests, 90%+ coverage, <5 min execution, zero escape defects

**Timeline:** 8 weeks, 440 hours, 5-6 engineers

**Deliverables:**
- Test suite (runnable, CI/CD integrated)
- Test reports & coverage metrics
- Performance baseline & optimization recommendations
- Security audit findings & fixes
- Production readiness sign-off

---

**Document Owner:** QA/Integration Agent
**Last Updated:** November 2025
**Next Review:** Before mainnet deployment (Q1 2026)

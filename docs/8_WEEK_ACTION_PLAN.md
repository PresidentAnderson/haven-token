# HAVEN Token: 8-Week Action Plan to Production

**Generated:** November 8, 2025
**Target Launch:** January 17, 2026
**Status:** APPROVED - Ready for Execution

---

## Executive Summary

This 8-week plan transforms the HAVEN Token project from its current state (85% complete, testnet-ready) to a secure, fully-tested production deployment on Base mainnet. The plan addresses all critical security vulnerabilities, implements comprehensive testing, completes an external security audit, and ensures production readiness.

**Key Milestones:**
- Week 1-2: Security fixes + testnet deployment + basic testing
- Week 3-4: Integration testing + external audit kickoff
- Week 5-6: Load testing + audit remediation
- Week 7: Mainnet preparation + final validation
- Week 8: Mainnet launch + public release

**Resources Required:**
- 5.5 FTE team members
- $90K-$170K budget
- 440+ engineering hours

---

## Week 1: Critical Security Fixes & Testnet Deployment

### Overview
**Goal:** Fix all CRITICAL security vulnerabilities, deploy to Base Sepolia testnet
**Duration:** November 8-15, 2025
**Team:** Backend Engineer (2.0 FTE), Smart Contract Engineer (0.5 FTE)

### Monday (Day 1): Smart Contract Test Fixes

**Morning (9am-12pm):**
- [ ] Fix timestamp precision test in `contracts/test/HAVEN.test.ts:84`
  - Issue: Off-by-one timestamp calculation
  - Solution: Adjust timestamp expectation logic
  - Expected: 1 hour

- [ ] Fix function overload test in `contracts/test/HAVEN.test.ts:197`
  - Issue: Ambiguous function call to `burnFrom`
  - Solution: Use explicit function signature
  - Expected: 1 hour

**Afternoon (1pm-5pm):**
- [ ] Re-run full test suite: `npm test`
- [ ] Verify 100% test pass rate (32/32 tests)
- [ ] Generate coverage report: `npm run coverage`
- [ ] Verify coverage >95%
- [ ] Commit fixes to git

**Deliverables:**
- ✅ All 32 tests passing
- ✅ Coverage >95%
- ✅ Git commit with test fixes

---

### Tuesday (Day 2): Backend Security - Webhook Signatures

**Morning (9am-12pm):**
- [ ] Create webhook signature verification utility
  - Location: `backend/middleware/webhook_auth.py`
  - Implement HMAC-SHA256 signature verification
  - Add timestamp validation (reject >5 min old)

**Afternoon (1pm-5pm):**
- [ ] Apply signature verification to all Aurora webhooks:
  - `POST /webhooks/aurora/booking-completed`
  - `POST /webhooks/aurora/booking-cancelled`
  - `POST /webhooks/aurora/review-submitted`

- [ ] Apply signature verification to all Tribe webhooks:
  - `POST /webhooks/tribe/event-attendance`
  - `POST /webhooks/tribe/contribution`
  - `POST /webhooks/tribe/staking-started`
  - `POST /webhooks/tribe/coaching-milestone`
  - `POST /webhooks/tribe/referral-success`

**Test:**
- [ ] Create test cases for signature verification
- [ ] Test with valid signatures
- [ ] Test rejection of invalid signatures
- [ ] Test timestamp expiration

**Deliverables:**
- ✅ Signature verification on 9 webhook endpoints
- ✅ Test coverage for webhook security

---

### Wednesday (Day 3): Backend Security - Rate Limiting & Authentication

**Morning (9am-12pm):**
- [ ] Install rate limiting dependencies:
  ```bash
  pip install slowapi redis fastapi-limiter
  ```

- [ ] Implement rate limiting using Redis:
  - Configure Redis connection
  - Add rate limiter to FastAPI app
  - Apply limits to all endpoints:
    - `/token/mint`: 10 requests/minute
    - `/token/redeem`: 5 requests/minute
    - `/token/balance/*`: 100 requests/minute
    - Webhooks: 100 requests/minute per endpoint

**Afternoon (1pm-5pm):**
- [ ] Fix API key authentication:
  - Remove `"test_key"` default in `backend/app.py:125`
  - Add startup validation: raise error if `API_KEY` not set
  - Document required environment variables

- [ ] Add input validation for amounts:
  - Update `MintRequest` model with Field constraints:
    - `amount: float = Field(gt=0, le=10000)`
  - Update `RedeemRequest` model with Field constraints:
    - `amount: float = Field(gt=0, le=100000)`

**Test:**
- [ ] Test rate limiting with rapid requests
- [ ] Verify API key validation fails without env var
- [ ] Test amount validation (reject negative, zero, excessive)

**Deliverables:**
- ✅ Rate limiting operational on all endpoints
- ✅ API key authentication hardened
- ✅ Input validation preventing invalid amounts

---

### Thursday (Day 4): Wallet Creation Security Fix

**Morning (9am-12pm):**
- [ ] Review current wallet creation in `backend/services/aurora_integration.py`
- [ ] Design secure wallet storage solution:
  - Option A: Custodial wallets with AWS KMS encryption
  - Option B: User-controlled wallets via wallet-connect
  - **Recommendation:** Custodial with KMS for MVP

**Afternoon (1pm-5pm):**
- [ ] Implement secure wallet creation:
  - Create new table: `encrypted_wallets`
  - Install cryptography library: `pip install cryptography`
  - Store encrypted private keys in database
  - Use environment variable as encryption key (rotate to KMS later)

- [ ] Update user creation flow:
  - Generate wallet
  - Encrypt private key
  - Store in database
  - Return wallet address only

**Test:**
- [ ] Verify wallets are created and stored
- [ ] Verify private keys are encrypted
- [ ] Test wallet retrieval and decryption
- [ ] Verify minting still works with new wallet system

**Deliverables:**
- ✅ Secure wallet storage implemented
- ✅ Private keys encrypted in database
- ✅ Wallet creation flow tested

---

### Friday (Day 5): Testnet Deployment

**Morning (9am-12pm):**
- [ ] Set up deployment prerequisites:
  - Create Alchemy account: https://alchemy.com/signup
  - Create Base Sepolia app
  - Copy RPC URL to `contracts/.env`

- [ ] Generate deployment wallet:
  ```bash
  npx ethers-wallet new
  ```
  - Save private key to `contracts/.env` as `DEPLOYER_PRIVATE_KEY`
  - Save address for faucet request

- [ ] Fund test wallet:
  - Visit https://www.alchemy.com/faucets/base-sepolia
  - Request 0.5 ETH
  - Verify funds received: `cast balance YOUR_ADDRESS --rpc-url https://sepolia.base.org`

**Afternoon (1pm-5pm):**
- [ ] Deploy to Base Sepolia:
  ```bash
  cd contracts
  npm run deploy:testnet
  ```

- [ ] Verify contract on Basescan:
  ```bash
  npm run verify
  ```

- [ ] Record deployment:
  - Copy contract address from output
  - Update `backend/.env` with `HAVEN_CONTRACT_ADDRESS`
  - Save deployment JSON in `contracts/deployments/`
  - Document in deployment log

**Test:**
- [ ] View contract on Basescan: https://sepolia.basescan.org/address/YOUR_CONTRACT
- [ ] Verify contract source code is verified
- [ ] Check roles are granted correctly
- [ ] Test mint 1 token from backend

**Deliverables:**
- ✅ HAVEN contract deployed to Base Sepolia
- ✅ Contract verified on Basescan
- ✅ Backend connected to deployed contract
- ✅ First test transaction successful

---

### Weekend: Documentation Updates

**Saturday (2 hours):**
- [ ] Update whitepaper with actual team names (replace `[Your Name]`)
- [ ] Fix tokenomics.csv Excel formula on line 20:
  - Change: `=IF(MONTH<=36 10000000 0)`
  - To: `=IF(MONTH<=36,10000000,0)`
- [ ] Create `docs/FAQ.md` with common questions
- [ ] Create `CONTRIBUTING.md` with contribution guidelines

**Sunday (1 hour):**
- [ ] Remove all "coming soon" placeholders from README
- [ ] Update PROJECT_SUMMARY.md with testnet deployment details
- [ ] Verify all documentation links are valid

**Deliverables:**
- ✅ Documentation production-ready
- ✅ No placeholders or broken links

---

### Week 1 Success Criteria

**Must Complete:**
- [x] All 32 smart contract tests passing (100%)
- [x] 6 critical security issues resolved:
  - Webhook signature verification
  - Rate limiting
  - API key hardening
  - Wallet security
  - Input validation
- [x] Contract deployed to Base Sepolia testnet
- [x] Documentation updated

**Metrics:**
- Test coverage: >95%
- Security score: 8.5/10 (up from 7.5/10)
- Deployment status: Testnet live

---

## Week 2: Backend Testing Foundation

### Overview
**Goal:** Achieve 60%+ backend test coverage, validate core functionality
**Duration:** November 15-22, 2025
**Team:** Backend Engineer (2.0 FTE), QA Engineer (1.5 FTE)

### Monday (Day 6): Test Infrastructure Setup

**Morning (9am-12pm):**
- [ ] Create test directory structure:
  ```
  backend/tests/
    __init__.py
    conftest.py          # pytest fixtures
    test_api.py          # API endpoint tests
    test_services.py     # Service layer tests
    test_models.py       # Database model tests
    test_webhooks.py     # Webhook handler tests
  ```

- [ ] Configure pytest in `backend/pytest.ini`:
  - Set test paths
  - Configure coverage reporting
  - Set up async test support

**Afternoon (1pm-5pm):**
- [ ] Create fixtures in `conftest.py`:
  - Database session fixture (with rollback)
  - FastAPI test client fixture
  - Web3 mock fixture
  - Sample user fixture
  - Sample transaction fixture

- [ ] Set up test database:
  - Create `haven_test` database
  - Run migrations
  - Add test data seed script

**Deliverables:**
- ✅ Test infrastructure configured
- ✅ Fixtures created and tested
- ✅ Test database operational

---

### Tuesday (Day 7): API Endpoint Tests

**Morning (9am-12pm):**
- [ ] Write tests for token operations endpoints:
  - `POST /token/mint` (success, auth failure, validation)
  - `POST /token/redeem` (success, insufficient balance, KYC check)
  - `GET /token/balance/{user_id}` (found, not found, invalid ID)

**Afternoon (1pm-5pm):**
- [ ] Write tests for analytics endpoints:
  - `GET /analytics/user/{user_id}`
  - `GET /analytics/token-stats`
  - `GET /analytics/transactions/{user_id}` (pagination)

**Evening (if needed):**
- [ ] Write tests for health endpoints:
  - `GET /health` (all services up, DB down, blockchain down)
  - `GET /` (version info)

**Test Coverage Target:** 40%

**Deliverables:**
- ✅ 30+ API endpoint tests
- ✅ All happy paths covered
- ✅ Error cases validated

---

### Wednesday (Day 8): Service Layer Tests - TokenAgent

**Morning (9am-12pm):**
- [ ] Write TokenAgent tests (`test_services.py`):
  - `process_mint()`:
    - Successful mint
    - Idempotency check (duplicate prevention)
    - Insufficient gas
    - Transaction timeout
    - Invalid wallet address

- [ ] Mock Web3 interactions:
  - Mock contract calls
  - Mock transaction receipts
  - Mock gas estimation

**Afternoon (1pm-5pm):**
- [ ] Write TokenAgent burn tests:
  - `process_burn()` success
  - Insufficient balance
  - User approval check

- [ ] Write balance query tests:
  - `get_balance()` for valid address
  - Invalid address handling
  - RPC connection failure

**Test Coverage Target:** 55%

**Deliverables:**
- ✅ TokenAgent fully tested
- ✅ Web3 mocking strategy proven
- ✅ Blockchain interaction coverage

---

### Thursday (Day 9): Service Layer Tests - Integrations

**Morning (9am-12pm):**
- [ ] Write Aurora integration tests:
  - `on_booking_created()`:
    - New user wallet creation
    - Token minting with 2 HNV/CAD rate
    - Multi-night bonus (1.2x multiplier)
    - Database record creation
  - `on_booking_completed()` status update
  - `on_booking_cancelled()` token burn
  - `on_review_submitted()` 50 HNV bonus

**Afternoon (1pm-5pm):**
- [ ] Write Tribe integration tests:
  - `on_event_attendance()` tiered rewards
  - `on_contribution()` quality scoring
  - `on_staking_started()` 10% APY calculation
  - `on_coaching_milestone()` tiered rewards
  - `on_referral_success()` tiered bonuses

**Test Coverage Target:** 65%

**Deliverables:**
- ✅ Aurora integration fully tested
- ✅ Tribe integration fully tested
- ✅ Reward calculation accuracy verified

---

### Friday (Day 10): Webhook Tests & CI/CD

**Morning (9am-12pm):**
- [ ] Write webhook signature tests:
  - Valid signature acceptance
  - Invalid signature rejection
  - Expired timestamp rejection
  - Replay attack prevention

- [ ] Write webhook handler tests:
  - All 9 webhook endpoints
  - Concurrent webhook handling
  - Idempotency key validation
  - Error handling and retries

**Afternoon (1pm-5pm):**
- [ ] Update GitHub Actions for backend tests:
  - Modify `.github/workflows/backend-ci.yml`
  - Remove `continue-on-error: true`
  - Make tests mandatory
  - Add coverage requirement (60% minimum)

- [ ] Run full test suite:
  ```bash
  pytest tests/ -v --cov=. --cov-report=html --cov-report=xml
  ```

**Test Coverage Target:** 70%

**Deliverables:**
- ✅ All webhooks tested
- ✅ CI/CD enforcing tests
- ✅ 70%+ coverage achieved

---

### Week 2 Success Criteria

**Must Complete:**
- [x] 100+ backend tests written and passing
- [x] 70%+ code coverage (exceeded 60% target)
- [x] GitHub Actions running tests automatically
- [x] Tests failing = pipeline fails (no continue-on-error)

**Metrics:**
- Test count: 100+
- Coverage: 70%+
- CI/CD: Enforced

---

## Week 3: Integration Testing

### Overview
**Goal:** Validate end-to-end flows, reach 80% backend coverage
**Duration:** November 22-29, 2025
**Team:** Backend Engineer (1.5 FTE), QA Engineer (2.0 FTE)

### Monday-Tuesday (Days 11-12): Critical Integration Flows

**Monday:**
- [ ] Write integration tests for booking flow:
  - Aurora webhook → Backend API → Database → Blockchain
  - Verify token minted on-chain
  - Verify database record created
  - Verify balance updated
  - Test flow with real testnet transaction

**Tuesday:**
- [ ] Write integration tests for redemption flow:
  - User request → Balance check → Burn transaction → Payout
  - Verify 2% burn applied
  - Verify transaction logged
  - Verify user balance decreased
  - Test with real testnet burn

**Deliverables:**
- ✅ 2 critical flows validated with real blockchain

---

### Wednesday-Thursday (Days 13-14): Comprehensive Integration Suite

**Wednesday:**
- [ ] Test concurrent operations:
  - Multiple mint requests simultaneously
  - Database transaction isolation
  - Nonce management for blockchain transactions
  - Race condition testing

**Thursday:**
- [ ] Test failure scenarios:
  - RPC connection failure → retry logic
  - Database connection failure → rollback
  - Transaction timeout → status tracking
  - Webhook delivery failure → queue retry

**Deliverables:**
- ✅ Concurrency handling validated
- ✅ Failure recovery tested

---

### Friday (Day 15): End-to-End User Journeys

- [ ] Implement E2E test: New Guest Journey
  - Day 1: User books hostel → tokens minted
  - Day 3: User checks out → booking marked complete
  - Day 5: User leaves review → bonus tokens minted
  - Day 14: User redeems tokens → burn transaction

- [ ] Implement E2E test: Community Builder Journey
  - Day 1: Attend event → tokens earned
  - Day 7: Submit contribution → tokens earned
  - Day 14: Start staking → 10% APY initiated
  - Day 30: Collect staking rewards

- [ ] Run all E2E tests on testnet

**Deliverables:**
- ✅ 3 E2E journeys passing
- ✅ 80%+ backend coverage

---

### Week 3 Success Criteria

**Must Complete:**
- [x] 15 critical integration flows validated
- [x] 3 E2E user journeys passing
- [x] 80%+ backend test coverage
- [x] All tests using real testnet transactions

---

## Week 4: Security Audit Kickoff

### Overview
**Goal:** Commission external audit, prepare audit materials
**Duration:** November 29 - December 6, 2025
**Team:** Smart Contract Engineer (1.0 FTE), Product Lead (0.5 FTE)

### Monday (Day 16): Audit Firm Selection

**Tasks:**
- [ ] Request quotes from audit firms:
  - CertiK: audit@certik.com
  - Hacken: contact@hacken.io
  - Code4rena: security@code4rena.com

- [ ] Compare proposals:
  - Cost ($20K-$45K range)
  - Timeline (2-4 weeks)
  - Scope (smart contracts + backend review)
  - Deliverables (report, re-test, sign-off)

- [ ] Select audit partner
- [ ] Negotiate contract terms
- [ ] Sign engagement letter

**Deliverables:**
- ✅ Audit contract signed
- ✅ Kickoff meeting scheduled

---

### Tuesday-Wednesday (Days 17-18): Audit Preparation

**Tuesday:**
- [ ] Package smart contract code:
  - Create audit branch in git
  - Include all contracts and dependencies
  - Document contract architecture
  - List all external calls and integrations

- [ ] Create threat model document:
  - Identify attack surfaces
  - List assumptions and trust boundaries
  - Document known limitations
  - Prioritize areas for review

**Wednesday:**
- [ ] Prepare technical documentation for auditors:
  - Architecture diagrams (contract, backend, database)
  - Data flow diagrams
  - Sequence diagrams for critical operations
  - List of all roles and permissions

- [ ] Document testing approach:
  - Test coverage reports
  - List of all test scenarios
  - Known edge cases
  - Areas of uncertainty

**Deliverables:**
- ✅ Audit package complete
- ✅ Documentation submitted to auditors

---

### Thursday-Friday (Days 19-20): Internal Security Review

**Thursday:**
- [ ] Run static analysis tools:
  ```bash
  pip install slither-analyzer mythril
  slither . --hardhat-ignore-compile
  myth analyze contracts/contracts/HAVEN.sol
  ```

- [ ] Review all findings:
  - Categorize by severity
  - Document false positives
  - Create remediation plan for real issues

**Friday:**
- [ ] Conduct penetration testing on API:
  - Test authentication bypass attempts
  - SQL injection attempts (should fail)
  - Rate limit bypass attempts
  - Webhook forgery attempts

- [ ] Create internal security report:
  - List all findings
  - Document mitigations
  - Track remediation status

**Deliverables:**
- ✅ Static analysis complete
- ✅ Penetration test results
- ✅ Internal security report

---

### Week 4 Success Criteria

**Must Complete:**
- [x] Audit firm selected and contracted
- [x] Code and documentation submitted to auditors
- [x] Internal security review complete
- [x] Audit in progress

---

## Week 5: Performance & Load Testing

### Overview
**Goal:** Validate system can handle production load
**Duration:** December 6-13, 2025
**Team:** Backend Engineer (1.5 FTE), DevOps Engineer (1.0 FTE), QA Engineer (1.0 FTE)

### Monday-Tuesday (Days 21-22): Load Test Development

**Monday:**
- [ ] Set up load testing infrastructure:
  - Install JMeter and Locust
  - Configure test data generators
  - Set up monitoring (Prometheus + Grafana)

- [ ] Define load test scenarios:
  - API endpoint throughput (500 RPS target)
  - Database query performance
  - Blockchain transaction rate (100 tx/min target)
  - Concurrent webhook handling (100 webhooks in 1 second)

**Tuesday:**
- [ ] Create JMeter test plans:
  - Ramp-up: 0 → 1,000 users over 5 minutes
  - Sustained load: 1,000 users for 30 minutes
  - Spike test: 2,000 users for 5 minutes
  - Stress test: increase until failure

- [ ] Create Locust scenarios:
  - Booking creation flow
  - Token redemption flow
  - Balance query flow
  - Mixed workload (realistic distribution)

**Deliverables:**
- ✅ Load test infrastructure ready
- ✅ Test scenarios defined

---

### Wednesday-Thursday (Days 23-24): Load Test Execution

**Wednesday:**
- [ ] Run API load tests:
  - Execute JMeter test plans
  - Monitor API response times
  - Track error rates
  - Measure throughput (requests/second)

- [ ] Collect metrics:
  - p50, p95, p99 response times
  - Error rate percentage
  - Maximum throughput achieved
  - Resource utilization (CPU, memory, DB connections)

**Thursday:**
- [ ] Run database stress tests:
  - Concurrent read/write operations
  - Connection pool exhaustion test
  - Query performance under load
  - Index effectiveness validation

- [ ] Run blockchain transaction tests:
  - Sequential minting (100 tx/min)
  - Nonce management under load
  - Gas price fluctuation handling
  - Transaction confirmation monitoring

**Success Criteria:**
- API p99 latency: <500ms ✓
- Throughput: 500 RPS ✓
- Concurrent users: 1,000 sustained ✓
- Error rate: <0.1% ✓

**Deliverables:**
- ✅ Load test results documented
- ✅ Performance baselines established

---

### Friday (Day 25): Performance Optimization

- [ ] Analyze load test results:
  - Identify bottlenecks
  - Review slow database queries
  - Check API endpoint performance
  - Evaluate blockchain transaction efficiency

- [ ] Implement optimizations:
  - Add database indexes for slow queries
  - Configure connection pooling (pool_size=20, max_overflow=40)
  - Implement Redis caching for balance queries (5-min TTL)
  - Optimize blockchain gas estimation

- [ ] Re-run load tests to verify improvements

**Deliverables:**
- ✅ System optimized for production load
- ✅ Performance targets met

---

### Week 5 Success Criteria

**Must Complete:**
- [x] Load tests executed successfully
- [x] System handles 1,000 concurrent users
- [x] API p99 latency <500ms
- [x] Throughput >500 RPS
- [x] Performance optimizations implemented

---

## Week 6: Audit Response & Remediation

### Overview
**Goal:** Address all audit findings, achieve audit sign-off
**Duration:** December 13-20, 2025
**Team:** Smart Contract Engineer (1.5 FTE), Backend Engineer (1.0 FTE), Product Lead (0.5 FTE)

### Monday (Day 26): Audit Report Review

- [ ] Receive audit report from auditors
- [ ] Review all findings:
  - Critical severity issues
  - High severity issues
  - Medium severity issues
  - Low severity issues
  - Informational notes

- [ ] Triage findings:
  - Categorize by impact and urgency
  - Identify false positives (justify)
  - Create remediation plan
  - Estimate effort for each fix

- [ ] Schedule team review meeting:
  - Discuss findings with team
  - Assign remediation tasks
  - Set deadlines for fixes

**Deliverables:**
- ✅ Audit report reviewed
- ✅ Remediation plan created

---

### Tuesday-Thursday (Days 27-29): Fix Critical & High Issues

**Tuesday:**
- [ ] Fix all Critical severity findings:
  - Update smart contract code
  - Add regression tests
  - Document changes
  - Verify fixes with unit tests

**Wednesday:**
- [ ] Fix all High severity findings:
  - Implement recommended changes
  - Update tests
  - Verify no new issues introduced
  - Code review by second engineer

**Thursday:**
- [ ] Address Medium severity findings:
  - Prioritize highest impact items
  - Implement fixes
  - Update documentation
  - Test thoroughly

**Testing:**
- [ ] Run full test suite after each fix
- [ ] Verify coverage maintained >90%
- [ ] Ensure no regressions introduced

**Deliverables:**
- ✅ All Critical/High findings resolved
- ✅ Tests updated and passing

---

### Friday (Day 30): Re-Audit & Sign-Off

- [ ] Submit fixes to auditors:
  - Create remediation branch
  - Document all changes
  - Provide line-by-line explanation
  - Submit for re-audit

- [ ] Auditor re-review:
  - Verify fixes implemented correctly
  - Confirm vulnerabilities resolved
  - Final security assessment

- [ ] Receive final audit report:
  - Sign-off from auditors
  - Final security rating
  - Publish audit report (optional)

**Deliverables:**
- ✅ Audit sign-off received
- ✅ Final audit report obtained
- ✅ All findings addressed

---

### Week 6 Success Criteria

**Must Complete:**
- [x] All Critical findings resolved
- [x] All High findings resolved
- [x] Audit sign-off obtained
- [x] Final audit report received

---

## Week 7: Mainnet Preparation

### Overview
**Goal:** Final validation, infrastructure setup, legal compliance
**Duration:** December 20-27, 2025
**Team:** Full team (5.5 FTE)

### Monday-Tuesday (Days 31-32): Final Testing & Validation

**Monday:**
- [ ] Run complete test suite:
  ```bash
  # Smart contracts
  cd contracts && npm test && npm run coverage

  # Backend
  cd backend && pytest tests/ -v --cov=. --cov-report=term
  ```

- [ ] Verify test results:
  - 265+ tests passing ✓
  - 90%+ code coverage ✓
  - Zero critical vulnerabilities ✓

**Tuesday:**
- [ ] Security regression testing:
  - Re-run Slither and Mythril
  - Verify all previous findings remain fixed
  - Penetration test on production configuration

- [ ] Smoke test all critical flows on testnet:
  - Booking → mint
  - Review → bonus
  - Redemption → burn
  - All 15 critical integration flows

**Deliverables:**
- ✅ All tests passing
- ✅ Security validated
- ✅ Testnet fully functional

---

### Wednesday (Day 33): Infrastructure Setup

**Morning:**
- [ ] Set up production database:
  - Provision PostgreSQL 15 on cloud (AWS RDS or GCP Cloud SQL)
  - Configure backups (daily snapshots, 30-day retention)
  - Set up read replicas for scaling
  - Configure connection pooling
  - Run migrations

**Afternoon:**
- [ ] Set up monitoring and alerting:
  - Deploy Prometheus + Grafana
  - Configure dashboards:
    - API metrics (latency, throughput, errors)
    - Blockchain metrics (tx/min, gas prices, confirmations)
    - Database metrics (connections, query time, locks)
  - Set up Slack alerts for:
    - API errors >1%
    - Blockchain transaction failures
    - Database connection issues
    - High gas prices (>10 gwei)

**Evening:**
- [ ] Set up error tracking:
  - Configure Sentry for backend
  - Test error reporting
  - Set up error alerts

**Deliverables:**
- ✅ Production database operational
- ✅ Monitoring dashboards live
- ✅ Alerting configured

---

### Thursday (Day 34): Multi-Sig & Security Setup

**Morning:**
- [ ] Deploy Gnosis Safe multi-sig wallet:
  - Go to https://safe.global
  - Create 2-of-3 multi-sig on Base mainnet
  - Add 3 signers:
    - Technical Lead wallet
    - Product Lead wallet
    - Operations Lead wallet
  - Fund with 0.01 ETH for operations

**Afternoon:**
- [ ] Prepare deployer wallet:
  - Generate fresh wallet for deployment
  - Fund with 0.002 ETH (for deployment + gas buffer)
  - Verify balance:
    ```bash
    cast balance YOUR_ADDRESS --rpc-url https://mainnet.base.org
    ```

**Evening:**
- [ ] Set up GitHub Secrets for mainnet:
  - `BASE_MAINNET_RPC` (Alchemy production URL)
  - `DEPLOYER_PRIVATE_KEY_MAINNET` (deployer wallet)
  - `BACKEND_SERVICE_ADDRESS_MAINNET` (backend signer)
  - `BASESCAN_API_KEY`
  - `SLACK_WEBHOOK_URL` (for deployment notifications)

**Deliverables:**
- ✅ Multi-sig wallet configured
- ✅ Deployer wallet funded
- ✅ GitHub Secrets configured

---

### Friday (Day 35): Legal & Compliance

**Morning:**
- [ ] Obtain legal opinion on token classification:
  - Engage legal counsel (if not already)
  - Review Howey Test analysis
  - Confirm utility token classification
  - Document legal opinion

**Afternoon:**
- [ ] Review and finalize compliance documents:
  - Terms of Service
  - Privacy Policy
  - Token Usage Agreement
  - KYC/AML procedures for redemptions

**Evening:**
- [ ] Final go/no-go checklist review:
  - [ ] All tests passing (265+)
  - [ ] Coverage >90%
  - [ ] Audit sign-off obtained
  - [ ] Load tests passed
  - [ ] Multi-sig configured
  - [ ] Monitoring operational
  - [ ] Legal opinion obtained
  - [ ] Team trained on procedures

**Deliverables:**
- ✅ Legal compliance verified
- ✅ All documents finalized
- ✅ Go/no-go checklist complete

---

### Week 7 Success Criteria

**Must Complete:**
- [x] All 265+ tests passing
- [x] Production infrastructure ready
- [x] Multi-sig wallet configured
- [x] Legal compliance verified
- [x] Team ready for launch

---

## Week 8: Mainnet Launch

### Overview
**Goal:** Deploy to Base mainnet, beta testing, public launch
**Duration:** December 27, 2025 - January 3, 2026
**Team:** Full team (5.5 FTE) + On-call rotation

### Monday (Day 36): Mainnet Deployment

**Morning (9am-11am): Pre-Deployment**
- [ ] Final security review:
  - Review all code changes since audit
  - Verify no new vulnerabilities introduced
  - Check GitHub Actions workflows configured correctly

- [ ] Verify environment:
  - All GitHub Secrets set
  - Deployer wallet has sufficient ETH
  - Multi-sig wallet ready
  - Backend infrastructure ready

**Late Morning (11am-12pm): Deployment**
- [ ] Trigger mainnet deployment via GitHub Actions:
  - Go to Actions → Deploy to Mainnet
  - Input: `"DEPLOY TO MAINNET"`
  - Wait for pre-deployment checks to pass
  - Deployment executes automatically

- [ ] Monitor deployment:
  - Watch GitHub Actions logs
  - Monitor deployer wallet on Basescan
  - Verify contract deployment transaction

**Afternoon (1pm-3pm): Post-Deployment Verification**
- [ ] Verify contract on Basescan:
  - Contract source code verified ✓
  - Roles granted correctly ✓
  - Initial state correct (0 supply) ✓

- [ ] Transfer admin to multi-sig:
  - Grant DEFAULT_ADMIN_ROLE to multi-sig
  - Revoke DEFAULT_ADMIN_ROLE from deployer
  - Verify roles on Basescan

**Late Afternoon (3pm-5pm): Backend Connection**
- [ ] Update backend environment:
  - Set `HAVEN_CONTRACT_ADDRESS` to mainnet address
  - Set `CHAIN_ID=8453`
  - Set `RPC_URL` to mainnet RPC
  - Deploy backend to production server

- [ ] Run smoke tests:
  - Mint 1 HNV to test address
  - Verify transaction on Basescan
  - Check balance query works
  - Burn 0.5 HNV
  - Verify database synced

**Deliverables:**
- ✅ Contract deployed to Base mainnet
- ✅ Contract verified on Basescan
- ✅ Admin transferred to multi-sig
- ✅ Backend connected and tested

---

### Tuesday (Day 37): Monitoring & Validation

**All Day:**
- [ ] Monitor mainnet activity:
  - Watch all transactions in Basescan
  - Monitor error logs in Sentry
  - Track API metrics in Grafana
  - Verify database syncing correctly

- [ ] Run extended smoke tests:
  - Test all 16 API endpoints
  - Verify all webhooks working
  - Test concurrent operations
  - Verify monitoring alerts working

**Evening:**
- [ ] Team review meeting:
  - Review deployment success
  - Discuss any issues encountered
  - Plan for beta launch tomorrow

**Deliverables:**
- ✅ 24 hours of mainnet operation successful
- ✅ All systems healthy

---

### Wednesday (Day 38): Internal Beta Launch

**Morning (9am-12pm): Beta User Onboarding**
- [ ] Send onboarding emails to 50 internal users:
  - Welcome message
  - How to earn tokens
  - How to check balance
  - How to redeem tokens
  - Support channel (#haven-beta on Slack)

- [ ] Distribute initial test tokens:
  - Mint 100 HNV to each beta user
  - Monitor minting transactions
  - Verify all distributions successful

**Afternoon (1pm-5pm): Real-Time Monitoring**
- [ ] Monitor all beta user activity:
  - Track bookings and token minting
  - Watch for errors or issues
  - Respond to support questions in #haven-beta
  - Collect feedback

**Evening (5pm-8pm):**
- [ ] Review beta metrics:
  - Number of transactions
  - Average transaction time
  - Error rate
  - User feedback sentiment

**Deliverables:**
- ✅ 50 beta users onboarded
- ✅ 100+ transactions processed
- ✅ No critical issues

---

### Thursday (Day 39): Hostels United Pilot

**Morning:**
- [ ] Onboard 3-5 pilot hostels:
  - Provide integration documentation
  - Configure Aurora PMS webhooks
  - Test booking flow end-to-end
  - Train hostel staff on token system

**Afternoon:**
- [ ] Monitor pilot hostel transactions:
  - First real guest booking → token mint
  - Verify rewards calculated correctly
  - Track guest satisfaction
  - Collect hostel feedback

**Evening:**
- [ ] Analyze pilot results:
  - Number of bookings processed
  - Tokens minted per hostel
  - Average rewards per guest
  - Issues encountered
  - Feedback summary

**Deliverables:**
- ✅ 3-5 hostels onboarded
- ✅ Real guest transactions processed
- ✅ Pilot feedback collected

---

### Friday (Day 40): Public Launch 🚀

**Morning (9am-11am): Final Pre-Launch Checks**
- [ ] Verify system health:
  - All services operational ✓
  - Monitoring dashboards green ✓
  - Support team ready ✓
  - Documentation published ✓

- [ ] Prepare launch communications:
  - Blog post finalized
  - Social media posts scheduled
  - Email campaign ready
  - Press release (if applicable)

**Late Morning (11am-12pm): Launch Communications**
- [ ] Publish launch materials:
  - Blog post on website
  - Tweet announcement
  - LinkedIn post
  - Email to user base (10,000+ subscribers)
  - Update website with HAVEN info

**Afternoon (12pm-5pm): Public Launch**
- [ ] Monitor launch activity:
  - Track new user registrations
  - Monitor transaction volume
  - Watch for error spikes
  - Respond to support inquiries

- [ ] Launch bug bounty program:
  - Publish on Immunefi
  - Set rewards: $10K (Medium) to $50K (Critical)
  - Publicize responsible disclosure policy
  - Monitor submissions

**Evening (5pm-8pm): Celebration & Monitoring**
- [ ] Team celebration 🎉
  - Reflect on achievement
  - Celebrate successful launch
  - Thank team members

- [ ] Continue monitoring:
  - 24/7 on-call rotation begins
  - Monitor all systems
  - Track launch metrics

**Launch Day Metrics:**
- New users onboarded: _____
- Transactions processed: _____
- Tokens minted: _____
- System uptime: _____
- Average response time: _____

**Deliverables:**
- ✅ Public launch complete
- ✅ Bug bounty live
- ✅ Monitoring operational
- ✅ On-call rotation active

---

### Week 8 Success Criteria

**Must Complete:**
- [x] Mainnet contract deployed and verified
- [x] 50 beta users successfully onboarded
- [x] 3-5 pilot hostels operational
- [x] Public launch executed
- [x] Bug bounty program live
- [x] 24/7 monitoring active

**Launch Metrics:**
- Beta users: 50
- Pilot hostels: 3-5
- Day 1 transactions: 100+ (target)
- System uptime: >99.9%
- Critical errors: 0

---

## Post-Launch: Weeks 9-10

### Week 9: Stabilization & Support

**Daily Tasks:**
- [ ] Monitor all metrics:
  - Active users
  - Transaction volume
  - Error rates
  - API uptime
  - Gas costs
  - User support tickets

- [ ] Respond to issues:
  - Triage bug reports
  - Fix critical bugs immediately
  - Schedule minor bug fixes
  - Update documentation

**Weekly Review (Friday):**
- [ ] Review Week 1 metrics:
  - Users onboarded: _____
  - Tokens minted: _____
  - Transactions: _____
  - Uptime: _____
  - Support tickets: _____
  - Average resolution time: _____

**Deliverables:**
- ✅ First week of production successful
- ✅ All critical issues resolved
- ✅ User satisfaction high (NPS >40 target)

---

### Week 10: 30-Day Review & Optimization

**Goals:**
- Measure against success criteria
- Plan optimizations
- Prepare for scaling

**Tasks:**
- [ ] Conduct 30-day review:
  - Active users: 1,000 (target)
  - Total HNV minted: 100,000 (target)
  - Total transactions: 5,000 (target)
  - API uptime: >99.9% (target)
  - Gas per tx: <$0.50 (target)
  - User NPS: >40 (target)

- [ ] User NPS survey:
  - Send survey to all users
  - Collect feedback
  - Analyze results
  - Plan improvements

- [ ] System performance review:
  - Analyze performance metrics
  - Identify optimization opportunities
  - Plan scaling strategy
  - Document lessons learned

**Deliverables:**
- ✅ 30-day review complete
- ✅ Success criteria met/measured
- ✅ Optimization plan created

---

## Success Metrics: 30 Days Post-Launch

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Active Users | 1,000 | _____ | ⬜ |
| Total HNV Minted | 100,000 | _____ | ⬜ |
| Total Transactions | 5,000 | _____ | ⬜ |
| API Uptime | >99.9% | _____% | ⬜ |
| Support SLA (<24h) | >95% | _____% | ⬜ |
| Gas Cost per TX | <$0.50 | $_____ | ⬜ |
| User NPS | >40 | _____ | ⬜ |

---

## Resource Allocation

### Team Composition (5.5 FTE)

**Backend Engineer (2.0 FTE):**
- Weeks 1-2: Security fixes, testing (80 hours)
- Weeks 3-4: Integration testing (80 hours)
- Weeks 5-6: Load testing, optimization (80 hours)
- Weeks 7-8: Production support (80 hours)
- **Total: 320 hours**

**QA Engineer (1.5 FTE):**
- Weeks 1-2: Test infrastructure, API tests (60 hours)
- Weeks 3-4: Integration tests, E2E journeys (60 hours)
- Weeks 5-6: Load test execution (60 hours)
- Weeks 7-8: Final validation, beta testing (60 hours)
- **Total: 240 hours**

**Smart Contract Engineer (0.5 FTE):**
- Week 1: Test fixes (20 hours)
- Weeks 4-6: Audit support, remediation (60 hours)
- Week 7-8: Mainnet deployment support (20 hours)
- **Total: 100 hours**

**DevOps Engineer (0.5 FTE):**
- Weeks 1-2: CI/CD improvements (20 hours)
- Week 5: Load test infrastructure (20 hours)
- Week 7: Production infrastructure setup (30 hours)
- Week 8: Deployment, monitoring (10 hours)
- **Total: 80 hours**

**Product/Test Lead (1.0 FTE):**
- Weeks 1-8: Planning, coordination, reviews (160 hours)
- Weeks 4, 7-8: Audit coordination, legal, launch (80 hours)
- **Total: 240 hours**

**Grand Total: 980 hours across 8 weeks**

---

## Budget Breakdown

### Team Costs
- Backend Engineer: 320 hrs × $125/hr = $40,000
- QA Engineer: 240 hrs × $100/hr = $24,000
- Smart Contract Engineer: 100 hrs × $150/hr = $15,000
- DevOps Engineer: 80 hrs × $120/hr = $9,600
- Product/Test Lead: 240 hrs × $110/hr = $26,400
- **Subtotal: $115,000**

### External Costs
- Security Audit: $25,000 - $45,000
- Load Testing Infrastructure: $4,000 (2 months)
- Production Infrastructure (first month): $2,000
- Monitoring Tools (Sentry, Grafana Cloud): $1,000
- Bug Bounty Program: $10,000 - $50,000 (reserve)
- **Subtotal: $42,000 - $102,000**

### Total Budget
**Conservative: $157,000**
**Optimistic: $217,000**

**Recommended Budget: $175,000** (includes 20% contingency)

---

## Risk Management

### High-Risk Scenarios

**1. Audit Finds Critical Vulnerability**
- **Likelihood:** Medium (30%)
- **Impact:** High (2-4 week delay)
- **Mitigation:**
  - Already fixed known issues in Week 1
  - Conducted internal security review
  - Budget 2 weeks for remediation
- **Action if occurs:** Delay launch, fix immediately, re-audit

**2. Load Tests Reveal Performance Issues**
- **Likelihood:** Low (20%)
- **Impact:** Medium (1-2 week delay)
- **Mitigation:**
  - Test early (Week 5)
  - Budget time for optimization
  - Can scale infrastructure if needed
- **Action if occurs:** Optimize code, scale infrastructure, re-test

**3. Team Member Unavailable**
- **Likelihood:** Medium (40%)
- **Impact:** Medium (varies)
- **Mitigation:**
  - Cross-train team members
  - Document all processes
  - Have backup contractors identified
- **Action if occurs:** Shift responsibilities, bring in contractor

**4. External Dependency Failure (Alchemy, Base)**
- **Likelihood:** Low (10%)
- **Impact:** High (launch blocker)
- **Mitigation:**
  - Have backup RPC providers
  - Test failover before launch
  - Monitor service status
- **Action if occurs:** Switch to backup provider, notify users

**5. Regulatory Changes**
- **Likelihood:** Low (5%)
- **Impact:** Critical (major redesign)
- **Mitigation:**
  - Legal counsel engaged
  - Monitor regulatory developments
  - Design with compliance in mind
- **Action if occurs:** Consult legal, pause launch if needed

---

## Communication Plan

### Daily Standups (15 min, 10am PT)
**Format:**
- Each person shares:
  - Yesterday's accomplishments
  - Today's tasks
  - Blockers
- Quick decisions, no deep dives
- Recorded in Slack #haven-standup

### Weekly Reviews (30 min, Fridays 4pm PT)
**Agenda:**
1. Review week's deliverables (10 min)
2. Demo progress (10 min)
3. Plan next week (5 min)
4. Risks and concerns (5 min)

### Milestone Reviews (1 hour)
- End of Week 2: Security + Testing
- End of Week 4: Audit Kickoff
- End of Week 6: Audit Complete
- End of Week 7: Pre-Launch Review

### Launch Day Communication
- Real-time updates in Slack #haven-launch
- Status emails to stakeholders every 4 hours
- Public status page (if applicable)

---

## Quality Gates

### Week 1 Gate
**Go/No-Go Criteria:**
- [ ] All 32 contract tests passing (100%)
- [ ] 6 critical security fixes implemented
- [ ] Contract deployed to Base Sepolia
- [ ] Documentation updated
- **Decision:** Product Lead + Tech Lead

### Week 4 Gate
**Go/No-Go Criteria:**
- [ ] 100+ backend tests passing
- [ ] 70%+ code coverage
- [ ] Audit contract signed
- [ ] Code submitted to auditors
- **Decision:** Product Lead + Security Team

### Week 6 Gate
**Go/No-Go Criteria:**
- [ ] Audit sign-off received
- [ ] All Critical/High findings resolved
- [ ] Load tests passed
- [ ] 80%+ integration test coverage
- **Decision:** Product Lead + Tech Lead + Legal

### Week 7 Gate (MAINNET GO/NO-GO)
**Go/No-Go Criteria:**
- [ ] All 265+ tests passing
- [ ] 90%+ code coverage
- [ ] Zero Critical vulnerabilities
- [ ] Audit sign-off obtained
- [ ] Load tests: 1K users, 500 RPS
- [ ] Multi-sig configured
- [ ] Monitoring operational
- [ ] Legal compliance verified
- **Decision:** CEO/Founder + Product Lead + Tech Lead + Legal

**If ANY criteria not met:** NO-GO, delay launch

---

## Incident Response

### Severity Levels

**P0 - Critical (Response: Immediate)**
- Security breach or vulnerability
- Funds at risk
- Complete system outage
- **Action:** Page on-call engineer, assemble team within 30 min

**P1 - High (Response: <1 hour)**
- Partial system outage
- Major feature broken
- Performance severely degraded
- **Action:** On-call engineer responds, escalate to team lead

**P2 - Medium (Response: <4 hours)**
- Minor feature broken
- Performance degraded but usable
- Non-critical errors
- **Action:** Create ticket, assign to appropriate engineer

**P3 - Low (Response: <24 hours)**
- Minor bugs
- Documentation issues
- Feature requests
- **Action:** Add to backlog, prioritize in planning

### Escalation Path

1. **On-Call Engineer** (first responder)
   ↓ (if unresolved in 30 min)
2. **Tech Lead** (technical decisions)
   ↓ (if requires business decision or >2 hour outage)
3. **Product Lead** (business decisions, communications)
   ↓ (if requires emergency spending or major decision)
4. **CEO/Founder** (final authority)

### Emergency Contacts

- **Tech Lead:** [Phone] [Email]
- **Product Lead:** [Phone] [Email]
- **On-Call Rotation:** See #haven-oncall channel
- **Legal Counsel:** [Email] (non-emergency)

### Emergency Procedures

**Contract Pause (Security Breach):**
1. Multi-sig signers execute `pause()` function
2. Notify users via Slack/email/status page
3. Investigate issue
4. Fix and test
5. Execute `unpause()` via multi-sig
6. Post-mortem within 48 hours

**Backend Outage:**
1. Check monitoring dashboards
2. Review error logs in Sentry
3. Restart services if needed
4. Investigate root cause
5. Fix and deploy
6. Monitor for recurrence

---

## Conclusion

This 8-week plan provides a comprehensive roadmap from the current state (85% complete) to a secure, tested, production deployment on Base mainnet. The plan:

- **Addresses all critical security vulnerabilities** identified by the agent team
- **Implements comprehensive testing** (265+ tests, 90%+ coverage)
- **Includes external security audit** with remediation time
- **Validates performance and scalability** through load testing
- **Ensures legal and compliance requirements** are met
- **Provides detailed week-by-week execution plan** with clear deliverables

**Key Success Factors:**
1. Team commitment and availability
2. Timely audit completion and findings remediation
3. Passing all quality gates before proceeding
4. Effective communication and coordination
5. Flexibility to adjust timeline if needed

**Expected Outcome:**
A secure, performant, compliant token system ready for public use, launching in Q1 2026 as planned.

---

**Let's build the currency of belonging. 🚀**

---

**Next Steps:**
1. Review and approve this plan with stakeholders
2. Assemble team and confirm availability
3. Kick off Week 1 tasks
4. Begin daily standups and weekly reviews

**Questions?** Contact Product Lead or Tech Lead

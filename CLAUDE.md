# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HAVEN Token is an ERC-20 utility token on Base (Ethereum Layer-2) that powers the PVT hospitality ecosystem. The project consists of:

- **Smart Contracts** (Solidity/Hardhat): ERC-20 token with role-based access control, minting, burning, and governance features
- **Backend API** (Python/FastAPI): RESTful API for token operations, webhooks, and integrations with Aurora PMS and Tribe App
- **Database** (PostgreSQL): User accounts, transactions, bookings, events, staking, and redemptions

**Key Facts:**
- Token: 1B total supply (fixed), 100M initial circulation (10%)
- Blockchain: Base (Chain ID 8453) and Base Sepolia testnet (Chain ID 84532)
- Burn rate: 2% per redemption (deflationary)
- Base value: 0.10 CAD (~$0.07 USD)

## Development Commands

### Smart Contracts (contracts/)

```bash
# Install dependencies
npm install

# Compile contracts
npm run compile

# Run tests
npm test

# Run tests with coverage
npx hardhat coverage

# Run tests with gas reporting
REPORT_GAS=true npm test

# Deploy to testnet (Base Sepolia)
npm run deploy:testnet

# Deploy to mainnet (Base)
npm run deploy:mainnet

# Verify contract on Basescan
npm run verify

# Start local Hardhat node
npx hardhat node

# Deploy to local node
npx hardhat run scripts/deploy.ts --network localhost
```

### Backend API (backend/)

```bash
# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server (with auto-reload)
uvicorn app:app --reload

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_token_agent.py -v
```

### Full Project Setup

```bash
# Automated setup (from project root)
./scripts/bootstrap.sh
```

This script checks prerequisites, installs dependencies, sets up databases, and creates environment files.

## Architecture

### Smart Contract Layer

**File:** `contracts/contracts/HAVEN.sol`

The HAVEN token extends OpenZeppelin's ERC20 with:
- **Role-based access control**: 4 roles (MINTER, BURNER, PAUSER, GOVERNANCE)
- **Minting**: Controlled by backend services with MINTER_ROLE, includes audit trail via `MintEvent`
- **Batch minting**: Gas-optimized for up to 100 recipients simultaneously
- **Burning**: User-initiated (`burnWithReason`) or admin (`burnFrom`) with BURNER_ROLE
- **Pausability**: Emergency halt by PAUSER_ROLE
- **Governance timelock**: 7-day delay for parameter changes (e.g., `monthlyMintTarget`)
- **Emission tracking**: `totalMinted`, `totalBurned`, circulating supply

**Key Design Decisions:**
- Fixed supply cap not enforced on-chain (controlled via backend logic and monthly mint targets)
- All minting/burning operations require a `reason` string for audit compliance
- Gas optimization target: <$0.50 per transaction on Base

### Backend Architecture

**Main file:** `backend/app.py` (FastAPI application with 15+ endpoints)

**Services:**
- `token_agent.py`: Blockchain interaction via Web3.py (minting, burning, balance queries)
- `aurora_integration.py`: Aurora PMS webhook handlers (bookings, reviews, referrals)
- `tribe_integration.py`: Tribe App webhook handlers (events, contributions, coaching, staking)

**Database Models** (`backend/database/models.py`):
- `User`: Wallet addresses, KYC status, relationships
- `Transaction`: Token operations with blockchain tx hashes, gas tracking
- `AuroraBooking`: Booking records, reward calculation
- `TribeEvent`: Event participation tracking
- `TribeReward`: Community contribution rewards
- `StakingRecord`: 10% APY staking program
- `RedemptionRequest`: Token-to-fiat redemptions with bank transfer details

**Background Jobs** (APScheduler):
- Daily blockchain sync (reconcile balances)
- Weekly staking reward distributions
- Hourly health checks

### Reward Logic

**Aurora PMS:**
- Base: 2 HNV per CAD spent
- Multi-night bonus: +20% for 3+ nights
- Review: 50 HNV for 4+ star reviews
- Referral: 100-500 HNV (tiered based on booking value)

**Tribe App:**
- Event attendance: 25-100 HNV (tiered by event type)
- Contributions: 5-25 HNV (posts, guides)
- Coaching milestones: 100-250 HNV (tiered)
- Staking: 10% APY for locked tokens

**Redemption:**
- User initiates redemption (HNV → CAD)
- 2% burn fee applied (20 HNV burned per 1000 redeemed)
- Backend processes bank transfer or preferred withdrawal method

## Configuration

### Environment Variables

**contracts/.env:**
```bash
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
BASE_MAINNET_RPC=https://mainnet.base.org
DEPLOYER_PRIVATE_KEY=0x...
BASESCAN_API_KEY=...
```

**backend/.env:**
```bash
# Blockchain
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
HAVEN_CONTRACT_ADDRESS=0x...  # Set after deployment
BACKEND_PRIVATE_KEY=0x...     # Wallet with MINTER_ROLE

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/haven

# External APIs (optional)
STRIPE_API_KEY=...
SLACK_WEBHOOK_URL=...
```

### Network Configuration

Networks are defined in `contracts/hardhat.config.ts`:
- **baseSepolia**: Testnet (Chain ID 84532)
- **base**: Mainnet (Chain ID 8453)
- **localhost**: Local Hardhat node (Chain ID 31337)

## Testing

### Smart Contract Tests

Located in `contracts/test/HAVEN.test.ts`. Covers:
- Role-based access control
- Minting (single and batch)
- Burning (user and admin)
- Pausability
- Governance timelock
- Edge cases and security

Target coverage: >95%

### Backend Tests

Located in `backend/tests/`. Should cover:
- Token agent operations (minting, burning, balance queries)
- Webhook handlers (Aurora, Tribe)
- Database operations
- Authentication and authorization
- Error handling

Run with `pytest tests/ -v`

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

- **contracts-ci.yml**: Runs on contract changes, executes tests, coverage, gas reports
- **backend-ci.yml**: Runs on backend changes, executes tests, linting, security scans
- **deploy-testnet.yml**: Automated testnet deployment (manual trigger)
- **deploy-mainnet.yml**: Mainnet deployment with safety checks (manual trigger, requires approvals)
- **pr-checks.yml**: PR labeling, size tracking, automated test runs

## Security Considerations

- **Never commit private keys**: Use `.env` files (gitignored)
- **Role management**: Only grant MINTER_ROLE to trusted backend wallets
- **Pause mechanism**: Use PAUSER_ROLE for emergency stops
- **Governance timelock**: 7-day delay prevents hasty parameter changes
- **Audit trail**: All mint/burn operations include reason strings
- **Gas limits**: Be mindful when batch minting (max ~100 recipients)

**Pre-mainnet checklist:**
- Complete security audit (CertiK or Code4rena)
- Obtain legal opinion on token classification
- Test all integrations on testnet
- Verify contracts on Basescan
- Set up monitoring and alerting

## Common Patterns

### Minting Tokens (Backend)

```python
# In token_agent.py
tx_hash = await mint_tokens(
    recipient_address="0x...",
    amount=100.0,  # HNV tokens
    reason="booking_reward"
)
```

### Webhook Integration (Aurora PMS)

When Aurora sends a booking webhook to `/webhooks/aurora/booking-created`:
1. Validate webhook signature
2. Calculate reward: `booking_total * 2 HNV/CAD`
3. Apply bonuses (multi-night, etc.)
4. Mint tokens via `token_agent.mint_tokens()`
5. Record in `AuroraBooking` table
6. Return success response

### Database Queries

Use SQLAlchemy ORM. Example:
```python
user = db.query(User).filter_by(user_id="user_123").first()
transactions = db.query(Transaction).filter_by(
    user_id="user_123",
    status="confirmed"
).order_by(Transaction.created_at.desc()).all()
```

## Deployment Workflow

### Testnet Deployment

1. Ensure `contracts/.env` has `BASE_SEPOLIA_RPC` and `DEPLOYER_PRIVATE_KEY`
2. Run `cd contracts && npm run deploy:testnet`
3. Note contract address from output
4. Update `backend/.env` with `HAVEN_CONTRACT_ADDRESS`
5. Grant MINTER_ROLE to backend wallet via Hardhat console
6. Start backend: `cd backend && uvicorn app:app --reload`
7. Test API at `http://localhost:8000/docs`

### Mainnet Deployment

Follow `docs/TIMELINE.md` for 4-week deployment plan. Key steps:
- Week 1: Smart contract audit, legal review
- Week 2: Backend testing, integration testing
- Week 3: Deploy to mainnet, verify contracts
- Week 4: Launch, monitor, iterate

See `docs/SETUP.md` for detailed instructions.

## API Endpoints

**Base URL:** `http://localhost:8000` (development)

**Token Operations:**
- `POST /token/mint`: Mint tokens (requires auth)
- `POST /token/redeem`: Redeem tokens for fiat
- `GET /token/balance/{user_id}`: Get user balance
- `GET /analytics/user/{user_id}`: User analytics
- `GET /analytics/token-stats`: Token-wide statistics

**Webhooks:**
- Aurora: `/webhooks/aurora/booking-created`, `/booking-completed`, `/booking-cancelled`, `/review-submitted`
- Tribe: `/webhooks/tribe/event-attendance`, `/contribution`, `/staking-started`, `/coaching-milestone`, `/referral-success`

**Docs:** `http://localhost:8000/docs` (Swagger UI)

## Documentation

- `README.md`: Project overview, quick start
- `PROJECT_SUMMARY.md`: Complete build summary, metrics
- `docs/HAVEN_Whitepaper.md`: Technical and economic overview (15,000+ words)
- `docs/SETUP.md`: Step-by-step setup guide
- `docs/TIMELINE.md`: 4-week deployment roadmap
- `docs/ROLES.md`: Team roles and responsibilities

## Useful Resources

- **Hardhat Docs**: https://hardhat.org/docs
- **OpenZeppelin Contracts**: https://docs.openzeppelin.com/contracts
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Web3.py Docs**: https://web3py.readthedocs.io
- **Base Network Docs**: https://docs.base.org
- **Basescan Testnet**: https://sepolia.basescan.org
- **Basescan Mainnet**: https://basescan.org

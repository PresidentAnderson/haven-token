# HAVEN Token Setup Guide

Complete guide for setting up the HAVEN Token development environment.

---

## Prerequisites

### Required Software

- **Node.js** >= 18.0.0 ([Download](https://nodejs.org))
- **Python** >= 3.9 ([Download](https://python.org))
- **PostgreSQL** >= 15 ([Download](https://postgresql.org) or use Docker)
- **Git** ([Download](https://git-scm.com))

### Optional (Recommended)

- **Docker** for PostgreSQL and Redis
- **VS Code** with Solidity and Python extensions

---

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd haven-token

# 2. Run bootstrap script
./scripts/bootstrap.sh

# 3. Get API keys (see below)

# 4. Update .env files

# 5. Deploy to testnet
cd contracts && npm run deploy:testnet
```

---

## Detailed Setup

### 1. Get RPC Access (Alchemy)

#### Option A: Alchemy (Recommended)

1. Go to [alchemy.com/signup](https://www.alchemy.com/signup)
2. Create account
3. Create new app: "HAVEN Token"
4. Select networks:
   - **Base Sepolia** (testnet)
   - **Base Mainnet** (production)
5. Copy API keys
6. Update `.env`:

```bash
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_API_KEY
BASE_MAINNET_RPC=https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

#### Option B: Public RPC (Not recommended for production)

```bash
BASE_SEPOLIA_RPC=https://sepolia.base.org
BASE_MAINNET_RPC=https://mainnet.base.org
```

### 2. Generate Test Wallet

```bash
# Install ethers CLI
npm install -g ethers

# Generate wallet
npx ethers-wallet new

# Output will show:
# Address: 0x...
# Private Key: 0x...
```

**Save these securely!**

Update `contracts/.env`:
```bash
DEPLOYER_PRIVATE_KEY=0x... (your private key)
```

### 3. Fund Test Wallet

Get testnet ETH from faucet:

1. Go to [alchemy.com/faucets/base-sepolia](https://www.alchemy.com/faucets/base-sepolia)
2. Paste your wallet address
3. Click "Send Me ETH"
4. Wait ~30 seconds

Verify balance:
```bash
cast balance 0xYOUR_ADDRESS --rpc-url https://sepolia.base.org
```

### 4. Get Basescan API Key

1. Go to [basescan.org/register](https://basescan.org/register)
2. Create account
3. Go to API-KEYs → Add
4. Copy API key

Update `contracts/.env`:
```bash
BASESCAN_API_KEY=YOUR_API_KEY
```

---

## Smart Contracts Setup

### Install Dependencies

```bash
cd contracts
npm install
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `contracts/.env`:
```bash
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
DEPLOYER_PRIVATE_KEY=0xYOUR_PRIVATE_KEY
BASESCAN_API_KEY=YOUR_BASESCAN_KEY
BACKEND_SERVICE_ADDRESS=0xYOUR_BACKEND_ADDRESS
```

### Compile Contracts

```bash
npm run compile
```

Expected output:
```
Compiled 15 Solidity files successfully
```

### Run Tests

```bash
# Local tests (uses Hardhat network)
npm test

# With gas reporting
REPORT_GAS=true npm test

# With coverage
npm run coverage
```

Expected: >95% test coverage

### Deploy to Testnet

```bash
npm run deploy:testnet
```

Expected output:
```
📝 Deploying HAVEN token with account: 0x...
🔗 Chain ID: 84532
💰 Account balance: 0.5 ETH
📦 Deploying HAVEN contract...
✅ HAVEN deployed to: 0xCONTRACT_ADDRESS
📌 Granting MINTER_ROLE to 0x...
✅ MINTER_ROLE granted
📌 Granting BURNER_ROLE to 0x...
✅ BURNER_ROLE granted
📋 Deployment data saved to deployments/84532-deployment.json
```

### Verify on Basescan

```bash
npm run verify
```

Expected output:
```
🔍 Verifying contract 0x... on baseSepolia...
✅ Contract verified successfully!
```

View on Basescan:
```
https://sepolia.basescan.org/address/0xYOUR_CONTRACT_ADDRESS
```

---

## Backend Setup

### Install Python Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `backend/.env`:
```bash
# Blockchain
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
HAVEN_CONTRACT_ADDRESS=0x... (from deployment)
BACKEND_PRIVATE_KEY=0x... (backend signer key)
CHAIN_ID=84532

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/haven

# Payment (optional for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# External APIs
AURORA_API_URL=http://localhost:3001
AURORA_API_KEY=test_key_123
AURORA_WEBHOOK_SECRET=test_secret

# Monitoring
SLACK_BOT_TOKEN=xoxb-... (optional)
SLACK_ALERT_CHANNEL=#haven-alerts

# Application
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
PORT=8000
WORKERS=4
```

### Setup Database

#### Option 1: Docker (Recommended)

```bash
docker run --name haven-postgres \
  -e POSTGRES_PASSWORD=haven_dev \
  -e POSTGRES_DB=haven \
  -p 5432:5432 \
  -d postgres:15
```

#### Option 2: Local PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Linux
sudo apt-get install postgresql-15

# Create database
psql -U postgres -c "CREATE DATABASE haven;"
```

### Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### Start Backend

```bash
# Development mode (auto-reload)
uvicorn app:app --reload --port 8000

# Production mode
uvicorn app:app --workers 4 --port 8000
```

API should be available at:
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Testing Full Stack

### 1. Test Mint Endpoint

```bash
curl -X POST http://localhost:8000/token/mint \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key" \
  -d '{
    "user_id": "test_user_001",
    "amount": 100.0,
    "reason": "test_mint"
  }'
```

Expected response:
```json
{
  "status": "success",
  "tx_id": "mint_test_user_001_...",
  "blockchain_tx": "0x..."
}
```

### 2. Check Balance

```bash
curl http://localhost:8000/analytics/user/test_user_001
```

Expected response:
```json
{
  "user_id": "test_user_001",
  "balance": 100.0,
  "total_earned": 100.0,
  "total_redeemed": 0.0
}
```

### 3. Test Aurora Webhook

```bash
curl -X POST http://localhost:8000/webhooks/aurora/booking-created \
  -H "Content-Type: application/json" \
  -d '{
    "id": "booking_123",
    "guest_id": "guest_001",
    "guest_email": "test@example.com",
    "total_price": 100.0,
    "nights": 2,
    "_signature": "test_sig"
  }'
```

---

## Troubleshooting

### Issue: "Insufficient balance for deployment"

**Solution:**
```bash
# Check balance
cast balance 0xYOUR_ADDRESS --rpc-url https://sepolia.base.org

# Get more testnet ETH from faucet
# https://www.alchemy.com/faucets/base-sepolia
```

### Issue: "RPC connection failed"

**Solution:**
```bash
# Verify RPC URL
curl -X POST https://base-sepolia.g.alchemy.com/v2/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

# Should return: {"jsonrpc":"2.0","result":"0x14a34","id":1}
```

### Issue: "Gas price too low"

**Solution:**
Edit `hardhat.config.ts`:
```typescript
gasPrice: "auto" // or specific value like 1000000000 (1 gwei)
```

### Issue: "Database connection refused"

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or for local install
pg_isready

# Check connection string in .env
DATABASE_URL=postgresql://user:password@localhost:5432/haven
```

### Issue: "Python import errors"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Next Steps

1. ✅ **Contracts deployed** → Deploy to testnet
2. ✅ **Backend running** → Test API endpoints
3. ✅ **Database setup** → Run migrations
4. 🚀 **Integration testing** → Test Aurora/Tribe webhooks
5. 🚀 **Mainnet prep** → Security audit, legal review

---

## Useful Commands

### Contracts

```bash
# Compile
npm run compile

# Test
npm test

# Deploy testnet
npm run deploy:testnet

# Deploy mainnet (CAREFUL!)
npm run deploy:mainnet

# Verify
npm run verify

# Gas report
REPORT_GAS=true npm test
```

### Backend

```bash
# Start dev server
uvicorn app:app --reload

# Run tests
pytest tests/ -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Check DB
psql -U postgres -d haven
```

### Docker

```bash
# Start PostgreSQL
docker run --name haven-postgres -e POSTGRES_PASSWORD=haven_dev -p 5432:5432 -d postgres:15

# Start Redis
docker run --name haven-redis -p 6379:6379 -d redis:7

# View logs
docker logs -f haven-postgres

# Stop all
docker stop haven-postgres haven-redis
```

---

## Support

**Questions?** Check the [FAQ](./FAQ.md) or reach out:
- GitHub Issues: [github.com/pvt-ecosystem/haven-token/issues](https://github.com/pvt-ecosystem/haven-token/issues)
- Discord: [discord.gg/pvt](https://discord.gg/pvt)
- Email: dev@pvt.eco

# HAVEN Token: Base Sepolia Testnet Deployment Guide

**Last Updated:** November 8, 2025
**Status:** Ready for Deployment ✅
**Prerequisites:** All 32 tests passing

---

## 🎯 Overview

This guide will walk you through deploying the HAVEN token contract to Base Sepolia testnet in approximately 30 minutes.

**What you'll accomplish:**
1. Get Alchemy API key (free)
2. Generate and fund a test wallet
3. Deploy HAVEN contract to Base Sepolia
4. Verify contract on Basescan
5. Test basic operations (mint, burn, balance)

---

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [ ] Node.js v18+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Git repository cloned
- [ ] All contract tests passing (`npm test` shows 32/32)
- [ ] 15 minutes of uninterrupted time

---

## Step 1: Get Alchemy API Key (5 minutes)

### Why Alchemy?
Alchemy provides reliable RPC access to Base network with better rate limits than public RPCs.

### Instructions:

1. **Sign up for Alchemy:**
   - Go to https://alchemy.com/signup
   - Sign up with email or GitHub
   - Verify your email

2. **Create Base Sepolia App:**
   - Click "Create new app"
   - Name: `HAVEN Token Testnet`
   - Chain: **Base**
   - Network: **Base Sepolia (testnet)**
   - Click "Create app"

3. **Get Your API Key:**
   - Click on your new app
   - Click "API Key" button
   - Copy the **HTTPS URL** (looks like: `https://base-sepolia.g.alchemy.com/v2/YOUR_KEY_HERE`)
   - Save this URL - you'll need it in Step 3

---

## Step 2: Generate Test Wallet (5 minutes)

### Generate Wallet

```bash
# Navigate to contracts directory
cd "/Volumes/DevOPS 2025/01_DEVOPS_PLATFORM/Haven Token/contracts"

# Generate a new wallet
npx ethers-wallet new
```

**Output will look like:**
```
Private Key: 0xabc123...def456
Address: 0x1234567890abcdef1234567890abcdef12345678
```

⚠️ **IMPORTANT:** Save both values securely!
- **Private Key:** Keep this SECRET - never commit to git
- **Address:** This is public - you'll use it to receive testnet ETH

---

## Step 3: Fund Test Wallet (5 minutes)

### Get Testnet ETH

You need ETH on Base Sepolia to pay for gas fees during deployment.

**Option 1: Alchemy Faucet (Recommended)**

1. Go to https://www.alchemy.com/faucets/base-sepolia
2. Paste your **wallet address** (from Step 2)
3. Complete CAPTCHA
4. Click "Send Me ETH"
5. Wait ~30 seconds

**Option 2: Base Sepolia Faucet**

1. Go to https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
2. Sign in with Coinbase account
3. Request testnet ETH

### Verify You Received Funds

```bash
# Check your balance (replace with your address)
npx hardhat run --network baseSepolia scripts/check-balance.ts
```

Expected: `Balance: 0.5 ETH` (or similar)

If balance is 0, wait 1-2 minutes and check again.

---

## Step 4: Configure Environment (2 minutes)

### Create .env File

```bash
# In contracts directory
cp .env.example .env
```

### Edit .env File

Open `contracts/.env` and fill in:

```bash
# Alchemy RPC URL (from Step 1)
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY_HERE

# Deployer Private Key (from Step 2)
DEPLOYER_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# Basescan API Key (optional for now, required for verification)
BASESCAN_API_KEY=

# Backend Service Address (use deployer address for now)
BACKEND_SERVICE_ADDRESS=0xYOUR_DEPLOYER_ADDRESS
```

**Example:**
```bash
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/abc123def456
DEPLOYER_PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
BASESCAN_API_KEY=
BACKEND_SERVICE_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
```

⚠️ **Security Check:**
- [ ] `.env` file is in `.gitignore`
- [ ] Never commit `.env` to git
- [ ] Keep private key secret

---

## Step 5: Deploy to Base Sepolia (3 minutes)

### Run Deployment

```bash
# Make sure you're in contracts directory
cd "/Volumes/DevOPS 2025/01_DEVOPS_PLATFORM/Haven Token/contracts"

# Deploy to testnet
npm run deploy:testnet
```

### Expected Output

```
📝 Deploying HAVEN token with account: 0x1234...5678
🔗 Chain ID: 84532
💰 Account balance: 0.5 ETH

📦 Deploying HAVEN contract...
✅ HAVEN deployed to: 0xABC123...DEF456

📌 Granting MINTER_ROLE to 0x1234...5678
✅ MINTER_ROLE granted

📌 Granting BURNER_ROLE to 0x1234...5678
✅ BURNER_ROLE granted

📋 Deployment data saved to deployments/84532-deployment.json

✅ Deployment complete!

Contract Address: 0xABC123...DEF456
Deployer: 0x1234...5678
Chain ID: 84532
Block Number: 12345678
Gas Used: 1,690,098
Transaction Hash: 0xabc123def456...
```

### Save Contract Address

**CRITICAL:** Copy and save the contract address from the output above. You'll need it for:
- Backend configuration
- Contract verification
- Testing

---

## Step 6: Verify Contract on Basescan (Optional, 10 minutes)

Contract verification makes your source code public and allows users to interact with your contract via Basescan.

### Get Basescan API Key

1. Go to https://basescan.org/register
2. Create account and verify email
3. Go to https://basescan.org/myapikey
4. Click "Add" to create new API key
5. Copy the API key
6. Add to `contracts/.env`:
   ```bash
   BASESCAN_API_KEY=YOUR_BASESCAN_API_KEY
   ```

### Verify Contract

```bash
npm run verify
```

**Expected Output:**
```
🔍 Verifying contract 0xABC...DEF on baseSepolia...
✅ Contract verified successfully!

View on Basescan:
https://sepolia.basescan.org/address/0xABC123...DEF456#code
```

### View on Basescan

Open the URL in your browser to see:
- ✅ Source code (verified with green checkmark)
- Contract ABI
- Read/Write contract functions
- Transaction history

---

## Step 7: Test Basic Operations (5 minutes)

Now let's test that everything works!

### Test 1: Check Initial State

```bash
npx hardhat console --network baseSepolia
```

In the console:

```javascript
// Get contract instance
const HAVEN = await ethers.getContractFactory("HAVEN");
const haven = HAVEN.attach("0xYOUR_CONTRACT_ADDRESS");

// Check name and symbol
await haven.name();  // Should return "HAVEN"
await haven.symbol();  // Should return "HNV"

// Check total supply
await haven.totalSupply();  // Should return 0n

// Check your balance
const [deployer] = await ethers.getSigners();
await haven.balanceOf(deployer.address);  // Should return 0n
```

### Test 2: Mint Test Tokens

```javascript
// Mint 100 HNV to yourself
const amount = ethers.parseEther("100");
const tx = await haven.mint(deployer.address, amount, "test_mint");
await tx.wait();

// Check balance
const balance = await haven.balanceOf(deployer.address);
console.log("Balance:", ethers.formatEther(balance), "HNV");
// Should show: Balance: 100.0 HNV

// Check total supply
const supply = await haven.totalSupply();
console.log("Total Supply:", ethers.formatEther(supply), "HNV");
// Should show: Total Supply: 100.0 HNV
```

### Test 3: Burn Tokens

```javascript
// Burn 50 HNV
const burnAmount = ethers.parseEther("50");
const burnTx = await haven.burnWithReason(burnAmount, "test_burn");
await burnTx.wait();

// Check balance
const newBalance = await haven.balanceOf(deployer.address);
console.log("Balance after burn:", ethers.formatEther(newBalance), "HNV");
// Should show: Balance after burn: 50.0 HNV

// Check emission stats
const stats = await haven.getEmissionStats();
console.log("Total Minted:", ethers.formatEther(stats[0]));  // 100 HNV
console.log("Total Burned:", ethers.formatEther(stats[1]));  // 50 HNV
console.log("Circulating:", ethers.formatEther(stats[2]));  // 50 HNV
```

### Exit Console

```javascript
.exit
```

---

## Step 8: Update Backend Configuration (2 minutes)

Now configure the backend to connect to your deployed contract.

### Update Backend .env

```bash
# Navigate to backend directory
cd "/Volumes/DevOPS 2025/01_DEVOPS_PLATFORM/Haven Token/backend"

# Copy example if not exists
cp .env.example .env
```

### Edit backend/.env

```bash
# Blockchain Configuration
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY_HERE
HAVEN_CONTRACT_ADDRESS=0xYOUR_CONTRACT_ADDRESS_FROM_DEPLOYMENT
BACKEND_PRIVATE_KEY=0xYOUR_PRIVATE_KEY
CHAIN_ID=84532

# Database (for local testing)
DATABASE_URL=postgresql://postgres:password@localhost:5432/haven

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000
```

---

## Step 9: Test Backend Connection (Optional, 5 minutes)

### Start Backend (if database is running)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
uvicorn app:app --reload
```

### Test API

Open http://localhost:8000/docs in browser

Try the `/health` endpoint - should show:
```json
{
  "status": "healthy",
  "database": "connected",
  "blockchain": "connected",
  "contract_address": "0xYOUR_CONTRACT_ADDRESS"
}
```

---

## ✅ Post-Deployment Checklist

Verify everything is working:

- [ ] Contract deployed successfully
- [ ] Contract address saved
- [ ] Contract verified on Basescan (optional)
- [ ] Test mint worked (balance increased)
- [ ] Test burn worked (balance decreased)
- [ ] Backend .env updated with contract address
- [ ] Health check passes (if backend running)

---

## 📊 Deployment Summary

**Record these details for your records:**

```
Deployment Date: _______________
Contract Address: 0x_________________________________
Deployer Address: 0x_________________________________
Transaction Hash: 0x_________________________________
Block Number: _______________
Gas Used: _______________
Basescan URL: https://sepolia.basescan.org/address/0x_______________
```

---

## 🎉 Success! What's Next?

You've successfully deployed HAVEN to Base Sepolia testnet!

### Immediate Next Steps:

1. **Share Contract Address** with team
2. **Test Integrations:**
   - Aurora PMS webhook → token mint
   - Tribe App webhook → token mint
   - Token redemption flow

3. **Run Integration Tests:**
   ```bash
   cd backend
   pytest tests/integration/ -v
   ```

4. **Monitor Testnet Activity:**
   - Watch transactions on Basescan
   - Track gas usage
   - Verify events are emitted correctly

### Before Mainnet:

- [ ] Complete security fixes (6 critical issues)
- [ ] Write backend tests (100+ tests, 80% coverage)
- [ ] Complete external security audit
- [ ] Load test (1,000 concurrent users)
- [ ] Legal compliance verification

**Timeline to Mainnet:** 8 weeks (See `8_WEEK_ACTION_PLAN.md`)

---

## 🐛 Troubleshooting

### Issue: "Insufficient funds for intrinsic transaction cost"

**Solution:** Your wallet doesn't have enough ETH for gas.
```bash
# Check balance
npx hardhat run scripts/check-balance.ts --network baseSepolia

# If low, get more from faucet
# https://www.alchemy.com/faucets/base-sepolia
```

---

### Issue: "Nonce too low"

**Solution:** Previous transaction still pending.
```bash
# Wait 30 seconds and try again
# Or check pending transactions on Basescan
```

---

### Issue: "Contract verification failed"

**Solution:**
1. Check Basescan API key is correct in `.env`
2. Wait 1-2 minutes after deployment before verifying
3. Ensure contract was deployed successfully

---

### Issue: "Cannot find module '@nomicfoundation/hardhat-toolbox'"

**Solution:**
```bash
# Install dependencies
cd contracts
npm install
```

---

### Issue: "Network baseSepolia not found"

**Solution:** Check `hardhat.config.ts` has Base Sepolia configured:
```typescript
networks: {
  baseSepolia: {
    url: process.env.BASE_SEPOLIA_RPC || "https://sepolia.base.org",
    accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
    chainId: 84532,
  }
}
```

---

### Issue: "Private key must start with 0x"

**Solution:** Ensure your `DEPLOYER_PRIVATE_KEY` in `.env` starts with `0x`:
```bash
DEPLOYER_PRIVATE_KEY=0x1234...  # ✅ Correct
DEPLOYER_PRIVATE_KEY=1234...    # ❌ Wrong
```

---

## 📞 Support

**Questions or Issues?**

- **Documentation:** Check `docs/SETUP.md`
- **GitHub Issues:** Create issue with `[testnet]` tag
- **Team Slack:** #haven-dev channel
- **Email:** dev@pvt.eco

---

## 🔐 Security Reminders

⚠️ **IMPORTANT:**

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Double-check before committing

2. **Testnet private keys ≠ Mainnet private keys**
   - ALWAYS use separate wallets
   - Never reuse testnet keys on mainnet

3. **Testnet ETH has no value**
   - Safe to experiment
   - No financial risk

4. **Monitor your contract**
   - Watch for unexpected transactions
   - Set up Basescan alerts

---

## 📚 Additional Resources

- **Base Sepolia Explorer:** https://sepolia.basescan.org
- **Base Network Docs:** https://docs.base.org
- **Alchemy Dashboard:** https://dashboard.alchemy.com
- **Hardhat Docs:** https://hardhat.org/docs
- **Ethers.js Docs:** https://docs.ethers.org

---

**Congratulations on deploying to testnet! 🎉**

You're now ready to test all HAVEN token functionality in a safe environment before mainnet launch.

---

**Next Document:** See `docs/PRIORITY_ACTION_ITEMS.md` for security fixes before mainnet.

# HAVEN Token

**The Currency of Belonging**

A utility token powering the PVT hospitality ecosystem — uniting PVT Hostel, Aurora PMS, Tribe App, WisdomOS, and the Hostels United Network through an economy of trust and contribution.

[![Contracts CI](https://github.com/pvt-ecosystem/haven-token/workflows/Smart%20Contracts%20CI/badge.svg)](https://github.com/pvt-ecosystem/haven-token/actions)
[![Backend CI](https://github.com/pvt-ecosystem/haven-token/workflows/Backend%20API%20CI/badge.svg)](https://github.com/pvt-ecosystem/haven-token/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is HAVEN?

HAVEN (HNV) is an ERC-20 utility token on Base (Ethereum Layer-2) that:

- ✅ **Rewards participation** — Earn tokens for stays, reviews, events, and contributions
- ✅ **Enables governance** — Vote on ecosystem decisions (1 HNV = 1 vote)
- ✅ **Facilitates settlement** — Power inter-hostel transactions via Hostels United
- ✅ **Creates transparency** — All operations auditable on-chain

**Not a security.** HAVEN is designed as a utility token under Canadian and U.S. regulations.

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Total Supply** | 1,000,000,000 HNV (fixed) |
| **Initial Circulation** | 100,000,000 HNV (10%) |
| **Blockchain** | Base (Chain ID: 8453) |
| **Token Standard** | ERC-20 |
| **Burn Rate** | 2% per redemption |
| **Base Value** | 0.10 CAD (~$0.07 USD) |

---

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18
- Python >= 3.9
- PostgreSQL >= 15 (or Docker)
- Git

### 1. Bootstrap the Project

```bash
# Clone repository
git clone <repository-url>
cd haven-token

# Run automated setup
./scripts/bootstrap.sh
```

### 2. Get API Keys

- **Alchemy:** https://alchemy.com/signup (for RPC access)
- **Basescan:** https://basescan.org/register (for contract verification)

### 3. Configure Environment

```bash
# Update contracts/.env
BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
DEPLOYER_PRIVATE_KEY=0x...
BASESCAN_API_KEY=...

# Update backend/.env
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
HAVEN_CONTRACT_ADDRESS=0x... (after deployment)
BACKEND_PRIVATE_KEY=0x...
DATABASE_URL=postgresql://...
```

### 4. Deploy to Testnet

```bash
cd contracts
npm install
npm run compile
npm run deploy:testnet
```

### 5. Start Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

**API Docs:** http://localhost:8000/docs

---

## 📁 Project Structure

```
haven-token/
├── contracts/              # Smart contracts (Hardhat + Solidity)
│   ├── contracts/
│   │   └── HAVEN.sol      # Main ERC-20 token contract
│   ├── scripts/
│   │   ├── deploy.ts      # Deployment script
│   │   └── verify.ts      # Contract verification
│   ├── test/
│   │   └── HAVEN.test.ts  # Comprehensive test suite (>95% coverage)
│   └── hardhat.config.ts  # Hardhat configuration
│
├── backend/                # Python FastAPI backend
│   ├── services/
│   │   ├── token_agent.py          # Blockchain interaction
│   │   ├── aurora_integration.py   # Aurora PMS integration
│   │   └── tribe_integration.py    # Tribe app integration
│   ├── database/
│   │   └── models.py               # SQLAlchemy models
│   ├── app.py                      # Main FastAPI application
│   └── requirements.txt            # Python dependencies
│
├── docs/                   # Documentation
│   ├── HAVEN_Whitepaper.md         # Complete whitepaper
│   ├── HAVEN_Tokenomics.csv        # Tokenomics spreadsheet
│   ├── SETUP.md                    # Detailed setup guide
│   ├── ROLES.md                    # Team roles & responsibilities
│   └── TIMELINE.md                 # 4-week deployment timeline
│
├── scripts/
│   └── bootstrap.sh                # Automated setup script
│
└── .github/workflows/      # CI/CD pipelines
    ├── contracts-ci.yml            # Smart contract testing
    ├── backend-ci.yml              # Backend testing
    ├── deploy-testnet.yml          # Testnet deployment
    └── deploy-mainnet.yml          # Mainnet deployment
```

---

## 🎁 Token Rewards

### Earn HAVEN by:

**PVT Hostel & Aurora:**
- 📍 **Booking stays:** 2 HNV per CAD spent
- ⭐ **Leaving reviews:** 50 HNV per verified review (4+ stars)
- 👥 **Referring guests:** 100-500 HNV per successful referral (tiered)
- 🏆 **Automation milestones:** 100-250 HNV per Aurora setup achievement

**Tribe App:**
- 🎉 **Event attendance:** 25-100 HNV per event (tiered)
- 💬 **Community contributions:** 5-25 HNV per post/guide
- 🎓 **Coaching milestones:** 100-250 HNV per completion (tiered)
- 💰 **Staking rewards:** 10% APY for locked HNV

**Hostels United:**
- 🌐 **Network participation:** Onboarding bonuses
- 🤝 **Inter-hostel bookings:** Referral rewards

### Spend HAVEN on:

- Discounted future stays
- Premium features in Aurora/Tribe
- Governance participation (DAO voting)
- Exclusive events and experiences

---

## 🔧 Development

### Run Tests

```bash
# Smart contracts
cd contracts
npm test

# With coverage
npx hardhat coverage

# With gas reporting
REPORT_GAS=true npm test

# Backend
cd backend
pytest tests/ -v
```

### Local Development

```bash
# Start local Hardhat node
cd contracts
npx hardhat node

# Deploy locally
npx hardhat run scripts/deploy.ts --network localhost

# Start backend
cd backend
source venv/bin/activate
uvicorn app:app --reload
```

---

## 🔐 Security

### Audits

- **Status:** Pending (scheduled for Q1 2026)
- **Auditors:** CertiK and/or Code4rena
- **Scope:** Smart contract security, gas optimization, access control

### Security Features

- ✅ Role-based access control (MINTER, BURNER, PAUSER, GOVERNANCE)
- ✅ Emergency pause mechanism
- ✅ Timelock governance (7-day delay)
- ✅ Reentrancy protection
- ✅ Integer overflow protection (Solidity 0.8+)

### Bug Bounty

**Launch:** Q2 2026 (post-audit)

**Rewards:**
- Critical: Up to 50,000 HNV (~$5,000 CAD)
- High: 10,000 HNV
- Medium: 2,500 HNV
- Low: 500 HNV

---

## 📜 Smart Contract

### Deployed Addresses

| Network | Chain ID | Contract Address | Explorer |
|---------|----------|------------------|----------|
| **Base Sepolia (Testnet)** | 84532 | `TBD` | [View on Basescan](https://sepolia.basescan.org) |
| **Base Mainnet** | 8453 | `TBD` | [View on Basescan](https://basescan.org) |

### Key Functions

```solidity
// Mint tokens (requires MINTER_ROLE)
function mint(address to, uint256 amount, string calldata reason)

// Burn tokens (user-initiated)
function burnWithReason(uint256 amount, string calldata reason)

// Burn from account (requires BURNER_ROLE)
function burnFrom(address from, uint256 amount, string calldata reason)

// Get balance
function balanceOf(address account) returns (uint256)

// Get emission statistics
function getEmissionStats() returns (uint256 totalMinted, uint256 totalBurned, uint256 circulating)
```

---

## 🌐 API Endpoints

**Base URL:** `http://localhost:8000` (development)

### Token Operations

```bash
# Mint tokens
POST /token/mint
{
  "user_id": "user_123",
  "amount": 100.0,
  "reason": "booking_reward"
}

# Redeem tokens
POST /token/redeem
{
  "user_id": "user_123",
  "amount": 50.0,
  "withdrawal_method": "bank_transfer",
  "idempotency_key": "unique_key"
}

# Get balance
GET /token/balance/{user_id}

# Get user analytics
GET /analytics/user/{user_id}

# Get token stats
GET /analytics/token-stats
```

### Webhooks

```bash
# Aurora PMS
POST /webhooks/aurora/booking-created
POST /webhooks/aurora/booking-completed
POST /webhooks/aurora/booking-cancelled
POST /webhooks/aurora/review-submitted

# Tribe App
POST /webhooks/tribe/event-attendance
POST /webhooks/tribe/contribution
POST /webhooks/tribe/staking-started
POST /webhooks/tribe/coaching-milestone
POST /webhooks/tribe/referral-success
```

**Full API Docs:** http://localhost:8000/docs

---

## 📖 Documentation

- **[Whitepaper](docs/HAVEN_Whitepaper.md)** — Complete technical and economic overview
- **[Tokenomics](docs/HAVEN_Tokenomics.csv)** — Supply, distribution, and reward rates
- **[Setup Guide](docs/SETUP.md)** — Step-by-step deployment instructions
- **[Team Roles](docs/ROLES.md)** — Responsibilities and deliverables
- **[Timeline](docs/TIMELINE.md)** — 4-week deployment roadmap

---

## 🗓️ Roadmap

### Phase 1: Alpha Launch (Q1 2026)
- ✅ Smart contract deployed to Base Sepolia
- ✅ Backend API operational
- ✅ Internal beta testing (50 users)

### Phase 2: Beta Launch (Q2 2026)
- 🚀 Mainnet deployment
- 🚀 Aurora PMS integration
- 🚀 Tribe App integration
- 🚀 1,000 active users

### Phase 3: Public Launch (Q4 2026)
- 🌍 Hostels United DAO launch
- 🌍 10,000 active users
- 🌍 5+ partner hostels

### Phase 4: Network Expansion (2027)
- 🌐 50+ hostels on network
- 🌐 Multi-chain support (Polygon, Avalanche)
- 🌐 100,000+ active users

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) (coming soon).

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- **Solidity:** Follow OpenZeppelin patterns
- **Python:** PEP 8, Black formatter, MyPy type hints
- **Tests:** >95% coverage required
- **Commits:** Conventional Commits format

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Product Lead:** [Your Name]
**Blockchain Developer:** [Name or TBD]
**Backend Developer:** [Name or TBD]
**Community Lead:** [Name or TBD]

**Legal Counsel:** LexChronos
**Audit Partner:** CertiK / Code4rena

---

## 💬 Support

- **Documentation:** [docs/SETUP.md](docs/SETUP.md)
- **GitHub Issues:** [github.com/pvt-ecosystem/haven-token/issues](https://github.com/pvt-ecosystem/haven-token/issues)
- **Email:** haven@pvt.eco
- **Discord:** [discord.gg/pvt](https://discord.gg/pvt)
- **Slack:** #haven-team (internal)

---

## 🔗 Links

- **Website:** https://haven.pvt.eco (coming soon)
- **Whitepaper:** [docs/HAVEN_Whitepaper.md](docs/HAVEN_Whitepaper.md)
- **Basescan (Testnet):** https://sepolia.basescan.org
- **Basescan (Mainnet):** https://basescan.org
- **Base Network Docs:** https://docs.base.org

---

## ⚠️ Disclaimer

HAVEN is a utility token designed for use within the PVT ecosystem. It is not intended as an investment vehicle. Token value may fluctuate based on supply and demand. Always do your own research before participating.

This software is provided "as is" without warranty of any kind. See the LICENSE file for details.

---

**Built with ❤️ by the PVT Team**

*Redefining hospitality through decentralized ownership and the economy of belonging.*

---

## 🙏 Acknowledgments

- [OpenZeppelin](https://openzeppelin.com) — Smart contract security standards
- [Hardhat](https://hardhat.org) — Ethereum development environment
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [Base](https://base.org) — Ethereum Layer-2 for accessible blockchain apps
- [Alchemy](https://alchemy.com) — Blockchain infrastructure and APIs

---

**Ready to build the currency of belonging?** 🚀

Get started: `./scripts/bootstrap.sh`

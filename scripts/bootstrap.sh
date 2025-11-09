#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════════════
# HAVEN Token: Bootstrap Script
# Automated setup for development environment
# ═══════════════════════════════════════════════════════════════════════════

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║           HAVEN Token: Bootstrap Environment                   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─────────────────────────────────────────────────────────────────────────
# 1. CHECK PREREQUISITES
# ─────────────────────────────────────────────────────────────────────────

echo -e "${BLUE}📋 Step 1: Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Install from https://nodejs.org${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Install from https://python.org${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Install from https://git-scm.com${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git: $(git --version)${NC}"

# Check for PostgreSQL or Docker
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL installed${NC}"
    HAS_POSTGRES=true
elif command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker installed (will use for PostgreSQL)${NC}"
    HAS_DOCKER=true
else
    echo -e "${YELLOW}⚠️  Neither PostgreSQL nor Docker found${NC}"
    echo -e "${YELLOW}   Install one of them to run the backend${NC}"
    HAS_DATABASE=false
fi

# ─────────────────────────────────────────────────────────────────────────
# 2. INITIALIZE GIT REPOSITORY
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${BLUE}📂 Step 2: Initializing Git repository...${NC}"

if [ ! -d ".git" ]; then
    git init
    git add .gitignore
    git commit -m "Initial commit: HAVEN Token project structure"
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Git repository already exists${NC}"
fi

# ─────────────────────────────────────────────────────────────────────────
# 3. SETUP SMART CONTRACTS
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${BLUE}📦 Step 3: Setting up smart contracts...${NC}"

cd contracts

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created contracts/.env${NC}"
    echo -e "${YELLOW}⚠️  Please update contracts/.env with your API keys!${NC}"
else
    echo -e "${YELLOW}⚠️  contracts/.env already exists${NC}"
fi

# Compile contracts
echo "Compiling smart contracts..."
npx hardhat compile

echo -e "${GREEN}✅ Smart contracts compiled successfully${NC}"

cd ..

# ─────────────────────────────────────────────────────────────────────────
# 4. SETUP BACKEND
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${BLUE}🐍 Step 4: Setting up Python backend...${NC}"

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created backend/.env${NC}"
    echo -e "${YELLOW}⚠️  Please update backend/.env with your configuration!${NC}"
else
    echo -e "${YELLOW}⚠️  backend/.env already exists${NC}"
fi

cd ..

# ─────────────────────────────────────────────────────────────────────────
# 5. SETUP DATABASE
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${BLUE}🗄️  Step 5: Setting up database...${NC}"

if [ "$HAS_DOCKER" = true ]; then
    echo "Starting PostgreSQL in Docker..."

    # Check if container already exists
    if docker ps -a | grep -q haven-postgres; then
        echo -e "${YELLOW}⚠️  PostgreSQL container already exists${NC}"
        echo "Starting existing container..."
        docker start haven-postgres
    else
        docker run --name haven-postgres \
            -e POSTGRES_PASSWORD=haven_dev \
            -e POSTGRES_DB=haven \
            -p 5432:5432 \
            -d postgres:15

        echo -e "${GREEN}✅ PostgreSQL container started${NC}"
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
    fi

    # Optional: Start Redis for caching
    if ! docker ps -a | grep -q haven-redis; then
        echo "Starting Redis in Docker..."
        docker run --name haven-redis \
            -p 6379:6379 \
            -d redis:7
        echo -e "${GREEN}✅ Redis container started${NC}"
    fi

elif [ "$HAS_POSTGRES" = true ]; then
    echo "PostgreSQL is installed locally"
    echo -e "${YELLOW}Please ensure PostgreSQL is running and create the 'haven' database:${NC}"
    echo -e "${YELLOW}  psql -U postgres -c \"CREATE DATABASE haven;\"${NC}"
else
    echo -e "${RED}❌ No database available${NC}"
    echo "Please install PostgreSQL or Docker to continue"
fi

# ─────────────────────────────────────────────────────────────────────────
# 6. CREATE DEPLOYMENT DIRECTORIES
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${BLUE}📁 Step 6: Creating deployment directories...${NC}"

mkdir -p contracts/deployments
mkdir -p docs
mkdir -p scripts

echo -e "${GREEN}✅ Directories created${NC}"

# ─────────────────────────────────────────────────────────────────────────
# 7. SUMMARY & NEXT STEPS
# ─────────────────────────────────────────────────────────────────────────

echo -e "\n${GREEN}✨ BOOTSTRAP COMPLETE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📊 Project Status:${NC}"
echo "  • Smart contracts: Compiled ✓"
echo "  • Backend dependencies: Installed ✓"
echo "  • Database: $([ "$HAS_DOCKER" = true ] || [ "$HAS_POSTGRES" = true ] && echo "Ready ✓" || echo "Needs setup ⚠")"
echo ""
echo -e "${YELLOW}🔑 NEXT STEPS:${NC}"
echo ""
echo "1. Get API Keys (5 minutes):"
echo "   → Alchemy: https://www.alchemy.com/signup"
echo "   → Basescan: https://basescan.org/register"
echo ""
echo "2. Update Environment Files:"
echo "   → contracts/.env:"
echo "     - BASE_SEPOLIA_RPC=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY"
echo "     - DEPLOYER_PRIVATE_KEY=0x..."
echo "     - BASESCAN_API_KEY=..."
echo ""
echo "   → backend/.env:"
echo "     - RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY"
echo "     - HAVEN_CONTRACT_ADDRESS=0x... (after deployment)"
echo "     - BACKEND_PRIVATE_KEY=0x..."
echo ""
echo "3. Generate Test Wallet:"
echo "   cd contracts"
echo "   npx ethers-wallet new"
echo "   (Save the private key to .env)"
echo ""
echo "4. Fund Test Wallet:"
echo "   → https://www.alchemy.com/faucets/base-sepolia"
echo "   → Paste your wallet address"
echo "   → Claim 0.5 ETH"
echo ""
echo "5. Deploy to Testnet:"
echo "   cd contracts"
echo "   npm run deploy:testnet"
echo ""
echo "6. Start Backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app:app --reload"
echo ""
echo "7. View API Documentation:"
echo "   → http://localhost:8000/docs"
echo ""
echo -e "${GREEN}📚 Documentation:${NC}"
echo "  • Setup Guide: docs/SETUP.md"
echo "  • Whitepaper: docs/HAVEN_Whitepaper.md"
echo "  • Tokenomics: docs/HAVEN_Tokenomics.csv"
echo ""
echo -e "${BLUE}💬 Need Help?${NC}"
echo "  • Check docs/SETUP.md for detailed instructions"
echo "  • Report issues: github.com/pvt-ecosystem/haven-token/issues"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🚀 Ready to launch HAVEN Token!${NC}"
echo ""

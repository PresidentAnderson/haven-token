# HAVEN Token Frontend - Quick Setup Guide

## Prerequisites

Before you begin, ensure you have:

- Node.js 18+ installed ([nodejs.org](https://nodejs.org))
- npm 9+ (comes with Node.js)
- A code editor (VS Code recommended)
- Git installed

## Step-by-Step Setup

### 1. Navigate to Frontend Directory

```bash
cd "/Volumes/DevOPS 2025/01_DEVOPS_PLATFORM/Haven Token/frontend"
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Next.js 14
- React 18
- TypeScript
- TailwindCSS
- Wagmi & Viem (Web3)
- Framer Motion
- Recharts
- And more...

### 3. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env.local
```

### 4. Configure Environment Variables

Open `.env.local` and configure the following:

#### Required Variables:

```env
# Get a WalletConnect Project ID from https://cloud.walletconnect.com
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id_here
```

#### Optional (but recommended for production):

```env
# Get from https://www.alchemy.com
NEXT_PUBLIC_ALCHEMY_API_KEY=your_alchemy_api_key

# Contract addresses (once deployed)
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET=0x...
```

### 5. Get WalletConnect Project ID

1. Go to [cloud.walletconnect.com](https://cloud.walletconnect.com)
2. Sign up or log in
3. Create a new project
4. Copy the Project ID
5. Paste it into `.env.local` as `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`

### 6. Get Alchemy API Key (Optional)

1. Go to [alchemy.com](https://www.alchemy.com)
2. Sign up or log in
3. Create a new app (select Base Mainnet and Base Sepolia)
4. Copy the API Key
5. Paste it into `.env.local` as `NEXT_PUBLIC_ALCHEMY_API_KEY`

### 7. Run Development Server

```bash
npm run dev
```

The application will start at [http://localhost:3000](http://localhost:3000)

### 8. Open in Browser

Navigate to:
- Local: [http://localhost:3000](http://localhost:3000)
- Network: Check terminal output for network URL

## Verification Checklist

After setup, verify the following:

- [ ] Page loads without errors
- [ ] Hero section displays with gradient background
- [ ] Navigation bar appears at top
- [ ] Dark mode toggle works
- [ ] "Connect Wallet" button is visible
- [ ] Smooth scroll navigation works
- [ ] All sections render correctly:
  - [ ] Hero
  - [ ] How It Works
  - [ ] Tokenomics (with chart)
  - [ ] FAQ (expandable)
  - [ ] Footer

## Testing Wallet Connection

### With MetaMask:

1. Install [MetaMask browser extension](https://metamask.io)
2. Create or import a wallet
3. Add Base network:
   - Network Name: Base
   - RPC URL: https://mainnet.base.org
   - Chain ID: 8453
   - Currency Symbol: ETH
   - Block Explorer: https://basescan.org
4. Click "Connect Wallet" on the site
5. Approve connection in MetaMask

### With Test Network:

1. Switch to Base Sepolia testnet in MetaMask:
   - Network Name: Base Sepolia
   - RPC URL: https://sepolia.base.org
   - Chain ID: 84532
   - Currency Symbol: ETH
   - Block Explorer: https://sepolia.basescan.org
2. Get test ETH from [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
3. Connect wallet on site

## Configuring Contract Address

Once the HAVEN token contract is deployed:

1. Copy the deployed contract address
2. Open `.env.local`
3. Add the address:
   ```env
   # For mainnet deployment
   NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS=0xYourContractAddress

   # For testnet deployment
   NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET=0xYourTestnetContractAddress
   ```
4. Restart the development server

## Common Issues & Solutions

### Issue: "Module not found" errors

**Solution**: Run `npm install` again

### Issue: Wallet won't connect

**Solutions**:
1. Ensure you have a Web3 wallet installed (MetaMask, Coinbase Wallet)
2. Check if WalletConnect Project ID is configured
3. Try clearing browser cache
4. Check browser console for specific errors

### Issue: Network errors

**Solutions**:
1. Verify you're on Base network (or Base Sepolia for testing)
2. Check RPC endpoints are accessible
3. Try using Alchemy RPC (configure API key)

### Issue: Contract data not loading

**Solutions**:
1. Ensure contract address is configured in `.env.local`
2. Verify contract is deployed to the network you're on
3. Check contract address is correct
4. Ensure wallet is connected to correct network

### Issue: Build fails

**Solutions**:
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

### Issue: TypeScript errors

**Solution**: Run type check to see specific errors
```bash
npm run type-check
```

## Production Build

To create a production build:

```bash
npm run build
```

To test production build locally:

```bash
npm run build
npm run start
```

## Deployment

### Deploy to Vercel (Recommended):

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Add environment variables in Vercel dashboard
5. Deploy!

### Deploy to Other Platforms:

The app can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Google Cloud Platform
- Railway
- Digital Ocean

## Next Steps

After setup is complete:

1. **Customize Branding**: Update colors in `tailwind.config.ts`
2. **Add Content**: Update text and copy throughout components
3. **Configure Analytics**: Add Google Analytics or similar
4. **Test Mobile**: Ensure responsive design works on mobile devices
5. **SEO Optimization**: Update metadata in `app/layout.tsx`
6. **Deploy Contract**: Deploy HAVEN token contract and configure address
7. **Production Deploy**: Deploy frontend to Vercel or other platform

## Development Workflow

1. Make changes to components or pages
2. Check browser for hot-reload updates
3. Test functionality
4. Run linter: `npm run lint`
5. Run type check: `npm run type-check`
6. Commit changes
7. Push to repository

## Getting Help

- **Documentation**: See `README.md` for detailed docs
- **Discord**: Join the HAVEN community
- **GitHub Issues**: Report bugs or request features
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **Wagmi Docs**: [wagmi.sh](https://wagmi.sh)

## Support

If you encounter any issues not covered here, please:

1. Check the main `README.md`
2. Search GitHub issues
3. Join our Discord community
4. Create a new GitHub issue with details

---

Happy coding! 🚀

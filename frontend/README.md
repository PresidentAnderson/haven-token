# HAVEN Token - Frontend

A modern, responsive landing page for the HAVEN Token built with Next.js 14, TypeScript, TailwindCSS, and Web3 integration.

## Features

- **Modern Design**: Beautiful gradient hero, smooth animations with Framer Motion
- **Web3 Integration**: Wallet connection (MetaMask, WalletConnect) with Wagmi + Viem
- **Real-time Data**: Live token balance and supply reading from Base blockchain
- **Interactive Components**:
  - Token distribution pie chart
  - Booking and staking rewards calculator
  - FAQ accordion
  - Dark mode toggle
- **Responsive**: Mobile-first design that works on all devices
- **Type-safe**: Full TypeScript support with strict mode
- **Accessible**: WCAG 2.1 AA compliant

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Web3**: Wagmi v2, Viem v2
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- A Web3 wallet (MetaMask recommended)
- WalletConnect Project ID (get from [cloud.walletconnect.com](https://cloud.walletconnect.com))

### Installation

1. **Install dependencies**:

```bash
npm install
```

2. **Configure environment variables**:

Copy `.env.example` to `.env.local` and fill in your values:

```bash
cp .env.example .env.local
```

Required environment variables:

```env
# Contract addresses
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET=0x...

# RPC Configuration (optional but recommended)
NEXT_PUBLIC_ALCHEMY_API_KEY=your_alchemy_api_key

# WalletConnect
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id

# Network settings
NEXT_PUBLIC_ENABLE_TESTNETS=true
NEXT_PUBLIC_DEFAULT_CHAIN=base
```

3. **Run development server**:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with metadata
│   ├── page.tsx             # Main landing page
│   ├── providers.tsx        # Context providers (Wagmi, React Query)
│   ├── theme-provider.tsx   # Dark mode provider
│   └── globals.css          # Global styles and Tailwind
├── components/
│   ├── Navigation.tsx       # Top navigation with wallet connect
│   ├── Hero.tsx             # Hero section with gradient
│   ├── HowItWorks.tsx       # 4-step process section
│   ├── Tokenomics.tsx       # Distribution chart & calculator
│   ├── FAQ.tsx              # FAQ accordion
│   ├── Footer.tsx           # Footer with links
│   ├── WalletConnect.tsx    # Wallet connection button
│   └── TokenBalance.tsx     # Display user token balance
├── lib/
│   ├── wagmi.ts             # Wagmi configuration
│   ├── contracts.ts         # Contract ABIs and addresses
│   ├── constants.ts         # App constants and token info
│   └── utils.ts             # Utility functions
└── public/                  # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Configuration

### Network Configuration

The app supports both Base mainnet and Base Sepolia testnet. Configure in `lib/wagmi.ts`:

```typescript
// Enable/disable testnets via environment variable
NEXT_PUBLIC_ENABLE_TESTNETS=true
```

### Contract Addresses

Set contract addresses in `.env.local`:

- `NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS` - Base mainnet contract
- `NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET` - Base Sepolia testnet contract

### Theme Customization

Customize colors in `tailwind.config.ts`:

```typescript
colors: {
  primary: { ... },    // Main brand color (purple/blue)
  secondary: { ... },  // Secondary brand color
  accent: { ... },     // Accent color (orange)
}
```

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import project to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Other Platforms

Build the production bundle:

```bash
npm run build
```

The output will be in `.next/` directory. You can deploy this to any platform that supports Next.js.

## Web3 Integration

### Connecting Wallet

The app automatically detects installed wallets and provides connection options:

1. Click "Connect Wallet"
2. Select your preferred wallet (MetaMask, WalletConnect, etc.)
3. Approve connection in your wallet
4. Switch to Base network if needed

### Reading Token Data

Token balance and supply are automatically fetched from the blockchain:

```typescript
// Example: Reading token balance
const { data: balance } = useReadContract({
  address: contractAddress,
  abi: HAVEN_ABI,
  functionName: 'balanceOf',
  args: [userAddress],
});
```

### Network Switching

If user is on wrong network, app prompts to switch to Base:

```typescript
const { switchChain } = useSwitchChain();
switchChain({ chainId: base.id });
```

## Accessibility

The landing page follows WCAG 2.1 AA standards:

- Semantic HTML structure
- Keyboard navigation support
- Sufficient color contrast
- Screen reader friendly
- Focus indicators
- Alt text for images

## Performance Optimization

- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js font optimization
- **Lazy Loading**: Components loaded on scroll
- **Caching**: React Query for data caching

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### Wallet Connection Issues

1. Ensure you're on the correct network (Base or Base Sepolia)
2. Clear browser cache and reload
3. Try different wallet (MetaMask, Coinbase Wallet)
4. Check browser console for errors

### Contract Read Failures

1. Verify contract address in `.env.local`
2. Check RPC endpoint is responding
3. Ensure contract is deployed to selected network
4. Try switching between RPC providers

### Build Errors

1. Delete `.next/` and `node_modules/`
2. Run `npm install` again
3. Check for TypeScript errors with `npm run type-check`

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

- **Documentation**: [docs.haven-token.com](https://docs.haven-token.com)
- **Discord**: [discord.gg/haventoken](https://discord.gg/haventoken)
- **GitHub Issues**: [github.com/pvt-haven/haven-token/issues](https://github.com/pvt-haven/haven-token/issues)

## Acknowledgments

- Built on [Base](https://base.org) - Ethereum L2
- Powered by [Wagmi](https://wagmi.sh) and [Viem](https://viem.sh)
- Icons by [Lucide](https://lucide.dev)
- UI inspired by modern Web3 projects

---

Made with ❤️ for the Puerto Vallarta Tribe community

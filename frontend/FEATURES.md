# HAVEN Token Frontend - Features & Components

## Overview

A production-ready, modern landing page for the HAVEN Token built with Next.js 14, featuring Web3 integration, beautiful animations, and a fully responsive design.

## Core Features

### 1. Web3 Wallet Integration

**Wallet Connection**
- Multi-wallet support (MetaMask, WalletConnect, Coinbase Wallet)
- Automatic network detection and switching
- Base mainnet (Chain ID: 8453) and Base Sepolia testnet (84532) support
- Connection state persistence
- Wrong network detection with one-click switching

**Blockchain Interaction**
- Read token balance from smart contract
- Display total supply in real-time
- Contract address verification
- Block explorer integration (BaseScan)
- Automatic data refreshing

**User Experience**
- Wallet dropdown with balance display
- One-click disconnect
- Network status indicator
- Testnet warning banner
- Transaction loading states

### 2. Hero Section

**Design Elements**
- Animated gradient background
- Floating orb animations
- Responsive typography
- Glass morphism effects
- Smooth fade-in animations

**Content**
- Compelling value proposition
- Live token price display
- Total supply counter
- Dual CTA buttons
- Trust indicators (reward rates)
- Scroll indicator animation

### 3. How It Works Section

**4-Step Process**
1. Book Your Stay - Earn 2 HNV per CAD
2. Engage with Community - Event rewards
3. Stake Your Tokens - 10% APY
4. Redeem for Perks - Use tokens

**Features**
- Icon-based step visualization
- Gradient step numbers
- Arrow connectors (desktop)
- Staggered animations
- Additional benefits grid

### 4. Tokenomics Section

**Token Distribution Chart**
- Interactive pie chart (Recharts)
- Color-coded segments:
  - Community Rewards: 40%
  - Staking Pool: 25%
  - Team & Development: 15%
  - Marketing: 10%
  - Liquidity: 10%
- Hover tooltips
- Legend with percentages

**Token Information**
- Symbol: HNV
- Total supply: 1 billion
- Base value: 0.10 CAD
- Network: Base (Ethereum L2)
- Decimals: 18

**Reward Rates Display**
- Staking APY: 10%
- Burn rate: 2%
- Visual cards with icons

**Rewards Calculator**
- Dual mode: Booking & Staking
- Interactive sliders
- Real-time calculations
- Visual results display

**Booking Calculator**
- Input: CAD amount (100-10,000)
- Output: HNV earned (2 per CAD)
- Value in CAD display

**Staking Calculator**
- Input: HNV amount (1,000-100,000)
- Input: Days (30-365)
- Output: Estimated rewards at 10% APY
- Total balance projection

### 5. FAQ Section

**Features**
- Expandable accordion
- 8 comprehensive questions
- Smooth animations
- Auto-collapse others (optional)
- Search-friendly content

**Topics Covered**
- What is HAVEN Token?
- How to earn tokens
- Token usage
- Staking mechanics
- Transaction fees
- Wallet support
- Security
- Getting started

**Additional CTA**
- Community links (Discord)
- Documentation link
- Help resources

### 6. Navigation

**Desktop Navigation**
- Sticky header
- Glass morphism on scroll
- Smooth scroll to sections
- External link indicators
- Dark mode toggle
- Wallet connect button

**Mobile Navigation**
- Hamburger menu
- Slide-in drawer
- Touch-optimized
- Responsive CTAs

**Navigation Links**
- How It Works
- Tokenomics
- FAQ
- Docs (external)

### 7. Footer

**Content Sections**
- Product links
- Resources
- Community
- Legal

**Features**
- Contract address display
- BaseScan link
- Social media links
- Newsletter signup (future)
- Copyright notice
- Risk disclaimer

**Social Links**
- Twitter
- Discord
- GitHub
- Documentation

### 8. Theme System

**Dark Mode**
- System preference detection
- Manual toggle
- Persistent storage
- Smooth transitions
- Tailwind dark: classes

**Color Themes**
- Light mode: Clean whites, subtle grays
- Dark mode: Deep blacks, vibrant accents
- Gradient accents throughout

### 9. Animations

**Framer Motion**
- Fade in on scroll
- Slide up on scroll
- Stagger children
- Scale animations
- Hover effects

**CSS Animations**
- Floating orbs
- Gradient shifts
- Pulse glow
- Loading spinners
- Smooth transitions

### 10. Responsive Design

**Breakpoints**
- Mobile: 0-640px
- Tablet: 640-1024px
- Desktop: 1024px+
- Large: 1280px+

**Mobile Optimizations**
- Touch-friendly buttons
- Collapsible sections
- Optimized typography
- Reduced animations
- Hamburger menu

## Technical Features

### Performance

**Optimization Techniques**
- Code splitting (automatic)
- Lazy loading components
- Image optimization (Next.js)
- Font optimization
- React Query caching
- Debounced inputs

**Loading States**
- Skeleton screens
- Spinner animations
- Progressive loading
- Error boundaries

### Accessibility

**WCAG 2.1 AA Compliance**
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators
- Alt text
- Color contrast ratios
- Screen reader support

**Interactive Elements**
- Tab index management
- Focus trapping in modals
- Skip links
- Descriptive labels

### SEO

**Meta Tags**
- Dynamic titles
- Descriptions
- Open Graph
- Twitter Cards
- Canonical URLs

**Structured Data**
- JSON-LD schema
- Rich snippets
- Site navigation

### Security

**Best Practices**
- Environment variables
- Secure RPC connections
- Input validation
- XSS protection
- HTTPS enforcement
- CSP headers (configurable)

## Component Architecture

### Reusable Components

**UI Components**
- Button variants (primary, secondary, outline)
- Card components
- Glass morphism effects
- Gradient text
- Loading states

**Layout Components**
- Section containers
- Responsive grids
- Flex layouts
- Max-width containers

### Utility Functions

**Number Formatting**
- Token amounts
- Currency values
- Large numbers (K, M, B)
- Decimal precision

**Address Utilities**
- Truncate addresses
- Copy to clipboard
- Explorer links
- Checksum validation

**Calculations**
- Booking rewards
- Staking rewards
- APY calculations
- Wei conversions

## Configuration

### Environment Variables

**Required**
- NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID

**Optional**
- NEXT_PUBLIC_ALCHEMY_API_KEY
- NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS
- NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET
- NEXT_PUBLIC_ENABLE_TESTNETS

### Customization

**Easy to Modify**
- Colors (tailwind.config.ts)
- Token constants (lib/constants.ts)
- FAQ content (lib/constants.ts)
- Distribution percentages
- Reward rates
- Social links

## Browser Support

**Tested Browsers**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Mobile Browsers**
- iOS Safari 14+
- Chrome Android 90+
- Samsung Internet 14+

## Future Enhancements

**Planned Features**
- Staking interface
- Token swap integration
- NFT gallery
- Governance voting
- Analytics dashboard
- User profiles
- Transaction history
- Referral system

**Nice to Have**
- Multi-language support
- Advanced charts
- Live chat support
- Push notifications
- Mobile app
- Desktop app (Electron)

## Dependencies Summary

**Core**
- next@14.2.0
- react@18.3.0
- typescript@5.6.0

**Web3**
- wagmi@2.12.0
- viem@2.21.0
- @tanstack/react-query@5.56.0

**UI/UX**
- tailwindcss@3.4.0
- framer-motion@11.5.0
- lucide-react@0.446.0

**Data Visualization**
- recharts@2.12.0

**Utilities**
- clsx@2.1.0
- tailwind-merge@2.5.0

## File Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   ├── loading.tsx          # Loading state
│   ├── providers.tsx        # Context providers
│   ├── theme-provider.tsx   # Theme management
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── Navigation.tsx       # Top nav
│   ├── Hero.tsx            # Hero section
│   ├── HowItWorks.tsx      # Process section
│   ├── Tokenomics.tsx      # Charts & calculator
│   ├── FAQ.tsx             # Questions
│   ├── Footer.tsx          # Footer
│   ├── WalletConnect.tsx   # Wallet button
│   ├── TokenBalance.tsx    # Balance display
│   └── NetworkStatus.tsx   # Network indicator
├── lib/                     # Utilities
│   ├── wagmi.ts            # Web3 config
│   ├── contracts.ts        # Contract ABIs
│   ├── constants.ts        # App constants
│   └── utils.ts            # Helper functions
├── public/                  # Static assets
│   ├── favicon.svg         # Favicon
│   └── robots.txt          # SEO
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── tailwind.config.ts      # Tailwind config
├── next.config.js          # Next.js config
├── README.md               # Documentation
├── SETUP.md                # Setup guide
└── FEATURES.md             # This file
```

## Performance Metrics

**Target Scores**
- Lighthouse Performance: 95+
- Lighthouse Accessibility: 100
- Lighthouse Best Practices: 100
- Lighthouse SEO: 100

**Bundle Size**
- Initial JS: ~200KB (gzipped)
- Initial CSS: ~15KB (gzipped)
- Total page weight: <500KB

**Load Times**
- First Contentful Paint: <1.5s
- Largest Contentful Paint: <2.5s
- Time to Interactive: <3.5s

---

Built with modern best practices and optimized for the best user experience.

/**
 * HAVEN Token Constants
 * Central configuration for token economics, pricing, and app settings
 */

// Token Economics
export const TOKEN_CONSTANTS = {
  TOTAL_SUPPLY: 1_000_000_000, // 1 billion HNV tokens
  BASE_VALUE_CAD: 0.10, // 0.10 CAD per token
  BASE_VALUE_USD: 0.07, // Approximate USD value
  DECIMALS: 18,
  SYMBOL: 'HNV',
  NAME: 'HAVEN Token',
} as const;

// Reward Rates
export const REWARD_RATES = {
  BOOKING_RATE: 2, // 2 HNV per CAD spent
  REVIEW_BONUS: 50, // 50 HNV for verified review
  STAKING_APY: 10, // 10% annual percentage yield
  BURN_RATE: 2, // 2% burn on redemptions
} as const;

// Token Distribution (percentages)
export const TOKEN_DISTRIBUTION = [
  { name: 'Community Rewards', value: 40, color: '#6366f1' },
  { name: 'Staking Pool', value: 25, color: '#8b5cf6' },
  { name: 'Team & Development', value: 15, color: '#d946ef' },
  { name: 'Marketing', value: 10, color: '#f97316' },
  { name: 'Liquidity', value: 10, color: '#ec4899' },
] as const;

// Network Configuration
export const NETWORKS = {
  BASE_MAINNET: {
    id: 8453,
    name: 'Base',
    nativeCurrency: { name: 'Ethereum', symbol: 'ETH', decimals: 18 },
    rpcUrls: {
      default: { http: ['https://mainnet.base.org'] },
      public: { http: ['https://mainnet.base.org'] },
    },
    blockExplorers: {
      default: { name: 'BaseScan', url: 'https://basescan.org' },
    },
    testnet: false,
  },
  BASE_SEPOLIA: {
    id: 84532,
    name: 'Base Sepolia',
    nativeCurrency: { name: 'Ethereum', symbol: 'ETH', decimals: 18 },
    rpcUrls: {
      default: { http: ['https://sepolia.base.org'] },
      public: { http: ['https://sepolia.base.org'] },
    },
    blockExplorers: {
      default: { name: 'BaseScan', url: 'https://sepolia.basescan.org' },
    },
    testnet: true,
  },
} as const;

// App URLs
export const APP_URLS = {
  WEBSITE: 'https://haven-token.com',
  DOCS: 'https://docs.haven-token.com',
  GITHUB: 'https://github.com/pvt-haven/haven-token',
  TWITTER: 'https://twitter.com/haventoken',
  DISCORD: 'https://discord.gg/haventoken',
} as const;

// How It Works Steps
export const HOW_IT_WORKS_STEPS = [
  {
    number: 1,
    title: 'Book Your Stay',
    description: 'Earn 2 HNV tokens for every CAD spent on PVT property bookings',
    icon: 'calendar',
    gradient: 'from-primary-500 to-primary-600',
  },
  {
    number: 2,
    title: 'Engage with Community',
    description: 'Get bonus rewards for reviews, events, and community participation',
    icon: 'users',
    gradient: 'from-secondary-500 to-secondary-600',
  },
  {
    number: 3,
    title: 'Stake Your Tokens',
    description: 'Earn passive income with 10% APY on staked HAVEN tokens',
    icon: 'piggy-bank',
    gradient: 'from-purple-500 to-pink-600',
  },
  {
    number: 4,
    title: 'Redeem for Perks',
    description: 'Use tokens for bookings, exclusive experiences, and community benefits',
    icon: 'gift',
    gradient: 'from-accent-500 to-orange-600',
  },
] as const;

// FAQ Items
export const FAQ_ITEMS = [
  {
    question: 'What is HAVEN Token?',
    answer: 'HAVEN (HNV) is a blockchain-based loyalty token for the Puerto Vallarta Tribe (PVT) hospitality ecosystem. Built on Base (Ethereum L2), it rewards community members for bookings, reviews, and engagement while offering staking rewards and exclusive perks.',
  },
  {
    question: 'How do I earn HAVEN tokens?',
    answer: 'You earn 2 HNV for every CAD spent on PVT property bookings, 50 HNV bonus for verified reviews, rewards for attending events, and 10% APY by staking your tokens. The more you engage with the community, the more you earn!',
  },
  {
    question: 'What can I do with my HAVEN tokens?',
    answer: 'Redeem tokens for property bookings (1 HNV = 0.10 CAD), access exclusive experiences and events, receive community perks and upgrades, stake for passive income, or trade on decentralized exchanges.',
  },
  {
    question: 'How does staking work?',
    answer: 'Stake your HNV tokens to earn 10% annual percentage yield (APY). Rewards are calculated based on your staked amount and duration. There is a minimum staking period to ensure network stability.',
  },
  {
    question: 'Is there a transaction fee?',
    answer: 'HAVEN implements a 2% burn rate on redemptions, which helps maintain token value over time. Regular transfers between wallets have minimal gas fees on the Base network (typically less than $0.01).',
  },
  {
    question: 'Which wallets are supported?',
    answer: 'HAVEN works with any Web3 wallet that supports Base network, including MetaMask, Coinbase Wallet, Rainbow, and WalletConnect-compatible wallets. Make sure to add Base network to your wallet.',
  },
  {
    question: 'Is HAVEN Token secure?',
    answer: 'Yes! HAVEN is built on Base (Ethereum L2) using audited smart contracts. The token follows ERC-20 standards with additional security features including multi-signature controls and role-based access.',
  },
  {
    question: 'How do I get started?',
    answer: 'Connect your Web3 wallet (make sure it\'s on Base network), start booking PVT properties to earn tokens, explore staking options, and join the community to unlock exclusive perks and rewards!',
  },
] as const;

// Animation Variants for Framer Motion
export const ANIMATION_VARIANTS = {
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.6 } },
  },
  slideUp: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  },
  slideDown: {
    hidden: { opacity: 0, y: -20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  },
  scaleIn: {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.4 } },
  },
  staggerContainer: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  },
} as const;

// Utility function to format large numbers
export const formatNumber = (num: number): string => {
  if (num >= 1_000_000_000) {
    return `${(num / 1_000_000_000).toFixed(1)}B`;
  }
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toFixed(2);
};

// Utility function to format token amounts
export const formatTokenAmount = (amount: bigint, decimals: number = TOKEN_CONSTANTS.DECIMALS): string => {
  const divisor = BigInt(10 ** decimals);
  const whole = amount / divisor;
  const remainder = amount % divisor;

  if (remainder === BigInt(0)) {
    return whole.toString();
  }

  const decimalStr = remainder.toString().padStart(decimals, '0');
  const trimmed = decimalStr.replace(/0+$/, '').slice(0, 2);

  return trimmed ? `${whole}.${trimmed}` : whole.toString();
};

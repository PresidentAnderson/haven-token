/**
 * Wagmi Configuration
 * Web3 wallet connection and blockchain interaction setup
 */

import { createConfig, http } from 'wagmi';
import { base, baseSepolia } from 'wagmi/chains';
import { injected, walletConnect } from 'wagmi/connectors';

// Get WalletConnect project ID from environment
const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '';

// Configure chains based on environment
const enableTestnets = process.env.NEXT_PUBLIC_ENABLE_TESTNETS === 'true';
const chains = enableTestnets
  ? [base, baseSepolia] as const
  : [base] as const;

// Configure connectors
const connectors = [
  injected({
    shimDisconnect: true,
    target: 'metaMask',
  }),
  ...(projectId ? [
    walletConnect({
      projectId,
      metadata: {
        name: 'HAVEN Token',
        description: 'Blockchain Loyalty for PVT Hospitality',
        url: process.env.NEXT_PUBLIC_SITE_URL || 'https://haven-token.com',
        icons: ['https://haven-token.com/icon.png'],
      },
      showQrModal: true,
    })
  ] : []),
];

// Configure transports with custom RPC URLs if available
const alchemyKey = process.env.NEXT_PUBLIC_ALCHEMY_API_KEY;

const transports = enableTestnets ? {
  [base.id]: alchemyKey
    ? http(`https://base-mainnet.g.alchemy.com/v2/${alchemyKey}`)
    : http('https://mainnet.base.org'),
  [baseSepolia.id]: alchemyKey
    ? http(`https://base-sepolia.g.alchemy.com/v2/${alchemyKey}`)
    : http('https://sepolia.base.org'),
} : {
  [base.id]: alchemyKey
    ? http(`https://base-mainnet.g.alchemy.com/v2/${alchemyKey}`)
    : http('https://mainnet.base.org'),
};

// Create wagmi config
export const config = createConfig({
  chains,
  connectors,
  transports: transports as any,
  ssr: true,
  batch: {
    multicall: true,
  },
});

// Export chain configuration
export { base, baseSepolia };
export const defaultChain = enableTestnets ? baseSepolia : base;

// Type exports for TypeScript
declare module 'wagmi' {
  interface Register {
    config: typeof config;
  }
}

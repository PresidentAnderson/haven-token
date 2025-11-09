/**
 * HAVEN Token Contract Configuration
 * Contract addresses, ABIs, and interaction utilities
 */

// Minimal ERC-20 ABI for reading token data
export const HAVEN_ABI = [
  {
    inputs: [],
    name: 'totalSupply',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'address', name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ internalType: 'uint256', name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'name',
    outputs: [{ internalType: 'string', name: '', type: 'string' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'symbol',
    outputs: [{ internalType: 'string', name: '', type: 'string' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [],
    name: 'decimals',
    outputs: [{ internalType: 'uint8', name: '', type: 'uint8' }],
    stateMutability: 'view',
    type: 'function',
  },
  {
    inputs: [
      { internalType: 'address', name: 'to', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' },
    ],
    name: 'transfer',
    outputs: [{ internalType: 'bool', name: '', type: 'bool' }],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    anonymous: false,
    inputs: [
      { indexed: true, internalType: 'address', name: 'from', type: 'address' },
      { indexed: true, internalType: 'address', name: 'to', type: 'address' },
      { indexed: false, internalType: 'uint256', name: 'value', type: 'uint256' },
    ],
    name: 'Transfer',
    type: 'event',
  },
] as const;

// Contract addresses from environment variables
export const getContractAddress = (chainId: number): `0x${string}` | undefined => {
  // Base Mainnet (8453)
  if (chainId === 8453) {
    return process.env.NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS as `0x${string}` | undefined;
  }

  // Base Sepolia Testnet (84532)
  if (chainId === 84532) {
    return process.env.NEXT_PUBLIC_HAVEN_CONTRACT_ADDRESS_TESTNET as `0x${string}` | undefined;
  }

  return undefined;
};

// Contract configuration helper
export const getContractConfig = (chainId: number) => {
  const address = getContractAddress(chainId);

  if (!address) {
    console.warn(`No contract address configured for chain ${chainId}`);
    return null;
  }

  return {
    address,
    abi: HAVEN_ABI,
  };
};

// Type-safe contract read configuration
export const createReadConfig = (
  chainId: number,
  functionName: string,
  args?: unknown[]
) => {
  const config = getContractConfig(chainId);

  if (!config) {
    throw new Error(`Contract not configured for chain ${chainId}`);
  }

  return {
    address: config.address,
    abi: config.abi,
    functionName,
    args,
  };
};

// Helper to get block explorer URL
export const getExplorerUrl = (chainId: number, address: string): string => {
  const baseUrl = chainId === 8453
    ? 'https://basescan.org'
    : 'https://sepolia.basescan.org';

  return `${baseUrl}/address/${address}`;
};

// Helper to get transaction explorer URL
export const getTransactionUrl = (chainId: number, hash: string): string => {
  const baseUrl = chainId === 8453
    ? 'https://basescan.org'
    : 'https://sepolia.basescan.org';

  return `${baseUrl}/tx/${hash}`;
};

'use client';

/**
 * TokenBalance Component
 * Displays user's HAVEN token balance from blockchain
 */

import { useReadContract, useAccount } from 'wagmi';
import { HAVEN_ABI, getContractAddress } from '@/lib/contracts';
import { formatTokenAmount, TOKEN_CONSTANTS } from '@/lib/constants';
import { Coins, Loader2 } from 'lucide-react';

interface TokenBalanceProps {
  address?: `0x${string}`;
}

export function TokenBalance({ address }: TokenBalanceProps) {
  const { chain } = useAccount();

  const contractAddress = chain?.id ? getContractAddress(chain.id) : undefined;

  const { data: balance, isError, isLoading } = useReadContract({
    address: contractAddress,
    abi: HAVEN_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && !!contractAddress,
      refetchInterval: 10000, // Refetch every 10 seconds
    },
  });

  if (!contractAddress) {
    return (
      <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400">
        <AlertTriangle className="w-4 h-4" />
        <span className="text-sm">Contract not configured</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading balance...</span>
      </div>
    );
  }

  if (isError || balance === undefined) {
    return (
      <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
        <Coins className="w-4 h-4" />
        <span className="text-sm">Unable to load balance</span>
      </div>
    );
  }

  const formattedBalance = formatTokenAmount(balance, TOKEN_CONSTANTS.DECIMALS);

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2 text-gray-700 dark:text-gray-300">
        <Coins className="w-5 h-5 text-primary-500" />
        <span className="text-sm font-medium">Your Balance</span>
      </div>
      <div className="text-right">
        <div className="font-bold text-lg text-gray-900 dark:text-white">
          {formattedBalance} HNV
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          ≈ ${(Number(formattedBalance) * TOKEN_CONSTANTS.BASE_VALUE_USD).toFixed(2)} USD
        </div>
      </div>
    </div>
  );
}

function AlertTriangle({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

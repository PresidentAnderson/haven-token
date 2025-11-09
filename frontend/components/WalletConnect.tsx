'use client';

/**
 * WalletConnect Component
 * Wallet connection button with network switching and balance display
 */

import { useAccount, useConnect, useDisconnect, useSwitchChain } from 'wagmi';
import { Wallet, LogOut, AlertTriangle } from 'lucide-react';
import { truncateAddress } from '@/lib/utils';
import { base, baseSepolia } from '@/lib/wagmi';
import { useState } from 'react';
import { TokenBalance } from './TokenBalance';

export function WalletConnect() {
  const { address, isConnected, chain } = useAccount();
  const { connect, connectors } = useConnect();
  const { disconnect } = useDisconnect();
  const { switchChain } = useSwitchChain();
  const [showDropdown, setShowDropdown] = useState(false);

  // Check if we're on the correct network
  const isCorrectNetwork = chain?.id === base.id || chain?.id === baseSepolia.id;

  // Handle wallet connection
  const handleConnect = () => {
    const injectedConnector = connectors.find((c) => c.id === 'injected');
    if (injectedConnector) {
      connect({ connector: injectedConnector });
    } else if (connectors[0]) {
      connect({ connector: connectors[0] });
    }
  };

  // Handle network switch
  const handleSwitchNetwork = () => {
    if (switchChain) {
      switchChain({ chainId: base.id });
    }
  };

  // Not connected state
  if (!isConnected) {
    return (
      <button
        onClick={handleConnect}
        className="flex items-center space-x-2 px-4 sm:px-6 py-2 sm:py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95"
      >
        <Wallet className="w-4 h-4 sm:w-5 sm:h-5" />
        <span className="hidden sm:inline">Connect Wallet</span>
        <span className="sm:hidden">Connect</span>
      </button>
    );
  }

  // Wrong network state
  if (!isCorrectNetwork) {
    return (
      <button
        onClick={handleSwitchNetwork}
        className="flex items-center space-x-2 px-4 sm:px-6 py-2 sm:py-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95"
      >
        <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5" />
        <span className="hidden sm:inline">Switch to Base</span>
        <span className="sm:hidden">Wrong Network</span>
      </button>
    );
  }

  // Connected state
  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-3 px-4 sm:px-6 py-2 sm:py-3 glass hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 active:scale-95"
      >
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span className="font-mono text-sm font-medium text-gray-900 dark:text-white">
          {truncateAddress(address || '')}
        </span>
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowDropdown(false)}
          />
          <div className="absolute right-0 mt-2 w-72 glass rounded-lg shadow-xl z-20 overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Connected Wallet
                </span>
                <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                  {chain?.name}
                </span>
              </div>
              <div className="font-mono text-sm text-gray-900 dark:text-white">
                {address}
              </div>
            </div>

            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <TokenBalance address={address} />
            </div>

            <div className="p-2">
              <button
                onClick={() => {
                  disconnect();
                  setShowDropdown(false);
                }}
                className="w-full flex items-center space-x-2 px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors duration-200"
              >
                <LogOut className="w-4 h-4" />
                <span className="font-medium">Disconnect</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

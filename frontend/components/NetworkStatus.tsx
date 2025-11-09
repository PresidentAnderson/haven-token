'use client';

/**
 * Network Status Component
 * Shows current network and testnet warning banner
 */

import { useAccount } from 'wagmi';
import { AlertTriangle, Wifi } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { baseSepolia } from '@/lib/wagmi';

export function NetworkStatus() {
  const { chain, isConnected } = useAccount();

  const isTestnet = chain?.id === baseSepolia.id;

  if (!isConnected || !isTestnet) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -100, opacity: 0 }}
        className="fixed top-20 left-0 right-0 z-40 no-print"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-amber-500 dark:bg-amber-600 rounded-lg shadow-lg p-4">
            <div className="flex items-center justify-center space-x-3">
              <AlertTriangle className="w-5 h-5 text-white flex-shrink-0" />
              <div className="flex items-center space-x-2 text-white">
                <Wifi className="w-4 h-4" />
                <span className="font-semibold text-sm sm:text-base">
                  You are connected to {chain?.name} (Testnet)
                </span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

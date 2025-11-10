'use client';

/**
 * Hero Section Component
 * Main landing page hero with animated gradient and CTAs
 */

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, TrendingUp } from 'lucide-react';
import { WalletConnect } from './WalletConnect';
import { useReadContract, useAccount } from 'wagmi';
import { HAVEN_ABI, getContractAddress } from '@/lib/contracts';
import { formatNumber, TOKEN_CONSTANTS } from '@/lib/constants';

export function Hero() {
  const { chain } = useAccount();
  const contractAddress = chain?.id ? getContractAddress(chain.id) : undefined;

  const { data: totalSupply } = useReadContract({
    address: contractAddress,
    abi: HAVEN_ABI,
    functionName: 'totalSupply',
    query: {
      enabled: !!contractAddress,
    },
  });

  const handleLearnMore = () => {
    const element = document.querySelector('#how-it-works');
    element?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 hero-gradient" />

      {/* Animated Orbs */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/30 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary-500/30 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 1,
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
        <div className="text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full border border-white/30 mb-8"
          >
            <Sparkles className="w-4 h-4 text-white" />
            <span className="text-white text-sm font-medium">
              Proprietary to PVT Hostel • Backed by Real Estate
            </span>
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="heading-1 text-white mb-6"
          >
            Earn Rewards,
            <br />
            Build Community,
            <br />
            <span className="inline-block bg-white/20 backdrop-blur-sm px-4 rounded-lg">
              Own Your Loyalty
            </span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-xl sm:text-2xl text-white/90 mb-4 max-w-3xl mx-auto leading-relaxed"
          >
            HAVEN Token is PVT Hostel's proprietary blockchain-based loyalty program,
            backed by real estate assets. Earn tokens on bookings, stake for rewards,
            and unlock exclusive perks within our hospitality ecosystem.
          </motion.p>

          {/* Token Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-8 mb-12"
          >
            <div className="flex items-center space-x-2 text-white">
              <TrendingUp className="w-5 h-5 text-green-300" />
              <span className="text-lg font-semibold">
                ${TOKEN_CONSTANTS.BASE_VALUE_USD.toFixed(2)} USD
              </span>
              <span className="text-white/70">per token</span>
            </div>
            <div className="hidden sm:block w-1 h-6 bg-white/30" />
            <div className="flex items-center space-x-2 text-white">
              <span className="text-lg font-semibold">
                {totalSupply
                  ? formatNumber(
                      Number(totalSupply) / Math.pow(10, TOKEN_CONSTANTS.DECIMALS)
                    )
                  : formatNumber(TOKEN_CONSTANTS.TOTAL_SUPPLY)}
              </span>
              <span className="text-white/70">total supply</span>
            </div>
          </motion.div>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <WalletConnect />
            <button
              onClick={handleLearnMore}
              className="flex items-center space-x-2 px-6 py-3 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white font-semibold rounded-lg border border-white/30 shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95"
            >
              <span>Learn More</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </motion.div>

          {/* Trust Indicators */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-4xl mx-auto"
          >
            <div className="glass p-6 rounded-2xl">
              <div className="text-3xl font-bold text-white mb-2">2 HNV</div>
              <div className="text-white/70">Per CAD Spent</div>
            </div>
            <div className="glass p-6 rounded-2xl">
              <div className="text-3xl font-bold text-white mb-2">10% APY</div>
              <div className="text-white/70">Staking Rewards</div>
            </div>
            <div className="glass p-6 rounded-2xl">
              <div className="text-3xl font-bold text-white mb-2">50 HNV</div>
              <div className="text-white/70">Review Bonus</div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 border-2 border-white/50 rounded-full flex items-start justify-center p-2"
        >
          <div className="w-1.5 h-1.5 bg-white rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
}

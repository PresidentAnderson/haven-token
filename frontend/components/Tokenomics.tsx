'use client';

/**
 * Tokenomics Component
 * Token distribution visualization and reward calculator
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Calculator, TrendingUp, Flame } from 'lucide-react';
import {
  TOKEN_DISTRIBUTION,
  TOKEN_CONSTANTS,
  REWARD_RATES,
  ANIMATION_VARIANTS,
} from '@/lib/constants';
import { formatNumber, formatCurrency, calculateTokensEarned, calculateStakingRewards } from '@/lib/utils';

export function Tokenomics() {
  const [calculatorMode, setCalculatorMode] = useState<'booking' | 'staking'>('booking');
  const [bookingAmount, setBookingAmount] = useState(1000);
  const [stakingAmount, setStakingAmount] = useState(10000);
  const [stakingDays, setStakingDays] = useState(365);

  const bookingRewards = calculateTokensEarned(bookingAmount, REWARD_RATES.BOOKING_RATE);
  const stakingRewards = calculateStakingRewards(
    stakingAmount,
    REWARD_RATES.STAKING_APY,
    stakingDays
  );

  return (
    <section id="tokenomics" className="section">
      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={ANIMATION_VARIANTS.fadeIn}
          className="text-center mb-16"
        >
          <h2 className="heading-2 text-gray-900 dark:text-white mb-4">
            Tokenomics
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Transparent, sustainable token economics designed for long-term value
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Token Distribution Chart */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-50px' }}
            variants={ANIMATION_VARIANTS.slideUp}
            className="card"
          >
            <h3 className="heading-4 text-gray-900 dark:text-white mb-6">
              Token Distribution
            </h3>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[...TOKEN_DISTRIBUTION]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {TOKEN_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-6 space-y-3">
              {TOKEN_DISTRIBUTION.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {item.name}
                    </span>
                  </div>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Token Info & Stats */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-50px' }}
            variants={ANIMATION_VARIANTS.slideUp}
            className="space-y-6"
          >
            {/* Token Stats */}
            <div className="card">
              <h3 className="heading-4 text-gray-900 dark:text-white mb-6">
                Token Information
              </h3>

              <div className="space-y-4">
                <div className="flex justify-between items-center pb-4 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-gray-600 dark:text-gray-400">Symbol</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {TOKEN_CONSTANTS.SYMBOL}
                  </span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-gray-600 dark:text-gray-400">Total Supply</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {formatNumber(TOKEN_CONSTANTS.TOTAL_SUPPLY, 0)}
                  </span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-gray-600 dark:text-gray-400">Base Value</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {formatCurrency(TOKEN_CONSTANTS.BASE_VALUE_CAD, 'CAD')}
                  </span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-gray-600 dark:text-gray-400">Network</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    Base (Ethereum L2)
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Decimals</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {TOKEN_CONSTANTS.DECIMALS}
                  </span>
                </div>
              </div>
            </div>

            {/* Reward Rates */}
            <div className="grid grid-cols-2 gap-4">
              <div className="card bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20">
                <TrendingUp className="w-8 h-8 text-primary-600 dark:text-primary-400 mb-2" />
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {REWARD_RATES.STAKING_APY}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Staking APY
                </div>
              </div>

              <div className="card bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20">
                <Flame className="w-8 h-8 text-orange-600 dark:text-orange-400 mb-2" />
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {REWARD_RATES.BURN_RATE}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Burn Rate
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Rewards Calculator */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={ANIMATION_VARIANTS.slideUp}
          className="card mt-12"
        >
          <div className="flex items-center space-x-3 mb-6">
            <Calculator className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            <h3 className="heading-4 text-gray-900 dark:text-white">
              Rewards Calculator
            </h3>
          </div>

          {/* Calculator Mode Toggle */}
          <div className="flex space-x-2 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            <button
              onClick={() => setCalculatorMode('booking')}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-all duration-200 ${
                calculatorMode === 'booking'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-md'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Booking Rewards
            </button>
            <button
              onClick={() => setCalculatorMode('staking')}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-all duration-200 ${
                calculatorMode === 'staking'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-md'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Staking Rewards
            </button>
          </div>

          {/* Booking Calculator */}
          {calculatorMode === 'booking' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Booking Amount (CAD)
                </label>
                <input
                  type="range"
                  min="100"
                  max="10000"
                  step="100"
                  value={bookingAmount}
                  onChange={(e) => setBookingAmount(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {formatCurrency(100, 'CAD')}
                  </span>
                  <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                    {formatCurrency(bookingAmount, 'CAD')}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {formatCurrency(10000, 'CAD')}
                  </span>
                </div>
              </div>

              <div className="glass rounded-xl p-6 text-center">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  You will earn
                </div>
                <div className="text-4xl font-bold gradient-text mb-2">
                  {formatNumber(bookingRewards, 0)} HNV
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Worth approximately{' '}
                  {formatCurrency(bookingRewards * TOKEN_CONSTANTS.BASE_VALUE_CAD, 'CAD')}
                </div>
              </div>
            </div>
          )}

          {/* Staking Calculator */}
          {calculatorMode === 'staking' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Staking Amount (HNV)
                </label>
                <input
                  type="range"
                  min="1000"
                  max="100000"
                  step="1000"
                  value={stakingAmount}
                  onChange={(e) => setStakingAmount(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">1,000</span>
                  <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                    {formatNumber(stakingAmount, 0)} HNV
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">100,000</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Staking Period (Days)
                </label>
                <input
                  type="range"
                  min="30"
                  max="365"
                  step="30"
                  value={stakingDays}
                  onChange={(e) => setStakingDays(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">30 days</span>
                  <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                    {stakingDays} days
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">365 days</span>
                </div>
              </div>

              <div className="glass rounded-xl p-6 text-center">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Estimated rewards
                </div>
                <div className="text-4xl font-bold gradient-text mb-2">
                  {formatNumber(stakingRewards, 2)} HNV
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Total: {formatNumber(stakingAmount + stakingRewards, 2)} HNV
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
}

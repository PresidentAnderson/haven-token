'use client';

/**
 * Real Estate Backing Section
 * Highlights that HAVEN Token is backed by real estate assets
 */

import { motion } from 'framer-motion';
import { Building2, Shield, TrendingUp, Lock } from 'lucide-react';

export function RealEstateBacking() {
  const features = [
    {
      icon: Building2,
      title: 'Asset-Backed',
      description:
        'HAVEN tokens are backed by PVT Holdings, Inc. real estate holdings, providing tangible value and security.',
    },
    {
      icon: Shield,
      title: 'PVT Proprietary',
      description:
        'Exclusively owned and operated by PVT Holdings, Inc., ensuring alignment with our hospitality ecosystem.',
    },
    {
      icon: TrendingUp,
      title: 'Value Growth',
      description:
        'As our real estate portfolio expands, token value is supported by increasing asset backing.',
    },
    {
      icon: Lock,
      title: 'Deflationary Model',
      description:
        '2% burn rate on redemptions reduces supply over time, creating scarcity and value appreciation.',
    },
  ];

  return (
    <section id="real-estate-backing" className="py-20 sm:py-32 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 rounded-full mb-4">
            <Building2 className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            <span className="text-primary-600 dark:text-primary-400 text-sm font-semibold">
              Real Estate Backed
            </span>
          </div>
          <h2 className="heading-2 mb-6">
            Secured by{' '}
            <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
              Real Assets
            </span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Unlike traditional loyalty points, HAVEN Token is backed by PVT Holdings, Inc.'s
            growing real estate portfolio, providing genuine value and security to our
            community.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="glass p-8 rounded-2xl hover:shadow-xl transition-shadow duration-300"
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Value Proposition */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="glass p-8 sm:p-12 rounded-2xl text-center"
        >
          <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Why Real Estate Backing Matters
          </h3>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8">
            PVT Holdings, Inc.'s real estate holdings provide a stable foundation for HAVEN Token's
            value. As we expand our property portfolio and improve our facilities, the
            underlying asset base grows, supporting long-term token appreciation while
            maintaining stable redemption values.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-8">
            <div className="bg-white/50 dark:bg-gray-800/50 p-6 rounded-xl">
              <div className="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                $0.07 USD
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Base Token Value
              </div>
            </div>
            <div className="bg-white/50 dark:bg-gray-800/50 p-6 rounded-xl">
              <div className="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                100%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                PVT Owned & Operated
              </div>
            </div>
            <div className="bg-white/50 dark:bg-gray-800/50 p-6 rounded-xl">
              <div className="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                2%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Deflationary Burn Rate
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

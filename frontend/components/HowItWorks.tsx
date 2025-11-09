'use client';

/**
 * How It Works Component
 * 4-step process showing how to earn and use HAVEN tokens
 */

import { motion } from 'framer-motion';
import {
  Calendar,
  Users,
  PiggyBank,
  Gift,
  ArrowRight,
  CheckCircle,
} from 'lucide-react';
import { HOW_IT_WORKS_STEPS, ANIMATION_VARIANTS } from '@/lib/constants';

const iconMap = {
  calendar: Calendar,
  users: Users,
  'piggy-bank': PiggyBank,
  gift: Gift,
};

export function HowItWorks() {
  return (
    <section id="how-it-works" className="section bg-gray-50 dark:bg-gray-900">
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
            How HAVEN Works
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Start earning rewards in four simple steps
          </p>
        </motion.div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {HOW_IT_WORKS_STEPS.map((step, index) => {
            const Icon = iconMap[step.icon as keyof typeof iconMap];

            return (
              <motion.div
                key={step.number}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-50px' }}
                variants={ANIMATION_VARIANTS.slideUp}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {/* Connector Arrow (desktop only) */}
                {index < HOW_IT_WORKS_STEPS.length - 1 && (
                  <div className="hidden lg:block absolute top-20 -right-4 z-0">
                    <ArrowRight className="w-8 h-8 text-gray-300 dark:text-gray-700" />
                  </div>
                )}

                {/* Step Card */}
                <div className="card-hover h-full relative z-10">
                  {/* Step Number */}
                  <div
                    className={`inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br ${step.gradient} text-white font-bold text-xl mb-4 shadow-lg`}
                  >
                    {step.number}
                  </div>

                  {/* Icon */}
                  <div className="mb-4">
                    <Icon className="w-12 h-12 text-primary-500 dark:text-primary-400" />
                  </div>

                  {/* Title */}
                  <h3 className="heading-4 text-gray-900 dark:text-white mb-2">
                    {step.title}
                  </h3>

                  {/* Description */}
                  <p className="text-gray-600 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Additional Benefits */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={ANIMATION_VARIANTS.staggerContainer}
          className="glass rounded-2xl p-8 md:p-12"
        >
          <h3 className="heading-3 text-gray-900 dark:text-white mb-8 text-center">
            Why Choose HAVEN?
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: 'True Ownership',
                description:
                  'Your tokens, your wallet. No central authority can freeze or revoke your rewards.',
              },
              {
                title: 'Transparent & Secure',
                description:
                  'All transactions on blockchain. Audited smart contracts ensure safety.',
              },
              {
                title: 'Growing Value',
                description:
                  '2% burn rate on redemptions helps maintain token value over time.',
              },
              {
                title: 'Community Governed',
                description:
                  'Token holders have a say in the future direction of the ecosystem.',
              },
              {
                title: 'Multiple Earning Ways',
                description:
                  'Bookings, reviews, events, staking - more ways to earn than traditional programs.',
              },
              {
                title: 'Instant Redemption',
                description:
                  'Use tokens immediately for bookings and perks. No waiting periods.',
              },
            ].map((benefit) => (
              <motion.div
                key={benefit.title}
                variants={ANIMATION_VARIANTS.slideUp}
                className="flex items-start space-x-3"
              >
                <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                    {benefit.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {benefit.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

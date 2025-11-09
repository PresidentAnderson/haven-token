'use client';

/**
 * FAQ Component
 * Frequently asked questions accordion
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, HelpCircle } from 'lucide-react';
import { FAQ_ITEMS, ANIMATION_VARIANTS } from '@/lib/constants';

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleQuestion = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="section bg-gray-50 dark:bg-gray-900">
      <div className="section-container max-w-4xl">
        {/* Section Header */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={ANIMATION_VARIANTS.fadeIn}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 rounded-full mb-4">
            <HelpCircle className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            <span className="text-primary-600 dark:text-primary-400 font-medium">
              Got Questions?
            </span>
          </div>
          <h2 className="heading-2 text-gray-900 dark:text-white mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Everything you need to know about HAVEN Token
          </p>
        </motion.div>

        {/* FAQ Items */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={ANIMATION_VARIANTS.staggerContainer}
          className="space-y-4"
        >
          {FAQ_ITEMS.map((item, index) => (
            <motion.div
              key={index}
              variants={ANIMATION_VARIANTS.slideUp}
              className="card cursor-pointer overflow-hidden"
              onClick={() => toggleQuestion(index)}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white pr-8">
                  {item.question}
                </h3>
                <motion.div
                  animate={{ rotate: openIndex === index ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex-shrink-0"
                >
                  <ChevronDown className="w-6 h-6 text-gray-500 dark:text-gray-400" />
                </motion.div>
              </div>

              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="pt-4 text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </motion.div>

        {/* Still Have Questions CTA */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          variants={ANIMATION_VARIANTS.fadeIn}
          className="mt-12 text-center"
        >
          <div className="glass rounded-2xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Still have questions?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Join our community on Discord or check out our comprehensive documentation
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="https://discord.gg/haventoken"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                Join Discord
              </a>
              <a
                href="/docs"
                className="btn-secondary"
              >
                Read Documentation
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

'use client';

/**
 * Main Landing Page
 * Combines all sections into a cohesive landing page experience
 */

import { Navigation } from '@/components/Navigation';
import { Hero } from '@/components/Hero';
import { HowItWorks } from '@/components/HowItWorks';
import { Tokenomics } from '@/components/Tokenomics';
import { FAQ } from '@/components/FAQ';
import { Footer } from '@/components/Footer';
import { NetworkStatus } from '@/components/NetworkStatus';
import { ClientOnly } from '@/components/ClientOnly';

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic';

export default function Home() {
  return (
    <main className="min-h-screen">
      <ClientOnly>
        <Navigation />
        <NetworkStatus />
        <Hero />
        <HowItWorks />
        <Tokenomics />
        <FAQ />
        <Footer />
      </ClientOnly>
    </main>
  );
}

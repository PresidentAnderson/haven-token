import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'HAVEN Token - Blockchain Loyalty for PVT Hospitality',
  description:
    'Earn rewards, build community, and own your loyalty with HAVEN Token. The blockchain-based loyalty token for Puerto Vallarta Tribe hospitality ecosystem on Base.',
  keywords: [
    'HAVEN Token',
    'HNV',
    'blockchain',
    'loyalty token',
    'Base',
    'Ethereum',
    'L2',
    'Puerto Vallarta',
    'hospitality',
    'rewards',
    'staking',
  ],
  authors: [{ name: 'HAVEN Token Team' }],
  creator: 'HAVEN Token',
  publisher: 'HAVEN Token',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://haven-token.com',
    title: 'HAVEN Token - Blockchain Loyalty for PVT Hospitality',
    description:
      'Earn rewards, build community, and own your loyalty with HAVEN Token on Base blockchain.',
    siteName: 'HAVEN Token',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'HAVEN Token',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'HAVEN Token - Blockchain Loyalty for PVT Hospitality',
    description:
      'Earn rewards, build community, and own your loyalty with HAVEN Token on Base blockchain.',
    creator: '@haventoken',
    images: ['/twitter-image.png'],
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#6366f1' },
    { media: '(prefers-color-scheme: dark)', color: '#4338ca' },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

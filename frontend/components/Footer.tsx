'use client';

/**
 * Footer Component
 * Site footer with links and contract information
 */

import { Github, Twitter, FileText, ExternalLink, Compass } from 'lucide-react';
import { useAccount } from 'wagmi';
import { getContractAddress, getExplorerUrl } from '@/lib/contracts';
import { APP_URLS } from '@/lib/constants';

export function Footer() {
  const { chain } = useAccount();
  const contractAddress = chain?.id ? getContractAddress(chain.id) : undefined;
  const explorerUrl = contractAddress && chain?.id
    ? getExplorerUrl(chain.id, contractAddress)
    : null;

  const currentYear = new Date().getFullYear();

  const footerLinks = {
    Product: [
      { name: 'How It Works', href: '#how-it-works' },
      { name: 'Tokenomics', href: '#tokenomics' },
      { name: 'FAQ', href: '#faq' },
      { name: 'Roadmap', href: '/roadmap' },
    ],
    Resources: [
      { name: 'Documentation', href: APP_URLS.DOCS, external: true },
      { name: 'Whitepaper', href: '/whitepaper.pdf', external: true },
      { name: 'Brand Kit', href: '/brand' },
      { name: 'API', href: '/api' },
    ],
    Community: [
      { name: 'Discord', href: APP_URLS.DISCORD, external: true },
      { name: 'Twitter', href: APP_URLS.TWITTER, external: true },
      { name: 'GitHub', href: APP_URLS.GITHUB, external: true },
      { name: 'Blog', href: '/blog' },
    ],
    Legal: [
      { name: 'Privacy Policy', href: '/privacy' },
      { name: 'Terms of Service', href: '/terms' },
      { name: 'Cookie Policy', href: '/cookies' },
      { name: 'Disclaimer', href: '/disclaimer' },
    ],
  };

  return (
    <footer className="bg-gray-900 dark:bg-black text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Content */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-12">
          {/* Brand Column */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-xl">H</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold gradient-text">HAVEN</span>
                <span className="text-xs text-gray-400 -mt-1">Token</span>
              </div>
            </div>
            <p className="text-gray-400 text-sm mb-4">
              Blockchain loyalty for the Puerto Vallarta Tribe hospitality ecosystem.
            </p>
            <div className="flex items-center space-x-4">
              <a
                href={APP_URLS.TWITTER}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors duration-200"
                aria-label="Twitter"
              >
                <Twitter className="w-5 h-5" />
              </a>
              <a
                href={APP_URLS.DISCORD}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors duration-200"
                aria-label="Discord"
              >
                <Compass className="w-5 h-5" />
              </a>
              <a
                href={APP_URLS.GITHUB}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors duration-200"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Link Columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="font-semibold text-white mb-4">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      target={'external' in link && link.external ? '_blank' : undefined}
                      rel={'external' in link && link.external ? 'noopener noreferrer' : undefined}
                      className="text-gray-400 hover:text-white text-sm transition-colors duration-200 inline-flex items-center"
                      onClick={(e) => {
                        if (!('external' in link && link.external) && link.href.startsWith('#')) {
                          e.preventDefault();
                          const element = document.querySelector(link.href);
                          element?.scrollIntoView({ behavior: 'smooth' });
                        }
                      }}
                    >
                      {link.name}
                      {'external' in link && link.external && (
                        <ExternalLink className="w-3 h-3 ml-1" />
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Contract Address Section */}
        {explorerUrl && (
          <div className="border-t border-gray-800 pt-8 mb-8">
            <div className="glass rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="text-sm text-gray-400 mb-1">Contract Address</div>
                <div className="font-mono text-sm text-white break-all">
                  {contractAddress}
                </div>
              </div>
              <a
                href={explorerUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors duration-200 whitespace-nowrap"
              >
                <span className="text-sm font-medium">View on BaseScan</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        )}

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-400">
              © {currentYear} HAVEN Token. All rights reserved.
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <a
                href="/privacy"
                className="hover:text-white transition-colors duration-200"
              >
                Privacy
              </a>
              <a
                href="/terms"
                className="hover:text-white transition-colors duration-200"
              >
                Terms
              </a>
              <a
                href={APP_URLS.DOCS}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white transition-colors duration-200 inline-flex items-center"
              >
                <FileText className="w-4 h-4 mr-1" />
                Docs
              </a>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 text-center text-xs text-gray-500">
          <p>
            HAVEN Token is a digital asset. Cryptocurrency investments carry risk.
            Please do your own research before investing.
          </p>
        </div>
      </div>
    </footer>
  );
}

'use client';

/**
 * Navigation Component
 * Top navigation bar with wallet connection and theme toggle
 */

import { useState, useEffect } from 'react';
import { Menu, X, Moon, Sun } from 'lucide-react';
import { WalletConnect } from './WalletConnect';
import { useTheme } from '@/app/theme-provider';
import { cn } from '@/lib/utils';

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Safe theme hook usage
  let theme = 'light';
  let setTheme: any = (_: string) => {};

  try {
    const themeContext = useTheme();
    theme = themeContext.theme;
    setTheme = themeContext.setTheme;
  } catch {
    // Theme provider not available during SSR
  }

  useEffect(() => {
    setMounted(true);
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleTheme = () => {
    if (mounted) {
      setTheme(theme === 'dark' ? 'light' : 'dark');
    }
  };

  const navLinks = [
    { name: 'How It Works', href: '#how-it-works' },
    { name: 'Tokenomics', href: '#tokenomics' },
    { name: 'FAQ', href: '#faq' },
    { name: 'Docs', href: '/docs', external: true },
  ];

  return (
    <nav
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        isScrolled
          ? 'bg-white/80 dark:bg-gray-950/80 backdrop-blur-lg shadow-lg'
          : 'bg-transparent'
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo */}
          <div className="flex items-center">
            <a
              href="#"
              className="flex items-center space-x-3 group"
              onClick={(e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-glow transition-all duration-300">
                <span className="text-white font-bold text-xl">H</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold gradient-text">HAVEN</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 -mt-1">
                  Token
                </span>
              </div>
            </a>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 font-medium transition-colors duration-200"
                onClick={(e) => {
                  if (!link.external) {
                    e.preventDefault();
                    const element = document.querySelector(link.href);
                    element?.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              ) : (
                <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              )}
            </button>
            <WalletConnect />
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center space-x-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              ) : (
                <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              )}
            </button>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
              aria-label="Toggle menu"
            >
              {isOpen ? (
                <X className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              ) : (
                <Menu className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isOpen && (
        <div className="md:hidden glass border-t border-gray-200 dark:border-gray-700">
          <div className="px-4 pt-2 pb-4 space-y-1">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-200"
                onClick={(e) => {
                  if (!link.external) {
                    e.preventDefault();
                    const element = document.querySelector(link.href);
                    element?.scrollIntoView({ behavior: 'smooth' });
                    setIsOpen(false);
                  }
                }}
              >
                {link.name}
              </a>
            ))}
            <div className="pt-4">
              <WalletConnect />
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

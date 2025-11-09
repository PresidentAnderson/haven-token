/**
 * Utility Functions
 * Common helper functions used throughout the application
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines class names with Tailwind merge
 * Useful for conditional styling with Tailwind classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Truncates Ethereum address for display
 * @param address - Full Ethereum address
 * @param chars - Number of characters to show on each end
 */
export function truncateAddress(address: string, chars = 4): string {
  if (address.length <= chars * 2 + 2) return address;
  return `${address.slice(0, chars + 2)}...${address.slice(-chars)}`;
}

/**
 * Formats a number with commas and optional decimals
 * @param num - Number to format
 * @param decimals - Number of decimal places
 */
export function formatNumber(num: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Formats currency values
 * @param amount - Amount to format
 * @param currency - Currency code (CAD, USD, etc.)
 */
export function formatCurrency(amount: number, currency = 'CAD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Calculates HNV tokens earned from CAD spending
 * @param cadAmount - Amount spent in CAD
 * @param rate - Tokens per CAD (default: 2)
 */
export function calculateTokensEarned(cadAmount: number, rate = 2): number {
  return cadAmount * rate;
}

/**
 * Calculates staking rewards
 * @param principal - Amount of tokens staked
 * @param apy - Annual percentage yield (as whole number, e.g., 10 for 10%)
 * @param days - Number of days staked
 */
export function calculateStakingRewards(
  principal: number,
  apy: number,
  days: number
): number {
  const dailyRate = apy / 100 / 365;
  return principal * dailyRate * days;
}

/**
 * Converts token amount from wei (bigint) to human readable
 * @param amount - Token amount in wei
 * @param decimals - Token decimals
 */
export function fromWei(amount: bigint, decimals = 18): number {
  return Number(amount) / Math.pow(10, decimals);
}

/**
 * Converts human readable amount to wei (bigint)
 * @param amount - Human readable amount
 * @param decimals - Token decimals
 */
export function toWei(amount: number, decimals = 18): bigint {
  return BigInt(Math.floor(amount * Math.pow(10, decimals)));
}

/**
 * Debounce function for search/input
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Checks if we're in browser environment
 */
export const isBrowser = typeof window !== 'undefined';

/**
 * Safely parse JSON with fallback
 */
export function safeJsonParse<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!isBrowser) return false;

  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      return true;
    } catch {
      return false;
    } finally {
      document.body.removeChild(textArea);
    }
  }
}

/**
 * Enterprise-grade currency utility functions
 * Supports 10+ currencies with proper locale formatting
 */

export type Currency = 'USD' | 'EUR' | 'GBP' | 'INR' | 'JPY' | 'AUD' | 'CAD' | 'CHF' | 'CNY' | 'SGD';

export interface CurrencyInfo {
  code: Currency;
  symbol: string;
  name: string;
  locale: string;
}

export const CURRENCIES: Record<Currency, CurrencyInfo> = {
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', locale: 'en-US' },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', locale: 'de-DE' },
  GBP: { code: 'GBP', symbol: '£', name: 'British Pound', locale: 'en-GB' },
  INR: { code: 'INR', symbol: '₹', name: 'Indian Rupee', locale: 'en-IN' },
  JPY: { code: 'JPY', symbol: '¥', name: 'Japanese Yen', locale: 'ja-JP' },
  AUD: { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', locale: 'en-AU' },
  CAD: { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', locale: 'en-CA' },
  CHF: { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc', locale: 'de-CH' },
  CNY: { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', locale: 'zh-CN' },
  SGD: { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', locale: 'en-SG' },
};

/**
 * Format amount with proper currency symbol and locale
 */
export function formatCurrency(amount: number, currency: Currency = 'USD'): string {
  const currencyInfo = CURRENCIES[currency] || CURRENCIES.USD;
  
  // Special handling for different currencies
  if (currency === 'INR') {
    return formatIndianCurrency(amount, currencyInfo.symbol);
  }
  
  if (currency === 'JPY') {
    // Yen typically has no decimal places
    const formatted = Math.round(amount).toLocaleString(currencyInfo.locale);
    return `${currencyInfo.symbol}${formatted}`;
  }
  
  const formatted = amount.toLocaleString(currencyInfo.locale, { 
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });

  return `${currencyInfo.symbol}${formatted}`;
}

/**
 * Format amount in Indian numbering system (lakhs, crores)
 */
function formatIndianCurrency(amount: number, symbol: string): string {
  const formatted = amount.toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
  return `${symbol}${formatted}`;
}

/**
 * Get currency symbol
 */
export function getCurrencySymbol(currency: Currency = 'USD'): string {
  return (CURRENCIES[currency] || CURRENCIES.USD).symbol;
}

/**
 * Get full currency info
 */
export function getCurrencyInfo(currency: Currency = 'USD'): CurrencyInfo {
  return CURRENCIES[currency] || CURRENCIES.USD;
}

/**
 * Detect currency from analytics data - checks multiple sources
 */
export function detectCurrency(data: any): Currency {
  // Check multiple possible locations for currency
  const currency = 
    data?.currency || 
    data?.metrics?.currency || 
    data?.report?.currency ||
    data?.sections?.[0]?.data?.currency;
  
  if (currency && currency in CURRENCIES) {
    return currency as Currency;
  }
  
  return 'USD'; // Default to USD (most common)
}

/**
 * Format compact currency (e.g., $1.2M, ₹10L)
 */
export function formatCompactCurrency(amount: number, currency: Currency = 'USD'): string {
  const symbol = getCurrencySymbol(currency);
  
  if (currency === 'INR') {
    // Indian format: Lakhs (L) and Crores (Cr)
    if (amount >= 10000000) {
      return `${symbol}${(amount / 10000000).toFixed(1)}Cr`;
    } else if (amount >= 100000) {
      return `${symbol}${(amount / 100000).toFixed(1)}L`;
    } else if (amount >= 1000) {
      return `${symbol}${(amount / 1000).toFixed(1)}K`;
    }
  } else {
    // Western format: K, M, B
    if (amount >= 1000000000) {
      return `${symbol}${(amount / 1000000000).toFixed(1)}B`;
    } else if (amount >= 1000000) {
      return `${symbol}${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `${symbol}${(amount / 1000).toFixed(1)}K`;
    }
  }
  
  return formatCurrency(amount, currency);
}

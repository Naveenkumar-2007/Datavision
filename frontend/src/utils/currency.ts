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

// Exchange rates: 1 USD = X units of currency (Real market rates Dec 2024)
export const EXCHANGE_RATES_FROM_USD: Record<Currency, number> = {
  USD: 1.0,
  EUR: 0.95,    // 1 USD = 0.95 EUR
  GBP: 0.79,    // 1 USD = 0.79 GBP
  INR: 84.0,    // 1 USD = 84 INR (REAL RATE)
  JPY: 149.5,   // 1 USD = 149.5 JPY
  AUD: 1.54,    // 1 USD = 1.54 AUD
  CAD: 1.35,    // 1 USD = 1.35 CAD
  CHF: 0.88,    // 1 USD = 0.88 CHF
  CNY: 7.15,    // 1 USD = 7.15 CNY
  SGD: 1.35,    // 1 USD = 1.35 SGD
};

// Legacy alias for backward compatibility
export const EXCHANGE_RATES_TO_USD = EXCHANGE_RATES_FROM_USD;

/**
 * Convert amount from one currency to another
 * Uses real market exchange rates (1 USD = X currency format)
 * 
 * Examples:
 * - $31,506 USD → ₹26,46,504 INR (×84)
 * - ₹1,00,000 INR → $1,190 USD (÷84)
 */
export function convertCurrency(amount: number, fromCurrency: Currency, toCurrency: Currency): number {
  if (fromCurrency === toCurrency) return amount;

  const fromRate = EXCHANGE_RATES_FROM_USD[fromCurrency] || 1;
  const toRate = EXCHANGE_RATES_FROM_USD[toCurrency] || 1;

  // Convert: source → USD → target
  // Step 1: source to USD (divide by source rate)
  // Step 2: USD to target (multiply by target rate)
  const usdAmount = amount / fromRate;
  const targetAmount = usdAmount * toRate;

  return targetAmount;
}

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
 * Get user's preferred currency from Settings (localStorage)
 */
export function getUserPreferredCurrency(): Currency {
  try {
    const saved = localStorage.getItem('userPreferences');
    if (saved) {
      const parsed = JSON.parse(saved);
      const currency = parsed?.preferences?.currency;
      if (currency && currency in CURRENCIES) {
        return currency as Currency;
      }
    }
  } catch (e) {
    console.warn('Failed to read currency preference:', e);
  }
  return 'INR'; // Default to INR
}

/**
 * Detect currency from analytics data - checks multiple sources
 * Falls back to user's preferred currency from Settings
 */
export function detectCurrency(data: any): Currency {
  // First, get user's preferred currency from settings
  const userPreference = getUserPreferredCurrency();

  // Check if data has a specific currency
  const dataCurrency =
    data?.currency ||
    data?.metrics?.currency ||
    data?.report?.currency ||
    data?.sections?.[0]?.data?.currency;

  // If data specifies a currency, use it; otherwise use user preference
  if (dataCurrency && dataCurrency in CURRENCIES) {
    return dataCurrency as Currency;
  }

  // Return user's preferred currency from settings
  return userPreference;
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

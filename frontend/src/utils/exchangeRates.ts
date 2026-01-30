/**
 * Real-Time Exchange Rate Service
 * 
 * Uses Frankfurter API (European Central Bank rates)
 * - No API key required
 * - Updates daily (official ECB rates)
 * - Free and reliable
 * 
 * API: https://api.frankfurter.app/latest
 */

// Types are defined in ./currency.ts - this module provides real-time rate fetching

// Cached rates with timestamp
let cachedRates: Record<string, number> | null = null;
let lastFetchTime: number = 0;
const CACHE_DURATION = 60 * 60 * 1000; // 1 hour cache

// Fallback static rates (Dec 2024 approximate values)
// These are used when API is unavailable
const FALLBACK_RATES: Record<string, number> = {
    USD: 1.0,
    EUR: 0.95,    // 1 USD = 0.95 EUR
    GBP: 0.79,    // 1 USD = 0.79 GBP
    INR: 84.0,    // 1 USD = 84 INR
    JPY: 149.5,   // 1 USD = 149.5 JPY
    AUD: 1.54,    // 1 USD = 1.54 AUD
    CAD: 1.35,    // 1 USD = 1.35 CAD
    CHF: 0.88,    // 1 USD = 0.88 CHF
    CNY: 7.15,    // 1 USD = 7.15 CNY
    SGD: 1.35,    // 1 USD = 1.35 SGD
};

/**
 * Fetch latest exchange rates from API
 * Returns rates relative to USD
 */
export async function fetchExchangeRates(): Promise<Record<string, number>> {
    const now = Date.now();

    // Return cached rates if still valid
    if (cachedRates && (now - lastFetchTime) < CACHE_DURATION) {
        return cachedRates;
    }

    try {
        // Frankfurter API - ECB rates, base USD
        const response = await fetch('https://api.frankfurter.app/latest?from=USD');

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Convert to our format: how many units of X = 1 USD
        const rates: Record<string, number> = { USD: 1.0 };

        if (data.rates) {
            for (const [currency, rate] of Object.entries(data.rates)) {
                rates[currency] = rate as number;
            }
        }

        // Cache the rates
        cachedRates = rates;
        lastFetchTime = now;

        console.log('✅ Exchange rates updated from ECB:', new Date().toLocaleString());

        return rates;
    } catch (error) {
        console.warn('⚠️ Failed to fetch exchange rates, using fallback:', error);
        return FALLBACK_RATES;
    }
}

/**
 * Get current exchange rates (cached or fallback)
 */
export function getExchangeRates(): Record<string, number> {
    return cachedRates || FALLBACK_RATES;
}

/**
 * Convert currency using real-time rates
 */
export async function convertCurrencyRealtime(
    amount: number,
    fromCurrency: string,
    toCurrency: string
): Promise<number> {
    if (fromCurrency === toCurrency) return amount;

    const rates = await fetchExchangeRates();

    // Both rates are relative to USD
    const fromRate = rates[fromCurrency] || 1;
    const toRate = rates[toCurrency] || 1;

    // Convert: source -> USD -> target
    const usdAmount = amount / fromRate;  // Convert to USD
    const targetAmount = usdAmount * toRate;  // Convert from USD to target

    return targetAmount;
}

/**
 * Sync version using cached rates
 */
export function convertCurrencySync(
    amount: number,
    fromCurrency: string,
    toCurrency: string
): number {
    if (fromCurrency === toCurrency) return amount;

    const rates = getExchangeRates();

    const fromRate = rates[fromCurrency] || 1;
    const toRate = rates[toCurrency] || 1;

    const usdAmount = amount / fromRate;
    const targetAmount = usdAmount * toRate;

    return targetAmount;
}

/**
 * Initialize rates on app load
 */
export function initializeExchangeRates(): void {
    fetchExchangeRates().then(() => {
        console.log('💱 Exchange rates initialized');
    }).catch(err => {
        console.warn('Failed to initialize rates:', err);
    });
}

/**
 * Get the current rate for a specific currency pair
 */
export async function getRate(fromCurrency: string, toCurrency: string): Promise<number> {
    const rates = await fetchExchangeRates();

    if (fromCurrency === 'USD') {
        return rates[toCurrency] || 1;
    }

    if (toCurrency === 'USD') {
        return 1 / (rates[fromCurrency] || 1);
    }

    // Cross rate: FROM -> USD -> TO
    const fromToUsd = 1 / (rates[fromCurrency] || 1);
    const usdToTarget = rates[toCurrency] || 1;

    return fromToUsd * usdToTarget;
}

/**
 * Format rate for display
 */
export function formatRate(rate: number): string {
    if (rate >= 100) {
        return rate.toFixed(2);
    } else if (rate >= 1) {
        return rate.toFixed(4);
    } else {
        return rate.toFixed(6);
    }
}

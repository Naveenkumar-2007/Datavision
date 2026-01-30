import { describe, it, expect } from 'vitest';
import {
  Currency,
  CURRENCIES,
  EXCHANGE_RATES_FROM_USD,
  convertCurrency,
  formatCurrency,
} from './currency';

describe('Currency Utilities', () => {
  describe('CURRENCIES', () => {
    it('should have all 10 supported currencies', () => {
      const expectedCurrencies: Currency[] = [
        'USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SGD'
      ];
      expect(Object.keys(CURRENCIES)).toEqual(expectedCurrencies);
    });

    it('should have correct symbols for currencies', () => {
      expect(CURRENCIES.USD.symbol).toBe('$');
      expect(CURRENCIES.EUR.symbol).toBe('€');
      expect(CURRENCIES.GBP.symbol).toBe('£');
      expect(CURRENCIES.INR.symbol).toBe('₹');
      expect(CURRENCIES.JPY.symbol).toBe('¥');
    });

    it('should have correct locales', () => {
      expect(CURRENCIES.USD.locale).toBe('en-US');
      expect(CURRENCIES.INR.locale).toBe('en-IN');
      expect(CURRENCIES.JPY.locale).toBe('ja-JP');
    });
  });

  describe('EXCHANGE_RATES_FROM_USD', () => {
    it('should have USD rate as 1.0', () => {
      expect(EXCHANGE_RATES_FROM_USD.USD).toBe(1.0);
    });

    it('should have reasonable exchange rates', () => {
      expect(EXCHANGE_RATES_FROM_USD.INR).toBeGreaterThan(80);
      expect(EXCHANGE_RATES_FROM_USD.INR).toBeLessThan(90);
      expect(EXCHANGE_RATES_FROM_USD.EUR).toBeLessThan(1);
      expect(EXCHANGE_RATES_FROM_USD.JPY).toBeGreaterThan(100);
    });
  });

  describe('convertCurrency', () => {
    it('should return same amount when converting to same currency', () => {
      expect(convertCurrency(100, 'USD', 'USD')).toBe(100);
      expect(convertCurrency(500, 'INR', 'INR')).toBe(500);
    });

    it('should convert USD to INR correctly', () => {
      // 1 USD = 84 INR
      const result = convertCurrency(100, 'USD', 'INR');
      expect(result).toBe(8400);
    });

    it('should convert INR to USD correctly', () => {
      // 84 INR = 1 USD
      const result = convertCurrency(8400, 'INR', 'USD');
      expect(result).toBe(100);
    });

    it('should convert between non-USD currencies', () => {
      // EUR to GBP: 100 EUR → USD → GBP
      const result = convertCurrency(100, 'EUR', 'GBP');
      // 100 EUR / 0.95 * 0.79 ≈ 83.16
      expect(result).toBeCloseTo(83.16, 1);
    });

    it('should handle zero amount', () => {
      expect(convertCurrency(0, 'USD', 'INR')).toBe(0);
    });

    it('should handle decimal amounts', () => {
      const result = convertCurrency(10.5, 'USD', 'INR');
      expect(result).toBe(882);
    });
  });

  describe('formatCurrency', () => {
    it('should format USD correctly', () => {
      const result = formatCurrency(1234.56, 'USD');
      expect(result).toMatch(/\$1,234\.56|\$1,234.56/);
    });

    it('should format INR with Indian numbering system', () => {
      // 100000 should be formatted as ₹1,00,000
      const result = formatCurrency(100000, 'INR');
      expect(result).toContain('₹');
      expect(result).toContain('1,00,000');
    });

    it('should format JPY without decimals', () => {
      const result = formatCurrency(1234.56, 'JPY');
      expect(result).toContain('¥');
      expect(result).toContain('1,235'); // Rounded
    });

    it('should default to USD when no currency specified', () => {
      const result = formatCurrency(100);
      expect(result).toContain('$');
    });

    it('should format EUR correctly', () => {
      const result = formatCurrency(1000, 'EUR');
      expect(result).toContain('€');
    });

    it('should format GBP correctly', () => {
      const result = formatCurrency(1000, 'GBP');
      expect(result).toContain('£');
    });
  });
});
